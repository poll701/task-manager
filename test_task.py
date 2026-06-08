import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from task import Task, TaskStore, DATE_FORMAT


def deadline(text):
    return datetime.strptime(text, DATE_FORMAT)


class TestTask(unittest.TestCase):
    def test_create_valid(self):
        t = Task(1, "купить хлеб", 3, 15, deadline("2026-06-15 18:00"))
        self.assertEqual(t.id, 1)
        self.assertEqual(t.priority, 3)

    def test_empty_title(self):
        with self.assertRaises(ValueError):
            Task(1, "   ", 3, 15, deadline("2026-06-15 18:00"))

    def test_bad_priority(self):
        with self.assertRaises(ValueError):
            Task(1, "тест", 9, 15, deadline("2026-06-15 18:00"))

    def test_negative_duration(self):
        with self.assertRaises(ValueError):
            Task(1, "тест", 3, -5, deadline("2026-06-15 18:00"))

    def test_to_dict_and_back(self):
        t = Task(5, "тест", 2, 30, deadline("2026-01-01 09:00"),
                 "в работе", "учеба")
        copy = Task.from_dict(t.to_dict())
        self.assertEqual(copy.id, 5)
        self.assertEqual(copy.status, "в работе")
        self.assertEqual(copy.deadline, t.deadline)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = TaskStore()

    def test_create_assigns_ids(self):
        a = self.store.create("a", 1, 10, deadline("2026-06-15 18:00"))
        b = self.store.create("b", 1, 10, deadline("2026-06-16 18:00"))
        self.assertEqual(a.id, 1)
        self.assertEqual(b.id, 2)

    def test_get_by_id(self):
        self.store.create("a", 1, 10, deadline("2026-06-15 18:00"))
        self.assertIsNotNone(self.store.get_by_id(1))
        self.assertIsNone(self.store.get_by_id(99))

    def test_remove(self):
        self.store.create("a", 1, 10, deadline("2026-06-15 18:00"))
        self.store.remove(1)
        self.assertIsNone(self.store.get_by_id(1))
        self.assertEqual(len(self.store.get_all()), 0)


if __name__ == "__main__":
    unittest.main()
