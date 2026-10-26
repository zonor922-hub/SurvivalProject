# A24 — изолированное плавание собственного персонажа

Статус: завершена в границах A24, повторно проверена 26.10.2026 на чистой базе. Ветка `task/a24-swimming` от `origin/main` (`f17f1d9`, PR №4 объединён). Только `c97f4495306a8e9eeeb6d08809698f872416cadd` перенесён новым коммитом `87c5303`. Зависимости по плану A01/A02/A03 присутствуют. A08 не нужна: BPC_Inventory отсутствует, PlayerState и другие Core-ресурсы совпадают с origin/main. Старые локальные main и backup не изменены.

## Четыре ресурса реализации

- `Content/Content/Survival/Maps/LV_Survival_Nature.umap`: верх 257 существующих LakeSwimVolume выровнен на z=0, нижняя граница -450. Объёмы не заменялись; исходная реализация корректирует CenterZ/ScaleZ. Состав природы не пересоздавался.
- `Content/Survival/Character/BP_SurvivalCharacter.uasset`: override Move. В Swimming используется полный forward камеры с pitch; strafe использует right камеры. На суше вызывается исходный родительский Move. Ввод и исходный ThirdPersonCharacter не меняются.
- `Content/Survival/Character/Animations/AS_SwimTread_A24.uasset`: процедурная MVP-петля удержания на воде, 48 кадров при 30 fps, существующий skeleton mannequin.
- `Content/Survival/Character/Animations/ABP_Survival.uasset`: собственный ABP с отдельной ветвью плавания и сглаженным смешиванием. IsSwimming берётся из CharacterMovement. Привязан к собственному персонажу; vendor ABP не меняется.

Все четыре файла побайтно совпадают с c97f449. Не включены предок A08 (2eea6d5), сводная документация 1e3c750, inventory-компонент, изменения PlayerState или production GameMode.

## Повторные проверки UE 5.8.4

[Итог](evidence/a24_verification.json): engine `5.8.4-58902052+++UE5+Release-5.8`, passed=true. Отдельный UnrealEditor-Cmd в режиме редактора, PythonScriptPlugin включён только для процесса; `-nullrhi -unattended`, реальная симуляция PIE. ExitCode=0. Карты и Blueprint не сохранялись.

- Десять Blueprint (включая ABP_Survival и BP_SurvivalCharacter) успешно скомпилированы, BS_UP_TO_DATE. Нет Inventory assets.
- Проверены 257 LakeSwimVolume: water_volume=true, priority=10, верх z=0 и низ z=-450.
- [Управление и регрессии](evidence/a24_move_verification.json): **7/7**. Forward с pitch вверх/вниз в Swimming, pitch не поднимает движение на суше, strafe по горизонтали. Дополнительно фактическая ходьба на тестовом полу (177.5 см), прыжок (подъём 105.9 см), приземление с возвратом в Walking.
- [Физическое плавание](evidence/a24_physics_after.json): подъём на 184.8 см, погружение на 263.2 см. Подъём достиг поверхности и завершился Falling; при погружении персонаж вновь Swimming. Над поверхностью на z≈150 режим Falling, а не Swimming. Это проверка реального движения, не только pending input.
- [Три берега](evidence/a24_shore_verification.json): западный, восточный, южный; **6/6**. Вход/выход выполняются непрерывным движением: Walking → Swimming → Walking. IsSwimming анимации true на входе и false после выхода. Между независимыми береговыми сценариями Pawn переносится к стартовой точке; сами переходы не телепортируются.
- В журнале проверочного процесса не обнаружены Error/Fatal, Accessed None или ошибки загрузки игровых ресурсов. Git LFS fsck — OK; повторный diff ресурсов совпадает с исходным коммитом.

## Границы результата

Production-карта сохраняет прежний GameMode; её переключение на собственный набор классов относится к A41. В тесте озера собственный Pawn создаётся и получает контроллер только в PIE; исходный Pawn удаляется только в тестовом мире. После окончания PIE эти изменения исчезают. Новое управление/анимация автоматически не добавляются старому production Pawn, а выравнивание водных объёмов уже сохранено в карте.

Анимация — MVP, не финальный swim-set. Headless-проверка подтверждает компиляцию и переключение состояния, но не художественное качество позы. Кислород и утопление не добавлялись. Повторная Windows-упаковка природы в A24 не выполнялась; A07 проверяла только SystemsTest и каталог.

## Как повторить

Все скрипты находятся рядом с отчётом, пути результата относительны собственному файлу: [a24_run_all.py](evidence/a24_run_all.py), [a24_move_verify.py](evidence/a24_move_verify.py), [a24_physics_after.py](evidence/a24_physics_after.py), [a24_shore_verify.py](evidence/a24_shore_verify.py). Неверные/временные состояния создаются только в PIE, сохранений нет.

```powershell
& 'F:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' 'C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A24PublicationWorktree/SurvivalProject.uproject' '-ExecutePythonScript=C:/Users/Denis/Documents/ChatGPT/SurvivalProject/A24PublicationWorktree/Docs/Architecture/evidence/a24_run_all.py' -EnablePlugins=PythonScriptPlugin -unattended -nullrhi -nosplash -ddc=InstalledNoZenLocalFallback
```

Проверка вручную в русском интерфейсе:

1. Открыть проект отдельной ветки A24. «Панель ресурсов» → «Содержимое/Survival/Maps» → LV_SystemsTest → «Играть»: собственный персонаж ходит и прыгает как прежде.
2. Открыть LV_Survival_Nature. Для ручной проверки временно выбрать собственный BP_SurvivalGameMode в «Параметры мира» → переопределение GameMode. Не сохранять это переключение: интеграция относится к A41.
3. «Играть» → войти в озеро с западного, восточного и южного берега, затем выйти. В воде ожидаются Swimming и ветвь плавания, на суше — Walking и обычная locomotion.
4. В воде направить камеру вверх и удерживать W для подъёма; вниз + W — для погружения; A/D — strafe. S идёт в обратном направлении. На суше наклон камеры не должен поднимать персонажа.
5. Остановить игру, вернуть прежний GameMode override (None) и не сохранять тестовые изменения карты. Автоматический набор выше не требует менять production GameMode.

Перед публикацией проверяются вся исходящая история, отсутствие A08/сводного коммита, список файлов, diff --check и LFS. PR автоматически не сливается.
