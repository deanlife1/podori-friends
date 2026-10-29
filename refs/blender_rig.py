# 블렌더 헤드리스용: AI가 만든 GLB를 읽어 크기를 맞추고, 면을 줄이고, 뼈대를 자동 배치해 자동 가중치로 붙인 뒤 GLB로 내보낸다.
# 사용: blender -b --python rig.py -- <입력.glb> <출력.glb> <미리보기 폴더> [앞방향 회전 도]
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst, prev, views, name = argv[0], argv[1], argv[2], argv[3], argv[4]
face_yaw = float(argv[5]) if len(argv) > 5 else 0.0
import json, os
TARGET_FACES = 24000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = 'Character'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in list(bpy.data.objects):
    if o is not obj and o.type != 'MESH':
        bpy.data.objects.remove(o)

# 앞방향 보정(도) 후 정규화: 키 1m, 발바닥 z=0, 중심 x=y=0
if face_yaw:
    obj.rotation_euler.z = math.radians(face_yaw)
    bpy.ops.object.transform_apply(rotation=True)
def bounds():
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi
lo, hi = bounds()
s = 1.0 / (hi.z - lo.z)
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
lo, hi = bounds()
obj.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
bpy.ops.object.transform_apply(location=True)

# 면 줄이기 (UV는 유지)
if len(obj.data.polygons) > TARGET_FACES:
    mod = obj.modifiers.new('dec', 'DECIMATE')
    mod.ratio = TARGET_FACES / len(obj.data.polygons)
    bpy.ops.object.modifier_apply(modifier='dec')
print('faces', len(obj.data.polygons), 'verts', len(obj.data.vertices))

# 텍스처 축소 (웹 용량)
for img in bpy.data.images:
    if img.size[0] > 1024:
        img.scale(1024, 1024)


# ---- 그림 투영 베이크: 앞·뒤·좌·우 그림을 법선 방향에 따라 섞어 UV 텍스처로 굽는다 ----
bounds = json.load(open(os.path.join(views, 'bounds.json')))
mesh = obj.data
mx = max(abs(v.co.x) for v in mesh.vertices); my0 = min(v.co.y for v in mesh.vertices); my1 = max(v.co.y for v in mesh.vertices)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02); bpy.ops.object.mode_set(mode='OBJECT')
mat = bpy.data.materials.new('Proj'); mat.use_nodes = True; nt = mat.node_tree; nodes, links = nt.nodes, nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); bsdf = nodes.new('ShaderNodeBsdfPrincipled'); links.new(bsdf.outputs[0], out.inputs[0])
bsdf.inputs['Roughness'].default_value = 1.0
tc = nodes.new('ShaderNodeTexCoord'); sep = nodes.new('ShaderNodeSeparateXYZ'); links.new(tc.outputs['Object'], sep.inputs[0])
geo = nodes.new('ShaderNodeNewGeometry'); nsep = nodes.new('ShaderNodeSeparateXYZ'); links.new(geo.outputs['Normal'], nsep.inputs[0])
def mathn(op, a, b=None, val=None):
    n = nodes.new('ShaderNodeMath'); n.operation = op
    if isinstance(a, (int, float)): n.inputs[0].default_value = a
    else: links.new(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): n.inputs[1].default_value = b
        else: links.new(b, n.inputs[1])
    return n.outputs[0]
def maprange(sock, a, b, c, d):
    # 월드 [a,b] -> 이미지 [c,d]
    return mathn('ADD', mathn('MULTIPLY', mathn('SUBTRACT', sock, a), (d - c) / (b - a)), c)
def tex_node(path, u, v):
    img = bpy.data.images.load(path); t = nodes.new('ShaderNodeTexImage'); t.image = img; t.extension = 'EXTEND'
    comb = nodes.new('ShaderNodeCombineXYZ'); links.new(u, comb.inputs[0]); links.new(v, comb.inputs[1]); links.new(comb.outputs[0], t.inputs[0])
    return t.outputs['Color']
