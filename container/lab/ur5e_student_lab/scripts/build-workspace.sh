#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
workspace=${1:-"$HOME/ur5e_ws"}
if [[ ${EUID} -eq 0 ]]; then
  echo 'Build as an ordinary Linux user, not root.' >&2
  exit 1
fi
set +u
source /opt/ros/humble/setup.bash
set -u
mkdir -p "$workspace/src"
if [[ -e "$workspace/src/ur5e_student_lab" ]]; then
  if [[ $(realpath "$workspace/src/ur5e_student_lab") != "$package_dir" ]]; then
    echo 'An unrelated ur5e_student_lab already exists in this workspace.' >&2
    exit 1
  fi
else
  ln -s "$package_dir" "$workspace/src/ur5e_student_lab"
fi
upstream="$workspace/src/webots_ros2"
if [[ ! -d "$upstream/.git" ]]; then
  git clone --depth 1 --branch 2023.1.0 --filter=blob:none --sparse \
    https://github.com/cyberbotics/webots_ros2.git "$upstream"
  git -C "$upstream" sparse-checkout set webots_ros2_driver webots_ros2_msgs webots_ros2_importer
  git -C "$upstream" submodule update --init --depth 1
fi
if [[ $(git -C "$upstream" rev-parse HEAD) != e3299e4b10c4f3a6832fec77950fe1a53807bae9 ]]; then
  echo 'Expected webots_ros2 2023.1.0; use a fresh workspace or inspect the existing checkout.' >&2
  exit 1
fi
rosdep update --rosdistro humble
cd "$workspace"
rosdep install --from-paths src --ignore-src --rosdistro humble -y
# This release tracks the supervisor without its executable bit. With
# --symlink-install the installed launcher keeps the source file permissions.
chmod +x "$upstream/webots_ros2_driver/webots_ros2_driver/ros2_supervisor.py"
colcon build --symlink-install --packages-up-to ur5e_student_lab
colcon test --packages-select ur5e_student_lab --event-handlers console_direct+
colcon test-result --verbose
echo "Workspace ready: $workspace"
echo "source $workspace/install/setup.bash"
echo 'ros2 launch ur5e_student_lab lab.launch.py demo:=true'
