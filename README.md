# Cobal Voxel Sandbox (Python + Pyglet)

A lightweight, original voxel sandbox game inspired by Minecraft. It features chunked terrain generation, block placement/destruction, a first-person controller, a simple hotbar, day/night lighting, and world save/load.

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`

## Run

```bash
python main.py
```

## Controls

- **W/A/S/D**: Move
- **Mouse**: Look
- **Space**: Jump
- **Shift**: Sneak
- **Left Click**: Break block
- **Right Click**: Place block
- **1-4**: Select block in hotbar
- **Esc**: Toggle mouse capture

## File Structure

```
/ (repo)
  main.py
  requirements.txt
  README.md
  voxel/
    __init__.py
    constants.py
    noise.py
    world.py
    chunk.py
    player.py
    renderer.py
    inventory.py
    storage.py
```

## Notes

- Terrain is generated with a simple value-noise based heightmap.
- Chunks are built into meshes; only visible faces are rendered.
- World changes are saved to `saves/world.json`.