X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
NX, NY = nsep.outputs[0], nsep.outputs[1]
def vmap(key): b = bounds[key]; return maprange(Z, 0.0, 1.0, 1 - b[3], 1 - b[1])
bf = bounds[f'{name}_front']; bb = bounds[f'{name}_back']; bs = bounds[f'{name}_side']; br = bounds[f'{name}_side_r']
cF = tex_node(os.path.join(views, f'{name}_front_fill.png'), maprange(X, -mx, mx, bf[0], bf[2]), vmap(f'{name}_front'))
cB = tex_node(os.path.join(views, f'{name}_back_fill.png'), maprange(X, mx, -mx, bb[0], bb[2]), vmap(f'{name}_back'))
cL = tex_node(os.path.join(views, f'{name}_side_fill.png'), maprange(Y, my0, my1, bs[0], bs[2]), vmap(f'{name}_side'))
cR = tex_node(os.path.join(views, f'{name}_side_r_fill.png'), maprange(Y, my1, my0, br[0], br[2]), vmap(f'{name}_side_r'))
P = 3.0
wF = mathn('POWER', mathn('MAXIMUM', mathn('MULTIPLY', NY, -1.0), 0.0), P)
wB = mathn('POWER', mathn('MAXIMUM', NY, 0.0), P)
wL = mathn('POWER', mathn('MAXIMUM', mathn('MULTIPLY', NX, -1.0), 0.0), P)
wR = mathn('POWER', mathn('MAXIMUM', NX, 0.0), P)
wsum = mathn('ADD', mathn('ADD', wF, wB), mathn('ADD', mathn('ADD', wL, wR), 1e-4))
def mixc(a, b, fac):
    m = nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'; links.new(fac, m.inputs['Factor']); links.new(a, m.inputs[6]); links.new(b, m.inputs[7]); return m.outputs[2]
# 가중 평균을 순차 혼합으로: ((F*wF + B*wB)/(wF+wB) ...) 대신 누적 비율 혼합
acc = cF; accw = wF
for c, w in ((cB, wB), (cL, wL), (cR, wR)):
    neww = mathn('ADD', accw, w); acc = mixc(acc, c, mathn('DIVIDE', w, mathn('ADD', neww, 1e-4))); accw = neww
links.new(acc, bsdf.inputs['Base Color'])
bake_img = bpy.data.images.new('Baked_' + name, 1024, 1024); bn = nodes.new('ShaderNodeTexImage'); bn.image = bake_img; nodes.active = bn
mesh.materials.clear(); mesh.materials.append(mat)
scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
scene.render.bake.use_pass_direct = False; scene.render.bake.use_pass_indirect = False; scene.render.bake.use_pass_color = True
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.bake(type='DIFFUSE', margin=12)
bake_img.filepath_raw = os.path.join(prev, 'baked.png'); bake_img.file_format = 'PNG'; bake_img.save()
# 최종 재질: 구운 텍스처만 사용
final = bpy.data.materials.new('Fur'); final.use_nodes = True; fn = final.node_tree.nodes; fl = final.node_tree.links
fb = fn['Principled BSDF']; fb.inputs['Roughness'].default_value = 0.9
ft = fn.new('ShaderNodeTexImage'); ft.image = bake_img; fl.new(ft.outputs['Color'], fb.inputs['Base Color'])
mesh.materials.clear(); mesh.materials.append(final)
print('baked')

# ---- 뼈 위치 추정: 높이별 단면을 훑는다 ----
vs = [v.co.copy() for v in obj.data.vertices]
def slab(z0, z1):
    return [v for v in vs if z0 <= v.z < z1]
def width(z, h=0.02):
    sl = slab(z - h, z + h)
    return (max(v.x for v in sl) - min(v.x for v in sl)) if sl else 0.0
def has_gap(z, h=0.015):
    sl = slab(z - h, z + h)
    return bool(sl) and not any(abs(v.x) < 0.02 for v in sl)
zs = [i / 100 for i in range(2, 99)]
# 가랑이: 아래쪽에서 x=0 부근이 비는 가장 높은 단면
crotch = max([z for z in zs if z < 0.5 and has_gap(z)] or [0.2])
# 어깨: 몸통 중간 띠에서 가장 넓은 단면 (팔이 벌어진 높이)
mid = [z for z in zs if crotch + 0.05 < z < 0.8]
shoulder = max(mid, key=width)
arm_tip_x = max(abs(v.x) for v in vs)
tips = [v for v in vs if abs(v.x) > arm_tip_x * 0.85]
arm_tip_z = sum(v.z for v in tips) / len(tips)
# 몸통 반폭: 어깨 높이보다 조금 아래, 팔이 아직 안 나온 단면
torso_half = width(max(crotch + 0.04, shoulder - 0.12)) / 2
# 목: 어깨 위~머리 사이에서 가장 좁은 단면
upper = [z for z in zs if shoulder + 0.04 < z < 0.88]
neck = min(upper, key=width) if upper else shoulder + 0.1
top = max(v.z for v in vs)
# 다리 x: 가랑이 바로 아래 두 덩어리의 평균
legs = slab(crotch - 0.08, crotch - 0.02)
leg_x = sum(abs(v.x) for v in legs) / len(legs) if legs else torso_half * 0.5
# 앞뒤(y) 중심: 머리·몸통 단면의 평균
def yc(z, h=0.03):
    sl = slab(z - h, z + h); return sum(v.y for v in sl) / len(sl) if sl else 0.0
