
#!/usr/bin/env python3

"""키보드 입력을 로봇 속도 명령으로 바꾸는 수동 주행 테스트 노드.

w·x로 전진 및 후진 속도를 조절하고 a·d로 회전 속도를 조절한다. 계산한
geometry_msgs/msg/Twist 메시지를 /cmd_vel 토픽으로 발행하므로 Gazebo URDF의
Diff Drive 플러그인이 이를 받아 바퀴를 움직인다. Nav2와 함께 실행하면 두
프로그램이 같은 /cmd_vel을 발행할 수 있으므로 수동 테스트할 때만 사용한다.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, select, termios, tty

# 프로그램 종료 후 복원할 수 있도록 현재 터미널 설정을 저장한다.
settings = termios.tcgetattr(sys.stdin)

msg = """
Servi Custom WASD Control Panel
---------------------------------------
Moving around:
        w
   a    s    d
        x

w / x : Increase linear velocity (Forward / Backward)
a / d : Increase angular velocity (Left / Right)
s     : Emergency Brake (Stop all movement)

CTRL-C to quit
"""

class ServiTeleop(Node):
    def __init__(self):
        super().__init__('servi_teleop')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.linear_vel = 0.0
        self.angular_vel = 0.0

    def publish_twist(self):
        twist = Twist()
        twist.linear.x = float(self.linear_vel)
        twist.angular.z = float(self.angular_vel)
        self.publisher_.publish(twist)

def getKey():
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main(args=None):
    rclpy.init(args=args)
    node = ServiTeleop()
    print(msg)

    try:
        while True:
            key = getKey()
            if key == 'w':
                node.linear_vel += 0.2
            elif key == 'x':
                node.linear_vel -= 0.2
            elif key == 'a':
                node.angular_vel += 0.5
            elif key == 'd':
                node.angular_vel -= 0.5
            elif key == 's':
                node.linear_vel = 0.0
                node.angular_vel = 0.0
            elif key == '\x03':  # CTRL-C 입력 시 반복을 종료한다.
                break

            node.publish_twist()
            print(f"Current Servi Speed 🏎️ : Linear {node.linear_vel:.1f} m/s | Angular {node.angular_vel:.1f} rad/s\r")

    except Exception as e:
        print(e)
    finally:
        # 노드를 종료하기 전에 속도 0을 한 번 발행해 로봇을 정지시킨다.
        twist = Twist()
        node.publisher_.publish(twist)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
