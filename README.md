# Mobile Robot Restaurant Simulation

#### English | [한국어](README.ko.md)

![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-11-orange)

> A mobile service robot simulation project for learning ROS 2 and Gazebo.

This project validates sensing, SLAM, localization, autonomous navigation, and
serving scenarios in a cafe or restaurant environment. The Docker-based setup
provides a consistent environment without requiring a native ROS 2 installation.

## 🚧 Project Status

### Roadmap

- [x] Mobile robot URDF modeling
- [x] LiDAR sensor integration
- [x] Differential drive configuration
- [x] Simple restaurant world
- [x] Gazebo simulation launch
- [x] SLAM mapping
- [x] AMCL localization
- [x] Nav2 navigation
- [x] Waypoint navigation
- [x] Autonomous serving scenario
- [x] RViz visualization
- [ ] Fleet management for multiple robots

## Preview

### Mobile Robot Model

<img width="1280" height="688" alt="Service robot spawned in an empty world" src="https://github.com/user-attachments/assets/4669417f-c91b-45aa-be82-97bd5f58ad8b" />

<p align="center"><i>Fig1. servi_model.urdf spawned in an empty world</i></p>

### Restaurant Simulation Environment

<img width="1913" height="1020" alt="Service robot in the restaurant environment" src="https://github.com/user-attachments/assets/7ea82b5c-6883-4a75-aac8-11a2785a5b0b" />

<p align="center"><i>Fig2. Mobile robot operating in the Gazebo restaurant environment</i></p>

### SLAM Mapping

<img width="1913" height="904" alt="SLAM 중간과정" src="https://github.com/user-attachments/assets/179b8cac-9fdb-4973-9ae7-2892c2a0cfcd" />

<p align="center"><i>Fig3. Mobile robot creating a SLAM map of the restaurant</i></p>

### Single-Robot Autonomous Navigation (.mp4)

https://github.com/user-attachments/assets/b09d8b21-9ca7-4926-a3cb-e7b876ed6227

<p align="center"><i>Fig4. Autonomous navigation from the charging station to the kitchen counter, Table 4, and back</i></p>

## Main Components

| Component | Details |
| :--- | :--- |
| Robot | Differential-drive mobile service robot |
| Sensors | 2D LiDAR and wheel odometry |
| Environment | Gazebo Classic simple restaurant |
| Mapping and localization | SLAM Toolbox, Nav2 Map Server, AMCL |
| Navigation | Nav2 Planner, Controller, and Costmap |
| Development environment | Ubuntu 22.04, ROS 2 Humble, Docker |

## Main Directories

```text
ros2_gazebo_ws/src/my_robot_package/
├── launch/                 # Gazebo, localization, and Nav2 launch files
├── config/
│   ├── amcl_params.yaml    # AMCL localization settings
│   ├── nav2_params.yaml    # Nav2 navigation settings
│   └── locations.yaml      # Table, kitchen, and charging destinations
├── maps/                   # restaurant_map_slam map files
├── models/                 # Table, chair, and counter models
├── my_robot_package/       # Serving controller and battery nodes
├── urdf/servi_model.urdf   # Robot model and Gazebo plugins
└── worlds/simple_restaurant.world
```

## One-Time Setup

### 1. Prepare the Repository and Container

```bash
git clone https://github.com/seonghun00/Gazebo-Simulation.git
cd Gazebo-Simulation
docker compose up -d
docker compose exec robot-sim bash
```

On a Windows host, start XLaunch with the following options to display Gazebo.

```text
Multiple Windows → Display Number 0 → Start No Client
→ Disable Access Control → Finish
```

### 2. Build the Workspace

Run these commands inside the container.

```bash
cd /workspace/ros2_gazebo_ws
colcon build --packages-select my_robot_package
source install/setup.bash
```

Run the commands below in separate container terminals or tmux panes. Initialize
every new terminal before running ROS 2 commands.

```bash
cd /workspace/ros2_gazebo_ws
source install/setup.bash
```

## 1. Create a Map with SLAM

Run this section only when no map exists or the restaurant layout has changed.
Do not run AMCL or Nav2 while mapping.

