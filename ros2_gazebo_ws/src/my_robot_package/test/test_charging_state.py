import rclpy
from rclpy.duration import Duration
from std_msgs.msg import String

from my_robot_package.charging_state import ChargingState


def test_all_low_battery_thresholds_are_triggered():
    rclpy.init()
    node = ChargingState()

    try:
        node.battery_percent = 51.0
        node._operation_callback(String(data='working'))
        node.last_update = node.get_clock().now() - Duration(seconds=410.1)
        node._update()

        assert node.battery_percent == 10.0
        assert node.triggered_thresholds == {50, 40, 30, 20, 10}
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def test_work_drains_and_empty_battery_requests_shutdown():
    rclpy.init()
    node = ChargingState()

    try:
        node.battery_percent = 11.0
        node._operation_callback(String(data='working'))
        node.last_update = node.get_clock().now() - Duration(seconds=110.1)
        node._update()

        assert 10 in node.triggered_thresholds
        assert node.battery_percent == 0.0
        assert node.depleted is True
        node._finish_shutdown()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def test_charging_stops_at_full_battery():
    rclpy.init()
    node = ChargingState()

    try:
        node.battery_percent = 98.0
        node._operation_callback(String(data='charging'))
        node.last_update = node.get_clock().now() - Duration(seconds=10.1)
        node._update()

        assert node.battery_percent == 100.0
        assert node.operation_state == 'full'
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
