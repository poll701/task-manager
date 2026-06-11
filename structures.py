# базовые структуры данных для менеджера задач


# стек на списке, нужен для отмены действий и для истории просмотров
class Stack:

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    # снимаем верхний элемент, при пустом стеке отдаем None
    def pop(self):
        if self.items:
            return self.items.pop()
        return None

    def is_empty(self):
        return len(self.items) == 0


# очередь задач на исполнение, хранит номера задач
class Queue:

    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    # берем элемент из начала очереди, при пустой очереди отдаем None
    def dequeue(self):
        if self.items:
            return self.items.pop(0)
        return None

    # убираем номер задачи из очереди, например когда задачу удалили
    def remove(self, item):
        if item in self.items:
            self.items.remove(item)

    def is_empty(self):
        return len(self.items) == 0

    def to_list(self):
        return list(self.items)


# узел дерева, ключ это дедлайн, в списке лежат все задачи с этим дедлайном
class Node:

    def __init__(self, key):
        self.key = key
        self.tasks = []
        self.left = None
        self.right = None


# бинарное дерево поиска задач по дедлайну
class BST:

    def __init__(self):
        self.root = None

    # добавляет задачу в дерево по ее дедлайну
    def insert(self, task):
        self.root = self._insert(self.root, task)

    def _insert(self, node, task):
        if node is None:
            node = Node(task["deadline"])
            node.tasks.append(task)
            return node
        if task["deadline"] < node.key:
            node.left = self._insert(node.left, task)
        elif task["deadline"] > node.key:
            node.right = self._insert(node.right, task)
        else:
            # тот же дедлайн, кладем задачу в этот же узел
            node.tasks.append(task)
        return node

    # строит дерево заново из списка задач, это проще удаления узлов по одному
    def rebuild(self, tasks):
        self.root = None
        for task in tasks:
            self.insert(task)

    # симметричный обход дает задачи по возрастанию дедлайна
    def in_order(self):
        result = []
        self._in_order(self.root, result)
        return result

    def _in_order(self, node, result):
        if node is not None:
            self._in_order(node.left, result)
            for task in node.tasks:
                result.append(task)
            self._in_order(node.right, result)

    # задачи с самым ранним дедлайном, для этого все время идем влево
    def earliest(self):
        if self.root is None:
            return []
        node = self.root
        while node.left is not None:
            node = node.left
        return list(node.tasks)

    # задачи с самым поздним дедлайном, для этого все время идем вправо
    def latest(self):
        if self.root is None:
            return []
        node = self.root
        while node.right is not None:
            node = node.right
        return list(node.tasks)
