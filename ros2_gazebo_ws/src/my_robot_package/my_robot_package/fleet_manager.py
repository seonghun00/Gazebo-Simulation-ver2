#!/usr/bin/env python3

"""여러 Servi의 상태를 확인하고 한 서빙 작업을 적절한 로봇에 배정한다.

robots.yaml에서 로봇 이름과 전용 충전소를, locations.yaml에서 주방과 테이블
목적지를 읽는다. b를 입력하면 대기·충전 중인 로봇의 거리, 배터리, 완료 작업
수를 비교해 한 대를 주방으로 호출한다. 이후 테이블 번호와 bb는 선택된 로봇의
네임스페이스별 NavigateToPose 액션으로 전달한다.
"""

import math
import queue
import threading
from dataclasses import dataclass
from pathlib import Path

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, Float32, String


COMMAND_HELP = """
Fleet serving commands
----------------------
  b       : select an available robot and call it to the kitchen
  1 - 7   : send the selected robot to a table
  bb      : return the selected robot to its own charging station
  status  : show every robot state
  q       : quit
"""


@dataclass
class RobotRecord:
    """Fleet가 작업 배정에 사용하는 로봇별 최소 상태."""

    name: str
    charger: dict
    current_pose: dict
    battery: float = 100.0
    state: str = 'idle'
    completed_jobs: int = 0
    available: bool = True
    action_client: ActionClient = None
    operation_publisher: object = None


