# A36 — архитектура SaveGame, DTO и версионирование сохранений

27.10.2026, Europe/Moscow. Движок проекта: Unreal Engine `5.8.4-58902052+++UE5+Release-5.8`.

**Статус: технический проект подготовлен; реализация A36 не начата.** Этот документ — проектное решение и техническое задание. В проекте нет ни одного класса SaveGame, DTO, SaveCoordinator, manifest или теста сохранения; это подтверждено аудитом A01 (AssetRegistry `/Game` не содержит SaveGame-классов) и текущим содержимым `Content/Survival` на базе main `031f4f7a284611bcdf032ad073c12e8d16e25bd7`. Имена ассетов, функций и полей ниже — **предлагаемые контракты**, а не существующий API.

В рамках проектирования не изменялись Blueprint, карты, `Config`, `.uproject`, игровые ресурсы, A10 и A11. Unreal не запускался: для документации это не требуется (AGENTS.md).

## 1. Исходное фактическое состояние

| Система | Состояние в main | Что важно для сохранения |
|---|---|---|
| A03 bootstrap | Реализована | GameInstance/GameMode/PlayerState/Controller/Character; Initialize/Ready без ожидания по Delay |
| A05 типы | Реализована | `FItemStack` {StackId Guid, ItemId Name, Quantity Integer, Durability Float, HasDurability Boolean}; `FInventorySlot` {SlotIndex, ItemStack, HasItem}; `FInventorySnapshot` {InventoryId Guid, Revision, Slots, MaxWeight} |
| A06 каталог | Реализована | `FindItemDefinition(ItemId)` после CatalogReady; неизвестный ID безопасен |
| A08 inventory | Реализована | `BPC_Inventory` на PlayerState, Private Slots/Revision/InventoryId/MaxWeight; повторный `InitializeInventory` — no-op; **API восстановления из DTO нет** |
| A09 операции | Реализована | TryAddExact/TryRemoveExact, mutation guard, `OnInventoryChanged` после commit; F02 отвергает NaN/±Infinity |
| A10/A11 split/merge/transfer | На момент принятия A36 не реализованы. Обновление 27.10.2026: A10 реализована и объединена (PR №12); A11 — проект без реализации ([проект A11](17_A11_DESIGN_PROPOSAL.md)) | Правила StackId берутся из архитектуры §6 как контракт; A36 их не меняет. TrySplit/TryMerge/TryTransferExact не добавляют полей в `FSave_ItemStack` |
| A15/A18/A20/A28/A32–A34 | Не реализованы | Pickup, контейнер, потребности, ресурсный узел, постройки: разделы схемы v1 резервируются и пусты, пока системы нет |
| A37–A40 | Не реализованы | Сбор snapshot, запись/fallback, восстановление мира, совместимость |

Замечание о сводке: в main уже есть merge PR №8 (F01/F02); ProjectStatus.md обновлён с учётом этого факта, проверки F01/F02 повторно не запускались.

## 2. Требования A36

Источник — [план A36](03_IMPLEMENTATION_BACKLOG.md) и [архитектура §4, §11](02_GAMEPLAY_ARCHITECTURE.md).

| ID | Требование |
|---|---|
| R01 | `SG_SurvivalSave` и DTO описывают игрока, inventories, контейнеры, постройки, ресурсные узлы, tombstones и метаданные мира |
| R02 | Ни один DTO не содержит ссылок на Actor, Component, Widget, Controller, Class/Object, soft-ссылок, делегатов, таймеров или Text |
| R03 | `SaveVersion = 1`, явная ошибка для версии новее поддерживаемой; цепочка миграций для будущих версий |
| R04 | Стабильные `EntityId`, `StackId`, `InventoryId`; правила назначения и проверки уникальности |
| R05 | `MapId` — стабильный логический идентификатор карты, не путь пакета |
| R06 | Tombstones авторских сущностей; подобранный authored pickup не возвращается после загрузки |
| R07 | Постройки и связи опор сохраняются по GUID; загрузка дважды не удваивает сущности |
| R08 | Запись двумя поколениями слотов + manifest; проверочное чтение; fallback на предыдущий валидный слот |
| R09 | Проверка целостности: структурная, семантическая и по каталогу; без молчаливой потери вещей |
| R10 | Документированный порядок восстановления |
| R11 | Fixture: stack, контейнер, построенная опора со связью и удалённый authored pickup |

## 3. Зависимости

- **Формальная зависимость A36:** A05 — выполнена. Проектирование не требует A10/A11 и не блокирует их.
- **Используемые контракты:** A08 (InventoryId, Revision, SlotCount/WeightLimit), A09 (атомарный commit, mutation guard), архитектура §6 (StackId при split/merge/transfer).
- **Потребители A36:** A37 → A38 → A39 → A40; разделы схемы для A15, A18, A20, A28, A32–A34 заполняются после появления этих систем.
- **Будущие изменения существующих классов** (не в A36 и не в этой ветке): A39 потребуется API восстановления `BPC_Inventory` и фаза Restore в bootstrap GameMode/PlayerController. Это изменения A08/A03-классов, которые выполняются только в своей задаче с регрессией F01/F02.

## 4. Архитектура

### 4.1. Компоненты и владение

| Элемент | Размещение (предложение) | Ответственность | Не делает |
|---|---|---|---|
| `SG_SurvivalSave` | `/Game/Survival/Persistence/SG_SurvivalSave` (родитель SaveGame) | Контейнер DTO одного поколения | Не содержит логики игры и ссылок на объекты мира |
| `SG_SaveManifest` | `/Game/Survival/Persistence/SG_SaveManifest` | Активное поколение и краткие сводки двух слотов | Не хранит игровые данные |
| `FSave_*` DTO | `/Game/Survival/Persistence/DTO/` | Отдельные структуры формата сохранения | Не переиспользуют runtime-структуры напрямую |
| `ESave*` enum | `/Game/Survival/Persistence/Types/` | Коды ошибок, Kind, Origin | — |
| `BPFL_SaveSchema` | `/Game/Survival/Persistence/BPFL_SaveSchema` | `GetCurrentSaveVersion`, `CheckSaveVersion`, `ValidateSaveData`, `MigrateToCurrent` (чистые функции над DTO) | Не пишет файлы и не трогает мир |
| SaveCoordinator | В `BP_SurvivalGameInstance` или его компоненте (A37/A38) | Блокировка save/load, сбор, запись, чтение, fallback, pending DTO при смене карты | Не держит ссылки на акторов прошлого мира |
| Реестр сущностей мира | Компонент GameMode (A37/A39) | Runtime-словарь EntityId → Actor текущего мира | Словарь не сохраняется |

