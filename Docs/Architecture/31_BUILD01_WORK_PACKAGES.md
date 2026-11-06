# BUILD01-FIX01 — спецификация BUILD-WP01–WP07 и план интеграции

**Статус:** документация и планирование; дизайн решений указан в [BUILD01 GDD](../GDD/BUILD01_Building_2026-11-05.md). Пакеты не реализованы, тесты реализации **NOT TESTED**. Это не рабочий backlog и не разрешение на реализацию или перенос задач. [A29–A40](03_IMPLEMENTATION_BACKLOG.md) и [A36 v1](15_A36_SAVEGAME_ARCHITECTURE.md) неизменны; изменения их исходных контрактов допустимы только по отдельному предложению владельцу. Источники: [Inventory A11](21_A11_TRANSFER.md), [A12](22_A12_INVENTORY_TESTS.md), [SLEEP01](../GDD/SLEEP01_Sleep_2026-11-05.md). D06-C WITHDRAWN, C03/C12 RETIRED: все WP работают со статической картой.

## Общие контракты и стадии

- Все наименования UE/Blueprint и DTO ниже — **кандидаты**, а не утверждение о наличии ассетов. Новую реализацию размещать только после проверки существующих компонентов и их переиспользования. Точные пути ассетов определяются отдельным implementation review; изменять сейчас только этот план, GDD и ProjectStatus.
- A29–A35 принадлежат исходному плану: WP01 интегрирует их результаты и проверку A35, а не создаёт параллельный строительный стек. A36 — схема v1, A37 — snapshot, A38 — два поколения/manifest, A39 — restore, A40 — совместимость; WP05 расширяет их отдельной v2-версией, не переписывая v1. A41–A43 принадлежат интеграционному плану и используются WP07.
- Во всех мутациях сохраняются Inventory A05–A12: идентичность ItemId/StackId/InventoryId, ограничения слотов/веса/количества, точные операции, Revision и MutationInProgress. Инвентарь меняется через существующий API; multi-inventory atomic coordinator остаётся открытым, частичные последовательные списания не допускаются. C10-B: приём только для текущей SessionEpoch с CommandId и ожидаемыми revisions; проверять повторно перед commit, повторы и изменённые payload не порождают повторных эффектов. Координатор и rollback не объявлены существующими.
- Общие результаты команд: успешный согласованный commit и новый snapshot либо диагностируемый отказ без частичной мутации; возможные классы отказов — Busy, stale epoch/revision, duplicate/conflict, невалидные ID/данные, ограничения поверхности/слотов/веса, ошибка подготовки/spawn/IO. Точные enum/API — engineering review. Save не сериализует pending, preview, epoch, command cache или UI/Actor references.
- **Порядок:** WP01 → WP02 → WP03 и WP04 (могут идти параллельно после WP02) → WP05-A (интерфейсы/схема и изолированная проверка) → WP06 → WP05-B (окончательный restore и приёмка) → WP07. WP05-A может проектироваться раньше, но полные fixtures требуют результатов WP03/WP04/WP06. WP06 принимает стабильный интерфейс и тестовый адаптер WP05-A, а не ожидает приёмку WP05-B; финальные сквозные проверки проводятся в WP05-B. Так нет цикла между завершениями.
- Формулы прочности/порогов, runtime timing, budget CPU/GPU/RAM и размер дедуп-кеша не утверждены. Для каждой реализации измерять baseline и p95/пиковые время и память на оговорённых устройстве/сцене/сборке; численные лимиты, eviction и fallback проходят отдельный review. Числа C11 50/200/1 МиБ — утверждённые функциональные ограничения, не performance budgets. Не подставлять фиктивный PASS вместо согласованного бюджета.
- Общий PASS реализации: выполнены исходные критерии зависимостей и все применимые сценарии пакета, ручные и автоматические проверки имеют воспроизводимые артефакты, нет потерь/дубликатов и незакрытых блокирующих ошибок. FAIL: нарушение инварианта или теста; **NOT TESTED** при отсутствии прогона/артефакта/утверждённого порога. Неприменимые исторические сценарии — RETIRED, не PASS. Определение документа не является подтверждением выполнения пакета.

