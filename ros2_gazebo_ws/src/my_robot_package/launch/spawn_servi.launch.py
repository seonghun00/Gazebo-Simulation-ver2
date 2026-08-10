from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    package_name = "my_robot_package"
    pkg_share = get_package_share_directory(package_name)

    world_file = os.path.join(pkg_share, "worlds", "simple_restaurant.world")
    urdf_file = os.path.join(pkg_share, "urdf", "servi_model.urdf")

    with open(urdf_file, "r") as f:
        robot_description = f.read()

    models_path = os.path.join(pkg_share, "models")

    return LaunchDescription([
        # 환경 변수 설정
        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=f"{models_path}:${{GAZEBO_MODEL_PATH:-}}"
        ),
        SetEnvironmentVariable(name='GAZEBO_VERBOSE', value='1'),
        SetEnvironmentVariable(name='LIBGL_ALWAYS_SOFTWARE', value='1'),

        # Gazebo 실행
        ExecuteProcess(
            cmd=[
    "gazebo",
    "--verbose",
    world_file,
    "-s", "libgazebo_ros_init.so",
    "-s", "libgazebo_ros_factory.so"
],
            output="screen",
        ),

        # robot_state_publisher
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}]
        ),

        # Spawn Entity - Gazebo가 충분히 뜰 때까지 8초 대기
        TimerAction(
            period=8.0,  # 8초 대기 (필요시 10~12초로 늘려라)
            actions=[
                Node(
                    package="gazebo_ros",
                    executable="spawn_entity.py",
                    arguments=[
                        '-entity', 'servi',
                        '-topic', 'robot_description',
                        # 스폰 지점 설정
                        '-x', '-3.5',   # 카운터 앞 위치
                        '-y', '0.0',
                        '-z', '0.25',
                        '-Y', '0.0'
                    ],
                    output="screen"
                )
            ]
        ),
    ])
