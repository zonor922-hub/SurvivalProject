# DOC-SLEEP01 — документация сна

**DESIGN COMPLETE / APPROVED; IMPLEMENTATION NOT STARTED.** [GDD SLEEP01](../GDD/SLEEP01_Sleep_2026-11-05.md) фиксирует решения владельца от 05.11.2026, в том числе переданную восстановленную сводку; числовой баланс — **TUNING / NOT FINAL**.

Зависимости: A15, A20/A21, A23/A24, Inventory/BP01, TIME01, DEATH01, [A36 Save](15_A36_SAVEGAME_ARCHITECTURE.md) и A37–A40, будущие угрозы и погода. Проектные BP01, TIME01 и DEATH01 присутствуют в Draft PR #32 и не включены в данную задачу; их независимые решения не утверждаются этим документом. Существующая схема сохранения не изменена.

Изменения: GDD SLEEP01, этот отчёт и ProjectStatus. Проверки: `git diff --check`, локальные Markdown-ссылки, Repository CI и проверка состава diff. Игровые проверки, Blueprint, PIE и сборка не запускались; реализация не заявлена проверенной.
