"""저장된 식당 지도에서 로봇의 현재 위치를 찾는 Localization Launch 파일.

Map Server는 restaurant_map_slam.yaml이 가리키는 PGM 지도를 /map 토픽으로
발행한다. AMCL은 /map, /scan, odom 정보를 비교해 로봇 위치를 추정하고
Nav2가 사용하는 map -> odom TF를 발행한다. Lifecycle Manager는 Map Server와
AMCL을 configure 및 active 상태로 자동 전환한다.

이 파일은 위치 추정까지만 담당한다. 목적지까지 경로를 만들고 /cmd_vel을
출력하는 기능은 navigation.launch.py가 담당한다.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    """Map Server, AMCL, Lifecycle Manager의 실행 구성을 만든다."""
    package_share = get_package_share_directory('my_robot_package')

    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(
                package_share, 'maps', 'restaurant_map_slam.yaml'
            ),
            description='Absolute path to the occupancy-grid map YAML file',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                package_share, 'config', 'amcl_params.yaml'
            ),
            description='Absolute path to the AMCL parameter file',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use the Gazebo simulation clock',
        ),
        # 저장된 식당 지도를 /map 토픽으로 발행한다.
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'yaml_filename': map_yaml,
                'use_sim_time': use_sim_time,
            }],
        ),
        # /map과 /scan을 비교해 지도 안에서 로봇의 위치를 추정한다.
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
        ),
        # Map Server와 AMCL의 Lifecycle 상태를 자동으로 활성화한다.
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'autostart': True,
                'node_names': ['map_server', 'amcl'],
                'use_sim_time': use_sim_time,
            }],
        ),
    ])
