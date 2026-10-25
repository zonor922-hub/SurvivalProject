> Копия документа на 25.10.2026. Исторические статусы сохранены; актуальное состояние — [ProjectStatus.md](../ProjectStatus.md). Локальные пути обезличены; обозначения раскрыты в Docs/README.md.

# A04 — Тестовая карта LV_SystemsTest

**Выполнена 25.10.2026.** Проект `<PROJECT_ROOT>\SurvivalProject.uproject`, Unreal Engine 5.8.4. Зависимость A03 выполнена. Commit: `cb3c32208309e3f1285b950c1e2408af39e181ea`, ветка `main`.

## Что создано

- `/Game/Survival/Maps/LV_SystemsTest` — отдельная обычная карта без World Partition.
- `/Game/Survival/Tests/BP_SystemsTestFixture` — Blueprint Actor с тестовыми данными и функцией `ResetTestData`.

В World Settings тестовой карты назначен `/Game/Survival/Core/BP_SurvivalGameMode`. Он создаёт собственные Character, PlayerController и PlayerState из A03; собственный GameInstance уже подключён в проекте.

| Объект | Параметры |
|---|---|
| Test_Floor | Площадка 40 × 40 м, поверхность Z=0, BlockAll |
| Test_Wall | Стена длиной 8 м, высотой 3 м и толщиной 0,3 м; X=800 см, BlockAll |
| Test_Slope20deg | Плоскость длиной 8 м и шириной 5 м, наклон Pitch=20°, центр (0,900,150) см, BlockAll |
| Test_PlayerStart | (-1000,-800,100) см; Yaw=30° |
| Test_DataFixture | Один экземпляр BP_SystemsTestFixture |
| Освещение | DirectionalLight, SkyAtmosphere и SkyLight |

Пол, стена и уклон используют стандартный Cube движка. На карте нет декоративной растительности, Water, inventory или игровых ресурсов. Она служит изолированной площадкой для следующих задач.

## Как открыть и проверить

1. В настоящем проекте открыть Content Browser → `Survival/Maps` → `LV_SystemsTest`. Карта уже оставлена открытой в редакторе.
2. Нажать Play: персонаж появляется перед стеной и уклоном. Управление наследуется от ThirdPerson: WASD, мышь, Space.
3. Для тестовых данных выбрать `Test_DataFixture` в Outliner. В Details доступны `TestValue`, `TestFlag` и кнопка `Reset Test Data`. Функция сбрасывает их к 0/false; её также можно вызывать из Blueprint теста.
4. Во время PIE нажать Shift+F1 для курсора, выбрать игровой экземпляр фикстуры, изменить данные и вызвать сброс. После Stop игровые изменения не сохраняются в карту.

Функция сброса относится только к фикстуре A04. Она не удаляет SaveGame, не сбрасывает InitializeCount классов A03 и пока не управляет отсутствующими inventory/craft/survival-системами. При добавлении новых тестовых данных расширять её явно.

## Журнал проверки

Проверялся один локальный игрок. Скрипт `evidence/a04_verify.py` выполняет три отдельных цикла Begin PIE → 120 кадров прогрева → проверки → End PIE. Это независимые игровые сессии, не три перехода в одном GameInstance.

| Проверка | PIE 1 | PIE 2 | PIE 3 |
|---|---|---|---|
| GameMode/Controller/PlayerState/Character/GI — собственные Survival | PASS | PASS | PASS |
| InitializeCount у всех пяти = 1, BootstrapReady=true | PASS | PASS | PASS |
| Один игровой Pawn | PASS | PASS | PASS |
| Позиция после установки на пол, см | (-1000,-800,92.15) | (-1000,-800,92.15) | (-1000,-800,92.15) |
| Поворот камеры Pitch/Yaw/Roll | 0/30/0 | 0/30/0 | 0/30/0 |
| Начальные TestValue / TestFlag | 0 / false | 0 / false | 0 / false |
| Изменение на 73/true → ResetTestData дважды → 0/false | PASS | PASS | PASS |

Финальный Blueprint имеет `BS_UP_TO_DATE`, компилируется без предупреждений. По журналу редактора не обнаружено `Accessed None` / `Blueprint Runtime Error`. После функциональных проверок добавлен только флаг Call In Editor для кнопки сброса; тело проверенной функции не изменялось, Blueprint повторно скомпилирован и сохранён.

Для воспроизведения открыть карту, остановить PIE и выполнить в строке Cmd редактора:

```text
py exec(open('<LOCAL_WORKSPACE>/Architecture/evidence/a04_verify.py',encoding='utf-8-sig').read())
```

Не нажимать игровые клавиши и не двигать игровую камеру во время автоматического прогона. Скрипт сам завершает PIE и пишет `a04_runtime_result.json`. Для ручного прогона использовать строки таблицы выше.

## Baseline CPU/GPU

Замер: третий успешный PIE-запуск, после 120 кадров прогрева, встроенная команда `csvprofile frames=300`, неподвижная ThirdPerson-камера у PlayerStart. UE 5.8.4 Editor, viewport 1201×862, Ryzen 5 5600X, RTX 3060, драйвер Windows 32.0.16.1742. VSync=0, t.MaxFPS=0; группы ViewDistance/Shadow/GI/Reflection/PostProcess/Texture/Effects/Foliage=3 (Epic). GI и reflections method=1. r.ScreenPercentage=0 — автоматический выбор редактора; фактический внутренний render resolution отдельно не измерялся.

| Метрика, мс | Среднее | Медиана | P95 | Максимум |
|---|---:|---:|---:|---:|
| FrameTime | 8.816 | 8.365 | 10.332 | 22.246 |
| CPU Game Thread | 8.356 | 8.121 | 10.171 | 19.201 |
| CPU Render Thread | 6.976 | 6.788 | 8.641 | 10.171 |
| GPU | 5.053 | 4.889 | 5.850 | 6.214 |

CPU-потоки и GPU работают с перекрытием; значения не складывать. Это baseline пустой тестовой сцены в редакторе, с Python-монитором и CSV-профилировщиком. Он не является оценкой производительности природы или packaged build. Сравнивать следующие замеры при тех же viewport, качестве, камере и фоне; проверка сборки остаётся задачей A07.

Сохранены только выбранные числовые timing-колонки исходного CSV: `a04_baseline_timings.csv`, а также агрегаты и условия в `a04_baseline.json` и `a04_runtime_result.json`.

## Границы изменений и следующий шаг

Git-коммит содержит ровно два новых LFS-ресурса: карту и Blueprint фикстуры. Все ранее отслеживаемые файлы совпадают с A03, рабочее дерево чистое. Все 779 исходных файлов дополнительно сверены со снимком A02: единственное отличие — уже выполненное в A03 подключение GameInstance в DefaultEngine.ini. Природа, vendor Demo, startup maps и global GameMode в A04 не менялись.

Далее A05 — базовые типы предметов и операций. A05 в этой итерации не выполнялась.

Свидетельства: `a04_build_result.json`, `a04_final_assets.json`, `a04_runtime_result.json`, `a04_baseline.json`, `a04_baseline_timings.csv`, `a04_scope.json`, `a04_git_result.json`. Скрипт создания `a04_build.py` отказывается перезаписывать существующие ресурсы; повторно запускать его для обычной проверки не нужно.
