"""robots.yaml에 등록된 모든 Servi와 공용 식당 환경을 실행한다.

Gazebo와 Map Server는 한 번만 실행한다. robots.yaml을 순회하며 각 로봇에
robot_bringup.launch.py를 적용하므로 로봇을 추가할 때 Python 코드를 수정할
필요가 없다.
"""

import os
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _load_robot_actions(context, package_share):
    """설정 파일을 검사하고 로봇 수만큼 공용 Bringup을 생성한다."""
    robots_file = Path(LaunchConfiguration('robots_file').perform(context))
    if not robots_file.is_file():
        raise FileNotFoundError(f'로봇 설정 파일이 없습니다: {robots_file}')

    with robots_file.open(encoding='utf-8') as file:
        data = yaml.safe_load(file) or {}

    robots = data.get('robots')
    if not isinstance(robots, list) or not robots:
        raise ValueError('robots.yaml에 robots 목록이 필요합니다.')

    names = [robot.get('name') for robot in robots]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError('모든 로봇은 중복되지 않는 name이 필요합니다.')

    robot_launch = os.path.join(
        package_share, 'launch', 'robot_bringup.launch.py'
    )
    actions = []

    for robot in robots:
        spawn = robot.get('spawn', {})
        charger = robot.get('charging_station', {})
        for key in ('x', 'y', 'yaw'):
            if key not in spawn:
                raise ValueError(f'{robot["name"]}.spawn에 {key}가 없습니다.')
            if key not in charger:
                raise ValueError(
                    f'{robot["name"]}.charging_station에 {key}가 없습니다.'
                )

        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(robot_launch),
                launch_arguments={
                    'robot_name': str(robot['name']),
                    'spawn_x': str(spawn['x']),
                    'spawn_y': str(spawn['y']),
                    'spawn_z': str(spawn.get('z', 0.25)),
                    'spawn_yaw': str(spawn['yaw']),
                    'charger_x': str(charger['x']),
                    'charger_y': str(charger['y']),
                    'charger_yaw': str(charger['yaw']),
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                    'autostart': LaunchConfiguration('autostart'),
                }.items(),
            )
        )

    return actions


def generate_launch_description():
    """공용 Gazebo·Map Server와 설정된 모든 로봇을 실행한다."""
    package_share = get_package_share_directory('my_robot_package')
    world_file = os.path.join(
        package_share, 'worlds', 'simple_restaurant.world'
    )
    models_path = os.path.join(package_share, 'models')
    default_robots = os.path.join(package_share, 'config', 'robots.yaml')
    default_map = os.path.join(
        package_share, 'maps', 'restaurant_map_slam.yaml'
    )

    gazebo = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            world_file,
            '-s',
            'libgazebo_ros_init.so',
            '-s',
            'libgazebo_ros_factory.so',
        ],
        output='screen',
    )

    map_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, 'launch', 'map_server.launch.py')
        ),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'robots_file',
                default_value=default_robots,
                description='실행할 로봇 목록 YAML 경로',
            ),
            DeclareLaunchArgument(
                'map',
                default_value=default_map,
                description='공용 점유 지도 YAML 경로',
            ),
            DeclareLaunchArgument('use_sim_time', default_value='true'),
            DeclareLaunchArgument('autostart', default_value='true'),
            SetEnvironmentVariable(
                name='GAZEBO_MODEL_PATH',
                value=os.pathsep.join(
                    path
                    for path in (
                        models_path,
                        os.environ.get('GAZEBO_MODEL_PATH', ''),
                    )
                    if path
                ),
            ),
            SetEnvironmentVariable(name='GAZEBO_VERBOSE', value='1'),
            SetEnvironmentVariable(name='LIBGL_ALWAYS_SOFTWARE', value='1'),
            gazebo,
            map_server,
            OpaqueFunction(
                function=_load_robot_actions,
                args=[package_share],
            ),
        ]
    )
