import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const canvas = document.querySelector("#court");
const ui = {
  score: document.querySelector("#score"),
  makes: document.querySelector("#makes"),
  streak: document.querySelector("#streak"),
  timer: document.querySelector("#timer"),
  feedback: document.querySelector("#feedback"),
  fill: document.querySelector("#meterFill"),
  needle: document.querySelector("#needle"),
  greenZone: document.querySelector("#greenZone"),
  modeButtons: [...document.querySelectorAll("[data-mode]")],
  bestResult: document.querySelector("#bestResult"),
  challengeGoal: document.querySelector("#challengeGoal"),
  shareResult: document.querySelector("#shareResult"),
};

const defaultShooter = {
  id: "lebron-inspired",
  name: "LeBron James",
  gatherTime: 0.22,
  loadTime: 0.18,
  jumpTime: 0.2,
  releaseTime: 0.11,
  greenWindow: 0.055,
  jumpHeight: 0.56,
  releaseHeight: 2.55,
  arc: 1.05,
  range: 1.18,
  movementPenalty: 0.11,
  consistency: 0.88,
  bodyScale: [1, 1, 1],
  team: {
    primary: "#552583",
    secondary: "#f5c84b",
    trim: "#ffffff",
  },
  jersey: {
    number: "23",
    name: "JAMES",
  },
  visual: {
    tier: "placeholder",
    primary: "rigged",
    glb: "./assets/players/lebron-inspired/player.glb",
    scanGlb: null,
    scanHeight: 2.1,
    scanOpacity: 0.2,
    scanPrimaryOpacity: 1,
    scanOffset: [0, 0, 0],
    anchorNames: {
      number: "JerseyNumberAnchor",
      name: "JerseyNameAnchor",
      ball: "BallReleaseAnchor",
    },
  },
  animationClips: {
    idle: "idle",
    dribbleIdle: "dribble_idle",
    gather: "gather",
    jump: "jump",
    release: "release",
    followThrough: "follow_through",
    land: "land",
  },
  releaseFrame: 42,
  releaseFps: 60,
  signature: {
    gatherDip: 0.12,
    fadeBack: 0.34,
    leftLegKick: 0.32,
    rightElbowTuck: 0.18,
    highSetPoint: 0.18,
    wristSnap: 0.42,
    shoulderTurn: 0.08,
    slowMotionScale: 2,
  },
};

const defaultAssetManifest = {
  runtimeTier: "procedural-mvp",
  assets: {
    court: { roughness: 0.33, clearcoat: 0.62, lineColor: "#f4ead5", paintColor: "#4f2581" },
    ball: { radius: 0.24, mass: 0.62, friction: 0.54, restitution: 0.74, linearDamping: 0.015, angularDamping: 0.04 },
    rim: { friction: 0.26, restitution: 0.82 },
    backboard: { friction: 0.32, restitution: 0.72 },
    floor: { friction: 0.82, restitution: 0.56 },
    net: { anchors: 12, friction: 0.14, restitution: 0.18 },
  },
};

const shooter = await loadShooterProfile("./src/shooters/lebron-inspired.json", defaultShooter);
const assetManifest = await loadAssetManifest("./src/assets/basketball-assets.json", defaultAssetManifest);
const assetTuning = assetManifest.assets ?? defaultAssetManifest.assets;

const shotDuration =
  shooter.gatherTime + shooter.loadTime + shooter.jumpTime + shooter.releaseTime;
const idealRelease = shooter.gatherTime + shooter.loadTime + shooter.jumpTime;
const meterDuration = idealRelease * 2;
const idealMeterPct = meterPositionForTime(idealRelease);
const visualGreenPct = THREE.MathUtils.clamp((shooter.greenWindow / idealRelease) * 1.05, 0.06, 0.12);
const releaseFrameSeconds = (shooter.releaseFrame ?? 42) / Math.max(1, shooter.releaseFps ?? 60);
const animationPhaseDurations = {
  idle: 2,
  dribbleIdle: 1,
  gather: shooter.gatherTime + shooter.loadTime,
  jump: shooter.jumpTime,
  release: shooter.releaseTime,
  followThrough: shooter.signature?.slowMotionScale ? 0.44 * shooter.signature.slowMotionScale : 0.72,
  land: 0.32,
};
const loopingPhases = new Set(["idle", "dribbleIdle"]);
ui.greenZone.style.left = `${idealMeterPct * 100}%`;
ui.greenZone.style.width = `${visualGreenPct * 100}%`;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x101820);
scene.fog = new THREE.Fog(0x101820, 18, 42);

const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
camera.position.set(0, 8.4, 14.5);

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;

const hemi = new THREE.HemisphereLight(0xf9fbff, 0x2b1b12, 1.6);
scene.add(hemi);

const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(-6, 14, 8);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.left = -16;
key.shadow.camera.right = 16;
key.shadow.camera.top = 18;
key.shadow.camera.bottom = -18;
scene.add(key);

const rimLight = new THREE.SpotLight(0xd8e9ff, 5.2, 32, Math.PI / 5, 0.55, 1.1);
rimLight.position.set(0, 9.2, -4.8);
rimLight.target.position.set(0, 1.8, 2.8);
rimLight.castShadow = false;
scene.add(rimLight, rimLight.target);

const courtGlow = new THREE.PointLight(0xffd59a, 0.8, 18, 1.8);
courtGlow.position.set(0, 3.2, 3.5);
scene.add(courtGlow);

const playerLight = new THREE.SpotLight(0xffffff, 2.8, 12, Math.PI / 5.2, 0.62, 1.1);
playerLight.castShadow = false;
playerLight.position.set(0, 4.8, 9.5);
playerLight.target.position.set(0, 1.5, 5.7);
scene.add(playerLight, playerLight.target);

const court = {
  width: 15,
  length: 28,
  hoopZ: -11.6,
  floorY: 0,
};

const state = {
  keys: new Set(),
  pointerDown: false,
  charging: false,
  chargeTime: 0,
  playerVelocity: new THREE.Vector3(),
  playerPos: new THREE.Vector3(0, 0, 5.7),
  facing: new THREE.Vector3(0, 0, -1),
  shots: 0,
  makes: 0,
  score: 0,
  streak: 0,
  feedbackTimer: 0,
  activeShot: null,
  netPulse: 0,
  phase: "idle",
  shotFocus: 0,
  releasePulse: 0,
  mode: "practice",
  modeActive: true,
  modeTime: Infinity,
  modeShotsRemaining: Infinity,
  dailyKey: dailyKey(),
  dailySpots: [],
  dailyChallenge: null,
  dailyIndex: 0,
};

const hoopTarget = new THREE.Vector3(0, 3.05, court.hoopZ);
const physics = {
  RAPIER: null,
  world: null,
  ballBody: null,
  ballCollider: null,
  accumulator: 0,
  fixedDt: 1 / 60,
  ready: false,
  lastBallY: 0,
  collisionCooldown: 0,
};

const sfx = {
  context: null,
  enabled: false,
};

const contactStats = {
  rim: 0,
  glass: 0,
  floor: 0,
  swish: 0,
};

const perfStats = {
  frames: 0,
  elapsed: 0,
  fps: 0,
  p95FrameMs: 0,
  samples: [],
};

function ensureAudio() {
  if (sfx.context) return;
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  sfx.context = new AudioContext();
}

function enableAudio() {
  ensureAudio();
  if (!sfx.context) return;
  sfx.enabled = true;
  if (sfx.context.state === "suspended") sfx.context.resume();
}

function playTone(type, intensity = 1) {
  if (!sfx.enabled || !sfx.context) return;
  const ctx = sfx.context;
  const now = ctx.currentTime;
  const gain = ctx.createGain();
  const osc = ctx.createOscillator();
  const filter = ctx.createBiquadFilter();
  const settings = {
    swish: [830, 0.075, "sine", 0.035],
    rim: [210, 0.09, "square", 0.028],
    glass: [520, 0.08, "triangle", 0.024],
    floor: [96, 0.07, "sawtooth", 0.022],
  }[type] ?? [330, 0.06, "sine", 0.02];
  osc.frequency.setValueAtTime(settings[0], now);
  osc.frequency.exponentialRampToValueAtTime(Math.max(40, settings[0] * 0.55), now + settings[1]);
  osc.type = settings[2];
  filter.type = type === "swish" ? "highpass" : "lowpass";
  filter.frequency.value = type === "swish" ? 720 : 900;
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(settings[3] * THREE.MathUtils.clamp(intensity, 0.35, 1.4), now + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + settings[1]);
  osc.connect(filter).connect(gain).connect(ctx.destination);
  osc.start(now);
  osc.stop(now + settings[1] + 0.02);
}

function mat(color, roughness = 0.72, metalness = 0.02) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness });
}

