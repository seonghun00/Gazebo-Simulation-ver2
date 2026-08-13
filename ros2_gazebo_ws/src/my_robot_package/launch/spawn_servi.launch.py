import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    EmitEvent,
    ExecuteProcess,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node


def generate_launch_description():
    package_name = 'my_robot_package'
    package_share = get_package_share_directory(package_name)

    world_file = os.path.join(
        package_share,
        'worlds',
        'simple_restaurant.world',
    )
    urdf_file = os.path.join(package_share, 'urdf', 'servi_model.urdf')
    models_path = os.path.join(package_share, 'models')

    with open(urdf_file, 'r', encoding='utf-8') as file:
        robot_description = file.read()

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

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': True,
            }
        ],
    )

    spawn_robot = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                arguments=[
                    '-entity',
                    'servi',
                    '-topic',
                    'robot_description',
                    '-x',
                    '-7.12',
                    '-y',
                    '-4.988542',
                    '-z',
                    '0.25',
                    '-Y',
                    '0.0',
                ],
                output='screen',
            )
        ],
    )

    charging_state = Node(
        package=package_name,
        executable='charging_state',
        name='charging_state_servi_1',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    shutdown_on_empty_battery = RegisterEventHandler(
        OnProcessExit(
            target_action=charging_state,
            on_exit=[
                EmitEvent(
                    event=Shutdown(
                        reason='Servi battery monitor stopped or battery is empty.'
                    )
                )
            ],
        )
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable(
                name='GAZEBO_MODEL_PATH',
                value=f'{models_path}:${{GAZEBO_MODEL_PATH:-}}',
            ),
            SetEnvironmentVariable(name='GAZEBO_VERBOSE', value='1'),
            SetEnvironmentVariable(name='LIBGL_ALWAYS_SOFTWARE', value='1'),
            gazebo,
            robot_state_publisher,
            spawn_robot,
            charging_state,
            shutdown_on_empty_battery,
        ]
    )