## BUILD-WP01 — базовая модульная стройка

1. **Цель.** Дать проверенный минимальный цикл выбора, установки и безопасного демонтажа на статической поверхности.
2. **Объём.** C08-B, C10-B; исполнить точки интеграции D01/D02/D05 и исходных A29–A35: foundation/wall/storage, preview, валидатор, один cost+actor, свободный socket и A34 без refund. HP/tier, шаблоны и разрушение непустого storage — вне WP01.
3. **Зависимости.** Inventory A05–A12, A25, A14/A16, A24, исходные A29–A35; A35 — общий приёмочный gate, а не отдельная дублирующая реализация. WP-зависимостей нет.
4. **Системы и файлы.** Кандидаты `PDA_BuildDefinition`, `BPC_Building`, `BP_BuildPiece`, BuildPlacement, существующий контейнер и HUD/input. Конкретные пути и наличие проверяются перед изменением, новые `.uasset` сейчас не создаются.
5. **Данные.** BuildDefinition/ItemId/cost/footprint/slope/socket/class, transform и стабильный EntityId; статическая карта, collision, вода/NoBuildZone. Базовая стоимость foundation `4 plank + 2 stone` из A29 не изменяется.
6. **Команды.** Preview без cost/коллизии; Confirm заново валидирует контекст и C10, A32 Prepare → exact cost+spawn → Activate либо отказ. Cancel/смерть/смена Pawn очищают preview. Demolition с подтверждением отклоняет dependents и непустой сундук, refund нет.
7. **Ошибки/восстановление.** Неизвестный каталог/class, препятствие, slope/range/water, occupied socket, нехватка cost, stale или spawn failure: без cost/actor/orphan; guard снимается. До WP03 запрещать опасное уничтожение непустого storage. Неподдержанный межинвентарный cost отклонять.
8. **Производительность.** Preview работает только в build mode, без постоянного Tick вне режима; измерить trace/preview и рост actors по общему правилу, budget OPEN.
9. **Проверки.** Авто: exact cost/spawn rollback, duplicate/stale/invalid definitions и socket, Inventory invariants. Ручные PIE: A31 край воды/склон/коллизия, A35 cancel/death/demolition и UI. C10 applicable; результаты NOT TESTED.
10. **PASS/FAIL.** PASS при A29–A35 и перечисленных проверках: один actor и один cost, все запрещённые попытки без побочных эффектов. Любая потеря/дублирование или обход A34 — FAIL; без PIE — NOT TESTED. Save/Load строений проверяется WP05, preview никогда не сохраняется.

## BUILD-WP02 — материалы, HP и опоры

1. **Цель.** Добавить устойчивость модулей, урон, repair и upgrade поверх WP01.
2. **Объём.** C04-B, C09-B, C10-B и применимые C01-B/C08-B; tier/материалы, граф нескольких опор, детерминированный каскад и damage. C05-B передачу loot выполняет WP03; до неё действует защитный запрет для непустых storage.
3. **Зависимости.** WP01, A29/A32–A35, Inventory и каталог; C04 формула несущей способности и C09 значения HP/стоимости требуют tuning/review.
4. **Системы и файлы.** Кандидаты `BP_BuildPiece`, компонент support graph/damage, каталог BuildDefinition и существующие Inventory API; место кода/Blueprint определяет audit реализации.
5. **Данные.** EntityId, MaterialId/tier, CurrentHP/MaxHP, cost, SupportLinks и ground anchors на статической карте; хранить только валидный DAG и совместимые sockets. Persisted MaxHPAtSave и поля v2 — WP05 schema review.
6. **Команды.** Damage/repair/upgrade с C10 guards и актуальными состояниями. Upgrade: `NewHP=(OldHP/OldMaxHP)*NewMaxHP`; repair: `EffectiveHP=min(RequestedHP,MaxHP-CurrentHP)`, cost каждого ингредиента `ceil(FullRepairCost_i*EffectiveHP/MaxHP)`. Один atomic commit cost+HP/tier+поддержка, без изменения EntityId/Storage InventoryId/содержимого.
7. **Ошибки/восстановление.** NaN/Inf, MaxHP≤0, неверный tier/cost, цикл/неизвестная опора, stale, spawn/cascade failure — отказ без частичных изменений; no resurrection и повторного loot. A34 добровольную разборку опоры с dependents и непустого сундука запрещает даже при резервной опоре.
8. **Производительность.** Замер пересчёта support graph и cascades, исключить бесконечный обход/дублирование общей ветви; масштаб fixtures и budget согласовать, не выдумывать.
9. **Проверки.** Авто C09-T01–T18, применимые C04-T01–T16, графы/границы/конкурентный damage и откаты. PIE A35: несколько опор, ремонт, upgrade 50/100→100/200 как пример, демонтаж и отсутствие бесплатного HP. Save round-trip относится WP05. Все NOT TESTED.
10. **PASS/FAIL.** PASS при сохранении доли HP, точной округлённой цене, стабильных IDs и корректном graph/cascade; любое бесплатное восстановление, потеря storage или нарушение A34 — FAIL. Бюджет без согласования — NOT TESTED.

