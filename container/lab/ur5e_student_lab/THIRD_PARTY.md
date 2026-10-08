# Происхождение файлов

Сцена, геометрия ограждения/стенда и модифицированный `TrainingUR5e.proto`
извлечены из `standalone/blockly-industrial/industrial_seed.zip`
репозитория https://github.com/ulstu/industrial-robot-sim,
коммит `b37fec1ead832906fd5d2dc3a857b9420b514258`.
Сохранены заголовки лицензии модели UR5e.

Ресурсы в `webots/assets/webots/` взяты из официального Webots R2023b
https://github.com/cyberbotics/webots/tree/R2023b и распространяются
на условиях Apache License 2.0. В локальных PROTO ссылки на ресурсы
заменены относительными путями. `ASSETS.tsv` перечисляет исходные URL
и SHA-256 файлов до замены путей.

Новый драйвер, пример, тесты и файлы запуска: Apache License 2.0.
Файл `config/ur5e_driver.urdf` задаёт плагин драйвера; это не полная
кинематическая модель для RViz или MoveIt.
