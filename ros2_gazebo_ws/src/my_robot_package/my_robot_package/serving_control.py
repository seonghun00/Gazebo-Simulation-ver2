#!/usr/bin/env python3

"""터미널 명령을 저장된 목적지로 변환해 Nav2에 전달하는 서빙 제어 노드.

config/locations.yaml에서 주방, 1~7번 테이블, 충전소의 x·y·yaw를 읽는다.
사용자가 b, 1~7, bb를 입력하면 해당 좌표를 NavigateToPose 액션 서버로
전송하며 실제 경로 계획과 장애물 회피는 navigation.launch.py로 실행한
Nav2가 수행한다.

연동 인터페이스:
* 액션 전송: navigate_to_pose (nav2_msgs/action/NavigateToPose)
* 상태 발행: operation_state에 working 또는 charging 전송
* 경고 구독: battery_alert를 받아 현재 터미널에 배터리 경고 출력
* 종료 구독: emergency_shutdown을 받아 진행 중인 목표 취소

operation_state는 charging_state.py가 구독하며, 배터리 감소·충전 시작 시점을
결정하는 데 사용한다.
"""

import math
import queue
import threading
from pathlib import Path

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String


COMMAND_HELP = """
Serving commands (press Enter after each command)
--------------------------------------------------
  b      : go to the kitchen pickup counter
  1 - 7  : go to the selected table
  bb     : return to the charging station
  q      : quit
"""


