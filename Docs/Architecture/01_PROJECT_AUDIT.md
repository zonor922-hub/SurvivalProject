> Копия документа на 25.10.2026. Исторические статусы сохранены; актуальное состояние — [ProjectStatus.md](../ProjectStatus.md). Локальные пути обезличены; обозначения раскрыты в Docs/README.md.

# Аудит текущего проекта

**Обновление A01:** [сверка в Unreal Editor](05_A01_EDITOR_AUDIT.md) выполнена 25.10.2026. Ниже сохранён первоначальный файловый аудит; его открытые вопросы о CDO, графах, World Settings и классах PIE уточнены новым отчётом.

## 1. Источник и метод

Авторитетный каталог — `<PROJECT_ROOT>`. Каталог чата `<LOCAL_WORKSPACE>` содержит инструменты подготовки окружения, отчёты и копии. `LandscapeWork`, `Проверка_карты` и ZIP не являются исходным игровым проектом.

Проверено 25.10.2026:

- `SurvivalProject.uproject`, `Config/DefaultEngine.ini`, `DefaultInput.ini`, `DefaultGame.ini`, часть `DefaultEditor.ini`;
- дерево `Content`, выбранные строки имён и ссылок в `.uasset`/`.umap`;
- `F:\UE_5.8\Engine\Build\Build.version`;
- `Saved/Logs/SurvivalProject.log`;
- прежние отчёты создания окружения и озера в рабочей папке, с отдельной маркировкой исторических данных.

Извлечение строк бинарных пакетов показывает кандидаты ссылок и имена узлов. Оно не определяет направление проводов, достижимость событий, значения всех свойств, hard/soft зависимости или корректность runtime-логики. Полноценный Reference Viewer/AssetRegistry и просмотр графов остаются задачей A01. Не найденный по имени ресурс не равнозначен доказанному отсутствию механики.

## 2. Структура

В корне проекта найдены `Config`, `Content`, `DerivedDataCache`, `Intermediate`, `Saved`, `.uproject`. `Source`, проектные `Plugins`, C++-модули и `.git` в корне не обнаружены. Дескриптор не содержит Modules. Это Blueprint-проект; наличие внешнего управления версиями отдельно не установлено.

Всего 772 файла `.uasset`/`.umap`, включая внешние объекты и резервную карту. Это не 772 игровых сущности.

| Каталог внутри Content | Количество | Назначение по содержимому |
|---|---:|---|
| StylizedEnvironment | 522 | Набор окружения, материалы, анимации, демонстрационные карты и Blueprints |
| Characters | 128 | Манекен, меши, анимации и сопутствующие ресурсы |
| __ExternalActors__ | 65 | Внешние акторы шаблонного уровня |
| LevelPrototyping | 29 | Ресурсы прототипирования |
| Content | 12 | Собственные карты Survival, слои ландшафта и сгенерированные Foliage Types |
| Input | 9 | Enhanced Input и touch UI |
| ThirdPerson | 5 | Шаблонная карта, её данные и три основных Blueprint-класса |
| __ExternalObjects__ | 2 | Внешние объекты уровня |

Карты:

- `/Game/Content/Survival/Maps/LV_Survival_Nature` — рабочая карта окружения с озером по предыдущим работам; текущий файл существует, размер 11 377 276 байт.
- `/Game/Content/Survival/Maps/LV_Survival` — исходная Survival-карта.
- `/Game/Content/Survival/Maps/LV_Survival_Backup_20261023` — резервная карта внутри Content; не включать в релиз без необходимости.
- `/Game/ThirdPerson/Lvl_ThirdPerson` — шаблон.
- `/Game/StylizedEnvironment/Demo/AssetShowcase`, `/Game/StylizedEnvironment/Demo/DemoLevel` — демонстрации набора.

Наличие ExternalActors у шаблона не доказывает использование World Partition у `LV_Survival_Nature`. Проверить World Settings отдельно.

## 3. Существующие системы

| Область | Найденное свидетельство | Вывод / ограничение |
|---|---|---|
| Управление персонажем | `ThirdPerson/Blueprints/BP_ThirdPersonCharacter`; ссылки на IA_Move, IA_Jump, IA_Look, IA_MouseLook, ABP_Unarmed и SKM_Quinn_Simple | Есть основа locomotion; граф и runtime не проверены |
| Контроллер | `BP_ThirdPersonPlayerController`; ссылки на IMC_Default, IMC_MouseLook, UI_TouchSimple | Есть основа ввода и touch UI; UI инвентаря не подтверждён |
| GameMode | Основной BP_ThirdPersonGameMode с ссылками на основной Character и PlayerController | Используется в глобальной конфигурации; override конкретной карты ещё проверить |
| Взаимодействия набора | InteractInterface, InteractPromtWidget, ChestActor_Interface/Trigger, GateActor_Interface/Trigger | Есть демонстрационные взаимодействия/анимации; не готовая универсальная система игры |
| Зависимость демо | Trigger-версии сундука/ворот содержат ссылку на vendor Demo BP_ThirdPersonCharacter; найдены имена старого InputAction Interact | Перенос без адаптации к основному персонажу и Enhanced Input рискован; проверить граф |
| Ветер | LeafsWind с ссылками на WindProperties и FallingLeafsSystem; материалы травы | Визуальный эффект, не игровая погода |
| Окружение | 6 FT_Auto_*: три дерева, два камня, трава | Foliage-декорации; добыча ресурсов не подтверждена |
| Вода | В природе найдены ссылки Water; журнал монтирует Water; прежние отчёты содержат WaterBodyLake и PhysicsVolume | Наличие воды не подтверждает плавание, кислород или питьё |
| Инвентарь/крафт/строительство/потребности | Отдельные собственные ресурсы этих систем в инвентаризации не обнаружены | Планировать как новые системы после проверки Blueprint-графов A01 |
| Сохранение | Найдены резервные карты и editor-скрипты | Это сохранение проекта, не система сохранения прогресса игрока |

