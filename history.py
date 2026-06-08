# сколько результатов держим в каждом стеке
MAX_HISTORY = 20


class Snapshot:
    def __init__(self, conditions, sort_field, ascending, task_ids):
        self.conditions = conditions     # какие условия применяли
        self.sort_field = sort_field     # по какому полю сортировали
        self.ascending = ascending       # по возрастанию или нет
        self.task_ids = task_ids         # номера найденных задач по порядку


class NavigationHistory:
    def __init__(self):
        self.back_stack = []       # результаты, которые смотрели до текущего
        self.forward_stack = []    # результаты, куда можно вернуться вперед
        self.current = None        # что показано прямо сейчас

    def push_new(self, snapshot):
        # запоминаем новый результат фильтрации как текущий
        if self.current is not None:
            self.back_stack.append(self.current)
            if len(self.back_stack) > MAX_HISTORY:
                self.back_stack.pop(0)
        # после нового фильтра идти вперед уже некуда
        self.forward_stack.clear()
        self.current = snapshot

    def go_back(self):
        # возвращаем предыдущий результат или None, если назад нельзя
        if not self.back_stack:
            return None
        self.forward_stack.append(self.current)
        self.current = self.back_stack.pop()
        return self.current

    def go_forward(self):
        # возвращаем следующий результат или None, если вперед нельзя
        if not self.forward_stack:
            return None
        self.back_stack.append(self.current)
        self.current = self.forward_stack.pop()
        return self.current