**Решение D1 — отдельные DTO.** Формат файла задаётся собственными `FSave_*` структурами и функциями конвертации runtime ↔ DTO. Если сохранять `FItemStack`/`FInventorySlot` напрямую, любое будущее изменение runtime-структуры молча меняет формат файла. Дублирование нескольких полей дешевле.

**Решение D2 — типизированные массивы вместо полиморфной записи.** Blueprint-структуры не поддерживают безопасный вариантный тип. `FWorldEntityRecord` из архитектуры §4 реализуется как общий заголовок `FSave_EntityHeader` плюс отдельные массивы записей по видам.

### 4.2. Конвейер сохранения (A37 + A38)

```text
Idle → Capturing → Validating → Writing(inactive slot) → Verifying(read-back) → CommittingManifest → Idle
                 ↘ любой отказ → Failed(ErrorCode) → Idle (старые файлы не изменены)
```

1. Запрос отклоняется (`Busy`/`NotReady`), если идёт другой save/load, мир не в Ready, активен mutation guard любого inventory, идёт commit постройки, игрок мёртв или в процессе respawn.
2. **Capturing** выполняется синхронно в одном кадре, без Delay/latent/async load. Результат — новый объект `SG_SurvivalSave`, независимый от мира.
3. **Validating** — `ValidateSaveData` (§10.2). Ошибка — запись не начинается.
4. **Writing** — `Save Game to Slot` в неактивный слот поколения. В MVP синхронный вызов; асинхронный вариант допустим позже, так как DTO уже отделён от мира, но блокировка save/load сохраняется до конца.
5. **Verifying** — `Load Game from Slot` того же слота, проверка класса, `SaveMagic`, `Generation`, `SaveVersion`, повторная `ValidateSaveData` и полное сравнение с записанным DTO.
6. **CommittingManifest** — запись manifest с новым `ActiveSlot`/`ActiveGeneration`, затем чтение manifest обратно. Сообщение «Сохранено» показывается только после этого шага.

### 4.3. Конвейер загрузки (A38 + A39)

```text
Idle → ReadingManifest → SelectingSlot → Reading → VersionCheck → Migrating → Validating(+catalog)
     → OpeningMap(MapId) → Restoring(фазы 1–8) → Activating → Ready
```

DTO хранится в SaveCoordinator как pending-данные на время OpenLevel; ссылки на акторов старого мира не переносятся. Порядок восстановления в новом мире:

1. Gameplay update выключен: таймеры потребностей, input, interaction, preview и UI не активны; авторские сущности не выполняют стартовые побочные эффекты (стартовый loot, истощение) до решения координатора.
2. Однократно собрать authored-сущности текущего мира в реестр (через интерфейс сохраняемой сущности; разрешён единичный поиск при восстановлении, не каждый кадр). Дубликат authored EntityId на карте — ошибка `DuplicateEntityId`.
3. Применить tombstones: соответствующие authored-акторы уничтожить до активации.
4. Применить override-записи authored-сущностей (контейнеры, ресурсные узлы).
5. Создать динамические сущности из записей неактивными (как Prepare в A32), без стартового loot, с EntityId из DTO.
6. Восстановить inventories (игрок, контейнеры, построенные хранилища), затем показатели игрока, затем transform Pawn и ControlRotation.
7. Разрешить связи опор по GUID; проверить уникальность всех ID и итоговые инварианты.
8. Authored-сущности без записи и без tombstone инициализируются как новые (`InitializeAsNew`, стартовый loot ровно один раз).
9. Activate всех сущностей → bootstrap Ready → подписка UI → ввод.

Если шаг 2–7 падает: мир не активируется, пользователю показывается ошибка, файлы не изменяются; возврат в главное меню или повторная попытка с другим поколением. Частично восстановленный мир не продолжает игру.

Повторная загрузка того же DTO полностью пересоздаёт мир через OpenLevel; применение DTO к уже восстановленному миру без перезагрузки карты запрещено (так исключается удвоение динамических actors).

### 4.4. Разделение ответственности A36–A40

| Задача | Входит | Не входит |
|---|---|---|
| A36 | Типы DTO, `SG_SurvivalSave`, `SG_SaveManifest` (только тип), enum ошибок, чистые функции `BPFL_SaveSchema`; тестовый harness, который в отдельном процессе редактора записывает fixture во **временный изолированный слот** и читает его обратно (T03) для проверки сериализуемости схемы | SaveCoordinator, запись по команде игрока, выбор слотов A/B, запись или чтение manifest, fallback, сбор мира, восстановление, UI. В игровых Blueprint нет вызовов `Save Game to Slot`/`Load Game from Slot` |
| A37 | SaveCoordinator: блокировки, синхронный сбор snapshot из компонентов, реестр сущностей, authored EntityId на карте | Файловый IO |
| A38 | Игровая запись и чтение: слоты A/B, проверочное чтение, manifest, выбор поколения и fallback, ошибки пользователю, MapId → карта | Восстановление мира |
| A39 | Порядок восстановления §4.3, API восстановления inventory, фаза Restore в bootstrap | Миграции контента |
| A40 | Golden-файлы, миграционные fixtures, совместимость каталога, проверка после перезапуска | — |

Round-trip T03 в A36 проверяет только то, что тип `SG_SurvivalSave` записывается и читается движком без потери полей. Он не является прототипом конвейера §4.2 и не проверяет атомарность, manifest или fallback.

## 5. Схема данных SaveVersion = 1

Типы — Blueprint-типы. `Int64` поддерживается Blueprint. Все Float-поля обязаны быть конечными (урок F02).

### 5.1. Корень `SG_SurvivalSave`

