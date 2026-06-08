from datetime import datetime

from task import DATE_FORMAT

# поля, по которым можно сортировать, и как достать значение из задачи
SORT_KEYS = {
    "deadline": lambda t: t.deadline,
    "priority": lambda t: t.priority,
    "duration": lambda t: t.duration,
    "title": lambda t: t.title.lower(),
}


def matches(task, c):
    # проверяем одну задачу по всем условиям, пустое условие пропускаем
    if c.get("status") and task.status != c["status"]:
        return False
    if c.get("category") and task.category != c["category"]:
        return False
    if c.get("priority_min") is not None and task.priority < c["priority_min"]:
        return False
    if c.get("priority_max") is not None and task.priority > c["priority_max"]:
        return False
    if c.get("deadline_from") is not None and task.deadline < c["deadline_from"]:
        return False
    if c.get("deadline_to") is not None and task.deadline > c["deadline_to"]:
        return False
    if c.get("keyword") and c["keyword"].lower() not in task.title.lower():
        return False
    if c.get("duration_min") is not None and task.duration < c["duration_min"]:
        return False
    if c.get("duration_max") is not None and task.duration > c["duration_max"]:
        return False
    return True


def filter_tasks(tasks, conditions):
    # оставляем задачи, которые подходят сразу под все заданные условия
    return [task for task in tasks if matches(task, conditions)]


def sort_tasks(tasks, field, ascending=True):
    # сортируем встроенной sorted по выбранному полю
    if field not in SORT_KEYS:
        return list(tasks)
    return sorted(tasks, key=SORT_KEYS[field], reverse=not ascending)


class SavedFilters:
    def __init__(self):
        self.filters = {}      # имя фильтра -> условия и параметры сортировки

    def save(self, name, conditions, sort_field, ascending):
        # запоминаем фильтр под именем, при совпадении имени перезаписываем
        self.filters[name] = {
            "conditions": conditions,
            "sort_field": sort_field,
            "ascending": ascending,
        }

    def has(self, name):
        return name in self.filters

    def get(self, name):
        return self.filters.get(name)

    def rename(self, old_name, new_name):
        # меняем имя, если старое есть, а новое еще не занято
        if old_name not in self.filters:
            return False
        if new_name in self.filters:
            return False
        self.filters[new_name] = self.filters.pop(old_name)
        return True

    def delete(self, name):
        if name in self.filters:
            del self.filters[name]
            return True
        return False

    def names(self):
        return list(self.filters.keys())

    def to_json_dict(self):
        # готовим фильтры к записи, даты превращаем в строки
        out = {}
        for name, f in self.filters.items():
            conditions = dict(f["conditions"])
            for key in ("deadline_from", "deadline_to"):
                if conditions.get(key) is not None:
                    conditions[key] = conditions[key].strftime(DATE_FORMAT)
            out[name] = {
                "conditions": conditions,
                "sort_field": f["sort_field"],
                "ascending": f["ascending"],
            }
        return out

    def load_json_dict(self, data):
        # читаем фильтры из файла, строки с датами разбираем обратно
        self.filters = {}
        for name, f in data.items():
            conditions = dict(f["conditions"])
            for key in ("deadline_from", "deadline_to"):
                if conditions.get(key) is not None:
                    conditions[key] = datetime.strptime(conditions[key], DATE_FORMAT)
            self.filters[name] = {
                "conditions": conditions,
                "sort_field": f["sort_field"],
                "ascending": f["ascending"],
            }
