import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from history import NavigationHistory, Snapshot


def snap(ids):
    return Snapshot({}, "deadline", True, ids)


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.history = NavigationHistory()

    def test_first_push_no_back(self):
        self.history.push_new(snap([1, 2]))
        self.assertIsNone(self.history.go_back())

    def test_back_and_forward(self):
        self.history.push_new(snap([1]))
        self.history.push_new(snap([2]))
        back = self.history.go_back()
        self.assertEqual(back.task_ids, [1])
        forward = self.history.go_forward()
        self.assertEqual(forward.task_ids, [2])

    def test_new_filter_clears_forward(self):
        self.history.push_new(snap([1]))
        self.history.push_new(snap([2]))
        self.history.go_back()             # вернулись на [1], вперед ведет [2]
        self.history.push_new(snap([3]))   # новый фильтр должен стереть вперед
        self.assertIsNone(self.history.go_forward())

    def test_forward_empty_at_start(self):
        self.history.push_new(snap([1]))
        self.assertIsNone(self.history.go_forward())


if __name__ == "__main__":
    unittest.main()
