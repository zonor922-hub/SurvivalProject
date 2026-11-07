# A18-ID01 — локальная реализация, проверки и восстановление после аварии

Дата: 07.11.2026 (Europe/Moscow). Версия контракта: [A18-ID01 v1.0](33_A18_ID01_INTERACTION_IDENTITY_SPEC.md), **DESIGN APPROVED владельцем**.
Проект: `D:/Project/SurvivalProject_A18/SurvivalProject.uproject`, ветка `task/a18-storage-container`, HEAD `3cc9e8ea80cff6ac936aa48cbaf586f31839cccd`.

**Итог: READY FOR REVIEW — локальный gate A18-ID01, 15 PASS / 0 PARTIAL.** Недостающие обязательные I01/R01 проверены в изолированной RecoveryCheck01 через MCP на отдельном порту, без изменения рабочего уровня/Blueprint. I05 и S01 остаются PASS. P01 использует явно отмеченный USER-VERIFIED baseline до рефакторинга, а не новый самостоятельный baseline-прогон. UNKNOWN native crash отслеживается отдельно как риск диагностического исполнения; его первопричина не установлена, исправление и tooling-only вина не заявлены. Локальная готовность к рассмотрению не означает DONE, release gate, разрешение на публикацию или завершение Open/Transfer. Актуальная матрица и основания — в последнем разделе этого отчёта.


## Реализованный и восстановленный срез

- В BPI_Interactable добавлена GetInteractionTargetId -> TargetId: Guid, HasStableId: Boolean. Сигнатуры двух прежних функций и структур Context/Result сохранены.
- BP_WorldPickup возвращает существующий WorldEntityId и IsValidGuid. Его остальные графы, HandleWorldPickupRequest и ValidateWorldPickup сохранены по сравнению графов. Guards A15, TryAddExact, commit/event/destroy не переписывались.
- BP_StorageContainer получил Instance Editable WorldEntityId с пустым default. Конкретному authored-сундуку назначен `3B404DA0-C151-4B73-8B0E-A4F116338F43`. Pickup сохранил `6128CE4A-49BB-F079-9579-23AE403CCABB`. Назначения GUID в BeginPlay/Construction/getter нет.
- В HandleInteractionFocusChanged заменён обязательный HUD-cast к pickup: IsValid Actor -> BPI -> IsValid актуального Pawn -> интерфейсный getter -> Context -> GetInteractionOptions. HasStableId AND IsValidGuid выбирает ID, иначе пустой Guid. Существующие prompt, disabled reason и скрытие сохранены. Использованы вручную добавленные Branch/Does Object Implement Interface; EventGraph целиком не перезаписывался.
- BPFL_InteractionIdentity.ValidateInteractionTargetIdentity проверяет Actor, интерфейс, ожидаемый/стабильный ID, точное совпадение, дубликаты среди живых загруженных Actor того же мира и повторную идентичность цели. Совпадающий raw ID другого Actor отклоняется даже при его HasStableId=False. Успех не кэшируется, ID не генерируется. Это не range/LoS/session-авторизация.
- [scripts/a18_id01_validate_ids.py](../../scripts/a18_id01_validate_ids.py) — read-only аудит одного загруженного мира. Он выдаёт обе ссылки при дубликате и не исправляет GUID. После восстановления аудит основного проекта выполнен: PASS для двух загруженных authored Actor; незагруженные карты/cells не охвачены.

WorldEntityId не смешивается с InventoryId/StackId. BPC_Inventory, A11, A36 v1 и GDD не изменялись. BPC_Interaction компилировался как зависимость; его графы не менялись. Open, сессия, Transfer и двухпанельный UI остаются вне ID01; прежний незавершённый ExecuteInteraction сундука не превращён в успешную заглушку.

Зависимости: A13, A15, A16, A17/A17.1; исходные A11 и правила INVENTORY-UX сохранены. A19 не разблокируется этим результатом.

## Достоверность проверок

[Машиночитаемый отчёт](evidence/a18_id01_local_verification_2026-11-07.json) содержит матрицу, hashes, происхождение результатов и ограничения. Полные локальные артефакты находятся в [Saved/Verification/A18-ID01](../../Saved/Verification/A18-ID01/); они не опубликованы.

До аварии выполнены четыре настоящие PIE-сессии. Нажатия E/I подавались через Slate в игровой viewport; Split/Merge/stale проверялись через реальные native OnClicked существующих кнопок и публичные команды. Это не ручные клики мышью. Изолированная Blueprint-фикстура считала настоящие inventory/focus dispatchers; первоначальная Python-подписка не сработала и не использовалась как доказательство событий.