### Terminal 1: Gazebo and Robot

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

### Terminal 2: SLAM

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

### Terminal 3: RViz

```bash
rviz2
```

Use these RViz settings. The same settings apply when running Nav2.

| Item | Setting |
| :--- | :--- |
| Fixed Frame | `map` |
| Map | `/map`, Durability `Transient Local` |
| LaserScan | `/scan`, Reliability `Best Effort` |

### Terminal 4: Teleoperation

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

Drive slowly through every aisle and revisit mapped areas to improve map quality.

### Save the Map

When the map is complete, run this command in a new terminal.

```bash
ros2 run nav2_map_server map_saver_cli \
  -f /workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam
```

This creates the following files:

```text
restaurant_map_slam.pgm
restaurant_map_slam.yaml
```

## 2. Run Nav2 with the Saved Map

Keep each of the following commands running in a separate terminal.

### Terminal 1: Gazebo and Robot

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

### Terminal 2: Map Server and AMCL

```bash
ros2 launch my_robot_package localization.launch.py
```

### Terminal 3: Nav2

```bash
ros2 launch my_robot_package navigation.launch.py
```

### Terminal 4: RViz

```bash
rviz2
```

Apply the common RViz settings above, then use **2D Goal Pose** to select a
destination and arrival heading. Keep AMCL running while Nav2 is active. Use
**2D Pose Estimate** only when the robot and map are not aligned.

## 3. Save Table and Service Locations

Save a collision-free stopping pose in front of each destination rather than
the center of a table or counter.

### Measure a Pose

Run this command first, then select a stopping pose and heading with RViz
**2D Goal Pose**.

```bash
ros2 topic echo /goal_pose --once
```

Record `position.x`, `position.y`, and the yaw for the desired heading.

| Heading | yaw |
| :--- | ---: |
| `+x` | `0.0` |
| `+y` | `1.5708` |
| `-x` | `3.1416` |
| `-y` | `-1.5708` |

### Update `locations.yaml`

Replace the existing values in `config/locations.yaml` with the measured poses.

```yaml
frame_id: map

locations:
  table_1: {x: -1.28, y: 2.56, yaw: 1.5708}
  kitchen_pickup: {x: -6.78, y: -0.47, yaw: 3.1416}
  charging_station: {x: -7.12, y: -4.99, yaw: 0.0}
```

Update the existing `table_2` through `table_7` entries in the same format.
Rebuild the package to copy the changed configuration into the install space.

```bash
cd /workspace/ros2_gazebo_ws
colcon build --packages-select my_robot_package
source install/setup.bash
```

## 4. Serve with the Saved Locations

### Start the Serving Controller

Start the controller while Gazebo, localization, and Nav2 are running.

```bash
ros2 run my_robot_package serving_control
```

| Command | Action |
| :--- | :--- |
| `b` | Move to the kitchen pickup counter |
| `1` - `7` | Move to the selected table |
| `bb` | Return to the charging station |
| `q` | Stop the controller |

Each command is converted to the matching pose in `locations.yaml`. For example,
`3` uses `table_3`, `b` uses `kitchen_pickup`, and `bb` uses
`charging_station`.

### Example Serving Sequence

1. Enter `b` when the food is ready while the robot is waiting at the charger.
2. Load the food after the robot reaches `kitchen_pickup`.
3. Enter `3` to deliver the food to `table_3`.
4. Enter `bb` after the customer takes the food to return to the charger.

```text
b  → kitchen_pickup
3  → table_3
bb → charging_station
```

Enter the next command after the current navigation succeeds or fails. Select
the other tables in the same way with commands `1` through `7`.

### Battery Behavior

The battery decreases by 1% every 10 seconds after the first task and charges by
1% every 5 seconds after reaching the charging station. Warnings appear in the
same command terminal at 50%, 40%, 30%, 20%, and 10%. Return immediately with
`bb` at 10%.

Use this topic for an optional battery check:

```bash
ros2 topic echo /servi_1/battery_percentage
```

---

© 2026 Seong-hun Bae.
