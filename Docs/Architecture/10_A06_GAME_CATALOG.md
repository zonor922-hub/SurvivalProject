# A06 — каталог предметов

Статус: завершена, повторно проверена 26.10.2026 в UE 5.8.4. Ветка `task/a06-item-catalog` создана от `origin/main` на `890ce3b` после слияния PR №2. Перенесён только исходный `daffec3`, новым коммитом `3086da6`. A05 присутствует в main (d6dbb4c является предком); её 13 тестов повторно прошли. A07, A08 и A24 не включены.

## Четыре изменённых ресурса

Пути относительно `Content/Survival/`:

- `Items/Catalog/PDA_GameCatalog.uasset`: PrimaryDataAsset с массивом Items.
- `Items/Catalog/DA_GameCatalog.uasset`: четыре определения A05 — wood, stone, berry, plank. Рецепты и постройки относятся к будущим задачам.
- `Core/BP_SurvivalGameInstance.uasset`: GameCatalog, CatalogReady, CatalogError и lookup ItemDefinitions. InitializeCatalog проверяет ссылки, ValidateDefinition и дубликаты. При отказе очищает частичный lookup и блокирует готовность. FindItemDefinition до готовности и при неизвестном ID возвращает None/false. Повторная успешная инициализация не добавляет дубликаты; после исправления конфигурации допустим явный InitializeCatalog.
- `Core/BP_SurvivalPlayerController.uasset`: финальный BootstrapReady дополнительно требует CatalogReady у проверенного собственного GameInstance. Ввод не изменён.

Все четыре ресурса точно совпадают с соответствующими файлами исходного daffec3. Карты, конфигурация, определения A05 и ресурс PlayerState не менялись. BPC_Inventory отсутствует в этой ветке.

## Повторные проверки на чистой базе

Запущен отдельный UnrealEditor-Cmd **в режиме редактора**, с `-ExecutePythonScript`, `-nullrhi -unattended`, временным включением PythonScriptPlugin и `-ddc=InstalledNoZenLocalFallback`. Это не commandlet-имитация PIE: проверочный callback запросил три настоящих PIE-сессии на LV_SystemsTest. Рендеринг отключён; визуальная приёмка не проводилась. Ресурсы не сохранялись, конфигурация проекта не менялась.

- [A05 regression](evidence/a06_a05_regression.json): 13/13, passed=true; исторический результат A05 не перезаписывается.
- [A06 contract](evidence/a06_verification.json): 24/24, passed=true. Проверены четыре ID, неизвестный ID, повторный InitializeCatalog/Bootstrap без дублирования, дублирующийся ID, отсутствующее определение, неверный MaxStack, отсутствие каталога, очистка частично заполненного lookup и явная повторная инициализация после исправления каждой ошибки.
- Четыре Blueprint скомпилированы: GameInstance, PlayerController, PDA_GameCatalog и PDA_ItemDefinition; статус каждого BS_UP_TO_DATE.
- [A06 PIE](evidence/a06_pie.json): три запуска; CatalogReady=true, PlayerController BootstrapReady=true, четыре записи, GameInstance InitializeCount=1. В каждом запуске повторены поиск четырёх ID, безопасный неизвестный ID и повторная инициализация с сохранением четырёх записей.
- Git LFS fsck — OK; ресурсы совпадают с исходным A06. Полная исходящая история проверяется перед push; A07/A08/A24 и сводный коммит старой main не переносятся.

Проверочные файлы: [a06_verify.py](evidence/a06_verify.py), [a06_pie.py](evidence/a06_pie.py), [a06_run_all.py](evidence/a06_run_all.py). Скрипты используют путь собственного проекта, временные объекты для ошибочных данных и не сохраняют assets.

## Как повторить

Автоматический запуск из PowerShell (заменить путь worktree при необходимости):

```powershell
& 'F:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' 'C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A06PublicationWorktree/SurvivalProject.uproject' '-ExecutePythonScript=C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A06PublicationWorktree/Docs/Architecture/evidence/a06_run_all.py' -EnablePlugins=PythonScriptPlugin -unattended -nullrhi -nosplash -ddc=InstalledNoZenLocalFallback
```

В русском интерфейсе:

1. Открыть `.uproject` отдельной ветки A06. «Панель ресурсов» → «Содержимое/Survival/Items/Catalog» → DA_GameCatalog: массив содержит четыре определения.
2. Открыть LV_SystemsTest и нажать «Играть».
3. В Blueprint GameInstance выбрать отладочный экземпляр: CatalogReady=true, CatalogError пуст, ItemDefinitions — четыре записи. У PlayerController BootstrapReady=true.
4. Для контрактных тестов при включённом PythonScriptPlugin выполнить в нижнем поле Cmd: `py exec(compile(open(unreal.Paths.project_dir()+'Docs/Architecture/evidence/a06_verify.py',encoding='utf-8').read(),unreal.Paths.project_dir()+'Docs/Architecture/evidence/a06_verify.py','exec'),{'__file__':unreal.Paths.project_dir()+'Docs/Architecture/evidence/a06_verify.py'})`.
5. Для трёх PIE-прогонов сначала остановить ручную игру, затем аналогично выполнить a06_pie.py. По завершении a06_pie.json должен содержать passed=true и три runs. Скрипт сам открывает тестовую карту и завершает тестовые PIE-сессии.

Доставка каталога и soft references в отдельную Windows-сборку относится к A07. Её прохождение не утверждается этим отчётом. Исходная локальная main и backup сохранены без изменений; PR A06 автоматически не сливается.
