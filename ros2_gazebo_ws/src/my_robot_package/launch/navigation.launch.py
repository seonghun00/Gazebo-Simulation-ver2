"""식당용 설정으로 Nav2 자율주행 기능을 실행하는 Launch 파일.

이 파일이 경로 계획 알고리즘을 직접 구현하는 것은 아니다. Nav2가 제공하는
navigation_launch.py를 불러오고 config/nav2_params.yaml에 선택한 Planner,
Controller, Costmap, Behavior, Velocity Smoother 플러그인을 실행한다.

Nav2는 serving_control.py가 navigate_to_pose 액션으로 보낸 목적지를 받고,
/map, /scan, /odom 및 TF를 이용해 경로를 계산한 뒤 최종 속도 명령을
/cmd_vel로 발행한다. AMCL 위치 추정은 localization.launch.py에서 별도로
실행되어 있어야 한다.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """프로젝트 파라미터와 시뮬레이션 옵션을 Nav2 Bringup에 전달한다."""
    package_share = get_package_share_directory('my_robot_package')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')

    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                package_share, 'config', 'nav2_params.yaml'
            ),
            description='Absolute path to the Nav2 parameter file',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use the Gazebo simulation clock',
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically activate the Nav2 lifecycle nodes',
        ),
        # 공용 nav2_params.yaml을 사용해 Nav2 공식 서버들을 실행한다.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_share, 'launch', 'navigation_launch.py')
            ),
            launch_arguments={
                'params_file': params_file,
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'use_composition': 'False',
                'use_respawn': 'False',
            }.items(),
        ),
    ])
