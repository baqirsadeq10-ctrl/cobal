from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from voxel.chunk import Chunk
from voxel.constants import CHUNK_SIZE, WORLD_HEIGHT
from voxel.noise import FractalNoise2D
from voxel.storage import WorldStorage

Vec3 = Tuple[int, int, int]


@dataclass
class World:
    seed: int
    storage: WorldStorage
    noise: FractalNoise2D = field(init=False)
    chunks: Dict[Tuple[int, int], Chunk] = field(default_factory=dict)
    modified_blocks: Dict[Vec3, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.noise = FractalNoise2D(self.seed)
        data = self.storage.load()
        if data:
            self.seed = data["seed"]
            self.noise = FractalNoise2D(self.seed)
            self.modified_blocks = {tuple(map(int, k.split(","))): v for k, v in data["blocks"].items()}

    def save(self) -> None:
        blocks = {f"{x},{y},{z}": block for (x, y, z), block in self.modified_blocks.items()}
        self.storage.save({"seed": self.seed, "blocks": blocks})

    def chunk_coords(self, x: int, z: int) -> Tuple[int, int]:
        return (x // CHUNK_SIZE, z // CHUNK_SIZE)

    def get_chunk(self, chunk_x: int, chunk_z: int) -> Chunk:
        chunk = self.chunks.get((chunk_x, chunk_z))
        if chunk is None:
            chunk = self.generate_chunk(chunk_x, chunk_z)
            self.chunks[(chunk_x, chunk_z)] = chunk
        return chunk

    def generate_chunk(self, chunk_x: int, chunk_z: int) -> Chunk:
        blocks: Dict[Vec3, int] = {}
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                world_x = chunk_x * CHUNK_SIZE + x
                world_z = chunk_z * CHUNK_SIZE + z
                height = int(self.noise.sample(world_x, world_z) * 24 + 24)
                height = max(1, min(height, WORLD_HEIGHT - 1))
                for y in range(height):
                    if y == height - 1:
                        block = 1
                    elif y >= height - 4:
                        block = 2
                    else:
                        block = 3
                    blocks[(x, y, z)] = block
        chunk = Chunk(chunk_x, chunk_z, blocks)
        for (bx, by, bz), block in self.modified_blocks.items():
            if self.chunk_coords(bx, bz) == (chunk_x, chunk_z):
                chunk.set_block(bx - chunk_x * CHUNK_SIZE, by, bz - chunk_z * CHUNK_SIZE, block)
        return chunk

    def get_height(self, x: int, z: int) -> int:
        height = int(self.noise.sample(x, z) * 24 + 24)
        return max(1, min(height, WORLD_HEIGHT - 1))

    def get_spawn_position(self) -> Tuple[float, float, float]:
        height = self.get_height(0, 0)
        return (0.5, height + 2.0, 0.5)

    def get_block(self, x: int, y: int, z: int) -> int:
        if y < 0 or y >= WORLD_HEIGHT:
            return 0
        chunk_x, chunk_z = self.chunk_coords(x, z)
        chunk = self.get_chunk(chunk_x, chunk_z)
        local_x = x - chunk_x * CHUNK_SIZE
        local_z = z - chunk_z * CHUNK_SIZE
        return chunk.get_block(local_x, y, local_z)

    def set_block(self, x: int, y: int, z: int, block_id: int) -> None:
        if y < 0 or y >= WORLD_HEIGHT:
            return
        chunk_x, chunk_z = self.chunk_coords(x, z)
        chunk = self.get_chunk(chunk_x, chunk_z)
        local_x = x - chunk_x * CHUNK_SIZE
        local_z = z - chunk_z * CHUNK_SIZE
        chunk.set_block(local_x, y, local_z, block_id)
        self.modified_blocks[(x, y, z)] = block_id

    def is_solid(self, x: int, y: int, z: int) -> bool:
        return self.get_block(x, y, z) != 0

    def unload_far_chunks(self, center_x: int, center_z: int, radius: int) -> None:
        to_remove = []
        for (chunk_x, chunk_z), chunk in self.chunks.items():
            if abs(chunk_x - center_x) > radius or abs(chunk_z - center_z) > radius:
                to_remove.append((chunk_x, chunk_z))
        for coords in to_remove:
            chunk = self.chunks.pop(coords)
            if chunk.vertex_list:
                chunk.vertex_list.delete()

    def rebuild_visible(self, batch) -> None:
        for chunk in self.chunks.values():
            chunk.batch = batch
            chunk.rebuild_mesh(self.is_solid)
