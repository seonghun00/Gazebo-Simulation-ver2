# 모바일 로봇 간이 레스토랑 시뮬레이션

#### [English](README.md) | 한국어

![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-11-orange)

> ROS 2와 Gazebo 학습을 위한 모바일 서비스 로봇 시뮬레이션 프로젝트입니다.

카페·레스토랑 환경에서 서비스 로봇의 센서, SLAM, 위치 추정, 자율주행과
서빙 시나리오를 검증합니다. Docker 기반이므로 호스트에 ROS 2를 직접
설치하지 않고 동일한 환경에서 실행할 수 있습니다.

## 🚧 프로젝트 상태

### 로드맵

- [x] 모바일 로봇 URDF 모델링
- [x] LiDAR 센서 연동
- [x] 차동 구동 시스템 설정
- [x] 간이 레스토랑 월드 생성
- [x] Gazebo 시뮬레이션 Launch
- [x] SLAM 지도 생성
- [x] AMCL 위치 추정
- [x] Nav2 내비게이션
- [x] 경유지 주행
- [x] 자율 서빙 시나리오
- [x] RViz 시각화
- [x] YAML 기반 2대 로봇 Fleet 기본 배정
- [ ] 동시 작업과 교통·교착 관리

## 미리보기

### 모바일 로봇 모델

<img width="1280" height="688" alt="빈 월드에 생성된 서비스 로봇" src="https://github.com/user-attachments/assets/4669417f-c91b-45aa-be82-97bd5f58ad8b" />

<p align="center"><i>Fig1. 빈 월드에서 생성된 servi_model.urdf</i></p>

### 레스토랑 시뮬레이션 환경

<img width="1913" height="1020" alt="레스토랑 환경의 서비스 로봇" src="https://github.com/user-attachments/assets/7ea82b5c-6883-4a75-aac8-11a2785a5b0b" />

<p align="center"><i>Fig2. Gazebo 간이 레스토랑 환경에서 동작하는 모바일 로봇</i></p>

### SLAM 맵핑

<img width="1913" height="904" alt="SLAM 중간과정" src="https://github.com/user-attachments/assets/ebdab7c6-e6c5-495f-ac02-fdf668800c6e" />

<p align="center"><i>Fig3. 간이 레스토랑 환경에서 SLAM 지도를 생성하는 모습</i></p>

### 단일 로봇 자율주행 결과 (.mp4)

https://github.com/user-attachments/assets/ae2cbac7-f8ef-4683-aa78-82b2f2b886a5

<p align="center"><i>Fig4. 충전 스테이션에서 주방 카운터와 4번 테이블을 거쳐 충전소로 복귀하는 자율주행</i></p>

## 주요 구성

| 구성 요소 | 내용 |
| :--- | :--- |
| 로봇 | 차동구동 모바일 서비스 로봇 |
| 센서 | 2D LiDAR, 바퀴 오도메트리 |
| 환경 | Gazebo Classic 간이 레스토랑 |
| 지도·위치 추정 | SLAM Toolbox, Nav2 Map Server, AMCL |
| 자율주행 | Nav2 Planner, Controller, Costmap |
| 개발 환경 | Ubuntu 22.04, ROS 2 Humble, Docker |

## 주요 폴더

```text
ros2_gazebo_ws/src/my_robot_package/
├── launch/                 # Gazebo, Localization, Nav2 Launch
├── config/
│   ├── amcl_params.yaml    # AMCL 위치 추정 설정
│   ├── nav2_params.yaml    # Nav2 주행 설정
│   └── locations.yaml      # 테이블·주방·충전소 목적지
├── maps/                   # restaurant_map_slam 지도
├── models/                 # 테이블, 의자, 카운터 모델
├── my_robot_package/       # 서빙 제어와 배터리 노드
├── urdf/servi_model.urdf   # 로봇 모델과 Gazebo 플러그인
└── worlds/simple_restaurant.world
```

## 처음 한 번 설정하기

### 1. 저장소와 컨테이너 준비

