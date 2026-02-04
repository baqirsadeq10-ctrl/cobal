from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from voxel.constants import GRAVITY, JUMP_VELOCITY, PLAYER_HEIGHT, PLAYER_RADIUS


@dataclass
class Player:
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    yaw: float = 0.0
    pitch: float = 0.0
    on_ground: bool = False

    def look(self, dx: float, dy: float) -> None:
        sensitivity = 0.1
        self.yaw += dx * sensitivity
        self.pitch -= dy * sensitivity
        self.pitch = max(-89.0, min(89.0, self.pitch))

    def forward_vector(self) -> Tuple[float, float, float]:
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        return (
            math.cos(pitch_rad) * math.sin(yaw_rad),
            math.sin(pitch_rad),
            -math.cos(pitch_rad) * math.cos(yaw_rad),
        )

    def update(self, dt: float, move_input: Tuple[float, float], world) -> None:
        vx, vy, vz = self.velocity
        move_x, move_z = move_input
        speed = 5.0
        yaw_rad = math.radians(self.yaw)
        forward = (math.sin(yaw_rad), -math.cos(yaw_rad))
        right = (forward[1], -forward[0])
        vx = (forward[0] * move_z + right[0] * move_x) * speed
        vz = (forward[1] * move_z + right[1] * move_x) * speed
        vy += GRAVITY * dt
        new_pos = (
            self.position[0] + vx * dt,
            self.position[1] + vy * dt,
            self.position[2] + vz * dt,
        )
        self.on_ground = False
        self.position, vy = self.resolve_collisions(new_pos, vy, world)
        self.velocity = (vx, vy, vz)

    def jump(self) -> None:
        if self.on_ground:
            self.velocity = (self.velocity[0], JUMP_VELOCITY, self.velocity[2])
            self.on_ground = False

    def resolve_collisions(self, new_pos, vy: float, world):
        px, py, pz = self.position
        nx, ny, nz = new_pos
        # Resolve Y
        if self.collides(px, ny, pz, world):
            if vy < 0:
                ny = math.floor(ny) + 1
                self.on_ground = True
            else:
                ny = math.floor(ny + PLAYER_HEIGHT) - PLAYER_HEIGHT - 0.01
            vy = 0
        # Resolve X
        if self.collides(nx, ny, pz, world):
            nx = px
        # Resolve Z
        if self.collides(nx, ny, nz, world):
            nz = pz
        return (nx, ny, nz), vy

    def collides(self, x: float, y: float, z: float, world) -> bool:
        min_x = math.floor(x - PLAYER_RADIUS)
        max_x = math.floor(x + PLAYER_RADIUS)
        min_y = math.floor(y)
        max_y = math.floor(y + PLAYER_HEIGHT)
        min_z = math.floor(z - PLAYER_RADIUS)
        max_z = math.floor(z + PLAYER_RADIUS)
        for bx in range(min_x, max_x + 1):
            for by in range(min_y, max_y + 1):
                for bz in range(min_z, max_z + 1):
                    if world.is_solid(bx, by, bz):
                        return True
        return False
