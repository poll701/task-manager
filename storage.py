import json
import os

from task import Task


def save_state(path, store, queue, saved_filters):
    # пишем задачи, очередь и сохраненные фильтры в один json файл
    data = {
        "next_id": store.next_id,
        "tasks": [task.to_dict() for task in store.get_all()],
        "queue": queue.to_list(),
        "saved_filters": saved_filters.to_json_dict(),
    }
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state(path, store, queue, bst, saved_filters):
    # читаем состояние из файла, если файла нет, оставляем все пустым
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for task_data in data.get("tasks", []):
        store.add(Task.from_dict(task_data))
    # next_id из файла берем, если он больше посчитанного при загрузке
    saved_next = data.get("next_id", 1)
    if saved_next > store.next_id:
        store.next_id = saved_next

    for task_id in data.get("queue", []):
        queue.enqueue(task_id)

    saved_filters.load_json_dict(data.get("saved_filters", {}))
    # дерево строим заново из загруженных задач
    bst.rebuild(store.get_all())
