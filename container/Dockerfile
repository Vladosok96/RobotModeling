FROM ros:humble-ros-base-jammy
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ARG BUILD_JOBS=2
ARG WEBOTS_URL=https://github.com/cyberbotics/webots/releases/download/R2023b/webots_2023b_amd64.deb
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential cmake python3-colcon-common-extensions \
    python3-rosdep python3-pytest python-is-python3 \
    xvfb x11vnc novnc websockify fluxbox x11-utils libgl1-mesa-dri tini \
    && curl -fL --retry 3 "$WEBOTS_URL" -o /tmp/webots.deb \
    && apt-get install -y /tmp/webots.deb \
    && rm /tmp/webots.deb && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/ur5e_ws
RUN git clone --depth 1 --branch 2023.1.0 --filter=blob:none --sparse \
      https://github.com/cyberbotics/webots_ros2.git src/webots_ros2 \
    && git -C src/webots_ros2 sparse-checkout set webots_ros2_driver webots_ros2_msgs webots_ros2_importer \
    && git -C src/webots_ros2 submodule update --init --depth 1 \
    && test "$(git -C src/webots_ros2 rev-parse HEAD)" = e3299e4b10c4f3a6832fec77950fe1a53807bae9 \
    && chmod +x src/webots_ros2/webots_ros2_driver/webots_ros2_driver/ros2_supervisor.py
RUN source /opt/ros/humble/setup.bash \
    && (test -f /etc/ros/rosdep/sources.list.d/20-default.list || rosdep init) \
    && rosdep update --rosdistro humble \
    && apt-get update \
    && rosdep install --from-paths src --ignore-src --rosdistro humble -y \
    && CMAKE_BUILD_PARALLEL_LEVEL="$BUILD_JOBS" MAKEFLAGS="-j$BUILD_JOBS" \
       colcon build --symlink-install --executor sequential --packages-up-to webots_ros2_driver \
    && rm -rf /var/lib/apt/lists/*
# Student edits rebuild only the small Python package, preserving the driver cache.
COPY lab/ur5e_student_lab src/ur5e_student_lab
RUN source /opt/ros/humble/setup.bash && source install/setup.bash \
    && colcon build --symlink-install --packages-select ur5e_student_lab \
    && colcon test --packages-select ur5e_student_lab --event-handlers console_direct+ \
    && colcon test-result --verbose \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 --shell /bin/bash student \
    && chown -R student:student /opt/ur5e_ws \
    && mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
COPY entrypoint.sh /usr/local/bin/lab-entrypoint
COPY ros-env.sh /usr/local/bin/ros-env
RUN chmod +x /usr/local/bin/lab-entrypoint /usr/local/bin/ros-env
ENV HOME=/home/student USER=student WEBOTS_HOME=/usr/local/webots DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 \
    UR5E_NATIVE_WEBOTS=1 ROS_LOCALHOST_ONLY=1 PYTHONUNBUFFERED=1 UR5E_DEMO_TIMEOUT=180
USER student
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/lab-entrypoint"]
CMD ["ros2", "launch", "ur5e_student_lab", "lab.launch.py", "demo:=true"]
