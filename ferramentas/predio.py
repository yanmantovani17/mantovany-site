"""Ciclo de vida de um prédio: projeto em linhas -> fundação -> estrutura com grua -> fachada -> pronto ao entardecer.
Uso: python predio.py <saida> [quadros|all|save] [escala%] [amostras]
"""
import bpy, bmesh, math, random, sys, os, time
from mathutils import Vector

a = sys.argv[1:]
SAIDA = a[0] if a else '/tmp/p'
QUAIS = a[1] if len(a) > 1 else 'all'
ESCALA = int(a[2]) if len(a) > 2 else 100
AMOSTRAS = int(a[3]) if len(a) > 3 else 12
FIM = 96
random.seed(4)

bpy.ops.wm.read_factory_settings(use_empty=True)
C = bpy.context.scene
C.frame_start, C.frame_end = 1, FIM

# ---------------- utilidades ----------------
def no(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k.startswith('i_'): n.inputs[k[2:].replace('_', ' ')].default_value = v
        else: setattr(n, k, v)
    return n

def mat_base(nome, cor, rug=0.6, metal=0.0, ruido=0.0, escala=4.0, trans=0.0, ior=1.45, emis=None, forca=0.0):
    m = bpy.data.materials.new(nome); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1); b.inputs['Roughness'].default_value = rug; b.inputs['Metallic'].default_value = metal
    if trans: b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    if emis: b.inputs['Emission Color'].default_value = (*emis, 1); b.inputs['Emission Strength'].default_value = forca
    if ruido:
        co = no(nt, 'ShaderNodeTexCoord'); n = no(nt, 'ShaderNodeTexNoise', i_Scale=escala, i_Detail=8.0)
        nt.links.new(co.outputs['Object'], n.inputs['Vector'])
        r = no(nt, 'ShaderNodeValToRGB')
        r.color_ramp.elements[0].color = (*[c * (1 - ruido) for c in cor], 1); r.color_ramp.elements[1].color = (*cor, 1)
        nt.links.new(n.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
        bp = no(nt, 'ShaderNodeBump', i_Strength=0.15); n2 = no(nt, 'ShaderNodeTexNoise', i_Scale=escala * 12)
        nt.links.new(co.outputs['Object'], n2.inputs['Vector']); nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def mat_emissao(nome, cor, forca):
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*cor, 1); e.inputs['Strength'].default_value = forca
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m, e

def caixa(nome, sx, sy, sz, x, y, z, m, base=True):
    """caixa com origem na base (para crescer para cima)"""
    me = bpy.data.meshes.new(nome); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector((v.co.x * sx, v.co.y * sy, (v.co.z + 0.5) * sz if base else v.co.z * sz))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nome, me); ob.location = (x, y, z); C.collection.objects.link(ob)
    if m: ob.data.materials.append(m)
    return ob

def surgir(ob, q, dur=3, esc=True):
    """objeto invisível antes do quadro q; cresce do chão em 'dur' quadros"""
    ob.hide_render = True; ob.keyframe_insert('hide_render', frame=max(1, q - 1))
    ob.hide_render = False; ob.keyframe_insert('hide_render', frame=q)
    if esc:
        ob.scale = (1, 1, 0.02); ob.keyframe_insert('scale', frame=q)
        ob.scale = (1, 1, 1); ob.keyframe_insert('scale', frame=q + dur)

def sumir(ob, q):
    ob.hide_render = False; ob.keyframe_insert('hide_render', frame=max(1, q - 1))
    ob.hide_render = True; ob.keyframe_insert('hide_render', frame=q)

# ---------------- materiais ----------------
M_CONC = mat_base('concreto', (0.42, 0.41, 0.4), 0.85, ruido=0.35, escala=3)
M_REBOCO = mat_base('reboco', (0.74, 0.72, 0.69), 0.65, ruido=0.08, escala=2)
M_VIDRO = mat_base('vidro', (0.55, 0.62, 0.66), 0.03, trans=1.0, ior=1.5)
M_METAL = mat_base('metal', (0.04, 0.045, 0.05), 0.35, metal=0.9)
M_MADEIRA = mat_base('madeira', (0.42, 0.24, 0.12), 0.55, ruido=0.4, escala=9)
M_GRAMA = mat_base('grama', (0.09, 0.14, 0.045), 0.95, ruido=0.55, escala=0.35)
M_TERRA = mat_base('terra', (0.33, 0.22, 0.14), 0.95, ruido=0.5, escala=0.8)
M_PISO = mat_base('piso_ext', (0.55, 0.53, 0.5), 0.7, ruido=0.2, escala=1.5)
M_GRUA = mat_base('grua', (0.85, 0.45, 0.02), 0.45, metal=0.3)
M_FOLHA = mat_base('folha', (0.12, 0.22, 0.07), 0.8, ruido=0.6, escala=6)
M_TRONCO = mat_base('tronco', (0.18, 0.12, 0.08), 0.9)
M_VIZ = mat_base('vizinho', (0.42, 0.42, 0.42), 0.8, ruido=0.25)
M_LINHA, _ = mat_emissao('projeto', (1.0, 0.62, 0.16), 2.6)
M_LUZ, E_LUZ = mat_emissao('luz_interna', (1.0, 0.58, 0.26), 0.0)
M_LUZ2, E_LUZ2 = mat_emissao('luz_interna2', (1.0, 0.66, 0.36), 0.0)

