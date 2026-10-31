# A15 — World Pickup

Дата: 30.10.2026
Статус: READY по целевой независимой проверке A15; PR #22. Текущий результат — в разделе закрытия lifecycle BLOCKER; ниже сохранена история проверок.

## Реализация

- BP_WorldPickup: WorldEntityId, Stack, Consumed, PickupInProgress.
- BPI_Interactable: GetInteractionOptions, ExecuteInteraction.
- BP_SurvivalPlayerController: BindWorldPickup, HandleWorldPickupRequest, ValidateWorldPickup.
- Повторная проверка Gameplay, Pawn, focus, range и Visibility.
- Подбор через BPC_Inventory.TryAddExact.
- Уничтожение объекта только после успешного добавления.
- Защита от повторного подбора.

## Ручная проверка PIE

PASS:
- item.wood x3: успешная выдача и удаление объекта.
- Два объекта x3 и x2: итог Snapshot = 5.
- Повторные E: дополнительной выдачи не обнаружено.
- WeightLimit: отказ, объект остаётся.
- Неизвестный ItemId: отказ без удаления объекта.
- Дистанция: отказ на 4 м, успех на 1 м.
- Стена Visibility: блокировка и последующий успех после обхода.
- UI: взаимодействие заблокировано, после закрытия восстановлено.
- Consumed и PickupInProgress: блокировка подбора.
- Blueprint Runtime Error / Accessed None: не обнаружены.

## Регрессия

- A14 Full PIE: 274 PASS / 0 FAIL, overall true, UE exit 0.
- A14 regression: Jump 4/0, A12 548/0, UE exit 0.
- A12 runner: 1644 assertions PASS / 0 FAIL, но итог runner false из-за отсутствующего process_exit_code. Полный статус процесса не подтверждён.
- Git diff --check: OK.
- Git LFS fsck: OK.

## Ограничения

NOT RUN / не подтверждено:
- Точная граница 250 см для A15.
- Полное сравнение Snapshot до/после отказа именно через pickup.
- Отказ при заполнении всех слотов отдельно от WeightLimit.
- Искусственная вложенная команда в inventory callback.
- Повторная смена Pawn и lifecycle подписок в A15.
- Уничтожение цели непосредственно между focus и execute.
- Свежий package, multiplayer и автоматизированная матрица A15.

Тестовые кубы не сохранены в LV_SystemsTest.
Merge только после независимого аудита.

## Независимая проверка и исправление camera trace — 31.10.2026

**Вердикт: NOT READY. Новый BLOCKER; commit/push остановлены.**

В рабочей ветке `task/a15-world-pickup` исправлены только `BPC_Interaction.UpdateFocus` и `BP_SurvivalPlayerController.ValidateWorldPickup`. A15: длина camera ray = `Distance(Camera, Pawn) + 250`. A13: `Max(TraceDistance, Distance(Camera, Pawn) + InteractionDistance)`, при штатном `InteractionDistance = 250`. Обоснование — неравенство треугольника: любая точка в пределах R от Pawn находится не дальше `Distance(Camera, Pawn)+R` от камеры. Направление луча по Rotation/ForwardVector сохранено. Сохранены исходные `Pawn-to-ImpactPoint <= 250`, Visibility от камеры и дополнительная проверка препятствия от Pawn. Контракты инвентаря, TryAddExact и BP_WorldPickup не изменены.

Фактические целевые PIE-проверки UE 5.8.4:

- PASS: измеренные 249,9 / 250 / 250,1 см; A13 focus и A15 validation согласованы. На 249,9 и 250 успешный pickup, на 250,1 отказ с полным rollback.
- PASS: штатная камера (около 400 см позади Pawn), E вызывает pickup; повторные E не дублируют выдачу.
- PASS: низкая стена между Pawn и предметом при сохранённой видимости с камеры блокирует focus и pickup, полный rollback.
- PASS: WeightLimit (`NewEnumerator8`) и все слоты заняты (`NewEnumerator9`), повторный отказ. Полностью совпадают Snapshot (включая InventoryId, Revision, StackId/GUID и количества), pickup Stack, WorldEntityId, flags и счётчик уведомлений. Для изоляции причин в PIE использован runtime BPC_Inventory на реальном PlayerState с 1 слотом и MaxWeight 100; сохранённые инвентарные ассеты не менялись.
- PASS: синхронный reentrant ExecuteInteraction в inventory callback отвергнут, один commit/event. В callback Pickup жив, Consumed=false, PickupInProgress=true; после возврата успеха Pickup уничтожен.
- PASS по состоянию: отсутствие Controller в Context, отсутствие request Pawn и possessed Pawn дают отказ без изменения полного состояния; два possession swap отклоняют старый Pawn, новая E-команда даёт ровно один commit/event.
- PASS по проверенным признакам: без Inventory или Interaction компонентa pickup не consumed, guard не установлен, Actor жив. Полная отдельная матрица отсутствующего PlayerState не запускалась.
- **FAIL / BLOCKER: уничтоженная цель.** Snapshot не меняется, однако реальный вызов HandleWorldPickupRequest после уничтожения сфокусированного Actor даёт четыре PIE Blueprint Runtime Error: `K2Node_DynamicCast_AsBP_World_Pickup` ссылается на pending-kill `BP_WorldPickup_C_1`, узел `ExecuteInteraction`, функция `HandleWorldPickupRequest`. Отсутствие мутации не означает безопасный PASS lifecycle.