```bash
git clone https://github.com/seonghun00/Gazebo-Simulation.git
cd Gazebo-Simulation
docker compose up -d
docker compose exec robot-sim bash
```

Windows에서 Gazebo GUI를 사용할 경우 XLaunch를 실행하고 다음 항목을 선택합니다.

```text
Multiple Windows → Display Number 0 → Start No Client
→ Disable Access Control → Finish
```

### 2. 워크스페이스 빌드

컨테이너 안에서 실행합니다.

```bash
cd /workspace/ros2_gazebo_ws
colcon build --packages-select my_robot_package
source install/setup.bash
```

이후 명령은 각각 별도의 컨테이너 터미널 또는 tmux 창에서 실행합니다. 새 터미널을
열 때마다 다음 환경 설정이 필요합니다.

```bash
cd /workspace/ros2_gazebo_ws
source install/setup.bash
```

## 1. SLAM으로 지도 만들기

식당 구조가 바뀌었거나 지도가 없을 때만 실행합니다. SLAM 중에는 AMCL과 Nav2를
동시에 실행하지 않습니다.

### 터미널 1: Gazebo와 로봇

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

### 터미널 2: SLAM

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

### 터미널 3: RViz

```bash
rviz2
```

RViz는 다음처럼 설정합니다. 같은 설정을 이후 Nav2에서도 사용합니다.

| 항목 | 설정 |
| :--- | :--- |
| Fixed Frame | `map` |
| Map | `/map`, Durability `Transient Local` |
| LaserScan | `/scan`, Reliability `Best Effort` |

### 터미널 4: 로봇 조종

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

통로 전체를 천천히 주행하고 같은 구역을 다시 방문하면 지도가 더 안정적으로
완성됩니다.

### 지도 저장

지도가 완성되면 새 터미널에서 실행합니다.

```bash
ros2 run nav2_map_server map_saver_cli \
  -f /workspace/ros2_gazebo_ws/src/my_robot_package/maps/restaurant_map_slam
```

다음 두 파일이 생성됩니다.

```text
restaurant_map_slam.pgm
restaurant_map_slam.yaml
```

## 2. 저장된 지도로 Nav2 실행하기

다음 네 명령을 각각 별도 터미널에서 계속 실행합니다.

### 터미널 1: Gazebo와 로봇

```bash
ros2 launch my_robot_package spawn_servi.launch.py
```

### 터미널 2: Map Server와 AMCL

```bash
ros2 launch my_robot_package localization.launch.py
```

### 터미널 3: Nav2

```bash
ros2 launch my_robot_package navigation.launch.py
```

### 터미널 4: RViz

```bash
rviz2
```

앞에서 설명한 RViz 공통 설정을 적용하고 **2D Goal Pose**로 목적지와 도착 방향을
지정합니다. AMCL은 Nav2가 주행하는 동안 계속 실행되어야 합니다. 지도와 로봇이
맞지 않을 때만 **2D Pose Estimate**로 초기 위치를 보정합니다.

## 3. 테이블과 서비스 위치 저장하기

테이블 중심이 아니라 로봇이 장애물과 충돌하지 않고 멈출 수 있는 위치를 저장합니다.

### 좌표 측정

다음 명령을 먼저 실행한 뒤 RViz의 **2D Goal Pose**로 정차 위치와 방향을
지정합니다.

```bash
ros2 topic echo /goal_pose --once
```

출력된 `position.x`, `position.y`와 목표 방향의 yaw를 기록합니다.

| 방향 | yaw |
| :--- | ---: |
| `+x` | `0.0` |
| `+y` | `1.5708` |
| `-x` | `3.1416` |
| `-y` | `-1.5708` |

### `locations.yaml` 수정

`config/locations.yaml`의 기존 항목을 측정한 값으로 바꿉니다.

```yaml
frame_id: map

locations:
  table_1: {x: -1.28, y: 2.56, yaw: 1.5708}
  kitchen_pickup: {x: -6.78, y: -0.47, yaw: 3.1416}
  charging_station: {x: -7.12, y: -4.99, yaw: 0.0}
```

