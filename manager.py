# менеджер задач, добавление, удаление, изменение, отмена и очередь
# логика собрана в классе TaskManager, который держит все структуры данных

from structures import Stack, Queue, BST

# допустимые статусы задачи
STATUSES = ("новая", "в работе", "выполнена")

# поля задачи, которые разрешено менять
EDITABLE = ("name", "priority", "time", "deadline", "status", "category")


# проверяет, что строка это дата вида ГГГГ-ММ-ДД с ведущими нулями
def valid_date(text):
    parts = text.split("-")
    if len(parts) != 3:
        return False
    year, month, day = parts
    if not (len(year) == 4 and len(month) == 2 and len(day) == 2):
        return False
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return False
    return 1 <= int(month) <= 12 and 1 <= int(day) <= 31


# собирает словарь задачи с проверкой всех полей, при ошибке кидает ValueError
def build_task(task_id, name, priority, time, deadline, status, category):
    name = name.strip()
    if not name:
        raise ValueError("название не может быть пустым")
    if not 1 <= priority <= 5:
        raise ValueError("приоритет должен быть от 1 до 5")
    if time < 0:
        raise ValueError("время выполнения не может быть отрицательным")
    if not valid_date(deadline):
        raise ValueError("дедлайн должен быть в формате ГГГГ-ММ-ДД")
    if status not in STATUSES:
        raise ValueError("статус может быть новая, в работе или выполнена")
    return {
        "id": task_id,
        "name": name,
        "priority": priority,
        "time": time,                 # в минутах
        "deadline": deadline,         # строка ГГГГ-ММ-ДД, такие строки сравниваются по дате
        "status": status,
        "category": category.strip() or "прочее",
    }


# короткая строка с данными задачи для вывода на экран
def format_task(task):
    return (f"#{task['id']} {task['name']} | приоритет {task['priority']} | "
            f"{task['time']} мин | дедлайн {task['deadline']} | "
            f"{task['status']} | {task['category']}")


# хранит список задач и все структуры данных, умеет менять задачи и откатывать действия
class TaskManager:

    def __init__(self):
        self.tasks = []            # все задачи по порядку добавления
        self.by_id = {}            # номер задачи -> задача, для быстрого поиска
        self.next_id = 1           # номер, который выдадим следующей новой задаче
        self.tree = BST()          # дерево задач по дедлайну
        self.queue = Queue()       # очередь задач на исполнение
        self.undo_stack = Stack()  # стек отмены последних действий

    # перестраивает дерево по текущему списку задач
    def refresh_tree(self):
        self.tree.rebuild(self.tasks)

    # создает задачу, кладет ее в список и дерево, запоминает действие для отмены
    def add(self, name, priority, time, deadline, status, category):
        task = build_task(self.next_id, name, priority, time, deadline, status, category)
        self.next_id += 1
        self.tasks.append(task)
        self.by_id[task["id"]] = task
        self.refresh_tree()
        self.undo_stack.push({"type": "add", "id": task["id"]})
        return task

    # удаляет задачу, убирает ее из очереди и дерева, запоминает для отмены
    def delete(self, task_id):
        task = self.by_id.get(task_id)
        if task is None:
            return None
        self.tasks.remove(task)
        del self.by_id[task_id]
        self.queue.remove(task_id)
        self.refresh_tree()
        # храним копию, чтобы при отмене вернуть задачу как была
        self.undo_stack.push({"type": "delete", "task": dict(task)})
        return task

    # меняет одно поле задачи, запоминает старое значение для отмены
    def edit(self, task_id, field, value):
        task = self.by_id.get(task_id)
        if task is None:
            return None
        if field not in EDITABLE:
            raise ValueError("такое поле менять нельзя")
        # пересобираем задачу через проверку, чтобы новое значение точно было корректным
        updated = dict(task)
        updated[field] = value
        checked = build_task(task["id"], updated["name"], updated["priority"],
                             updated["time"], updated["deadline"],
                             updated["status"], updated["category"])
        old = task[field]
        task[field] = checked[field]
        self.refresh_tree()
        self.undo_stack.push({"type": "edit", "id": task_id, "field": field, "old": old})
        return task

    # откатывает последнее действие, возвращает текст о результате
    def undo(self):
        action = self.undo_stack.pop()
        if action is None:
            return "отменять нечего"
        if action["type"] == "add":
            # добавление отменяем удалением задачи
            task_id = action["id"]
            task = self.by_id.get(task_id)
            if task is not None:
                self.tasks.remove(task)
                del self.by_id[task_id]
                self.queue.remove(task_id)
            self.refresh_tree()
            return f"отменено добавление задачи #{task_id}"
        if action["type"] == "delete":
            # удаление отменяем возвратом сохраненной задачи
            task = action["task"]
            self.tasks.append(task)
            self.by_id[task["id"]] = task
            self.refresh_tree()
            return f"восстановлена задача #{task['id']}"
        if action["type"] == "edit":
            # изменение отменяем возвратом старого значения поля
            task = self.by_id.get(action["id"])
            if task is not None:
                task[action["field"]] = action["old"]
                self.refresh_tree()
            return f"отменено изменение задачи #{action['id']}"
        return "неизвестное действие"

    # ставит задачу в очередь на исполнение
    def enqueue(self, task_id):
        task = self.by_id.get(task_id)
        if task is None:
            return None
        self.queue.enqueue(task_id)
        return task

    # берет задачу из начала очереди и отмечает ее выполненной
    def run_next(self):
        task_id = self.queue.dequeue()
        if task_id is None:
            return None
        task = self.by_id.get(task_id)
        if task is not None:
            task["status"] = "выполнена"
        return task

    # задачи по возрастанию дедлайна из дерева
    def ordered(self):
        return self.tree.in_order()

    # задачи с самым ранним дедлайном
    def earliest(self):
        return self.tree.earliest()

    # задачи с самым поздним дедлайном
    def latest(self):
        return self.tree.latest()
