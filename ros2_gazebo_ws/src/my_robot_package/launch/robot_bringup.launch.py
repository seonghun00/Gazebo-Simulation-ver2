"""robots.yaml의 로봇 한 대를 스폰하고 AMCL·Nav2·배터리를 실행한다.

이 파일은 단독 실행보다 fleet_bringup.launch.py에서 반복 호출하도록 만든
공용 Launch이다. robot_name으로 ROS 네임스페이스와 TF 프레임을 분리하고,
spawn 좌표를 Gazebo 생성 위치와 AMCL 초기 위치에 함께 사용한다.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.descriptions import ParameterValue
from nav2_common.launch import ReplaceString


def generate_launch_description():
    """한 로봇의 모델, 위치 추정, 자율주행과 배터리 노드를 구성한다."""
    package_name = 'my_robot_package'
    package_share = get_package_share_directory(package_name)
    nav2_share = get_package_share_directory('nav2_bringup')

    robot_name = LaunchConfiguration('robot_name')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_z = LaunchConfiguration('spawn_z')
    spawn_yaw = LaunchConfiguration('spawn_yaw')
    charger_x = LaunchConfiguration('charger_x')
    charger_y = LaunchConfiguration('charger_y')
    charger_yaw = LaunchConfiguration('charger_yaw')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    xacro_file = os.path.join(
        package_share, 'urdf', 'servi_model.urdf.xacro'
    )
    amcl_params = os.path.join(package_share, 'config', 'amcl_params.yaml')
    nav2_params = os.path.join(
        package_share, 'config', 'nav2_multi_params.yaml'
    )

    robot_description = ParameterValue(
        Command(
            [
                FindExecutable(name='xacro'),
                ' ',
                xacro_file,
                ' robot_name:=',
                robot_name,
            ]
        ),
        value_type=str,
    )

    # 공용 Nav2 설정의 프레임 자리표시자를 현재 로봇 이름으로 바꾼다.
    configured_nav2_params = ReplaceString(
        source_file=nav2_params,
        replacements={'<robot_name>': robot_name},
    )

    # URDF TF와 joint_states를 현재 로봇 네임스페이스에 발행한다.
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=robot_name,
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'frame_prefix': ParameterValue(
                    [robot_name, '/'], value_type=str
                ),
                'use_sim_time': use_sim_time,
            }
        ],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
    )

    # spawn_entity.py가 Gazebo 서비스를 기다린 뒤 고유 이름과 좌표로 생성한다.
    # 지연 실행하면 다음 로봇의 Launch 값이 섞일 수 있으므로 즉시 시작한다.
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        namespace=robot_name,
        name='spawn_entity',
        arguments=[
            '-entity',
            robot_name,
            '-topic',
            'robot_description',
            '-x',
            spawn_x,
            '-y',
            spawn_y,
            '-z',
            spawn_z,
            '-Y',
            spawn_yaw,
        ],
        output='screen',
    )

    # 전역 /map과 현재 로봇의 scan·odom을 사용해 위치를 추정한다.
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        namespace=robot_name,
        name='amcl',
        output='screen',
        parameters=[
            amcl_params,
            {
                'use_sim_time': use_sim_time,
                'global_frame_id': 'map',
                'odom_frame_id': ParameterValue(
                    [robot_name, '/odom'], value_type=str
                ),
                'base_frame_id': ParameterValue(
                    [robot_name, '/base_footprint'], value_type=str
                ),
                'scan_topic': 'scan',
                'set_initial_pose': True,
                'initial_pose.x': ParameterValue(spawn_x, value_type=float),
                'initial_pose.y': ParameterValue(spawn_y, value_type=float),
                'initial_pose.z': 0.0,
                'initial_pose.yaw': ParameterValue(
                    spawn_yaw, value_type=float
                ),
            },
        ],
        remappings=[
            ('map', '/map'),
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static'),
        ],
    )

    amcl_lifecycle = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        namespace=robot_name,
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[
            {
                'autostart': autostart,
                'node_names': ['amcl'],
                'use_sim_time': use_sim_time,
            }
        ],
    )

    # 공식 Nav2 Navigation Launch를 현재 로봇 네임스페이스로 실행한다.
    navigation = GroupAction(
        actions=[
            PushRosNamespace(robot_name),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        nav2_share, 'launch', 'navigation_launch.py'
                    )
                ),
                launch_arguments={
                    'namespace': robot_name,
                    'params_file': configured_nav2_params,
                    'use_sim_time': use_sim_time,
                    'autostart': autostart,
                    'use_composition': 'False',
                    'use_respawn': 'False',
                }.items(),
            ),
        ]
    )

    # 동일한 배터리 코드를 네임스페이스별로 한 번씩 실행한다.
    charging_state = Node(
        package=package_name,
        executable='charging_state',
        namespace=robot_name,
        name='charging_state',
        output='screen',
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'charger_x': ParameterValue(charger_x, value_type=float),
                'charger_y': ParameterValue(charger_y, value_type=float),
                'charger_yaw': ParameterValue(charger_yaw, value_type=float),
            }
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument('robot_name'),
            DeclareLaunchArgument('spawn_x'),
            DeclareLaunchArgument('spawn_y'),
            DeclareLaunchArgument('spawn_z', default_value='0.25'),
            DeclareLaunchArgument('spawn_yaw', default_value='0.0'),
            DeclareLaunchArgument('charger_x'),
            DeclareLaunchArgument('charger_y'),
            DeclareLaunchArgument('charger_yaw', default_value='0.0'),
            DeclareLaunchArgument('use_sim_time', default_value='true'),
            DeclareLaunchArgument('autostart', default_value='true'),
            robot_state_publisher,
            spawn_robot,
            amcl,
            amcl_lifecycle,
            navigation,
            charging_state,
        ]
    )