`table_2`부터 `table_7`까지도 파일에 이미 정의된 같은 형식으로 수정합니다. 변경된
설정 파일을 install 공간에 반영하려면 다시 빌드합니다.

```bash
cd /workspace/ros2_gazebo_ws
colcon build --packages-select my_robot_package
source install/setup.bash
```

## 4. 저장한 좌표로 서빙하기

### 서빙 제어 실행

Gazebo, Localization, Nav2가 실행 중인 상태에서 시작합니다.

```bash
ros2 run my_robot_package serving_control
```

| 명령 | 동작 |
| :--- | :--- |
| `b` | 주방 음식 수령대로 이동 |
| `1` - `7` | 선택한 테이블로 이동 |
| `bb` | 충전 스테이션으로 복귀 |
| `q` | 제어 노드 종료 |

입력한 명령은 `locations.yaml`의 같은 이름을 가진 좌표로 변환됩니다. 예를 들어
`3`은 `table_3`, `b`는 `kitchen_pickup`, `bb`는 `charging_station`을 사용합니다.

### 서빙 실행 예시

1. 로봇이 충전소에서 대기하는 동안 음식이 완성되면 `b`를 입력합니다.
2. 로봇이 `kitchen_pickup`에 도착하면 음식을 적재합니다.
3. 배달할 테이블 번호가 3번이면 `3`을 입력해 `table_3`으로 이동합니다.
4. 손님이 음식을 가져간 뒤 `bb`를 입력하면 충전 스테이션으로 복귀합니다.

```text
b  → kitchen_pickup
3  → table_3
bb → charging_station
```

각 이동이 성공하거나 실패한 뒤에 다음 명령을 입력할 수 있습니다. 다른 테이블도
`1`부터 `7`까지 같은 방식으로 선택합니다.

### 배터리 동작

배터리는 첫 작업부터 10초마다 1% 감소하고, 충전소 도착 후 5초마다 1% 충전됩니다.
50%, 40%, 30%, 20%, 10%에서 같은 명령 터미널에 경고가 출력되며, 10%가 되면
`bb`로 즉시 복귀해야 합니다.

잔량을 별도로 확인하려면 다음 토픽을 사용합니다.

```bash
ros2 topic echo /servi_1/battery_percentage
```

## 5. 로봇 2대 Fleet 실행

`config/robots.yaml`에는 로봇 이름, Gazebo 시작 위치와 전용 충전소 좌표가
저장됩니다. `spawn` 좌표는 Gazebo 생성 위치와 AMCL 초기 위치에 함께 사용됩니다.

### 터미널 1: 공용 환경과 로봇 2대

```bash
ros2 launch my_robot_package fleet_bringup.launch.py
```

Gazebo와 Map Server는 각각 한 번만 실행하고, `robots.yaml`에 등록된 로봇마다
URDF, AMCL, Nav2와 배터리 노드를 별도 네임스페이스로 실행합니다.

### 터미널 2: Fleet 명령

```bash
ros2 run my_robot_package fleet_manager
```

| 명령 | 동작 |
| :--- | :--- |
| `b` | 거리·배터리·완료 작업 수를 비교해 로봇 한 대를 주방으로 배정 |
| `1` - `7` | 배정된 로봇을 선택한 테이블로 이동 |
| `bb` | 배정된 로봇을 자신의 충전소로 복귀 |
| `status` | 모든 로봇의 상태, 배터리와 완료 작업 수 확인 |
| `q` | Fleet Manager 종료 |

현재 단계는 한 번에 한 건을 배정하는 기본 Fleet입니다. 로봇별 토픽과 Nav2는
완전히 분리되어 있으며, 다음 단계에서 여러 주문의 동시 배정과 교통 관리를
추가할 수 있습니다.

로봇을 추가할 때는 Python이나 Launch 코드를 복사하지 않고 `robots.yaml`에
새 항목만 추가한 뒤 다시 빌드합니다.

---

© 2026 Seong-hun Bae.