# ---------------- terreno e entorno ----------------
grama = caixa('grama', 600, 600, 0.1, 0, 0, -0.1, M_GRAMA)
terra = caixa('canteiro', 34, 28, 0.05, 0, 0, -0.02, M_TERRA)
piso = caixa('calcada', 34, 28, 0.05, 0, 0, -0.01, M_PISO); piso.hide_render = True
for q in (1,): piso.keyframe_insert('hide_render', frame=1)
surgir(piso, 80, esc=False); sumir(terra, 80)
# rua
caixa('rua', 600, 9, 0.04, 0, -21, -0.03, mat_base('asfalto', (0.05, 0.05, 0.055), 0.8, ruido=0.3, escala=2))
# árvores ao redor
def arvore(x, y, s=1.0):
    t = caixa('tronco', 0.35 * s, 0.35 * s, 3.2 * s, x, y, 0, M_TRONCO)
    obs = [t]
    for k in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=random.uniform(1.6, 2.4) * s, location=(x + random.uniform(-0.8, 0.8) * s, y + random.uniform(-0.8, 0.8) * s, (3.4 + k * 0.9) * s))
        f = bpy.context.object; f.data.materials.append(M_FOLHA)
        for v in f.data.vertices: v.co *= random.uniform(0.8, 1.2)
        for p in f.data.polygons: p.use_smooth = True
        obs.append(f)
    return obs
for i in range(26):
    ang = random.uniform(0, 6.28); r = random.uniform(24, 60)
    x, y = math.cos(ang) * r, math.sin(ang) * r
    if -27 < y < -15: continue  # não plantar na rua
    arvore(x, y, random.uniform(0.9, 1.4))
paisagismo = []
for (x, y) in ((-15, -9), (15, -9), (-15, 4), (15, 4)):
    for o in arvore(x, y, 0.75): paisagismo.append(o)
