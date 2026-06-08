import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from task import TaskStore, DATE_FORMAT
from bst import BST
from queue_module import TaskQueue
from undo import UndoStack


def deadline(text):
    return datetime.strptime(text, DATE_FORMAT)


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.store = TaskStore()
        self.bst = BST()
        self.queue = TaskQueue()
        self.undo = UndoStack(self.store, self.bst, self.queue)

    def add_task(self):
        task = self.store.create("t", 3, 10, deadline("2026-06-15 18:00"))
        self.bst.insert(task)
        self.undo.push({"type": "add", "task_id": task.id})
        return task

    def test_undo_add(self):
        task = self.add_task()
        self.undo.undo_last()
        self.assertIsNone(self.store.get_by_id(task.id))

    def test_undo_delete(self):
        task = self.add_task()
        self.undo.push({"type": "delete", "task_data": task.to_dict()})
        self.store.remove(task.id)
        self.bst.rebuild(self.store.get_all())
        self.undo.undo_last()
        self.assertIsNotNone(self.store.get_by_id(task.id))

    def test_undo_edit(self):
        task = self.add_task()
        old = task.priority
        self.undo.push({"type": "edit", "task_id": task.id,
                        "field": "priority", "old_value": old})
        self.store.update_field(task.id, "priority", 1)
        self.undo.undo_last()
        self.assertEqual(self.store.get_by_id(task.id).priority, old)

    def test_nothing_to_undo(self):
        self.assertIn("нечего", self.undo.undo_last())


if __name__ == "__main__":
    unittest.main()