| Проверка | Фактический результат |
|---|---|
| C01 — compile | PASS 6/6 с warnings_as_errors в памяти; повторные compile тех же классов из recovery-копии PASS. Общий commandlet exit 1 отдельно ниже |
| P01 — Pickup/E | PASS до аварии: точный прирост количества, одна Revision и одно inventory-событие, уничтожение pickup; повтор E/запросов без изменения snapshot/events. Независимый прогон до изменения — NOT RUN; прежний Pickup PASS сообщён пользователем |
| P02 — отказы/reentry | PASS: чрезмерный стек отклонён с полным rollback состояния inventory/pickup; вложенный запрос в настоящем callback видит PickupInProgress=True, Consumed=False; один commit/event |
| H01 — trace/HUD | PASS: экспортированы реальные HitActor/ImpactPoint pickup и StorageMesh. Open Chest отображается. 350 см очищает focus. Камера видит сундук над низкой стеной, но Pawn LoS отклоняет цель; удаление стены восстанавливает focus |
| H02 — пустой ID | PASS: prompt и пустой Context на read-only цели; нет inventory-мутации/событий |
| H03 — варианты options | PASS: пустой массив скрывает старый prompt; явная и резервная disabled reason; проверено на временном другом классе с BPI |
| H04 — lifecycle | PASS: null, неинтерактивный и уничтоженный Actor, отсутствующий Pawn/HUD безопасны; ссылки восстановлены. Blueprint observer: стабильная цель не повторяет событие, смена/потеря даёт одно событие |
| I01 — дубликаты | PASS: два authored Actor с одним GUID перечислены с обеими ссылками, валидатор отказывает. Временный Actor удалён в finally, список Actor восстановлен, аудит после cleanup PASS. Также проверен PIE-дубликат |
| I02 — guards/Context | PASS: missing/mismatch/invalid Actor; True+пустой Guid, False+валидный Guid; точное соответствие стабильного Context цели; raw-дубликат даже при False другого Actor |
| I03 — стабильность | PASS: GUID до deferred spawn/BeginPlay сохранён; повторный ReceiveBeginPlay фикстуры и новые PIE-сессии ID не меняют. При холодной загрузке recovery оба authored-ID сохранены |
| I04 — создание/восстановление | PASS только для назначения до spawn и загрузки сохранённого authored-ID карты. Полноценный Save/Load — NOT RUN, вне ID01 |
| I05 — ExecuteInteraction | PARTIAL: пустой ID отклонён настоящим Controller -> ExecuteInteraction; destroyed focus безопасен. На первоначальном этапе прямой вызов pickup ExecuteInteraction с намеренно несовпадающим переданным Context был NOT RUN; последующий прямой тест PASS, см. дополнение. Отдельный новый identity-validator mismatch проверен |
| R01 — A16/A17/A17.1 | Целевая регрессия PASS: I открывает UI (фактическое имя режима — UI), E блокируется, I возвращает Gameplay, после закрытия E работает; Split/Merge — по одному событию, stale Split/Merge без commit/события. Полные A10/A11/A12 и ручные mouse-click проверки — NOT RUN |
| L01 — журнал/устойчивость | 0 Accessed None, 0 Blueprint Runtime Error, 0 PIE: Error в сохранённом полном журнале. **Общий gate FAIL из-за последующего native EXCEPTION_ACCESS_VIOLATION**, а не PASS редактора |
| S01 — область/сохранение | PARTIAL: графы A15 и несвязанные графы совпали; исходные шесть дисковых файлов неизменны. Сохранение/восстановление оригинала и post-restore PIE — NOT RUN |

Ошибки оснастки сохранены в runtime_harness_attempt1/2 и session JSON, не удалены и не выданы за игровые PASS. В частности: неверные Python ScriptName; недоступная Python-подписка; попытка установить закрытый guard/MaxWeight; ошибочное ожидание имени режима Inventory вместо UI; исходная стена без меша из-за Mobility=Static; освобождённый Python-wrapper уничтоженного Actor. Исправленные сценарии повторялись на том же игровом коде. Часть прежних event-assertions с неустановленным Python observer недействительна; доказательства событий — только последующие BP_* проверки Blueprint-фикстуры.

Cook/Windows package NOT RUN и не включены в локальный gate ID01. Проектная уникальность GUID в незагруженных картах/cells и A36 не подтверждены.

## Авария и фактическая сохранность

В 11:33:02 (Europe/Moscow) 07.11.2026 редактор завершился с `EXCEPTION_ACCESS_VIOLATION reading address 0xffffffffffffffff` во время выполнения final_graph_audit.py через SlateInspector Type. В стеке есть PythonScriptPlugin, SlateInspectorToolset и MCP; **точная первопричина не установлена**. Финальный широкий экспорт verification_graphs_final.json не записался. Это не основание объявлять дефектом BPI/HUD, но блокирует общий verdict.

