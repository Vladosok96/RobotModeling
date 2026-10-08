#!/usr/bin/env bash
# Run with sudo on Ubuntu 22.04; installs system dependencies, not the workspace.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo 'Run: sudo bash scripts/install-humble.sh' >&2
  exit 1
fi
source /etc/os-release
if [[ ${ID} != ubuntu || ${VERSION_ID} != 22.04 ]]; then
  echo 'This installer targets Ubuntu 22.04 (Jammy) and ROS 2 Humble.' >&2
  exit 1
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl ca-certificates software-properties-common locales python3
locale-gen en_US.UTF-8
export LANG=en_US.UTF-8
add-apt-repository -y universe
# Current official ros2-apt-source package supplies the ROS repository and keys.
apt_source_version=$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
deb_file=$(mktemp --suffix=.deb)
trap 'rm -f "$deb_file"' EXIT
curl -fL "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${apt_source_version}/ros2-apt-source_${apt_source_version}.jammy_all.deb" -o "$deb_file"
dpkg -i "$deb_file"
apt-get update
# Required for a fresh Jammy installation before adding ROS dependencies.
apt-get upgrade -y
apt-get install -y ros-humble-ros-base ros-humble-trajectory-msgs ros-humble-sensor-msgs \
  ros-humble-std-srvs python3-colcon-common-extensions python3-rosdep python3-pytest \
  python-is-python3 build-essential cmake git
if [[ ! -e /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  rosdep init
fi
echo 'ROS 2 Humble installed. Run build-workspace.sh as your ordinary Linux user.'
