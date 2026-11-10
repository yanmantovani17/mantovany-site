// Planta 3D interativa do apartamento (tipo "maquete aberta"), com ambientes clicáveis.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function iniciarPlanta({ canvas, rotulo, aoSelecionar, aoPronto }) {
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true }); } catch (e) { return null; }
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const cena = new THREE.Scene();
  const pm = new THREE.PMREMGenerator(renderer); cena.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  const cam = new THREE.PerspectiveCamera(32, 1, 0.1, 200);
  const CX = 6.5, CZ = 3.6;                       // centro da planta
  const P = (x, z) => [x - CX, z - CZ];

  // ---------- texturas procedurais ----------
  const tex = (desenho, rep) => { const c = document.createElement('canvas'); c.width = c.height = 512; desenho(c.getContext('2d'));
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const madeira = (base, var_) => tex((g) => { for (let i = 0; i < 8; i++) { const y = i * 64, off = (i % 2) * 180;
      for (let x = -off; x < 512; x += 360) { const k = Math.random() * var_ - var_ / 2; g.fillStyle = `hsl(${base[0]},${base[1]}%,${base[2] + k}%)`; g.fillRect(x, y, 358, 62);
        for (let l = 0; l < 14; l++) { g.strokeStyle = `rgba(60,35,20,${Math.random() * 0.12})`; g.beginPath(); const yy = y + Math.random() * 62; g.moveTo(x, yy); g.bezierCurveTo(x + 120, yy + 3, x + 240, yy - 3, x + 358, yy); g.stroke(); } } } }, 0.5);
  const piso = (cor) => tex((g) => { g.fillStyle = cor; g.fillRect(0, 0, 512, 512); g.strokeStyle = 'rgba(0,0,0,.12)'; g.lineWidth = 3;
      for (let i = 0; i <= 512; i += 128) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 512); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(512, i); g.stroke(); }
      for (let i = 0; i < 2000; i++) { g.fillStyle = `rgba(0,0,0,${Math.random() * 0.03})`; g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2); } }, 0.6);
  const TEX = { madeira: madeira([28, 38, 52], 8), deck: madeira([24, 30, 34], 6), porcelanato: piso('#d9d5cd') };

  const M = (cor, rug = 0.8, metal = 0, extra = {}) => new THREE.MeshStandardMaterial({ color: cor, roughness: rug, metalness: metal, ...extra });
  const COR = { parede: M(0xf2eee7, 0.9), topo: M(0x2a3444, 0.7), sofa: M(0xcfc6b6, 0.95), linho: M(0xefebe3, 0.95), nogueira: M(0x6a4730, 0.6), escuro: M(0x262b33, 0.5),
    tapete: M(0xc9b897, 1), tapete2: M(0x8f9aa6, 1), branco: M(0xf7f6f3, 0.4), pedra: M(0xe7e3dc, 0.25), planta: M(0x4c6a38, 0.9), vaso: M(0xb98e5e, 0.8),
    ouro: M(0xd4a83a, 0.35, 0.8), vidro: new THREE.MeshPhysicalMaterial({ color: 0xd8e6ec, roughness: 0.05, transmission: 0.9, transparent: true, opacity: 0.35, thickness: 0.02 }), metal: M(0x9aa1a8, 0.3, 0.9) };

  const grupo = new THREE.Group(); cena.add(grupo);
  const caixa = (w, h, d, x, y, z, mat, ry = 0) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); const [px, pz] = P(x, z);
    m.position.set(px, y + h / 2, pz); m.rotation.y = ry; m.castShadow = true; m.receiveShadow = true; grupo.add(m); return m; };
  const cil = (r, h, x, y, z, mat, seg = 24) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat); const [px, pz] = P(x, z);
    m.position.set(px, y + h / 2, pz); m.castShadow = true; m.receiveShadow = true; grupo.add(m); return m; };

  // ---------- ambientes ----------
  const AMB = [
    { id: 'varanda', nome: 'Varanda gourmet', r: [[0, -1.8, 6.5, 0]], piso: 'deck', d: 'Bancada com churrasqueira e mesa para seis, integrada à sala por porta de vidro.' },
    { id: 'estar', nome: 'Estar e jantar', r: [[0, 0, 6.5, 5]], piso: 'madeira', d: 'Living integrado, com luz natural pela fachada de vidro e mesa para seis lugares.' },
    { id: 'cozinha', nome: 'Cozinha', r: [[6.5, 0, 10, 3.5]], piso: 'porcelanato', d: 'Cozinha aberta para a sala, com ilha central e bancadas em pedra.' },
    { id: 'servico', nome: 'Área de serviço', r: [[10, 0, 13, 3.5]], piso: 'porcelanato', d: 'Lavanderia com ventilação natural e espaço para lavadora e secadora.' },
    { id: 'hall', nome: 'Circulação', r: [[6.5, 3.5, 13, 5]], piso: 'madeira', d: 'Hall que distribui para a ala íntima.' },
    { id: 'master', nome: 'Suíte master', r: [[0, 5, 5, 9]], piso: 'madeira', d: 'Suíte principal com closet e banheiro com bancada ampla.' },
    { id: 'closet', nome: 'Closet', r: [[5, 5, 7, 6.5]], piso: 'madeira', d: 'Closet da suíte master, com armários sob medida.' },
    { id: 'banho1', nome: 'Banho master', r: [[5, 6.5, 7, 9]], piso: 'porcelanato', d: 'Banheiro da suíte com box em vidro e bancada.' },
    { id: 'suite2', nome: 'Suíte 2', r: [[7, 5, 10, 9]], piso: 'madeira', d: 'Segunda suíte, com armário e bancada de estudo.' },
    { id: 'office', nome: 'Home office', r: [[10, 5, 13, 7.5]], piso: 'madeira', d: 'Escritório com bancada junto à janela.' },
    { id: 'banho2', nome: 'Banho 2', r: [[10, 7.5, 13, 9]], piso: 'porcelanato', d: 'Banheiro da suíte 2.' },
  ];
  const pisos = [];
  for (const a of AMB) {
    a.area = a.r.reduce((s, [x1, z1, x2, z2]) => s + (x2 - x1) * (z2 - z1), 0);
    for (const [x1, z1, x2, z2] of a.r) {
      const t = TEX[a.piso].clone(); t.needsUpdate = true; t.repeat.set((x2 - x1) * 0.5, (z2 - z1) * 0.5);
      const mat = new THREE.MeshStandardMaterial({ map: t, roughness: a.piso === 'porcelanato' ? 0.35 : 0.7, emissive: 0xd4a83a, emissiveIntensity: 0 });
      const m = new THREE.Mesh(new THREE.BoxGeometry(x2 - x1, 0.08, z2 - z1), mat); const [px, pz] = P((x1 + x2) / 2, (z1 + z2) / 2);
      m.position.set(px, -0.04, pz); m.receiveShadow = true; m.userData.amb = a; grupo.add(m); pisos.push(m); (a.pisos ||= []).push(m);
    }
    a.centro = (() => { const [x1, z1, x2, z2] = a.r[0]; const [px, pz] = P((x1 + x2) / 2, (z1 + z2) / 2); return new THREE.Vector3(px, 0.2, pz); })();
  }
  // laje embaixo, com borda
  const base = new THREE.Mesh(new THREE.BoxGeometry(13.6, 0.35, 11.4), M(0x1b2636, 0.6)); base.position.set(0, -0.26, P(0, 3.6)[1] + 0.0); base.receiveShadow = true; grupo.add(base);

  // ---------- paredes (com janelas) ----------
  const HP = 2.5;
  const parede = (x1, z1, x2, z2, esp = 0.12, janelas = []) => {
    const L = Math.hypot(x2 - x1, z2 - z1), ang = Math.atan2(z2 - z1, x2 - x1), ux = (x2 - x1) / L, uz = (z2 - z1) / L;
    const peca = (a, b, y0, y1, mat) => { if (b - a < 0.01) return; const cx = x1 + ux * (a + b) / 2, cz = z1 + uz * (a + b) / 2;
      const m = caixa(b - a + (mat === COR.parede ? esp : 0), y1 - y0, esp, cx, y0, cz, mat, -ang); return m; };
    let t = 0; const js = [...janelas].sort((p, q) => p[0] - q[0]);
    for (const [a, b] of js) { peca(t, a, 0, HP, COR.parede); peca(a, b, 0, 0.9, COR.parede); peca(a, b, 0.9, 2.2, COR.vidro); peca(a, b, 2.2, HP, COR.parede); t = b; }
    peca(t, L, 0, HP, COR.parede);
    // tampa escura no topo (efeito maquete cortada)
    const cx = (x1 + x2) / 2, cz = (z1 + z2) / 2; const tp = caixa(L + esp, 0.02, esp + 0.005, cx, HP, cz, COR.topo, -ang); tp.castShadow = false;
  };
  parede(0, 0, 0, 9, 0.2, [[1, 4], [6, 8]]);
  parede(13, 0, 13, 9, 0.2, [[5.4, 7]]);
  parede(0, 9, 13, 9, 0.2, [[1, 4], [7.8, 9.4], [11, 12.3]]);
  parede(6.5, 0, 13, 0, 0.2, [[1, 3.2], [4.2, 5.6]]);
  // porta de vidro da sala para a varanda
  caixa(6.3, 2.3, 0.04, 3.25, 0, 0, COR.vidro); caixa(6.5, 0.2, 0.2, 3.25, 2.3, 0, COR.parede);
  [[10, 0, 10, 2.3], [10, 3.2, 10, 3.5], [7.5, 3.5, 10, 3.5], [10, 3.5, 11, 3.5], [11.9, 3.5, 13, 3.5],
   [0, 5, 4.0, 5], [4.9, 5, 7.3, 5], [8.2, 5, 10.3, 5], [11.2, 5, 13, 5],
   [5, 5, 5, 5.6], [5, 6.4, 5, 9], [5, 6.5, 5.6, 6.5], [6.4, 6.5, 7, 6.5], [7, 5, 7, 9],
   [10, 5, 10, 7.8], [10, 8.6, 10, 9], [10, 7.5, 13, 7.5]].forEach(([a, b, c, d]) => parede(a, b, c, d));
  // guarda-corpo de vidro da varanda
  [[0, -1.8, 6.5, -1.8], [0, -1.8, 0, 0], [6.5, -1.8, 6.5, 0]].forEach(([a, b, c, d]) => {
    const L = Math.hypot(c - a, d - b), ang = Math.atan2(d - b, c - a); caixa(L, 1.05, 0.03, (a + c) / 2, 0, (b + d) / 2, COR.vidro, -ang); caixa(L, 0.04, 0.06, (a + c) / 2, 1.05, (b + d) / 2, COR.metal, -ang); });

  // ---------- móveis ----------
  // estar
  caixa(2.4, 0.01, 2.8, 1.9, 0, 2.5, COR.tapete);
  caixa(0.95, 0.42, 2.6, 3.25, 0, 2.5, COR.sofa); caixa(0.22, 0.8, 2.6, 3.62, 0, 2.5, COR.sofa);
  caixa(0.95, 0.6, 0.2, 3.25, 0, 1.2, COR.sofa); caixa(0.95, 0.6, 0.2, 3.25, 0, 3.8, COR.sofa);
  cil(0.45, 0.38, 1.9, 0, 2.5, COR.nogueira, 32);
  caixa(0.42, 0.45, 2.2, 0.32, 0, 2.5, COR.nogueira); caixa(0.05, 0.75, 1.5, 0.14, 1.0, 2.5, COR.escuro);
  caixa(0.75, 0.42, 0.75, 1.6, 0, 0.9, COR.tapete2); caixa(0.75, 0.42, 0.75, 2.5, 0, 0.9, COR.tapete2);
  caixa(1.9, 0.75, 0.95, 5.15, 0, 3.95, COR.nogueira);
  for (const x of [4.55, 5.15, 5.75]) for (const z of [3.25, 4.65]) caixa(0.45, 0.48, 0.45, x, 0, z, COR.linho);
  cil(0.22, 0.4, 6.1, 0, 0.5, COR.vaso); const fo = new THREE.Mesh(new THREE.IcosahedronGeometry(0.42, 1), COR.planta); fo.position.set(...P(6.1, 0.5).flatMap((v, i) => i === 0 ? [v, 0.85] : [v])); fo.castShadow = true; grupo.add(fo);
  // cozinha
  caixa(2.7, 0.9, 0.62, 8.65, 0, 0.35, COR.branco); caixa(2.72, 0.04, 0.64, 8.65, 0.9, 0.35, COR.pedra);
  caixa(0.75, 2.0, 0.7, 6.95, 0, 0.4, COR.metal);
  caixa(1.9, 0.9, 0.95, 8.3, 0, 1.95, COR.nogueira); caixa(1.95, 0.05, 1.0, 8.3, 0.9, 1.95, COR.pedra);
  for (const x of [7.7, 8.3, 8.9]) cil(0.18, 0.7, x, 0, 2.75, COR.escuro);
  // serviço
  caixa(0.62, 0.85, 0.62, 12.55, 0, 0.4, COR.branco); caixa(0.62, 0.85, 0.62, 11.85, 0, 0.4, COR.branco); caixa(1.0, 0.9, 0.55, 10.7, 0, 0.35, COR.branco);
  // suíte master
  caixa(2.2, 0.01, 2.8, 2.5, 0, 7.6, COR.tapete);
  caixa(1.9, 0.4, 2.1, 2.5, 0, 7.85, COR.nogueira); caixa(1.85, 0.2, 2.0, 2.5, 0.4, 7.85, COR.linho); caixa(2.3, 1.1, 0.1, 2.5, 0, 8.93, COR.nogueira);
  caixa(0.7, 0.12, 0.35, 2.05, 0.6, 8.65, COR.branco); caixa(0.7, 0.12, 0.35, 2.95, 0.6, 8.65, COR.branco);
  caixa(0.5, 0.5, 0.45, 1.1, 0, 8.6, COR.nogueira); caixa(0.5, 0.5, 0.45, 3.9, 0, 8.6, COR.nogueira);
  caixa(0.8, 0.45, 0.8, 0.7, 0, 5.8, COR.tapete2);
  // closet + banho master
  caixa(1.9, 2.2, 0.55, 6.0, 0, 5.32, COR.nogueira); caixa(0.55, 2.2, 1.0, 6.7, 0, 6.0, COR.nogueira);
  caixa(1.4, 0.85, 0.5, 6.0, 0, 8.7, COR.branco); caixa(1.42, 0.04, 0.52, 6.0, 0.85, 8.7, COR.pedra);
  caixa(0.95, 0.05, 0.95, 6.45, 0, 7.1, COR.pedra); caixa(0.02, 2.0, 0.95, 5.95, 0, 7.1, COR.vidro);
  caixa(0.38, 0.42, 0.6, 5.35, 0, 7.9, COR.branco);
  // suíte 2
  caixa(1.6, 0.4, 2.0, 8.5, 0, 7.95, COR.nogueira); caixa(1.55, 0.2, 1.9, 8.5, 0.4, 7.95, COR.linho); caixa(1.9, 1.0, 0.1, 8.5, 0, 8.93, COR.nogueira);
  caixa(0.6, 2.2, 1.8, 7.35, 0, 5.95, COR.nogueira); caixa(1.2, 0.75, 0.5, 9.6, 0, 5.4, COR.branco);
  // escritório + banho 2
  caixa(0.7, 0.75, 1.6, 12.6, 0, 6.2, COR.nogueira); cil(0.25, 0.5, 12.0, 0, 6.2, COR.escuro); caixa(1.6, 1.6, 0.35, 11.4, 0, 7.3, COR.branco);
  caixa(1.1, 0.85, 0.5, 12.3, 0, 8.7, COR.branco); caixa(0.9, 0.05, 0.9, 10.6, 0, 8.3, COR.pedra); caixa(0.38, 0.42, 0.6, 11.3, 0, 8.65, COR.branco);
  // varanda gourmet
  caixa(0.62, 0.9, 2.2, 0.4, 0, -0.9, COR.escuro); caixa(0.64, 0.04, 2.22, 0.4, 0.9, -0.9, COR.pedra);
  cil(0.6, 0.75, 3.6, 0, -0.9, COR.nogueira, 32);
  for (let k = 0; k < 4; k++) { const a = k * Math.PI / 2 + 0.4; caixa(0.42, 0.45, 0.42, 3.6 + Math.cos(a) * 0.95, 0, -0.9 + Math.sin(a) * 0.95, COR.linho); }
  cil(0.2, 0.45, 6.0, 0, -1.4, COR.vaso); const f2 = new THREE.Mesh(new THREE.IcosahedronGeometry(0.4, 1), COR.planta); const [fx, fz] = P(6.0, -1.4); f2.position.set(fx, 0.85, fz); f2.castShadow = true; grupo.add(f2);
  fo.position.set(P(6.1, 0.5)[0], 0.85, P(6.1, 0.5)[1]);

  // ---------- luz ----------
  cena.add(new THREE.HemisphereLight(0xfff4e6, 0x3a4658, 0.9));
  const sol = new THREE.DirectionalLight(0xffe2bf, 2.4); sol.position.set(-8, 14, -6); sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048); Object.assign(sol.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 40 }); sol.shadow.bias = -0.0004; sol.shadow.radius = 4;
  cena.add(sol);

  // ---------- câmera e interação ----------
  const ctrl = new OrbitControls(cam, canvas);
  ctrl.enableZoom = false; ctrl.enablePan = false; ctrl.enableDamping = true; ctrl.dampingFactor = 0.08;
  ctrl.minPolarAngle = 0.35; ctrl.maxPolarAngle = 1.1; ctrl.autoRotate = true; ctrl.autoRotateSpeed = 0.5;
  ctrl.target.set(0, 0, -0.4);
  const pos0 = new THREE.Vector3(9.5, 15, 13.5);
  cam.position.copy(pos0);
  canvas.addEventListener('pointerdown', () => { ctrl.autoRotate = false; });

  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(); let sobre = null, sel = null;
  const pintar = () => pisos.forEach((m) => { const a = m.userData.amb; m.material.emissiveIntensity = a === sel ? 0.42 : a === sobre ? 0.2 : 0; });
  const pegar = (e) => { const r = canvas.getBoundingClientRect(); ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ptr, cam); const hit = ray.intersectObjects(pisos, false)[0]; return hit ? hit.object.userData.amb : null; };
  let arrastou = false, x0 = 0, y0 = 0;
  canvas.addEventListener('pointerdown', (e) => { arrastou = false; x0 = e.clientX; y0 = e.clientY; });
  canvas.addEventListener('pointermove', (e) => { if (Math.abs(e.clientX - x0) + Math.abs(e.clientY - y0) > 6) arrastou = true;
    if (e.pointerType !== 'mouse') return; const a = pegar(e); if (a !== sobre) { sobre = a; pintar(); canvas.style.cursor = a ? 'pointer' : 'grab'; } });
  canvas.addEventListener('pointerleave', () => { sobre = null; pintar(); });
  canvas.addEventListener('pointerup', (e) => { if (arrastou) return; const a = pegar(e); if (a) selecionar(a.id); });
  const selecionar = (id) => { sel = AMB.find((a) => a.id === id) || null; pintar(); aoSelecionar && aoSelecionar(sel); };

  const tamanho = () => { const w = canvas.clientWidth, h = canvas.clientHeight; renderer.setSize(w, h, false); cam.aspect = w / h;
    cam.fov = cam.aspect < 1 ? 46 : 32; cam.updateProjectionMatrix(); };
  addEventListener('resize', tamanho); tamanho();

  const v = new THREE.Vector3();
  let visivel = false;
  new IntersectionObserver(([e]) => { visivel = e.isIntersecting; if (visivel) requestAnimationFrame(loop); }, { rootMargin: '100px' }).observe(canvas);
  function loop() {
    if (!visivel) return;
    ctrl.update(); renderer.render(cena, cam);
    if (rotulo) { const a = sobre || sel; if (a) { v.copy(a.centro); v.y = 2.9; v.project(cam);
        rotulo.style.transform = `translate(${(v.x + 1) / 2 * canvas.clientWidth}px, ${(1 - v.y) / 2 * canvas.clientHeight}px) translate(-50%,-100%)`;
        rotulo.textContent = `${a.nome} · ${a.area.toFixed(1).replace('.', ',')} m²`; rotulo.classList.add('on'); } else rotulo.classList.remove('on'); }
    requestAnimationFrame(loop);
  }
  aoPronto && aoPronto(AMB);
  return { selecionar, ambientes: AMB, render: () => { ctrl.update(); renderer.render(cena, cam); } };
}