function createHardwoodTexture() {
  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = 1024;
  textureCanvas.height = 1024;
  const ctx = textureCanvas.getContext("2d");
  ctx.fillStyle = "#c58a48";
  ctx.fillRect(0, 0, 1024, 1024);
  for (let x = 0; x < 1024; x += 64) {
    const warm = 176 + ((x / 64) % 3) * 10;
    ctx.fillStyle = `rgb(${warm}, ${126 + ((x / 32) % 2) * 8}, 64)`;
    ctx.fillRect(x, 0, 62, 1024);
    ctx.fillStyle = "rgba(255,255,255,0.09)";
    ctx.fillRect(x + 1, 0, 2, 1024);
    ctx.fillStyle = "rgba(85,45,20,0.22)";
    ctx.fillRect(x + 61, 0, 1, 1024);
    for (let y = 0; y < 1024; y += 128) {
      ctx.strokeStyle = "rgba(70,36,16,0.22)";
      ctx.beginPath();
      ctx.moveTo(x + 5, y + ((x * 13 + y) % 38));
      ctx.bezierCurveTo(x + 22, y + 18, x + 34, y + 82, x + 57, y + 110);
      ctx.stroke();
    }
  }
  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2.5, 5.2);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createPaintTexture() {
  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = 512;
  textureCanvas.height = 512;
  const ctx = textureCanvas.getContext("2d");
  ctx.fillStyle = shooter.team?.primary ?? "#552583";
  ctx.fillRect(0, 0, 512, 512);
  ctx.fillStyle = "rgba(255,255,255,0.06)";
  for (let i = 0; i < 80; i += 1) {
    ctx.fillRect(Math.random() * 512, Math.random() * 512, 1 + Math.random() * 5, 1);
  }
  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2, 2);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createFabricTexture(primary, secondary) {
  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = 512;
  textureCanvas.height = 512;
  const ctx = textureCanvas.getContext("2d");
  ctx.fillStyle = primary;
  ctx.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 6) {
    ctx.fillStyle = y % 12 === 0 ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.08)";
    ctx.fillRect(0, y, 512, 1);
  }
  for (let x = 0; x < 512; x += 7) {
    ctx.fillStyle = "rgba(255,255,255,0.035)";
    ctx.fillRect(x, 0, 1, 512);
  }
  ctx.strokeStyle = secondary;
  ctx.lineWidth = 8;
  ctx.strokeRect(10, 10, 492, 492);
  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1.2, 1.2);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createSkinTexture() {
  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = 256;
  textureCanvas.height = 256;
  const ctx = textureCanvas.getContext("2d");
  ctx.fillStyle = "#8b5638";
  ctx.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 600; i += 1) {
    const shade = 92 + Math.random() * 60;
    ctx.fillStyle = `rgba(${shade + 35},${shade * 0.72},${shade * 0.48},0.10)`;
    ctx.fillRect(Math.random() * 256, Math.random() * 256, 1, 1);
  }
  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function addArenaDepth() {
  const arena = new THREE.Group();
  arena.name = "arena-depth";
  const riserMat = new THREE.MeshStandardMaterial({ color: 0x151b22, roughness: 0.85 });
  const seatMats = [
    new THREE.MeshStandardMaterial({ color: 0x33204d, roughness: 0.9 }),
    new THREE.MeshStandardMaterial({ color: 0xc59a3a, roughness: 0.9 }),
    new THREE.MeshStandardMaterial({ color: 0x202834, roughness: 0.9 }),
    new THREE.MeshStandardMaterial({ color: 0x6f4d35, roughness: 0.9 }),
  ];
  for (let row = 0; row < 7; row += 1) {
    const z = court.hoopZ - 2.6 - row * 0.48;
    const y = 0.55 + row * 0.34;
    const width = 13.5 + row * 1.4;
    const riser = new THREE.Mesh(new THREE.BoxGeometry(width, 0.18, 0.18), riserMat);
    riser.position.set(0, y - 0.15, z + 0.1);
    arena.add(riser);
    const count = 18 + row * 3;
    for (let i = 0; i < count; i += 1) {
      const x = -width / 2 + (i + 0.5) * (width / count);
      const fan = new THREE.Mesh(
        new THREE.CapsuleGeometry(0.065, 0.18, 3, 6),
        seatMats[(i + row) % seatMats.length]
      );
      fan.position.set(x, y, z);
      fan.rotation.x = 0.18;
      arena.add(fan);
    }
  }
  const tunnel = new THREE.Mesh(
    new THREE.BoxGeometry(4.8, 2.5, 0.16),
    new THREE.MeshStandardMaterial({ color: 0x070b0f, roughness: 0.9 })
  );
  tunnel.position.set(0, 1.65, court.hoopZ - 5.7);
  arena.add(tunnel);
  scene.add(arena);
}

const hardwoodTexture = createHardwoodTexture();
const paintTexture = createPaintTexture();
const jerseyTexture = createFabricTexture(shooter.team?.primary ?? "#552583", shooter.team?.secondary ?? "#f5c84b");
const skinTexture = createSkinTexture();

const materials = {
  court: new THREE.MeshPhysicalMaterial({
    color: 0xd39a59,
    map: hardwoodTexture,
    roughness: assetTuning.court?.roughness ?? 0.33,
    metalness: 0,
    clearcoat: assetTuning.court?.clearcoat ?? 0.62,
    clearcoatRoughness: 0.18,
  }),
  paint: new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(assetTuning.court?.paintColor ?? "#4f2581"),
    map: paintTexture,
    roughness: 0.42,
    clearcoat: 0.5,
    clearcoatRoughness: 0.2,
  }),
  line: new THREE.LineBasicMaterial({ color: new THREE.Color(assetTuning.court?.lineColor ?? "#f4ead5"), linewidth: 2 }),
  gold: new THREE.MeshStandardMaterial({ color: shooter.team?.secondary ?? 0xf5c84b, roughness: 0.5 }),
  jersey: new THREE.MeshStandardMaterial({ color: shooter.team?.primary ?? 0x552583, map: jerseyTexture, roughness: 0.72 }),
  skin: new THREE.MeshStandardMaterial({ color: 0xb2714b, map: skinTexture, roughness: 0.4 }),
  black: mat(0x121316),
  ball: mat(0xd86f2e),
  rim: mat(0xf15c2f, 0.42, 0.18),
  glass: new THREE.MeshPhysicalMaterial({
    color: 0xb9d7e7,
    roughness: 0.08,
    transmission: 0.25,
    transparent: true,
    opacity: 0.45,
  }),
};

function addBox(name, size, position, material, cast = false) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  mesh.name = name;
  mesh.position.set(...position);
  mesh.castShadow = cast;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}

addBox("court", [court.width, 0.18, court.length], [0, -0.09, 0], materials.court);
addBox("paint", [4.9, 0.045, 5.8], [0, 0.018, court.hoopZ + 2.9], materials.paint);
addArenaDepth();

function line(points) {
  const geo = new THREE.BufferGeometry().setFromPoints(points);
  const mesh = new THREE.Line(geo, materials.line);
  mesh.position.y = 0.035;
  scene.add(mesh);
  return mesh;
}

function rect(w, z0, z1) {
  line([
    new THREE.Vector3(-w / 2, 0, z0),
    new THREE.Vector3(w / 2, 0, z0),
    new THREE.Vector3(w / 2, 0, z1),
    new THREE.Vector3(-w / 2, 0, z1),
    new THREE.Vector3(-w / 2, 0, z0),
  ]);
}

rect(court.width, -court.length / 2, court.length / 2);
rect(4.9, court.hoopZ, court.hoopZ + 5.8);
line([new THREE.Vector3(-court.width / 2, 0, 0), new THREE.Vector3(court.width / 2, 0, 0)]);

const arcPoints = [];
for (let i = 0; i <= 48; i += 1) {
  const a = THREE.MathUtils.degToRad(22 + (136 * i) / 48);
  arcPoints.push(new THREE.Vector3(Math.cos(a) * 6.7, 0, court.hoopZ + Math.sin(a) * 6.7));
}
line(arcPoints);

const restrictedArc = [];
for (let i = 0; i <= 36; i += 1) {
  const a = THREE.MathUtils.degToRad(205 + (130 * i) / 36);
  restrictedArc.push(new THREE.Vector3(Math.cos(a) * 1.25, 0, court.hoopZ + 0.3 + Math.sin(a) * 1.25));
}
line(restrictedArc);

for (const x of [-2.45, 2.45]) {
  for (let i = 0; i < 4; i += 1) {
    const z = court.hoopZ + 1.15 + i * 0.76;
    line([new THREE.Vector3(x, 0, z), new THREE.Vector3(x + Math.sign(x) * 0.52, 0, z)]);
  }
}

const hoop = new THREE.Group();
scene.add(hoop);
const backboard = new THREE.Mesh(new THREE.BoxGeometry(4.1, 2.35, 0.18), materials.glass);
backboard.position.set(0, 3.45, court.hoopZ - 0.55);
backboard.castShadow = true;
hoop.add(backboard);

const rim = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.035, 12, 64), materials.rim);
rim.position.copy(hoopTarget);
rim.rotation.x = Math.PI / 2;
rim.castShadow = true;
hoop.add(rim);

const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.11, 4.2, 18), materials.black);
pole.position.set(0, 2.1, court.hoopZ - 1.35);
pole.castShadow = true;
hoop.add(pole);

const stanchion = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.46, 0.58), materials.black);
stanchion.position.set(0, 0.42, court.hoopZ - 1.35);
stanchion.castShadow = true;
hoop.add(stanchion);

const backboardPadding = new THREE.Mesh(
  new THREE.BoxGeometry(3.25, 0.12, 0.08),
  new THREE.MeshStandardMaterial({ color: shooter.team?.primary ?? 0x552583, roughness: 0.56 })
);
backboardPadding.position.set(0, 2.4, court.hoopZ - 0.45);
backboardPadding.castShadow = true;
hoop.add(backboardPadding);

const net = new THREE.Group();
net.userData.strands = [];
for (let i = 0; i < 12; i += 1) {
  const a = (Math.PI * 2 * i) / 12;
  const x = Math.cos(a) * 0.42;
  const z = Math.sin(a) * 0.42;
  const geo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(x, 2.98, court.hoopZ + z),
    new THREE.Vector3(x * 0.58, 2.35, court.hoopZ + z * 0.58),
  ]);
  const strand = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xf7f2df }));
  strand.userData.phase = i / 12;
  strand.userData.restEnd = new THREE.Vector3(x * 0.58, 2.35, court.hoopZ + z * 0.58);
  net.userData.strands.push(strand);
  net.add(strand);
}
hoop.add(net);

const player = new THREE.Group();
scene.add(player);
player.scale.set(...(shooter.bodyScale ?? [1, 1, 1]));

const playerRig = {
  mixer: null,
  actions: {},
  activeAction: null,
  root: null,
  scan: null,
  scanMixer: null,
  scanActions: {},
  activeScanAction: null,
  scanDecals: null,
  scanBounds: null,
  anchors: {},
  parts: {},
  visualTier: "placeholder",
  animationStatus: "placeholder",
};

const generatedScanIsPrimary = shooter.visual?.primary === "generated-scan";

const placeholderPlayer = new THREE.Group();
placeholderPlayer.visible = !generatedScanIsPrimary;
player.add(placeholderPlayer);

function limb(radius, length, color) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length, 18), color);
  mesh.castShadow = true;
  return mesh;
}

const hips = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.42, 0.44), materials.jersey);
hips.position.y = 1.02;
hips.castShadow = true;
placeholderPlayer.add(hips);

const torso = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.15, 0.52), materials.jersey);
torso.position.y = 1.62;
torso.castShadow = true;
placeholderPlayer.add(torso);

const head = new THREE.Mesh(new THREE.SphereGeometry(0.32, 24, 18), materials.skin);
head.position.y = 2.38;
head.scale.set(0.92, 1.05, 0.9);
head.castShadow = true;
placeholderPlayer.add(head);

const beard = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.12, 0.08), materials.black);
beard.position.set(0, 2.25, -0.29);
placeholderPlayer.add(beard);

const number = makeTextPatch(shooter.jersey?.number ?? "23", shooter.team?.secondary ?? "#f5c84b", 128, 128, "900 72px Inter, Arial");
number.position.set(0, 1.74, -0.285);
number.rotation.y = Math.PI;
placeholderPlayer.add(number);

const leftLeg = limb(0.13, 1.05, materials.skin);
const rightLeg = limb(0.13, 1.05, materials.skin);
leftLeg.position.set(-0.28, 0.48, 0);
rightLeg.position.set(0.28, 0.48, 0);
placeholderPlayer.add(leftLeg, rightLeg);

const leftArm = limb(0.105, 0.94, materials.skin);
const rightArm = limb(0.105, 0.94, materials.skin);
leftArm.position.set(-0.68, 1.62, -0.05);
rightArm.position.set(0.68, 1.62, -0.05);
leftArm.rotation.z = -0.28;
rightArm.rotation.z = 0.28;
placeholderPlayer.add(leftArm, rightArm);

const shoes = new THREE.Group();
const shoeMat = mat(0xf2f2ea);
for (const x of [-0.28, 0.28]) {
  const shoe = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.16, 0.62), shoeMat);
  shoe.position.set(x, 0.08, -0.09);
  shoe.castShadow = true;
  shoes.add(shoe);
}
placeholderPlayer.add(shoes);