## BUILD-WP03 — разрушение хранилищ

1. **Цель.** Сохранять всё содержимое уничтоженного сундука в единственном наборе world drops.
2. **Объём.** C05-B, C04-B, C08-B, C10-B; интеграция damage/cascade со storage и Inventory. Добровольный A34 остаётся защищённым и не выдаёт refund.
3. **Зависимости.** WP02, A33–A35, Inventory exact operations и pickup; WP05 позже проверяет устойчивое сохранение.
4. **Системы и файлы.** Существующий storage component, build piece, world pickup/loot, кандидат transaction coordinator и каталог; не создавать второй контейнер или дублирующий pickup pipeline.
5. **Данные.** Исходные InventoryId/StackId, ItemId, Quantity, Durability; EntityId события и world-drop records. Представление drops/TTL и точные DTO остаются OPEN; identity policy проверять с A11/A36.
6. **Команды.** Одноразовый damage/cascade event под C10 guard: подготовить валидные drops → атомарно зафиксировать переход storage→world drops и уничтожение либо безопасно отклонить. Повтор события не создаёт второй набор.
7. **Ошибки/восстановление.** Неудача подготовки/позиции/spawn или stale/cancel: сохранить авторитетные данные либо полностью отклонить переход; snapshot не захватывает промежуток. Пока безопасный pipeline не доказан, потенциально разрушительные операции с непустым storage запрещены.
8. **Производительность.** Замер cascade, числа стеков, количества drops и памяти; не добавлять постоянный Tick на каждый stack. Численные бюджеты OPEN.
9. **Проверки.** Авто C05-T01–T16 и применимые C04/C10: двойной damage, несколько storage, неудачный spawn, подсчёт ItemId/Quantity/Durability, stale pickup. Ручной PIE: разрушение/подбор, полная сумка, сохранение/загрузка после WP05. Все NOT TESTED.
10. **PASS/FAIL.** PASS — ровно один набор, суммы и свойства сохранены, в ошибках нет потери/дублирования. Дубликат, потеря или обход A34 — FAIL; persistence до WP05 — NOT TESTED.

## BUILD-WP04 — редактор и шаблоны