class ServingControl(Node):
    """저장된 식당 목적지를 Nav2 NavigateToPose 액션 서버로 전송한다."""

    def __init__(self):
        super().__init__('serving_control')

        self.declare_parameter('robot_name', 'servi_1')
        self.declare_parameter('use_robot_namespace', False)
        robot_name = self.get_parameter('robot_name').value
        use_robot_namespace = self.get_parameter(
            'use_robot_namespace'
        ).value
        node_namespace = self.get_namespace().strip('/')
        state_prefix = '' if node_namespace else f'/{robot_name}/'
        navigation_prefix = (
            state_prefix if node_namespace or use_robot_namespace else ''
        )

        package_share = Path(get_package_share_directory('my_robot_package'))
        default_locations_file = package_share / 'config' / 'locations.yaml'

        self.declare_parameter(
            'locations_file',
            str(default_locations_file),
        )
        locations_file = Path(
            self.get_parameter('locations_file').get_parameter_value().string_value
        )

        self.frame_id, self.locations = self._load_locations(locations_file)
        self.navigate_client = ActionClient(
            self,
            NavigateToPose,
            f'{navigation_prefix}navigate_to_pose',
        )
        shutdown_qos = QoSProfile(depth=1)
        shutdown_qos.reliability = ReliabilityPolicy.RELIABLE
        shutdown_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.create_subscription(
            Bool,
            f'{state_prefix}emergency_shutdown',
            self._emergency_shutdown_callback,
            shutdown_qos,
        )
        self.create_subscription(
            String,
            f'{state_prefix}battery_alert',
            self._battery_alert_callback,
            10,
        )
        self.operation_state_publisher = self.create_publisher(
            String,
            f'{state_prefix}operation_state',
            shutdown_qos,
        )
        self.emergency_shutdown = False
        self.active_goal_handle = None

        self.get_logger().info(f'Loaded locations from: {locations_file}')

    def _battery_alert_callback(self, message):
        alert = message.data

        if alert.startswith('10%'):
            self.get_logger().error(
                '[CRITICAL BATTERY] 10% remaining. '
                'Enter "bb" now to return to the charging station.'
            )
        elif alert.startswith(('20%', '30%', '40%', '50%')):
            percentage = alert.split('%', maxsplit=1)[0]
            self.get_logger().warning(
                f'[BATTERY WARNING] {percentage}% remaining.'
            )
        elif alert.startswith('100%'):
            self.get_logger().info(
                '[CHARGING COMPLETE] Battery is at 100%.'
            )

    def _emergency_shutdown_callback(self, message):
        if not message.data or self.emergency_shutdown:
            return

        self.emergency_shutdown = True
        self.get_logger().fatal(
            'Battery is depleted. Cancelling navigation and stopping '
            'the serving controller.'
        )
        if self.active_goal_handle is not None:
            self.active_goal_handle.cancel_goal_async()

    def _load_locations(self, locations_file):
        """map 기준 목적지 좌표를 불러오고 필수 위치와 값이 있는지 검사한다."""
        if not locations_file.is_file():
            raise FileNotFoundError(
                f'Locations file does not exist: {locations_file}'
            )

        with locations_file.open(encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}

        frame_id = data.get('frame_id', 'map')
        locations = data.get('locations')
        if not isinstance(locations, dict) or not locations:
            raise ValueError(
                f'No locations are defined in: {locations_file}'
            )

        required = {
            *(f'table_{number}' for number in range(1, 8)),
            'kitchen_pickup',
            'charging_station',
        }
        missing = sorted(required - locations.keys())
        if missing:
            raise ValueError(
                f'Missing locations: {", ".join(missing)}'
            )

        for name, pose in locations.items():
            if not all(key in pose for key in ('x', 'y', 'yaw')):
                raise ValueError(
                    f'Location "{name}" must contain x, y, and yaw.'
                )

        return frame_id, locations

    def navigate_to(self, location_name):
        """선택한 좌표를 Nav2로 보내고 성공·실패 결과가 올 때까지 기다린다."""
        if self.emergency_shutdown:
            self.get_logger().error('Navigation is disabled: battery is empty.')
            return False

        if location_name not in self.locations:
            self.get_logger().error(f'Unknown location: {location_name}')
            return False

        self.get_logger().info('Waiting for the Nav2 action server...')
        if not self.navigate_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(
                'NavigateToPose is unavailable. Start AMCL and Nav2 first.'
            )
            return False

        location = self.locations[location_name]
        yaw = float(location['yaw'])

        pose = PoseStamped()
        pose.header.frame_id = self.frame_id
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(location['x'])
        pose.pose.position.y = float(location['y'])
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        goal = NavigateToPose.Goal()
        goal.pose = pose

        self.get_logger().info(
            f'Going to {location_name}: '
            f'x={location["x"]}, y={location["y"]}, yaw={yaw}'
        )

        send_future = self.navigate_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f'Goal rejected: {location_name}')
            return False

        self.active_goal_handle = goal_handle
        if location_name != 'charging_station':
            self.operation_state_publisher.publish(String(data='working'))

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result()
        self.active_goal_handle = None

        if self.emergency_shutdown:
            return False

        if result is not None and result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Arrived at {location_name}.')
            if location_name == 'charging_station':
                self.operation_state_publisher.publish(String(data='charging'))
            return True

        status = result.status if result is not None else 'unknown'
        self.get_logger().error(
            f'Failed to reach {location_name}. Status: {status}'
        )
        return False


def command_to_location(command):
    """짧은 터미널 명령을 locations.yaml의 목적지 이름으로 변환한다."""
    if command == 'b':
        return 'kitchen_pickup'
    if command == 'bb':
        return 'charging_station'
    if command in {str(number) for number in range(1, 8)}:
        return f'table_{command}'
    return None


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = ServingControl()
        print(COMMAND_HELP)

        command_queue = queue.Queue()
        request_input = threading.Event()
        request_input.set()

        def read_commands():
            while True:
                request_input.wait()
                request_input.clear()
                try:
                    command_queue.put(input('serving> ').strip().lower())
                except (EOFError, KeyboardInterrupt):
                    command_queue.put('q')
                    return

        threading.Thread(target=read_commands, daemon=True).start()

        while rclpy.ok() and not node.emergency_shutdown:
            rclpy.spin_once(node, timeout_sec=0.1)
            try:
                command = command_queue.get_nowait()
            except queue.Empty:
                continue

            if command == 'q':
                break

            location_name = command_to_location(command)
            if location_name is None:
                print('Invalid command. Use b, bb, 1-7, or q.')
                request_input.set()
                continue

            node.navigate_to(location_name)
            if not node.emergency_shutdown:
                request_input.set()

    except (FileNotFoundError, ValueError) as error:
        if node is not None:
            node.get_logger().error(str(error))
        else:
            print(f'Configuration error: {error}')
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