| Поле | Тип | Правило |
|---|---|---|
| SaveMagic | Name | Всегда `survival.save`; иное — `WrongMagic` |
| SaveVersion | Integer | 1 для этой схемы |
| ContentVersion | Integer | Версия игрового контента; до появления поля в каталоге = 1 |
| Generation | Integer64 | Монотонно растёт с каждой успешной записью; ≥1 |
| SaveSlotName | String | Имя слота, в который DTO записан; диагностика и защита от подмены |
| CreatedUtc | DateTime | Только для отображения; не участвует в выборе поколения |
| BuildInfo | String | Версия сборки/движка, информационно |
| IsComplete | Boolean | Устанавливается последним шагом Capturing; false — `Incomplete` |
| MapId | Name | §6.5 |
| Player | FSave_Player | §5.2 |
| Containers | Array FSave_ContainerRecord | Контейнеры, размещённые на карте |
| BuildPieces | Array FSave_BuildPieceRecord | Динамические постройки |
| ResourceNodes | Array FSave_ResourceNodeRecord | Authored-узлы (A28) |
| DynamicPickups | Array FSave_PickupRecord | Резерв: брошенные игроком предметы; в MVP пусто |
| RemovedAuthoredIds | Array Guid | Tombstones, §7 |
| Summary | FSave_Summary | Контрольные счётчики, §10.2 |

### 5.2. Игрок

`FSave_Player`:

| Поле | Тип | Правило |
|---|---|---|
| PawnLocation | Vector | Конечные компоненты |
| PawnRotation | Rotator | Конечные; используется Yaw, Pitch/Roll восстанавливаются нулём для Character |
| ControlRotation | Rotator | Конечные |
| Inventory | FSave_Inventory | Inventory PlayerState |
| HasSurvivalState | Boolean | false до A20 |
| Survival | FSave_SurvivalStats | Health, Hunger, Thirst, Stamina — Float в [0, Max профиля] |

MovementMode не сохраняется: после установки transform CharacterMovement определяет Walking/Swimming сам (A24). Загрузка у воды проверяется отдельным сценарием.

### 5.3. Inventory и стеки

`FSave_Inventory`: InventoryId Guid; Revision Integer; SlotCount Integer > 0; MaxWeight Float ≥ 0 и конечный; Slots Array `FSave_Slot`.

`FSave_Slot`: SlotIndex Integer в [0, SlotCount); Stack `FSave_ItemStack`. **Сохраняются только занятые слоты**; пустой слот не записывается (аналог правила «пустой слот не имеет stack с Quantity=0»). При восстановлении создаются SlotCount пустых слотов и заполняются перечисленные.

`FSave_ItemStack`: StackId Guid; ItemId Name; Quantity Integer в [1, MaxStack]; HasDurability Boolean; Durability Float (учитывается только при HasDurability, конечное, в [0, DurabilityMax]).

CurrentWeight не сохраняется, вычисляется из каталога.

### 5.4. Мировые сущности

`FSave_EntityHeader`: EntityId Guid; Origin `ESaveEntityOrigin` {Authored, Dynamic}; Kind `ESaveEntityKind` {Pickup, Container, BuildPiece, ResourceNode}; DefinitionId Name (ItemId/BuildId/ResourceId из каталога; для authored-контейнера — ContainerDefinitionId); Location Vector; Rotation Rotator; StateVersion Integer (версия состояния этого вида, в v1 = 1).

| Запись | Поля после заголовка | Origin в v1 |
|---|---|---|
| FSave_ContainerRecord | Inventory FSave_Inventory; LootInitialized Boolean (true всегда в сохранении) | Authored |
| FSave_BuildPieceRecord | BuildId Name; PaidCost Array {ItemId, Quantity}; SupportParentId Guid (нулевой — опора на землю); SupportSocketId Name; HasStorage Boolean; Storage FSave_Inventory | Dynamic |
| FSave_ResourceNodeRecord | RemainingYield Integer ≥ 0 | Authored |
| FSave_PickupRecord | Stack FSave_ItemStack | Dynamic (резерв) |

Построенный сундук — `FSave_BuildPieceRecord` с HasStorage=true, а не отдельная запись контейнера: один EntityId — одна запись.

Связь опоры хранится на зависимой постройке (`SupportParentId` + `SupportSocketId`). Обратные ссылки родителя вычисляются при восстановлении и не сохраняются, чтобы не было двух источников истины.

### 5.5. Manifest `SG_SaveManifest`

| Поле | Тип | Правило |
|---|---|---|
| ManifestMagic | Name | `survival.manifest` |
| ManifestVersion | Integer | 1 |
| ActiveSlot | Name | `A` или `B` |
| ActiveGeneration | Integer64 | Должен совпасть с Generation слота |
| SlotA / SlotB | FSave_SlotInfo | Generation, SaveVersion, IsValid, Summary |

Имена слотов (UserIndex 0): `survival_profile0_A`, `survival_profile0_B`, `survival_profile0_manifest`. Тесты используют только префикс `__test_` и никогда не трогают пользовательские слоты. Файлы находятся в `Saved/SaveGames/` проекта (редактор) или пользовательском каталоге Saved упакованной игры; точный путь Windows-сборки подтверждается в A38/A42.

## 6. Правила идентификаторов

### 6.1. Общие

- Нулевой GUID (`00000000-…`) недопустим ни в одном ID-поле, кроме явно описанного `SupportParentId` = «опора на землю».
- ID не вычисляются из имени актора, пути пакета, DisplayName, индекса массива или HISM/Foliage instance index.
- При загрузке ID восстанавливаются **как есть**. Восстановление никогда не перегенерирует ID ради устранения конфликта: дубликат — признак повреждения, загрузка отклоняется.

### 6.2. EntityId

| Origin | Когда назначается | Где хранится | Правила |
|---|---|---|---|
| Authored | Один раз при подготовке уровня редакторским инструментом (A37), сохраняется в свойстве размещённого актора на карте | Карта | Не генерировать в BeginPlay/Construction Script. Копирование актора в редакторе копирует GUID — валидатор карты и шаг 2 загрузки обязаны найти дубликат |
| Dynamic | В момент commit создания (установка постройки, будущий бросок предмета), до Activate | DTO | При загрузке берётся из DTO; новый GUID создаётся только для новой сущности игрового процесса |

EntityId уникален во всём сохранении: authored ∪ dynamic, все массивы вместе.

### 6.3. StackId

- Сохраняется и восстанавливается без изменений; используется для адресации команд split/merge/transfer после загрузки.
- Уникален во **всех** inventories сохранения (игрок, контейнеры, хранилища построек, dynamic pickups). Совпадение — `DuplicateStackId`.
- Правила появления новых StackId задаёт архитектура §6 (A10/A11): merge сохраняет GUID принимающего стека, split и частичный transfer создают новый, перенос целого стека сохраняет GUID, если он целиком помещается в один пустой слот приёмника; при слиянии с совместимыми стеками действует правило merge (уточнение D2, [проект A11](17_A11_DESIGN_PROPOSAL.md) §3.5). A36 их только проверяет; уникальность StackId во всех inventories (T15) от уточнения не меняется.