const ball = new THREE.Mesh(new THREE.SphereGeometry(0.24, 32, 18), materials.ball);
ball.castShadow = true;
scene.add(ball);

const ballLines = new THREE.Group();
for (const rot of [0, Math.PI / 2]) {
  const seam = new THREE.Mesh(
    new THREE.TorusGeometry(0.245, 0.006, 8, 48),
    new THREE.MeshBasicMaterial({ color: 0x2b1610 })
  );
  seam.rotation.set(Math.PI / 2, rot, 0);
  ballLines.add(seam);
}
for (const [x, y, z] of [
  [0.42, 0.0, 0.0],
  [-0.42, 0.0, 0.0],
  [0.0, 0.42, Math.PI / 2],
  [0.0, -0.42, Math.PI / 2],
]) {
  const curve = new THREE.Mesh(
    new THREE.TorusGeometry(0.175, 0.0045, 8, 44),
    new THREE.MeshBasicMaterial({ color: 0x2b1610 })
  );
  curve.scale.set(0.42, 1, 1);
  curve.position.set(x * 0.24, y * 0.24, 0);
  curve.rotation.set(Math.PI / 2, z, 0);
  ballLines.add(curve);
}
ball.add(ballLines);

const releaseRing = new THREE.Mesh(
  new THREE.TorusGeometry(0.92, 0.018, 10, 96),
  new THREE.MeshBasicMaterial({
    color: 0x47ff93,
    transparent: true,
    opacity: 0,
    blending: THREE.AdditiveBlending,
  })
);
releaseRing.rotation.x = Math.PI / 2;
releaseRing.visible = false;
scene.add(releaseRing);

const clock = new THREE.Clock();
setSize();
updateStats();
updateBestSummary();
updateChallengeGoal();
setFeedback("Ready", "#fff9e7");
loadPlayerAsset();
initPhysics();

window.addEventListener("resize", setSize);
window.addEventListener("keydown", (event) => {
  enableAudio();
  if (event.repeat && event.code === "Space") return;
  state.keys.add(event.code);
  if (event.code === "Space") {
    event.preventDefault();
    beginCharge();
  }
});
window.addEventListener("keyup", (event) => {
  state.keys.delete(event.code);
  if (event.code === "Space") {
    event.preventDefault();
    releaseShot();
  }
});
window.addEventListener("pointerdown", () => {
  enableAudio();
  state.pointerDown = true;
  beginCharge();
});
window.addEventListener("pointerup", () => {
  state.pointerDown = false;
  releaseShot();
});
window.addEventListener("blur", () => {
  state.keys.clear();
  if (state.charging) releaseShot();
});
ui.modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});
ui.shareResult?.addEventListener("click", shareCurrentResult);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  });
}

renderer.setAnimationLoop(tick);

function makeTextPatch(text, color, width, height, font) {
  const textCanvas = document.createElement("canvas");
  textCanvas.width = width;
  textCanvas.height = height;
  const ctx = textCanvas.getContext("2d");
  ctx.clearRect(0, 0, width, height);
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, width / 2, height / 2);
  const texture = new THREE.CanvasTexture(textCanvas);
  const patch = new THREE.Mesh(
    new THREE.PlaneGeometry(0.58, 0.58),
    new THREE.MeshBasicMaterial({ map: texture, transparent: true })
  );
  return patch;
}

