# SurvivalProject — текущий прогресс

> **BUILD01-FIX01 — документация / проверка в Draft PR #35:** исправлен активный BUILD01 GDD с сохранением архива отменённых D06-C/C03; подготовлены [спецификации BUILD-WP01–WP07 и план переноса](Architecture/31_BUILD01_WORK_PACKAGES.md). Зависимости: Inventory A05–A12, A29–A40, A36 v1 и SLEEP01; WP05 разделён на интерфейсный gate и итоговую приёмку после WP06. Игровая реализация, PIE, migration и Windows build **NOT TESTED**; исходный backlog не изменён, перенос только после отдельного прямого разрешения. Изменённые файлы: GDD BUILD01, указанный отчёт Architecture и ProjectStatus. Документальные проверки и Repository CI фиксируются в отчёте PR; это не merge и не подтверждение готовности к реализации.


> **DOC-SLEEP01 — DESIGN COMPLETE / APPROVED; IMPLEMENTATION NOT STARTED:** [дизайн сна](GDD/SLEEP01_Sleep_2026-11-05.md) фиксирует утверждённые правила усталости, восстановления, опасностей, спальника, возрождения, UI, времени и сохранений. Баланс **TUNING / NOT FINAL**. Зависимости: A20/A21/A23/A24, Inventory, TIME01, DEATH01, A36–A40. Игровые проверки NOT RUN. [Отчёт](Architecture/30_DOC_SLEEP01.md).

> **Дизайн-дополнение 05.11.2026 (NOT IMPLEMENTED):** утверждён [BP-D04 Core→EquippedBag](GDD/BP01_Backpacks_Decisions_2026-11-05.md) и дорожная карта S1→S2/P1. Будущая [DEATH01](GDD/DEATH01_LostGear_Decisions_2026-11-05.md) предполагает потерю всего носимого и возврат до исчезновения; это противоречит исторической политике A23 «сохранить inventory», а не её фактическому статусу реализации. Часы/TTL открыты. [Изменения и зависимости](GDD/CHANGE_CONTROL_2026-11-05.md). Данная редакция документа не содержит изменений runtime, Blueprint и новых тестов.

## A17 — независимый аудит 03.11.2026