Минимальное следующее исправление (не выполнено по требованию остановиться при новом BLOCKER): `IsValid` сфокусированного pickup до чтения WorldEntityId и вызова ExecuteInteraction; недействительная цель должна завершать команду. Затем проверить только уничтоженную цель/повторную команду и целевые затронутые инварианты.

Evidence: [a15_followup_results.json](evidence/a15_followup_results.json). 29 проверок состояния дали true, но итог false из-за отдельного log gate. Подтверждённые сценарии переносились между целевыми сессиями без повторного запуска; inventory/E проверялись в предыдущей сессии, wall/lifecycle — в последней. Одинаковое исправление графов применялось в памяти из одного временного скрипта. После проверок состояния оба графа были сохранены локально до анализа лога; они не опубликованы. Ошибка временного tick-runner `generator already executing` возникла при финальном сохранении, после проверки всех состояний; отдельно сохранена в evidence и не считается игровым дефектом. UE exit 0 не считается PASS тестов.

Не запускались: полная регрессия A09–A14, package, multiplayer, дополнительные направления/смещения камеры сверх геометрического обоснования и штатной камеры. Оригинальные SHA256 BPC_Inventory и BP_WorldPickup после прогона совпадают с head PR `fd6519f2acbd79e672915d494f8009fb0b37b943`.

Изменены локально: `Content/Survival/Interaction/BPC_Interaction.uasset`, `Content/Survival/Core/BP_SurvivalPlayerController.uasset`, этот отчёт, `Docs/ProjectStatus.md`, evidence JSON. Нового commit SHA нет. PR #22 не обновлён; merge запрещён.

## Закрытие lifecycle BLOCKER — 31.10.2026

**Текущий вердикт: READY для A15 / PR #22. Предыдущие NOT READY выше — история обнаружения и устранения дефектов.**

В `BP_SurvivalPlayerController.HandleWorldPickupRequest` добавлен `KismetSystemLibrary.IsValid(FocusedActor)` и последовательная exec-ветка до cast к BP_WorldPickup, чтения WorldEntityId, построения Context и ExecuteInteraction. False (в том числе pending-kill) безопасно завершает void-команду. Контракты и логика Inventory / TryAddExact / BP_WorldPickup не изменены; их прежние SHA256 подтверждены после проверки.

Только затронутый PIE-прогон UE 5.8.4: **10 PASS / 0 FAIL**, процесс UE exit **0**. Весь лог после закрытия редактора проверен: **0** `PIE: Error`, `Accessed None`, `LogBlueprint: Error`.

- Уничтоженный реально сфокусированный Pickup, подтверждённый IsValid=false: три непосредственных вызова команды, затем два нажатия E (Enhanced Input injection) безопасны. Полный Snapshot, включая InventoryId, Revision, GUID стеков и количества, побайтно совпадает с исходным export_text; уведомлений нет.
- Живой pickup через E: точное добавление x3, одна Revision и одно уведомление, Actor уничтожен.
- Повторная команда и две повторные E после успеха: полный Snapshot и число уведомлений неизменны.
- Вложенный ExecuteInteraction в inventory callback: отвергнут; внешний x2 даёт один commit/event. В callback Actor ещё жив, guard=true, consumed=false; после успеха уничтожен.

Evidence: [a15_lifecycle_results.json](evidence/a15_lifecycle_results.json). Ранее полученные результаты границ, препятствий, полного rollback, ёмкости, компонентов и смены Pawn из [a15_followup_results.json](evidence/a15_followup_results.json) повторно не запускались. Его общий false фиксирует исторический lifecycle BLOCKER, теперь закрытый новым прогоном; исторические ошибки не удалялись и не переименовывались в PASS.

Включённые исправления: геометрически обоснованный camera reach A13/A15 из предыдущего этапа и lifecycle guard. Сохранены только BPC_Interaction и BP_SurvivalPlayerController; игровые карты/тестовые Blueprint не сохранялись. Временная оснастка исправляет повторный вход tick при сохранении и не входит в PR.

NOT RUN: полная регрессия A09–A14, package, multiplayer, новая ручная проверка физической клавиши E. Они вне этого целевого изменения. Неизвестных новых BLOCKER нет. Merge не выполнялся и запрещён данным заданием. Commit SHA сообщается после фиксации и сверки опубликованной ветки.