function setSize() {
  const width = window.innerWidth;
  const height = window.innerHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function beginCharge() {
  if (state.activeShot || state.charging || !state.modeActive) return;
  state.charging = true;
  state.chargeTime = 0;
  setPlayerPhase("gather");
  setFeedback("Set", "#fff9e7");
}

function releaseShot() {
  if (!state.charging || state.activeShot) return;
  const elapsed = state.chargeTime;
  state.charging = false;
  ui.fill.style.width = "0%";
  ui.needle.style.left = "0%";
  ui.needle.style.transform = "translateX(-50%) scaleY(1)";
  setPlayerPhase("release", true);
  launchShot(elapsed);
}

async function initPhysics() {
  try {
    const RAPIER = await import("https://cdn.jsdelivr.net/npm/@dimforge/rapier3d-compat@0.19.3/rapier.mjs");
    await RAPIER.init();
    physics.RAPIER = RAPIER;
    physics.world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
    physics.world.integrationParameters.dt = physics.fixedDt;
    createStaticPhysicsCourt();
    physics.ready = true;
  } catch (error) {
    physics.ready = false;
    console.warn("Rapier physics unavailable; using analytic fallback.", error);
  }
}

function createStaticPhysicsCourt() {
  if (!physics.RAPIER || !physics.world) return;
  const { RigidBodyDesc, ColliderDesc } = physics.RAPIER;
  const fixed = RigidBodyDesc.fixed();
  const floorBody = physics.world.createRigidBody(fixed);
  physics.world.createCollider(
    ColliderDesc.cuboid(court.width / 2, 0.08, court.length / 2)
      .setTranslation(0, -0.08, 0)
      .setFriction(assetTuning.floor?.friction ?? 0.82)
      .setRestitution(assetTuning.floor?.restitution ?? 0.56),
    floorBody
  );

  const glassBody = physics.world.createRigidBody(RigidBodyDesc.fixed());
  physics.world.createCollider(
    ColliderDesc.cuboid(2.05, 1.18, 0.045)
      .setTranslation(0, 3.45, court.hoopZ - 0.55)
      .setFriction(assetTuning.backboard?.friction ?? 0.32)
      .setRestitution(assetTuning.backboard?.restitution ?? 0.72),
    glassBody
  );

  const rimBody = physics.world.createRigidBody(RigidBodyDesc.fixed());
  const rimSegments = 18;
  for (let i = 0; i < rimSegments; i += 1) {
    const angle = (Math.PI * 2 * i) / rimSegments;
    const x = Math.cos(angle) * 0.47;
    const z = Math.sin(angle) * 0.47;
    physics.world.createCollider(
      ColliderDesc.ball(0.045)
        .setTranslation(hoopTarget.x + x, hoopTarget.y, hoopTarget.z + z)
        .setFriction(assetTuning.rim?.friction ?? 0.26)
        .setRestitution(assetTuning.rim?.restitution ?? 0.82),
      rimBody
    );
  }

  const neckBody = physics.world.createRigidBody(RigidBodyDesc.fixed());
  physics.world.createCollider(
    ColliderDesc.cuboid(0.08, 0.08, 0.62)
      .setTranslation(0, hoopTarget.y, court.hoopZ - 0.82)
      .setFriction(0.3)
      .setRestitution(0.58),
    neckBody
  );

  const netBody = physics.world.createRigidBody(RigidBodyDesc.fixed());
  const netAnchors = assetTuning.net?.anchors ?? 12;
  for (let i = 0; i < netAnchors; i += 1) {
    const angle = (Math.PI * 2 * i) / netAnchors;
    physics.world.createCollider(
      ColliderDesc.ball(0.026)
        .setTranslation(
          hoopTarget.x + Math.cos(angle) * 0.34,
          hoopTarget.y - 0.44,
          hoopTarget.z + Math.sin(angle) * 0.34
        )
        .setFriction(assetTuning.net?.friction ?? 0.14)
        .setRestitution(assetTuning.net?.restitution ?? 0.18),
      netBody
    );
  }
}

function resetPhysicsBall(start, velocity) {
  if (!physics.ready || !physics.RAPIER || !physics.world) return false;
  const { RigidBodyDesc, ColliderDesc } = physics.RAPIER;
  if (physics.ballCollider) {
    physics.world.removeCollider(physics.ballCollider, false);
    physics.ballCollider = null;
  }
  if (physics.ballBody) {
    physics.world.removeRigidBody(physics.ballBody);
    physics.ballBody = null;
  }
  const bodyDesc = RigidBodyDesc.dynamic()
    .setTranslation(start.x, start.y, start.z)
    .setLinvel(velocity.x, velocity.y, velocity.z)
    .setCcdEnabled(true)
    .setLinearDamping(assetTuning.ball?.linearDamping ?? 0.015)
    .setAngularDamping(assetTuning.ball?.angularDamping ?? 0.04);
  physics.ballBody = physics.world.createRigidBody(bodyDesc);
  physics.ballCollider = physics.world.createCollider(
    ColliderDesc.ball(assetTuning.ball?.radius ?? 0.24)
      .setMass(assetTuning.ball?.mass ?? 0.62)
      .setFriction(assetTuning.ball?.friction ?? 0.54)
      .setRestitution(assetTuning.ball?.restitution ?? 0.74),
    physics.ballBody
  );
  physics.lastBallY = start.y;
  physics.accumulator = 0;
  physics.collisionCooldown = 0;
  return true;
}

function analyticLaunchVelocity(start, target, flightTime) {
  const gravity = -9.81;
  return new THREE.Vector3(
    (target.x - start.x) / flightTime,
    (target.y - start.y - 0.5 * gravity * flightTime * flightTime) / flightTime,
    (target.z - start.z) / flightTime
  );
}

function launchShot(releaseTime) {
  const distance = state.playerPos.distanceTo(hoopTarget);
  const movement = state.playerVelocity.length();
  const shotType = classifyShotType(distance, movement);
  const distancePenalty = Math.max(0, distance - 7.2) * 0.007;
  const movingPenalty = movement * shooter.movementPenalty * 0.018;
  const effectiveGreen = Math.max(0.023, shooter.greenWindow - distancePenalty - movingPenalty);
  const timingError = releaseTime - idealRelease;
  const green = Math.abs(timingError) <= effectiveGreen;
  const make = green;
  const errorDirection = Math.sign(timingError || 1);
  const errorMagnitude = THREE.MathUtils.clamp(Math.abs(timingError) / effectiveGreen, 0, 6);
  const normalizedError = errorDirection * errorMagnitude;
  const meterPct = meterPositionForTime(releaseTime);
  const meterError = meterPct - idealMeterPct;
  const start = getReleasePointWorld();
  const target = hoopTarget.clone();
  if (!make) {
    const missPower = THREE.MathUtils.clamp((errorMagnitude - 1) / 5, 0, 1);
    const lateralFromMeter = THREE.MathUtils.clamp(meterError * 4.6, -1.15, 1.15);
    const lateralFromMovement = THREE.MathUtils.clamp(state.playerVelocity.x * 0.05, -0.28, 0.28);
    const readableMiss = 0.48 + missPower * 0.95;
    const missZ =
      timingError < 0
        ? readableMiss + Math.abs(meterError) * 2.6
        : -readableMiss - Math.abs(meterError) * 3.2;
    target.z += missZ;
    target.x += THREE.MathUtils.clamp(lateralFromMeter + lateralFromMovement, -1.25, 1.25);
    target.y += timingError < 0 ? -0.2 - missPower * 0.25 : 0.06 + missPower * 0.22;
  }
  const hang = THREE.MathUtils.clamp(0.74 + distance * 0.04, 0.78, 1.18);
  const missArcBias = make ? 0 : timingError < 0 ? -0.45 * errorMagnitude : 0.18 * errorMagnitude;
  const velocity = analyticLaunchVelocity(start, target, hang);
  const hasPhysics = resetPhysicsBall(start, velocity);
  state.activeShot = {
    elapsed: 0,
    duration: hang,
    start,
    target,
    peak: Math.max(start.y, target.y) + 2.2 + distance * 0.08 * shooter.arc + missArcBias,
    velocity,
    physics: hasPhysics,
    shotType,
    make,
    green,
    timingError,
    normalizedError,
    meterPct,
    meterError,
    counted: false,
    rimTouched: false,
    glassTouched: false,
    netTouched: false,
  };
  state.shots += 1;
  state.releasePulse = green ? 1 : 0.45;
  const earlyLate = timingError < 0 ? "Early" : "Late";
  setFeedback(green ? `${shotType.label} Green` : `${shotType.label} ${earlyLate}`, green ? "#47ff93" : "#ffd36a");
}

function classifyShotType(distance, movement) {
  const lateral = Math.abs(state.playerVelocity.x);
  const movingTowardHoop = state.playerVelocity.z < -0.35;
  if (distance > 8.3) return { id: "deep", label: "Deep", fadeScale: 1.22, legKick: 1.16, cameraPush: 1.12 };
  if (movement > 1.25 && lateral > 0.8) return { id: "drift", label: "Drift", fadeScale: 1.12, legKick: 1.28, cameraPush: 1.06 };
  if (movement > 1.1 && movingTowardHoop) return { id: "pullup", label: "Pull-Up", fadeScale: 0.86, legKick: 0.92, cameraPush: 1.0 };
  if (distance < 5.6) return { id: "postfade", label: "Fade", fadeScale: 1.35, legKick: 1.32, cameraPush: 1.1 };
  return { id: "set", label: "Set", fadeScale: 1, legKick: 1, cameraPush: 1 };
}

function currentJumpLift() {
  const slowMo = state.activeShot ? shooter.signature?.slowMotionScale ?? 2 : 1;
  if (state.activeShot) {
    const t = THREE.MathUtils.clamp(state.activeShot.elapsed / (0.52 * slowMo), 0, 1);
    return Math.sin((1 - t) * Math.PI * 0.5) * shooter.jumpHeight * 0.92;
  }
  if (!state.charging) return 0;
  const jumpStart = shooter.gatherTime + shooter.loadTime;
  const t = THREE.MathUtils.clamp((state.chargeTime - jumpStart) / shooter.jumpTime, 0, 1);
  return Math.sin(t * Math.PI) * shooter.jumpHeight * (0.86 + state.shotFocus * 0.16);
}

function easeInOutCubic(t) {
  const x = THREE.MathUtils.clamp(t, 0, 1);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
}

function easeOutBack(t) {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  const x = THREE.MathUtils.clamp(t, 0, 1);
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
}

function meterPositionForTime(time) {
  return easeInOutCubic(time / meterDuration);
}

function tick() {
  const dt = Math.min(clock.getDelta(), 0.033);
  const time = clock.elapsedTime;
  updatePerfStats(dt);
  if (playerRig.mixer) playerRig.mixer.update(dt);
  if (playerRig.scanMixer) playerRig.scanMixer.update(dt);
  updateMode(dt);
  updateShotFeel(dt);
  updateMovement(dt);
  updateCharge(dt);
  updatePlayer(time);
  updateBall(dt, time);
  updateCamera(dt);
  updateNet(dt);
  renderer.render(scene, camera);
}

function updatePerfStats(dt) {
  perfStats.frames += 1;
  perfStats.elapsed += dt;
  perfStats.samples.push(dt * 1000);
  if (perfStats.samples.length > 180) perfStats.samples.shift();
  if (perfStats.elapsed >= 1) {
    const sorted = [...perfStats.samples].sort((a, b) => a - b);
    perfStats.fps = Math.round(perfStats.frames / perfStats.elapsed);
    perfStats.p95FrameMs = Math.round((sorted[Math.floor(sorted.length * 0.95)] ?? 0) * 100) / 100;
    perfStats.frames = 0;
    perfStats.elapsed = 0;
    document.documentElement.dataset.jumpshotFps = String(perfStats.fps);
    document.documentElement.dataset.jumpshotP95 = String(perfStats.p95FrameMs);
    document.documentElement.dataset.jumpshotPhysics = physics.ready ? "ready" : "fallback";
  }
}

function setMode(mode) {
  state.mode = mode;
  state.modeActive = true;
  state.shots = 0;
  state.makes = 0;
  state.score = 0;
  state.streak = 0;
  state.activeShot = null;
  state.charging = false;
  state.modeShotsRemaining = Infinity;
  state.modeTime = Infinity;
  state.dailyIndex = 0;
  if (mode === "daily") {
    state.dailyKey = dailyKey();
    state.dailySpots = generateDailySpots(state.dailyKey);
    state.dailyChallenge = generateDailyChallenge(state.dailyKey);
    state.modeShotsRemaining = state.dailySpots.length;
    movePlayerToSpot(state.dailySpots[0]);
    setFeedback(`Daily ${state.dailyKey}`, "#fff9e7");
  } else if (mode === "threes15") {
    state.modeTime = 15;
    state.dailyChallenge = null;
    movePlayerToSpot(new THREE.Vector3(0, 0, 6.1));
    setFeedback("15s Threes", "#fff9e7");
  } else {
    state.dailyChallenge = null;
    setFeedback("Practice", "#fff9e7");
  }
  ui.modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  updateStats();
  updateBestSummary();
  updateChallengeGoal();
}

function updateMode(dt) {
  if (state.mode !== "threes15" || !state.modeActive) return;
  state.modeTime = Math.max(0, state.modeTime - dt);
  if (state.modeTime <= 0) {
    state.modeActive = false;
    state.charging = false;
    setFeedback(`Final: ${state.score}`, "#f9d65c");
    saveModeResult("threes15", currentResultPayload());
  }
  updateStats();
}

function dailyKey(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function seededRandom(seedText) {
  let seed = 2166136261;
  for (let i = 0; i < seedText.length; i += 1) {
    seed ^= seedText.charCodeAt(i);
    seed = Math.imul(seed, 16777619);
  }
  return () => {
    seed += 0x6d2b79f5;
    let t = seed;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function generateDailySpots(key) {
  const rand = seededRandom(`jumpshot:${key}`);
  const spots = [];
  for (let i = 0; i < 8; i += 1) {
    const side = rand() < 0.5 ? -1 : 1;
    const x = side * THREE.MathUtils.lerp(0.4, 5.7, rand());
    const z = THREE.MathUtils.lerp(2.2, 8.3, rand());
    spots.push(new THREE.Vector3(x, 0, z));
  }
  return spots;
}

function generateDailyChallenge(key) {
  const rand = seededRandom(`jumpshot:challenge:${key}`);
  const variants = [
    { id: "green-streak", label: "Hit 3 greens", targetScore: 12, bonus: "streak" },
    { id: "wing-work", label: "Win the wings", targetScore: 15, bonus: "wing" },
    { id: "deep-touch", label: "Score 18+", targetScore: 18, bonus: "deep" },
    { id: "perfect-eight", label: "6 makes / 8", targetScore: 16, bonus: "accuracy" },
  ];
  return variants[Math.floor(rand() * variants.length)] ?? variants[0];
}

function movePlayerToSpot(spot) {
  state.playerPos.copy(spot);
  state.playerVelocity.set(0, 0, 0);
  ball.position.set(spot.x + 0.42, 0.58, spot.z - 0.52);
}

function saveModeResult(mode, result) {
  const key = modeStorageKey(mode);
  const previous = JSON.parse(localStorage.getItem(key) || "null");
  const next = { ...result, at: new Date().toISOString(), mode, key: state.dailyKey };
  if (!previous || result.score > previous.score || result.makes > previous.makes || result.streak > (previous.streak ?? 0)) {
    localStorage.setItem(key, JSON.stringify(next));
    updateBestSummary(next);
    return true;
  }
  updateBestSummary(previous);
  return false;
}

function modeStorageKey(mode = state.mode) {
  return mode === "daily" ? `jumpshot:${mode}:${state.dailyKey}` : `jumpshot:${mode}:best`;
}

function getModeBest(mode = state.mode) {
  return JSON.parse(localStorage.getItem(modeStorageKey(mode)) || "null");
}

function formatResult(result) {
  if (!result) return "--";
  const made = `${result.makes ?? 0}/${result.shots ?? 0}`;
  const streak = result.streak ? `, streak ${result.streak}` : "";
  const grade = result.goalMet ? " cleared" : "";
  return `${result.score ?? 0} pts, ${made}${streak}${grade}`;
}

function updateBestSummary(result = getModeBest()) {
  if (!ui.bestResult) return;
  ui.bestResult.textContent = formatResult(result);
}

function updateChallengeGoal() {
  if (!ui.challengeGoal) return;
  if (state.mode === "daily") {
    const challenge = state.dailyChallenge ?? generateDailyChallenge(state.dailyKey);
    ui.challengeGoal.textContent = `${challenge.label} (${challenge.targetScore}+ pts)`;
  } else if (state.mode === "threes15") {
    ui.challengeGoal.textContent = "Most threes in 15s";
  } else {
    ui.challengeGoal.textContent = "Learn the release";
  }
}

function currentResultPayload() {
  const goalMet = state.mode === "daily" && state.dailyChallenge
    ? state.score >= state.dailyChallenge.targetScore
    : false;
  return {
    score: state.score,
    makes: state.makes,
    shots: state.shots,
    streak: state.streak,
    challenge: state.mode === "daily" ? state.dailyChallenge : null,
    goalMet,
  };
}

async function shareCurrentResult() {
  const best = getModeBest();
  const modeLabel = state.mode === "threes15" ? "15s Threes" : state.mode[0].toUpperCase() + state.mode.slice(1);
  const current = `${state.score} pts, ${state.makes}/${state.shots}, streak ${state.streak}`;
  const goal = ui.challengeGoal?.textContent ? ` Goal: ${ui.challengeGoal.textContent}.` : "";
  const url = window.location.href.split("#")[0];
  const text = `JumpShot ${modeLabel}: ${current}.${goal} Best: ${formatResult(best)}. Play: ${url}`;
  try {
    if (navigator.share) await navigator.share({ title: "JumpShot", text, url });
    else if (navigator.clipboard) await navigator.clipboard.writeText(text);
    setFeedback("Share copied", "#f9d65c");
  } catch {
    setFeedback("Share ready", "#f9d65c");
  }
}

function updateShotFeel(dt) {
  const targetFocus = state.charging
    ? easeInOutCubic(THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1))
    : state.activeShot
      ? 0.42
      : 0;
  state.shotFocus = THREE.MathUtils.lerp(state.shotFocus, targetFocus, 1 - Math.pow(0.0004, dt));
  state.releasePulse = Math.max(0, state.releasePulse - dt * 2.35);
  releaseRing.visible = state.releasePulse > 0.01;
  if (releaseRing.visible) {
    const pulse = easeOutBack(1 - state.releasePulse);
    releaseRing.position.set(state.playerPos.x, 0.07, state.playerPos.z);
    releaseRing.scale.setScalar(0.72 + pulse * 1.9);
    releaseRing.material.opacity = state.releasePulse * 0.68;
  }
  key.intensity = 2.2 + state.shotFocus * 0.7 + state.releasePulse * 1.4;
  rimLight.intensity = 5.2 + state.shotFocus * 1.5;
}

function updateMovement(dt) {
  const input = new THREE.Vector3();
  if (state.keys.has("KeyA")) input.x -= 1;
  if (state.keys.has("KeyD")) input.x += 1;
  if (state.keys.has("KeyW")) input.z -= 1;
  if (state.keys.has("KeyS")) input.z += 1;
  if (input.lengthSq() > 0) input.normalize();
  const sprint = state.keys.has("ShiftLeft") || state.keys.has("ShiftRight");
  const speed = state.charging ? 1.25 : sprint ? 5.1 : 3.65;
  const desired = input.multiplyScalar(speed);
  state.playerVelocity.lerp(desired, 1 - Math.pow(0.0004, dt));
  state.playerPos.addScaledVector(state.playerVelocity, dt);
  state.playerPos.x = THREE.MathUtils.clamp(state.playerPos.x, -court.width / 2 + 0.8, court.width / 2 - 0.8);
  state.playerPos.z = THREE.MathUtils.clamp(state.playerPos.z, court.hoopZ + 1.6, court.length / 2 - 1.5);
  const toHoop = hoopTarget.clone().sub(state.playerPos);
  toHoop.y = 0;
  if (toHoop.lengthSq() > 0.001) state.facing.copy(toHoop.normalize());
  if (!state.charging && !state.activeShot) {
    setPlayerPhase(state.playerVelocity.length() > 0.35 ? "dribbleIdle" : "idle");
  }
}

function updateCharge(dt) {
  if (!state.charging) return;
  state.chargeTime += dt;
  if (state.chargeTime > meterDuration + 0.12) {
    releaseShot();
    return;
  }
  const rawPct = THREE.MathUtils.clamp(state.chargeTime / meterDuration, 0, 1);
  const meterPct = meterPositionForTime(state.chargeTime);
  const beatDistance = Math.abs(state.chargeTime - idealRelease);
  const needleStretch = 1 + Math.max(0, 1 - beatDistance / 0.16) * 0.55;
  ui.fill.style.width = `${meterPct * 100}%`;
  ui.needle.style.left = `${meterPct * 100}%`;
  ui.needle.style.transform = `translateX(-50%) scaleY(${needleStretch.toFixed(3)})`;
  if (state.chargeTime < shooter.gatherTime) {
    setPlayerPhase("gather");
    setFeedback("Gather", "#fff9e7");
  } else if (state.chargeTime < shooter.gatherTime + shooter.loadTime) {
    setPlayerPhase("gather");
    setFeedback("Load", "#fff9e7");
  } else if (state.chargeTime < idealRelease) {
    setPlayerPhase("jump");
    setFeedback("Rise", "#fff9e7");
  } else if (rawPct < 0.58) {
    setPlayerPhase("release");
    setFeedback("Release", "#47ff93");
  } else {
    setPlayerPhase("release");
    setFeedback("Late", "#ffd36a");
  }
}

function updatePlayer(time) {
  player.position.copy(state.playerPos);
  player.position.y = currentJumpLift();
  const sig = shooter.signature ?? defaultShooter.signature;
  const slowMo = state.activeShot ? sig.slowMotionScale ?? 2 : 1;
  const releasePct = state.activeShot ? THREE.MathUtils.clamp(state.activeShot.elapsed / (0.42 * slowMo), 0, 1) : 0;
  const chargePctForFade = state.charging ? THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1) : 0;
  const fadeScale = state.activeShot?.shotType?.fadeScale ?? 1;
  const fadeAmount = (state.activeShot ? 1 - releasePct * 0.55 : chargePctForFade * 0.35) * (sig.fadeBack ?? 0.34) * fadeScale;
  player.position.addScaledVector(state.facing, -fadeAmount);
  const yaw = Math.atan2(state.facing.x, state.facing.z);
  const gatherLean = state.charging ? Math.sin(THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1) * Math.PI) * 0.04 : 0;
  player.rotation.y = yaw + gatherLean * Math.sign(state.playerVelocity.x || 1);
  if (!placeholderPlayer.visible) {
    updateLoadedPlayerPose(time);
  } else {
    updatePlaceholderPlayerPose(time);
  }
  updateGeneratedScanPose();
}

function updatePlaceholderPlayerPose(time) {
  const stride = Math.sin(time * 10.5) * THREE.MathUtils.clamp(state.playerVelocity.length() / 4, 0, 1);
  leftLeg.rotation.x = stride * 0.34;
  rightLeg.rotation.x = -stride * 0.34;
  leftArm.rotation.x = -stride * 0.16;
  rightArm.rotation.x = stride * 0.16;
  if (state.charging || state.activeShot) {
    const pct = state.activeShot ? 1 : THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1);
    const follow = state.activeShot ? THREE.MathUtils.clamp(state.activeShot.elapsed / (0.38 * (shooter.signature?.slowMotionScale ?? 2)), 0, 1) : 0;
    const shotType = state.activeShot?.shotType ?? { legKick: 1 };
    const rhythm = easeInOutCubic(pct);
    leftArm.rotation.x = -0.62 - rhythm * 1.55 + follow * 0.22;
    rightArm.rotation.x = -0.62 - rhythm * 2.12 - follow * 0.34;
    leftArm.rotation.z = -0.48 + rhythm * 0.38 - follow * 0.44;
    rightArm.rotation.z = 0.48 - rhythm * 0.46 - follow * 0.34;
    leftLeg.rotation.x = -0.22 + follow * 0.38 * shotType.legKick;
    rightLeg.rotation.x = 0.16 - follow * 0.26;
    torso.rotation.x = -0.18 + rhythm * 0.28 + follow * 0.08;
    torso.rotation.z = -follow * 0.08;
  } else {
    leftArm.rotation.z = -0.28;
    rightArm.rotation.z = 0.28;
    torso.rotation.x = THREE.MathUtils.lerp(torso.rotation.x, 0, 0.16);
  }
}

