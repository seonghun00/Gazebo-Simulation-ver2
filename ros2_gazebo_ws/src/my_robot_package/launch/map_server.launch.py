"""저장된 식당 점유 지도를 /map으로 발행하는 전용 Launch 파일.

restaurant_map_slam.yaml에서 PGM 파일 경로, 해상도, 원점을 읽어 Nav2 Map
Server에 전달한다. AMCL이나 Navigation은 실행하지 않으므로 SLAM 결과를
RViz에서 확인하거나 /map만 필요한 경우 사용한다. Lifecycle Manager가 Map
Server를 configure 및 active 상태로 자동 전환한다.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    """Nav2 Map Server와 전용 Lifecycle Manager의 실행 구성을 만든다."""
    package_share = get_package_share_directory('my_robot_package')
    default_map = os.path.join(package_share, 'maps', 'restaurant_map_slam.yaml')

    map_yaml = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Absolute path to the occupancy-grid map YAML file',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use the Gazebo simulation clock',
        ),
        # 선택한 YAML을 통해 PGM 경로와 지도 메타데이터를 불러온다.
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
        # Map Server를 unconfigured 상태에서 active 상태로 자동 전환한다.
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_map_server',
            output='screen',
            parameters=[{
                'autostart': True,
                'node_names': ['map_server'],
                'use_sim_time': use_sim_time,
            }],
        ),
    ])