Ранее сохранены live_raw_before.json, live_raw_after.json, live_defaults/disk_defaults, preservation_summary.json и резервные копии шести исходных файлов. При сравнении до/после до аварии изменён только Controller.EventGraph; добавлены getter-графы BPI/pickup/storage, прочие графы пяти исходных Blueprint совпали. Сохранённые defaults до правки совпали с живыми значениями.

Сохранение шести ресурсов через save_assets было отклонено автоматической проверкой: «Сохранение шести Blueprint/карты постоянным образом может перезаписать несохранённые пользовательские изменения, а явного разрешения именно на сохранение этих assets нет». Исторически был отправлен отдельный запрос; теперь владелец явно ответил: «Разрешаю сохранить эти шесть ресурсов». Отказ не обходился. До разрешённого восстановления исходный Content не перезаписывался; SHA256 защищённых файлов совпадали с preflight. Затем применён описанный ниже набор из шести файлов, включая новый BPFL.

Ранее автоматическая проверка отдельно требовала разрешения на read-only консоль и создание BPFL. Владелец явно разрешил оба действия; они выполнены. Отдельное последующее разрешение на шесть ресурсов сняло блокировку именно их сохранения.

Две временные тестовые Blueprint были только в памяти/автосохранениях. Их MCP-delete после обрыва не выполнился; в исходном Content соответствующих файлов нет. Пользовательская старая __A09Test/Listener не удалялась и не менялась намеренно. Все autosave сохранены; дополнительные BPC_Interaction/HUD/Inventory/Listener-копии отдельно заморожены в RecoveryUserAuxiliary и **не включены** в автоматическое восстановление шести A18-пакетов.

## Изолированная проверка перед восстановлением (история)

[Манифест шести замороженных autosave с SHA256](../../Saved/Verification/A18-ID01/RecoverySources/manifest.json) — конкретный набор для последующего согласования восстановления:

| Целевой ресурс | Сохранённый источник |
|---|---|
| Content/Survival/Interaction/BPI_Interactable.uasset | BPI_Interactable_Auto5.uasset |
| Content/Survival/Interaction/BP_WorldPickup.uasset | BP_WorldPickup_Auto5.uasset |
| Content/Survival/Interaction/BP_StorageContainer.uasset | BP_StorageContainer_Auto5.uasset |
| Content/Survival/Interaction/BPFL_InteractionIdentity.uasset | BPFL_InteractionIdentity_Auto6.uasset |
| Content/Survival/Core/BP_SurvivalPlayerController.uasset | BP_SurvivalPlayerController_Auto6.uasset |
| Content/Survival/Maps/LV_SystemsTest.umap | LV_SystemsTest_Auto6.umap |

Они наложены исключительно в Saved/Verification/A18-ID01/RecoveryCheck01. Core/Interaction/Maps в этой копии — собственные файлы; остальные неизменяемые Content-каталоги читаются через junction на исходные. Оригинальные Content/Config не записывались. SecurityToken из копируемой конфигурации исключён.

В recovery_check_results.json: строгая компиляция шести Blueprint PASS; загрузка карты и identity-аудит PASS; оба authored Actor имеют прежние ID, HasStableId=True и ValidateInteractionTargetIdentity=True. Эти узкие проверки прошли. **Общий Unreal commandlet exit 1**: две startup-ошибки GameFeatureData/PrimaryAssetTypesToScan также наблюдались в исходных preflight commandlet. Они не исправлялись и не скрывались; общего чистого UE PASS нет. Первые две попытки проверки имели ошибку позиционного вызова скрытого WorldContext в оснастке; после холодной загрузки установлен порядок TargetActor, ExpectedTargetId, WorldContext. Это не изменение Blueprint-контракта.

Приведённая выше матрица относится к состоянию до аварии. Новые post-restore проверки основного проекта приведены отдельно ниже; происхождение результатов не смешивается.

## Файлы и Git

Сохранены шесть игровых файлов: BPI_Interactable (getter), BP_WorldPickup (getter без изменения A15), BP_StorageContainer (стабильный WorldEntityId/getter), новый BPFL_InteractionIdentity (валидатор), BP_SurvivalPlayerController (универсальный HUD), LV_SystemsTest (authored-ID сундука). Изменены спецификация 33, этот отчёт 34, ProjectStatus, evidence JSON; добавлен scripts/a18_id01_validate_ids.py. Config/DefaultEngine.ini и .uproject сохраняют исходный numstat 1/0 и 12/0 и не правились агентом. BPC_Interaction/BPC_Inventory/A11/A36/GDD не сохранены и не изменены задачей.

Git status перед этапом реализации:

```text
## task/a18-storage-container...origin/main
 M Config/DefaultEngine.ini
 M Content/Survival/Maps/LV_SystemsTest.umap
 M Docs/ProjectStatus.md
 M SurvivalProject.uproject
?? Content/Survival/Interaction/BP_StorageContainer.uasset
?? Docs/Architecture/33_A18_ID01_INTERACTION_IDENTITY_SPEC.md
```