function updateGeneratedScanPose() {
  const scan = playerRig.scan;
  if (!scan) return;
  const base = scan.userData.basePosition ?? new THREE.Vector3();
  const isPrimary = scan.userData.primary === true;
  const sig = shooter.signature ?? defaultShooter.signature;
  const activeScale = state.activeShot?.shotType?.fadeScale ?? 1;
  const slowMo = state.activeShot ? sig.slowMotionScale ?? 2 : 1;
  const chargePct = state.charging ? THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1) : 0;
  const activePct = state.activeShot ? THREE.MathUtils.clamp(state.activeShot.elapsed / (0.62 * slowMo), 0, 1) : 0;
  const followPct = state.activeShot ? easeInOutCubic(THREE.MathUtils.clamp(state.activeShot.elapsed / (0.34 * slowMo), 0, 1)) : 0;
  const loadPct = Math.sin(Math.min(chargePct, 0.58) / 0.58 * Math.PI);
  const dip = loadPct * (sig.gatherDip ?? 0.12);
  const setPoint = easeInOutCubic(chargePct) * (sig.highSetPoint ?? 0.18);
  const fade = (state.activeShot ? 1 - activePct * 0.52 : chargePct * 0.28) * (sig.fadeBack ?? 0.34) * activeScale;
  const jumpAccent = isPrimary ? currentJumpLift() * 0.06 : currentJumpLift() * 0.04;
  scan.position.set(base.x, base.y - dip + jumpAccent, base.z + fade * (isPrimary ? 0.18 : 0.1));

  const targetLean = state.activeShot
    ? -0.18 - followPct * 0.08
    : state.charging
      ? -0.07 + setPoint * 0.1
      : 0;
  const targetShoulder = state.activeShot
    ? -0.08 * activeScale
    : state.charging
      ? -0.025 * chargePct
      : 0;
  scan.rotation.x = THREE.MathUtils.lerp(scan.rotation.x, targetLean, 0.1);
  scan.rotation.z = THREE.MathUtils.lerp(scan.rotation.z, targetShoulder, 0.1);

  const baseScale = scan.userData.baseScale ?? 1;
  const loadSquash = state.charging ? loadPct : 0;
  const releaseStretch = state.activeShot ? Math.sin(Math.min(activePct, 1) * Math.PI) : 0;
  const idleBreath = state.charging || state.activeShot ? 0 : Math.sin(clock.elapsedTime * 1.4) * 0.006;
  const targetScale = new THREE.Vector3(
    baseScale * (1 + loadSquash * 0.025 - releaseStretch * 0.012 + idleBreath),
    baseScale * (1 - loadSquash * 0.045 + releaseStretch * 0.035),
    baseScale * (1 + loadSquash * 0.02 - releaseStretch * 0.008 + idleBreath)
  );
  scan.scale.lerp(targetScale, 0.1);

  scan.traverse((object) => {
    if (object.isMesh && object.material) {
      const targetOpacity = isPrimary
        ? shooter.visual?.scanPrimaryOpacity ?? 1
        : state.activeShot
          ? 0.16
          : shooter.visual?.scanOpacity ?? 0.22;
      object.material.opacity = THREE.MathUtils.lerp(object.material.opacity, targetOpacity, 0.08);
    }
  });

  document.documentElement.dataset.jumpshotVisualPhase = state.activeShot
    ? "release"
    : state.charging
      ? chargePct < 0.55
        ? "gather"
        : "rise"
      : state.playerVelocity.length() > 0.35
        ? "dribble"
        : "idle";
}