### 6.4. InventoryId и Revision

- InventoryId (создаётся A08 при первой инициализации) сохраняется и восстанавливается; уникален среди inventories сохранения.
- Revision сохраняется для диагностики. После восстановления inventory получает `Revision = сохранённая + 1`. Это отклоняет команды с любой ревизией, кроме «сохранённая + 1» (для `TryTransferExact` A11 — проверка обеих ExpectedRevision с отказом `StaleRevision`), но **не** все команды, полученные до загрузки: ложно проходит команда, полученная после сохранения в момент, когда живая ревизия была ровно «сохранённая + 1». Уточнение 27.10.2026 ([проект A11](17_A11_DESIGN_PROPOSAL.md) §3.8), контрпример: сохранение при Revision = 10 → ещё одна команда → живая Revision = 11, UI запомнил 11 → загрузка → восстановленная Revision = 10 + 1 = 11 совпадает с запомненной, и подготовленная команда прошла бы проверку для другого состояния. Поэтому A39 обязана гарантированно инвалидировать команды и привязки, полученные до загрузки (например закрыть окна, отменить подготовленные команды и заново получить ссылки и snapshot после Activate, либо ввести runtime-эпоху команд), независимо от номеров ревизий. Выбор механизма — в A39 с отдельным согласованием; формат сохранения и архитектура A36 этим уточнением не меняются. Событие изменения отправляется только после фазы Activate.
- Команды inventory, в том числе перенос A11, увеличивают Revision только до INT32_MAX и при пределе отклоняются NotReady без переполнения. Если сохранённая Revision равна INT32_MAX, «+1» в A39 невозможно: A39 обязана определить для этого случая отдельное поведение (например отказ восстановления с `InvalidNumber`) и тест; A36 это значение формально не запрещает.
- Во время переноса A11 mutation guard удерживается у обоих участвующих inventories, поэтому правило §4.2 п. 1 (отказ сохранения при активном guard) исключает DTO с промежуточным состоянием переноса.
- Сейчас A08 повторный `InitializeInventory` после успеха — no-op, поэтому восстановление требует отдельного API в A39 (например `RestoreFromSave(FSave_Inventory)`, разрешён только до Ready и только один раз за фазу Restore). В A36 это API не создаётся.

### 6.5. MapId и DefinitionId

- `MapId` — Name вида `map.systems_test`, `map.nature`. Таблица MapId → карта (мягкая ссылка на World) добавляется в каталог/GameInstance в A38; переименование или перенос пакета карты меняет только таблицу.
- В v1 одно сохранение принадлежит одной карте. Неизвестный MapId — `UnknownMapId`. Если в будущем появится несколько карт, мировые разделы переедут в `WorldStates[MapId]` миграцией v1→v2.
- `ItemId`, `BuildId`, `ResourceId` — стабильные ID каталога (архитектура §4); удалённый ID нельзя переиспользовать.

## 7. Tombstones и восстановление сущностей

| Сущность | Что происходит в игре | Что попадает в сохранение | Что делает загрузка |
|---|---|---|---|
| Authored pickup | Подобран (TryAddExact успешен) | EntityId в RemovedAuthoredIds; предметы — в inventory игрока | Уничтожает актор до активации; предметы не дублируются |
| Authored pickup | Не тронут или отказ из-за полного inventory | Ничего | Остаётся из карты |
| Dynamic pickup (резерв) | Брошен / подобран | Запись / отсутствие записи | Создаёт по записи; tombstone не нужен |
| Authored контейнер | Любое состояние | Всегда полная FSave_ContainerRecord | Восстанавливает содержимое; стартовый loot не запускается |
| Authored контейнер без записи | Появился в новой версии контента | — | `InitializeAsNew`: стартовый loot ровно один раз |
| Authored ресурсный узел | Любое состояние | Всегда FSave_ResourceNodeRecord | Восстанавливает RemainingYield; узел с 0 остаётся исчерпанным |
| Dynamic постройка | Установлена | FSave_BuildPieceRecord | Создаёт неактивной, связывает опоры, активирует |
| Dynamic постройка | Демонтирована (A34) | Записи нет | Не создаётся; tombstone не нужен |

Решение D3: stateful authored-сущности (контейнеры, узлы) записываются **всегда**, а не только при изменении. Это проще и исключает ошибки определения «изменено ли».

Инварианты:

- В RemovedAuthoredIds только Authored ID, без повторов.
- Один ID не может одновременно быть tombstone и иметь запись.
- Tombstone на ID, отсутствующий на карте: предупреждение, загрузка продолжается, tombstone сохраняется в следующем сохранении (защита от повторного появления, если ID вернут в контент).
- Запись authored-сущности, отсутствующей на карте: `UnknownAuthoredEntity`, загрузка отклоняется (иначе будет молча потеряно содержимое контейнера).
- Связи опор: родитель существует среди BuildPieces, нет циклов, пара (SupportParentId, SupportSocketId) уникальна; совместимость сокета с BuildDefinition — после появления определений построек (§10.2 п. 6b). Ошибка — `BrokenSupportLink`.

## 8. Что запрещено сохранять

Запрещены в любом DTO, рекурсивно: Object/Actor/Component/Pawn/Controller/PlayerState/Widget ссылки (жёсткие, мягкие, слабые), Class и SoftClass, Interface, делегаты и dispatcher, Timer Handle, Text, Data Asset/Definition (вместо них — ID), preview строительства, текущий focus взаимодействия, состояние открытых окон, кеши lookup каталога, CurrentWeight, флаги mutation guard и bootstrap.

Разрешённые типы полей DTO: Boolean, Integer, Integer64, Float/Double, Name, String, Guid, Vector, Rotator, DateTime, Enum и вложенные `FSave_*` структуры/массивы этих типов.

Проверка автоматизирована (§12, T01): рекурсивный обход свойств `SG_SurvivalSave` и `SG_SaveManifest` через reflection в тестовом harness отклоняет любой запрещённый тип.

## 9. Версионирование и миграции