После восстановления git status:

```text
## task/a18-storage-container...origin/main
 M Config/DefaultEngine.ini
 M Content/Survival/Core/BP_SurvivalPlayerController.uasset
 M Content/Survival/Interaction/BPI_Interactable.uasset
 M Content/Survival/Interaction/BP_WorldPickup.uasset
 M Content/Survival/Maps/LV_SystemsTest.umap
 M Docs/ProjectStatus.md
 M SurvivalProject.uproject
?? Content/Survival/Interaction/BPFL_InteractionIdentity.uasset
?? Content/Survival/Interaction/BP_StorageContainer.uasset
?? Docs/Architecture/33_A18_ID01_INTERACTION_IDENTITY_SPEC.md
?? Docs/Architecture/34_A18_ID01_LOCAL_IMPLEMENTATION_REPORT.md
?? Docs/Architecture/evidence/a18_id01_local_verification_2026-11-07.json
?? scripts/a18_id01_validate_ids.py
```

Индекс пуст; HEAD прежний. Commit/push/PR/merge не выполнялись. Значение SecurityToken не включено в отчёт/evidence. Нужен отдельный безопасный возврат SEC01 перед публикацией; текущую Config не коммитить.

## Восстановление и повторные проверки основного проекта

Владелец явно разрешил сохранить ровно шесть ресурсов. Перед записью проверены ветка/HEAD, отсутствие редактора, hashes всех исходных защищённых файлов и RecoverySources. Создана дополнительная копия pre_restore_20261107_120804; шесть файлов записаны по явному списку. [Манифест восстановления](../../Saved/Verification/A18-ID01/primary_restore_manifest.json). Все шесть SHA256 после PIE совпадают с замороженными копиями. Дополнительные user-autosave не применялись и сохранены отдельно. После паузы редактор был повторно открыт; MCP подтвердил основной проект. Повторное сохранение всех dirty-пакетов не выполнялось.

Результаты: [PrimaryPostRestore](../../Saved/Verification/A18-ID01/PrimaryPostRestore/). Blueprint compile с warnings_as_errors: **PASS 6/6**, карта загружена, два authored-ID ожидаемые, валидатор возвращает True. Три настоящих PIE после восстановления:

| Сценарий | Результат |
|---|---|
| Session1: identity, trace/HUD, пустой ID, null/non-interface/destroyed, Pawn, реальная E | 30 PASS; два event/reentry пункта NOT RUN в этой сессии, затем проверены Session2 |
| Session2: Blueprint-счётчики focus/инвентаря, A15 reentry, E/repeat, пустой ID отказ | PASS: одно событие при переходе focus, один commit/event при E; повтор без дублирования; вложенный запрос видит PickupInProgress=True |
| Session2: Split/Merge/stale, read-only другой BPI-класс, malformed getter, missing HUD, range/LoS, I/UI/E/закрытие | PASS; число событий Split/Merge по одному, stale без изменения snapshot/events |
| Session2: oversized | HARNESS_ERROR: использован освобождённый pickup-wrapper после успешного подбора; это не игровой PASS/FAIL. Повторён Session3 |
| Session3: identity/дубликаты/deferred spawn/repeated BeginPlay и oversized rollback на живом pickup | 15 PASS |
| Журнал нового редактора | 0 Accessed None, 0 Blueprint Runtime Error, 0 PIE: Error, 0 нового native access violation. Существующая GameFeatures startup-ошибка остаётся; общий чистый Editor PASS не заявляется |

Session2 содержит 41 PASS и одну сохранённую ошибку оснастки. Тестовые Blueprint загружены из старых autosave в /Temp, без создания файлов в Content. Широкий аварийный экспорт не повторялся. Результаты сессий и исключения сохранены, NOT RUN не превращены в PASS.

## Остаточные риски и ручная проверка

Не закрыты: причина прежнего native crash; глобальная уникальность в незагруженных картах/cells; полный Save/Load и исторические A10/A11/A12 suites. Cook/package NOT RUN, вне локального ID01 gate. Open/внешняя сессия/Transfer требуют отдельного технического контракта и не завершены.

Человеку: в Blueprint нажать «Компилировать»; на LV_SystemsTest запустить «Играть», проверить prompt pickup/сундука, E и повторную E, потерю focus, I/закрытие inventory и возврат управления; проверить «Журнал вывода». Сверить сохранность своих незавершённых графов и auxiliary-autosave. Open сундука успешным не считать. До закрытия остаточного gate задача не объявляется завершённой; публикация не выполняется.