function updateBall(dt, time) {
  if (state.activeShot) {
    const shot = state.activeShot;
    shot.elapsed += dt;
    updateActiveShotPhase(shot);
    if (shot.physics && physics.ballBody && physics.world) {
      physics.accumulator += dt;
      const maxSteps = 4;
      let steps = 0;
      while (physics.accumulator >= physics.fixedDt && steps < maxSteps) {
        physics.world.step();
        physics.accumulator -= physics.fixedDt;
        steps += 1;
      }
      const p = physics.ballBody.translation();
      const v = physics.ballBody.linvel();
      ball.position.set(p.x, p.y, p.z);
      ball.rotation.x += dt * (Math.abs(v.z) + 4.5);
      ball.rotation.z += dt * (Math.abs(v.x) + 3.2);
      if (detectPhysicsShotEvents(shot, v)) return;
      if (shot.elapsed > 3.2 || ball.position.y < -1.5 || ball.position.z > court.length / 2 + 2) {
        if (!shot.counted) finishShot({ ...shot, make: false, green: false });
        state.activeShot = null;
      }
    } else {
      const t = THREE.MathUtils.clamp(shot.elapsed / shot.duration, 0, 1);
      ball.position.lerpVectors(shot.start, shot.target, t);
      ball.position.y = THREE.MathUtils.lerp(shot.start.y, shot.target.y, t) + Math.sin(t * Math.PI) * (shot.peak - Math.max(shot.start.y, shot.target.y));
      ball.rotation.x += dt * 12;
      ball.rotation.z += dt * 7;
      if (!shot.counted && t > 0.88) {
        shot.counted = true;
        finishShot(shot);
      }
      if (t >= 1) state.activeShot = null;
    }
    return;
  }

  const moving = state.playerVelocity.length();
  const bounce = Math.abs(Math.sin(time * (moving > 0.3 ? 9.5 : 3.2)));
  const handSide = Math.sin(time * 5.6) > 0 ? 1 : -1;
  const liftPct = state.charging ? easeInOutCubic(THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1)) : 0;
  const local = state.charging
    ? new THREE.Vector3(0.16, 1.24 + liftPct * 1.08 + currentJumpLift(), -0.48 - liftPct * 0.12)
    : new THREE.Vector3(0.44 * handSide, 0.42 + bounce * 0.68, -0.52);
  const world = local.applyAxisAngle(new THREE.Vector3(0, 1, 0), player.rotation.y).add(state.playerPos);
  if (state.charging) world.y += Math.min(0.45, state.chargeTime * 0.8);
  ball.position.lerp(world, 1 - Math.pow(0.00001, dt));
  ball.rotation.x += dt * (moving * 3.5 + 2.1);
  ball.rotation.z += dt * handSide * 3.2;
}

function detectPhysicsShotEvents(shot, velocity) {
  const previousY = physics.lastBallY;
  physics.lastBallY = ball.position.y;
  physics.collisionCooldown = Math.max(0, physics.collisionCooldown - physics.fixedDt);
  const rimDistance = Math.hypot(ball.position.x - hoopTarget.x, ball.position.z - hoopTarget.z);
  const nearRimPlane = Math.abs(ball.position.y - hoopTarget.y) < 0.22;
  if (!shot.counted && previousY >= hoopTarget.y && ball.position.y < hoopTarget.y && rimDistance < 0.36 && velocity.y < 0) {
    shot.counted = true;
    finishShot({ ...shot, make: shot.green });
    state.activeShot = null;
    return true;
  }
  if (!shot.rimTouched && nearRimPlane && rimDistance > 0.36 && rimDistance < 0.68) {
    shot.rimTouched = true;
    contactStats.rim += 1;
    state.releasePulse = Math.max(state.releasePulse, 0.35);
    playTone("rim", 0.9);
    setFeedback(shot.green ? "Rim" : shot.timingError < 0 ? "Front Rim" : "Back Rim", shot.green ? "#fff9e7" : "#ff9a6a");
  }
  if (!shot.glassTouched && Math.abs(ball.position.z - (court.hoopZ - 0.55)) < 0.12 && ball.position.y > 2.2 && ball.position.y < 4.7) {
    shot.glassTouched = true;
    contactStats.glass += 1;
    state.releasePulse = Math.max(state.releasePulse, 0.26);
    playTone("glass", 0.82);
    if (!shot.green) setFeedback("Glass", "#ffd36a");
  }
  if (!shot.netTouched && ball.position.y < hoopTarget.y - 0.32 && ball.position.y > hoopTarget.y - 0.9 && rimDistance < 0.42 && velocity.y < 0) {
    shot.netTouched = true;
    contactStats.swish += shot.green ? 1 : 0;
    state.netPulse = Math.max(state.netPulse, shot.green ? 1 : 0.45);
    playTone("swish", shot.green ? 1.15 : 0.55);
  }
  if (physics.collisionCooldown <= 0 && ball.position.y < 0.32 && Math.abs(velocity.y) > 1.4) {
    physics.collisionCooldown = 0.12;
    contactStats.floor += 1;
    state.releasePulse = Math.max(state.releasePulse, 0.18);
    playTone("floor", 0.7);
  }
  return false;
}

function updateActiveShotPhase(shot) {
  const slowMo = shooter.signature?.slowMotionScale ?? 2;
  if (shot.elapsed < 0.16 * slowMo) {
    setPlayerPhase("release");
  } else {
    setPlayerPhase("followThrough");
  }
}

function finishShot(shot) {
  if (shot.make) {
    state.makes += 1;
    state.streak += 1;
    const three = state.playerPos.distanceTo(hoopTarget) > 7;
    state.score += three ? 3 : 2;
    state.netPulse = 1;
    if (!shot.rimTouched) {
      contactStats.swish += 1;
      playTone("swish", 1.2);
    }
    setPlayerPhase("land");
    setFeedback(shot.green ? "Perfect" : "Made", shot.green ? "#47ff93" : "#fff9e7");
  } else {
    state.streak = 0;
    setPlayerPhase("land");
    const missText =
      Math.abs(shot.normalizedError) < 1.6
        ? shot.timingError < 0
          ? "Slightly Early"
          : "Slightly Late"
        : shot.timingError < 0
          ? "Short"
          : "Long";
    setFeedback(missText, "#ff7f66");
  }
  updateStats();
  if (state.mode === "practice") saveModeResult("practice", currentResultPayload());
  handleModeAfterShot();
}

function updateStats() {
  ui.score.textContent = String(state.score);
  ui.makes.textContent = `${state.makes}/${state.shots}`;
  ui.streak.textContent = String(state.streak);
  if (state.mode === "threes15") ui.timer.textContent = `${Math.ceil(state.modeTime)}`;
  else if (state.mode === "daily") ui.timer.textContent = `${Math.max(0, state.modeShotsRemaining)}`;
  else ui.timer.textContent = "--";
}

function handleModeAfterShot() {
  if (state.mode === "daily") {
    state.modeShotsRemaining = Math.max(0, state.modeShotsRemaining - 1);
    state.dailyIndex += 1;
    if (state.dailyIndex >= state.dailySpots.length) {
      state.modeActive = false;
      setFeedback(`Daily: ${state.makes}/${state.shots}`, "#f9d65c");
      saveModeResult("daily", currentResultPayload());
    } else {
      window.setTimeout(() => {
        if (state.mode === "daily") movePlayerToSpot(state.dailySpots[state.dailyIndex]);
      }, 650);
    }
  }
  if (state.mode === "threes15" && state.modeActive) {
    window.setTimeout(() => {
      if (state.mode === "threes15" && state.modeActive && !state.activeShot) {
        const rand = seededRandom(`${state.dailyKey}:${state.shots}:${state.score}`);
        movePlayerToSpot(new THREE.Vector3(THREE.MathUtils.lerp(-5.2, 5.2, rand()), 0, THREE.MathUtils.lerp(4.5, 8.4, rand())));
      }
    }, 350);
  }
  updateStats();
}

function setFeedback(text, color) {
  ui.feedback.textContent = text;
  ui.feedback.style.color = color;
  state.feedbackTimer = 0.9;
}

function updateCamera(dt) {
  const shotFocus = state.shotFocus;
  const shotFollow = state.activeShot ? state.activeShot.shotType?.cameraPush ?? 1 : 0;
  const slowMo = state.activeShot ? shooter.signature?.slowMotionScale ?? 2 : 1;
  const inspectionZoom = state.activeShot
    ? easeInOutCubic(THREE.MathUtils.clamp(state.activeShot.elapsed / (0.34 * slowMo), 0, 1))
    : 0;
  const shake = state.releasePulse * 0.045;
  const target = new THREE.Vector3(
    state.playerPos.x * 0.35 + Math.sin(clock.elapsedTime * 34) * shake,
    7.6 - shotFocus * 1.15 - inspectionZoom * 1.65 + Math.cos(clock.elapsedTime * 41) * shake,
    state.playerPos.z + 8.7 - shotFocus * 2.35 + shotFollow * 0.55 - inspectionZoom * 3.15
  );
  camera.position.lerp(target, 1 - Math.pow(0.001, dt));
  const look = new THREE.Vector3(
    state.playerPos.x * 0.25,
    1.6 + shotFocus * 0.72 + inspectionZoom * 0.95,
    state.playerPos.z - 2.8 - shotFocus * 0.7 + inspectionZoom * 1.2
  );
  camera.lookAt(look);
  camera.fov = THREE.MathUtils.lerp(camera.fov, 48 - inspectionZoom * 9, 1 - Math.pow(0.0009, dt));
  camera.updateProjectionMatrix();
  document.documentElement.dataset.jumpshotZoom = inspectionZoom.toFixed(3);
  playerLight.position.lerp(
    new THREE.Vector3(state.playerPos.x * 0.35, 4.5, state.playerPos.z + 5.6),
    1 - Math.pow(0.0008, dt)
  );
  playerLight.target.position.lerp(new THREE.Vector3(state.playerPos.x, 1.55, state.playerPos.z), 0.28);
}

function updateNet(dt) {
  const strands = net.userData.strands ?? [];
  if (state.netPulse <= 0) {
    net.scale.setScalar(1);
    for (const strand of strands) {
      const attr = strand.geometry.getAttribute("position");
      const rest = strand.userData.restEnd;
      attr.setXYZ(1, rest.x, rest.y, rest.z);
      attr.needsUpdate = true;
    }
    return;
  }
  state.netPulse = Math.max(0, state.netPulse - dt * 2.8);
  const pulse = Math.sin(state.netPulse * Math.PI) * 0.16;
  net.scale.set(1 + pulse, 1 - pulse * 0.5, 1 + pulse);
  for (const strand of strands) {
    const attr = strand.geometry.getAttribute("position");
    const phase = strand.userData.phase * Math.PI * 2;
    const sway = Math.sin(clock.elapsedTime * 18 + phase) * state.netPulse * 0.055;
    const rest = strand.userData.restEnd;
    attr.setXYZ(1, rest.x + sway, rest.y - state.netPulse * 0.18, rest.z + Math.cos(phase) * state.netPulse * 0.035);
    attr.needsUpdate = true;
  }
}

async function loadShooterProfile(url, fallback) {
  try {
    const response = await fetch(url);
    if (!response.ok) return fallback;
    const profile = await response.json();
    return {
      ...fallback,
      ...profile,
      team: { ...fallback.team, ...profile.team },
      jersey: { ...fallback.jersey, ...profile.jersey },
      visual: { ...fallback.visual, ...profile.visual },
      animationClips: { ...fallback.animationClips, ...profile.animationClips },
      signature: { ...fallback.signature, ...profile.signature },
    };
  } catch {
    return fallback;
  }
}

async function loadAssetManifest(url, fallback) {
  try {
    const response = await fetch(url);
    if (!response.ok) return fallback;
    const manifest = await response.json();
    return {
      ...fallback,
      ...manifest,
      assets: {
        ...fallback.assets,
        ...manifest.assets,
      },
    };
  } catch {
    return fallback;
  }
}