**A17 MVP — ручная PIE-приёмка завершена 10/10 PASS; Draft PR №28 открыт на проверку.** Владелец формально уточнил 03.11.2026, что минимальный экран — объём A17, а UI Split/Merge и stale Revision относятся к отдельной A17.1. Изменение объёма оформлено в backlog; требования AGENTS.md к проверкам и публикации сохранены. База после fetch `4784cb9d21f62243cf446cceafa04d73f0b77572`, зависимости A10/A12/A14/A16 присутствуют в main. Исходная `task/a17-inventory-ui` без исходящих коммитов; чистая копия подготовлена в `codex/a17-inventory-audit` (`.a17-audit-worktree`), резервная ссылка сохранена. Открыт Draft [PR №28](https://github.com/zonor922-hub/SurvivalProject/pull/28) из `codex/a17-inventory-audit`; исходный проверенный commit `6f574b66f44d0f20a9f14957bc9c4f983d2128af`. PR остаётся Draft и не объединён.

Codex: UE 5.8.4, compile **5/5 BS_UP_TO_DATE**, exit 0; экспорт графов и наличие project package dependencies PASS; четыре кандидата ассетов побитово сохранены; LFS-атрибуты и fsck объектов базы PASS. Новые LFS upload/pre-push не проверялись. В последнем пользовательском логе и новом логе компиляции — 0 совпадений Blueprint Runtime Error/Accessed None. Пользовательские физические PIE A17 PASS и A16 5/5 PASS записаны отдельно; Codex их не повторял.

**Ручная PIE:** пользователь сообщил A17 MVP 5/5 и A16 5/5 PASS, Output Log без Blueprint Runtime Error/Accessed None/Infinite Loop; сохранений/auto-fix не было. Codex повторно посчитал 4 целевых ассета + тестовую карту + 24 dependencies: 29/29 сравнений, 26 уникальных файлов, SHA совпали с preflight. Результаты пользователя отдельно от compile 5/5 Codex. Preflight, чеклист и Git state: `Architecture/evidence/a17/pie_preflight.json`. Live refresh во время внешней операции и перепривязка при смене Pawn/PlayerState не проверены; последнее остаётся зависимостью A19. A17.1 Split/Merge + stale Revision — отдельная задача. Для A17 MVP backlog не требует package; package не выполнялся. Чужие GDD/Build/A15, изменённая карта и Config с восстановленной строкой AFS SecurityToken исключены. Игровая логика не менялась. Полный состав, доказательства, ограничения, решение по объёму и следующие проверки: [отчёт A17](Architecture/29_A17_INVENTORY_UI_AUDIT.md).

## DOC01 — актуальная сводка (03.11.2026, Europe/Moscow)

Проверенный HEAD `origin/main`: `04c09ce6aec359b2afaecc2ac6eddf37c495009e` (fetch и GitHub API). DOC01 меняет только этот файл, индекс архитектуры и новый [отчёт A16](Architecture/28_A16_INTERACTION_HUD.md); зависимости — объединённые A15/A16/SEC01/SEC02 и read-only проверка SEC03. Исторические FAIL/NOT RUN сохранены. Игра не объявляется готовой к выпуску.

- **A15 — реализована и объединена** через [PR №22](https://github.com/zonor922-hub/SurvivalProject/pull/22), merge `15b3f6d8087d850f5f156254dd757bd616b469df`. [Отчёт](Architecture/25_A15_WORLD_PICKUP.md): целевой lifecycle 10/0 закрыл прежний BLOCKER; полная регрессия и свежая упаковка не повторялись.
- **A16 — реализована и объединена**, [PR №23](https://github.com/zonor922-hub/SurvivalProject/pull/23), merge `aa8f7dbd25bf707a30722feee809794d61fcfbf8`. Минимальный HUD взаимодействия; ручные проверки PR и пользовательские 6/6 PASS описаны отдельно в [отчёте A16](Architecture/28_A16_INTERACTION_HUD.md). Независимая инспекция графов и полный lifecycle подписок не доказаны.
- **A17 — в работе локально**; реализация в main не подтверждена. Локальные незакоммиченные файлы не включены в DOC01.
- **A36 SaveGame — технический проект**, реализация не подтверждена; наличие ТЗ не означает готовую систему сохранения.
- **SEC03 — активирована защита main и обязательный CI**. GitHub API подтвердил [Ruleset 26429234](https://github.com/zonor922-hub/SurvivalProject/rules/26429234): active, default branch main, обязательный PR, запрет удаления/force push, strict status check `Repository checks (no Unreal Engine)` (integration 15368), bypass отсутствует. Отдельного документа SEC03 в main нет; настройки в DOC01 не изменялись.

## SEC02 — repository CI без Unreal Engine (02.11.2026)

**Реализована и объединена в main через [PR №25](https://github.com/zonor922-hub/SurvivalProject/pull/25)**, merge `04c09ce6aec359b2afaecc2ac6eddf37c495009e`. Зависимость SEC01 объединена через PR №24. Локальные исторические проверки: 7 групп PASS, 14/14 самотестов PASS. Первый [Actions run](https://github.com/zonor922-hub/SurvivalProject/actions/runs/41439797798) на `ceb490f20a5b73d1e6822a18d2cc94f711c44281` — success; [run на main](https://github.com/zonor922-hub/SurvivalProject/actions/runs/41441466761) на merge SHA — completed / success, проверено через GitHub API 03.11.2026. CI проверяет metadata и целостность выбранных исторических evidence, а не исполнение Blueprint. Unreal runtime / PIE / package в SEC02 — NOT RUN. [Отчёт SEC02](Architecture/27_SEC02_CI.md) сохраняет контекст подготовки до merge.

## SEC01 — безопасность AFS (02.11.2026)

Ветка `security/sec01-disable-afs` от `main` / `aa8f7dbd25bf707a30722feee809794d61fcfbf8`: отключены неиспользуемый Android File Server и сетевое соединение, строка опубликованного SecurityToken удалена. Shipping-настройки сохранены. Статические проверки INI, области изменений, отсутствия прежнего значения в текущем рабочем дереве и `git diff --check` — PASS. Unreal Editor / PIE / package — NOT RUN. Исторический токен остаётся в Git history; при использовании где-либо ещё его необходимо заменить. **Реализована и объединена через [PR №24](https://github.com/zonor922-hub/SurvivalProject/pull/24)**, merge `75f40934a7c68034777106dd0f706d5f33292e04`. [Отчёт SEC01](Architecture/26_SEC01_AFS_SECURITY.md). Остальные статусы ниже этой записью не пересматриваются.

Историческая сводка A11–A14 от 29 октября 2026 (результаты не пересчитывались). **A14 завершена и объединена в `main`** через [PR №20](https://github.com/zonor922-hub/SurvivalProject/pull/20), merge `a8e8fcaea27ed39852c25d5ac912aa5b62a1434f`: [отчёт](Architecture/24_A14_ENHANCED_INPUT.md), 8 Blueprint compile PASS, два PIE 274 PASS / 0 FAIL, Jump 4 PASS / 0 FAIL, A12 548 PASS / 0 FAIL до исправления Jump. После merge автоматический UE-прогон не повторялся; последующая ручная проверка пользователя в PIE подтвердила физические Tab и E (остановка в отладчике), блокировку движения/обзора/прыжка в UI и восстановление управления. **A13 завершена и объединена в `main`**: [PR №19](https://github.com/zonor922-hub/SurvivalProject/pull/19), merge `a09826aab6cff4ebfe7f2bdbcd54d85e9af3aff0`; три PIE-запуска, 171 PASS / 0 FAIL до merge; после объединения UE повторно не запускался. **A12 завершена и объединена в `main`** через [PR №18](https://github.com/zonor922-hub/SurvivalProject/pull/18), merge `fa74e69536d0ff4339fa41bfa3badd9a6d0bb93c`. Проверки A12 и регрессии выполнены до merge; UE после объединения не запускался. **A11 завершена и объединена в `main`** через [PR №16](https://github.com/zonor922-hub/SurvivalProject/pull/16), merge `6d4e854cbacc08e7f6d661eff00714c94cf974a4`. 15 093 PASS/0 FAIL относятся к проверенному до merge коду; UE после объединения не запускался.

Репозиторий https://github.com/zonor922-hub/SurvivalProject первоначально был приватным; по состоянию на 03.11.2026 GitHub API подтверждает, что сейчас он публичный. A08 (PR №6), A09 (PR №7) и исправления F01/F02 (PR №8) объединены в main; база проектирования A36 — `031f4f7a284611bcdf032ad073c12e8d16e25bd7`. Проверки F01/F02 описаны в их отчёте и при подготовке A36 повторно не запускались. Движок реального запуска: Unreal Engine `5.8.4-58902052+++UE5+Release-5.8`. A10 (PR №12) объединена в main merge-коммитом `513b33870990a9db31e32dc98326ec584e9b69fa`; A11 (PR №16) объединена обычным merge `6d4e854cbacc08e7f6d661eff00714c94cf974a4`; последующие PR не объединяются автоматически.

| Задача | Статус | Подтверждение |
|---|---|---|
| A01 — аудит в редакторе | Выполнена | [Отчёт](Architecture/05_A01_EDITOR_AUDIT.md): классы, графы, компиляция и PIE |
| A02 — резервная копия и Git/LFS | Выполнена | [Отчёт](Architecture/06_A02_BACKUP_AND_VERSIONING.md), baseline `04b7b95`; восстановление 779 файлов проверено в A02 |
| A03 — gameplay bootstrap | Выполнена | [Отчёт](Architecture/07_A03_GAMEPLAY_BOOTSTRAP.md), commit `60a577d` |
| A04 — тестовая карта и журнал | Выполнена | [Отчёт](Architecture/08_A04_SYSTEMS_TEST_MAP.md), commit `cb3c322`; три PIE-прогона и baseline CPU/GPU |
| A05 — базовые типы предметов и операций | Завершена, PR №2 слит в main | [Отчёт](Architecture/09_A05_ITEM_TYPES.md); [повторные 13 тестов на базе A06](Architecture/evidence/a06_a05_regression.json) |
| A06 — каталог предметов | Завершена, PR №3 слит в main | [Отчёт](Architecture/10_A06_GAME_CATALOG.md), [24 теста](Architecture/evidence/a06_verification.json), [три PIE-запуска](Architecture/evidence/a06_pie.json) |
| A07 — доставка каталога в сборку | Завершена, PR №4 слит в main | [Отчёт](Architecture/11_A07_WINDOWS_BUILD.md), [повторная упаковка](Architecture/evidence/a07_verification.json), [отдельный запуск](Architecture/evidence/a07_standalone_proof.txt) |
| A24 — изолированное плавание собственного персонажа | Завершена, PR №5 слит в main | [Отчёт](Architecture/13_A24_SWIMMING.md), [новая проверка](Architecture/evidence/a24_verification.json), [три берега](Architecture/evidence/a24_shore_verification.json) |
| A08 — состояние и чтение инвентаря | Завершена, PR №6 объединён | [Отчёт](Architecture/12_A08_INVENTORY_STATE.md); контракты и private-защита повторены в F01/F02 |
| A09 — точные операции инвентаря | Реализация в main (PR №7); воспроизводимость восстановлена F01 | [Итоговый отчёт A09/F01/F02](Architecture/14_A09_F01_F02_VALIDATION.md); 69 контрактов A09, 13 access-проверок, 600 модельных операций, три PIE-запуска |
| F01/F02 — исправления аудита | Проверены, PR №8 объединён | [Runner, результаты и ограничения](Architecture/14_A09_F01_F02_VALIDATION.md): 211 проверок; nonfinite definitions и WeightLimit отклоняются |
| A10 — разделение и объединение стопок | **Завершена, PR №12 объединён в main** (`513b33870990a9db31e32dc98326ec584e9b69fa`); остаточный риск явно принят | [Отчёт](Architecture/16_A10_SPLIT_MERGE.md): A10-F1, 486 PASS / 0 FAIL на чистом проверенном коммите; 190 дробных split/merge, 17 путей отказа; 12 Blueprint, PIE A09/A10 и A24; 8 SHA-256. Эксперимент чувствительности Mutation Guard — **NOT RUN**, в PASS не входит; [решение о риске в PR](https://github.com/zonor922-hub/SurvivalProject/pull/12#issuecomment-6449528324) |
| A36 — схема SaveGame, DTO и версии | Технический проект принят как документация через PR №10; реализация не начата | [Проект и ТЗ](Architecture/15_A36_SAVEGAME_ARCHITECTURE.md): схема v1, ID, tombstones, двухслотовая запись без заявления о файловой атомарности, 42 сценария тестов; Unreal не запускался |
| A11 — перенос между инвентарями | **Завершена, PR №16 объединён в main** (`6d4e854cbacc08e7f6d661eff00714c94cf974a4`) | [Отчёт и матрица](Architecture/21_A11_TRANSFER.md): 15 093 PASS / 0 FAIL на чистом `c858e93`, 12 Blueprint, PIE A09/A10/A11 по 3/3, A24 PASS; [аудит: Ready with Conditions](https://github.com/zonor922-hub/SurvivalProject/pull/16#issuecomment-6488845100). Ограничения: A36/T15 (глобальные GUID), A39 (38a–d NOT RUN), риск бинарных Blueprint, F04 (свежая упаковка) |
| A12 — инварианты inventory | **Завершена, PR №18 объединён в main** (`fa74e69536d0ff4339fa41bfa3badd9a6d0bb93c`) | [Отчёт](Architecture/22_A12_INVENTORY_TESTS.md): 545/0 пользовательских PIE assertions; 1644/0 автоматических, финальная регрессия 15093/0; предупреждения ChangedSlots — Minor |
| A13 — Interaction Focus | **Завершена, PR №19 объединён в main** (`a09826aab6cff4ebfe7f2bdbcd54d85e9af3aff0`) | [Отчёт](Architecture/23_A13_INTERACTION_FOCUS.md): 3 Blueprint BS_UP_TO_DATE, PIE 3/3, 171 PASS / 0 FAIL до merge; временная тестовая оснастка, Visibility вместо Interaction channel; package/multiplayer NOT RUN |
| A14 — Enhanced Input | **Завершена, PR №20 объединён в main** (`a8e8fcaea27ed39852c25d5ac912aa5b62a1434f`) | [Отчёт](Architecture/24_A14_ENHANCED_INPUT.md): 8 Blueprint compile PASS, PIE 274/0, Jump 4/0, регрессия A12 548/0 (до Jump fix); физические E/Tab и UI-политика подтверждены пользователем после merge (E через breakpoint). Полная A13/A24, package, multiplayer — NOT RUN |
| A15 — World Pickup | Реализована, PR №22 объединён | [Отчёт и исторические проверки](Architecture/25_A15_WORLD_PICKUP.md); ограничения сохранены |
| A16 — Interaction HUD | Реализована, PR №23 объединён; ограничения проверки открыты | [Отчёт](Architecture/28_A16_INTERACTION_HUD.md); ручные результаты не равны независимому автоматическому аудиту |
| A17 — экран inventory | В работе локально; реализация в main не подтверждена | Вне DOC01 |
| A18–A23, A25–A35, A37–A44 | Реализация в main не подтверждена | [План и критерии](Architecture/03_IMPLEMENTATION_BACKLOG.md) |

В main объединены реализации A01–A16 и A24 (17 пунктов из 44); объём проверок и ограничения различаются, см. отчёты. Полная независимая проверка A16 не завершена. F01/F02 — исправления существующих задач, не новые пункты из 44. Это не процент готовности игры. Свежий package A09 не проверен; историческая A07 проверяла каталог отдельно.

## Рабочая концепция игры (GDD)

[Game Design Document v0.1.1 — «Земли Отголосков»](GAME_DESIGN_DOCUMENT.md) описывает выбранное направление: собственный стилизованный фэнтезийный survival с исследованием, крафтом, модульным строительством и поздней прогрессией через Узлы Эха. После аудита PR №11 уточнены игровой профиль жажды (`ThirstDrainRate = 0` до появления питья), respawn, состав среза, карта и терминология без изменения технических контрактов. **Это дизайн-документ, не реализация и не новая задача A01–A44.** Первый вертикальный срез, зависимости и технические контракты остаются без изменений. Поздние системы (враги, биомы, Узлы Эха, сюжетный прогресс) требуют отдельных спецификаций, задач и версионирования сохранения; утверждённая схема A36 v1 автоматически не расширяется.

## Подключение и сохранение

- GitHub-репозиторий первоначально создан как приватный и позднее открыт; по состоянию на 03.11.2026 он публичный. Origin настроен на него. Игровая версия A04 опубликована; чтение файлов через GitHub-подключение подтверждено. Подключению предоставлены права pull/push.
- В репозитории действуют .gitignore и .gitattributes для Git LFS. Историческая проверка восстановления A02 была локальной; полная загрузка LFS из GitHub при публикации документации заново не проверялась.
- Доступ именно из обычного чата ChatGPT требует проверки в том чате: прочитать SurvivalProject.uproject через подключённый GitHub. Наличие подключения здесь не подтверждает доступность во всех режимах ChatGPT.
- Документация хранится в Docs; этот файл — единственный основной файл текущего прогресса. A05–A16/A24 и исправления F01/F02 (PR №8) опубликованы в main. Старые a05_types_created.json и a09_build.json — исторические записи, не доказательство новых проверок. Текущий runner пишет новые результаты в Saved/Verification/F01F02 и не перезаписывает исторические отчёты.

## Следующий шаг и ограничения

**Следующая локальная работа — A17**, зависимости A10/A12/A14/A16 объединены. В DOC01 A17 не проверяется и не публикуется. A15 World Pickup и A16 минимальный HUD уже в main. Сохраняются ограничения исторических регрессий, жизненного цикла HUD и свежей упаковки. Для A14 полная A13, A24, package, multiplayer и визуальная QA были NOT RUN; CI-статусы A14 не опубликованы. 17 предсуществующих startup-диагностик UE зафиксированы без установления причинности. Эти ограничения не пересматриваются DOC01; новый запуск Unreal в DOC01 не выполнялся.

A10 объединена через PR №12 (merge `513b33870990a9db31e32dc98326ec584e9b69fa`). M1–M3 закрыты; опубликованный прогон A10-F1 на чистом коммите — 486 PASS, 0 FAIL, без повторного запуска Unreal после merge. Пользователь явно принял низкий остаточный риск: эксперимент чувствительности Mutation Guard на реальной изолированной Blueprint-копии — NOT RUN; четыре недостижимые ветки подтверждены только статически, синтетическая проверка анализатора выполнена в независимом аудите. Замечания Low L1–L8 не исправлены и остаются отдельной работой. A11 реализована и объединена через [PR №16](https://github.com/zonor922-hub/SurvivalProject/pull/16) (merge `6d4e854cbacc08e7f6d661eff00714c94cf974a4`), без повторного UE-прогона после merge. Приняты условия независимого аудита: бинарные `.uasset` проверены косвенно через Editor API и runtime assertions, а не прямой source-level инспекцией. Два согласованных исключения — общий private CheckReceiveExact и сохранение исходной неактивной Durability стека приёмника. A36 остаётся отдельной реализацией по утверждённому ТЗ (включая глобальные GUID/T15), A39 отвечает за загрузку и инвалидирование команд (38a–d NOT RUN). F03, F04 (свежая упаковка) и F05 остаются отдельной работой. Локальную main и резервные ветки не переписывать.

Собственный GameInstance подключён; глобальный GameMode остаётся ThirdPerson. В LV_SystemsTest назначен BP_SurvivalGameMode. Производственная карта не переключена на собственный игровой набор: это A41. A09 добавляет команды изменения inventory на PlayerState; минимальный HUD A16 реализован; экран inventory A17 не подтверждён в main, крафт, строительство и сохранение остаются отдельными задачами. Windows Development-сборка A07 проверила каталог; новый cook/package F01/F02 не выполнялся. В F01/F02 повторены PIE инвентаря, управление/ходьба/прыжок и физическое плавание с тремя берегами без сохранения карт. Ручной Listener сохранён; автоматические проверки не считают его PrintString результатом приёмки.

При переносе исторических документов сохранены прежние формулировки статуса; они не отменяют эту сводку. В A24 повторены компиляция десяти Blueprint, семь проверок управления/ходьбы/прыжка, физический подъём/спуск и шесть береговых проходов; код завершения процесса 0. Ресурсы не пересохранялись, все четыре файла реализации совпадают с исходным c97f449. Проверки выполнены headless; художественная оценка анимации не проводилась. Анимация плавания — MVP-заглушка, кислород/утопление не добавлены.

## T0 — проверка Private-доступа (28 октября 2026)

**T0: PASS. A11 implementation: ALLOWED.**

Ручная проверка выполнена в Unreal Engine 5.8.4 (`5.8.4-58902052+++UE5+Release-5.8`) в изолированном проекте `D:\Project\SurvivalProject_T0`.

Использованы два временных Blueprint: `BPC_Inventory_T0_TEMP` и `BP_T0_External_TEMP`.

### Результаты компиляции

| Тест | Проверка | Результат |
|---|---|---|
| T0-a | Чтение Private Slots другого экземпляра того же класса | PASS |
| T0-b | Запись Private Slots другого экземпляра того же класса | PASS |
| T0-c | Вызов Private FindStackIndex другого экземпляра с использованием результата | PASS |
| T0-d1 | Запрет внешнего чтения Private Slots | PASS — ожидаемая ошибка |
| T0-d2 | Запрет внешней записи Private Slots | PASS — ожидаемая ошибка |
| T0-d3 | Запрет внешнего вызова Private FindStackIndex | PASS — ожидаемая ошибка |
| T0-e | Контроль SHA-256, Git и очистки временных ассетов | PASS |

### Проверка целостности

После закрытия Unreal Engine без сохранения временных Blueprint выполнена проверка через PowerShell:

- MAIN HASH: PASS.
- T0 HASH: PASS.
- TEMP ASSETS: PASS.
- Основной SurvivalProject: Git clean.
- Изолированный SurvivalProject_T0: изменены только документы `Docs/ProjectStatus.md` и `Docs/Architecture/18_T0_LOCAL_ATTEMPT.md`.
- Оригинальные игровые ресурсы не изменены.
- Временные Blueprint отсутствуют на диске.

Предыдущая автоматизированная попытка завершилась NOT RUN / BLOCKED из-за ограничений управления интерфейсом. Последующая ручная проверка успешно закрыла блокер.

**Итог:** доступ к Private-членам другого экземпляра того же Blueprint-класса подтверждён реальной компиляцией. Доступ из внешнего Blueprint корректно запрещён.

**A11 разблокирована для отдельной реализации.** Сама реализация A11 ещё не начата. Архитектура A09, A10 и A36 не изменялась.

Подробности: [Issue #14 — итоговый отчёт T0](https://github.com/zonor922-hub/SurvivalProject/issues/14#issuecomment-6471492116).

## A11 — история первого блокера (28.10.2026)

Историческая запись. Снято разрешением пользователя; актуальные результаты — [отчёт21](Architecture/21_A11_TRANSFER.md).

T0 остаётся PASS по Issue #14. Реализация A11 остановлена по явному условию §3.3/§8 п.5 проекта: UE 5.8.4 подтвердил, что SimulateAddExact возвращает только Success, а классификация ошибок находится в TryAddExact. Переиспользование требует отдельно согласованного изменения A09; копирование логики запрещено. Ассеты не менялись, исходный BPC_Inventory скомпилирован успешно. Тесты реализации и регрессия NOT RUN. Ветка task/a11-atomic-transfer от 02fe8a8, отдельный worktree D:/Project/SurvivalProject_A11; коммит, push и PR не выполнялись. [Доказательства, SHA-256 и матрица тестов](Architecture/19_A11_TRANSFER_BLOCKER.md).

## A11 — история второго блокера (28.10.2026)

Историческая запись. Снято вторым разрешением пользователя; FAIL7c ниже относится к прежнему ассету. Актуальные результаты — [отчёт21](Architecture/21_A11_TRANSFER.md).

Первоначальный блокер19 снят разрешением пользователя на выделение общего private CheckReceiveExact. Рефакторинг A09 прошёл полный runner:486 PASS, компиляция12 Blueprint, PIE A09/A10 3/3 и A24. В worktree A11 сохранена частичная реализация переноса; тесты A11:2726 PASS-проверок,1 FAIL на7c (неактивная Durability при merge), оставшиеся сценарии NOT RUN. Прямой A09 вызов и неизменный граф SimulateAddExact подтвердили дополнительное противоречие требованиям7c/36; реализация остановлена для нового решения. A11 НЕ завершена. Коммит/push/PR не выполнялись. [Исторический отчёт, матрица и SHA-256](Architecture/20_A11_IMPLEMENTATION_STATUS.md).

Повторная регрессия на текущих ассетах A11 завершилась:486 PASS/0 FAIL, компиляция12 Blueprint, PIE A09/A10 по3/3, A24 PASS; файлы во время тестов не менялись. Это не отменяет FAIL7c и NOT RUN остальных тестов A11. [Summary](Architecture/evidence/a11_current_regression.json).

## A11 — история контрольного этапа7620 (29.10.2026)

После утверждённой нормализации неактивной Durability итоговый стандартный запуск UE5.8.4:7620 PASS assertions/0 FAIL, включая прежние486; компиляция12 Blueprint, PIE A09/A10/A11 по3/3, A24 PASS, exit0, changed_source_files=[]. Отрицательная проверка runner вернула ожидаемый shell exit1. Сверка803 файлов нашла только2 изменённых игровых ассета. Полная приёмка не объявлена: NOT RUN части25c/32/40, отложенные38a–d(A39), повтор исторического T0 перечислены отдельно в [отчёте21](Architecture/21_A11_TRANSFER.md). Никакой коммит или публикация не выполнялись.

## A11 — предкоммитное завершение25c/40 (29.10.2026)

Предкоммитный стандартный UE5.8.4 runner: 15011 PASS/0 FAIL,486 baseline сохранены;12 Blueprint, PIE A09/A10/A11 по3/3, A24 PASS.25c:40 двусторонних переносов с неизменным C;40:562 вызова с полным аудитором. Игровые ассеты не менялись после ранее утверждённой реализации. Разрешён локальный коммит с последующей проверкой чистого HEAD. [Текущая матрица](Architecture/21_A11_TRANSFER.md).

## A11 — история приёмки15011 (29.10.2026)

**Ready for PR.** Реализация `1acdb0c3f5bc60d5c7d0872b4de81867a402173c`: полный стандартный прогон на чистом HEAD —15011 PASS/0 FAIL,12 Blueprint, PIE A09/A10/A11 по3/3 и A24 PASS; context.working_tree=[], exit0, timed_out=false, changed_source_files=[].25c/40 полностью закрыты; обязательных NOT RUN A11 нет.38a–d отложены по ТЗ в A39, T0 — исторический PASS. [Матрица/риски/SHA](Architecture/21_A11_TRANSFER.md), [clean summary](Architecture/evidence/a11_clean_head_summary.json). Только два игровых ассета плюс тесты/документация; main/backup сохранены. Push/PR/merge не выполнялись.

## A11 — история предкоммитного усиления40 для отказов

Последний полный предкоммитный прогон15093 PASS/0 FAIL: добавлены82 прямые побитовые проверки Durability на отказах. Production не менялась. Следующий этап — чистый HEAD нового тестового набора; предыдущие чистые1acdb0c/53cdc0d успешно прошли15011/0. Push/PR/merge запрещены.

## A11 — историческая локальная приёмка перед публикацией (29.10.2026)

**На тот момент: Ready for PR.** Протестированный чистый коммит `c858e932306c7dd7d9419562a00572da96e3927c`:15093 PASS/0 FAIL, context.working_tree=[],12 Blueprint, PIE A09/A10/A11 по3/3, A24 PASS, exit0, timed_out=false, changed_source_files=[].25c/40/32 полностью закрыты, включая82 прямые bitwise-проверки на отказах.38a–d остаются отложенными в A39; T0 ранее PASS. [Отчёт/риски/SHA](Architecture/21_A11_TRANSFER.md), [фактический clean summary](Architecture/evidence/a11_clean_head_summary.json). После коммита только итоговой документации проверяются чистота и идентичность runtime/test blobs этому проверенному коммиту. Main/backup сохранены; push/PR/merge не выполнялись.

## A11 — итог после объединения PR №16 (29.10.2026)

**Завершена / Merged / Closed.** [PR №16](https://github.com/zonor922-hub/SurvivalProject/pull/16), аудитированный HEAD `957947c92c30a688fc8c28048226bcbd670e3383`, итоговый merge SHA `6d4e854cbacc08e7f6d661eff00714c94cf974a4`. Все 41 файла вошли без дополнительных изменений. Проверенный чистый implementation/test-коммит — `c858e932306c7dd7d9419562a00572da96e3927c`; финальный HEAD отличается от него лишь документацией/JSON. **15 093 PASS / 0 FAIL** (assertions, не сценариев), 12 Blueprint, PIE A09/A10/A11 по 3/3, A24 PASS — результаты до merge, без нового UE-прогона после него. [Финальная матрица](Architecture/21_A11_TRANSFER.md), [clean summary](Architecture/evidence/a11_clean_head_summary.json).

Независимый аудит: **Ready with Conditions**, Blocker/Major нет, [условия и принятие риска](https://github.com/zonor922-hub/SurvivalProject/pull/16#issuecomment-6488845100). Принят остаточный риск непрозрачности бинарных Blueprint: проверка опирается на Editor API traversal/graph paths и runtime assertions; прямой source-level аудит `.uasset` не заявляется. Ограничения: A36/T15 — глобальные GUID с третьим инвентарём; A39 — загрузка/инвалидирование команд, **38a–d NOT RUN**; F04 — свежий cook/package, **не выполнен**. Отчёты 19/20 и ранние результаты сохранены как история, не как текущий статус.

## A12 — гибридная приёмка и аудит (29.10.2026; историческая запись до merge)

**На момент записи: завершена в отдельной ветке / Ready for PR; не объединена в main.** Ветка codex/a12-inventory-tests от origin/main 79bb0fc. Найдены три оригинальных user-started PIE JSON UE5.8.4: 166/0, 153/0, 226/0, всего **545 PASS / 0 FAIL**; копии побитово идентичны, SHA-256 и provenance записаны в manifest. Новый black-box harness реального BPC_Inventory: 1644/0, три группы по три независимых повтора. Игровые ассеты/архитектура не менялись, main/backup сохранены. Финальная регрессия: 15093/0, 12 Blueprint, автоматические PIE A09/A10/A11 по 3/3 и A24 PASS; отрицательный runner shell exit 1. Блокирующих замечаний нет; ChangedSlots — Minor, diagnostics идентичны принятой A11. Чистый implementation/test HEAD `eeb32f801cc6abd5bd040245b342d5e1e39e5038` повторил 1644/0 и 15093/0, context.working_tree=[], editor exit 0, timeout=false, changed_source_files=[]. Итоговые документы/JSON не меняют исполняемые тесты. [Clean summary](Architecture/evidence/a12_clean_head_summary.json). Merge запрещён. [Отчёт, доказательства и риски](Architecture/22_A12_INVENTORY_TESTS.md).


## A12 — итог после объединения PR №18 (29.10.2026)

**Завершена / Merged / Closed.** [PR №18](https://github.com/zonor922-hub/SurvivalProject/pull/18) объединён обычным merge commit `fa74e69536d0ff4339fa41bfa3badd9a6d0bb93c`; проверенный HEAD `c6c19f0739e972929f3d58d8dc27945e78c6502c` вошёл в main. На момент проверки `main` совпадала с merge commit; squash/rebase не применялись. Независимое заключение, представленное пользователем: **READY FOR MERGE**, Critical/High замечаний нет. Автоматическая A12: **1 644 PASS / 0 FAIL** (9 повторов); ручные PIE: **545 PASS / 0 FAIL** (3 сценария); регрессия: **15 093 PASS / 0 FAIL**, 12 Blueprint, A09/A10/A11 PIE 3/3, A24 PASS; отрицательный runner — ожидаемый exit 1. Это результаты **до merge**, UE после объединения повторно не запускался. Игровые файлы A12 не изменяла. Остаточные риски: три предупреждения ChangedSlots (Minor), отсутствие встроенного SHA исходников в ручных JSON, ограничения бинарного аудита Blueprint и ранее принятый A10 guard sensitivity. F04, A39 и A36/T15 не входят в завершённую A12.

## A13 — итог после объединения PR №19 (29.10.2026)

**Завершена / Merged / Closed.** [PR №19](https://github.com/zonor922-hub/SurvivalProject/pull/19) объединён обычным merge commit `a09826aab6cff4ebfe7f2bdbcd54d85e9af3aff0`; исходный проверенный HEAD `154711fd63b61566724727b4901918dcb11e29c7`. Аудит: **READY WITH CONDITIONS**, блокирующих замечаний по опубликованным материалам нет. Три Blueprint скомпилированы (BS_UP_TO_DATE), PIE 3/3, **171 PASS / 0 FAIL**, результаты получены **до merge**, без повторного запуска UE после него. Шесть игровых ресурсов и четыре файла отчётности/документации опубликованы; карта, Config, Inventory не менялись. Ограничения: тестовая Python/Blueprint-оснастка и полные логи находятся локально в `Saved/Verification/A13`, воспроизводимость после чистого checkout не подтверждена; используется Visibility channel вместо отдельного Interaction channel; package и multiplayer **NOT RUN**. На момент подготовки отчёта A13 задача A14 оставалась отдельной; позднее объединена через PR №20. Последующие задачи A15–A17 не реализованы в A14.

## A14 — итог после объединения PR №20 (29.10.2026)

**Завершена / Merged / Closed.** [PR №20](https://github.com/zonor922-hub/SurvivalProject/pull/20) объединён обычным merge `a8e8fcaea27ed39852c25d5ac912aa5b62a1434f`; финальный HEAD `4fcca7f4e34ef718e8a69c2afc61a759b8251583`, проверенный игровой commit `5209f56b186245590f0298140ad9774abedb816d`. Между ними изменены только отчёт A14 и ProjectStatus, без изменения Blueprint. В main добавлены IA_Interact, IA_Inventory, IMC_Survival, ESurvivalInputMode и обновлён BP_SurvivalPlayerController: события OnInteractRequested(Pawn) и OnSurvivalInputModeChanged(Mode), защита BootstrapReady/Pawn, режимы Gameplay/UI/Build, восстановление при possession, сохранение шаблонных Mapping Contexts. Подбор предметов и полноценный экран инвентаря не реализованы.

**Приёмка до merge:** 8 Blueprint BS_UP_TO_DATE; 274 PASS / 0 FAIL в двух PIE с action injection (в каждом по три смены Pawn); 4 PASS / 0 FAIL исправленного UI Jump; 548 PASS / 0 FAIL A12 до исправления Jump (Inventory после него не менялся). Реальный UI Jump FAIL до исправления задокументирован отдельно. **Ручная проверка пользователя после merge:** Tab открывает/закрывает UI, движение, камера и прыжок блокируются, управление восстанавливается; физическая E дошла до `IA_Interact` (подтверждено breakpoint), но полноценного действия в мире ещё нет, поскольку A15 не реализована. Ручная проверка не равна повторному полному автоматическому прогону UE после merge.

**Ограничения:** полная A13 (171 assertions), A24, package, multiplayer, визуальная QA — NOT RUN в A14; input injection не заменяет все физические сценарии ввода. Предсуществующие 17 startup `Condition failed` задокументированы без установления причины; в финальных PIE Blueprint Runtime Error / Accessed None не обнаружено. [Технический отчёт и evidence](Architecture/24_A14_ENHANCED_INPUT.md). Исторический следующий шаг после A14 — отдельная A15 по [backlog](Architecture/03_IMPLEMENTATION_BACKLOG.md).

## История A15 — World Pickup (30.10.2026; до merge PR №22)

Статус: локальная реализация завершена, ожидает PR и независимого аудита. В main пока не объединена.

Реализованы BP_WorldPickup и подключение взаимодействия в BP_SurvivalPlayerController.

Ручные PIE-проверки:
- Успешный подбор, итоговый Inventory Snapshot 3 -> 5: PASS.
- WeightLimit, неизвестный ItemId: PASS.
- Дистанция, Visibility/стена: PASS.
- UI, Consumed, PickupInProgress, повторные E: PASS.
- Ошибок Blueprint Runtime Error / Accessed None не обнаружено.

Регрессия:
- A14 Full PIE: 274 PASS / 0 FAIL, UE exit 0.
- A14 regression: Jump 4/0, A12 548/0, UE exit 0.
- A12 runner: 1644 assertions PASS / 0 FAIL; итог runner false из-за неопределённого exit code.

Не подтверждены: точная граница 250 см, полный Snapshot при отказе pickup, заполнение слотов, reentrant callback, lifecycle после смены Pawn, уничтожение цели между focus и execute, package и multiplayer.

Подробности: Architecture/25_A15_WORLD_PICKUP.md.

Следующее действие: публикация PR A15, независимый аудит. Merge не выполнять.

## История A15 — независимая проверка 31.10.2026: NOT READY (до исправления)

Camera trace A13/A15 исправлен локально с геометрически обоснованной дальностью. Целевые PIE-проверки границы, rollback, слотов, reentry, E, препятствий и смены Pawn выполнены. Новый BLOCKER: HandleWorldPickupRequest вызывает ExecuteInteraction на уничтоженной цели (PIE runtime error). Работа остановлена; локальные изменения не закоммичены и не отправлены. Следующее действие — IsValid цели до чтения GUID/вызова, затем только затронутые проверки. См. Architecture/25_A15_WORLD_PICKUP.md и evidence/a15_followup_results.json. Merge PR #22 запрещён.

## История A15 — lifecycle BLOCKER закрыт 31.10.2026: READY (до merge)

В ветке PR #22 сохранены camera reach A13/A15 и IsValid(FocusedActor) до чтения GUID/ExecuteInteraction. Целевой lifecycle PIE: 10 PASS / 0 FAIL, UE exit 0, полный лог без Blueprint Runtime Error/Accessed None. Полный Snapshot при командах по уничтоженной цели неизменен; успешный pickup, повторные E и callback reentry проверены. Предыдущие проверки границ/rollback/слотов/стены/Pawn переиспользованы; полная регрессия, package, multiplayer и новая физическая E — NOT RUN. Подробности: Architecture/25_A15_WORLD_PICKUP.md и Architecture/evidence/a15_lifecycle_results.json. Merge не выполняется.