- `CurrentSaveVersion = 1` — константа в `BPFL_SaveSchema`.
- `CheckSaveVersion(V)`: V ≤ 0 → `CorruptVersion`; V > Current → `NewerVersion`; V < минимальной поддерживаемой → `UnsupportedOldVersion`; иначе `None`.
- Файл с `NewerVersion` не загружается и **не перезаписывается**. Если хоть один слот или manifest имеет версию новее, запись в этот профиль блокируется (`ProtectedNewerSave`) до явного выбора пользователя.
- Миграция: отдельная чистая функция `Migrate_V{n}_To_V{n+1}` на DTO в памяти с собственным fixture; цепочка выполняется до Current, затем `ValidateSaveData`. Исходный файл не переписывается при загрузке; новая версия появится только при следующем ручном сохранении в другой слот, старый остаётся fallback.
- Схема v1 «замораживается» с первой сборкой, которая даёт пользователю сохранять (A38/A42). До этого изменение v1 допускается только обновлением этого документа и fixtures. После — любое изменение формата = новая SaveVersion.
- Правила эволюции Blueprint-структур: не удалять и не пересоздавать поля, не менять их тип; новые поля добавлять с безопасным значением по умолчанию; ненужные поля оставлять как устаревшие. Тегированная сериализация SaveGame пропускает неизвестные поля и подставляет значения по умолчанию для новых — поэтому смена типа или пересоздание поля может **молча** обнулить данные. Это ловится только golden-fixture тестом (T20).
- **Гипотеза для проверки при реализации:** внутреннее имя поля пользовательской структуры содержит GUID поля, и переименование в редакторе не ломает чтение старых файлов. До теста T21 переименование полей DTO запрещено.

## 10. Надёжность записи, целостность и восстановление

### 10.1. Двухслотовая запись: что гарантируется и что нет

**Непроверенные свойства платформы.** Как `Save Game to Slot` в UE 5.8.4 пишет файл на Windows (прямая перезапись или временный файл с переименованием), сбрасывается ли кэш записи на диск до возврата `true` и может ли после сбоя остаться частично записанный файл, — не проверялось. Поэтому **ни запись слота, ни запись manifest не считаются атомарными файловыми операциями**. Manifest — такой же файл SaveGame, и его перезапись может прерваться так же, как запись слота.

Переключение manifest — **логическая отметка подтверждённого поколения**, а не атомарная операция. Схема даёт следующие свойства только при условии, что файл, который не открывался на запись, не повреждается при сбое:

- Новое поколение пишется только в слот, который **не** активен в manifest; файл активного слота в цикле сохранения не открывается на запись.
- Manifest записывается только после успешного проверочного чтения нового слота.
- Valid manifest — источник истины. Неактивный слот с бо́льшим Generation при валидном manifest не выбирается автоматически: он не подтверждён. Это записывается в журнал как предупреждение.
- Если manifest отсутствует или повреждён, выбирается валидный слот с наибольшим Generation (§10.3).

**Отключение питания или аварийное завершение процесса:**

| Момент сбоя | Возможное состояние файлов | Результат загрузки | Потеря |
|---|---|---|---|
| Во время записи неактивного слота | Слот пуст, обрезан, содержит мусор или прежнее поколение; manifest и активный слот не трогались | Manifest → активный слот, поколение N | Прогресс после N |
| После записи слота, до начала записи manifest | Новый слот может быть валиден, manifest старый | Поколение N по manifest; N+1 игнорируется с предупреждением | Прогресс после N |
| Во время записи manifest | Manifest старый, новый или повреждён | Старый → N; новый → N+1; повреждён → сканирование, наибольший валидный (обычно N+1, иначе N) | Не больше прогресса после N |
| После «Сохранено», но до сброса кэша ОС на диск (не проверено) | Новый слот и/или manifest могут быть неполными, хотя проверочное чтение прошло (оно могло читать из кэша) | Manifest повреждён → сканирование; manifest указывает на повреждённый слот → другой слот (§10.3 п. 2) | Прогресс после N |

**Ограничения восстановления:**

- Хранятся только два поколения. Несколько сбоев подряд, повреждение диска, антивирус, ручное удаление или две быстрые записи подряд, ни одна из которых не дошла до диска, могут оставить оба слота невалидными → `NoValidSave`.
- Максимальная гарантированная потеря — прогресс после последнего поколения, файл которого гарантированно дошёл до диска. Из Blueprint это определить нельзя.
- L1 обнаруживает только повреждения, которые нарушают структуру, инварианты или Summary. Данные, которые десериализовались в правдоподобные значения, L1 может не заметить; это закрывает только L2.
- Поведение движка при чтении обрезанного файла не проверено (K02); если десериализация может завершить процесс, fallback не сработает, пока нет L2.
- Резервных копий вне двух слотов, облачного хранилища и истории поколений нет.

**Что проверить до объявления A38 завершённой:** по исходному коду UE 5.8.4 и тестам — способ записи файла сохранения на Windows; T51 (принудительное завершение процесса во время записи слота и manifest); по возможности T52 (жёсткий сброс виртуальной машины во время записи). Принудительное завершение процесса не эквивалентно отключению питания: оно не проверяет кэш ОС. По итогам — либо подтвердить таблицу выше, либо принять решение L2 / запись через временный файл в C++.

### 10.2. Проверка целостности

Уровень L1 (обязателен, только Blueprint). Колонка «Где» показывает задачу, в которой проверка реализуется; A36 реализует только проверки над DTO в памяти.

