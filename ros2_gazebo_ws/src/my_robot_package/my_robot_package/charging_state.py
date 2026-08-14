#!/usr/bin/env python3

"""Servi의 배터리 감소, 충전, 잔량 경고와 방전을 모의하는 노드.

serving_control.py가 /servi_1/operation_state에 보내는 working 또는 charging을
구독한다. working 상태에서는 10초마다 1% 감소하고, 로봇이 충전소에 도착해
charging 상태가 되면 5초마다 1% 증가한다. 100%가 되면 충전을 멈추며
50·40·30·20·10%에서 경고를 한 번씩 발행한다.

연동 인터페이스:
* 구독: /servi_1/operation_state (working 또는 charging)
* 발행: /servi_1/battery_percentage, /servi_1/is_charging
* 발행: /servi_1/battery_alert (경고 및 충전 완료 메시지)
* 발행: /servi_1/emergency_shutdown (0%일 때 True)

serving_control.py는 경고와 긴급 종료 토픽을 구독해 같은 명령 터미널에
메시지를 출력하고 진행 중인 Nav2 목표를 취소한다.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, Float32, String


class ChargingState(Node):
    """servi_1의 작업·충전 이벤트에 따라 가상 배터리 상태를 관리한다."""

    def __init__(self):
        super().__init__('charging_state_servi_1')

        state_qos = QoSProfile(depth=1)
        state_qos.reliability = ReliabilityPolicy.RELIABLE
        state_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self.battery_publisher = self.create_publisher(
            Float32, '/servi_1/battery_percentage', state_qos
        )
        self.charging_publisher = self.create_publisher(
            Bool, '/servi_1/is_charging', state_qos
        )
        self.alert_publisher = self.create_publisher(
            String, '/servi_1/battery_alert', 10
        )
        self.shutdown_publisher = self.create_publisher(
            Bool, '/servi_1/emergency_shutdown', state_qos
        )
        self.create_subscription(
            String,
            '/servi_1/operation_state',
            self._operation_callback,
            state_qos,
        )

        self.battery_percent = 100.0
        self.operation_state = 'full'
        self.elapsed_seconds = 0.0
        self.triggered_thresholds = set()
        self.depleted = False
        self.last_update = self.get_clock().now()
        self.timer = self.create_timer(1.0, self._update)
        self.shutdown_timer = None

        self._publish_state()
        self._alert('100%: Battery is full. Charging stopped.')

    def _operation_callback(self, message):
        """serving_control이 보낸 이벤트에 따라 작업과 충전 상태를 전환한다."""
        state = message.data.strip().lower()
        if state not in ('working', 'charging'):
            self.get_logger().warning(f'Unknown operation state: {state}')
            return

        if state == 'charging' and self.battery_percent >= 100.0:
            self.operation_state = 'full'
            self._alert('100%: Battery is full. Charging stopped.')
        else:
            self.operation_state = state
            if state == 'working':
                self.triggered_thresholds = {
                    threshold
                    for threshold in self.triggered_thresholds
                    if threshold >= self.battery_percent
                }
                self.get_logger().info('Work started. Battery drain started.')
            else:
                self.get_logger().info('Charging station reached. Charging started.')

        self.elapsed_seconds = 0.0
        self.last_update = self.get_clock().now()
        self._publish_state()

    def _update(self):
        """현재 동작 상태와 경과 시간에 따라 배터리 잔량을 증감한다."""
        now = self.get_clock().now()
        elapsed = (now - self.last_update).nanoseconds / 1e9
        self.last_update = now

        if self.operation_state == 'working':
            self._apply_steps(elapsed, seconds_per_step=10.0, amount=-1.0)
        elif self.operation_state == 'charging':
            self._apply_steps(elapsed, seconds_per_step=5.0, amount=1.0)

        self._publish_state()

    def _apply_steps(self, elapsed, seconds_per_step, amount):
        self.elapsed_seconds += max(0.0, elapsed)

        while self.elapsed_seconds >= seconds_per_step:
            self.elapsed_seconds -= seconds_per_step
            previous = self.battery_percent
            self.battery_percent = min(
                100.0,
                max(0.0, self.battery_percent + amount),
            )

            if amount < 0.0:
                self._check_low_battery(previous)
                if self.battery_percent <= 0.0:
                    self._request_shutdown()
                    return
            elif self.battery_percent >= 100.0:
                self.operation_state = 'full'
                self.elapsed_seconds = 0.0
                self.triggered_thresholds.clear()
                self._alert('100%: Battery is full. Charging stopped.')
                return

    def _check_low_battery(self, previous):
        """한 번의 방전 주기에서 잔량 단계별 경고를 각각 한 번만 발행한다."""
        for threshold in (50, 40, 30, 20, 10):
            if (
                threshold not in self.triggered_thresholds
                and previous > threshold >= self.battery_percent
            ):
                self.triggered_thresholds.add(threshold)
                self._alert(f'{threshold}%: Battery remaining.')

    def _request_shutdown(self):
        if self.depleted:
            return

        self.depleted = True
        self.operation_state = 'empty'
        self._alert('0%: Battery depleted. Shutting down the Servi system.')
        self.shutdown_publisher.publish(Bool(data=True))
        self.timer.cancel()
        self.shutdown_timer = self.create_timer(0.5, self._finish_shutdown)

    def _publish_state(self):
        self.battery_publisher.publish(Float32(data=self.battery_percent))
        self.charging_publisher.publish(
            Bool(data=self.operation_state == 'charging')
        )

    def _alert(self, message):
        self.alert_publisher.publish(String(data=message))
        self.get_logger().info(message)

    def _finish_shutdown(self):
        if self.shutdown_timer is not None:
            self.shutdown_timer.cancel()
        if rclpy.ok():
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = ChargingState()

    try:
        rclpy.spin(node)
    except (ExternalShutdownException, KeyboardInterrupt):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    if node.depleted:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