function loadPlayerAsset() {
  const glb = shooter.visual?.glb;
  if (generatedScanIsPrimary) {
    placeholderPlayer.visible = false;
    playerRig.visualTier = "generated-scan";
    loadGeneratedScanAsset();
    return;
  }
  if (!glb) return;
  const loader = new GLTFLoader();
  loader.load(
    glb,
    (gltf) => {
      playerRig.root = gltf.scene;
      playerRig.visualTier = shooter.visual?.tier ?? "mvp";
      playerRig.root.name = `${shooter.id}-runtime-asset`;
      playerRig.root.traverse((object) => {
        if (object.isMesh) {
          object.castShadow = true;
          object.receiveShadow = true;
          object.material = materialForPart(object.name, object.material);
          playerRig.parts[object.name] = object;
        }
        const anchorNames = shooter.visual?.anchorNames ?? {};
        for (const [key, anchorName] of Object.entries(anchorNames)) {
          if (object.name === anchorName) playerRig.anchors[key] = object;
        }
      });

      playerRig.mixer = new THREE.AnimationMixer(playerRig.root);
      for (const clip of gltf.animations) {
        const action = playerRig.mixer.clipAction(clip);
        configurePhaseAction(action, phaseForClipName(clip.name));
        playerRig.actions[clip.name] = action;
      }
      player.add(playerRig.root);
      playerRig.root.visible = !generatedScanIsPrimary;
      placeholderPlayer.visible = false;
      attachUniformDecals(playerRig.anchors.number ?? playerRig.root);
      if (!generatedScanIsPrimary) loadGeneratedScanAsset();
      playerRig.animationStatus = "rig-ready";
      setPlayerPhase("idle", true);
      setFeedback("Ready", "#fff9e7");
    },
    undefined,
    () => {
      if (!generatedScanIsPrimary) {
        placeholderPlayer.visible = true;
        playerRig.visualTier = "placeholder";
      }
    }
  );
}

function loadGeneratedScanAsset() {
  const scanGlb = shooter.visual?.scanGlb;
  if (!scanGlb || playerRig.scan) return;
  document.documentElement.dataset.jumpshotScan = "loading";
  document.documentElement.dataset.jumpshotPrimaryVisual = generatedScanIsPrimary ? "generated-scan" : "rigged";
  const loader = new GLTFLoader();
  loader.load(
    scanGlb,
    (gltf) => {
      const scan = gltf.scene;
      scan.name = "hunyuan-selected-scan";
      const tint = new THREE.Color(shooter.team?.primary ?? "#552583").lerp(new THREE.Color("#ffffff"), 0.18);
      const isPrimary = generatedScanIsPrimary;
      const anchorNames = shooter.visual?.anchorNames ?? {};
      scan.traverse((object) => {
        if (object.isMesh) {
          object.castShadow = true;
          object.receiveShadow = true;
          object.renderOrder = isPrimary ? 1 : 3;
          const source = Array.isArray(object.material) ? object.material[0] : object.material;
          const scanMaterial = source?.clone?.() ?? new THREE.MeshStandardMaterial();
          if (!scanMaterial.map) {
            scanMaterial.color = isPrimary ? tint : tint;
          } else if (isPrimary) {
            scanMaterial.color = new THREE.Color(0xffffff);
          }
          scanMaterial.roughness = isPrimary ? 0.58 : 0.74;
          scanMaterial.metalness = 0.01;
          scanMaterial.emissive = isPrimary ? new THREE.Color(0x0b0705) : tint;
          scanMaterial.emissiveIntensity = isPrimary ? 0.03 : 0.18;
          scanMaterial.transparent = !isPrimary || (shooter.visual?.scanPrimaryOpacity ?? 1) < 1;
          scanMaterial.opacity = isPrimary ? shooter.visual?.scanPrimaryOpacity ?? 1 : shooter.visual?.scanOpacity ?? 0.2;
          scanMaterial.depthWrite = isPrimary;
          scanMaterial.depthTest = true;
          object.material = scanMaterial;
        }
        for (const [key, anchorName] of Object.entries(anchorNames)) {
          if (object.name === anchorName) playerRig.anchors[key] = object;
        }
      });
      const bounds = new THREE.Box3().setFromObject(scan);
      const size = new THREE.Vector3();
      const center = new THREE.Vector3();
      bounds.getSize(size);
      bounds.getCenter(center);
      const targetHeight = shooter.visual?.scanHeight ?? 2.1;
      const scale = targetHeight / Math.max(size.y, 0.001);
      const offset = shooter.visual?.scanOffset ?? [0, 0, 0];
      scan.scale.setScalar(scale);
      scan.position.set(-center.x * scale + offset[0], -bounds.min.y * scale + offset[1], -center.z * scale + 0.02 + offset[2]);
      scan.rotation.y = Math.PI;
      scan.userData.basePosition = scan.position.clone();
      scan.userData.baseScale = scale;
      scan.userData.primary = isPrimary;
      playerRig.scanMixer = new THREE.AnimationMixer(scan);
      playerRig.scanActions = {};
      for (const clip of gltf.animations) {
        const action = playerRig.scanMixer.clipAction(clip);
        configurePhaseAction(action, phaseForClipName(clip.name));
        playerRig.scanActions[clip.name] = action;
      }
      playerRig.scan = scan;
      playerRig.scanBounds = {
        rawSize: [size.x, size.y, size.z],
        normalizedHeight: targetHeight,
        scale,
        animations: gltf.animations.map((clip) => clip.name),
      };
      if (isPrimary) {
        playerRig.visualTier = "generated-scan";
        playerRig.animationStatus = "generated-scan-ready";
        attachGeneratedScanDecals(scan);
        setPlayerPhase("idle", true);
        setFeedback("LeBron mesh ready", "#fff9e7");
      }
      document.documentElement.dataset.jumpshotScan = "ready";
      document.documentElement.dataset.jumpshotAnimation = "ready";
      document.documentElement.dataset.jumpshotPrimaryVisual = isPrimary ? "generated-scan" : "rigged";
      document.documentElement.dataset.jumpshotScanHeight = String(targetHeight);
      document.documentElement.dataset.jumpshotScanClips = String(gltf.animations.length);
      document.documentElement.dataset.jumpshotReleaseFrameSeconds = releaseFrameSeconds.toFixed(3);
      player.add(scan);
    },
    undefined,
    (error) => {
      document.documentElement.dataset.jumpshotScan = "error";
      document.documentElement.dataset.jumpshotAnimation = "fallback";
      if (generatedScanIsPrimary) {
        placeholderPlayer.visible = true;
        playerRig.visualTier = "placeholder-fallback";
        playerRig.animationStatus = "placeholder-fallback";
        setPlayerPhase("idle", true);
        setFeedback("Blocky fallback", "#ffd36a");
      }
      console.warn("Hunyuan scan mesh unavailable.", error);
    }
  );
}

function materialForPart(name, existing) {
  const lower = name.toLowerCase();
  const base = existing?.clone?.() ?? new THREE.MeshStandardMaterial();
  base.roughness = 0.62;
  base.metalness = 0.02;
  if (lower.includes("headband") || lower.includes("wristband") || lower.includes("kneepad")) {
    base.color = lower.includes("rightwristband")
      ? new THREE.Color(shooter.team?.secondary ?? "#f5c84b")
      : new THREE.Color(0x111318);
    base.roughness = 0.5;
  } else if (lower.includes("shoegold") || lower.includes("trim") || lower.includes("stripe")) {
    base.color = new THREE.Color(shooter.team?.secondary ?? "#f5c84b");
    base.roughness = 0.48;
  } else if (
    lower.includes("skin") ||
    lower.includes("body") ||
    lower.includes("head") ||
    lower.includes("arm") ||
    lower.includes("leg") ||
    lower.includes("shoulder")
  ) {
    base.color = new THREE.Color(0xb2714b);
    base.map = skinTexture;
    base.roughness = 0.42;
  } else if (lower.includes("jersey") || lower.includes("shirt")) {
    base.color = new THREE.Color("#6f35b5");
    base.map = jerseyTexture;
    base.roughness = 0.72;
    base.emissive = new THREE.Color(0x12071f);
    base.emissiveIntensity = 0.1;
  } else if (lower.includes("short")) {
    base.color = new THREE.Color("#6f35b5");
    base.map = jerseyTexture;
    base.roughness = 0.72;
    base.emissive = new THREE.Color(0x12071f);
    base.emissiveIntensity = 0.1;
  } else if (lower.includes("sock") || lower.includes("compression")) {
    base.color = new THREE.Color(shooter.team?.trim ?? "#ffffff");
  } else if (lower.includes("shoe")) {
    base.color = new THREE.Color(0xf4f1e8);
    base.roughness = 0.38;
  }
  return base;
}

function updateLoadedPlayerPose(time) {
  const moving = THREE.MathUtils.clamp(state.playerVelocity.length() / 4, 0, 1);
  const stride = Math.sin(time * 10.5) * moving;
  const rawChargePct = state.charging ? THREE.MathUtils.clamp(state.chargeTime / idealRelease, 0, 1) : 0;
  const chargePct = easeInOutCubic(rawChargePct);
  const sig = shooter.signature ?? defaultShooter.signature;
  const slowMo = state.activeShot ? sig.slowMotionScale ?? 2 : 1;
  const activePct = state.activeShot ? THREE.MathUtils.clamp(state.activeShot.elapsed / (0.46 * slowMo), 0, 1) : 0;
  const followThrough = state.activeShot ? Math.min(1, state.activeShot.elapsed / (0.32 * slowMo)) : 0;
  const shotType = state.activeShot?.shotType ?? { fadeScale: 1, legKick: 1 };
  const signatureFade = (state.activeShot ? 1 - activePct * 0.45 : rawChargePct * 0.28) * (sig.fadeBack ?? 0.34) * shotType.fadeScale;
  const lebronDip = Math.sin(Math.min(rawChargePct, 0.55) / 0.55 * Math.PI) * (sig.gatherDip ?? 0.12);
  const releaseSnap = rawChargePct > 0.72 ? easeOutBack((rawChargePct - 0.72) / 0.28) : 0;
  const jumpLift = currentJumpLift();
  const parts = playerRig.parts;

  posePart(parts.LeftLeg, -stride * 0.28, 0, 0);
  posePart(parts.RightLeg, stride * 0.28, 0, 0);
  posePart(parts.LeftArm, -stride * 0.14, 0, -0.08);
  posePart(parts.RightArm, stride * 0.14, 0, 0.08);

  if (state.charging || state.activeShot) {
    const guideDrop = state.activeShot ? easeInOutCubic(followThrough) * 0.52 : 0;
    const wristSnap = followThrough * (sig.wristSnap ?? 0.42);
    const setPoint = chargePct * (sig.highSetPoint ?? 0.18);
    posePart(parts.LeftArm, -0.55 - chargePct * 1.24 + guideDrop * 0.18, 0.04, -0.46 + chargePct * 0.34 - guideDrop);
    posePart(parts.RightArm, -0.8 - chargePct * 1.78 - followThrough * 0.52 - setPoint, -0.05 - wristSnap * 0.1, 0.34 - chargePct * (sig.rightElbowTuck ?? 0.18) - wristSnap);
    posePart(parts.LeftShoulder, -0.08 - chargePct * 0.18, 0.02 + releaseSnap * (sig.shoulderTurn ?? 0.08), -0.12 - guideDrop * 0.12);
    posePart(parts.RightShoulder, -0.14 - chargePct * 0.24, -0.02 - releaseSnap * (sig.shoulderTurn ?? 0.08), 0.12 - wristSnap * 0.12);
    posePart(parts.LeftLeg, -0.18 - lebronDip * 1.35 + followThrough * (sig.leftLegKick ?? 0.32) * shotType.legKick, 0.02, -0.05 - followThrough * 0.16);
    posePart(parts.RightLeg, 0.16 + lebronDip * 0.7 - followThrough * 0.3, 0, 0.05);
    posePart(parts.Body, -0.18 + chargePct * 0.22 + followThrough * 0.08, -releaseSnap * 0.05, -releaseSnap * (sig.shoulderTurn ?? 0.08));
    if (parts.Body) parts.Body.position.set(0, 1.47 - lebronDip + jumpLift * 0.03, signatureFade * 0.08);
    if (parts.Jersey) parts.Jersey.position.set(0, 1.58 - lebronDip + jumpLift * 0.03, signatureFade * 0.085);
    if (parts.JerseyBackPanel) parts.JerseyBackPanel.position.set(0, 1.57 - lebronDip + jumpLift * 0.03, signatureFade * 0.085);
    if (parts.Shorts) parts.Shorts.position.set(0, 0.91 - lebronDip * 0.4 + jumpLift * 0.02, signatureFade * 0.055);
    if (parts.Head) parts.Head.position.y = 2.47 + jumpLift * 0.08;
    if (parts.Hair) parts.Hair.position.y = 2.68 + jumpLift * 0.08;
    moveHeadband(2.59 + jumpLift * 0.08);
  } else {
    posePart(parts.Body, 0, 0, 0);
    if (parts.Body) parts.Body.position.set(0, 1.47, 0);
    if (parts.Jersey) parts.Jersey.position.set(0, 1.58, 0);
    if (parts.JerseyBackPanel) parts.JerseyBackPanel.position.set(0, 1.57, 0);
    if (parts.Shorts) parts.Shorts.position.set(0, 0.91, 0);
    if (parts.Head) parts.Head.position.y = 2.47;
    if (parts.Hair) parts.Hair.position.y = 2.68;
    moveHeadband(2.59);
  }
}

