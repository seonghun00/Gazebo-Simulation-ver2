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
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),

        # models 폴더는 아래 방식으로 설치 (가장 안정적)
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
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'charging_state = my_robot_package.charging_state:main',
            'serving_control = my_robot_package.serving_control:main',
        ],
    },
)
