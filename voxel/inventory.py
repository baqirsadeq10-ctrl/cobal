from dataclasses import dataclass
from typing import List

from voxel.constants import HOTBAR_BLOCKS


@dataclass
class Hotbar:
    slots: List[int] = None
    selected_index: int = 0

    def __post_init__(self) -> None:
        if self.slots is None:
            self.slots = list(HOTBAR_BLOCKS)

    @property
    def selected_block(self) -> int:
        return self.slots[self.selected_index]

    def select(self, index: int) -> None:
        if 0 <= index < len(self.slots):
            self.selected_index = index
