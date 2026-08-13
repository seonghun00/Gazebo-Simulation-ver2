# 모바일 로봇 간이 레스토랑 시뮬레이션

#### [English](README.md) | 한국어

![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-11-orange)

> 본 저장소는 ROS 2 및 Gazebo 학습을 목적으로 만들어진 repo 입니다. 

본 프로젝트는 카페, 레스토랑 환경에서 서비스 로봇의 주행 및 센서 동작을 검증하기 위해 제작되었습니다. Docker 기반으로 구성하여 별도의 ROS 2 설치 없이 동일한 개발 환경에서 실행할 수 있습니다.

## 🚧 프로젝트 상태

### 로드맵

- [x] 모바일 로봇 URDF 모델링
- [x] LiDAR 센서 연동
- [x] 차동 구동 시스템 설정
- [x] 간이 레스토랑 월드 생성
- [x] Gazebo 시뮬레이션 실행 (Launch)
- [x] SLAM 지도 생성
- [x] AMCL 위치 추정
- [x] Nav2 내비게이션 적용
- [X] 경유지 주행 내비게이션
- [X] 자율 서빙 시나리오 구현
- [x] RViz 시각화
- [ ] 2대 이상 Fleet 관리

## 미리보기

### 모바일 로봇 모델
<img width="1280" height="688" alt="image" src="https://github.com/user-attachments/assets/4669417f-c91b-45aa-be82-97bd5f58ad8b" />   

<p align="center"><i>Fig1. 빈 월드에서 생성된 servi_model.urdf</i></p>

### 레스토랑 시뮬레이션 환경
<img width="1913" height="1020" alt="image" src="https://github.com/user-attachments/assets/7ea82b5c-6883-4a75-aac8-11a2785a5b0b" />

<p align="center"><i>Fig2. Gazebo 간이 레스토랑 환경에서 동작하는 모바일 로봇</i></p>

### SLAM 맵핑
<img width="1912" height="767" alt="SLAM 중간과정" src="https://github.com/user-attachments/assets/4cb9bc90-7143-4ca4-ac37-d214f4e5926b" />

<p align="center"><i>Fig3. Gazebo 간이 레스토랑 환경에서 SLAM 맵핑 하는 모습</i></p>

---

## 개요

### 주요 기능
* ROS 2 Humble 기반 시뮬레이션 환경
* Gazebo Cafe World 구축
* 모바일 로봇 URDF 모델링
* LiDAR 센서 시뮬레이션
* Differential Drive 구동 모델 적용
* Docker 기반 개발 환경 제공

---

## 시뮬레이션 구성 요소

| 구성 요소 | 설명 |
|------------|------------|
| Robot Model | Mobile Service Robot |
| Sensor | 2D LiDAR |
| Drive System | Differential Drive |
| Environment | Simple Restaurant |
| Simulator | Gazebo Classic |
| Middleware | ROS 2 Humble |

---

## 폴더 구조
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

## 요구 사항

### 호스트 환경
* Docker Desktop
* Docker Compose

### 시뮬레이션 환경
* Ubuntu 22.04
* ROS 2 Humble
* Gazebo
* RViz2

---

# 사용 방법

## 1. 저장소 복제

```bash
git clone https://github.com/seonghun00/Gazebo-Simulation.git
cd Gazebo-Simulation
```

## 2. XLaunch 실행

Windows 환경에서 Gazebo GUI를 사용하기 위해 XLaunch를 실행합니다.

1. Multiple Windows 선택
2. Display Number → 0
3. Start No Client 선택
4. Disable Access Control 체크
5. Finish

## 3. Docker 환경 실행

```bash
docker compose up -d

docker compose exec robot-sim bash
```

## 4. 워크스페이스 빌드

```bash
cd /workspace/ros2_gazebo_ws

rm -rf build install log

colcon build --packages-select my_robot_package

source install/setup.bash
```

---

# 시뮬레이션 실행

## 1. 빈 월드에서 로봇 모델 확인

URDF 모델이 정상적으로 생성되는지 확인하기 위한 단계입니다.

### 터미널 1

```bash
ros2 launch gazebo_ros gazebo.launch.py
```

### 터미널 2

```bash
cd /workspace/ros2_gazebo_ws

ros2 run gazebo_ros spawn_entity.py \
  -entity mobile_robot \
  -file src/my_robot_package/urdf/servi_model.urdf
```

