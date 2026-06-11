# консольный менеджер задач, ввод команд и главный цикл

from manager import TaskManager, format_task, valid_date, STATUSES, EDITABLE
from manager import TaskManager, format_task, STATUSES, EDITABLE
from filters import empty_filter, run_filter, describe, SORT_FIELDS, SavedQueries, ViewHistory


# печатает список доступных команд
def show_help():
    print("Доступные команды:")
    print("  add                     добавить задачу")
    print("  del <id>                удалить задачу")
    print("  edit <id>               изменить поле задачи")
    print("  list                    все задачи по возрастанию дедлайна")
    print("  early                   задача с самым ранним дедлайном")
    print("  late                    задача с самым поздним дедлайном")
    print("  enqueue <id>            поставить задачу в очередь на исполнение")
    print("  next                    исполнить следующую задачу из очереди")
    print("  queue                   показать очередь на исполнение")
    print("  undo                    отменить последнее действие")
    print("  find                    найти задачи по условиям")
    print("  save <имя>              сохранить последний фильтр под именем")
    print("  run <имя>               выполнить сохраненный фильтр")
    print("  saved                   список сохраненных фильтров")
    print("  rename <старое> <новое> переименовать сохраненный фильтр")
    print("  drop <имя>              удалить сохраненный фильтр")
    print("  back                    предыдущий результат поиска")
    print("  forward                 следующий результат поиска")
    print("  help                    показать команды")
    print("  quit                    выход")


# выводит список задач или сообщение, что задач нет
def print_tasks(tasks):
    if not tasks:
        print("Задач нет.")
        return
    for task in tasks:
        print("  " + format_task(task))


# спрашивает целое число в диапазоне, повторяет вопрос при ошибке
def ask_int(prompt, low, high):
    while True:
        text = input(prompt).strip()
        if text.isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"Нужно целое число от {low} до {high}.")


# спрашивает необязательное целое число, пустой ответ дает None
def ask_opt_int(prompt):
    while True:
        text = input(prompt).strip()
        if text == "":
            return None
        if text.lstrip("-").isdigit():
            return int(text)
        print("Нужно целое число или пустой ответ.")


# спрашивает статус из трех допустимых, пустой ответ дает новая
def ask_status():
    while True:
        text = input("Статус, варианты новая, в работе, выполнена (пусто = новая): ").strip()
        if text == "":
            return "новая"
        if text in STATUSES:
            return text
        print("Такого статуса нет.")

# спрашивает дату, повторяет вопрос пока формат неверный
def ask_date(prompt):
    while True:
        text = input(prompt).strip()
        if valid_date(text):
            return text
        print("Дата должна быть в формате ГГГГ-ММ-ДД, например 2026-06-15.")

# спрашивает поля новой задачи и добавляет ее
def add_dialog(tm):
    name = input("Название: ").strip()
    if not name:
        print("Название не может быть пустым.")
        return
    priority = ask_int("Приоритет от 1 до 5: ", 1, 5)
    time = ask_int("Время выполнения в минутах: ", 0, 100000)
    deadline = ask_date("Дедлайн (ГГГГ-ММ-ДД): ")
    status = ask_status()
    category = input("Категория (пусто = прочее): ").strip()
    try:
        task = tm.add(name, priority, time, deadline, status, category)
        print(f"Добавлена задача #{task['id']}.")
    except ValueError as error:
        print(f"Ошибка: {error}.")


# переводит строку в значение нужного типа для поля задачи
def convert_value(field, raw):
    if field in ("priority", "time"):
        if raw.lstrip("-").isdigit():
            return int(raw)
        return None
    return raw


# спрашивает поле и новое значение, меняет задачу
def edit_dialog(tm, task_id):
    if tm.by_id.get(task_id) is None:
        print("Задачи с таким номером нет.")
        return
    print("Поля: name, priority, time, deadline, status, category")
    field = input("Какое поле менять: ").strip()
    if field not in EDITABLE:
        print("Такого поля нет.")
        return
    raw = input("Новое значение: ").strip()
    value = convert_value(field, raw)
    if value is None:
        print("Значение не подходит для этого поля.")
        return
    try:
        tm.edit(task_id, field, value)
        print(f"Задача #{task_id} изменена.")
    except ValueError as error:
        print(f"Ошибка: {error}.")