function posePart(part, x = 0, y = 0, z = 0) {
  if (!part) return;
  part.rotation.x = THREE.MathUtils.lerp(part.rotation.x, x, 0.22);
  part.rotation.y = THREE.MathUtils.lerp(part.rotation.y, y, 0.22);
  part.rotation.z = THREE.MathUtils.lerp(part.rotation.z, z, 0.22);
}

function moveHeadband(y) {
  for (const partName of ["HeadbandFront", "HeadbandBack", "HeadbandLeft", "HeadbandRight"]) {
    if (playerRig.parts[partName]) playerRig.parts[partName].position.y = y;
  }
}

function getReleasePointWorld() {
  const anchor = playerRig.anchors.ball;
  if (anchor) {
    player.updateMatrixWorld(true);
    const world = new THREE.Vector3();
    anchor.getWorldPosition(world);
    if (Number.isFinite(world.x) && Number.isFinite(world.y) && Number.isFinite(world.z)) {
      world.y = Math.max(world.y, shooter.releaseHeight * 0.82);
      return world;
    }
  }
  return new THREE.Vector3(
    state.playerPos.x + state.facing.x * 0.5,
    shooter.releaseHeight + currentJumpLift(),
    state.playerPos.z + state.facing.z * 0.5
  );
}

function phaseForClipName(clipName) {
  const entries = Object.entries(shooter.animationClips ?? {});
  return entries.find(([, name]) => name === clipName)?.[0] ?? clipName;
}

function configurePhaseAction(action, phase) {
  if (!action) return;
  const duration = animationPhaseDurations[phase] ?? action.getClip().duration;
  const looping = loopingPhases.has(phase);
  action.enabled = true;
  action.clampWhenFinished = !looping;
  action.setLoop(looping ? THREE.LoopRepeat : THREE.LoopOnce, looping ? Infinity : 1);
  if (duration > 0 && action.getClip().duration > 0) {
    action.timeScale = action.getClip().duration / duration;
  }
}

function attachGeneratedScanDecals(scan) {
  const decals = new THREE.Group();
  decals.name = "generated-scan-uniform-decals";

  const backName = makeTextPatch(
    shooter.jersey?.name ?? "JAMES",
    shooter.team?.secondary ?? "#FDB927",
    256,
    128,
    "900 52px Inter, Arial"
  );
  backName.position.set(0, 1.78, 0.315);
  backName.scale.set(0.7, 0.32, 0.7);
  decals.add(backName);

  const backNumber = makeTextPatch(
    shooter.jersey?.number ?? "23",
    shooter.team?.secondary ?? "#FDB927",
    256,
    256,
    "900 134px Inter, Arial"
  );
  backNumber.position.set(0, 1.5, 0.325);
  backNumber.scale.set(0.78, 0.78, 0.78);
  decals.add(backNumber);

  const frontNumber = makeTextPatch(
    shooter.jersey?.number ?? "23",
    shooter.team?.secondary ?? "#FDB927",
    192,
    192,
    "900 96px Inter, Arial"
  );
  frontNumber.position.set(0, 1.5, -0.325);
  frontNumber.rotation.y = Math.PI;
  frontNumber.scale.set(0.45, 0.45, 0.45);
  decals.add(frontNumber);

  decals.traverse((object) => {
    if (object.isMesh) {
      object.renderOrder = 4;
      object.material.depthWrite = false;
      object.material.depthTest = true;
    }
  });

  scan.add(decals);
  playerRig.scanDecals = decals;
}

function attachUniformDecals(anchor) {
  const namePatch = makeTextPatch(
    shooter.jersey?.name ?? "JAMES",
    shooter.team?.secondary ?? "#f5c84b",
    256,
    128,
    "900 52px Inter, Arial"
  );
  namePatch.position.set(0, 1.88, -0.345);
  namePatch.rotation.y = Math.PI;
  namePatch.scale.set(0.72, 0.36, 0.72);
  anchor.add(namePatch);

  const numberPatch = makeTextPatch(
    shooter.jersey?.number ?? "23",
    shooter.team?.secondary ?? "#f5c84b",
    256,
    256,
    "900 136px Inter, Arial"
  );
  numberPatch.position.set(0, 1.58, -0.34);
  numberPatch.rotation.y = Math.PI;
  numberPatch.scale.setScalar(0.82);
  anchor.add(numberPatch);
}

function setPlayerPhase(phase, force = false) {
  if (!force && state.phase === phase) return;
  state.phase = phase;
  document.documentElement.dataset.jumpshotPlayerPhase = phase;
  const clipName = shooter.animationClips?.[phase];
  if (clipName) document.documentElement.dataset.jumpshotClip = clipName;
  if (playerRig.mixer) {
    const next = playerRig.actions[clipName];
    if (next && playerRig.activeAction !== next) {
      next.reset().fadeIn(0.12).play();
      if (playerRig.activeAction) playerRig.activeAction.fadeOut(0.12);
      playerRig.activeAction = next;
    }
  }
  if (playerRig.scanMixer) {
    const nextScan = playerRig.scanActions[clipName];
    if (nextScan && playerRig.activeScanAction !== nextScan) {
      nextScan.reset().fadeIn(0.12).play();
      if (playerRig.activeScanAction) playerRig.activeScanAction.fadeOut(0.12);
      playerRig.activeScanAction = nextScan;
    }
  }
}

if (["localhost", "127.0.0.1", ""].includes(window.location.hostname)) {
  window.__jumpshotDebug = {
    holdAndRelease: async (seconds = idealRelease) => {
      beginCharge();
      await new Promise((resolve) => window.setTimeout(resolve, seconds * 1000));
      releaseShot();
      return {
        held: seconds,
        idealRelease,
        meterPosition: meterPositionForTime(seconds),
      };
    },
    meterSample: (seconds) => ({
      seconds,
      idealRelease,
      meterDuration,
      meterPosition: meterPositionForTime(seconds),
    }),
    state: () => ({
      mode: state.mode,
      modeActive: state.modeActive,
      score: state.score,
      makes: state.makes,
      shots: state.shots,
      streak: state.streak,
      physicsReady: physics.ready,
      fixedDt: physics.fixedDt,
      assetTier: assetManifest.runtimeTier,
      scanBounds: playerRig.scanBounds,
      challenge: state.mode === "daily" ? state.dailyChallenge : ui.challengeGoal?.textContent,
      perf: { fps: perfStats.fps, p95FrameMs: perfStats.p95FrameMs },
      contactStats: { ...contactStats },
      best: getModeBest(),
      playerVisualTier: playerRig.visualTier,
      animationStatus: playerRig.animationStatus,
      activeClip: document.documentElement.dataset.jumpshotClip ?? null,
      activeScanClipTime: playerRig.activeScanAction ? Number(playerRig.activeScanAction.time.toFixed(3)) : null,
      releaseFrameSeconds,
      primaryVisual: document.documentElement.dataset.jumpshotPrimaryVisual ?? null,
      placeholderVisible: placeholderPlayer.visible,
      rigRootVisible: playerRig.root?.visible ?? null,
      scanState: document.documentElement.dataset.jumpshotScan ?? null,
      scanReady: Boolean(playerRig.scan),
      visualPhase: document.documentElement.dataset.jumpshotVisualPhase ?? null,
      activeShot: state.activeShot
        ? {
            elapsed: state.activeShot.elapsed,
            green: state.activeShot.green,
            make: state.activeShot.make,
            shotType: state.activeShot.shotType,
            meterError: state.activeShot.meterError,
            physics: state.activeShot.physics,
          }
        : null,
    }),
    benchmark: async (seconds = 5) => {
      const frames = [];
      let last = performance.now();
      const stopAt = last + seconds * 1000;
      while (performance.now() < stopAt) {
        await new Promise((resolve) => requestAnimationFrame(resolve));
        const now = performance.now();
        frames.push(now - last);
        last = now;
      }
      const sorted = [...frames].sort((a, b) => a - b);
      const average = frames.reduce((sum, value) => sum + value, 0) / Math.max(1, frames.length);
      const p95 = sorted[Math.floor(sorted.length * 0.95)] ?? average;
      return {
        seconds,
        frames: frames.length,
        averageFps: Math.round(10000 / average) / 10,
        p95FrameMs: Math.round(p95 * 100) / 100,
        physicsReady: physics.ready,
        fixedDt: physics.fixedDt,
        assetTier: assetManifest.runtimeTier,
        scanBounds: playerRig.scanBounds,
        challenge: state.mode === "daily" ? state.dailyChallenge : ui.challengeGoal?.textContent,
        perf: { fps: perfStats.fps, p95FrameMs: perfStats.p95FrameMs },
        contactStats: { ...contactStats },
        drawSurface: {
          pixelRatio: renderer.getPixelRatio(),
          width: renderer.domElement.width,
          height: renderer.domElement.height,
        },
      };
    },
  };
}
