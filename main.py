from datetime import datetime

from task import TaskStore, DATE_FORMAT, ALLOWED_STATUSES
from bst import BST
from queue_module import TaskQueue
from undo import UndoStack
from filters import filter_tasks, sort_tasks, SavedFilters, SORT_KEYS
from history import NavigationHistory, Snapshot
import storage

STATE_PATH = "data/state.json"

# создаем все хранилища один раз при запуске
store = TaskStore()
bst = BST()
queue = TaskQueue()
saved = SavedFilters()
history = NavigationHistory()
undo = UndoStack(store, bst, queue)

# какие поля задачи разрешено менять
EDITABLE = ("title", "priority", "duration", "deadline", "status", "category")


# --- помощники для ввода ---

def ask(prompt):
    return input(prompt).strip()


def ask_int(prompt, allow_empty=False):
    # спрашиваем целое число, при allow_empty пустой ввод дает None
    while True:
        raw = input(prompt).strip()
        if raw == "" and allow_empty:
            return None
        try:
            return int(raw)
        except ValueError:
            print("нужно целое число")


def ask_deadline(prompt, allow_empty=False):
    # спрашиваем дату в формате 2026-06-15 18:00
    while True:
        raw = input(prompt).strip()
        if raw == "" and allow_empty:
            return None
        try:
            return datetime.strptime(raw, DATE_FORMAT)
        except ValueError:
            print("формат даты: 2026-06-15 18:00")


def show_tasks(tasks):
    if not tasks:
        print("ничего нет")
        return
    for task in tasks:
        print(task)


# --- команды работы с задачами ---

def add_task_cmd():
    title = ask("название: ")
    priority = ask_int("приоритет 1-5: ")
    duration = ask_int("время в минутах: ")
    deadline = ask_deadline("дедлайн (2026-06-15 18:00): ")
    category = ask("категория: ") or "прочее"
    try:
        task = store.create(title, priority, duration, deadline, "новая", category)
    except ValueError as error:
        print("ошибка:", error)
        return
    bst.insert(task)
    undo.push({"type": "add", "task_id": task.id})
    print("добавлена задача #%d" % task.id)


def delete_task_cmd():
    task_id = ask_int("номер задачи для удаления: ")
    task = store.get_by_id(task_id)
    if task is None:
        print("задачи с таким номером нет")
        return
    # сначала запоминаем данные, потом удаляем
    undo.push({"type": "delete", "task_data": task.to_dict()})
    store.remove(task_id)
    queue.remove(task_id)
    bst.rebuild(store.get_all())
    print("задача #%d удалена" % task_id)


def read_field_value(field):
    # спрашиваем новое значение поля с нужной проверкой
    if field == "priority":
        value = ask_int("новый приоритет 1-5: ")
        if not 1 <= value <= 5:
            print("приоритет от 1 до 5")
            return None
        return value
    if field == "duration":
        value = ask_int("новое время в минутах: ")
        if value < 0:
            print("время не может быть отрицательным")
            return None
        return value
    if field == "deadline":
        return ask_deadline("новый дедлайн: ")
    if field == "status":
        value = ask("новый статус (%s): " % ", ".join(ALLOWED_STATUSES))
        if value not in ALLOWED_STATUSES:
            print("недопустимый статус")
            return None
        return value
    if field == "title":
        value = ask("новое название: ")
        if not value:
            print("название не может быть пустым")
            return None
        return value
    # категория без особых проверок
    return ask("новое значение: ")


def edit_task_cmd():
    task_id = ask_int("номер задачи для изменения: ")
    task = store.get_by_id(task_id)
    if task is None:
        print("задачи с таким номером нет")
        return
    print("поля:", ", ".join(EDITABLE))
    field = ask("какое поле менять: ")
    if field not in EDITABLE:
        print("нет такого поля")
        return

    old_value = getattr(task, field)
    new_value = read_field_value(field)
    if new_value is None:
        return

    undo.push({"type": "edit", "task_id": task_id,
               "field": field, "old_value": old_value})
    store.update_field(task_id, field, new_value)
    if field == "deadline":
        bst.rebuild(store.get_all())
    print("задача #%d изменена" % task_id)


def enqueue_cmd():
    task_id = ask_int("номер задачи в очередь: ")
    if store.get_by_id(task_id) is None:
        print("задачи с таким номером нет")
        return
    queue.enqueue(task_id)
    print("задача #%d поставлена в очередь" % task_id)


def dequeue_cmd():
    task_id = queue.dequeue()
    if task_id is None:
        print("очередь пуста")
        return
    task = store.get_by_id(task_id)
    if task is None:
        print("задача #%d уже удалена" % task_id)
    else:
        print("следующая на исполнение:", task)


def show_by_deadline_cmd():
    show_tasks(bst.in_order())


def earliest_cmd():
    task = bst.find_min()
    print("самый ранний дедлайн:", task if task else "задач нет")


def latest_cmd():
    task = bst.find_max()
    print("самый поздний дедлайн:", task if task else "задач нет")


def undo_cmd():
    print(undo.undo_last())


# --- фильтрация ---