for o in paisagismo: surgir(o, 80, esc=False)
# prédios vizinhos ao fundo, com janelas acesas
M_JAN = bpy.data.materials.new('janelas_viz'); M_JAN.use_nodes = True
nt = M_JAN.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.2, 0.2, 0.21, 1); b.inputs['Roughness'].default_value = 0.7
co = no(nt, 'ShaderNodeTexCoord'); tij = no(nt, 'ShaderNodeTexBrick', i_Scale=0.35, i_Mortar_Size=0.11, offset=0.0)
tij.inputs['Color1'].default_value = (1, 0.72, 0.4, 1); tij.inputs['Color2'].default_value = (0.02, 0.02, 0.03, 1); tij.inputs['Mortar'].default_value = (0, 0, 0, 1)
tb = no(nt, 'ShaderNodeTexBrick', i_Scale=0.35, i_Mortar_Size=0.11, offset=0.0)
tb.inputs['Color1'].default_value = (0.04, 0.05, 0.06, 1); tb.inputs['Color2'].default_value = (0.04, 0.05, 0.06, 1); tb.inputs['Mortar'].default_value = (0.22, 0.215, 0.21, 1)
nt.links.new(co.outputs['Object'], tb.inputs['Vector']); nt.links.new(tb.outputs['Color'], b.inputs['Base Color'])
nt.links.new(co.outputs['Object'], tij.inputs['Vector'])
ruid = no(nt, 'ShaderNodeTexNoise', i_Scale=1.3); nt.links.new(co.outputs['Object'], ruid.inputs['Vector'])
msk = no(nt, 'ShaderNodeMath', operation='GREATER_THAN'); msk.inputs[1].default_value = 0.56; nt.links.new(ruid.outputs['Fac'], msk.inputs[0])
mx = no(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs['A'].default_value = (0, 0, 0, 1)
nt.links.new(msk.outputs[0], mx.inputs['Factor']); nt.links.new(tij.outputs['Color'], mx.inputs['B'])
nt.links.new(mx.outputs['Result'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 0.0
EMV = b.inputs['Emission Strength']; EMV.keyframe_insert('default_value', frame=70); EMV.default_value = 0.9; EMV.keyframe_insert('default_value', frame=FIM)
for i in range(22):
    ang = random.uniform(0.35, 2.8); r = random.uniform(120, 220)
    caixa('viz', random.uniform(14, 24), random.uniform(14, 22), random.uniform(10, 40), math.cos(ang) * r, math.sin(ang) * r, 0, M_JAN)

# ---------------- o prédio ----------------
N, H, W, D = 8, 3.1, 18.0, 13.0
XS, YS = [-8.6, -4.3, 0, 4.3, 8.6], [-6.1, 0, 6.1]
T_FUND = 14
def t_andar(k): return 18 + (k - 1) * 5     # quadro em que surgem os pilares do andar k (1..N)
def t_fach(k): return 56 + k * 2.3          # quadro em que surge a fachada do andar k (0..N-1)

# fantasma do projeto (linhas douradas) por andar
def fantasma(k):
    me = bpy.data.meshes.new('fant'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=5, use_grid_fill=True)
    for v in bm.verts: v.co = Vector((v.co.x * W, v.co.y * D, (v.co.z + 0.5) * H))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('fantasma', me); ob.location = (0, 0, k * H); C.collection.objects.link(ob)
    w = ob.modifiers.new('w', 'WIREFRAME'); w.thickness = 0.045; w.use_replace = True
    ob.data.materials.append(M_LINHA)
    return ob
for k in range(N):
    f = fantasma(k)
    f.hide_render = True; f.keyframe_insert('hide_render', frame=1)
    f.hide_render = False; f.keyframe_insert('hide_render', frame=2 + k)      # o projeto se desenha de baixo para cima
    sumir(f, t_andar(k + 1) + 3)
# planta no chão (linhas)
planta = caixa('planta', W + 6, D + 6, 0.01, 0, 0, 0.02, M_LINHA)
pm = planta.modifiers.new('w', 'WIREFRAME'); pm.thickness = 0.06
bpy.context.view_layer.objects.active = planta
me = planta.data; bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True); bm.to_mesh(me); bm.free()
sumir(planta, T_FUND + 2)

# fundação
fund = caixa('fundacao', W + 1, D + 1, 0.5, 0, 0, -0.45, M_CONC); surgir(fund, T_FUND, 3)
# andares: pilares + laje
for k in range(1, N + 1):
    q = t_andar(k); z0 = (k - 1) * H
    for x in XS:
        for y in YS:
            p = caixa('pilar', 0.45, 0.45, H - 0.28, x, y, z0 + (0.05 if k == 1 else 0), M_CONC); surgir(p, q, 3)
    laje = caixa('laje', W, D, 0.28, 0, 0, k * H - 0.28, M_CONC); surgir(laje, q + 3, 2)
    if k < N:  # sacada na frente
        sac = caixa('sacada', W - 1.0, 1.8, 0.22, 0, -D / 2 - 0.9, k * H - 0.22, M_CONC); surgir(sac, q + 4, 2)
        forro = caixa('forro_madeira', W - 1.2, 1.7, 0.03, 0, -D / 2 - 0.9, k * H - 0.25, M_MADEIRA); surgir(forro, t_fach(k), 2, esc=False)
# esperas de vergalhão no topo enquanto a obra sobe
M_ACO = mat_base('aco', (0.35, 0.16, 0.07), 0.7, metal=0.4)
for k in range(1, N):
    for x in XS:
        for y in YS:
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.05, depth=1.0, location=(x, y, k * H + 0.5))
            v = bpy.context.object; v.data.materials.append(M_ACO)
            surgir(v, t_andar(k) + 3, 1, esc=False); sumir(v, t_andar(k + 1))

# fachada e acabamento por andar
def fachada(k):
    z = k * H + (0.05 if k == 0 else 0); h = H - 0.28 - (0.05 if k == 0 else 0); q = t_fach(k); obs = []
    # frente: vidro + caixilhos
    g = caixa('vidro_frente', W - 0.8, 0.04, h, 0, -D / 2 + 0.25, z, M_VIDRO); obs.append(g)
    mul = caixa('montante', 0.07, 0.12, h, -W / 2 + 0.4, -D / 2 + 0.22, z, M_METAL)
    ar = mul.modifiers.new('a', 'ARRAY'); ar.count = 12; ar.relative_offset_displace = (0, 0, 0); ar.use_relative_offset = False; ar.use_constant_offset = True; ar.constant_offset_displace = ((W - 0.8) / 11, 0, 0)
    obs.append(mul)
    # fundos: vidro também
    obs.append(caixa('vidro_fundo', W - 0.8, 0.04, h, 0, D / 2 - 0.25, z, M_VIDRO))
    # laterais: reboco branco com faixa de janela
    for sx in (-1, 1):
        obs.append(caixa('parede_lat', 0.25, D - 0.3, h, sx * (W / 2 - 0.12), 0, z, M_REBOCO))
        obs.append(caixa('jan_lat', 0.06, 2.4, h * 0.6, sx * (W / 2 + 0.02), -2.5, z + h * 0.22, M_VIDRO))
    # guarda-corpo de vidro na sacada
    if k > 0:
        obs.append(caixa('guarda', W - 1.0, 0.03, 1.05, 0, -D / 2 - 1.75, z, M_VIDRO))
        obs.append(caixa('corrimao', W - 1.0, 0.06, 0.05, 0, -D / 2 - 1.75, z + 1.05, M_METAL))
    # luz interna (apartamentos), divididos em 4 unidades
    for u in range(4):
        mat = M_LUZ if random.random() < 0.6 else M_LUZ2
        lz = caixa('luz', (W - 1.4) / 4 - 0.3, 0.02, h - 0.4, -W / 2 + 0.7 + (u + 0.5) * (W - 1.4) / 4, -D / 2 + 1.6, z + 0.2, mat)
        obs.append(lz)
        if random.random() < 0.3: lz.data.materials[0] = M_REBOCO  # unidade apagada
    for o in obs: surgir(o, q, 2, esc=False)
for k in range(N): fachada(k)
# platibanda + pergolado na cobertura
pl = caixa('platibanda', W, D, 1.1, 0, 0, N * H, M_REBOCO); surgir(pl, t_fach(N - 1) + 2, 2)
oc = caixa('platibanda_oca', W - 0.5, D - 0.5, 1.2, 0, 0, N * H + 0.1, None)
bo = pl.modifiers.new('b', 'BOOLEAN'); bo.object = oc; bo.operation = 'DIFFERENCE'; oc.hide_render = True; oc.hide_viewport = True
for i in range(9):
    r = caixa('pergolado', 0.12, 5.0, 0.25, -4 + i * 1.0, -2, N * H + 2.6, M_MADEIRA); surgir(r, t_fach(N - 1) + 3, 2, esc=False)

# ---------------- grua ----------------
grua = []
GX, GY = W / 2 + 5, D / 2 - 1
ALT = N * H + 9
def trelica(nome, sx, sy, sz, x, y, z, cortes, base=True):
    ob = caixa(nome, sx, sy, sz, x, y, z, M_GRUA, base)
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me)
    eixo = 2 if sz >= max(sx, sy) else 0   # subdivide só ao longo do comprimento
    longas = [e for e in bm.edges if abs(e.verts[0].co[eixo] - e.verts[1].co[eixo]) > 0.5 * max(sx, sy, sz)]
    bmesh.ops.subdivide_edges(bm, edges=longas, cuts=cortes, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    w = ob.modifiers.new('w', 'WIREFRAME'); w.thickness = 0.09; w.use_even_offset = False
    return ob
mast = trelica('mastro', 1.6, 1.6, ALT, GX, GY, 0, int(ALT / 1.6))
grua.append(mast)
pivo = bpy.data.objects.new('pivo', None); pivo.location = (GX, GY, ALT); C.collection.objects.link(pivo)
lanca = trelica('lanca', 34, 1.2, 1.3, -12, 0, 0, 24); lanca.parent = pivo
topo = trelica('torre_topo', 1.2, 1.2, 4.5, 0, 0, 0, 3); topo.parent = pivo
cab = caixa('cabine', 2.0, 1.8, 2.0, 1.6, 0, -2.0, M_GRUA); cab.parent = pivo
contra = caixa('contrapeso', 3, 1.8, 1.6, 7.5, 0, -0.3, M_CONC); contra.parent = pivo
cabo = caixa('cabo', 0.04, 0.04, 12, -20, 0, -12, M_METAL); cabo.parent = pivo
carga = caixa('carga', 2.5, 1.2, 0.5, -20, 0, -12.5, M_MADEIRA); carga.parent = pivo
grua += [topo]
grua += [lanca, cab, contra, cabo, carga]
for o in grua:
    o.hide_render = True; o.keyframe_insert('hide_render', frame=1)
    o.hide_render = False; o.keyframe_insert('hide_render', frame=T_FUND + 2)
    sumir(o, 76)
pivo.rotation_euler = (0, 0, 0.3); pivo.keyframe_insert('rotation_euler', frame=16)
pivo.rotation_euler = (0, 0, -1.4); pivo.keyframe_insert('rotation_euler', frame=74)

# luzes internas acendem no fim
for e in (E_LUZ, E_LUZ2):
    e.inputs['Strength'].default_value = 0.0; e.inputs['Strength'].keyframe_insert('default_value', frame=76)
    e.inputs['Strength'].default_value = 2.6; e.inputs['Strength'].keyframe_insert('default_value', frame=88)

# ---------------- céu (entardecer) ----------------
mundo = bpy.data.worlds.new('ceu'); C.world = mundo; mundo.use_nodes = True
nt = mundo.node_tree; bg = nt.nodes['Background']
sky = no(nt, 'ShaderNodeTexSky', sky_type='NISHITA', sun_elevation=math.radians(14), sun_rotation=math.radians(205), altitude=200, air_density=1.2, dust_density=2.5)
nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.35
sky.keyframe_insert('sun_elevation', frame=1)
sky.sun_elevation = math.radians(1.2); sky.keyframe_insert('sun_elevation', frame=FIM)
bg.inputs['Strength'].keyframe_insert('default_value', frame=60)
bg.inputs['Strength'].default_value = 0.3; bg.inputs['Strength'].keyframe_insert('default_value', frame=FIM)
sol = bpy.data.lights.new('sol', 'SUN'); sol.energy = 2.2; sol.color = (1.0, 0.72, 0.45); sol.angle = math.radians(2)
so = bpy.data.objects.new('sol', sol); C.collection.objects.link(so); so.rotation_euler = (math.radians(76), 0, math.radians(205 - 180 + 90))
sol.keyframe_insert('energy', frame=60); sol.energy = 0.6; sol.keyframe_insert('energy', frame=FIM)

# ---------------- câmera ----------------
cd = bpy.data.cameras.new('cam'); cd.lens = 32; cd.clip_end = 1000
cam = bpy.data.objects.new('cam', cd); C.collection.objects.link(cam); C.camera = cam
alvo = bpy.data.objects.new('alvo', None); C.collection.objects.link(alvo)
tc = cam.constraints.new('TRACK_TO'); tc.target = alvo; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
for q, pc, pa in [(1, (55, -80, 95), (0, 0, 6)), (16, (38, -52, 34), (0, 0, 8)), (44, (-6, -58, 24), (0, 0, 11)), (72, (-40, -40, 20), (0, 0, 12)), (FIM, (-30, -52, 11), (0, 0, 12))]:
    cam.location = pc; cam.keyframe_insert('location', frame=q); alvo.location = pa; alvo.keyframe_insert('location', frame=q)

# ---------------- render ----------------
r = C.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1600, 900, ESCALA
cy = C.cycles; cy.device = 'CPU'; cy.samples = AMOSTRAS; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.transmission_bounces = 3; cy.transparent_max_bounces = 3; cy.volume_bounces = 0
cy.caustics_reflective = cy.caustics_refractive = False; cy.blur_glossy = 1.0
C.view_settings.view_transform = 'AgX'; C.view_settings.look = 'AgX - Medium High Contrast'; C.view_settings.exposure = -0.6
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.use_persistent_data = True
C.use_nodes = True; ntc = C.node_tree
for n in list(ntc.nodes): ntc.nodes.remove(n)
rl = ntc.nodes.new('CompositorNodeRLayers'); comp = ntc.nodes.new('CompositorNodeComposite')
gl = ntc.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.threshold = 1.0; gl.size = 7; gl.mix = -0.8
ntc.links.new(rl.outputs['Image'], gl.inputs['Image']); ntc.links.new(gl.outputs['Image'], comp.inputs['Image'])

if QUAIS == 'save':
    bpy.ops.wm.save_as_mainfile(filepath=SAIDA)
else:
    os.makedirs(SAIDA, exist_ok=True)
    quadros = range(1, FIM + 1) if QUAIS == 'all' else [int(x) for x in QUAIS.split(',')]
    for q in quadros:
        arq = f'{SAIDA}/q{q:04d}.png'
        if os.path.exists(arq): continue
        t0 = time.time(); C.frame_set(q); r.filepath = arq
        bpy.ops.render.render(write_still=True)
        print(f'quadro {q} em {time.time() - t0:.1f}s', flush=True)
