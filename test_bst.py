import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from task import Task, DATE_FORMAT
from bst import BST


def task_with(id_, deadline_text):
    d = datetime.strptime(deadline_text, DATE_FORMAT)
    return Task(id_, "t%d" % id_, 1, 10, d)


class TestBST(unittest.TestCase):
    def setUp(self):
        self.bst = BST()
        # вставляем в перемешанном порядке
        self.bst.insert(task_with(1, "2026-06-15 10:00"))
        self.bst.insert(task_with(2, "2026-06-10 10:00"))
        self.bst.insert(task_with(3, "2026-06-20 10:00"))
        self.bst.insert(task_with(4, "2026-06-12 10:00"))

    def test_in_order_sorted(self):
        order = [t.id for t in self.bst.in_order()]
        self.assertEqual(order, [2, 4, 1, 3])

    def test_find_min(self):
        self.assertEqual(self.bst.find_min().id, 2)

    def test_find_max(self):
        self.assertEqual(self.bst.find_max().id, 3)

    def test_rebuild(self):
        self.bst.rebuild([task_with(5, "2026-01-01 00:00")])
        self.assertEqual(self.bst.find_min().id, 5)
        self.assertEqual(self.bst.find_max().id, 5)

    def test_empty(self):
        empty = BST()
        self.assertIsNone(empty.find_min())
        self.assertIsNone(empty.find_max())
        self.assertEqual(empty.in_order(), [])


if __name__ == "__main__":
    unittest.main()
