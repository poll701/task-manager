import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from task import Task, DATE_FORMAT
from filters import filter_tasks, sort_tasks, SavedFilters


def d(text):
    return datetime.strptime(text, DATE_FORMAT)


def sample_tasks():
    return [
        Task(1, "купить молоко", 2, 15, d("2026-06-15 10:00"), "новая", "дом"),
        Task(2, "сдать отчет", 5, 120, d("2026-06-10 10:00"), "в работе", "работа"),
        Task(3, "позвонить маме", 3, 20, d("2026-06-20 10:00"), "новая", "личное"),
    ]


def empty_conditions():
    return {
        "status": None, "category": None,
        "priority_min": None, "priority_max": None,
        "deadline_from": None, "deadline_to": None,
        "keyword": None, "duration_min": None, "duration_max": None,
    }


class TestFilter(unittest.TestCase):
    def test_no_conditions_returns_all(self):
        result = filter_tasks(sample_tasks(), empty_conditions())
        self.assertEqual(len(result), 3)

    def test_by_status(self):
        c = empty_conditions()
        c["status"] = "новая"
        result = filter_tasks(sample_tasks(), c)
        self.assertEqual({t.id for t in result}, {1, 3})

    def test_by_priority_range(self):
        c = empty_conditions()
        c["priority_min"] = 3
        result = filter_tasks(sample_tasks(), c)
        self.assertEqual({t.id for t in result}, {2, 3})

    def test_by_keyword_ignores_case(self):
        c = empty_conditions()
        c["keyword"] = "МОЛОКО"
        result = filter_tasks(sample_tasks(), c)
        self.assertEqual({t.id for t in result}, {1})

    def test_by_deadline_range(self):
        c = empty_conditions()
        c["deadline_to"] = d("2026-06-16 00:00")
        result = filter_tasks(sample_tasks(), c)
        self.assertEqual({t.id for t in result}, {1, 2})

    def test_two_conditions_together(self):
        c = empty_conditions()
        c["status"] = "новая"
        c["priority_min"] = 3
        result = filter_tasks(sample_tasks(), c)
        self.assertEqual({t.id for t in result}, {3})


class TestSort(unittest.TestCase):
    def test_sort_by_priority_asc(self):
        order = [t.id for t in sort_tasks(sample_tasks(), "priority", True)]
        self.assertEqual(order, [1, 3, 2])

    def test_sort_by_priority_desc(self):
        order = [t.id for t in sort_tasks(sample_tasks(), "priority", False)]
        self.assertEqual(order, [2, 3, 1])

    def test_sort_by_deadline(self):
        order = [t.id for t in sort_tasks(sample_tasks(), "deadline", True)]
        self.assertEqual(order, [2, 1, 3])


class TestSavedFilters(unittest.TestCase):
    def setUp(self):
        self.saved = SavedFilters()

    def test_save_and_get(self):
        self.saved.save("срочные", empty_conditions(), "priority", False)
        self.assertTrue(self.saved.has("срочные"))
        self.assertEqual(self.saved.get("срочные")["sort_field"], "priority")

    def test_rename(self):
        self.saved.save("a", empty_conditions(), "deadline", True)
        self.assertTrue(self.saved.rename("a", "b"))
        self.assertFalse(self.saved.has("a"))
        self.assertTrue(self.saved.has("b"))

    def test_rename_to_busy_name_fails(self):
        self.saved.save("a", empty_conditions(), "deadline", True)
        self.saved.save("b", empty_conditions(), "deadline", True)
        self.assertFalse(self.saved.rename("a", "b"))

    def test_delete(self):
        self.saved.save("a", empty_conditions(), "deadline", True)
        self.assertTrue(self.saved.delete("a"))
        self.assertFalse(self.saved.has("a"))

    def test_json_round_trip(self):
        c = empty_conditions()
        c["deadline_from"] = d("2026-06-01 00:00")
        self.saved.save("f", c, "deadline", True)

        fresh = SavedFilters()
        fresh.load_json_dict(self.saved.to_json_dict())
        restored = fresh.get("f")["conditions"]["deadline_from"]
        self.assertEqual(restored, d("2026-06-01 00:00"))


if __name__ == "__main__":
    unittest.main()