1. **Цель.** Планировать модули и безопасно переиспользовать шаблоны при поэлементной платной установке.
2. **Объём.** C02-A, C06-B, C11-B, C08-B, C10-B, D07-C; ghost, local links/materials, профильная библиотека и явный JSON v1 import/export. Массовый Confirm и изменение земли отсутствуют.
3. **Зависимости.** WP01/WP02, A14–A17, A29–A35, каталог и Inventory; может идти параллельно WP03. Save v2 и библиотека независимы, интеграция проверяется WP05/WP07.
4. **Системы и файлы.** Кандидаты build editor component/UI, `SG_BuildTemplates` как отдельное хранилище профиля, serializer и file picker; точный backend/backup требует review. Не дублировать A30/A32.
5. **Данные.** TemplateId/TemplatePartId, локальные transforms/support links, BuildDefinitionId и DesiredMaterialId/tier; 50 templates/профиль, 200 частей/template, файл ≤1 048 576 байт до parse. Whitelist исключает runtime EntityId/InventoryId/StackId, HP, paid cost, loot, bed assignment, WorldClock, epoch и commands.
6. **Команды.** Import/export только выбранного файла: UTF-8 JSON v1, staging и строгая валидация схемы, версий, конечных transforms, каталога, уникальности/циклов/socket и путей; новый TemplateId при import, подтверждение overwrite/duplicate. ConfirmPart: одна деталь, новый world ID и одна точная оплата, C10 revalidation; 32 из 40 успешных остаются при отказе 33-й.
7. **Ошибки/восстановление.** Невалидный/огромный JSON, неизвестные поля, scripts/path traversal, несовместимый каталог, ошибка записи или отмена: библиотека и мир не повреждаются; storage write staging/rollback требуется доказать. При неопределённости отклонять.
8. **Производительность.** Проверить лимиты до parse, ограничение глубины/строк и измерить время/память preview/import на 200 частях и предельном файле; точные bounds требуют engineering review.
9. **Проверки.** Авто C02-T01–T16, C06-T01–T16, C11-T01–T20 и C10; malformed/unknown fields, quota, 32/40, stale и rollback. Ручной PIE/file picker: импорт двух профилей, export/import, отказ, оплата детали, отсутствие копирования loot/HP. Все NOT TESTED.
10. **PASS/FAIL.** PASS при раздельном хранении профиля и мира, whitelist, безопасной записи и поэлементном commit; любая мутация мира через import, бесплатная часть или клонирование данных — FAIL. Требования к реализации и тестам NOT TESTED.

## BUILD-WP05 — SaveVersion 2, миграция и restore

1. **Цель.** Ввести совместимое сохранение построек и зависимого состояния без изменения исходной схемы A36 v1.
2. **Объём.** C01-B, C04-B, C05-B, C07-B, C09-B, C10-B, C08-B; v2 HP/tier/SupportLinks/WorldDrops/Inventory/SLEEP, migration, A37 snapshot, A38 A/B и A39 restore. WP05-A — схема/контракты и изолированный adapter; WP05-B — полная интеграция и приёмка после WP06.
3. **Зависимости.** A36–A40, WP02–WP04; WP05-A предоставляет стабильный интерфейс WP06, WP05-B зависит от WP06 и данных WP03/WP04. Не считать A36 v1 реализацией v2.
4. **Системы и файлы.** Кандидаты v2 `SG_SurvivalSave`/DTO, SaveCoordinator и A38/A39 adapters; исходный [A36](15_A36_SAVEGAME_ARCHITECTURE.md) остаётся исторической схемой, изменения версии описываются отдельным schema review. `SG_BuildTemplates` — отдельная библиотека профиля WP04.
5. **Данные.** MapId/static map version, стабильные world/Inventory/stack IDs, HP/tier, SupportLinks, world drops, WorldClock/SleepState и данные A36; без изменённых terrain DTO, transient preview, UI, SessionEpoch и command cache. Durability и durable revisions нуждаются в schema review.
6. **Команды.** Save capture только вне мутации: world+Inventory+sleep единым логическим snapshot; A/B write/validate/manifest. Load: инвалидировать epoch при старте → validate/migrate → static map → inactive entities/storage/links → sleep/player → validate → новая epoch → Activate. Обычный Save epoch не меняет.
7. **Ошибки/восстановление.** Unknown schema/catalog/MapId, broken links, неутверждённый baseline v1, failed write или load: не активировать частичный мир и не перезаписывать старый валидный save; A38 fallback, новая epoch и при fallback. Нет неутверждённого durable replay и заявления об атомарности файловой системы.
8. **Производительность.** Измерить snapshot/write/read/migrate/restore, размер обоих слотов и память для больших графов/drops; budgets и версии контента требуют отдельного review.
9. **Проверки.** Авто золотые v1→v2 fixtures, исходный v1 неизменён, C01-T01–T15 кроме RETIRED, C10-T01–T20 применимые, A38 failure/fallback и A40 duplicate load/IDs; WP05-A — изолированные fixtures, WP05-B — реальные sleep/drop/template интеграции. Ручной PIE и packaged restart после WP06. Все NOT TESTED.
10. **PASS/FAIL.** WP05-A PASS только как интерфейсный gate после schema review и изолированных тестов; это не PASS WP05. WP05-B PASS только после WP06 и полного A40 round-trip/failure matrix; потери, dup, повторное лечение, stale command или перезапись v1 — FAIL. Без утверждённых v1 HP/tier и sleep defaults миграция соответствующих данных BLOCKED.

