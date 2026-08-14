"""my_robot_package를 ROS 2 Python 패키지로 설치하기 위한 설정 파일.

Launch, 설정, 지도, URDF, World와 Gazebo 모델 파일을 install 디렉터리에
복사하고 charging_state와 serving_control을 ros2 run 명령으로 실행할 수
있도록 콘솔 실행 항목을 등록한다.
"""

import os
from glob import glob
from setuptools import setup

package_name = 'my_robot_package'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf*')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),

        # Gazebo가 model:// 이름으로 찾을 수 있도록 모델별 폴더를 설치한다.
        (os.path.join('share', package_name, 'models/chair'), glob('models/chair/*')),
        (os.path.join('share', package_name, 'models/counter'), glob('models/counter/*')),
        (os.path.join('share', package_name, 'models/table'), glob('models/table/*')),
        (os.path.join('share', package_name, 'models/table_set'), glob('models/table_set/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@email.com',
    description='Servi robot simulation and control',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'charging_state = my_robot_package.charging_state:main',
            'fleet_manager = my_robot_package.fleet_manager:main',
            'serving_control = my_robot_package.serving_control:main',
        ],
    },
)
