# A07 — доставка каталога в Windows Development-сборку

Статус: завершена, повторно проверена 26.10.2026. Отдельная ветка `task/a07-catalog-delivery` создана от `origin/main` (`945bb46`) после слияния PR №3. Перенесена только реализация `faaed61397f7a0b0655363ef27fa1f969cc2d4a0` в `87a2958`. Зависимости A04, A05 и A06 присутствуют в базе. A08, A24 и сводный локальный коммит не включены; старая локальная main и backup не изменены.

## Восемь файлов реализации

- Четыре `Content/Survival/Items/Definitions/DA_Item_*.uasset`: WorldMesh=/Engine/BasicShapes/Cube, Icon=/Engine/EngineResources/WhiteSquareTexture. Это явные функциональные заглушки. Проверяются восемь ссылок (по две на каждый предмет), а не восемь уникальных файлов: уникальных визуальных ресурсов два.
- `Content/Survival/Tests/BP_CatalogCookProbe.uasset`: при BeginPlay находит четыре ItemId, блокирующе загружает mesh/icon, проверяет валидность, логирует результат. Один запуск, не Tick.
- `Content/Survival/Maps/LV_SystemsTest.umap`: добавлен один Test_CatalogCookProbe.
- `Config/DefaultGame.ini`: DirectoriesToAlwaysCook=/Game/Survival/Items, MapsToCook=/Game/Survival/Maps/LV_SystemsTest, bUseZenStore=False. Применяется файловый cook без обязательного локального Zen.
- `SurvivalProject.uproject`: GameplayStateTree выключен в исходной реализации A07, чтобы неиспользуемый плагин не требовал проектную C++ target-сборку для Blueprint-проекта. Water и используемые зависимости окружения не заменялись. Повторная упаковка этой конфигурации успешна; StateTree-механики этой задачей не добавляются.

Игровые ресурсы побайтно совпадают с исходным A07. В Config/DefaultGame.ini после проверки удалена только лишняя пустая строка в конце для прохождения diff --check; значения настроек не изменены. Другие игровые ресурсы не пересохранялись.

## Редактор и регрессии

[a07_verify.py](evidence/a07_verify.py) выполняется в отдельном UnrealEditor-Cmd с временно включённым PythonScriptPlugin; saves не вызываются. [Новый результат](evidence/a07_editor_verification.json):

- Engine `5.8.4-58902052+++UE5+Release-5.8`;
- A05: 13/13, A06: 24/24;
- девять собственных Blueprint скомпилированы, каждый BS_UP_TO_DATE;
- восемь mesh/icon ссылок разрешены в ожидаемые StaticMesh/Texture2D;
- на LV_SystemsTest найден ровно один экземпляр probe.

Исторические JSON A05/A06 восстановлены скриптом после регрессий; новые результаты включены только в a07_editor_verification.json.

## Упаковка и отдельный запуск

[a07_verification.json](evidence/a07_verification.json) содержит новый итог упаковки и известные предупреждения. BuildCookRun: **BUILD SUCCESSFUL**, 29.51 секунды, ExitCode=0. Архив создан заново в отдельном каталоге:

`D:/Project/SurvivalProjectBuilds/A07Publication_20261026/Windows/SurvivalProject.exe`

Игра запущена этим exe отдельным процессом вне Unreal Editor с `/Game/Survival/Maps/LV_SystemsTest -windowed -ResX=960 -ResY=540 -unattended -nosplash -seconds=12`. NullRHI для игры не использовался; автоматический запуск выполнен со скрытым окном. Проверка визуального качества вручную не проводилась. Игра завершилась штатно, код launcher=0; журнал содержит LogExit: Exiting.

[Отобранный журнал игры](evidence/a07_standalone_proof.txt) подтверждает:

- A07 ITEM PASS item.wood;
- A07 ITEM PASS item.stone;
- A07 ITEM PASS item.berry;
- A07 ITEM PASS item.plank;
- A07 PASS 4 IDs and 8 soft assets.

В полном журнале упаковки/игры не обнаружены Error/Fatal, A07 FAIL и ошибки LogStreaming/LogLinker загрузки ресурсов. Полные журналы оставлены локально; в репозиторий включены только отобранное доказательство и сводка.

## Предупреждения и пределы проверки

Cook сообщает об отсутствующих NodeGuid у узлов-комментариев нескольких Blueprint; это предупреждение о возможной недетерминированности cook, не ошибка компиляции или загрузки. Они перечислены в сводке; несвязанные ресурсы не пересохранялись для исправления предупреждений.

Среда также сообщает об отсутствии необязательных profiler DLL (aqProf/Vtune/WinPix), неуказанном default SoundConcurrencyObject и недоступном PlatformFileJournal на F:. Это не отсутствие визуальных ресурсов каталога. Отдельных ошибок загрузки игровых assets не найдено.

Сборка проверяет **LV_SystemsTest** и основу A01–A07. Производственная карта природы, плавание и полноценная survival-петля не входят в проверку. Глобальная стартовая карта не заменялась: тестовую карту нужно указывать при запуске.

## Повторить в Unreal Engine с русским интерфейсом

1. Открыть `.uproject` из отдельного worktree A07.
2. «Панель ресурсов» → «Содержимое/Survival/Maps» → LV_SystemsTest → «Играть».
3. У Test_CatalogCookProbe в отладочном экземпляре Passed=true и CheckedCount=4. В «Журнале выходных данных» найти четыре A07 ITEM PASS и итог A07 PASS.
4. Для самостоятельной проверки запустить указанный exe с аргументами `/Game/Survival/Maps/LV_SystemsTest -windowed`.

Для повторной упаковки из PowerShell:

```powershell
& 'F:/UE_5.8/Engine/Build/BatchFiles/RunUAT.bat' BuildCookRun '-project=C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A07PublicationWorktree/SurvivalProject.uproject' -noP4 -platform=Win64 -clientconfig=Development -installed -nocompileeditor -skipbuildeditor -cook -map=/Game/Survival/Maps/LV_SystemsTest -AdditionalCookerOptions=-ddc=InstalledNoZenLocalFallback -stage -pak -package -archive '-archivedirectory=D:/Project/SurvivalProjectBuilds/A07Publication_20261026' -utf8output
```

Перед публикацией проверяются Git LFS, полный исходящий диапазон и точный список файлов. Временные Build/Windows/FileOpenOrder журналы, Saved/Intermediate и собранная игра в PR не включаются. PR автоматически не сливается.