## BUILD-WP06 — SLEEP01 / bed / bedroll / respawn

1. **Цель.** Согласовать строительство, разрушение и восстановление с утверждённым сном и точкой возрождения.
2. **Объём.** C07-B, C01-B, C10-B, C08-B; bed/bedroll на статической поверхности, назначение, реальные прерывания, фактическое время и fallback. SLEEP01 не меняется, земля не редактируется.
3. **Зависимости.** WP02, стабильный контракт WP05-A, SLEEP01, A20/A21/A23, BP01/Inventory. WP06 проверяет реализацию через интерфейс/fixture WP05-A и не зависит от финального WP05-B.
4. **Системы и файлы.** Существующие/будущие sleep/needs/WorldClock/respawn, bed/bedroll actor, Inventory, support graph и Save adapter; конкретные ассеты и наличие A23 требуется проверить до реализации.
5. **Данные.** AssignedBedEntityId или none, bed/bedroll IDs и состояние, fatigue, eligibility, фактический sleep interval, WorldClock и потребности. World save v2 — через WP05; шаблоны не копируют назначение/состояние сна.
6. **Команды.** StartSleep/Wake/interrupt, назначение кровати, размещение/сворачивание спальника и respawn проходят guards/epoch и актуальную валидацию; damage применяет sleep effects ровно раз по фактическому времени. Спальник world→Inventory — точный перенос без dup; автосохранение после каждого сна не добавляется.
7. **Ошибки/восстановление.** Полный Inventory оставляет спальник в мире; временно выгруженную зону сначала загрузить и проверить, отсутствие actor не равно разрушению. При реально недоступной кровати/позиции — исходный PlayerStart, без переназначения; stale/повторный callback не повторяет эффект.
8. **Производительность.** Замерить проверку collision/respawn и восстановление при выгрузке, не сканировать мир каждый Tick; радиус 3 м — tuning, не новый утверждённый бюджет.
9. **Проверки.** Авто применимые C07-T07–T17 кроме RETIRED, C10-T13 и SLEEP fixtures: 20 минут вместо запрошенных 8 часов, double interrupt, missing/unloaded bed, полный Inventory, migration. Ручной PIE: сон, урон опоры, bedroll, fallback; финальный save/restart — WP05-B. Все NOT TESTED.
10. **PASS/FAIL.** PASS WP06 при корректной интеграции через интерфейс WP05-A и всех его собственных тестах; окончательное постоянство подтверждается WP05-B. Двойное восстановление, неверное время, dup спальника или ложный fallback — FAIL.

## BUILD-WP07 — сквозная приёмка