Есть два разных `BP_ThirdPersonCharacter` и два `BP_ThirdPersonGameMode`: основные в `/Game/ThirdPerson/Blueprints` и демонстрационные в `/Game/StylizedEnvironment/Demo/ThirdPerson/Blueprints`. В отчётах и задачах использовать полный package path.

## 4. Настройки и зависимости

| Зависимость / настройка | Факт | Практическое значение |
|---|---|---|
| Версия | EngineAssociation=5.8; Build.version=5.8.4, CL 58902052 | Сохранять/проверять ресурсы этой версией |
| Стартовые карты | EditorStartupMap и GameDefaultMap = `/Game/ThirdPerson/Lvl_ThirdPerson.Lvl_ThirdPerson` | Упакованная игра может открыть шаблон вместо Survival; исправлять отдельной задачей |
| GameMode | GlobalDefaultGameMode = `/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C` | Не подменять vendor GameMode |
| Enhanced Input | DefaultPlayerInputClass/DefaultInputComponentClass указывают EnhancedInput; журнал подтверждает монтирование | Развивать существующий ввод; не добавлять параллельные legacy mappings |
| ModelingToolsEditorMode | Явно включён, TargetAllowList=Editor | Инструмент редактора, не зависимость игровой механики |
| GameplayStateTree | Явно включён; журнал подтверждает монтирование | Использование StateTree в игре не доказано; для первого этапа не требуется |
| Water | Монтируется в журнале, есть ссылки в карте; явной записи в Plugins дескриптора нет | Проверить способ включения и Windows cook; не считать запись в одном журнале доказательством переносимости |
| UMG | Ссылки в основном контроллере и vendor widgets | Достаточная основа простого HUD; использование CommonUI не доказано его console variables |
| Рендеринг | DX12/SM6, Lumen, RayTracing, Virtual Shadow Maps, VirtualTextures, Substrate; static lighting выключен | До добавления тысяч интерактивных акторов замерить CPU/GPU; производительность не измерена |
| Exposure / AA | AutoExposure=False, AA method=0 в конфигурации | Визуальные проблемы отделять от архитектуры механик; не менять в этой работе |
| CustomDepth | Значение 1 | Для подсветки со stencil нужно отдельно проверить режим; в MVP достаточно текстового prompt |
| Имя проекта | ProjectName=`Third Person BP Game Template` | Перед релизом заменить метаданные, это не блокер прототипа |

Специальные профили коллизии WaterBody и каналы Interaction/BuildPlacement в прочитанном DefaultEngine.ini не найдены. Это не исключает профили движка или настройки ресурсов. Добавление каналов требует проверки существующей матрицы ответов.

Предлагаемый граф зависимостей первого этапа:

```text
Engine CharacterMovement + EnhancedInput -> Survival Character/Controller
UMG -> HUD / inventory / crafting views -> команды компонентов
Item catalog -> Inventory -> Crafting / Consumption / Building
Landscape + Foliage + StylizedEnvironment -> визуальная сцена
Water + проверенный водный объём -> плавание; отдельно от предметов и крафта
SaveGame DTO -> восстановление PlayerState, потребностей и мировых сущностей
```

Это проектируемый граф. Точный граф зависимостей существующих пакетов ещё не экспортирован.

## 5. Озеро и технический долг

Исторические `build_report.json` описывают первоначальную генерацию 535 деревьев, 344 камней и 29 945 экземпляров травы. После чистки озера эти числа могли измениться; не использовать их как текущую статистику.

Последний отчёт создания плавательных объёмов описывает 257 PhysicsVolume. Ранний `swim_final_verify.json` относится к 236 объёмам. Не смешивать версии. Геометрическая аппроксимация озера большим количеством коробок требует проверки краёв, выхода на сушу и стоимости overlaps. Заменять её только после проверки и резервной копии, не удалять вслепую.

Ранее `inspect_swimming.py` искал ошибочный путь `/Game/Content/ThirdPerson/Blueprints/BP_ThirdPersonCharacter` и получил `bp=null`. Поэтому этот отчёт **не доказывает** настройки плавания основного персонажа. Пользователь сообщал, что персонаж не плавает; считать вопрос открытым до теста MovementMode, глубины, управления и анимации.

В журнале найдены `LogAutomationTest: Error: Condition failed` рядом с `UE::UnifiedErrorTest`. Без имени теста и отчёта это нельзя приписывать механикам игры. Сборка, cook и функциональные тесты в данном аудите не запускались успешно.

## 6. Приоритеты перед реализацией

1. Проверить основной GameMode/Pawn/Controller, Blueprint-компиляцию, World Settings и доступность Water в чистом запуске.
2. Зафиксировать резервную копию/управление версиями; отделить собственные классы от vendor Demo.
3. Создать изолированную тестовую карту, не развивать ядро сразу на большой карте.
4. Закрыть вопрос плавания отдельным тестом; не связывать его с готовностью инвентаря.
5. Подключать новые системы по одной; cook-проверку выполнить до наполнения большим каталогом предметов.
