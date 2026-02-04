from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import pyglet
from pyglet import gl

from voxel.constants import BLOCK_SIZE, DAY_LENGTH


@dataclass
class Renderer:
    window: pyglet.window.Window
    day_time: float = 0.0
    intensity: float = 1.0

    def setup(self) -> None:
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)

    def apply_camera(self, position: Tuple[float, float, float], yaw: float, pitch: float) -> None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glRotatef(pitch, 1.0, 0.0, 0.0)
        gl.glRotatef(yaw, 0.0, 1.0, 0.0)
        gl.glTranslatef(-position[0] * BLOCK_SIZE, -position[1] * BLOCK_SIZE, -position[2] * BLOCK_SIZE)

    def update_day_cycle(self, dt: float) -> float:
        self.day_time = (self.day_time + dt) % DAY_LENGTH
        t = self.day_time / DAY_LENGTH
        self.intensity = 0.25 + 0.75 * math.sin(t * math.tau) * 0.5 + 0.5
        return self.intensity

    def set_lighting(self, intensity: float) -> None:
        gl.glClearColor(0.2 * intensity, 0.4 * intensity, 0.8 * intensity, 1.0)
        gl.glColor3f(intensity, intensity, intensity)

    def draw_crosshair(self) -> None:
        width, height = self.window.get_size()
        center_x, center_y = width // 2, height // 2
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.gluOrtho2D(0, width, 0, height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glColor3f(1.0, 1.0, 1.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(center_x - 6, center_y)
        gl.glVertex2f(center_x + 6, center_y)
        gl.glVertex2f(center_x, center_y - 6)
        gl.glVertex2f(center_x, center_y + 6)
        gl.glEnd()
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def draw_hotbar(self, hotbar, block_types) -> None:
        width, height = self.window.get_size()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.gluOrtho2D(0, width, 0, height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_DEPTH_TEST)
        slot_size = 28
        total_width = slot_size * len(hotbar.slots)
        start_x = (width - total_width) // 2
        y = 20
        for index, block_id in enumerate(hotbar.slots):
            x = start_x + index * slot_size
            if index == hotbar.selected_index:
                gl.glColor3f(1.0, 1.0, 1.0)
            else:
                gl.glColor3f(0.6, 0.6, 0.6)
            gl.glBegin(gl.GL_LINE_LOOP)
            gl.glVertex2f(x, y)
            gl.glVertex2f(x + slot_size, y)
            gl.glVertex2f(x + slot_size, y + slot_size)
            gl.glVertex2f(x, y + slot_size)
            gl.glEnd()
            color = block_types[block_id].color
            gl.glColor3f(*color)
            gl.glBegin(gl.GL_QUADS)
            gl.glVertex2f(x + 6, y + 6)
            gl.glVertex2f(x + slot_size - 6, y + 6)
            gl.glVertex2f(x + slot_size - 6, y + slot_size - 6)
            gl.glVertex2f(x + 6, y + slot_size - 6)
            gl.glEnd()
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
