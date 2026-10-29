# A15 — World Pickup

Дата: 30.10.2026
Статус: реализация и ручная проверка выполнены; PR и независимый аудит ожидаются.

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