빈 Gazebo 환경에 로봇 모델만 생성하여 URDF 구조 및 외형을 확인할 수 있습니다.

---

## 2. 레스토랑 시뮬레이션

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

실행 후 Gazebo가 시작되며 간이 레스토랑 환경과 모바일 서비스 로봇이 함께 생성됩니다.

---

# SLAM으로 지도 생성하기

SLAM은 `/scan`과 `/odom`으로 지도를 생성합니다. 각 명령은 별도의 컨테이너
터미널에서 실행합니다. 지도 생성 중에는 Localization과 Nav2를 실행하지 마세요.

터미널에서 `my_robot_package`를 찾지 못하면 다음 명령을 실행합니다.

```bash
source /workspace/ros2_gazebo_ws/install/setup.bash
```

## 터미널 1: Gazebo와 로봇 실행

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

레스토랑에 로봇이 나타날 때까지 기다립니다.

## 터미널 2: SLAM 실행

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

지도를 저장할 때까지 이 터미널을 종료하지 마세요.

## 터미널 3: RViz 실행

```bash
rviz2
```

RViz를 다음과 같이 설정합니다.

| 항목 | 설정 |
| :--- | :--- |
| Fixed Frame | `map` |
| Map | Topic `/map`, Durability `Transient Local` |
| LaserScan | Topic `/scan`, Reliability `Best Effort` |

## 터미널 4: 로봇 조종

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

모든 통로를 천천히 주행합니다. 시작 위치에서 천천히 회전하고, 이미 작성한 구역을
다시 방문하면 지도가 더 정확해집니다.

## 터미널 5: 지도 저장

rviz2로 지도를 어느정도 선명하게 만들었다면 아래 명령어로 지도를 저장합니다.

```bash
ros2 run nav2_map_server map_saver_cli \
  -f /workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam
```

다음 두 파일이 생성됩니다.

```text
restaurant_map_slam.pgm
restaurant_map_slam.yaml
```

파일을 확인한 다음 모든 터미널을 `Ctrl+C`로 종료합니다.

```bash
ls -lh /workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam.*
```

# 기존 지도로 위치 추정 실행하기

SLAM을 종료한 후 실행합니다.

## 터미널 1: Gazebo와 로봇

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

## 터미널 2: 지도 서버와 AMCL

```bash
ros2 launch my_robot_package localization.launch.py
```

새로 만든 지도를 사용하려면 다음 명령을 대신 실행합니다.

```bash
ros2 launch my_robot_package localization.launch.py \
  map:=/workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam.yaml
```

## 터미널 3: RViz

```bash
rviz2
```

Fixed Frame은 `map`으로 설정합니다. `/map`은 `Transient Local`, `/scan`은
`Best Effort`로 설정합니다. AMCL은 설정된 시뮬레이션 시작 위치를 자동으로
사용합니다. 지도와 로봇이 맞지 않을 때만 **2D Pose Estimate**로 보정합니다.

# Nav2로 자율주행 실행하기

저장된 지도와 AMCL을 사용합니다. 각 명령은 별도의 터미널에서 계속 실행합니다.

## 터미널 1: Gazebo와 로봇

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

## 터미널 2: 지도 서버와 AMCL

```bash
ros2 launch my_robot_package localization.launch.py
```

## 터미널 3: Nav2

```bash
ros2 launch my_robot_package navigation.launch.py
```

## 터미널 4: RViz

```bash
rviz2
```

RViz에서 다음 순서로 설정합니다.

1. **Fixed Frame**을 `map`으로 설정합니다.
2. Map `/map`의 Durability를 `Transient Local`로 설정합니다.
3. LaserScan `/scan`의 Reliability를 `Best Effort`로 설정합니다.
4. 지도와 로봇 및 LaserScan이 일치하는지 확인합니다. 맞지 않을 때만
   **2D Pose Estimate**로 보정합니다.
5. **2D Goal Pose**로 목적지와 도착 방향을 지정합니다.

Nav2가 경로를 계획하고 주행하는 동안 AMCL을 계속 실행해야 합니다.

## Nav2 상태 확인

```bash
ros2 lifecycle get /map_server
ros2 action list | grep navigate_to_pose
ros2 run tf2_ros tf2_echo map base_footprint
```

`/map_server`는 `active`여야 하며, navigation action과 계속 갱신되는 TF가 보여야
합니다.

# 테이블과 서비스 위치 저장하기

테이블이나 카운터의 중심이 아니라, 로봇이 실제로 도착해서 멈출 위치를 저장합니다.