Финальная проверка документации: PASS — 87 локальных ссылок, whitespace/diff, синтаксис audit-скрипта, JSON, шесть SHA256, неизменный BPC_Interaction, пустой индекс/прежний HEAD, отсутствие тестовых файлов в Content. Первая попытка verifier получила UnicodeDecodeError из-за cp1251; повтор с явным UTF-8 прошёл. PIE остановлен.

## Дополнение: три шага A18-ID01, 07.11.2026

**1 — Native export crash: UNKNOWN.** Исследованы сохранённый EditorCrash_2026-11-07.log, оба CrashContext.runtime-xml и final_graph_audit.py; экспорт не повторялся. В 11:29:38 МСК был handled ensure PythonScriptPlugin, MTAccessDetector.h:624: «race detected ... or ... trivially relocated», 65654 readers. Это диагностическая альтернатива, а не доказанная гонка. Через ~201 секунду, в 11:33:02 МСК, падение reading 0xffffffffffffffff: верхний frame python311.dll+0x67865, ниже PythonScriptPlugin, OutputLog, SlateInspector/MCP. Последний PIE завершён в 11:32:16, команда экспорта начата в 11:33:00.504. Скрипт обходит восемь Blueprint, их графы/пины и CDO; нет прогресса по узлам, запись JSON только в конце. Ни конкретная строка Python, ни Actor/узел виновника не установлены. Проблема lifetime/refcount Python-wrapper или порчи памяти возможна; причинная связь с BPI/HUD не доказана. Старый hidden self-pin также не доказанная причина. [Диагностика и извлечённые стеки](../../Saved/Verification/A18-ID01/native_crash_analysis.json).

**2 — Прямой отрицательный pickup-тест: PASS.** Одна завершённая прямая попытка в PIE через MCP/Slate Python: ExecuteInteraction(Context, Pickup) на настоящем BP_WorldPickup. В Context корректные Controller и текущий Pawn, TargetId подменён на GUID другого реального Actor — сундука. Pickup является актуальной целью focus. Типизированная структура получена через Struct.copy() временной /Temp Blueprint; производственные графы и интерфейс не менялись. Результат: Success=False, Message=Invalid target ID, ErrorCode=None (существующее поведение A15). Полный Inventory snapshot до/после одинаков, Revision=0, inventory callbacks 0→0; pickup жив, Stack/WorldEntityId/Consumed/PickupInProgress неизменны. Предмет не выдан. [Полное доказательство](../../Saved/Verification/A18-ID01/direct_negative_context_results.json), [тест](../../Saved/Verification/A18-ID01/direct_negative_context.py).

Неудачная подготовка до обновления кадра камеры остановилась на предусловии до ExecuteInteraction и сохранена в attempt1. Пробное редактирование структуры CDO отклонено защитой template; применена независимая копия. После состоявшегося вызова оснастка ошибочно ожидала ErrorCode=TargetIdMismatch, хотя контракт этого не требует: исходный результат сохранён в attempt2; итог пересчитан по отказу/сообщению/snapshot/events без повторного игрового вызова. Эти ошибки оснастки не скрыты и не объявлены дефектом игры.

**3 — Отчёт и блокеры: обновлены локально.** Подтверждённые PASS не прогонялись заново. Новый игровой код не записывался; все шесть SHA256 совпадают с восстановленным набором. PIE остановлен. Изменения текущего продолжения: этот отчёт, спецификация 33 (только статус), Docs/ProjectStatus.md и evidence JSON; локальная оснастка/логи — в Saved/Verification/A18-ID01. Config/SecurityToken/SEC01 не изменялись, commit/push/PR/merge и публикация отсутствуют.

Следующий блокер — UNKNOWN первопричина native-аварии; для дальнейшего расследования нужен офлайн-разбор minidump с соответствующими Python/UE символами, без повторения широкого экспорта. Оставшиеся прежние ограничения по Save/Load, незагруженным картам/cells и отдельному контракту Open/сессии не сняты. После этих трёх шагов работа остановлена.

## Историческая сверка после отчёта 34: три шага (заменена текущим gate ниже)

### 1. Offline native crash investigation — UNKNOWN

Оба UEMinidump.dmp существуют (ensure 783241 байт; crash 1795681 байт). Прочитаны Windows dbghelp.dll/MiniDumpReadDumpStream, исключение, контекст x64, модули, CodeView и включённые диапазоны памяти; процесс редактора не запускался. Применены MSVC dumpbin (headers/exports/disassembly) и LLVM symbolizer. [Разбор дампов](../../Saved/Verification/A18-ID01/offline_minidump_analysis.json), [дизассемблирование](../../Saved/Verification/A18-ID01/python311_fault_disassembly.txt), [обновлённая диагностика](../../Saved/Verification/A18-ID01/native_crash_analysis.json).

