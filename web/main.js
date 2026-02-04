import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.module.js";
import { PointerLockControls } from "https://cdn.jsdelivr.net/npm/three@0.158.0/examples/jsm/controls/PointerLockControls.js";

const BLOCK_TYPES = [
  { id: 1, name: "grass", color: 0x59c94f },
  { id: 2, name: "dirt", color: 0x8b5a2b },
  { id: 3, name: "stone", color: 0x808080 },
  { id: 4, name: "wood", color: 0xa0703a },
];

const CHUNK_SIZE = 16;
const WORLD_HEIGHT = 48;
const RENDER_DISTANCE = 3;
const GRAVITY = -18;
const JUMP_VELOCITY = 7.5;
const MAX_RAY_DISTANCE = 6;
const DAY_LENGTH = 120;

class ValueNoise2D {
  constructor(seed = 1337) {
    this.seed = seed;
  }

  random2(x, z) {
    const n = Math.sin(x * 127.1 + z * 311.7 + this.seed * 17.7) * 43758.5453;
    return n - Math.floor(n);
  }

  smoothstep(t) {
    return t * t * (3 - 2 * t);
  }

  lerp(a, b, t) {
    return a + (b - a) * t;
  }

  sample(x, z, scale = 0.05) {
    const sx = x * scale;
    const sz = z * scale;
    const xi = Math.floor(sx);
    const zi = Math.floor(sz);
    const xf = sx - xi;
    const zf = sz - zi;
    const v00 = this.random2(xi, zi);
    const v10 = this.random2(xi + 1, zi);
    const v01 = this.random2(xi, zi + 1);
    const v11 = this.random2(xi + 1, zi + 1);
    const u = this.smoothstep(xf);
    const v = this.smoothstep(zf);
    const x1 = this.lerp(v00, v10, u);
    const x2 = this.lerp(v01, v11, u);
    return this.lerp(x1, x2, v);
  }
}

class FractalNoise2D {
  constructor(seed) {
    this.base = new ValueNoise2D(seed);
  }

  sample(x, z) {
    let total = 0;
    let amplitude = 1;
    let frequency = 1;
    let maxValue = 0;
    for (let i = 0; i < 4; i += 1) {
      total += this.base.sample(x * frequency, z * frequency, 0.02) * amplitude;
      maxValue += amplitude;
      amplitude *= 0.5;
      frequency *= 2;
    }
    return total / maxValue;
  }
}

class World {
  constructor(seed) {
    this.seed = seed;
    this.noise = new FractalNoise2D(seed);
    this.chunks = new Map();
    this.modifiedBlocks = new Map();
    this.load();
  }

  load() {
    const raw = localStorage.getItem("cobal-save");
    if (!raw) return;
    const data = JSON.parse(raw);
    this.seed = data.seed;
    this.noise = new FractalNoise2D(this.seed);
    this.modifiedBlocks = new Map(Object.entries(data.blocks).map(([k, v]) => [k, v]));
  }

  save() {
    const blocks = Object.fromEntries(this.modifiedBlocks);
    localStorage.setItem("cobal-save", JSON.stringify({ seed: this.seed, blocks }));
  }

  chunkKey(cx, cz) {
    return `${cx},${cz}`;
  }

  blockKey(x, y, z) {
    return `${x},${y},${z}`;
  }

  getHeight(x, z) {
    const height = Math.floor(this.noise.sample(x, z) * 20 + 20);
    return Math.min(Math.max(height, 1), WORLD_HEIGHT - 1);
  }

  getBlock(x, y, z) {
    if (y < 0 || y >= WORLD_HEIGHT) return 0;
    const key = this.blockKey(x, y, z);
    if (this.modifiedBlocks.has(key)) return this.modifiedBlocks.get(key);
    const height = this.getHeight(x, z);
    if (y >= height) return 0;
    if (y === height - 1) return 1;
    if (y >= height - 4) return 2;
    return 3;
  }

  setBlock(x, y, z, blockId) {
    const key = this.blockKey(x, y, z);
    if (blockId === 0) {
      this.modifiedBlocks.set(key, 0);
    } else {
      this.modifiedBlocks.set(key, blockId);
    }
  }
}

