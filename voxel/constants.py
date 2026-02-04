from dataclasses import dataclass
from typing import Dict, Tuple

CHUNK_SIZE = 16
WORLD_HEIGHT = 64
RENDER_DISTANCE = 4
BLOCK_SIZE = 1.0
GRAVITY = -18.0
JUMP_VELOCITY = 7.5
PLAYER_HEIGHT = 1.8
PLAYER_RADIUS = 0.35
MAX_RAY_DISTANCE = 6.0
DAY_LENGTH = 120.0

Color = Tuple[float, float, float]


@dataclass(frozen=True)
class BlockType:
    block_id: int
    name: str
    color: Color
    solid: bool = True


BLOCK_TYPES: Dict[int, BlockType] = {
    0: BlockType(0, "air", (0.0, 0.0, 0.0), solid=False),
    1: BlockType(1, "grass", (0.35, 0.8, 0.3)),
    2: BlockType(2, "dirt", (0.55, 0.4, 0.2)),
    3: BlockType(3, "stone", (0.5, 0.5, 0.5)),
    4: BlockType(4, "wood", (0.6, 0.45, 0.25)),
}

HOTBAR_BLOCKS = [1, 2, 3, 4]
