"""Small reusable exponential-moving-average smoother."""


class EMA:
    def __init__(self, factor: float = 0.35, initial: float = 0.0):
        self.factor = factor
        self.value = initial
        self._initialized = False

    def update(self, new_value: float) -> float:
        if not self._initialized:
            self.value = new_value
            self._initialized = True
        else:
            self.value = self.factor * new_value + (1 - self.factor) * self.value
        return self.value

    def reset(self, value: float = 0.0):
        self.value = value
        self._initialized = False