class ChunkMesh {
  constructor(cx, cz, scene) {
    this.cx = cx;
    this.cz = cz;
    this.scene = scene;
    this.group = new THREE.Group();
    this.scene.add(this.group);
  }

  dispose() {
    this.scene.remove(this.group);
    this.group.traverse((child) => {
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
    });
  }

  rebuild(world) {
    this.group.clear();
    const materialCache = new Map();
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    for (let x = 0; x < CHUNK_SIZE; x += 1) {
      for (let z = 0; z < CHUNK_SIZE; z += 1) {
        const worldX = this.cx * CHUNK_SIZE + x;
        const worldZ = this.cz * CHUNK_SIZE + z;
        const height = world.getHeight(worldX, worldZ);
        for (let y = 0; y < height; y += 1) {
          const blockId = world.getBlock(worldX, y, worldZ);
          if (blockId === 0) continue;
          if (!this.isExposed(world, worldX, y, worldZ)) continue;
          const blockType = BLOCK_TYPES.find((b) => b.id === blockId);
          if (!materialCache.has(blockId)) {
            materialCache.set(blockId, new THREE.MeshLambertMaterial({ color: blockType.color }));
          }
          const cube = new THREE.Mesh(geometry, materialCache.get(blockId));
          cube.position.set(worldX + 0.5, y + 0.5, worldZ + 0.5);
          cube.userData.block = { x: worldX, y, z: worldZ };
          this.group.add(cube);
        }
      }
    }
  }

  isExposed(world, x, y, z) {
    const neighbors = [
      [1, 0, 0],
      [-1, 0, 0],
      [0, 1, 0],
      [0, -1, 0],
      [0, 0, 1],
      [0, 0, -1],
    ];
    return neighbors.some(([dx, dy, dz]) => world.getBlock(x + dx, y + dy, z + dz) === 0);
  }
}

class Game {
  constructor() {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 200);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(this.renderer.domElement);

    this.controls = new PointerLockControls(this.camera, document.body);
    this.camera.position.set(0.5, 30, 0.5);

    this.world = new World(Math.floor(Math.random() * 999999));
    this.chunkMeshes = new Map();
    this.velocity = new THREE.Vector3();
    this.direction = new THREE.Vector3();
    this.keys = new Set();
    this.selectedBlockIndex = 0;
    this.dayTime = 0;

