import math
import random

import pyglet
from pyglet import gl
from pyglet.window import key, mouse

from voxel.constants import BLOCK_TYPES, CHUNK_SIZE, MAX_RAY_DISTANCE, RENDER_DISTANCE
from voxel.inventory import Hotbar
from voxel.player import Player
from voxel.renderer import Renderer
from voxel.storage import WorldStorage
from voxel.world import World


class VoxelGame(pyglet.window.Window):
    def __init__(self) -> None:
        super().__init__(1280, 720, "Cobal Voxel Sandbox", resizable=True)
        self.set_exclusive_mouse(True)
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.batch = pyglet.graphics.Batch()
        self.storage = WorldStorage("saves/world.json")
        self.world = World(seed=random.randint(0, 999999), storage=self.storage)
        self.player = Player(position=(0.0, 40.0, 0.0), velocity=(0.0, 0.0, 0.0))
        self.hotbar = Hotbar()
        self.renderer = Renderer(self)
        self.renderer.setup()
        self._rebuild_all_chunks()
        pyglet.clock.schedule_interval(self.update, 1 / 60)

    def _rebuild_all_chunks(self) -> None:
        self.batch = pyglet.graphics.Batch()
        self.world.rebuild_visible(self.batch)

    def on_draw(self) -> None:
        self.clear()
        self.renderer.set_lighting(self.renderer.intensity)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(65.0, self.width / self.height, 0.1, 200.0)
        self.renderer.apply_camera(self.player.position, self.player.yaw, self.player.pitch)
        self.batch.draw()
        self.renderer.draw_crosshair()
        self.renderer.draw_hotbar(self.hotbar, BLOCK_TYPES)

    def update(self, dt: float) -> None:
        self.renderer.update_day_cycle(dt)
        self.handle_input(dt)
        move_input = (
            float(self.keys[key.D]) - float(self.keys[key.A]),
            float(self.keys[key.W]) - float(self.keys[key.S]),
        )
        self.player.update(dt, move_input, self.world)
        self.update_chunks()

    def update_chunks(self) -> None:
        cx, cz = self.world.chunk_coords(int(self.player.position[0]), int(self.player.position[2]))
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                chunk = self.world.get_chunk(cx + dx, cz + dz)
                if chunk.batch is None:
                    chunk.batch = self.batch
                    chunk.rebuild_mesh(self.world.is_solid)
        self.world.unload_far_chunks(cx, cz, RENDER_DISTANCE)

    def handle_input(self, dt: float) -> None:
        if self.keys[key.SPACE]:
            self.player.jump()
        if self.keys[key.ESCAPE]:
            self.set_exclusive_mouse(False)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if not self._exclusive:
            return
        hit = self.raycast()
        if not hit:
            return
        block_pos, face = hit
        if button == mouse.LEFT:
            self.world.set_block(*block_pos, 0)
        elif button == mouse.RIGHT:
            place_pos = (block_pos[0] + face[0], block_pos[1] + face[1], block_pos[2] + face[2])
            self.world.set_block(*place_pos, self.hotbar.selected_block)
        self._rebuild_all_chunks()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        if self._exclusive:
            self.player.look(dx, dy)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == key._1:
            self.hotbar.select(0)
        elif symbol == key._2:
            self.hotbar.select(1)
        elif symbol == key._3:
            self.hotbar.select(2)
        elif symbol == key._4:
            self.hotbar.select(3)

    def on_close(self) -> None:
        self.world.save()
        super().on_close()

    def raycast(self):
        ox, oy, oz = self.player.position
        dx, dy, dz = self.player.forward_vector()
        step = 0.1
        last_pos = None
        for i in range(int(MAX_RAY_DISTANCE / step)):
            t = i * step
            x = ox + dx * t
            y = oy + dy * t
            z = oz + dz * t
            block_pos = (math.floor(x), math.floor(y), math.floor(z))
            if self.world.is_solid(*block_pos):
                if last_pos:
                    face = (
                        block_pos[0] - last_pos[0],
                        block_pos[1] - last_pos[1],
                        block_pos[2] - last_pos[2],
                    )
                else:
                    face = (0, 1, 0)
                return block_pos, face
            last_pos = block_pos
        return None


if __name__ == "__main__":
    game = VoxelGame()
    pyglet.app.run()