# спрашивает поле и порядок сортировки результата
def ask_sort():
    print("Поля сортировки: deadline, priority, time, name")
    field = input("Сортировать по (пусто = deadline): ").strip()
    if field not in SORT_FIELDS:
        field = "deadline"
    order = input("Порядок: 1 по возрастанию, 2 по убыванию (пусто = 1): ").strip()
    return field, order != "2"


# выводит результат фильтрации и кладет его в историю просмотров
def show_result(found, label, history):
    history.add({"label": label, "ids": [task["id"] for task in found]})
    print(f"Фильтр: {label}")
    print(f"Найдено задач: {len(found)}")
    print_tasks(found)


# спрашивает условия фильтра, выполняет его и запоминает как последний
def find_dialog(tm, history, last):
    f = empty_filter()
    print("Пустой ответ значит, что условие не используется.")
    status = input("Статус: ").strip()
    if status:
        f["status"] = status
    category = input("Категория: ").strip()
    if category:
        f["category"] = category
    f["priority_from"] = ask_opt_int("Приоритет от: ")
    f["priority_to"] = ask_opt_int("Приоритет до: ")
    deadline_from = input("Дедлайн от (ГГГГ-ММ-ДД): ").strip()
    if deadline_from:
        f["deadline_from"] = deadline_from
    deadline_to = input("Дедлайн до (ГГГГ-ММ-ДД): ").strip()
    if deadline_to:
        f["deadline_to"] = deadline_to
    keyword = input("Ключевое слово в названии: ").strip()
    if keyword:
        f["keyword"] = keyword
    f["time_from"] = ask_opt_int("Время выполнения от: ")
    f["time_to"] = ask_opt_int("Время выполнения до: ")

    sort_field, ascending = ask_sort()
    found = run_filter(tm.tasks, f, sort_field, ascending)
    label = describe(f, sort_field, ascending)
    last["filter"] = dict(f)
    last["sort_field"] = sort_field
    last["ascending"] = ascending
    show_result(found, label, history)


# показывает сохраненный результат фильтрации по его номерам задач
def show_view(tm, view):
    print(f"Фильтр: {view['label']}")
    tasks = []
    for i in view["ids"]:
        if i in tm.by_id:
            tasks.append(tm.by_id[i])
    print(f"Найдено задач: {len(tasks)}")
    print_tasks(tasks)


# добавляет несколько задач для демонстрации работы программы
def seed(tm):
    tm.add("Выполнить дз", 5, 600, "2026-06-15", "в работе", "учеба")
    tm.add("Купить продукты", 2, 40, "2026-06-11", "новая", "дом")
    tm.add("Подготовить презентацию", 4, 120, "2026-06-13", "новая", "учеба")
    tm.add("Тренировка в зале", 1, 90, "2026-06-12", "новая", "спорт")
    tm.add("Ответить на письма", 3, 30, "2026-06-11", "выполнена", "работа")
    tm.add("Сдать отчет по практике", 5, 180, "2026-06-14", "в работе", "учеба")
    # демонстрационные задачи не считаем действиями пользователя
    tm.undo_stack.items = []


# предлагает загрузить демонстрационные задачи при старте
def maybe_seed(tm):
    answer = input("Загрузить демонстрационные задачи? (д/н): ").strip().lower()
    if answer == "д":
        seed(tm)
        print(f"Добавлено демонстрационных задач: {len(tm.tasks)}.")


# достает номер задачи из остатка команды, иначе None
def parse_id(rest):
    if rest.isdigit():
        return int(rest)
    return None