1. **Цель.** Проверить полный вертикальный срез в PIE и Windows packaged build с воспроизводимыми доказательствами.
2. **Объём.** C01/C02/C04–C11 в применимой части, C08-B и A35/A40/A41–A43; pickup → craft → build → storage → damage/repair → drops → save/load → sleep. C03/C12 и D06-C не исполняются.
3. **Зависимости.** WP01–WP04, WP06, окончательная приёмка WP05-B и исходные A35/A40/A41–A43. Нет обратной зависимости от WP07 к их реализации.
4. **Системы и файлы.** Существующая интеграционная карта, input/HUD, Inventory/crafting, build/storage, save и sleep; тестовые fixtures/логи/Windows package в отдельной реализации. Конкретные тестовые ассеты заранее не утверждены.
5. **Данные.** Версионированные fixtures v1/v2, каталоги, стабильные GUID и baseline counts, target platform/build/config, timing/memory; независимая библиотека шаблонов профиля, без terrain данных.
6. **Команды.** Выполнять реальные операции через публичные API/UI, проверять C10 epoch/revision/CommandId, A37 границы snapshot и A38 fallback; повторный load и перезапуск не повторяют эффекты.
7. **Ошибки/восстановление.** Инъекции отказа spawn/IO, stale/duplicate, invalid data и повреждённого слота должны оставлять согласованное предыдущее состояние и диагностируемую ошибку; сборка/отсутствие артефактов не маскируются.
8. **Производительность.** Зафиксировать target hardware, сценарии, p95/peak frame time, память, длительности snapshot/load/import и согласованные бюджеты; до утверждения порогов perf acceptance NOT TESTED.
9. **Проверки.** Автоматические контрактные/regression suites A35/A40, все применимые C01/C02/C04–C07/C09–C11; ручные PIE вода/склон/no-build/cascade/sleep/32 из 40 и чистый Windows Development cook/package/restart. Доказательства включают SHA, команды, логи, платформу, fixtures и PASS/FAIL. Все NOT TESTED.
10. **PASS/FAIL.** PASS только при выполнении всех исходных и новых критериев, реальных PIE и packaged артефактах и согласованных perf budgets. Нарушение инварианта или неуспешный build — FAIL; пропущенный тест/порог — NOT TESTED, не PASS.

## Матрица и контрольные точки

| Gate | Проверка при реализации | Доказательство | Статус сейчас |
|---|---|---|---|
| WP01 | A29–A35, exact cost, no-build, double Confirm и A34 | автоматические assertions + PIE | NOT TESTED |
| WP02 | C09-T01–T18, применимые C04 и A35 | graph/HP fixtures + PIE | NOT TESTED |
| WP03 | C05-T01–T16, отказ/cascade/no dup | Inventory/world counts + PIE | NOT TESTED |
| WP04 | C02/C06-T01–T16, C11-T01–T20 | JSON/security и 32/40 + PIE | NOT TESTED |
| WP05-A | schema review, v1 fixtures, интерфейс SLEEP | утверждённая схема + fixtures | NOT TESTED |
| WP06 | применимые C07, C10-T13, SLEEP01 | sleep/respawn fixtures + PIE | NOT TESTED |
| WP05-B | применимые C01/C10, A38–A40, интеграция WP03/WP06 | golden round-trip + fallback/restart | NOT TESTED |
| WP07 | A35/A40/A41–A43, применимые C01/C02/C04–C07/C09–C11 | PIE, Windows build и performance | NOT TESTED |

Точные исключения из исторических тестов: C03-T01–T12, C04-T06–T08/T10–T12, C07-T01–T06/T11/T18 и C01-T03 — **RETIRED / NOT APPLICABLE**, не PASS. В смешанных C02-T07/T13, C04-T14–T16, C05-T13 и C07-T15 проверяется только сохраняющаяся не-terrain часть; исходная редакция доступна в истории PR. Все остальные перечисленные сценарии требуют проверки применимости к реализации и доказательств.

## Отдельный план будущего переноса в рабочий backlog

Перенос сейчас запрещён. После **отдельного прямого разрешения владельца**: (1) сверить актуальную версию A29–A40, владельцев и зависимости, не переписывая их; готовность — согласованная карта интеграции и отсутствие дублирования; (2) добавить отдельные ссылки/задачи WP01–WP02 после подтверждения исходных зависимостей и критериев A29–A35; gate — документы контрактов и тестов; (3) добавить WP03/WP04 после WP02 с интеграцией A33/A34 и A30/A32, не создавая второй storage/build pipeline; (4) добавить WP05-A с A36–A40 и согласовать schema review/baselines, затем WP06 на интерфейсе WP05-A; (5) назначить WP05-B после WP06, затем WP07 после всех пакетов и A35/A40/A41–A43. На каждом этапе проверять исходные идентификаторы, владельцев, тестовые артефакты и зависимости. Если для реализации требуется изменение старого контракта — остановить соответствующую интеграцию и оформить отдельное предложение владельцу; автоматически менять A29–A40 запрещено.