def build_conditions():
    # спрашиваем все условия, пустой ввод значит не фильтровать по полю
    print("оставляйте поле пустым, если оно не нужно")
    conditions = {}

    conditions["status"] = ask("статус (%s): " % ", ".join(ALLOWED_STATUSES)) or None
    conditions["category"] = ask("категория: ") or None
    conditions["priority_min"] = ask_int("приоритет от: ", allow_empty=True)
    conditions["priority_max"] = ask_int("приоритет до: ", allow_empty=True)
    conditions["deadline_from"] = ask_deadline("дедлайн от: ", allow_empty=True)
    conditions["deadline_to"] = ask_deadline("дедлайн до: ", allow_empty=True)
    conditions["keyword"] = ask("ключевое слово в названии: ") or None
    conditions["duration_min"] = ask_int("время от: ", allow_empty=True)
    conditions["duration_max"] = ask_int("время до: ", allow_empty=True)
    return conditions


def ask_sort():
    # спрашиваем поле и направление сортировки
    print("поля сортировки:", ", ".join(SORT_KEYS.keys()))
    field = ask("сортировать по: ")
    if field not in SORT_KEYS:
        field = "deadline"
    ascending = ask("по возрастанию? (д/н): ").lower() != "н"
    return field, ascending


def run_filter(conditions, sort_field, ascending):
    # применяем фильтр, печатаем результат и кладем снимок в историю
    found = filter_tasks(store.get_all(), conditions)
    found = sort_tasks(found, sort_field, ascending)
    show_tasks(found)
    snapshot = Snapshot(conditions, sort_field, ascending,
                        [t.id for t in found])
    history.push_new(snapshot)


def filter_cmd():
    conditions = build_conditions()
    sort_field, ascending = ask_sort()
    run_filter(conditions, sort_field, ascending)


# --- сохраненные фильтры ---

def save_current_filter():
    if history.current is None:
        print("сначала примените какой-нибудь фильтр")
        return
    name = ask("имя фильтра: ")
    if not name:
        print("имя не может быть пустым")
        return
    if saved.has(name):
        if ask("имя занято, перезаписать? (д/н): ").lower() != "д":
            return
    snap = history.current
    saved.save(name, snap.conditions, snap.sort_field, snap.ascending)
    print("фильтр сохранен как '%s'" % name)


def apply_saved_filter():
    name = ask("имя фильтра: ")
    f = saved.get(name)
    if f is None:
        print("нет фильтра с таким именем")
        return
    run_filter(f["conditions"], f["sort_field"], f["ascending"])


def rename_saved_filter():
    old_name = ask("старое имя: ")
    new_name = ask("новое имя: ")
    if saved.rename(old_name, new_name):
        print("переименовано")
    else:
        print("не получилось, проверьте имена")


def delete_saved_filter():
    name = ask("имя фильтра: ")
    if saved.delete(name):
        print("удалено")
    else:
        print("нет фильтра с таким именем")


def list_saved_filters():
    names = saved.names()
    if not names:
        print("сохраненных фильтров нет")
        return
    for name in names:
        print(" -", name)


def saved_filters_cmd():
    print("что сделать с сохраненными фильтрами:")
    print("  1 сохранить последний фильтр под именем")
    print("  2 применить сохраненный")
    print("  3 переименовать")
    print("  4 удалить")
    print("  5 показать список")
    actions = {
        "1": save_current_filter,
        "2": apply_saved_filter,
        "3": rename_saved_filter,
        "4": delete_saved_filter,
        "5": list_saved_filters,
    }
    action = actions.get(ask("выбор: "))
    if action is None:
        print("нет такого пункта")
    else:
        action()


# --- история просмотров ---

def show_snapshot(snap):
    # разворачиваем номера задач из снимка в сами задачи
    tasks = []
    for task_id in snap.task_ids:
        task = store.get_by_id(task_id)
        if task is not None:
            tasks.append(task)
    if not tasks:
        print("задачи из этого результата удалены")
        return
    show_tasks(tasks)


def history_cmd():
    print("1 назад   2 вперед")
    choice = ask("выбор: ")
    if choice == "1":
        snap = history.go_back()
    elif choice == "2":
        snap = history.go_forward()
    else:
        print("нет такого пункта")
        return
    if snap is None:
        print("листать некуда")
    else:
        show_snapshot(snap)


def save_and_exit_cmd():
    storage.save_state(STATE_PATH, store, queue, saved)
    print("состояние сохранено, до встречи")
    raise SystemExit


# --- меню ---

COMMANDS = {
    "1": ("добавить задачу", add_task_cmd),
    "2": ("удалить задачу", delete_task_cmd),
    "3": ("изменить задачу", edit_task_cmd),
    "4": ("поставить в очередь", enqueue_cmd),
    "5": ("взять из очереди", dequeue_cmd),
    "6": ("показать по дедлайну", show_by_deadline_cmd),
    "7": ("самая ранняя задача", earliest_cmd),
    "8": ("самая поздняя задача", latest_cmd),
    "9": ("отменить последнее действие", undo_cmd),
    "10": ("фильтр", filter_cmd),
    "11": ("сохраненные фильтры", saved_filters_cmd),
    "12": ("история просмотров", history_cmd),
    "0": ("сохранить и выйти", save_and_exit_cmd),
}

MENU_ORDER = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "0"]


def print_menu():
    print("\n=== управление задачами ===")
    for key in MENU_ORDER:
        print("  %s %s" % (key, COMMANDS[key][0]))


def main():
    storage.load_state(STATE_PATH, store, queue, bst, saved)
    while True:
        print_menu()
        command = COMMANDS.get(ask("команда: "))
        if command is None:
            print("нет такой команды")
            continue
        command[1]()


if __name__ == "__main__":
    main()
