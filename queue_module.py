from collections import deque


class TaskQueue:
    def __init__(self):
        self.items = deque()       # хранит номера задач

    def enqueue(self, task_id):
        self.items.append(task_id)

    def dequeue(self):
        # берем номер задачи из начала очереди
        if not self.items:
            return None
        return self.items.popleft()

    def peek(self):
        if not self.items:
            return None
        return self.items[0]

    def is_empty(self):
        return len(self.items) == 0

    def remove(self, task_id):
        # убираем задачу из очереди, если она там есть
        if task_id in self.items:
            self.items.remove(task_id)

    def to_list(self):
        return list(self.items)
