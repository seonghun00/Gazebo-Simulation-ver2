# ============================================================
# Dockerfile
# Purpose:
#   Windows 10 + Docker Desktop 환경에서
#   ROS2 Humble + Gazebo Classic + MuJoCo 3.6.0 + Python
#   실습 환경을 구성하기 위한 이미지 정의 파일
# ============================================================

FROM ubuntu:22.04

# ------------------------------------------------------------
# 1. 기본 환경 변수 설정
# ------------------------------------------------------------
# DEBIAN_FRONTEND=noninteractive:
#   Docker build 중 tzdata 같은 패키지가 대화형 질문을 하지 않게 함
#
# TZ=Asia/Seoul:
#   실습 로그 시간이 한국 시간 기준으로 보이도록 설정
# ------------------------------------------------------------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# ------------------------------------------------------------
# 2. 기본 패키지 설치
# ------------------------------------------------------------
# curl, gnupg, lsb-release:
#   ROS2 저장소 등록에 필요
#
# python3, python3-pip:
#   MuJoCo Python 실습에 필요
#
# git, vim, nano:
#   컨테이너 내부 간단한 파일 확인 및 수정용
#
# libgl1, libglib2.0-0, libx11-6 등:
#   Gazebo/MuJoCo GUI 실행 시 필요한 그래픽 관련 라이브러리
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    software-properties-common \
    build-essential \
    terminator \
    tree \
    git \
    vim \
    nano \
    wget \
	net-tools \
	iputils-ping \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 3. ROS2 apt 저장소 등록
# ------------------------------------------------------------
# ROS2 Humble은 Ubuntu 22.04에서 deb 패키지로 설치 가능
# ------------------------------------------------------------
RUN add-apt-repository universe

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg]\
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    > /etc/apt/sources.list.d/ros2.list

# ------------------------------------------------------------
# 4. ROS2 Humble + Gazebo 관련 패키지 설치
# ------------------------------------------------------------
# ros-humble-desktop:
#   ROS2 기본 도구, RViz2, 예제 등을 포함
#
# gazebo:
#   Gazebo Classic 실행 명령 제공
#
# ros-humble-gazebo-ros-pkgs:
#   Gazebo와 ROS2 연동 패키지
#
# python3-colcon-common-extensions:
#   ROS2 작업 공간(Workspace) 빌드를 위한 핵심 툴 (colcon build 명령어 제공)
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-desktop \
	ros-dev-tools \
    gazebo \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-tf2-tools \
    ros-humble-rqt \
    ros-humble-rqt-graph \
    python3-colcon-common-extensions \
	ros-humble-gazebo-ros2-control \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-controller-manager \
    ros-humble-joint-state-broadcaster \
    ros-humble-forward-command-controller \
	python3-rosdep \
	python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 5. SLAM / Nav2 / TurtleBot3 패키지 설치
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    ros-humble-slam-toolbox \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-msgs \
    ros-humble-turtlebot3-simulations \
	ros-humble-turtlebot3-teleop \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 6. MoveIt2 설치
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    ros-humble-moveit \
    ros-humble-moveit-setup-assistant \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 5. Python 패키지 설치
# ------------------------------------------------------------
# mujoco==3.6.0:
#   MuJoCo 3.6.0 Python binding
#
# numpy:
#   수치 계산
#
# matplotlib:
#   로그 분석 및 간단한 그래프
#
# pyyaml:
#   설정 파일 처리
# ------------------------------------------------------------
RUN python3 -m pip install --upgrade pip setuptools wheel

RUN python3 -m pip install \
    mujoco==3.6.0 \
    numpy \
    matplotlib \
	pandas \
    scipy \
	opencv-python \
	pyyaml

# ------------------------------------------------------------
# 8. rosdep 초기화
# ------------------------------------------------------------
RUN rosdep init || true
RUN rosdep update || true

# ------------------------------------------------------------
# 6. ROS2 환경 자동 로딩
# ------------------------------------------------------------
# 컨테이너에 접속할 때마다 source /opt/ros/humble/setup.bash
# 명령을 매번 치지 않도록 bashrc에 등록
# ------------------------------------------------------------
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "export TURTLEBOT3_MODEL=waffle" >> /root/.bashrc
RUN echo "export GAZEBO_MODEL_PATH=\$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models" >> /root/.bashrc

# ------------------------------------------------------------
# 7. 작업 디렉터리 설정
# ------------------------------------------------------------
WORKDIR /workspace

# ------------------------------------------------------------
# 8. 기본 실행 명령
# ------------------------------------------------------------
# docker compose up 후 컨테이너가 바로 종료되지 않도록 bash 실행
# ------------------------------------------------------------
CMD ["/bin/bash"]
