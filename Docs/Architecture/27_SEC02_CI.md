# SEC02 — статические проверки репозитория без Unreal Engine

Дата: 02.11.2026. Зависимость: SEC01 / PR №24.
Исходная база: `security/sec01-disable-afs`, `db95b1c909598828b1cb6a41eb3c9826109c8525`.
Проверенный `main`: `aa8f7dbd25bf707a30722feee809794d61fcfbf8`.
Ветка: `ci/sec02-repository-checks`; Draft PR направляется в `security/sec01-disable-afs`, поскольку PR №24 ещё не объединён. После merge SEC01 базу SEC02 нужно отдельно переключить на `main`. SEC02 не изменяет PR №24.

## Реализация

`.github/workflows/repository-ci.yml` запускается на всех `pull_request` без фильтра путей/целевой ветки, на `push` в `main` и через `workflow_dispatch`. Runner — `ubuntu-latest`, Python 3.12; права — только `contents: read`. Группа concurrency привязана к номеру PR или ref, устаревший запуск отменяется. Timeout — 10 минут. Checkout не сохраняет credentials и не загружает LFS; checkout/setup-python закреплены полными SHA. Секреты и дополнительные Python-пакеты не требуются.

Проверки реализованы в `scripts/ci/repository_checks.py`; самотесты — в `scripts/ci/test_repository_checks.py`. Список выбранных исторических evidence и их SHA-256 находится в `scripts/ci/evidence_manifest.json`.

| Группа | Что проверяется |
|---|---|
| structure | 18 обязательных отслеживаемых файлов, включая конфигурацию, основные assets, документацию и CI; FileVersion и EngineAssociation в uproject |
| python | AST всех отслеживаемых `.py`; игровые скрипты не импортируются и не исполняются |
| json | Все отслеживаемые JSON/uproject/uplugin, UTF-8/BOM, запрет повторных ключей и NaN/Infinity |
| lfs | Канонический pointer v1 с SHA-256 и размером в Git index; эффективные cached `.gitattributes`, обязательные бинарные расширения, `filter/diff/merge=lfs`, `-text`; pointer без атрибутов отклоняется |
| ini | UTF-8, секции и key=value; повторные ключи и операторы массивов UE `+`, `-`, `.`, `!` допускаются, значения не интерполируются |
| afs | В DefaultEngine.ini plugin/network выключены, безопасные Shipping-флаги сохранены; неоднозначные повторные флаги и SecurityToken, включая пустое значение и альтернативный регистр, отклоняются без вывода значения |
| evidence | Четыре исторических JSON: SHA-256 после нормализации CRLF в LF, основные типы полей, записи assertions; для A12 — commit/runner metadata и согласованность счётчиков |

Выбранные evidence: `a12_automatic_summary.json`, `a12_negative_summary.json`, `a14_pie.json`, `a15_lifecycle_results.json`. Исторический `passed=false` допускается: отрицательный A12 runner не должен превращаться в ошибку статического CI. Исторические SHA assets не сравниваются с текущими игровыми ресурсами как доказательство нового запуска. Изменение manifest требует содержательного review, а не автоматического обновления контрольных сумм.

LFS проверяется через Git index и `git cat-file`: сначала запрашиваются размеры объектов, затем читаются только blobs до 1024 байт. Содержимое тяжёлых assets не читается и не скачивается. Поэтому проверка одинакова для smudged checkout и checkout только с указателями. Следует учитывать: неиндексированные изменения `.gitattributes` и бинарников не входят в LFS-проверку.

## Локальный запуск

Из корня проекта, Python 3.12 и Git в PATH:

```bash
python -B scripts/ci/repository_checks.py
python -B -m unittest discover -s scripts/ci -p 'test_*.py' -v
```

Для отдельной группы: `python -B scripts/ci/repository_checks.py --check afs`.
Для другого checkout доступен `--root /path/to/checkout`.
Новые файлы и изменения LFS metadata должны быть добавлены в index до проверки; checker не выполняет `git add` самостоятельно. Каждая группа печатает понятный PASS/FAIL, при ошибке CLI возвращает 1. Значения конфигурации и исходные строки с секретами в диагностику не выводятся.