## Точки интеграции с исходными задачами

| Исходная задача | Интеграция WP без изменения исходного контракта |
|---|---|
| A29 | WP01 использует исходный каталог/стоимость; WP02 добавляет материал/HP как отдельное расширение и не меняет baseline. |
| A30 | WP01 использует существующий preview/lifecycle; WP04 расширяет ghost и ConfirmPart без второй системы ввода. |
| A31 | WP01/WP04 повторно вызывают валидатор статической карты, slope/range/footprint/collision и воды. |
| A32 | WP01 использует единый cost+spawn; WP04 вызывает тот же контракт для каждой детали. |
| A33 | WP01 использует исходные sockets/storage; WP02–WP03 добавляют graph/drop через те же identities. |
| A34 | WP01–WP03 сохраняют подтверждение, запрет зависимых опор/непустого storage и no refund. |
| A35 | WP01–WP04 сохраняют исходные сценарии; новые матрицы WP дополняют их. |
| A36 | WP05 оставляет v1 неизменной; v2, миграция и baseline требуют отдельного schema review. |
| A37 | WP05 использует согласованный snapshot и guard, WP06 подключает завершённые эффекты сна. |
| A38 | WP05 сохраняет A/B slots, manifest и fallback, тестирует failure без обещания атомарности файловой системы. |
| A39 | WP05 восстанавливает статическую карту, GUID и links до активации; WP06 подключает bed/sleep; C10 обновляет эпоху. |
| A40 | WP05-B/WP07 дополняют исходные fixtures v1→v2, sleep, drop и повторным load; исходные критерии A40 не ослабляются. |

## Отчёт документальной проверки BUILD01-FIX01

Проверенная база `main` — `2bdc2791f04638bdc3c9101dc85618c0e4f8528c`, исходный head PR — `92b582997c70aa2cbd7759380a45442ebb8b93d9`. Изменения ограничены GDD BUILD01, этим отчётом и `Docs/ProjectStatus.md`. Исходный backlog A29–A40 и архитектура A36 v1 побайтно совпадают с базой. Текст архива D06-C/C03 сохранён; удалена только лишняя пустая строка в конце GDD; смешанные исторические сценарии доступны в [исходном GDD на head PR](https://github.com/zonor922-hub/SurvivalProject/blob/92b582997c70aa2cbd7759380a45442ebb8b93d9/Docs/GDD/BUILD01_Building_2026-11-05.md).

| Проверка | Результат |
|---|---|
| Git fetch основной и PR-ветки; чистый изолированный worktree | PASS |
| Локальные команды Repository CI: metadata/evidence и 14 fixtures | PASS; Unreal не запускался |
| Локальные Markdown-ссылки изменённых документов, WP01–WP07 по 10 разделов, ID сценариев C01–C07/C09–C11 и колонки C10/C11 | PASS для проверенной структуры; внешние ссылки не проверялись |
| Активный GDD, статическая поверхность и исторический архив без изменений содержания | PASS документального сопоставления; не тест runtime |
| Состав файлов и `git diff --check` относительно main | PASS для трёх документальных файлов; итоговый опубликованный SHA проверяется в PR |
| Исходящая история | Все 18 коммитов меняют только BUILD01 GDD. Исторический commit `0e02ca62` содержит лишнюю пустую строку в конце файла в его собственном diff; это предупреждение истории, не игровая проверка и не основание переписывать историю. Итоговый diff проверяется отдельно. |
| Gameplay/Blueprint compile/PIE/migration/Windows package/performance | NOT TESTED; реализация не выполнялась |
| GitHub Repository CI нового head | NOT TESTED до публикации и завершения workflow |

Открытые препятствия реализации: отдельные schema review и утверждённые baseline миграции HP/tier и SleepState; атомарный координатор Inventory/world/cascade и безопасная ограниченная дедупликация; tuning HP/стоимостей/support и performance budgets; проверка фактических компонентов A23/SLEEP; подтверждение всех запланированных тестов. Это не разрешение на реализацию, перенос backlog или merge.