| № | Проверка | Ошибка | Где |
|---|---|---|---|
| 1a | Объект не None, `SaveMagic`, `IsComplete=true` | WrongClass / WrongMagic / Incomplete | A36 (`ValidateSaveData`) |
| 1b | Класс прочитанного объекта `SG_SurvivalSave`, `SaveSlotName` совпадает с фактическим слотом | WrongClass / SlotCorrupt | A38 (после чтения файла) |
| 2 | Версия: `CheckSaveVersion`, затем `MigrateToCurrent` | CorruptVersion / NewerVersion / UnsupportedOldVersion / MigrationFailed | A36 (функции), A38 (вызов при загрузке) |
| 3 | Структура: обязательные поля (в т. ч. MapId) не пусты, нет нулевых GUID, все Float конечны, Quantity > 0, SlotIndex в диапазоне и без повторов, MaxWeight ≥ 0 | MissingField / ZeroGuid / InvalidNumber / InvalidQuantity / InvalidSlotIndex | A36 |
| 4 | Уникальность EntityId, StackId, InventoryId, tombstones; конфликт tombstone/запись | DuplicateEntityId / DuplicateStackId / DuplicateInventoryId / TombstoneConflict | A36 |
| 5a | Каталог предметов (A06): ItemId известен, Quantity ≤ MaxStack, прочность согласована с определением, вес ≤ MaxWeight с допуском A09 | UnknownItemId / StackLimitExceeded / InvalidDurability / WeightLimitExceeded | A36 |
| 5b | BuildId, ResourceId, MapId известны | UnknownBuildId / UnknownResourceId / UnknownMapId | Каталоги появятся в A29/A28/A38; до этого A36 проверяет только непустое значение (п. 3) |
| 6a | Связи опор: родитель существует среди BuildPieces, нет циклов, пара (SupportParentId, SupportSocketId) уникальна | BrokenSupportLink | A36 |
| 6b | Сокет совместим с BuildDefinition родителя | BrokenSupportLink | После A29/A33, проверяется в A40 |
| 7 | `Summary` пересчитывается и сравнивается: число записей каждого вида, число стеков, сумма Quantity по каждому ItemId, число tombstones | SummaryMismatch | A36 (`ComputeSummary` + сравнение) |
| 8 | Manifest: `ActiveGeneration` равен Generation слота, Summary слота в manifest равна Summary файла | ManifestCorrupt | A38 |

Любое нарушение п. 5 — ошибка совместимости с предложением выбрать предыдущее сохранение, без молчаливого удаления вещей.

Уровень L2 (решение владельца проекта, вне A36–A38 MVP): CRC32/хеш сериализованных байтов **до** десериализации. Blueprint не даёт доступа к байтам SaveGame, поэтому L2 требует минимального C++-модуля (функции SaveGameToMemory/LoadGameFromMemory и FCrc доступны только из C++). Архитектура §1 разрешает пересмотр Blueprint-first, если этого требует тестирование. Решение принимать по результатам T10–T13 и T51/T52.

### 10.3. Выбор поколения при загрузке

1. Manifest валиден → прочитать ActiveSlot → L1. Успех — загрузка.
2. Активный слот невалиден → прочитать другой слот → L1. Успех — загрузка с явным сообщением «загружено предыдущее сохранение, поколение N».
3. Manifest отсутствует или повреждён → прочитать оба слота, выбрать валидный с наибольшим Generation; сообщить о восстановлении manifest. Manifest переписывается только при следующем успешном сохранении.
4. Оба слота невалидны → `NoValidSave`; ничего не перезаписывается автоматически. Новая игра — только с явным подтверждением пользователя.

Невалидный слот не удаляется: он будет перезаписан следующим сохранением как неактивный. Ручное копирование для диагностики — по инструкции пользователю.

### 10.4. Коды ошибок `ESaveLoadError`

None, Busy, NotReady, NoValidSave, ManifestMissing, ManifestCorrupt, SlotMissing, SlotCorrupt, WrongClass, WrongMagic, Incomplete, CorruptVersion, NewerVersion, UnsupportedOldVersion, MigrationFailed, ProtectedNewerSave, UnknownMapId, UnknownItemId, UnknownBuildId, UnknownResourceId, UnknownAuthoredEntity, DuplicateEntityId, DuplicateStackId, DuplicateInventoryId, ZeroGuid, MissingField, InvalidQuantity, InvalidNumber, InvalidDurability, InvalidSlotIndex, StackLimitExceeded, WeightLimitExceeded, TombstoneConflict, BrokenSupportLink, SummaryMismatch, WriteFailed, VerifyFailed, ManifestWriteFailed.

Каждая ошибка возвращается вместе с кратким контекстом (поле/ID) для журнала; пользователю показывается понятное сообщение без технического стека.

## 11. Риски

| ID | Риск | Последствие | Мера |
|---|---|---|---|
| K01 | Изменение типа или пересоздание поля Blueprint-структуры | Тихое обнуление данных старых сохранений | Отдельные DTO, правила §9, golden fixture T20 |
| K02 | Повреждённое тело файла при корректном заголовке | Частично прочитанный объект или сбой редактора/игры при десериализации — не проверено | L1-проверки, тесты T10–T13; при сбое — решение L2/C++ |
| K03 | Копирование authored-актора копирует EntityId | Две сущности с одним ID, потеря tombstone | Валидатор карты и шаг 2 загрузки |
| K04 | BeginPlay authored-контейнера выдаёт стартовый loot до восстановления | Дублирование предметов | Стартовый loot только по команде координатора |
| K05 | Порядок BeginPlay акторов не гарантирован | Восстановление до готовности сущностей | Явная фаза Restore после BeginPlay мира, без Delay |
| K06 | Изменение каталога (MaxStack, вес, удалённый ID) | Невалидный inventory после загрузки | Ошибки совместимости §10.2 п. 5 с выбором предыдущего сохранения; миграция контента отдельной функцией |
| K07 | Сохранение во время операции inventory/постройки | Несогласованный snapshot | Блокировка по mutation guard и состоянию Ready |
| K08 | Отсутствие API восстановления A08 | A39 потребует изменения BPC_Inventory | Делается в A39 с полной регрессией F01/F02; A36 не трогает |
| K09 | Даунгрейд игры | Перезапись более нового сохранения | `ProtectedNewerSave` |
| K10 | Атомарность и сброс на диск у Save Game to Slot и записи manifest не подтверждены | Повреждение нового слота или manifest при сбое питания; потеря прогресса после последнего дошедшего до диска поколения | Двухслотовая запись, активный слот не открывается на запись, сканирование при повреждённом manifest; T51/T52 и проверка исходного кода в A38 (§10.1) |
| K11 | Загрузка у/в воде | Неверный MovementMode после transform | Тест T33 после A24/A39 |
| K12 | Сеть и мультиплеер | Схема одного игрока | Вне объёма; до кооператива — новая схема и миграция |

## 12. Сценарии тестирования

Колонка «Задача» указывает, где тест реализуется и становится критерием приёмки; A36 отвечает только за тесты с пометкой A36. Тесты с файлами используют временные слоты с префиксом `__test_` и удаляют их в finally; игровые ресурсы и пользовательские сохранения (`survival_profile*`) не сохраняются и не изменяются. Тесты A36 работают с DTO в памяти, кроме T03.

### 12.1. Схема и fixture