В crash-дампе 0xC0000005, поток 19144, RIP=python311.dll+0x67865. Локальная DLL совпадает по timestamp 0x65C2AD06 и CodeView GUID/age. Инструкция mov rcx,[r8], r8=0x7000000265b73de8; включённая в dump память [rax+8] содержит тот же некорректный указатель. Это локализует место отказа во внутренней allocator-like процедуре Python (вывод по дизассемблированию), но не источник записи/повреждения. Ближайший экспорт PyType_GenericAlloc+0x355 не является доказанным именем текущей внутренней функции. Предшествующий ensure PythonScriptPlugin/MTAccessDetector остаётся корреляцией. SlateInspector и MCP в стеке — вызывающий транспорт, не доказательство их вины. Игровой Blueprint в качестве причины не установлен.

Не хватает python311.pdb GUID **0A53B3B3-C6F6-4F54-B771-AD15EFDA80D8**, age **1**, и совпадающих PDB PythonScriptPlugin/SlateInspector/MCP, идентификаторы которых извлечены в native_crash_analysis.json. В проверенных каталогах UE/Python их нет. LLVM не загрузил PDB/DIA: HRESULT 0x8007007E, NoRegCoCreate; WinDbg/CDB в проверенных путях не найдены. Для продолжения нужен совместимый x64 debugger/DIA с этими символами. Если малого дампа недостаточно для определения писателя — полный dump/trace будущего отдельно разрешённого случая, без повторения широкого экспорта. Категория аварии: **UNKNOWN**, не подтверждённый игровой дефект и не подтверждённый дефект только диагностической оснастки.

### 2. Актуальная матрица 15 критериев

Эта таблица заменяет исторические PARTIAL/NOT RUN только для текущего решения; исходные результаты попыток выше сохранены. Новые PIE/compile не запускались. [Полная матрица с evidence](../../Saved/Verification/A18-ID01/final_acceptance_matrix.json).

| ID | Сейчас | Основание и предел |
|---|---|---|
| C01 | PASS | Post-restore strict compile 6/6. |
| P01 | PASS | Реальная E, точная выдача, Revision/event по одному, repeat без выдачи. До изменения — USER-VERIFIED из исходного сообщения, самостоятельного baseline snapshot нет. |
| P02 | PASS | Post-restore BP reentry и oversized rollback на живом pickup; исправленная оснастка Session3. |
| H01 | PASS | Сохранённые реальные trace/focus pickup/storage, prompt, range/LoS. |
| H02 | PASS | Read-only другой класс: пустой Context, prompt, snapshot/events неизменны. |
| H03 | PASS | Empty options, explicit/fallback disabled reason, non-interface/null/потеря focus. |
| H04 | PASS | Invalid/destroyed Actor, Pawn/HUD, восстановление ссылок и BP focus counters. |
| I01 | PARTIAL | Разные классы authored — PASS до аварии; один класс PIE — PASS после. Отдельный authored same-class подслучай не записан; это PARTIAL покрытия, не FAIL игры. |
| I02 | PASS | Уникальный/missing/mismatch/malformed/raw duplicate ID, отказы без мутации. |
| I03 | PASS | Между PIE ID сохранены, repeated BeginPlay/deferred fixture и статическая сохранность getter/присваиваний. |
| I04 | PASS | Назначение ID до spawn и загрузка заранее сохранённого authored-ID. Не тест полного Save/Load. |
| I05 | PASS | Прямой mismatch ExecuteInteraction: отказ, snapshot/Revision/Stack/guards неизменны, 0 событий; empty-ID/Controller и destroyed focus безопасны. |
| R01 | PARTIAL | UI/E/возврат ввода, Split/Merge/stale и per-command events PASS. Накопление callbacks после повторных открытий в одной PIE отдельно не измерено: PARTIAL. |
| L01 | PASS | Blueprint Runtime Error/Accessed None отсутствуют в сохранённых интервалах. Native ensure/crash отдельно UNKNOWN; общего чистого Editor PASS нет. |
| S01 | PASS | Повторно пересчитаны before/after preservation и равенство defaults; текущие шесть hashes совпадают с RecoverySources; резервные копии сохранены. Изменения HUD/getter/карты объяснены. Новый опасный экспорт не нужен. |

Источники: PrimaryPostRestore/session1–3, recovery_check_results.json, trace_pickup/storage.json; authored_duplicate_audit.json (исторический cross-class editor-тест с cleanup); direct_negative_context_results.json (актуальный I05); preservation_summary.json, live_raw_before/after, live_defaults/disk_defaults, primary_restore_manifest и RecoverySources/manifest (S01). Равенство hashes привязывает проверенные бинарные ресурсы к текущему диску; это не новый экспорт всех текущих графов. BPC_Interaction и несвязанные A11/A36/inventory не менялись задачей. Исходные Config/.uproject пользовательские изменения остаются исключёнными из пакета.

