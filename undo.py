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
        if self.is_empty():
            return "отменять нечего"

        last_action = self.actions.pop()
        action_type = last_action["type"]

        if action_type == "add":
            # добавление отменяем удалением задачи
            task_id = last_action["task_id"]
            self.store.remove(task_id)
            self.queue.remove(task_id)
            
            self.bst.rebuild(self.store.get_all())
            return f"отменено добавление задачи #{task_id}"

        elif action_type == "delete":
            # удаление отменяем восстановлением задачи из сохраненных данных
            saved_data = last_action["task_data"]
            restored_task = Task.from_dict(saved_data)
            
            self.store.add(restored_task)
            self.bst.rebuild(self.store.get_all())
            return f"восстановлена задача #{restored_task.id}"

        elif action_type == "edit":
            # изменение отменяем возвратом старого значения поля
            task_id = last_action["task_id"]
            field_name = last_action["field"]
            old_text = last_action["old_value"]
            
            self.store.update_field(task_id, field_name, old_text)
            
            if field_name == "deadline":
                self.bst.rebuild(self.store.get_all())
                
            return f"отменено изменение задачи #{task_id}"

        else:
            return "неизвестное действие"