| ID | Задача | Сценарий | Ожидание |
|---|---|---|---|
| T01 | A36 | Рекурсивный обход типов свойств SG_SurvivalSave и SG_SaveManifest | Только разрешённые типы §8 |
| T02 | A36 | Эталонный fixture F-A36: inventory игрока SlotCount=4, MaxWeight=20 со стеками wood 20 и wood 1 (вес 10.5); authored контейнер SlotCount=4, MaxWeight=50 со stone 5; фундамент + стена с SupportParentId (BuildId проверяется только на непустоту, §10.2 п. 5b); tombstone authored pickup | `ValidateSaveData` = None |
| T03 | A36 | Только тестовый harness в отдельном процессе редактора: fixture → `Save Game to Slot` в слот `__test_a36_roundtrip_<timestamp>` → `Load Game from Slot` → удаление слота в finally. Без manifest, без слотов A/B, без игровых Blueprint-вызовов | Глубокое равенство всех полей, ID, количеств; после теста файла слота нет, пользовательские слоты не изменены |
| T04 | A36 | `CheckSaveVersion` для 1, 2, 0, −1 | None, NewerVersion, CorruptVersion, CorruptVersion |
| T05 | A36 | `MigrateToCurrent` на v1 | Тождественно, без изменения данных |

### 12.2. Повреждённые файлы и данные

T10–T13 повреждают файл и требуют IO → A38. T14–T19 портят DTO в памяти и проверяют `ValidateSaveData` → A36.

| ID | Сценарий | Ожидание |
|---|---|---|
| T10 | Файл слота нулевой длины | SlotCorrupt, fallback на другой слот |
| T11 | Файл обрезан на 50 % и на 1 байт | SlotCorrupt, без сбоя процесса (результат фиксировать фактически; при сбое — риск K02) |
| T12 | Случайная замена байтов в теле | SlotCorrupt или SummaryMismatch, без сбоя процесса |
| T13 | Корректный GVAS-файл другого SaveGame-класса | WrongClass |
| T14 | SaveMagic изменён | WrongMagic |
| T15 | Дубликат StackId между игроком и контейнером | DuplicateStackId |
| T16 | Дубликат EntityId, нулевой GUID | DuplicateEntityId, ZeroGuid |
| T17 | NaN/±Infinity в Location, Durability, MaxWeight, Survival | InvalidNumber |
| T18 | Quantity 0/−1, SlotIndex вне диапазона, повтор SlotIndex | InvalidQuantity, InvalidSlotIndex |
| T19 | Summary не совпадает | SummaryMismatch |

### 12.3. Устаревшие и будущие версии

| ID | Задача | Сценарий | Ожидание |
|---|---|---|---|
| T20 | A40 | Golden v1-файл из репозитория читается текущей сборкой | Равенство с эталонным описанием |
| T21 | A40 | Во временной копии переименовать поле DTO, прочитать golden v1 | Зафиксировать факт; при потере данных — запрет переименования окончательный |
| T22 | A38 | Слот с SaveVersion=2 | NewerVersion; файл не изменён (SHA256 до/после) |
| T23 | A38 | Попытка сохранить при наличии v2 в профиле | ProtectedNewerSave |
| T24 | A40 | Будущая миграция v1→v2 на fixture | Результат = эталон v2, ValidateSaveData = None |

### 12.4. Неполные и несогласованные

| ID | Задача | Сценарий | Ожидание |
|---|---|---|---|
| T30 | A36 | IsComplete=false; пустой MapId (неизвестный непустой MapId проверяется в A38) | Incomplete / MissingField |
| T31 | A36 | SupportParentId на отсутствующую постройку; цикл опор; два потомка в одном сокете (совместимость сокета — позже, §10.2 п. 6b) | BrokenSupportLink |
| T32 | A36 | Один ID одновременно в tombstones и записях | TombstoneConflict |
| T33 | A39 | Сохранение у берега и в воде, загрузка | Transform в допуске 1 cm/0.1°, MovementMode корректный |
| T34 | A38 | Manifest отсутствует; manifest указывает на отсутствующий слот; ActiveGeneration ≠ Generation | Выбор валидного слота с максимальным Generation |
| T35 | A38 | Существует только один слот | Загрузка его; следующая запись идёт во второй |
| T36 | A40 | Неизвестный ItemId/BuildId (изменённый каталог в тестовой копии) | UnknownItemId/UnknownBuildId, старое сохранение не изменено |
| T37 | A40 | Запись authored-сущности, отсутствующей на карте | UnknownAuthoredEntity |
| T38 | A39 | Tombstone на отсутствующий authored ID | Предупреждение, загрузка успешна, tombstone сохранён |

### 12.5. Запись, fallback и повторы (A37–A39)

| ID | Сценарий | Ожидание |
|---|---|---|
| T40 | Инъекция отказа на Writing, Verifying, CommittingManifest | Активное поколение и его файл не изменены (SHA256) |
| T41 | Слот только для чтения (Windows: атрибут «Только чтение») | WriteFailed, сообщение пользователю, старый save цел |
| T42 | Второй save/load во время первого | Busy |
| T43 | Save во время mutation guard / commit постройки / смерти | NotReady или Busy, файлы не изменены |
| T44 | Load того же сохранения дважды подряд | Одинаковое число сущностей, стеков, суммы Quantity |
| T45 | Подобрать authored pickup → save → load | Pickup не вернулся, предметы в inventory один раз |
| T46 | Authored контейнер опустошён → save → load | Пуст, стартовый loot не выдан |
| T47 | Новый authored контейнер без записи в старом save | Стартовый loot один раз |
| T48 | Повторный snapshot без изменений | Эквивалентен, кроме Generation/CreatedUtc/SaveSlotName |
| T49 | Команда inventory с Revision, полученной до загрузки, в том числе `TryTransferExact` A11: (a) ревизия ≤ сохранённой; (b) контрпример §6.4 — ревизия, полученная между сохранением и загрузкой и равная «сохранённая + 1» | (a) отклонена `StaleRevision`; (b) не выполнена механизмом инвалидирования A39, оба inventories без изменений; с ревизиями после загрузки перенос успешен, StackId уникальны во всём сохранении |
| T50 | Save/load после перезапуска приложения и в Windows Development-сборке | Совпадение по ID/Quantity/state (A40/A42) |
| T51 | A38: принудительное завершение процесса (TerminateProcess) во время записи неактивного слота и во время записи manifest, по 3 повтора | Загрузка выбирает поколение по таблице §10.1; процесс загрузки не падает; фактический результат записан. Не заменяет проверку отключения питания |
| T52 | A42, по возможности: жёсткий сброс виртуальной машины с Windows во время записи | Результат записан фактически; при расхождении с §10.1 — решение L2 / запись через временный файл |