### 3. Историческое решение — BLOCKED (до закрытия I01/R01)

Основание: точное покрытие I01/R01 неполно, поэтому условие «все критерии закрыты» для READY FOR REVIEW не выполнено. Native crash также нельзя пока обоснованно назвать исключительно tooling-дефектом. При этом L01 сформулирован как проверка Blueprint Runtime Error/Accessed None/pending-kill: native crash не превращён молча в Blueprint FAIL и не используется как доказательство CHANGE REQUIRED. Подтверждённого дефекта игрового кода нет.

Владельцу: рассмотреть UNKNOWN native-риск с совпадающими PDB/отладчиком; для следующего отдельного среза согласовать точечное закрытие authored same-class duplicate и same-PIE repeated-open callback подслучаев либо явно утвердить изменение критериев. До этого не объявлять задачу завершённой. Open/сессия/Transfer, полный Save/Load и глобальная уникальность незагруженных карт остаются вне закрытого среза. SEC01 и проверка всей исходящей истории — отдельные обязательные этапы перед любой публикацией, здесь не выполнялись.

Git status до/после этого продолжения одинаков по списку путей (полный список выше и в final_acceptance_matrix.json). Ветка task/a18-storage-container, HEAD 3cc9e8ea80cff6ac936aa48cbaf586f31839cccd; индекс пуст. Изменены в этом продолжении только отчёт 34, Docs/ProjectStatus.md и evidence JSON, локальные диагностические результаты в Saved. Blueprint, Config/SecurityToken, пользовательские autosave не менялись. Commit/push/PR/merge отсутствуют. После трёх шагов работа остановлена.

## Актуальный acceptance gate: закрытие I01/R01, три шага

Этот раздел и matrix_current/matrix/final_acceptance_matrix в evidence — единственный текущий verdict. Предыдущие PARTIAL/NOT RUN/BLOCKED выше — история на тот момент, не актуальные блокеры. Исходная матрица 13 PASS/2 PARTIAL сохранена в MissingCasesIsolated/matrix_before_missing_cases.json.

**Шаг 1 — требования уточнены.** I01 требует выявления двух authored Actor как одного, так и разных классов с совпадающим GUID; отсутствовал только same-class editor/authored подслучай. R01 требует отсутствия накопления callbacks при повторном открытии; отсутствовал только same-PIE repeated-open подслучай. Охват ID01 — загруженные Actor одного мира. Project-wide GUID-аудит незагруженных карт/cells, полный Save/Load, полные исторические A10/A11/A12 suites и будущий Open/Transfer в эти пробелы не включались. Утверждённый контракт не расширен.

**Шаг 2 — только недостающие проверки, PASS.** Использована существующая изолированная RecoveryCheck01 с собственными Core/Interaction/Maps и read-only доступом к неизменяемым зависимостям. Шесть файлов реализации побайтно соответствуют основному восстановленному набору. Собственный редактор запущен с NoAutoSave, MCP порт 8001; основной редактор/рабочая карта не использовались. Две существующие агентские Blueprint-фикстуры скопированы в тестовый Content, без изменения исходных autosave. Игровые Blueprint не редактировались и не сохранялись.

| Подслучай | Вход/ожидание | Наблюдение |
|---|---|---|
| I01 same-class authored | В editor-world копии LV_SystemsTest второй BP_StorageContainer с GUID первого; аудит должен вывести обе ссылки, validator — DuplicateTargetId | PASS: обе ссылки, аудит FAIL как ожидаемый отрицательный результат, оба PIE-storage validator False/DuplicateTargetId |
| I01 отсутствие побочных эффектов | Snapshot игрока и двух StorageInventory, настоящие BP inventory-observers | PASS: все три snapshot до/после равны, inventory events 0→0 / 0→0 / 0→0 |
| R01 повторное открытие | Шесть настоящих I-open/close в одном PIE-world; один widget, снимок/события/полный экспорт delegate bindings неизменны | PASS: каждый цикл UI→Gameplay, тот же widget; InventoryChanged/Split/Merge bindings по одному, без накопления |
| R01 действие после повторных открытий | По одному native OnClicked broadcast существующих Split/Merge после шести циклов; ожидаются +1 Revision/event и сумма 2 предмета | PASS: Split +1/+1, Merge +1/+1, сумма 2; DisplayedRevision актуальна, bindings не изменились. Это вызов native delegate, не физический mouse-click |

R01 фактические счётчики: baseline после подготовительного заполнения inventory — 1; после шести циклов — 1; после Split/Merge — 3. Подготовительное заполнение не включено в число событий UI-команд. Полные входы, GUID, ссылки Actor, snapshots и bindings — [I01](../../Saved/Verification/A18-ID01/MissingCasesIsolated/i01_final.json), [R01](../../Saved/Verification/A18-ID01/MissingCasesIsolated/r01_final.json), [итог изоляции](../../Saved/Verification/A18-ID01/MissingCasesIsolated/verification_summary.json).

