import math
import random
from typing import List


class ValueNoise2D:
    """Simple value noise for heightmap generation."""

    def __init__(self, seed: int, grid_size: int = 256) -> None:
        self.seed = seed
        self.grid_size = grid_size
        random.seed(seed)
        self.grid: List[List[float]] = [
            [random.random() for _ in range(grid_size + 1)]
            for _ in range(grid_size + 1)
        ]

    def _smoothstep(self, t: float) -> float:
        return t * t * (3 - 2 * t)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    def sample(self, x: float, z: float, scale: float = 0.05) -> float:
        x *= scale
        z *= scale
        xi = int(math.floor(x)) % self.grid_size
        zi = int(math.floor(z)) % self.grid_size
        xf = x - math.floor(x)
        zf = z - math.floor(z)
        v00 = self.grid[zi][xi]
        v10 = self.grid[zi][xi + 1]
        v01 = self.grid[zi + 1][xi]
        v11 = self.grid[zi + 1][xi + 1]
        u = self._smoothstep(xf)
        v = self._smoothstep(zf)
        x1 = self._lerp(v00, v10, u)
        x2 = self._lerp(v01, v11, u)
        return self._lerp(x1, x2, v)


class FractalNoise2D:
    def __init__(self, seed: int) -> None:
        self.base = ValueNoise2D(seed)

    def sample(self, x: float, z: float) -> float:
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        for _ in range(4):
            total += self.base.sample(x * frequency, z * frequency, scale=0.02) * amplitude
            max_value += amplitude
            amplitude *= 0.5
            frequency *= 2.0
        return total / max_value