## 13. Техническое задание для Sol: реализация A36

**Цель:** создать схему данных сохранения и её чистые проверки. Без сбора мира, записи пользователем, восстановления и UI.

**База:** отдельная ветка `task/a36-save-schema` от актуальной main после приёмки этого проекта. Не включать незавершённые A10/A11 и старую локальную main.

**Создать** (все пути в `/Game/Survival/Persistence/`):

1. `Types/ESaveLoadError`, `Types/ESaveEntityOrigin`, `Types/ESaveEntityKind`.
2. `DTO/FSave_ItemStack`, `FSave_Slot`, `FSave_Inventory`, `FSave_SurvivalStats`, `FSave_Player`, `FSave_EntityHeader`, `FSave_ItemAmount`, `FSave_ContainerRecord`, `FSave_BuildPieceRecord`, `FSave_ResourceNodeRecord`, `FSave_PickupRecord`, `FSave_Summary`, `FSave_SlotInfo` — точно по §5.
3. `SG_SurvivalSave`, `SG_SaveManifest` (родитель SaveGame).
4. `BPFL_SaveSchema`: `GetCurrentSaveVersion() → 1`; `CheckSaveVersion(Integer) → ESaveLoadError`; `ComputeSummary(SG_SurvivalSave) → FSave_Summary`; `ValidateSaveData(SG_SurvivalSave, GameInstance) → ESaveLoadError + контекст` — строки §10.2 с пометкой «A36» (1a, 3, 4, 5a, 6a, 7); `MigrateToCurrent(SG_SurvivalSave) → ESaveLoadError` (v1 — тождественно).
5. Тесты: `Docs/Architecture/evidence/a36_verify.py` и запуск через существующий runner-подход F01 (отдельный UnrealEditor-Cmd, хеши Content/Config/uproject до/после, новый каталог `Saved/Verification/A36/<timestamp>`). Fixture F-A36 строится скриптом в памяти; файлы `.sav` в репозиторий не добавляются (golden-файлы — A40, с добавлением правила LFS для `*.sav` отдельным решением).

**Обязательные тесты:** T01–T05, T14–T19, T30–T32 — все с пометкой A36 в §12; плюс регрессия F01/F02 (211 assertions) без изменений результата. T03 выполняется только из harness во временном слоте (§4.4). T10–T13 и T20+ в A36 не реализуются.

**Не делать:** SaveCoordinator, запись по команде игрока, вызовы `Save Game to Slot`/`Load Game from Slot` в игровых Blueprint (они допустимы только в тестовом harness T03), слоты A/B, запись или чтение manifest, fallback, проверки L1 п. 1b и 8, реестр сущностей, EntityId на карте, API восстановления inventory, изменения BPC_Inventory, GameInstance, GameMode, PlayerState, Controller, карт, A10/A11, Config и `.uproject`; не включать PythonScriptPlugin постоянно; не добавлять C++.

**Отчёт:** `Docs/Architecture/16_A36_SAVE_SCHEMA.md` (или следующий свободный номер) и строка в ProjectStatus.md: изменённые ассеты, компиляция, статусы BS_UP_TO_DATE, результаты тестов, ограничения. Статус «завершена» — только после всех тестов.

## 14. Критерии приёмки

Проекта (этот документ):

- [x] Требования и зависимости A36 перечислены; отсутствующие системы помечены как отсутствующие.
- [x] Описаны DTO игрока, inventory, контейнеров, построек, ресурсных узлов, pickups, tombstones, manifest.
- [x] Правила GUID/EntityId/StackId/InventoryId/MapId; SaveVersion=1 и миграции.
- [x] Запрет Actor/Widget/временных объектов и способ автоматической проверки.
- [x] Двухслотовая запись без заявления о файловой атомарности, поведение при сбое питания и ограничения восстановления (§10.1), проверка целостности, fallback, коды ошибок.
- [x] Ответственность A36–A40 разделена (§4.4); тесты §12, ТЗ §13 и критерии §14 ссылаются на одни и те же проверки §10.2.
- [x] Сценарии повреждённых, устаревших и неполных сохранений; риски; ТЗ для Sol.

Реализации A36 (будущая задача):

1. Все новые ассеты компилируются (BS_UP_TO_DATE), нет новых Accessed None.
2. T01–T05, T14–T19, T30–T32 проходят в отдельном процессе редактора; результат записан в новый каталог Verification. После T03 временного слота нет, файлы `Saved/SaveGames/survival_profile*` (если есть) не изменены по SHA256.
3. Регрессия F01/F02 — 211/0 без изменения.
4. SHA256 существующих Content/Config/uproject вне `/Game/Survival/Persistence/` не изменились.
5. В DTO нет запрещённых типов (T01); fixture F-A36 содержит stack, container, build support link и удалённый authored pickup (R11).
6. Версия 2 даёт `NewerVersion` (критерий плана A36).
7. В игровых Blueprint нет вызовов записи/чтения SaveGame; SaveCoordinator и manifest IO отсутствуют (граница §4.4).

## 15. Проверка этого документа

- Объём изменений: только Markdown в `Docs/` — этот отчёт, ProjectStatus.md, ссылка в README архитектуры и строка статуса A36 в плане. Blueprint, карты, Config, `.uproject`, A10, A11 не изменялись.
- Ссылки на соседние документы проверены на существование файлов.
- Ревизия 2 (по замечаниям PR №10): разделена ответственность A36–A40 и ограничен T03 тестовым harness (§4.4); снято утверждение об атомарности manifest, добавлены сценарии сбоя питания и ограничения восстановления (§10.1, T51/T52); проверки §10.2 разнесены по задачам, а §12–§14 согласованы с ними (коды ошибок, fixture F-A36 в пределах MaxWeight, проверки BuildId/MapId/сокетов перенесены в задачи с соответствующими каталогами).
- Unreal не запускался; ни одно утверждение о поведении SaveGame в UE 5.8.4 не объявлено проверенным: такие места помечены как гипотеза или риск.
