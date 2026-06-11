# поиск задач по условиям, сортировка, именованные фильтры и история просмотров

from structures import Stack

# поля, по которым можно сортировать результат, и как достать значение из задачи
SORT_FIELDS = {
    "deadline": lambda t: t["deadline"],
    "priority": lambda t: t["priority"],
    "time": lambda t: t["time"],
    "name": lambda t: t["name"].lower(),
}


# набор условий, где ни одно поле еще не задано
def empty_filter():
    return {
        "status": None,
        "category": None,
        "priority_from": None,
        "priority_to": None,
        "deadline_from": None,
        "deadline_to": None,
        "keyword": None,
        "time_from": None,
        "time_to": None,
    }


# проверяет задачу по всем заданным условиям, пустые условия пропускаем
def matches(task, f):
    if f["status"] is not None and task["status"] != f["status"]:
        return False
    if f["category"] is not None and task["category"] != f["category"]:
        return False
    if f["priority_from"] is not None and task["priority"] < f["priority_from"]:
        return False
    if f["priority_to"] is not None and task["priority"] > f["priority_to"]:
        return False
    if f["deadline_from"] is not None and task["deadline"] < f["deadline_from"]:
        return False
    if f["deadline_to"] is not None and task["deadline"] > f["deadline_to"]:
        return False
    if f["keyword"] is not None and f["keyword"].lower() not in task["name"].lower():
        return False
    if f["time_from"] is not None and task["time"] < f["time_from"]:
        return False
    if f["time_to"] is not None and task["time"] > f["time_to"]:
        return False
    return True


# отбирает подходящие задачи и сортирует их по выбранному полю
def run_filter(tasks, f, sort_field, ascending):
    found = []
    for task in tasks:
        if matches(task, f):
            found.append(task)
    if sort_field in SORT_FIELDS:
        found = sorted(found, key=SORT_FIELDS[sort_field], reverse=not ascending)
    return found


# короткое описание фильтра для заголовка результата
def describe(f, sort_field, ascending):
    parts = []
    if f["status"] is not None:
        parts.append(f"статус {f['status']}")
    if f["category"] is not None:
        parts.append(f"категория {f['category']}")
    if f["priority_from"] is not None or f["priority_to"] is not None:
        parts.append(f"приоритет {f['priority_from']}..{f['priority_to']}")
    if f["deadline_from"] is not None or f["deadline_to"] is not None:
        parts.append(f"дедлайн {f['deadline_from']}..{f['deadline_to']}")
    if f["keyword"] is not None:
        parts.append(f"слово '{f['keyword']}'")
    if f["time_from"] is not None or f["time_to"] is not None:
        parts.append(f"время {f['time_from']}..{f['time_to']}")
    if not parts:
        parts.append("без условий")
    order = "по возрастанию" if ascending else "по убыванию"
    return ", ".join(parts) + f"; сортировка {sort_field} {order}"


# именованные фильтры, их можно сохранить, вызвать, переименовать и удалить
class SavedQueries:

    def __init__(self):
        self.items = {}        # имя -> условия и параметры сортировки

    # сохраняем под именем, при совпадении имени перезаписываем
    def save(self, name, f, sort_field, ascending):
        self.items[name] = {
            "filter": dict(f),
            "sort_field": sort_field,
            "ascending": ascending,
        }

    def get(self, name):
        return self.items.get(name)

    # переименовываем, если старое имя есть, а новое еще свободно
    def rename(self, old, new):
        if old not in self.items or new in self.items:
            return False
        self.items[new] = self.items.pop(old)
        return True

    def delete(self, name):
        if name in self.items:
            del self.items[name]
            return True
        return False

    def names(self):
        return list(self.items.keys())


# история результатов фильтрации на двух стеках, листается назад и вперед
class ViewHistory:

    def __init__(self):
        self.back = Stack()        # результаты, которые смотрели раньше
        self.forward = Stack()     # результаты, куда можно шагнуть вперед
        self.current = None        # результат, показанный прямо сейчас

    # новый результат становится текущим, прошлый уходит в стек назад
    def add(self, view):
        if self.current is not None:
            self.back.push(self.current)
        self.forward = Stack()     # после нового фильтра вперед идти уже некуда
        self.current = view

    # шаг назад к прошлому результату или None, если назад нельзя
    def go_back(self):
        if self.back.is_empty():
            return None
        self.forward.push(self.current)
        self.current = self.back.pop()
        return self.current

    # шаг вперед к следующему результату или None, если вперед нельзя
    def go_forward(self):
        if self.forward.is_empty():
            return None
        self.back.push(self.current)
        self.current = self.forward.pop()
        return self.current
