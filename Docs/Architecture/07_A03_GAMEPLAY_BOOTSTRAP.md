> Копия документа на 25.10.2026. Исторические статусы сохранены; актуальное состояние — [ProjectStatus.md](../ProjectStatus.md). Локальные пути обезличены; обозначения раскрыты в Docs/README.md.

# A03 — Основные классы игры

Статус: выполнена 25.10.2026 в `<PROJECT_ROOT>`. Зависимость A02 выполнена. Commit: `60a577d3255784022a5450fe5d1bd66c72c61ea0`.

## Созданные ресурсы

| Blueprint | Package | Родитель |
|---|---|---|
| BP_SurvivalGameInstance | `/Game/Survival/Core/BP_SurvivalGameInstance` | GameInstance |
| BP_SurvivalGameMode | `/Game/Survival/Core/BP_SurvivalGameMode` | `/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode` |
| BP_SurvivalPlayerState | `/Game/Survival/Core/BP_SurvivalPlayerState` | PlayerState |
| BP_SurvivalPlayerController | `/Game/Survival/Core/BP_SurvivalPlayerController` | `/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController` |
| BP_SurvivalCharacter | `/Game/Survival/Character/BP_SurvivalCharacter` | `/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter` |

GameMode назначает собственные Character, Controller и PlayerState. В `Config/DefaultEngine.ini`, секция `[/Script/EngineSettings.GameMapsSettings]`, добавлена `GameInstanceClass=/Game/Survival/Core/BP_SurvivalGameInstance.BP_SurvivalGameInstance_C`. Python используется только для создания ресурсов и проверки в редакторе; runtime работает на Blueprints.

## Initialize / Ready

Все пять классов содержат `BootstrapInitialized`, `BootstrapReady`, `InitializeCount` и функцию `InitializeBootstrap`. Первый вызов устанавливает Initialized, увеличивает счётчик до 1 и устанавливает Ready. Следующие вызовы ничего не делают. GameInstance запускает её из Init, GameMode/PlayerState/Character — из BeginPlay.

Controller хранит `BoundGameInstance`, `BoundPlayerState`, `BoundPawn`, `PossessionGeneration`. OnPossess вызывает `TryInitialize`: сбрасывает Ready и ссылки, проверяет типы GI/PS/Pawn, вызывает их InitializeBootstrap, затем собственную инициализацию, сохраняет ссылки и устанавливает Ready. Повторный вызов для уже готового текущего Pawn ничего не меняет. OnUnPossess сбрасывает Ready и BoundPawn; последующий TryInitialize без Pawn остаётся в состоянии not ready. Новое possession увеличивает поколение привязки, но не InitializeCount.

Controller наследует BeginPlay родителя без override, сохраняя существующий AddMappingContexts и Enhanced Input. В собственных графах нет повторной установки контекстов ввода. Character наследует движение, прыжок, камеру и animation blueprint основного ThirdPerson.

Это готовность только базового bootstrap. Каталог, UI, inventory и асинхронная загрузка ещё не существуют. При A06 расширить последовательность: готовность каталога должна предшествовать готовности зависимых систем. Не считать текущий BootstrapReady подтверждением наличия каталога. Текущая проверка предназначена для одиночной игры; сетевой lifecycle не проверен.

## Фактическая проверка

Все пять Blueprint имеют `BS_UP_TO_DATE`, без предупреждений компиляции. В PIE сделан OpenLevel на Nature с URL-override собственного GameMode. Карта на диске не сохранялась.

- По одному GameMode, Controller, PlayerState и Character; один GameInstance, у всех InitializeCount=1 и Ready=true.
- Повторные InitializeBootstrap и TryInitialize оставили счётчики равными 1.
- Действия Enhanced Input: движение на 36.41 см; пиковая скорость 322.02 см/с; подъём при прыжке 124.45 см.
- Три цикла UnPossess/Possess: InitializeCount=1, PossessionGeneration=4, один EnhancedInputComponent, ни одного добавления mapping context.
- Одинаковая инъекция IA_MouseLook до и после циклов дала одинаковый поворот 2.5°.
- Сохранились одна CameraComponent и один SpringArmComponent. Сценарий без Pawn безопасен и не выставляет Ready.

Свидетельства: `evidence/a03_build_result.json`, `a03_assets.json`, `a03_runtime_result.json`, `a03_scope_verification.json`. Воспроизводимый тест — `a03_runtime_test.py`: запустить PIE с одним локальным игроком, затем выполнить в строке Cmd редактора `py exec(open('<LOCAL_WORKSPACE>/Architecture/evidence/a03_runtime_test.py',encoding='utf-8-sig').read())`. Тест делает переход только внутри PIE, подаёт действия ввода и записывает JSON; во время проверки не двигать мышь и не нажимать игровые клавиши. Он находит единственную живую EnhancedInputLocalPlayerSubsystem через ObjectIterator, исключая CDO; для нескольких игроков этот harness нужно расширить.

Проверена работа в редакторе, не Windows packaged build. Проверка cook запланирована в A07.

## Границы изменений и дальнейшая работа

SHA-256 всех 779 исходных файлов сверены со снимком A02: изменился только DefaultEngine.ini; все старые карты, основной шаблон и vendor Demo совпадают побайтно. Добавлены ровно пять Blueprint. Коммит содержит шесть файлов, рабочее дерево чистое, новые uasset находятся в LFS.

Стартовые карты и GlobalDefaultGameMode остаются прежними. Поэтому обычный Play на существующей карте ещё использует ThirdPerson GameMode: это ожидаемо до явного override. Следующая задача A04 создаст `/Game/Survival/Maps/LV_SystemsTest` с собственным GameMode; production-интеграция остаётся отдельным этапом. A04 в этой итерации не выполнялась.
