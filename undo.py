from task import Task


class UndoStack:
    def __init__(self, store, bst, queue):
        self.actions = []      # список выполненных действий
        self.store = store
        self.bst = bst
        self.queue = queue

    def push(self, action):
        # запоминаем выполненное действие, чтобы можно было откатить
        self.actions.append(action)

    def is_empty(self):
        return len(self.actions) == 0

    def undo_last(self):
        # откатываем последнее действие и возвращаем текст о том, что сделали
        if not self.actions:
            return "отменять нечего"

        action = self.actions.pop()
        kind = action["type"]

        if kind == "add":
            # добавление отменяем удалением задачи
            task_id = action["task_id"]
            self.store.remove(task_id)
            self.queue.remove(task_id)
            self.bst.rebuild(self.store.get_all())
            return "отменено добавление задачи #%d" % task_id

        if kind == "delete":
            # удаление отменяем восстановлением задачи из сохраненных данных
            task = Task.from_dict(action["task_data"])
            self.store.add(task)
            self.bst.rebuild(self.store.get_all())
            return "восстановлена задача #%d" % task.id

        if kind == "edit":
            # изменение отменяем возвратом старого значения поля
            task_id = action["task_id"]
            field = action["field"]
            self.store.update_field(task_id, field, action["old_value"])
            if field == "deadline":
                self.bst.rebuild(self.store.get_all())
            return "отменено изменение задачи #%d" % task_id

        return "неизвестное действие"
