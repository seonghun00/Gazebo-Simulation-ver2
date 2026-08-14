"""식당 Gazebo 시뮬레이션을 열고 Servi 로봇 한 대를 생성하는 Launch 파일.

simple_restaurant.world와 servi_model.urdf를 불러온 뒤 다음 구성요소를 함께
실행한다.

* robot_state_publisher: URDF의 링크 관계를 /tf와 /tf_static으로 발행한다.
* spawn_entity.py: robot_description을 읽어 충전소 좌표에 로봇을 생성한다.
* charging_state: serving_control이 보내는 /servi_1/operation_state를 받아
  배터리를 계산하고 /servi_1/battery_percentage 등의 상태 토픽을 발행한다.

배터리 노드가 0%로 종료되면 이 Launch도 Gazebo를 포함한 실행 구성을
종료한다. 현재는 단일 로봇용 구조이며, Fleet 범용화 전의 기본 실행 파일이다.
"""

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
    """Gazebo, 로봇 스폰, TF 발행, 배터리 노드를 하나의 실행 구성으로 만든다."""
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

    # 식당 World와 ROS 연동 플러그인을 포함해 Gazebo Classic을 실행한다.
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

    # URDF 링크들의 고정·이동 좌표 변환을 /tf와 /tf_static으로 발행한다.
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

    # Gazebo가 준비될 때까지 기다린 후 로봇을 충전소 좌표에 생성한다.
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

    # 작업·충전 상태를 받아 가상 배터리 잔량과 경고 토픽을 발행한다.
    charging_state = Node(
        package=package_name,
        executable='charging_state',
        name='charging_state_servi_1',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    # 배터리 노드 종료를 전체 시뮬레이션 종료 요청으로 처리한다.
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