print(dict(crotch=crotch, shoulder=shoulder, neck=neck, top=top, torso_half=torso_half, arm_tip=(arm_tip_x, arm_tip_z), leg_x=leg_x))

# 귀: 머리 위쪽 바깥 덩어리
head_half = width((neck + top) / 2) / 2
ears = {}
for sgn, nm in ((-1, 'L'), (1, 'R')):
    ev = [v for v in vs if v.z > top - 0.14 and sgn * v.x > head_half * 0.5]
    if len(ev) > 20:
        c = sum((v for v in ev), Vector()) / len(ev)
        ears[nm] = c
# 꼬리: 몸통 뒤(+y)로 빠져나온 덩어리
body_back = max(v.y for v in slab(crotch, shoulder) if abs(v.x) < torso_half * 0.6)
tail_v = [v for v in vs if v.y > body_back + 0.03 and v.z < shoulder + 0.1]
tail_chain = []
if len(tail_v) > 40:
    tail_v.sort(key=lambda v: v.y)
    n = 3
    for i in range(n):
        seg = tail_v[i * len(tail_v) // n:(i + 1) * len(tail_v) // n]
        tail_chain.append(sum((v for v in seg), Vector()) / len(seg))
print('ears', ears, 'tail', tail_chain)

# ---- 뼈대 만들기 ----
arm_data = bpy.data.armatures.new('Rig')
arm = bpy.data.objects.new('Rig', arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name); b.head = head; b.tail = tail
    if parent: b.parent = eb[parent]; b.use_connect = connect
    return b
yb = yc((crotch + shoulder) / 2)
bone('Root', (0, 0, 0), (0, -0.1, 0))
bone('Hips', (0, yb, crotch), (0, yb, crotch + (neck - crotch) * 0.45), 'Root')
bone('Chest', (0, yb, crotch + (neck - crotch) * 0.45), (0, yb, neck), 'Hips', True)
bone('Head', (0, yc((neck + top) / 2), neck), (0, yc((neck + top) / 2), top), 'Chest')
for sgn, nm in ((-1, 'L'), (1, 'R')):
    bone('UpperArm.' + nm, (sgn * torso_half * 0.85, yc(shoulder), shoulder), (sgn * arm_tip_x, yc(shoulder), arm_tip_z), 'Chest')
    bone('Thigh.' + nm, (sgn * leg_x, yc(crotch - 0.05), crotch + 0.01), (sgn * leg_x, yc(crotch - 0.05), 0.0), 'Hips')
    if nm in ears:
        c = ears[nm]; bone('Ear.' + nm, (c.x, c.y, c.z - 0.06), (c.x, c.y, c.z + 0.06), 'Head')
prev_name = 'Hips'
for i, c in enumerate(tail_chain):
    start = Vector((0, body_back, crotch + 0.06)) if i == 0 else tail_chain[i - 1]
    bone(f'Tail{i + 1}', start, c, prev_name, i > 0); prev_name = f'Tail{i + 1}'
bpy.ops.object.mode_set(mode='OBJECT')

# 자동 가중치로 붙이기
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('rigged, bones:', [b.name for b in arm_data.bones])

# ---- 미리보기 렌더 (앞·옆) ----
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.film_transparent = False
cam_data = bpy.data.cameras.new('Cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 1.3
cam = bpy.data.objects.new('Cam', cam_data); bpy.context.collection.objects.link(cam); scene.camera = cam
for nm, loc, rot in (('front', (0, -5, 0.5), (90, 0, 0)), ('side', (5, 0, 0.5), (90, 0, 90)), ('back', (0, 5, 0.5), (90, 0, 180))):
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    scene.render.filepath = f'{prev}/{nm}.png'
    bpy.ops.render.render(write_still=True)

# ---- 내보내기 ----
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); arm.select_set(True)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=True, export_skins=True, export_animations=False,
                          export_image_format='JPEG', export_jpeg_quality=85, export_apply=True, export_yup=True)
print('exported', dst)