    this.sun = new THREE.DirectionalLight(0xffffff, 1);
    this.sun.position.set(30, 60, 20);
    this.scene.add(this.sun);
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.2));

    this.raycaster = new THREE.Raycaster();

    this.setupUI();
    this.setupEvents();
    this.rebuildVisibleChunks();
    this.animate();
  }

  setupUI() {
    const hotbar = document.getElementById("hotbar");
    hotbar.innerHTML = "";
    BLOCK_TYPES.forEach((block, index) => {
      const slot = document.createElement("div");
      slot.className = "hotbar-slot";
      if (index === this.selectedBlockIndex) {
        slot.classList.add("selected");
      }
      const swatch = document.createElement("div");
      swatch.className = "hotbar-color";
      swatch.style.background = `#${block.color.toString(16).padStart(6, "0")}`;
      slot.appendChild(swatch);
      hotbar.appendChild(slot);
    });
  }

  setupEvents() {
    const overlay = document.getElementById("overlay");
    document.body.addEventListener("click", () => {
      this.controls.lock();
    });

    this.controls.addEventListener("lock", () => {
      overlay.classList.add("hidden");
    });

    this.controls.addEventListener("unlock", () => {
      overlay.classList.remove("hidden");
    });

    window.addEventListener("keydown", (event) => {
      this.keys.add(event.code);
      if (event.code.startsWith("Digit")) {
        const index = parseInt(event.code.replace("Digit", ""), 10) - 1;
        if (index >= 0 && index < BLOCK_TYPES.length) {
          this.selectedBlockIndex = index;
          this.setupUI();
        }
      }
    });

    window.addEventListener("keyup", (event) => {
      this.keys.delete(event.code);
    });

    window.addEventListener("resize", () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });

    window.addEventListener("mousedown", (event) => {
      if (!this.controls.isLocked) return;
      if (event.button === 0) {
        this.breakBlock();
      } else if (event.button === 2) {
        this.placeBlock();
      }
    });

    window.addEventListener("contextmenu", (event) => event.preventDefault());
    window.addEventListener("beforeunload", () => this.world.save());
  }

  breakBlock() {
    const hit = this.raycast();
    if (!hit) return;
    const { block } = hit;
    this.world.setBlock(block.x, block.y, block.z, 0);
    this.rebuildVisibleChunks();
  }

  placeBlock() {
    const hit = this.raycast();
    if (!hit) return;
    const { block, face } = hit;
    const blockType = BLOCK_TYPES[this.selectedBlockIndex];
    this.world.setBlock(block.x + face.x, block.y + face.y, block.z + face.z, blockType.id);
    this.rebuildVisibleChunks();
  }

  raycast() {
    this.raycaster.setFromCamera(new THREE.Vector2(0, 0), this.camera);
    this.raycaster.far = MAX_RAY_DISTANCE;
    const intersects = this.raycaster.intersectObjects(this.scene.children, true);
    if (!intersects.length) return null;
    const hit = intersects[0];
    if (!hit.object.userData.block) return null;
    return {
      block: hit.object.userData.block,
      face: hit.face.normal,
    };
  }

  rebuildVisibleChunks() {
    const playerX = Math.floor(this.camera.position.x);
    const playerZ = Math.floor(this.camera.position.z);
    const centerChunkX = Math.floor(playerX / CHUNK_SIZE);
    const centerChunkZ = Math.floor(playerZ / CHUNK_SIZE);

    const nextChunks = new Set();
    for (let dx = -RENDER_DISTANCE; dx <= RENDER_DISTANCE; dx += 1) {
      for (let dz = -RENDER_DISTANCE; dz <= RENDER_DISTANCE; dz += 1) {
        const cx = centerChunkX + dx;
        const cz = centerChunkZ + dz;
        const key = `${cx},${cz}`;
        nextChunks.add(key);
        if (!this.chunkMeshes.has(key)) {
          const mesh = new ChunkMesh(cx, cz, this.scene);
          mesh.rebuild(this.world);
          this.chunkMeshes.set(key, mesh);
        }
      }
    }

    for (const [key, mesh] of this.chunkMeshes.entries()) {
      if (!nextChunks.has(key)) {
        mesh.dispose();
        this.chunkMeshes.delete(key);
      }
    }
  }

  updateMovement(delta) {
    this.direction.set(0, 0, 0);
    const speed = 5;
    if (this.keys.has("KeyW")) this.direction.z -= 1;
    if (this.keys.has("KeyS")) this.direction.z += 1;
    if (this.keys.has("KeyA")) this.direction.x -= 1;
    if (this.keys.has("KeyD")) this.direction.x += 1;
    this.direction.normalize();

    if (this.controls.isLocked) {
      const moveX = this.direction.x * speed * delta;
      const moveZ = this.direction.z * speed * delta;
      this.controls.moveRight(moveX);
      this.controls.moveForward(moveZ);

      this.velocity.y += GRAVITY * delta;
      if (this.keys.has("Space") && this.onGround()) {
        this.velocity.y = JUMP_VELOCITY;
      }
      this.camera.position.y += this.velocity.y * delta;

      if (this.camera.position.y < 1.5) {
        this.camera.position.y = 1.5;
        this.velocity.y = 0;
      }
    }
  }

  onGround() {
    const x = Math.floor(this.camera.position.x);
    const z = Math.floor(this.camera.position.z);
    const groundHeight = this.world.getHeight(x, z);
    return this.camera.position.y <= groundHeight + 1.6;
  }

  updateDayCycle(delta) {
    this.dayTime = (this.dayTime + delta) % DAY_LENGTH;
    const t = this.dayTime / DAY_LENGTH;
    const intensity = 0.25 + 0.75 * (Math.sin(t * Math.PI * 2) * 0.5 + 0.5);
    this.sun.intensity = intensity;
    this.scene.background = new THREE.Color(0.2 * intensity, 0.4 * intensity, 0.8 * intensity);
  }

  animate() {
    let lastTime = performance.now();
    const loop = () => {
      const now = performance.now();
      const delta = (now - lastTime) / 1000;
      lastTime = now;
      this.updateDayCycle(delta);
      this.updateMovement(delta);
      if (Math.random() < 0.02) {
        this.rebuildVisibleChunks();
      }
      this.renderer.render(this.scene, this.camera);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

new Game();
