# Развёртывание тестовой сцены UR5e и ROS 2 Humble

В папке находятся четыре задания (`Lab1.md`–`Lab4.md`), эта инструкция и Docker-комплект `container/`. Каталог критериев включён в ЛР1, общий протокол эксперимента — в ЛР2. Исходники сцены и контроллера находятся внутри Docker-комплекта.

## Что запускается

В одном контейнере: Ubuntu 22.04, ROS 2 Humble, Webots R2023b, драйвер `webots_ros2 2023.1.0` и тестовая сцена UR5e с конвейером и деталями. Симулятор отображается в браузере через noVNC. При запуске пример двигает пять суставов и возвращает робот в исходное положение.

**Это тестовый пример управления суставами.** В данном образе конвейер неподвижен. Стандартный драйвер Webots публикует изображение камеры и состояние вакуумного захвата, а также принимает команду включения захвата. Готового алгоритма перестановки объектов, динамического захвата и зрения нет. Студент строит собственную сцену и программу технологической операции для курса.

## Требования

- Компьютер x86-64, Windows с Docker Desktop (Linux containers, WSL2) либо Linux с Docker Engine и Compose v2.
- Рекомендуется выделить Docker 4 ГБ RAM и 2 CPU, иметь 10 ГБ свободного диска.
- Для запуска готового образа сеть не требуется. Для пересборки нужны интернет и загрузка зависимостей.

Docker Desktop должен быть запущен. При Docker Engine внутри Ubuntu WSL команды выполняйте в Ubuntu с `sudo` перед `docker`; при необходимости запустите `sudo systemctl start docker`. `docker` из PowerShell доступен при установленном Docker Desktop, а не автоматически после установки Engine в WSL.

## Запуск готового образа