Самотесты создают отдельные временные Git-репозитории, копируют только выбранные текстовые evidence и генерируют малые фикстуры. Исходный checkout и существующие результаты тестов не перезаписываются. Никаких UE runners они не запускают.

## Результаты подготовки в Codex Cloud

- PASS: все 7 групп на проекте — 18 обязательных файлов, 45 Python-файлов, 91 JSON/descriptor, 809 LFS-указателей, 5 INI, AFS и 4 исторических evidence.
- PASS: 14 самотестов; ожидаемые отказы возвращают exit code 1. Повреждённый JSON (также duplicate keys/NaN), Python syntax error, некорректный pointer и небезопасная AFS-конфигурация обнаруживаются.
- PASS: дополнительные сценарии — raw binary вместо pointer, несоответствие LFS-атрибутов, pointer без атрибутов, повреждённый INI, отсутствующий обязательный файл, изменение digest evidence и некорректная schema даже после пересчёта digest.
- PASS: положительные сценарии — UE duplicate/array keys, исторический negative evidence, AST без исполнения фикстуры с `raise`, LFS index при smudged рабочем файле.
- PASS: локальный разбор YAML и проверки triggers/permissions/concurrency; существование закреплённых SHA actions подтверждено через GitHub API.
- PASS: `git diff --check`, область изменений SEC02; Config, Content и прежние evidence совпадают с базой SEC01.
- Первый запуск самотестов: 13/14; один сбой подготовки временного удаления файла исправлен в новой тестовой оснастке. Итоговый повтор: 14/14. Это не игровой FAIL и не изменение исторического evidence.
- GitHub Actions до публикации PR: **NOT RUN**. Фактическое исполнение на GitHub проверяется после публикации и сообщается отдельно; локальный PASS не означает успешный удалённый запуск.
- Unreal Editor, Blueprint compilation, PIE, ввод, cook/package: **NOT RUN**.

## Фактический GitHub Actions run после публикации

[Run 41439797798](https://github.com/zonor922-hub/SurvivalProject/actions/runs/41439797798), событие `pull_request` для Draft PR №25, head `ceb490f20a5b73d1e6822a18d2cc94f711c44281`: **completed / success**. Job `Repository checks (no Unreal Engine)` и оба шага проверки metadata/evidence и временных положительных/отрицательных фикстур завершились успешно. Это первый реальный GitHub Actions PASS, отдельно от локальной проверки и исторических UE evidence. Последующее документирование результата не меняет checker или workflow; статус нового head следует проверять в PR.

## Ограничения и защита main

CI не читает Blueprint-графы, не проверяет игровую логику, физику, визуальное поведение, runtime-зависимости или готовность сборки. Базовый INI-парсер проверяет структуру используемого подмножества формата, а не всю семантику Unreal Config. AST не проверяет доступность Unreal Python API.

LFS-проверка не подтверждает наличие удалённых LFS objects, их загрузку или соответствие реального бинарника digest указателя. Проверка evidence подтверждает целостность выбранных опубликованных документов, а не правдивость, свежесть или повторное выполнение исторических тестов. Manifest и checker находятся в том же PR и требуют review. Полный поиск секретов в истории не реализован этой задачей.

`workflow_dispatch` становится доступен обычным способом после попадания workflow в default branch; недоступность ручного запуска до этого не равна успешной проверке. Политики Actions организации/репозитория могут потребовать ручного разрешения запуска. SEC02 эти политики не меняет.

После SEC01 и SEC02 рекомендуется отдельно включить защиту `main`: обязательный PR, review изменений workflow/скриптов и status check `Repository checks (no Unreal Engine)` после первого реального успешного запуска; запрет force push/удаления и согласованный порядок bypass. Настройки GitHub и merge в SEC02 не выполняются. Перед merge SEC02 после смены базы следует дождаться нового успешного PR-run на актуальном merge ref.

Локальная реализация, самотесты и первый реальный GitHub Actions run проверены. Вердикт: **READY для ручного рассмотрения Draft PR**. После объединения SEC01 требуется отдельная смена базы SEC02 и новый успешный PR-run; автоматический merge не выполняется.