class FleetManager(Node):
    """등록된 로봇을 선택하고 네임스페이스별 Nav2 목표를 전송한다."""

    def __init__(self):
        super().__init__('fleet_manager')

        package_share = Path(get_package_share_directory('my_robot_package'))
        self.declare_parameter(
            'robots_file', str(package_share / 'config' / 'robots.yaml')
        )
        self.declare_parameter(
            'locations_file', str(package_share / 'config' / 'locations.yaml')
        )

        robots_file = Path(self.get_parameter('robots_file').value)
        locations_file = Path(self.get_parameter('locations_file').value)
        self.frame_id, self.locations = self._load_locations(locations_file)
        robot_configs = self._load_robots(robots_file)

        state_qos = QoSProfile(depth=1)
        state_qos.reliability = ReliabilityPolicy.RELIABLE
        state_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self.robots = {}
        for config in robot_configs:
            name = config['name']
            charger = dict(config['charging_station'])
            record = RobotRecord(
                name=name,
                charger=charger,
                current_pose=dict(charger),
            )
            record.action_client = ActionClient(
                self, NavigateToPose, f'/{name}/navigate_to_pose'
            )
            record.operation_publisher = self.create_publisher(
                String, f'/{name}/operation_state', state_qos
            )
            self.create_subscription(
                Float32,
                f'/{name}/battery_percentage',
                lambda msg, robot_name=name: self._battery_callback(
                    robot_name, msg
                ),
                state_qos,
            )
            self.create_subscription(
                PoseWithCovarianceStamped,
                f'/{name}/amcl_pose',
                lambda msg, robot_name=name: self._pose_callback(
                    robot_name, msg
                ),
                10,
            )
            self.create_subscription(
                String,
                f'/{name}/battery_alert',
                lambda msg, robot_name=name: self._alert_callback(
                    robot_name, msg
                ),
                10,
            )
            self.create_subscription(
                Bool,
                f'/{name}/emergency_shutdown',
                lambda msg, robot_name=name: self._shutdown_callback(
                    robot_name, msg
                ),
                state_qos,
            )
            self.robots[name] = record

        self.active_robot_name = None
        self.active_phase = None
        self.get_logger().info(
            f'Fleet robots loaded: {", ".join(self.robots)}'
        )

    @staticmethod
    def _read_yaml(path):
        if not path.is_file():
            raise FileNotFoundError(f'설정 파일이 없습니다: {path}')
        with path.open(encoding='utf-8') as file:
            return yaml.safe_load(file) or {}

    def _load_robots(self, path):
        data = self._read_yaml(path)
        robots = data.get('robots')
        if not isinstance(robots, list) or not robots:
            raise ValueError('robots.yaml에 robots 목록이 필요합니다.')

        names = set()
        for robot in robots:
            name = robot.get('name')
            charger = robot.get('charging_station')
            if not name or name in names:
                raise ValueError('로봇 name은 비어 있지 않고 중복되지 않아야 합니다.')
            if not isinstance(charger, dict) or not all(
                key in charger for key in ('x', 'y', 'yaw')
            ):
                raise ValueError(f'{name}의 charging_station 좌표가 잘못됐습니다.')
            names.add(name)
        return robots

    def _load_locations(self, path):
        data = self._read_yaml(path)
        locations = data.get('locations')
        required = {
            'kitchen_pickup',
            *(f'table_{number}' for number in range(1, 8)),
        }
        if not isinstance(locations, dict) or required - locations.keys():
            missing = sorted(required - (locations or {}).keys())
            raise ValueError(f'필수 목적지가 없습니다: {", ".join(missing)}')
        return data.get('frame_id', 'map'), locations

    def _battery_callback(self, robot_name, message):
        self.robots[robot_name].battery = float(message.data)

    def _pose_callback(self, robot_name, message):
        """AMCL이 추정한 map 기준 현재 위치를 배정 거리 계산에 반영한다."""
        pose = message.pose.pose
        quaternion = pose.orientation
        yaw = math.atan2(
            2.0
            * (
                quaternion.w * quaternion.z
                + quaternion.x * quaternion.y
            ),
            1.0
            - 2.0
            * (
                quaternion.y * quaternion.y
                + quaternion.z * quaternion.z
            ),
        )
        self.robots[robot_name].current_pose = {
            'x': float(pose.position.x),
            'y': float(pose.position.y),
            'yaw': yaw,
        }

    def _alert_callback(self, robot_name, message):
        """로봇별 배터리 경고를 Fleet 명령 터미널에 함께 표시한다."""
        alert = message.data
        if alert.startswith('10%'):
            self.get_logger().error(f'{robot_name}: {alert} 즉시 복귀하세요.')
        elif alert.startswith(('20%', '30%', '40%', '50%')):
            self.get_logger().warning(f'{robot_name}: {alert}')
        elif alert.startswith('100%'):
            self.get_logger().info(f'{robot_name}: 충전 완료')

    def _shutdown_callback(self, robot_name, message):
        if not message.data:
            return
        robot = self.robots[robot_name]
        robot.available = False
        robot.state = 'out_of_service'
        self.get_logger().error(
            f'{robot_name}: 배터리가 소진되어 Fleet 배정에서 제외합니다.'
        )

    @staticmethod
    def _distance(first, second):
        return math.hypot(
            float(first['x']) - float(second['x']),
            float(first['y']) - float(second['y']),
        )

    def _select_robot(self):
        kitchen = self.locations['kitchen_pickup']
        candidates = [
            robot
            for robot in self.robots.values()
            if robot.available
            and robot.state in ('idle', 'charging')
            and robot.battery > 20.0
        ]
        if not candidates:
            return None

        def assignment_cost(robot):
            distance_cost = self._distance(robot.current_pose, kitchen)
            battery_penalty = (100.0 - robot.battery) * 0.02
            workload_penalty = robot.completed_jobs * 0.50
            return distance_cost + battery_penalty + workload_penalty

        return min(candidates, key=assignment_cost)

    def _send_goal(self, robot, destination_name, pose_data):
        if not robot.action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error(
                f'{robot.name}: NavigateToPose 액션 서버를 찾을 수 없습니다.'
            )
            return False

        yaw = float(pose_data['yaw'])
        pose = PoseStamped()
        pose.header.frame_id = self.frame_id
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(pose_data['x'])
        pose.pose.position.y = float(pose_data['y'])
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        goal = NavigateToPose.Goal()
        goal.pose = pose
        robot.operation_publisher.publish(String(data='working'))
        robot.state = 'working'
        self.get_logger().info(
            f'{robot.name} -> {destination_name} '
            f'(x={pose_data["x"]}, y={pose_data["y"]}, yaw={yaw})'
        )

        send_future = robot.action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f'{robot.name}: 목표가 거절됐습니다.')
            robot.state = 'idle'
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result()
        if result is None or result.status != GoalStatus.STATUS_SUCCEEDED:
            status = result.status if result is not None else 'unknown'
            self.get_logger().error(
                f'{robot.name}: {destination_name} 이동 실패 (status={status})'
            )
            robot.state = 'idle'
            return False

        robot.current_pose = dict(pose_data)
        self.get_logger().info(f'{robot.name}: {destination_name} 도착')
        return True

    def handle_command(self, command):
        if command == 'status':
            self.print_status()
            return

        if command == 'b':
            if self.active_robot_name is not None:
                self.get_logger().warning(
                    '현재 서빙 작업을 bb로 종료한 뒤 새 작업을 시작하세요.'
                )
                return
            robot = self._select_robot()
            if robot is None:
                self.get_logger().error(
                    '배정 가능한 로봇이 없습니다. 상태와 배터리를 확인하세요.'
                )
                return
            if self._send_goal(
                robot, 'kitchen_pickup', self.locations['kitchen_pickup']
            ):
                robot.state = 'loading'
                self.active_robot_name = robot.name
                self.active_phase = 'loading'
                self.get_logger().info(
                    f'{robot.name}에 음식을 적재한 뒤 테이블 번호를 입력하세요.'
                )
            return

        if command in {str(number) for number in range(1, 8)}:
            robot = self._active_robot(required_phase='loading')
            if robot is None:
                return
            destination = f'table_{command}'
            if self._send_goal(robot, destination, self.locations[destination]):
                robot.state = 'waiting_customer'
                self.active_phase = 'waiting_customer'
                self.get_logger().info(
                    '손님이 음식을 가져가면 bb를 입력하세요.'
                )
            return

        if command == 'bb':
            robot = self._active_robot(required_phase='waiting_customer')
            if robot is None:
                return
            if self._send_goal(robot, 'charging_station', robot.charger):
                robot.operation_publisher.publish(String(data='charging'))
                robot.state = 'charging'
                robot.completed_jobs += 1
                self.active_robot_name = None
                self.active_phase = None
            return

        self.get_logger().warning('b, 1-7, bb, status 또는 q를 입력하세요.')

    def _active_robot(self, required_phase):
        if self.active_robot_name is None or self.active_phase != required_phase:
            self.get_logger().warning('현재 명령 순서에 맞는 활성 로봇이 없습니다.')
            return None
        return self.robots[self.active_robot_name]

    def print_status(self):
        for robot in self.robots.values():
            self.get_logger().info(
                f'{robot.name}: state={robot.state}, '
                f'battery={robot.battery:.0f}%, jobs={robot.completed_jobs}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = FleetManager()
        print(COMMAND_HELP)
        command_queue = queue.Queue()

        def read_commands():
            while rclpy.ok():
                try:
                    command_queue.put(input('fleet> ').strip().lower())
                except (EOFError, KeyboardInterrupt):
                    command_queue.put('q')
                    return

        threading.Thread(target=read_commands, daemon=True).start()

        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            try:
                command = command_queue.get_nowait()
            except queue.Empty:
                continue
            if command == 'q':
                break
            node.handle_command(command)
    except (FileNotFoundError, ValueError) as error:
        if node is None:
            print(f'Fleet configuration error: {error}')
        else:
            node.get_logger().error(str(error))
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
