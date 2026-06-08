class Node:
    def __init__(self, task):
        self.task = task
        self.left = None
        self.right = None


class BST:
    def __init__(self):
        self.root = None

    def insert(self, task):
        # добавляем задачу в дерево по ее дедлайну
        self.root = self._insert(self.root, task)

    def _insert(self, node, task):
        if node is None:
            return Node(task)
        # меньший дедлайн уходит влево, остальное вправо
        if task.deadline < node.task.deadline:
            node.left = self._insert(node.left, task)
        else:
            node.right = self._insert(node.right, task)
        return node

    def in_order(self):
        # обход слева направо дает задачи по возрастанию дедлайна
        result = []
        self._in_order(self.root, result)
        return result

    def _in_order(self, node, result):
        if node is None:
            return
        self._in_order(node.left, result)
        result.append(node.task)
        self._in_order(node.right, result)

    def find_min(self):
        # самая ранняя задача, все время идем влево
        if self.root is None:
            return None
        node = self.root
        while node.left is not None:
            node = node.left
        return node.task

    def find_max(self):
        # самая поздняя задача, все время идем вправо
        if self.root is None:
            return None
        node = self.root
        while node.right is not None:
            node = node.right
        return node.task

    def rebuild(self, tasks):
        # вместо сложного удаления узла просто строим дерево заново
        self.root = None
        for task in tasks:
            self.insert(task)
