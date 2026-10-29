# A12 — инварианты inventory: гибридная приёмка и финальный аудит

29.10.2026, Europe/Moscow. **Завершена / Merged / Closed.** [PR №18](https://github.com/zonor922-hub/SurvivalProject/pull/18) объединён обычным merge commit `fa74e69536d0ff4339fa41bfa3badd9a6d0bb93c`.
База: `origin/main` = `79bb0fcbaa478f658d913e613be1ca00faf3fd5a`, fetch выполнен.
Ветка `codex/a12-inventory-tests`; изолированный worktree:
`C:/Users/Denis/.codex/worktrees/a12-inventory-tests/SurvivalProject`.
Локальная main и резервные ветки сохранены. Публикация — отдельный PR в main; merge запрещён без разрешения.

## Требования и зависимости

ТЗ: [Backlog A12](03_IMPLEMENTATION_BACKLOG.md#a12--закрепить-инварианты-inventory-тестами).
Прочитаны Architecture, Backlog, ProjectStatus, отчёты A09/F01/F02, A10, A11.
A04 (LV_SystemsTest), A09/F01/F02, A10 (PR12), A11 (PR16) присутствуют в базе.
Контракт: публичные операции настоящего BPC_Inventory, Snapshot, баланс количества,
границы веса/слотов, split/merge, transfer, stale revision, три одинаковых повтора.
Архитектура A01–A44 и функциональность A09/A10/A11 не менялись.

## Подготовленная инфраструктура

- `evidence/a12_suite.py`: три группы black-box assertions. Вызывает публичные команды
  настоящего BPC_Inventory; не реализует симулятор размещения, merge или transfer.
  Простые ожидаемые количества взяты из фиксированных wood=20/0.5 данных проекта.
- `evidence/a12_runner.py`: три одинаковых повтора каждой группы (9 запусков),
  реальная компиляция Blueprint, новый GameInstance с реальным каталогом.
- `evidence/run_a12.ps1`: отдельный UnrealEditor-Cmd, уникальный каталог результатов,
  контекст SHA/dirty, полные SHA256 Content/Config/uproject до/после, timeout,
  обработка исключений и ненулевой shell exit при отказе. За основу взят существующий runner.
- `evidence/a12_pie.py`: выполнение выбранной группы на реальном Inventory PlayerState
  уже запущенной пользователем PIE-сессии. Не создаёт графы и не сохраняет ассеты.
  Дополнительные ограниченные инвентари существуют только в памяти.

Проверяются: detached nested Snapshot; отсутствие мутации от повторных чтений;
нулевой вес и точная верхняя граница; превышение веса; полный слот;
количество 0/−1; многостековое удаление 21; split 6+4 и merge обратно;
занятая цель, исчезнувший GUID, переполнение MaxStack; transfer 7/3 и целого стека;
обе stale revisions; self-transfer; отказы по весу и слотам с полным сравнением
снимков обеих сторон; успешные Revision +1, неизменные Revision при отказах;
уникальные/валидные GUID и стабильные индексы слотов; баланс и вес после операций.
Проверка инвариантов self-transfer учитывает один и тот же объект один раз.
События и видимость обеих commit в callbacks дополнительно проверяет неизменённая
регрессия A09/A10/A11. A12 не проверяет детали графов реализации.

## Автоматические проверки

Команды из корня worktree:

```powershell
& ./Docs/Architecture/evidence/run_a12.ps1 -EngineRoot 'F:/UE_5.8'
& ./Docs/Architecture/evidence/run_a12.ps1 -EngineRoot 'F:/UE_5.8' -InjectFailureForRunnerTest
& ./Docs/Architecture/evidence/run_f01_f02.ps1 -EngineRoot 'F:/UE_5.8'
```

Движок: `5.8.4-58902052+++UE5+Release-5.8`.
Новый набор: **1644 PASS / 0 FAIL assertions**, 9/9 запусков;
scenario 1 = 167, scenario 2 = 154, scenario 3 = 227 assertions на повтор.
Blueprint status BS_UP_TO_DATE; shell/editor exit 0; timeout false;
changed_source_files = []. Сохранённый результат: `evidence/a12_automatic_summary.json`.
Регрессия: **15093 PASS / 0 FAIL assertions**, 12 Blueprint; автоматические PIE
A09/A10/A11 по 3/3, A24 movement/physics/shore PASS. Shell/editor exit 0,
timeout false, changed_source_files = []. [Свежий summary](evidence/a12_regression_summary.json).
Предупреждения компилятора о возвращении параметра ChangedSlots по ссылке в
CommitInventory/BroadcastChange/Listener сохранены в diagnostics; ошибок компиляции нет.
Отрицательный прогон: все 1644 assertions пройдены, затем намеренный assert;
summary.passed=false, shell exit 1, editor exit 0, хеши неизменны — ожидаемый результат
проверки распространения ошибки, а не дефект BPC_Inventory.
[Отрицательный summary](evidence/a12_negative_summary.json).
Финальный аудит повторил все три команды в Saved/Verification/A12/FinalAudit:
1644/0 A12, 15093/0 регрессия, отрицательный shell exit 1. Diagnostics побуквенно
совпадают с принятой A11. Блокирующих замечаний нет. Тот же набор повторён на чистом
`eeb32f801cc6abd5bd040245b342d5e1e39e5038`: context.working_tree=[], все результаты совпали;
автоматические PIE учитываются отдельно от ручной приёмки.
[Итог чистого HEAD](evidence/a12_clean_head_summary.json).

Первая подготовительная попытка имела синтаксическую ошибку harness, исправленную
до успешного прогона. Следующая выявила LFS pointers в новом worktree вместо
uasset; выполнен git lfs pull. Эти попытки не являются результатом проверки
игровой логики. Их логи сохранены в Saved/Verification/A12 и не входят в PASS.

## Ручная проверка — ровно три контрольных PIE-сценария

Все три **PASS**: оригинальные пользовательские отчёты найдены и проверены, 545 PASS / 0 FAIL.
Автоматические прогоны учитываются отдельно от ручной приёмки.
Для каждого сценария нужен новый запуск PIE; повтор команды в той же сессии
даст ожидаемый отказ требования свежего состояния.

Общая подготовка:

1. Открыть именно `SurvivalProject.uproject` из указанного выше worktree в UE 5.8.4.
   Основной проект `D:/Project/SurvivalProject` для этого не открывать.
2. В «Правка → Плагины» найти Python, включить «Python Editor Script Plugin»
   (название плагина может оставаться английским) и перезапустить редактор по запросу.
   Это локальная настройка проверки; изменение uproject не включать в A12.
   Альтернатива: запуск редактора с `-EnablePlugins=PythonScriptPlugin` без сохранения настройки.
3. «Окно → Инструменты разработчика → Журнал вывода» (Output Log).
   В строке ввода выбрать режим **Python**, а не Cmd.
4. Через «Панель содержимого» открыть `/Game/Survival/Maps/LV_SystemsTest`.
   Выпадающий список у «Играть» → «Выбранное окно просмотра»;
   затем «Играть» (Alt+P), дождаться появления персонажа. Shift+F1 освобождает мышь.
5. После каждой проверки нажать «Остановить» (Esc), затем для следующей заново «Играть».
   Не сохранять пакеты тестового сеанса. Если нет Python API, PIE не начинается,
   не найден Inventory или интерфейс недоступен — записать BLOCKED с точным текстом;
   не заменять запуск расчётом на бумаге и не отмечать PASS.

### 1. Добавление предметов, ограничения вместимости и Snapshot — PASS (166/0)

В свежей PIE выполнить одной строкой в Python-консоли:

```python
import runpy; runpy.run_path('C:/Users/Denis/.codex/worktrees/a12-inventory-tests/SurvivalProject/Docs/Architecture/evidence/a12_pie.py', init_globals={'SCENARIO': 1})
```

Ожидается: 20 wood, вес 10, Revision 1; чтение и изменение возвращённой копии
не меняют компонент. Ещё 1 wood отклоняется по весу; 0/−1 отклоняются.
Удаление 20 возвращает вес 0, Revision 2; последующее удаление отклоняется.
Временные компоненты проверяют нулевую ёмкость, полный слот и удаление 21 из 20+1.
Все отказы сохраняют снимок и Revision. Журнал: `A12 scenario 1: PASS`.
Фиксация: сохранить путь JSON из журнала и снимок экрана журнала/PIE.
PASS только при passed=true и всех tests.passed=true; FAIL при исключении/ложном assert.

### 2. Split/Merge, успешные операции и атомарные отказы — PASS (153/0)

Остановить предыдущую сессию, снова «Играть», выполнить:

```python
import runpy; runpy.run_path('C:/Users/Denis/.codex/worktrees/a12-inventory-tests/SurvivalProject/Docs/Architecture/evidence/a12_pie.py', init_globals={'SCENARIO': 2})
```

Ожидается: 10 wood → 6+4 → 10; вес всегда 5, Revision 1→2→3.
Split сохраняет исходный GUID и создаёт другой валидный GUID; merge сохраняет GUID
приёмника. Split в занятый слот, Quantity=0, merge исчезнувшего GUID, split без
свободного слота и merge сверх MaxStack отклоняются без изменения снимка/Revision.
Журнал: `A12 scenario 2: PASS`. Фиксация и критерий PASS/FAIL — JSON плюс снимок
экрана, как в сценарии 1; отдельно записать наблюдённый итог.

### 3. Transfer, Revision и неизменность после отказов — PASS (226/0)

Остановить предыдущую сессию, снова «Играть», выполнить:

```python
import runpy; runpy.run_path('C:/Users/Denis/.codex/worktrees/a12-inventory-tests/SurvivalProject/Docs/Architecture/evidence/a12_pie.py', init_globals={'SCENARIO': 3})
```

Ожидается: источник 10 → 7, приёмник 0 → 3, общий баланс 10;
Revision источника 1→2, приёмника 0→1. Частичный transfer сохраняет GUID источника
и создаёт другой GUID приёмника. Отказы по устаревшей Revision каждой стороны,
self-transfer, весу и полным слотам сохраняют полные снимки обеих сторон.
Затем целый оставшийся стек 7 переносится в пустой компонент с сохранением GUID,
Revision источника 3 и нового приёмника 1; баланс по всем затронутым компонентам 10.
Журнал: `A12 scenario 3: PASS`. Фиксация — JSON и снимок экрана журнала/PIE.
PASS требует passed=true и отсутствия ложных tests; при отказе сохранить traceback.

JSON создаются в `Saved/Verification/A12/Manual/` с уникальным UTC-временем.
Это assertions над компонентами: предметы не обязаны отображаться в игровом HUD.
Передать три JSON и фактический результат каждого сценария; при сбое также Unreal.log.

## Подтверждение ручных результатов

Найдены оригиналы в Saved/Verification/A12/Manual. Проверены mode=user-started PIE,
engine_version=5.8.4-58902052+++UE5+Release-5.8, passed=true, отсутствие error,
все tests.passed=true, принадлежность assertions указанному сценарию и точный порядок
названий проверок относительно автоматического набора. Репозиторные копии побитово
идентичны оригиналам, включая Git blobs (локальное правило -text исключает нормализацию CRLF); [manifest с путями и SHA-256](evidence/a12_manual_manifest.json).

| Сценарий | PASS | FAIL | Оригинальный JSON (не изменён) |
|---|---:|---:|---|
| PIE-1 | 166 | 0 | [20261029T061819_903866Z](evidence/a12_manual/20261029T061819_903866Z_scenario1.json) |
| PIE-2 | 153 | 0 | [20261029T062205_068223Z](evidence/a12_manual/20261029T062205_068223Z_scenario2.json) |
| PIE-3 | 226 | 0 | [20261029T062253_752995Z](evidence/a12_manual/20261029T062253_752995Z_scenario3.json) |
| Всего | **545** | **0** | Три пользовательские PIE-сессии |

На одну проверку меньше, чем в автоматическом сценарии: primary берётся из уже
инициализированного PlayerState; assertion initialized fixture выполняется только
при создании нового primary автоматическим runner. Проверка fresh primary остаётся
в обоих режимах. Новых ручных сессий агент не создавал и результаты не синтезировал.
Скриншоты не использованы как доказательство: подтверждение опирается на найденные
оригинальные JSON и сообщение пользователя о выполненных сессиях.

## Аудит инфраструктуры и риски

[Машиночитаемый аудит](evidence/a12_audit.json) содержит SHA-256 тестовых исходников,
защищённые refs и сравнение хешей игровых файлов с этапом подготовки.
Каждый из девяти запусков создаёт новый primary и новые ограниченные компоненты;
перед командами утверждаются Revision=0 и пустое состояние. GameInstance общий
только для чтения каталога, A12 его данные не меняет. GUID случайны по контракту;
повторяются входные количества/параметры и семантические ожидания, а не GUID-строки.
Бизнес-логика не копируется: команды исполняет реальный BPC_Inventory.
Импортируемые A09 helpers сериализуют структуры; их suite при импорте не запускается.
AST-проверка подтверждает публичные вызовы и отсутствие save-вызовов в A12 Python.

**ChangedSlots — Minor, неблокирующий.** Три существующих предупреждения в
CommitInventory, BroadcastChange и Listener: «По ссылке не будет возвращено
значение». Dispatcher передаёт массив подписчикам; обратная запись из обработчика
не используется как результат команды. A09/A10/A11 проверяют точные ChangedSlots,
число событий, Revision, снимки обоих инвентарей в callbacks. Исправление сигнатур
не входит в A12 и могло бы затронуть защищённую функциональность. Список diagnostics
сверяется с принятой A11; новые предупреждения требуют отдельного разбора.

**Minor, происхождение отчётов:** исходные ручные JSON содержат режим, версию и
assertions, но не содержат встроенного SHA тестов. SHA-256 оригиналов и неизменных
копий зафиксированы аудитом; происхождение пользовательских сессий подтверждено
пользователем. Криптографическая привязка к историческому HEAD не заявляется.

**Принятые ограничения зависимостей:** бинарные Blueprint проверяются UE API и
runtime assertions; source-level аудит uasset не заявляется. Исторический риск
эксперимента чувствительности guard A10 остаётся принятым в PR12.
**Вне A12:** cook/package F04, загрузка/эпохи A39 (38a–d NOT RUN), координация
глобальных GUID A36/T15. Эти пункты не входят в PASS и не объявлены реализованными.

## Список файлов A12

Созданы:

- Docs/Architecture/22_A12_INVENTORY_TESTS.md
- Docs/Architecture/evidence/a12_suite.py
- Docs/Architecture/evidence/a12_runner.py
- Docs/Architecture/evidence/a12_pie.py
- Docs/Architecture/evidence/run_a12.ps1
- Docs/Architecture/evidence/a12_automatic_summary.json
- Docs/Architecture/evidence/a12_negative_summary.json
- Docs/Architecture/evidence/a12_regression_summary.json
- Docs/Architecture/evidence/a12_manual/ — три неизменных оригинальных JSON-копии и .gitattributes (*.json -text), сохраняющий исходные окончания строк
- Docs/Architecture/evidence/a12_manual_manifest.json
- Docs/Architecture/evidence/a12_audit.json
- Docs/Architecture/evidence/a12_clean_head_summary.json

Изменён: Docs/ProjectStatus.md. Игровые ассеты, Config и uproject не изменены.
Восстановление LFS материализовало отслеживаемые бинарные файлы без изменения их содержимого.
Локальные логи/хеши/контексты находятся в игнорируемом Saved/Verification,
не предназначены для добавления в Git целиком.

## Итог публикационного аудита

Приёмка A12 выполнена: 1644/0 автоматических assertions, 545/0 пользовательских PIE,
15093/0 полной регрессии, 12 Blueprint, автоматические PIE A09/A10/A11 по 3/3,
A24 PASS. Отрицательный runner подтверждён shell exit 1. Все три чистых процесса:
editor exit 0, timeout=false, changed_source_files=[]. Хеши 803 игровых файлов
равны этапу подготовки. Git LFS fsck OK; локальная main и обе backup refs неизменны.

Implementation/test-коммит указан в clean summary. Последующий коммит добавляет
результаты чистого прогона, итоговую документацию и атрибут whitespace=cr-at-eol
для неизменных CRLF JSON-доказательств. Исполняемые тесты и игровые blobs между
проверенным коммитом и публикуемым HEAD должны быть идентичны; это проверяется
перед push. Три оригинальных отчёта в Git проверены по SHA-256 manifest.

Результат аудита **на момент публикации**: **Ready for PR**, блокирующих замечаний нет. Риски и границы
проверки перечислены выше; на том этапе merge не выполнялся.


## Итог после объединения (29.10.2026)

**A12 завершена.** [PR №18](https://github.com/zonor922-hub/SurvivalProject/pull/18) — **Merged / Closed** обычным merge, SHA `fa74e69536d0ff4339fa41bfa3badd9a6d0bb93c`.
Аудированный HEAD `c6c19f0739e972929f3d58d8dc27945e78c6502c` включён в main.
Проверенные до merge результаты: A12 **1644 PASS / 0 FAIL** (9 запусков), ручные PIE **545 PASS / 0 FAIL**,
регрессия **15093 PASS / 0 FAIL**, 12 Blueprint, A09/A10/A11 PIE 3/3, A24 PASS;
отрицательный runner — ожидаемый exit 1. Независимый аудит, представленный пользователем,
вынес вердикт **READY FOR MERGE**, без блокирующих замечаний.
Новый прогон Unreal Engine после merge **не выполнялся**. Принятые низкие риски и задачи вне A12 перечислены выше.
