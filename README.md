# Mobile Robot restaurant Simulation

#### English | [Korean](README.ko.md)

![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-11-orange)

> This repository is created for the purpose of learning ROS 2 and Gazebo simulation.

This project is designed to verify the driving performance and sensor operations of a mobile service robot within a cafe/restaurant environment. It is fully containerized using Docker, allowing you to run the simulation in an identical development environment without requiring a native ROS 2 installation.

---

## 🚧 Project Status

### Roadmap

- [x] Mobile Robot URDF Modeling
- [x] LiDAR Sensor Integration
- [x] Differential Drive Configuration
- [x] Simple Restaurant Environment
- [x] Gazebo Simulation Launch
- [X] SLAM Mapping
- [ ] AMCL Localization
- [ ] Nav2 Integration
- [ ] Waypoint Navigation
- [ ] Autonomous Serving Scenario
- [ ] RViz Visualization

---

## Preview

### Mobile Robot Model
<img width="1280" height="688" alt="Service robot in an empty world" src="https://github.com/user-attachments/assets/7acf06bd-3825-44f7-9a45-ec2eab9c51fa" />

<p align="center"><i>Fig1. servi_model.urdf spawned in an empty world</i></p>

### Restaurant Simulation Environment
<img width="1135" height="632" alt="Service robot in the restaurant" src="https://github.com/user-attachments/assets/75729a63-e1d2-4441-9135-0f9ffe96fb54" />

<p align="center"><i>Fig2. Mobile robot operating within the Gazebo simple restaurant environment</i></p>

---

## Overview

### Features
* Simulation environment based on ROS 2 Humble
* Gazebo Cafe World implementation
* Mobile robot URDF modeling
* 2D LiDAR sensor simulation
* Differential Drive kinematic model application
* Docker-based development environment support

---

## Simulation Components

| Component | Description |
| :--- | :--- |
| **Robot Model** | Mobile Service Robot |
| **Sensor** | 2D LiDAR |
| **Drive System** | Differential Drive |
| **Environment** | Simple Restaurant |
| **Simulator** | Gazebo Classic |
| **Middleware** | ROS 2 Humble |

---

## Project Structure

```text
Gazebo-Simulation/
├── docker-compose.yml
├── Dockerfile
├── README.md
└── ros2_gazebo_ws/
    └── src/
        └── my_robot_package/
            ├── launch/
            │   ├── localization.launch.py
            │   ├── map_server.launch.py
            │   ├── navigation.launch.py
            │   └── spawn_servi.launch.py
            ├── config/
            │   ├── amcl_params.yaml
            │   └── nav2_params.yaml
            ├── maps/
            │   ├── restaurant_map.pgm
            │   └── restaurant_map.yaml
            ├── models/
            │   ├── chair/
            │   ├── counter/
            │   ├── table/
            │   └── table_set/
            ├── urdf/
            │   └── servi_model.urdf
            ├── worlds/
            │   └── simple_restaurant.world
            ├── package.xml
            └── setup.py
```

---

## Requirements

### Host Environment
* Docker Desktop
* Docker Compose

### Simulation Environment
* Ubuntu 22.04
* ROS 2 Humble
* Gazebo 11
* RViz2

---

# How to Use

## 1. Clone Repository

```bash
git clone https://github.com/seonghun00/Gazebo-Simul.git
cd Gazebo-Simul
```

## 2. Start XLaunch (For Windows Host)

To enable the Gazebo GUI when running via Docker on a Windows host environment, configure XLaunch with the following settings:

1. Select **Multiple Windows**
2. Set **Display Number** → `0`
3. Select **Start No Client**
4. Check **Disable Access Control**
5. Click **Finish**

## 3. Start Docker Environment

```bash
# Start the container in detached mode
docker compose up -d

# Attach to the simulation container shell
docker compose exec robot-sim bash
```

## 4. Build Workspace

Inside the Docker container terminal, execute the following commands to build the ROS 2 workspace:

```bash
cd /workspace/ros2_gazebo_ws

# Clean up previous build artifacts if any
rm -rf build install log

# Build the specific package
colcon build --packages-select my_robot_package

# Source the workspace environment
source install/setup.bash
```

---

# Run Simulation

## 1. Empty World (Robot Model Verification)

This step verifies whether the URDF model loads correctly without any environmental obstacles.

### Terminal 1 (Launch Gazebo Server)
```bash
ros2 launch gazebo_ros gazebo.launch.py
```

### Terminal 2 (Spawn Robot Entity)
```bash
cd /workspace/ros2_gazebo_ws

ros2 run gazebo_ros spawn_entity.py \
  -entity mobile_robot \
  -file src/my_robot_package/urdf/servi_model.urdf
```
*You can verify the URDF structure and visual appearance of the mobile robot model spawned in the empty Gazebo world.*

---

## 2. Restaurant Simulation

This step launches the full integrated simulation setup including both the custom restaurant environment and the mobile robot.

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```
*Upon execution, Gazebo will open up displaying the simple restaurant world with the mobile service robot automatically spawned at its initial position.*

---

# Create a Map with SLAM

SLAM creates a map from `/scan` and `/odom`. Run each command in a separate
container terminal. Do not run localization or Nav2 while creating a map.

If a terminal cannot find `my_robot_package`, run:

```bash
source /workspace/ros2_gazebo_ws/install/setup.bash
```

## Terminal 1: Start Gazebo and the Robot

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

Wait until the robot appears in the restaurant.

## Terminal 2: Start SLAM

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

Keep this terminal running until the map is saved.

## Terminal 3: Start RViz

```bash
rviz2
```

Use these RViz settings:

| Display | Setting |
| :--- | :--- |
| Fixed Frame | `map` |
| Map | Topic `/map`, Durability `Transient Local` |
| LaserScan | Topic `/scan`, Reliability `Best Effort` |

## Terminal 4: Drive the Robot

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

Drive slowly through every aisle. Rotate slowly near the starting point and revisit
mapped areas to improve the result.

## Terminal 5: Save the Map

```bash
ros2 run nav2_map_server map_saver_cli \
  -f /workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam
```

This creates:

```text
restaurant_map_slam.pgm
restaurant_map_slam.yaml
```

Check the files, then stop all terminals with `Ctrl+C`.

```bash
ls -lh /workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam.*
```

# Run Localization with the Existing Map

Stop SLAM before starting localization.

## Terminal 1: Gazebo and the Robot

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

## Terminal 2: Map Server and AMCL

```bash
ros2 launch my_robot_package localization.launch.py
```

To use the newly created map instead of the default map:

```bash
ros2 launch my_robot_package localization.launch.py \
  map:=/workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam.yaml
```

## Terminal 3: RViz

```bash
rviz2
```

Set the fixed frame to `map`. Set `/map` to `Transient Local` and `/scan` to
`Best Effort`. Use **2D Pose Estimate** to mark the robot's position and direction.

---

© 2026 Seong-hun Bae.
