# A08 — состояние и чтение инвентаря

Завершена 26.10.2026 на базе опубликованных A05–A07/A24 (`63a1598`). Рабочая ветка публикации `task/a08-complete` создана от origin/main. Исходный `2eea6d5` изучен в отдельной локальной ветке; в публикуемую историю checkpoint не включён. Пользовательские изменения Slots=[] и нулевой InventoryId сохранены; исходный файл дополнительно скопирован в локальный TaskSnapshots перед доработкой.

## Ресурсы и API

- `Content/Survival/Inventory/BPC_Inventory.uasset`: один ActorComponent с Private-полями Slots, Revision, InventoryId, MaxWeight, Initialized и CatalogGameInstance. Instance Editable/Expose on Spawn выключены. До инициализации Slots пуст, GUID нулевой, Revision=0, Initialized=false.
- `Content/Survival/Core/BP_SurvivalPlayerState.uasset`: один Inventory-компонент. InitializeBootstrap вызывает InitializeInventory после готового GameInstance; BootstrapReady читает публичный IsInitialized вместо прямого доступа к Initialized.
- InitializeInventory(GameInstance, SlotCount=4, WeightLimit=10): требует готовый каталог, SlotCount>0 и WeightLimit>=0. Создаёт уникальный GUID и индексированные пустые слоты. Повторный вызов после успеха ничего не сбрасывает.
- IsInitialized: публичный pure getter готовности, без setter.
- GetSnapshot: возвращает отдельное значение FInventorySnapshot. Изменения копии слотов, Revision и MaxWeight не меняют компонент.
- GetCurrentWeight: вычисляет сумму Quantity×UnitWeight по каталогу. До готовности, при неизвестном ItemId или неположительном количестве возвращает 0/Valid=false. Пустой инициализированный inventory — 0/true. Tick выключен.

## Проверки UE 5.8.4

Новый изолированный headless editor/PIE-запуск: exit=0.

- [22 контрактных теста](evidence/a08_verification.json): **22 успешных, 0 неуспешных**. Включают нулевые defaults, готовность, четыре пустых индексированных слота, уникальность GUID между двумя inventory, отделённость snapshot, вес 2 wood=1.0, сохранение заполненного inventory/GUID/Revision при повторном init, неизвестный ID и Quantity=0/-1, некорректную вместимость, отсутствие/неготовность каталога и повтор после исправления.
- [Защита доступа](evidence/a08_access_verification.json): **7 успешных, 0 неуспешных**. Шесть попыток Set из внешнего Blueprint ожидаемо отвергнуты компилятором; публичный IsInitialized компилируется. Диагностические compiler errors этого временного Blueprint — ожидаемый результат отрицательных тестов. Сам Blueprint не сохраняется.
- [Три PIE-прогона](evidence/a08_pie.json): каталог/Controller/PlayerState готовы, один Inventory, четыре пустых слота, вес 0, Tick выключен, собственный Animation Blueprint A24 сохранён.
- [Компиляция](evidence/a08_compile.json): все собственные Blueprint скомпилированы после удаления временной fixture-функции. Тестовая функция A08TestSeed не входит в сохранённый API.

Private-параметры проверялись через интерфейс с использованием навыка Computer Use, затем независимо подтверждены отрицательными compiler-тестами. Доступ доверенной Python-reflection для фикстур не является игровым публичным setter. Проверочные скрипты не сохраняют ресурсы и удаляют временную fixture-функцию в finally.

## Повторение

```powershell
& 'F:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' 'C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A08PublicationWorktree/SurvivalProject.uproject' '-ExecutePythonScript=C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A08PublicationWorktree/Docs/Architecture/evidence/a08_run_all.py' -EnablePlugins=PythonScriptPlugin -unattended -nullrhi -nosplash -ddc=InstalledNoZenLocalFallback
```

В русском интерфейсе открыть BPC_Inventory → «Моя схема» → переменная → «Сведения»: «Частная» включена у всех шести полей. На LV_SystemsTest нажать «Играть», выбрать отладочный PlayerState и Inventory: IsInitialized=true, Snapshot содержит четыре пустых слота, GetCurrentWeight=0/true.

A08 не добавляет команды добавления/удаления, разделения, transfer, события изменений или UI. Они относятся к A09 и последующим задачам. Проверка отсутствия дублирования здесь ограничена инициализацией/чтением и сохранением уже заполненной фикстуры; глобальные inventory-инварианты закрепляются в A12. Исходная main, backup, карты и ресурсы A24 не изменены. PR автоматически не сливается.