Изолированная PIE остановлена. Временный editor-дубликат удалён, исходный список Actor копии восстановлен, аудит после cleanup PASS. Дисковые hashes шести файлов рабочего проекта и изолированной копии неизменны. В полном новом логе ноль Accessed None, Blueprint Runtime Error, PIE: Error, pending-kill ошибок и native access violation. Это не повторная приёмка старых PASS и не доказательство устранения прежнего native crash. Начальная попытка остановилась на assert неверной стартовой карты до изменения Actor; затем загружена собственная LV_SystemsTest. Ошибка выбора console/focus исправлена выбором главного окна; история оснастки сохранена в логе.

**Шаг 3 — актуальная матрица и READY FOR REVIEW.**

| ID | Текущий результат | Актуальное основание |
|---|---|---|
| C01 | PASS | Существующий post-restore strict compile 6/6. |
| P01 | PASS | Существующий post-restore E/repeat/count PASS; pre-refactor baseline USER-VERIFIED, не отдельный измеренный прогон. |
| P02 | PASS | Существующий BP reentry/oversized rollback PASS. |
| H01 | PASS | Существующие реальные trace/HUD/range/LoS PASS. |
| H02 | PASS | Существующий read-only empty Context без inventory/events PASS. |
| H03 | PASS | Существующие options/disabled/non-interface/miss PASS. |
| H04 | PASS | Существующий invalid/destroyed/Pawn/HUD/focus lifecycle PASS. |
| I01 | PASS | Same-class authored новый изолированный PASS + прежний different-class authored PASS. |
| I02 | PASS | Существующие unique/missing/mismatch/malformed/duplicate guards PASS. |
| I03 | PASS | Существующая ID stability/lifecycle/static preservation PASS. |
| I04 | PASS | Существующая deferred assignment/authored reload PASS, не полный Save/Load. |
| I05 | PASS | Существующий прямой отрицательный pickup Context PASS; не повторялся. |
| R01 | PASS | Прежние UI/stale PASS + новый isolated same-PIE repeated-open/bindings/counters PASS. |
| L01 | PASS | Полные сохранённые игровые интервалы и новый isolated log без Blueprint Runtime Error/Accessed None/pending-kill. UNKNOWN native отдельно. |
| S01 | PASS | Существующий preservation PASS; текущие hashes основного и изолированного наборов ещё раз совпали. |

Незакрытых PARTIAL нет. [Полная актуальная матрица с источниками](../../Saved/Verification/A18-ID01/final_acceptance_matrix.json). Все прежние утверждения о неподтверждённых same-class/repeated-open подслучаях заменены этими доказательствами, без переименования исторических попыток в PASS.

**UNKNOWN native crash и L01.** Точный L01 требует ноль Blueprint Runtime Error / Accessed None / pending-kill обращений, а не обязательного установления причины любого native-сбоя диагностики. Прежний crash случился в CPython при независимом широком read-only экспорте после PIE; причинный компонент/писатель неизвестен. По имеющимся данным он не подтверждает нарушение перечисленных игровых требований. Поэтому он не блокирует передачу локального ID01 на review и отслеживается отдельно как риск диагностического исполнения. Это не доказанный tooling-only дефект, не доказанный игровой дефект и не утверждение, что runtime-причина исключена. Широкий экспорт запрещён до безопасного отдельного расследования; владельцу остаются выводы offline_minidump_analysis/native_crash_analysis и точные недостающие PDB из предыдущего раздела.

Владельцу: рассмотреть реализацию и отдельно остаточный UNKNOWN native-риск; при необходимости предоставить совпадающие символы/совместимый debugger для самостоятельного расследования. Перед публикацией обязательны отдельные SEC01 и полная проверка исходящей истории, whitelist/LFS и разрешение на публикацию. Здесь эти этапы не выполнялись. Open/сессия/Transfer и A19 не считаются завершёнными/разблокированными. Глобальная уникальность незагруженных карт, полный Save/Load и полный исторический runtime-suite не объявлены PASS.

Git status по путям до/после текущего продолжения одинаков (полный список в текущей матрице); ветка task/a18-storage-container, HEAD 3cc9e8ea80cff6ac936aa48cbaf586f31839cccd, индекс пуст. Изменены только отчёт 34, Docs/ProjectStatus.md и evidence JSON; локальные тесты/логи — Saved/Verification/A18-ID01/MissingCasesIsolated. Рабочие Blueprint/карта, Config/SecurityToken, пользовательские autosave не менялись. Commit/push/PR/merge отсутствуют. После трёх шагов остановлено.
