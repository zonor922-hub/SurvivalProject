# A13 — Interaction Focus

Статус: **завершена**, 29 октября 2026 (Europe/Moscow). Зависимость: A04; проверенная база `dbb273bb94b95e808a4fa998c3682252c48e4738`. UE `5.8.4-58902052+++UE5+Release-5.8`, Blueprint-only.

Продолжение выполнено с шага 34. Сохранены пять ресурсов пользователя и все 21 исходный узел UpdateFocus. BPI_Interactable и структуры не пересоздавались; их контракты не менялись.

## Реализация

- BPC_Interaction: ApplyFocus сравнивает ссылку с текущей, присваивает FocusedActor и вызывает OnFocusChanged(NewFocus) только при изменении. Все отказы UpdateFocus очищают Focus через эту функцию.
- Существующий camera Line Trace использует Visibility, игнорирует текущий Pawn и выбирает первый blocking hit. Требуются BPI_Interactable, живая цель и расстояние **Pawn location -> ImpactPoint <= 250 см**. TraceDistance = 600 см. Дополнительная трасса Pawn -> ImpactPoint исключает взаимодействие сквозь препятствие со стороны Pawn. Blocking hit другого актора отклоняется.
- Стены и взаимодействующие объекты должны блокировать Visibility. Для проверок использованы кубы с BlockAll. Объект без интерфейса блокирует луч, но не становится целью. Конфигурация collision проекта и карта не менялись.
- BeginPlay запускает StartFocusSearch: очищает старый FocusTimerHandle, устанавливает looping timer UpdateFocus с FocusInterval = 0.1 с и выполняет первый поиск. Event Tick удалён; Start with Tick Enabled выключен.
- Каждый поиск заново получает Controller и его Pawn. CastFailed, невалидный Controller/Pawn, промах, отсутствие BPI, дальняя или уничтоженная цель сбрасывают Focus. Ссылки на Pawn/Controller не кэшируются.
- EndPlay вызывает StopFocusSearch: Clear and Invalidate Timer by Handle и очистка FocusedActor. В BP_SurvivalPlayerController добавлен ровно один компонент Interaction.
- Enhanced Input, выполнение взаимодействия, подбор, Inventory-команды и HUD не добавлялись.

## Файлы

Игровые: `Content/Survival/Core/BP_SurvivalPlayerController.uasset` и пять ресурсов в `Content/Survival/Interaction/`: BPI_Interactable, BPC_Interaction, FInteractionOption, FInteractionContext, FInteractionResult. Документация: этот отчёт, ProjectStatus.md и два evidence JSON. Карты, Config и Inventory не изменены.

## Проверки

Реальная финальная компиляция BPI_Interactable, BPC_Interaction, BP_SurvivalPlayerController: **PASS**, каждый BS_UP_TO_DATE. [Схема графов, соединения и compile-результаты](evidence/a13_blueprint_audit.json). Это отдельная проверка, она не засчитывается как PIE.

**Реальный PIE на LV_SystemsTest: 3/3 свежих запуска, 171 PASS / 0 FAIL** — по 57 assertions в запуске. [Полная матрица с отдельными результатами](evidence/a13_pie.json).

| Runtime-сценарий | Результат |
|---|---|
| Цель в 150 см от Pawn, таймерный поиск | PASS x3 |
| Камера позади Pawn, достижение цели трассой 600 см; предел camera trace | PASS x3 |
| Стена BlockAll блокирует цель; удаление препятствия возвращает Focus | PASS x3 |
| Объект без BPI не становится целью | PASS x3 |
| ImpactPoint в 300 см сбрасывает Focus; ровно 250 см принимается, 250.5 см отклоняется | PASS x3 |
| Промах и возврат направления камеры | PASS x3 |
| Уничтожение цели и появление новой | PASS x3 |
| Unpossess, повторный possess, смена Pawn и проверка расстояния от нового Pawn | PASS x3 |
| Компонент с владельцем без Controller | PASS x3 |
| Стабильная цель не повторяет события; десять рестартов оставляют один активный timer handle | PASS x3 |
| EndPlay владельца и уничтожение компонента удаляют таймер; Focus очищается одним событием | PASS x3 |
| Полный snapshot Inventory, включая Quantity и Revision, совпадает после каждого шага | PASS x3 |
| Accessed None / Blueprint Runtime Error в сохранённом журнале | Не обнаружены |
| Packaged build | NOT RUN; не требуется критериями A13 |

PIE управлялся Python Editor API, а поиск, таймеры, события и EndPlay исполнялись настоящими Blueprint. Использованы временный StaticMeshActor Blueprint с существующим BPI, Blueprint listener и Blueprint spawner; они не сохранялись в Content. Камера фиксировалась CameraActor, движение тестовых Pawn отключалось после possession, чтобы точно проверять расстояния. Это функциональные runtime-тесты; обычное управление игроком и Enhanced Input не проверялись в A13.

Полный журнал редактора, исполнявшиеся Python-скрипты, предварительные диагностики оснастки и результаты сохранены локально в `Saved/Verification/A13/` и `Saved/a13_*.py`. Основной журнал: `Saved/Verification/A13/SurvivalProject.log`. Предварительные FAIL касались оснастки: старый Pawn на линии, падение нового Pawn после possession, ссылки Python на меняющийся TimerHandle и доступ к не editable переменной. Исправления оснастки: убрать старый Pawn, выключить движение после possess, брать TimerHandle.copy(), вызывать ApplyFocus через Blueprint. Затем вся матрица прошла трижды. Эти попытки не включены в 171 PASS.

Дополнительное сохранение постоянного тестового Blueprint и косметические правки графов не выполнены: automatic approval review отклонил дополнительные persistent side effects. Игровая реализация была сохранена ранее; все обязательные проверки выполнены на ней.

## Ограничения

Тестовые Blueprint временные: для повторения после перезапуска редактора необходимо создать тестового наследника StaticMeshActor с BPI_Interactable и восстановить listener/spawner из локальных Python-скриптов. JSON-аудит фиксирует проверенную игровую схему, но не является независимым runtime runner. После потери цели Focus обновляется ближайшим поиском (обычно до 0.1 с игрового времени). Для объектов без блокировки Visibility обнаружение не предусмотрено. Упаковка и multiplayer — NOT RUN.
