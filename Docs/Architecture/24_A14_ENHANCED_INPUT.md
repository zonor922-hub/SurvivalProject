# A14 — Enhanced Input

Статус: **реализована и проверена в task/a14-enhanced-input; готова к отдельному PR, не merged**. 29 октября 2026, Europe/Moscow. База: `7bb77eb`. Зависимости A03/A13. Рабочая папка `D:\Project\SurvivalProject_A14`, UE `5.8.4-58902052+++UE5+Release-5.8`.

## Сохранённая реализация и контракты

Сохранены существующие ручные IA_Interact, IA_Inventory, IMC_Survival, ESurvivalInputMode и графы контроллера. InputAction имеют Boolean value, без triggers/modifiers; IMC содержит E → IA_Interact и Tab → IA_Inventory в UE 5.8 DefaultKeyMappings. Оба обработчика используют только Started; удержание не повторяет команду. EnsureSurvivalInput проверяет HasMappingContext перед AddMappingContext (priority 1), не удаляет mapping contexts шаблона. A03 TryInitialize/InitializeBootstrap и A13 BPC_Interaction не менялись.

- `OnInteractRequested(Pawn)` — типизированный dispatcher контроллера вместо Print String. Вызывается ровно один раз на Started в Gameplay при BootstrapReady и валидном актуальном Pawn. UI и Build отклоняют запрос. Это намерение взаимодействовать: будущий обработчик A16 обязан заново проверить focus, дистанцию, видимость, доступность и результат. Запрос не означает успешный pickup и не меняет Inventory.
- `SetSurvivalInputMode(NewMode)` — существующий идемпотентный setter. Gameplay/Build: GameOnly, cursor off, ResetIgnoreMove/LookInput, ввод текущего Pawn включён. UI: GameAndUI, cursor on, SetIgnoreMove/LookInput, ввод Pawn отключён; контроллер продолжает принимать Tab. Tab запоминает Gameplay либо Build и при закрытии восстанавливает этот режим.
- `OnSurvivalInputModeChanged(Mode)` — типизированный dispatcher после применения политики нового режима, включая сброс из UI/Build при possession. Повторное назначение того же режима не вызывает событие. A17 может слушать UI-состояние; widgets, предметные операции, pickup и выполнение взаимодействия здесь не реализованы.
- ResetSurvivalInputState сбрасывает текущий и предыдущий режим в Gameplay, cursor и ignore flags, очищает удерживаемый ввод (bFlushInput), восстанавливает ввод актуального Pawn. Вызов безопасен без Pawn. ApplySurvivalPawnInput — небольшой helper контроллера для существующего стека ввода Pawn, без новых компонентов, bindings или vendor edits.

Оба временных Print String удалены, включая ранее отключённый Inventory Print.

## Найденная ошибка и исправление

Реальный PIE выявил **FAIL**: прыжок шаблона работал при открытом UI, несмотря на SetIgnoreMoveInput (подъём 127.53 см). [Evidence до исправления](evidence/a14_jump_before_fix.json). Исправление: DisableInput текущего Pawn в UI, EnableInput в Gameplay/Build и при сбросе possession. Проверка валидности Pawn предшествует вызову. Контроллер и Tab остаются активными. Ни один готовый Blueprint не пересоздавался.

## Реальные проверки

