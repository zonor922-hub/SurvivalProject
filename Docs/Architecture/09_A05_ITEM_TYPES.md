# A05 — базовые типы предметов и операций

Статус: завершена; повторно проверена 26.10.2026 в изолированной ветке `task/a05-item-types` от `origin/main` (`f7ac117`). Исходная реализация перенесена только из `aada215bf64faab98a1e735bfcccc736083061d8` в `d6dbb4c542490311d72b6657365e7da00e511f46`. Основная локальная main не изменена. A06, A07, A08 и A24 не переносились.

## Зависимость и границы

A03 присутствует в истории базы (коммит `60a577d`). A04 и предыдущие классы не изменены. Новые ресурсы зависят от базовых Engine-типов и собственных типов A05; каталог, UI, состояние inventory и игровые механики в эту задачу не входят. Все 11 ресурсов совпадают с исходной A05; никаких версий определений из A07 с визуальными заглушками не подмешано.

## Ресурсы

Все пути относительно `Content/Survival/Items/`:

| Ресурс | Назначение и поля |
|---|---|
| Types/EItemCategory | Unknown, Resource, Food, Material |
| Types/EOperationError | NotReady, None, InvalidItemId, InvalidMaxStack, InvalidUnitWeight, InvalidDurability |
| Types/FItemStack | StackId Guid, ItemId Name, Quantity Integer, Durability Float, HasDurability Boolean |
| Types/FInventorySlot | SlotIndex Integer, ItemStack FItemStack, HasItem Boolean; при false данные стека игнорируются |
| Types/FInventorySnapshot | InventoryId Guid, Revision Integer, Slots — массив FInventorySlot, MaxWeight Float |
| Types/FOperationResult | Success Boolean, ErrorCode EOperationError, ActualQuantity Integer, NewRevision Integer |
| Definitions/PDA_ItemDefinition | PrimaryDataAsset: ItemId, DisplayName, Description, Icon, WorldMesh, MaxStack, UnitWeight, Category, ConsumableEffectId, HasDurability, DurabilityMax; ValidateDefinition возвращает FOperationResult |
| Definitions/DA_Item_Wood | item.wood, MaxStack=20, UnitWeight=0.5, Resource |
| Definitions/DA_Item_Stone | item.stone, MaxStack=20, UnitWeight=1.0, Resource |
| Definitions/DA_Item_Berry | item.berry, MaxStack=10, UnitWeight=0.1, Food |
| Definitions/DA_Item_Plank | item.plank, MaxStack=20, UnitWeight=0.4, Material |

Icon и WorldMesh — мягкие ссылки на Texture2D/StaticMesh; пока не назначены. ConsumableEffectId не назначен: эффект ягод относится к будущей задаче. CurrentWeight не хранится в Snapshot: расчёт веса относится к inventory. Структуры данных не содержат UI-полей.

## Фактическая повторная проверка

Запущен UnrealEditor-Cmd с `.uproject` именно этой рабочей копии, `-run=pythonscript`, временным `-EnablePlugins=PythonScriptPlugin`, `-unattended -nullrhi -ddc=InstalledNoZenLocalFallback`. Конфигурация проекта и игровые ресурсы не сохранялись. Версия движка: `5.8.4-58902052+++UE5+Release-5.8`; код завершения процесса 0.

[Проверочный скрипт](evidence/a05_verify.py) и [новый результат](evidence/a05_verification.json) хранятся рядом. Результат `passed=true`, Blueprint скомпилирован, `BS_UP_TO_DATE`. Все 13 сценариев прошли:

- четыре корректных определения;
- пустой ItemId, нулевой/отрицательный MaxStack, отрицательный UnitWeight;
- некорректная прочность и недопустимый стек предметов с прочностью;
- допустимый нулевой вес и корректная прочность;
- изменение DisplayName без изменения ItemId.

Дополнительно проверены точные наборы полей четырёх структур, числовой Durability, массив Slots, числовой MaxWeight, отсутствие UI-типов в схемах и мягкие типы Icon/WorldMesh. Неверные данные создавались только во временных объектах. Скрипт не сохраняет assets.

Git-проверки: `git lfs fsck --objects HEAD` — OK; diff ресурсов относительно aada215 пуст; исходная A03 является предком HEAD. После теста изменённых отслеживаемых ресурсов нет. Упаковка и PIE не требуются критериями A05: доставка мягких ссылок проверяется отдельно в A07.

## Повторение проверки в русском интерфейсе

1. Открыть `.uproject` из отдельного worktree A05, не из старой main.
2. В «Панель ресурсов» → «Содержимое/Survival/Items/Definitions» открыть четыре DA_Item и сверить ID, MaxStack и UnitWeight с таблицей.
3. Открыть PDA_ItemDefinition → ValidateDefinition, нажать «Компилировать»; ошибок быть не должно.
4. При включённом PythonScriptPlugin выполнить в нижнем поле Cmd: `py exec(compile(open(unreal.Paths.project_dir()+'Docs/Architecture/evidence/a05_verify.py',encoding='utf-8').read(),unreal.Paths.project_dir()+'Docs/Architecture/evidence/a05_verify.py','exec'),{'__file__':unreal.Paths.project_dir()+'Docs/Architecture/evidence/a05_verify.py'})`.
5. Проверить новый a05_verification.json: passed=true, 13 результатов passed=true, compile=BS_UP_TO_DATE. Не сохранять временные изменения ресурсов после проверки.

Следующая задача — A06. A08 остаётся незавершённой в старой локальной ветке и не является частью этого PR.

## Расширение EOperationError для A11 (29.10.2026)

В отдельном worktree A11 в конец enum добавлены StaleRevision=15 и SameInventory=16; прежние значения0–14 сохранены. Это расширение не меняет контрактов A09/A10. Проверки текущего незакоммиченного состояния и SHA-256: [отчёт A11](21_A11_TRANSFER.md). Исходная таблица выше описывает историческую A05.
