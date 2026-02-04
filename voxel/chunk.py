from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pyglet
from pyglet import gl

from voxel.constants import BLOCK_TYPES, BLOCK_SIZE, CHUNK_SIZE, WORLD_HEIGHT

Vec3 = Tuple[int, int, int]


FACE_DIRECTIONS = [
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
]


FACE_VERTICES = {
    (1, 0, 0): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
    (-1, 0, 0): [(0, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 0)],
    (0, 1, 0): [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)],
    (0, -1, 0): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
    (0, 0, 1): [(1, 0, 1), (1, 1, 1), (0, 1, 1), (0, 0, 1)],
    (0, 0, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
}


@dataclass
class Chunk:
    chunk_x: int
    chunk_z: int
    blocks: Dict[Vec3, int]
    vertex_list: Optional[pyglet.graphics.vertexdomain.VertexList] = None
    batch: Optional[pyglet.graphics.Batch] = None

    def get_block(self, x: int, y: int, z: int) -> int:
        if y < 0 or y >= WORLD_HEIGHT:
            return 0
        return self.blocks.get((x, y, z), 0)

    def set_block(self, x: int, y: int, z: int, block_id: int) -> None:
        if block_id == 0:
            self.blocks.pop((x, y, z), None)
        else:
            self.blocks[(x, y, z)] = block_id

    def rebuild_mesh(self, is_solid_fn) -> None:
        if self.vertex_list:
            self.vertex_list.delete()
        vertices: List[float] = []
        colors: List[float] = []
        for (x, y, z), block_id in self.blocks.items():
            if block_id == 0:
                continue
            block = BLOCK_TYPES[block_id]
            for direction in FACE_DIRECTIONS:
                nx, ny, nz = x + direction[0], y + direction[1], z + direction[2]
                if not is_solid_fn(self.chunk_x * CHUNK_SIZE + nx, ny, self.chunk_z * CHUNK_SIZE + nz):
                    face = FACE_VERTICES[direction]
                    for vx, vy, vz in face:
                        wx = (self.chunk_x * CHUNK_SIZE + x + vx) * BLOCK_SIZE
                        wy = (y + vy) * BLOCK_SIZE
                        wz = (self.chunk_z * CHUNK_SIZE + z + vz) * BLOCK_SIZE
                        vertices.extend([wx, wy, wz])
                        colors.extend(block.color)
        if vertices and self.batch:
            self.vertex_list = self.batch.add(
                len(vertices) // 3,
                gl.GL_QUADS,
                None,
                ("v3f/static", vertices),
                ("c3f/static", colors),
            )

    def within_bounds(self, x: int, y: int, z: int) -> bool:
        return 0 <= x < CHUNK_SIZE and 0 <= z < CHUNK_SIZE and 0 <= y < WORLD_HEIGHT