| Проверка | Результат и evidence |
|---|---|
| Загрузка пяти ресурсов, фактические узлы/пины/связи, финальный saved-graph audit | PASS — [графы](evidence/a14_blueprint_audit.json) |
| Компиляция восьми Blueprint: PC, GM, GI, PS, Character, Interaction, BPI, Inventory | PASS, BS_UP_TO_DATE — [compile](evidence/a14_pie.json) |
| Финальная матрица, два свежих PIE на LV_SystemsTest | **274 PASS / 0 FAIL** — [assertions](evidence/a14_pie.json) |
| Одно удержание Interact → одна команда; payload актуального Pawn | PASS в обоих запусках, до/после possession |
| UI блокирует Interact; Build блокирует Interact | PASS |
| 10 UI циклов из Gameplay и 10 из Build в каждом запуске; удержание Tab; repeated Set(UI) | PASS, без повторных mode events и накопления locks |
| Все шесть прямых переходов Gameplay/UI/Build | PASS |
| Три смены на новые Pawn в каждом запуске, unpossess negative case, bootstrap, новый BoundPawn и generation | PASS, никаких повторных AddMappingContext |
| Сохранение PlayerState и полного Inventory snapshot при трёх сменах Pawn | PASS |
| Mapping contexts шаблона, движение и камера после возврата из UI и трёх смен Pawn | PASS в обоих запусках |
| Jump в Gameplay → UI → Build → Gameplay после исправления | **4 PASS / 0 FAIL**, высота 127.53 / 0 / 127.53 / 127.53 см — [evidence](evidence/a14_jump_regression.json) |
| Регрессия A12: три сценария публичных команд Inventory | **548 PASS / 0 FAIL** — [evidence](evidence/a14_inventory_regression.json); выполнена до исправления UI Jump, Inventory после этого не менялся |
| Accessed None / Blueprint Runtime Error в финальных двух журналах PIE | Не обнаружены |
| Пользовательская ручная PIE-проверка исходной реализации | По сообщению пользователя 6/6 PASS; отдельно от автоматической приёмки, после исправлений физические клавиши вручную не перепроверялись |
| Полная матрица A13 171 assertions, A24 вода, packaged build, multiplayer, визуальная QA | **NOT RUN** в A14; существующие результаты не объявляются повторёнными |

PIE настоящий, ввод подаётся через Enhanced Input action injection. Это проверяет обработчики Started/удержание и стек ввода, но не является повтором ручного нажатия физических E/Tab. Mapping keys проверены по сохранённому IMC. Listener Blueprint создаётся только в памяти и не сохраняется в Content. Предварительные сбои Python-оснастки (имена API, тип enum, spawn) не засчитываются в финальные PASS; отдельный продуктовый FAIL UI Jump сохранён выше.

В журналах UE до инициализации Engine присутствуют 17 `LogAutomationTest: Error: Condition failed`, рядом с UnifiedErrorTest; столько же в исходном пользовательском Saved/Logs/SurvivalProject.log до изменений. Это предсуществующая диагностика старта, не 17 успешных или проваленных assertions A14; её первопричина здесь не исследована. Финальные процессы завершаются с exit code 0, отчёты runner passed=true. Полные журналы и промежуточные скрипты оставлены локально в Saved/a14_*.log и Saved/a14_*.py, не публикуются.

## Воспроизводимость

Сохранены read-only audit и runtime runners: [audit](evidence/a14_blueprint_audit.py), [PIE](evidence/a14_pie.py), [Jump + A12](evidence/a14_regression.py). Запуск из корня checkout (свой путь UE):

```powershell
& 'F:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' "$PWD/SurvivalProject.uproject" "-ExecCmds=py $PWD/Docs/Architecture/evidence/a14_pie.py" -EnablePlugins=PythonScriptPlugin -unattended -nullrhi -nosplash -UseFixedTimeStep -FPS=60 -ddc=InstalledNoZenLocalFallback
```

Для дополнительной регрессии заменить a14_pie.py на a14_regression.py. Результаты пишутся в Saved/a14_pie.json, Saved/a14_audit.json, Saved/a14_regression.json. Канонические runners используют путь относительно __file__. Финальная матрица 274 PASS и audit выполнены непосредственно публикуемыми runners из Docs; Jump/A12 — эквивалентной локальной версией из Saved. HasMappingContext в Python возвращает optional priority: 0 означает присутствующий шаблонный контекст, None — отсутствие; raw priorities 1/0/0 сохранены в evidence.

## Область изменений и ограничения

Игровых ресурсов пять: существующий BP_SurvivalPlayerController и четыре новых ручных Input assets. Остальное — отчёт, ProjectStatus, evidence и runners. Карты, Config, Inventory, A13 и vendor assets без изменений. Политика input locks принадлежит контроллеру; будущим системам следует пользоваться SetSurvivalInputMode, а не независимо накапливать ignore counters. A15–A17 остаются отдельными задачами. PR не объединять автоматически.