# обрабатывает команды, которые работают с задачами и очередью
def handle_task_command(tm, word, rest):
    if word == "add":
        add_dialog(tm)
        return True
    if word == "del":
        task_id = parse_id(rest)
        if task_id is None:
            print("Укажите номер задачи, например: del 3.")
        elif tm.delete(task_id) is None:
            print("Задачи с таким номером нет.")
        else:
            print(f"Задача #{task_id} удалена.")
        return True
    if word == "edit":
        task_id = parse_id(rest)
        if task_id is None:
            print("Укажите номер задачи, например: edit 3.")
        else:
            edit_dialog(tm, task_id)
        return True
    if word == "list":
        print("Задачи по возрастанию дедлайна:")
        print_tasks(tm.ordered())
        return True
    if word == "early":
        tasks = tm.earliest()
        if not tasks:
            print("Задач нет.")
        else:
            print("Самый ранний дедлайн:")
            print_tasks(tasks)
        return True
    if word == "late":
        tasks = tm.latest()
        if not tasks:
            print("Задач нет.")
        else:
            print("Самый поздний дедлайн:")
            print_tasks(tasks)
        return True
    if word == "enqueue":
        task_id = parse_id(rest)
        if task_id is None:
            print("Укажите номер задачи, например: enqueue 3.")
        elif tm.enqueue(task_id) is None:
            print("Задачи с таким номером нет.")
        else:
            print(f"Задача #{task_id} поставлена в очередь.")
        return True
    if word == "next":
        task = tm.run_next()
        if task is None:
            print("Очередь пуста.")
        else:
            print(f"Исполнена задача #{task['id']}: {task['name']}. Статус выполнена.")
        return True
    if word == "queue":
        ids = tm.queue.to_list()
        if not ids:
            print("Очередь пуста.")
        else:
            print("Очередь на исполнение:")
            print_tasks([tm.by_id[i] for i in ids if i in tm.by_id])
        return True
    if word == "undo":
        print(tm.undo())
        return True
    return False


# обрабатывает команды поиска, сохраненных фильтров и истории
def handle_query_command(tm, word, rest, saved, history, last):
    if word == "find":
        find_dialog(tm, history, last)
        return True
    if word == "save":
        if not rest:
            print("Укажите имя фильтра, например: save срочное.")
        elif last["filter"] is None:
            print("Сначала выполните find.")
        else:
            saved.save(rest, last["filter"], last["sort_field"], last["ascending"])
            print(f"Фильтр сохранен под именем {rest}.")
        return True
    if word == "run":
        item = saved.get(rest)
        if item is None:
            print("Такого фильтра нет.")
        else:
            found = run_filter(tm.tasks, item["filter"], item["sort_field"], item["ascending"])
            label = describe(item["filter"], item["sort_field"], item["ascending"])
            last["filter"] = dict(item["filter"])
            last["sort_field"] = item["sort_field"]
            last["ascending"] = item["ascending"]
            show_result(found, label, history)
        return True
    if word == "saved":
        names = saved.names()
        if not names:
            print("Сохраненных фильтров нет.")
        else:
            print("Сохраненные фильтры:")
            for name in names:
                item = saved.get(name)
                print(f"  {name} - {describe(item['filter'], item['sort_field'], item['ascending'])}")
        return True
    if word == "rename":
        pair = rest.split()
        if len(pair) != 2:
            print("Нужно старое и новое имя, например: rename срочное важное.")
        elif saved.rename(pair[0], pair[1]):
            print(f"Фильтр {pair[0]} теперь называется {pair[1]}.")
        else:
            print("Переименовать не вышло, проверьте имена.")
        return True
    if word == "drop":
        if saved.delete(rest):
            print(f"Фильтр {rest} удален.")
        else:
            print("Такого фильтра нет.")
        return True
    if word == "back":
        view = history.go_back()
        if view is None:
            print("Назад нельзя, это первый результат.")
        else:
            show_view(tm, view)
        return True
    if word == "forward":
        view = history.go_forward()
        if view is None:
            print("Вперед нельзя, это последний результат.")
        else:
            show_view(tm, view)
        return True
    return False


# главный цикл программы
def main():
    print("        МЕНЕДЖЕР ЗАДАЧ")
    tm = TaskManager()
    saved = SavedQueries()
    history = ViewHistory()
    last = {"filter": None, "sort_field": "deadline", "ascending": True}

    maybe_seed(tm)
    show_help()

    while True:
        line = input("\n> ").strip()
        if not line:
            continue
        parts = line.split()
        word = parts[0].lower()
        rest = line[len(parts[0]):].strip()   # все после первого слова, регистр сохранен

        if word == "quit":
            print("Выход.")
            break
        if word == "help":
            show_help()
            continue
        if handle_task_command(tm, word, rest):
            continue
        if handle_query_command(tm, word, rest, saved, history, last):
            continue

        print("Неизвестная команда. Введите help для списка команд.")


if __name__ == "__main__":
    main()
