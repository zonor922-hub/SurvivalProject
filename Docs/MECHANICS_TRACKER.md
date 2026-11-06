# SurvivalProject — единый реестр игровых механик

> Обновлено: **06.11.2026** (INVENTORY-UX PR #36 merged, A17.1 PR #37 merged; Design Gate PR #29 на review; остальные исторические статусы без пересмотра). База GitHub `main` перед синхронизацией: `16c51bc39244ca107c427777abadc033960995a4`.
> **ВНИМАНИЕ:** GDD APPROVED ≠ IMPLEMENTED ≠ TESTED ≠ MERGED. Завершённый MVP означает закрытый **согласованный объём**, а не готовность полной механики или игры.

## Правило ведения
- Источник правды: **GitHub**, этот реестр + [ProjectStatus.md](ProjectStatus.md) + конкретные GDD и отчёты. Доска Notion служит удобной копией; автоматической двусторонней синхронизации нет.
- При новом утверждении GDD обновлять только проектный статус; **не** выдавать это за изменение Blueprint.
- При реализации отмечать локальный статус, запуск проверок и публикацию в `main` **отдельно**. Исторические PASS не превращать в новые PASS.
- Перед следующим обсуждением читать этот реестр, не спрашивать вновь о закрытых решениях. Если обнаружен конфликт, указывать код и затронутые зависимости, не переписывать молча.
- При межсистемных изменениях сверять Inventory, BP01, SLEEP01, TIME01, DEATH01, UI, сохранения A36–A40, тесты. См. [CHANGE_CONTROL](GDD/CHANGE_CONTROL_2026-11-05.md).
- Поля «Сделано» и «Осталось» отражают статус на дату среза. Отсутствие свежего аудита значит **не подтверждено**, а не «заведомо не реализовано».

## Трекер (27 механик и рабочих срезов)
| Код | Механика | GDD | Unreal | Проверки | GitHub | Объём закрыт | Этап | Сделано | Осталось | Источник |
|---|---|---|---|---|---|---|---|---|---|---|
| A05–A07 | Предметы и каталог | Утверждено | MVP в main | PASS истор. | В main | Да | Завершён MVP | Типы предметов, каталог, доставка в сборку | Новые определения и баланс по мере развития | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/Architecture/09_A05_ITEM_TYPES.md) |
| A08–A12 | Инвентарь: ядро и операции | Утверждено | MVP в main | PASS истор. | В main | Да | Завершён MVP | Стопки, слот/вес, split/merge, перенос, инварианты | Не менять точные контракты при внедрении BP01 | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/Architecture/22_A12_INVENTORY_TESTS.md) |
| A17 | Экран инвентаря MVP | Утверждено | MVP в main | PASS владелец | В main | Да | Завершён MVP | Read-only экран; пользовательская PIE 10/10; PR #28 merged | Расширенные операции отнесены к A17.1 | [документ](https://github.com/zonor922-hub/SurvivalProject/pull/28) |
| INV-UX01 | Инвентарь UX: Drag/Hotbar/Inspect/Sort/Core+Bag/External | Утверждено | Не начато | NOT RUN | PR #36 merged | Нет | DESIGN APPROVED / UE OPEN | Владелец утвердил GDD правил интерфейса и операций 06.11.2026; docs-only PR #36 | Реализовать отдельно от A17.1, сохранить A05–A12/BP01 и выполнить новые PIE | [GDD](GDD/INVENTORY_UX_DECISIONS_2026-11-06.md) |
| A17.1 | UI Split/Merge + stale Revision | Утверждено | UI в main | Отчёт Sol: compile 4/4, UI 15/15, A12 1644, A10 272 PASS; Windows package NOT RUN | PR #37 merged | Да (scope A17.1) | Опубликован MVP | Изолированные WBP_Inventory/WBP_InventorySlot опубликованы; PR #37 объединён 06.11.2026 | Полные машинные доказательства и Windows package не опубликованы; новые INVENTORY-UX вне A17.1 | [PR #37](https://github.com/zonor922-hub/SurvivalProject/pull/37) |
| A13–A16 | Взаимодействия, подбор, HUD | Утверждено | MVP в main | PASS истор. | В main | Да | Завершён MVP | Focus, Input, World Pickup, HUD | Дополнительные проверки жизненного цикла; новый BP01 pickup отдельно | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/Architecture/25_A15_WORLD_PICKUP.md) |
| A24 | Плавание | Утверждено | MVP в main | PASS истор. | В main | Да | Завершён MVP | Базовые переходы в воде, прохождение берегов | Анимация MVP; кислород/утопление не реализованы | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/Architecture/13_A24_SWIMMING.md) |
| BP01 | Рюкзаки и контейнеры | Частично | Не начато | NOT RUN | Дизайн в main | Нет | Требует проектирования | InventoryId, Core→Bag fallback по capacity, перенос в мир; S1→S2/P1 как roadmap | Открытые правила, UI, UE, Save/Load, проверки | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/BP01_Backpacks_Decisions_2026-11-05.md) |
| SLEEP01 | Сон и усталость | Утверждено | Не начато | NOT RUN | Дизайн в main | Нет | Готов к реализации | Утверждён полный GDD, сон 1–8 ч, кровать, спальник, риски, UI и сохранения | Реализация в UE/PIE; числовой баланс TUNING | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/SLEEP01_Sleep_2026-11-05.md) |
| TIME01 | Мировое время | Частично | Не начато | NOT RUN | Дизайн в main | Нет | Требует проектирования | TIME-D01: пропуск времени только сном | Длительность суток, WorldClock, интеграция с сохранениями | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/TIME01_WorldClock_2026-11-05.md) |
| DEATH01 | Смерть и потеря вещей | Частично | Не начато | NOT RUN | Дизайн в main | Нет | Требует проектирования | Принцип потери всего носимого и отсутствия страховок | DeathCache, TTL, повторная смерть, UI, интеграция и тесты | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/DEATH01_LostGear_Decisions_2026-11-05.md) |
| A23 | Базовое возрождение | Концепция | Не подтверждено | Неизвестно | Не подтверждено | Нет | Требует аудита | В документах упомянут исторический runtime-контракт respawn | Проверить фактические ассеты A23 и согласовать новые SLEEP/DEATH | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/ProjectStatus.md) |
| A36–A40 | Сохранения Save/Load | ТЗ утверждено | Не начато | NOT RUN | Документация в main | Нет | Готов к реализации | Архитектура A36: DTO, версии, тест-план | Реализация, миграции, PIE и атомарная интеграция | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/Architecture/15_A36_SAVEGAME_ARCHITECTURE.md) |
| A20–A21 | Здоровье, потребности, Stamina | Частично | Не подтверждено | Неизвестно | Не подтверждено | Нет | Требует аудита | В SLEEP01 согласованы принципы расхода и восстановления во сне | Аудит фактической UE-реализации, отдельные GDD/баланс | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/SLEEP01_Sleep_2026-11-05.md) |
| BUILD01 | Строительство базы | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Модульное строительство входит в общую концепцию GDD | Фундамент, стены, крыша, прочность, размещение, безопасность | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| CRAFT01 | Крафт и производство | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Крафт входит в концепцию; рецепт спальника предварительный | Верстаки, рецепты, инструменты, прогрессия | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| STORAGE01 | Сундуки и хранилища | Частично | Не начато | NOT RUN | Нет | Нет | Требует проектирования | A11 основа; утверждён внешний UI/прямой Drag как GDD (#36) | Физические сундуки, вместимость, доступ/дистанция, Save/Load, UE | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/Architecture/21_A11_TRANSFER.md) |
| GATHER01 | Добыча ресурсов | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Задумана в общей survival-концепции | Деревья, камни, руда, растения, инструменты | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| COMBAT01 | Боевая система | Не проработано | Не начато | NOT RUN | Нет | Нет | К обсуждению | Отдельных утверждённых правил нет | Удары, блок, уклонения, урон, оружие и ИИ | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| WEATHER01 | Погода и температура | Не проработано | Не начато | NOT RUN | Нет | Нет | К обсуждению | SLEEP01 предусматривает пробуждение от непогоды | Погода, температура, укрытия, последствия | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/SLEEP01_Sleep_2026-11-05.md) |
| FOOD01 | Еда, вода и готовка | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | В SLEEP01 согласован расход Hunger/Thirst во время сна | Готовка, порча, источники воды, баланс | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/SLEEP01_Sleep_2026-11-05.md) |
| EQUIP01 | Экипировка и прочность | Частично | Не начато | NOT RUN | Нет | Нет | Требует проектирования | Утверждены UX Equip/Unequip, Compare и Hotbar broken GUID (#36) | Слоты экипировки, прочность и числовой баланс ремонта, Unreal/тесты | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GDD/BP01_Backpacks_Decisions_2026-11-05.md) |
| FARM01 | Фермерство | Не проработано | Не начато | NOT RUN | Нет | Нет | К обсуждению | Утверждённого дизайна нет | Посев, рост, урожай, животноводство | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| EXPLORE01 | Исследование мира | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Исследование является частью общей концепции | Карта, ориентирование, регионы, открытия | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| PROGRESS01 | Развитие персонажа | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Запланирована поздняя прогрессия | Навыки, рост характеристик, технологии | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| WORLD01 | Экосистема и живой мир | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Идея угроз и живого мира в концепции | Поведение существ, спавн, реакция мира | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |
| ECHO01 | Узлы Эха | Концепция | Не начато | NOT RUN | Нет | Нет | К обсуждению | Узлы Эха запланированы как часть поздней прогрессии | Разработать отдельный GDD, интеграцию и сохранение | [документ](https://github.com/zonor922-hub/SurvivalProject/blob/main/Docs/GAME_DESIGN_DOCUMENT.md) |

## Открытые принципиальные вопросы
- **SLEEP01:** GDD закрыт на уровне проектирования; только числа и интеграция в рамках будущих задач. Дополнительный раунд утверждения базовых правил не нужен. Реализация и PIE — NOT RUN.
- **BP01:** утверждены контейнер Bag, маршрут Core→Bag только по отказу вместимости, roadmap S1→S2/P1. Этап S3 (частичный world pickup) не утверждён.
- **TIME01:** единственный игровой пропуск времени — сон. 60 реальных минут/сутки — **кандидат**, не окончательная норма.
- **DEATH01:** потеря носимого имущества является целевой нормой, но модель DeathCache, DEATH-D05-B1, TTL 3 игровых дня, повторные смерти, UX остаются **OPEN**. Исторический A23 не становится новой реализацией сам по себе.
- **A17.1:** PR #37 объединён в main; локальный отчёт Sol фиксирует проверки, но полный машинный пакет доказательств и Windows package не опубликованы. PR #29 относится к DOC02 и не является PR игровой реализации A17.1.
- **A36–A40:** принятая архитектура v1 ещё не реализована; любые новые поля/DTO и миграции требуют отдельного решения.

## Ссылки для сверки
- [ProjectStatus](ProjectStatus.md) — исторические тесты и PR.
- [GAME_DESIGN_DOCUMENT](GAME_DESIGN_DOCUMENT.md) — игровая концепция.
- [SLEEP01](GDD/SLEEP01_Sleep_2026-11-05.md), [BP01](GDD/BP01_Backpacks_Decisions_2026-11-05.md), [TIME01](GDD/TIME01_WorldClock_2026-11-05.md), [DEATH01](GDD/DEATH01_LostGear_Decisions_2026-11-05.md).
- [CHANGE_CONTROL](GDD/CHANGE_CONTROL_2026-11-05.md) — межсистемные конфликты.

## Дальнейшее обновление
Обновлять запись **после подтверждённого решения, нового проверенного результата или GitHub merge**. Дата среза должна изменяться при следующем обновлении; нет подтверждения — помечать `Не подтверждено` / `NOT RUN`. Не объединять `main` без review.

## Дополнение INVENTORY-UX (06.11.2026)

- [Утверждённые правила UI инвентаря и контейнеров](GDD/INVENTORY_UX_DECISIONS_2026-11-06.md): DESIGN APPROVED; новые функции НЕ реализованы и НЕ проверены. Документация опубликована через merged PR #36; Unreal-реализация новых функций NOT RUN.
- A17 MVP (#28) и A17.1 (#37) объединены в main; новый дизайн INV-UX01 не реализован в их рамках.
- Старые DOC02 PR #29 и его Inventory v0.4 остаются историческим ранним черновиком, устаревшие рекомендации не замещают более поздние явные решения.
