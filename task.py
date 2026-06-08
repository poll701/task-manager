from datetime import datetime

# единый формат даты по всему проекту
DATE_FORMAT = "%Y-%m-%d %H:%M"

# допустимые статусы задачи
ALLOWED_STATUSES = ("новая", "в работе", "выполнена")


class Task:
    def __init__(self, task_id, title, priority, duration, deadline,
                 status="новая", category="прочее"):
        title = title.strip()
        if not title:
            raise ValueError("название не может быть пустым")
        if len(title) > 200:
            raise ValueError("название не длиннее 200 символов")
        if not 1 <= priority <= 5:
            raise ValueError("приоритет должен быть от 1 до 5")
        if duration < 0:
            raise ValueError("время выполнения не может быть отрицательным")
        if status not in ALLOWED_STATUSES:
            raise ValueError("недопустимый статус")

        self.id = task_id
        self.title = title
        self.priority = priority
        self.duration = duration       # в минутах
        self.deadline = deadline       # объект datetime
        self.status = status
        self.category = category

    def to_dict(self):
        # превращаем задачу в словарь, чтобы записать в json
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "duration": self.duration,
            "deadline": self.deadline.strftime(DATE_FORMAT),
            "status": self.status,
            "category": self.category,
        }

    @staticmethod
    def from_dict(data):
        # собираем задачу обратно из словаря
        deadline = datetime.strptime(data["deadline"], DATE_FORMAT)
        return Task(
            data["id"], data["title"], data["priority"], data["duration"],
            deadline, data["status"], data["category"],
        )

    def __repr__(self):
        d = self.deadline.strftime(DATE_FORMAT)
        return ("#%d %s | приоритет %d | %d мин | до %s | %s | %s"
                % (self.id, self.title, self.priority, self.duration,
                   d, self.status, self.category))


class TaskStore:
    def __init__(self):
        self.tasks = []        # все задачи по порядку добавления
        self.by_id = {}        # номер задачи -> задача, для быстрого поиска
        self.next_id = 1       # какой номер выдать следующей задаче

    def add(self, task):
        # кладем готовую задачу и в список, и в словарь
        self.tasks.append(task)
        self.by_id[task.id] = task
        if task.id >= self.next_id:
            self.next_id = task.id + 1

    def create(self, title, priority, duration, deadline,
               status="новая", category="прочее"):
        # создаем новую задачу с очередным свободным номером
        task = Task(self.next_id, title, priority, duration,
                    deadline, status, category)
        self.next_id += 1
        self.add(task)
        return task

    def remove(self, task_id):
        # убираем задачу из обеих структур, возвращаем что удалили
        task = self.by_id.get(task_id)
        if task is None:
            return None
        self.tasks.remove(task)
        del self.by_id[task_id]
        return task

    def update_field(self, task_id, field, value):
        # меняем одно поле задачи
        task = self.by_id.get(task_id)
        if task is None:
            return None
        setattr(task, field, value)
        return task

    def get_by_id(self, task_id):
        return self.by_id.get(task_id)

    def get_all(self):
        # отдаем копию списка, чтобы снаружи его случайно не испортили
        return list(self.tasks)