## 1. RViz에서 목표 시험

**2D Goal Pose**를 클릭하기 전에 다음 명령을 실행합니다.

```bash
ros2 topic echo /goal_pose --once
```

테이블 앞의 빈 공간을 클릭하고 화살표를 테이블 방향으로 드래그합니다. 로봇이 의자와
충돌하지 않고 도착하면 `position.x`, `position.y`와 도착 방향을 기록합니다.

| 방향 | yaw |
| :--- | ---: |
| 정면 `+x` | `0.0` |
| 왼쪽 `+y` | `1.5708` |
| 뒤쪽 `-x` | `3.1416` |
| 오른쪽 `-y` | `-1.5708` |

## 2. `locations.yaml` 작성

`ros2_gazebo_ws/src/my_robot_package/config/locations.yaml` 파일을 만듭니다.

```yaml
frame_id: map

locations:
  table_1: {x: 0.0, y: 0.0, yaw: 0.0}
  table_2: {x: 0.0, y: 0.0, yaw: 0.0}
  table_3: {x: 0.0, y: 0.0, yaw: 0.0}
  table_4: {x: 0.0, y: 0.0, yaw: 0.0}
  table_5: {x: 0.0, y: 0.0, yaw: 0.0}
  table_6: {x: 0.0, y: 0.0, yaw: 0.0}
  table_7: {x: 0.0, y: 0.0, yaw: 0.0}
  kitchen_pickup: {x: 0.0, y: 0.0, yaw: 0.0}
  charging_station: {x: 0.0, y: 0.0, yaw: 0.0}
```

`0.0`을 RViz에서 성공적으로 시험한 값으로 교체합니다. 1~7번 테이블, 주방 카운터,
충전 스테이션을 각각 같은 방법으로 시험합니다.

## 3. 저장 후 다시 빌드

```bash
cd /workspace/ros2_gazebo_ws
colcon build --packages-select my_robot_package
source install/setup.bash
```

## 4. 서빙 제어 노드 실행

Gazebo, Localization, Nav2를 먼저 실행한 다음 시작합니다.

```bash
ros2 run my_robot_package serving_control
```

명령을 입력하고 Enter를 누릅니다. 현재 이동이 성공하거나 실패한 뒤 다음 명령을
입력할 수 있습니다.

| 명령 | 목적지 |
| :--- | :--- |
| `b` | 주방 음식 수령대 |
| `1` - `7` | 선택한 테이블 |
| `bb` | 충전 스테이션 |
| `q` | 종료 |

## 배터리와 충전

`charging_state_servi_1` 노드는 `spawn_servi.launch.py`와 함께 자동으로
실행됩니다. 로봇은 충전 스테이션에서 배터리 100%로 시작하므로 서빙 명령을
받기 전에는 배터리가 감소하지 않습니다.

| 상태 | 배터리 동작 |
| :--- | :--- |
| `b` 또는 `1` - `7` 목표 수락 | 작업 시작: 10초마다 1% 감소 |
| `bb`로 충전 스테이션 도착 성공 | 충전 시작: 5초마다 1% 증가 |
| 배터리 100% 도달 | 충전을 멈추고 완충 메시지 출력 |
| 배터리 0% 도달 | 주행을 중단하고 시스템 종료 요청 |

배터리가 50%, 40%, 30%, 20%, 10%가 되면 `serving_control`을 실행한 명령
터미널에 경고가 바로 출력됩니다. 10% 경고가 나오면 즉시 `bb`를 입력해 충전
스테이션으로 복귀합니다.

```text
[BATTERY WARNING] 50% remaining.
[BATTERY WARNING] 40% remaining.
[BATTERY WARNING] 30% remaining.
[BATTERY WARNING] 20% remaining.
[CRITICAL BATTERY] 10% remaining. Enter "bb" now to return to the charging station.
[CHARGING COMPLETE] Battery is at 100%.
```

필요한 경우 다른 터미널에서 상태를 확인할 수 있습니다.

```bash
ros2 topic echo /servi_1/battery_percentage
ros2 topic echo /servi_1/is_charging
```

---
## 각 위치로 자율주행 하는 결과 영상 (충전스테이션 -> 주방카운터 -> 4번테이블 -> 충전복귀)

https://github.com/user-attachments/assets/ae2cbac7-f8ef-4683-aa78-82b2f2b886a5

---

© 2026 Seong-hun Bae.