Скачайте [готовый Docker-образ ur5e-student-lab.tar.gz](https://github.com/Vladosok96/RobotModeling/releases/download/ur5e-test-scene-2026-10-09/ur5e-student-lab.tar.gz) (около 671 МБ) и сохраните его в подпапку `container`. Образ распространяется через GitHub Releases; при клонировании Git скачиваются задания и исходники Docker-комплекта.

Откройте терминал в подпапке `container` и выполните:

```bash
docker load -i ur5e-student-lab.tar.gz
docker compose up --no-build -d
```

Для сборки из исходников с доступом в интернет вместо загрузки готового образа выполните в той же папке `docker compose up --build -d`.

Откройте <http://localhost:8080/vnc.html?autoconnect=1&resize=scale>. Если появляется запрос подключения, нажмите Connect. Движение начинается автоматически и длится 9 секунд симуляционного времени; при программной графике реальное ожидание может быть больше.

Если робот уже закончил движение, повторите пример:

```bash
docker compose exec lab ros-env ros2 run ur5e_student_lab joint_demo
```

Успешное выполнение: `PASS: 5 joints moved`. Проверить журнал и доступность:

```bash
docker compose logs -f lab
docker compose ps
```

`healthy` подтверждает доступность браузерного интерфейса; работу ROS и движения подтверждает `PASS`. `Ctrl+C` завершает просмотр журнала.

На текущем компьютере с Engine внутри `Ubuntu-22.04` можно запустить `container/start-wsl.cmd`. Он открывает браузер и держит WSL активной. Оставьте его окно открытым. Этот помощник рассчитан на названный WSL-дистрибутив и установленный в нём Docker; на других компьютерах используйте команды выше. Сервисы systemd сами по себе не гарантируют, что WSL не завершится при закрытии всех её терминалов.

## Проверка интерфейсов ROS

```bash
docker compose exec lab ros-env ros2 topic list
docker compose exec lab ros-env ros2 topic echo /joint_states --once --qos-reliability best_effort
docker compose exec lab ros-env ros2 topic echo /clock --once
docker compose exec lab ros-env ros2 service call /ur5e/stop std_srvs/srv/Trigger '{}'
```

Проверка изображения камеры без вывода большого массива пикселей:

```bash
docker compose exec lab ros-env ros2 topic echo /UR5e/camera/image_color --once --field width
```

Ожидаемая ширина изображения — `320`. Изображение публикуется как `sensor_msgs/msg/Image`; параметры камеры — в `/UR5e/camera/camera_info`. Состояние наличия детали публикуется в `/UR5e/vacuum/presence`, команда включения захвата принимается в `/UR5e/vacuum/turn_on` (`std_msgs/msg/Bool`). Наличие этих интерфейсов подтверждено; физический захват и перенос детали в тесте движения суставов не проверяются.

Команды траекторий отправляются в `/ur5e/joint_trajectory` (`trajectory_msgs/msg/JointTrajectory`). Обратная связь — `/joint_states` (`sensor_msgs/msg/JointState`). В траектории указываются все шесть суставов, позиции в радианах и возрастающие времена; поля скоростей/ускорений оставляются пустыми, timestamp заголовка нулевой. Ограничение учебного драйвера — 0.6 рад/с по пику интерполяции, позиции в пределах ±2π. Сервис `/ur5e/stop` прекращает траекторию и удерживает измеренные углы.

Интерактивная оболочка с подключённым ROS:

```bash
docker compose exec lab ros-env bash
```

## Изменение сцены и программы

Рабочие исходники на компьютере:

- `container/lab/ur5e_student_lab/webots/worlds/ur5e_lab.wbt` — тестовая сцена;
- `container/lab/ur5e_student_lab/webots/protos/` и `webots/assets/` — модели и ресурсы;
- `container/lab/ur5e_student_lab/ur5e_student_lab/demo.py` — публикация траектории;
- `container/lab/ur5e_student_lab/ur5e_student_lab/trajectory.py` — точки, проверка и интерполяция;
- `container/lab/ur5e_student_lab/ur5e_student_lab/driver.py` — двигатели, датчики и ROS-интерфейс;
- `container/lab/ur5e_student_lab/launch/lab.launch.py` — запуск Webots и драйвера.

После изменений исходников пересоберите из папки `container`:

```bash
docker compose up --build -d
```

Готовый `.tar.gz` содержит исходную версию образа и не обновляется от изменения файлов. `docker load` повторно загрузит именно сохранённую версию. Если меняете имя world-файла для собственной сцены, измените также путь в launch-файле и включите её ресурсы в сборку пакета.

Для своего ROS-узла добавьте Python-модуль в пакет и команду в `setup.py` → `console_scripts`; затем пересоберите. Например, для команды `student_controller`:

```bash
docker compose exec lab ros-env ros2 run ur5e_student_lab student_controller
```

Автоматическую демонстрацию отключите перед собственными опытами: в сервис `lab` файла `compose.yaml` добавьте на уровне `image`:

```yaml
    command: ["ros2", "launch", "ur5e_student_lab", "lab.launch.py", "demo:=false"]
```

Затем `docker compose up --no-build -d --force-recreate` для неизменённого образа либо `docker compose up --build -d` для изменённых исходников. Не запускайте две управляющие программы одновременно.

Файлы хоста не подключены в контейнер автоматически. Результаты сохраняйте и копируйте до удаления контейнера; пример для каталога `/home/student/results`:

```bash
docker compose cp lab:/home/student/results ./results
```

## Остановка и неполадки

```bash
docker compose down
```

- Docker недоступен: проверьте Docker Desktop или службу Engine в Linux/WSL.
- Порт 8080 занят: в PowerShell выполните `$env:LAB_PORT='8081'`, в Linux `export LAB_PORT=8081`, затем повторите запуск и откройте порт 8081.
- Нет движения: проверьте Play в Webots и журнал контейнера; запустите пример повторно.
- Чёрное окно: дождитесь загрузки программной графики; при ошибке проверьте журнал.
- Ошибка архитектуры: образ предназначен для `linux/amd64`, на ARM требуется эмуляция.

Порт браузера открыт только на `127.0.0.1`; ROS ограничен контейнером. Подключение ROS-узлов на хосте этим комплектом не настроено. MoveIt и `ros2_control` не включены.

## Проверенная версия и лицензии

Готовый образ повторно проверен 9 октября 2026 года на Docker Engine в Ubuntu 22.04 WSL2: загрузка файла образа, запуск по Compose, отображение сцены в браузере, ROS 2 Humble, движение пяти суставов с возвратом, получение `/joint_states`, `/clock`, изображения камеры и состояния захвата, успешный ответ сервиса остановки. Тест движения завершился `PASS: 5 joints moved; max return error = 0.0000 rad`. Проверка выполнена отдельным проектом Compose на порту 18080; обычный запуск выше использует порт 8080. При сборке выполняются семь тестов учебного пакета. Docker Desktop отдельно не проверялся.

Идентификатор сохранённого образа:

```text
sha256:6d1c76948e036b53423c4203bf01d2562e73923d1dda8054eccf98f6e87a7151
```

Сведения о лицензиях моделей и ресурсов сохранены внутри пакета в `LICENSE`, `THIRD_PARTY.md` и `ASSETS.tsv`. Вложенные файлы пакета — служебная документация/атрибуция, отдельные инструкции для выполнения лабораторных не требуются.
