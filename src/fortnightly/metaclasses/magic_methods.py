from copy import copy


class Vector:
    def __init__(self, dim: int) -> None:
        self._data: tuple[float, ...] = tuple([0] * dim)

    @property
    def dim(self) -> int:
        return len(self._data)

    def set(self, data: tuple[float, ...]) -> None:
        if len(data) != self.dim:
            raise ValueError("Data length must match vector dimension")
        self._data = copy(data)

    def __add__(self, other: "Vector") -> "Vector":
        if not isinstance(other, Vector):
            return NotImplemented
        if self.dim != other.dim:
            raise ValueError("Vectors must have the same dimension")
        result = Vector(self.dim)
        result.set(tuple(a + b for a, b in zip(self._data, other._data)))
        return result

    def __str__(self) -> str:
        return f"({', '.join(map(str, self._data))})"


vector1 = Vector(3)
vector2 = Vector(3)
vector1.set((1, 2, 3))
vector2.set((4, 5, 6))
result_vector = vector1 + vector2
print(result_vector)  # Output: (5, 7, 9)
