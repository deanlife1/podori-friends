# 알프스 마을 소품을 블렌더로 생성해 하나의 GLB로 내보낸다 (정점 색으로 칠함, 외부 텍스처 없음)
# 사용: blender -b --python alps_assets.py -- <출력.glb>
import bpy, sys, math, random
from mathutils import Vector, Euler

out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(7)

mat = bpy.data.materials.new('Painted'); mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value = 0.85
vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])

parts = {}  # 이름 -> [메시 오브젝트들]
def add(name, obj, color, jitter=0.06):
    me = obj.data
    if not me.vertex_colors: me.vertex_colors.new(name='Col')
    col = me.vertex_colors['Col']
    for poly in me.polygons:
        k = 1 + random.uniform(-jitter, jitter)
        for li in poly.loop_indices:
            col.data[li].color = (color[0] * k, color[1] * k, color[2] * k, 1)
    me.materials.clear(); me.materials.append(mat)
    parts.setdefault(name, []).append(obj)
    return obj

def box(name, color, size, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return add(name, o, color)
def prism(name, color, w, d, h, loc, rot=(0, 0, 0)):
    # 지붕용 삼각 프리즘(길이 d, 폭 w, 높이 h)
    verts = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (0, -d / 2, h), (-w / 2, d / 2, 0), (w / 2, d / 2, 0), (0, d / 2, h)]
    faces = [(0, 1, 2), (5, 4, 3), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return add(name, o, color)
def cyl(name, color, r, h, loc, rot=(0, 0, 0), seg=12, r2=None):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r, radius2=r if r2 is None else r2, depth=h, location=loc, rotation=rot)
    return add(name, bpy.context.object, color)
def ball(name, color, r, loc, scale=(1, 1, 1), seg=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(6, seg // 2), radius=r, location=loc)
    o = bpy.context.object; o.scale = scale; bpy.ops.object.transform_apply(scale=True)
    return add(name, o, color)
def cone(name, color, r, h, loc, seg=16):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r, radius2=0, depth=h, location=loc)
    return add(name, bpy.context.object, color)

WOOD = (0.42, 0.26, 0.14); WOOD_D = (0.3, 0.18, 0.1); CREAM = (0.93, 0.87, 0.74); ROOF = (0.35, 0.2, 0.13)
STONE = (0.62, 0.6, 0.56); WHITE = (0.95, 0.95, 0.93); GREEN = (0.3, 0.5, 0.22); RED = (0.8, 0.2, 0.18); PINK = (0.95, 0.5, 0.6)
YELLOW = (0.95, 0.8, 0.3); HAY = (0.85, 0.7, 0.35); BLACK = (0.1, 0.09, 0.09); COW = (0.95, 0.93, 0.9); SHEEP = (0.96, 0.95, 0.9)

# ---- 샬레: 돌 기단 + 통나무 벽 + 큰 경사 지붕 + 발코니 + 창문 + 꽃화분 ----
def chalet(name, w=6, d=7, floors=2):
    h = 2.6 * floors
    box(name, STONE, (w + 0.2, d + 0.2, 0.8), (0, 0, 0.4))
    box(name, WOOD, (w, d, h - 0.8), (0, 0, 0.8 + (h - 0.8) / 2))
    for i in range(int((h - 0.8) / 0.35)):  # 통나무 줄
        z = 0.8 + 0.175 + i * 0.35
        box(name, WOOD_D, (w + 0.08, 0.06, 0.05), (0, -d / 2, z)); box(name, WOOD_D, (w + 0.08, 0.06, 0.05), (0, d / 2, z))
    prism(name, ROOF, w + 1.6, d + 1.2, 2.4, (0, 0, h))
    prism(name, CREAM, w - 0.05, d - 0.3, 2.3, (0, 0, h + 0.02))  # 박공 벽
    # 발코니
    box(name, WOOD, (w + 0.4, 1.0, 0.12), (0, -d / 2 - 0.5, 2.6));
    for x in [-w / 2 + 0.2 + i * 0.4 for i in range(int(w / 0.4))]:
        box(name, WOOD_D, (0.08, 0.08, 0.9), (x, -d / 2 - 0.95, 3.05))
    box(name, WOOD, (w + 0.4, 0.08, 0.08), (0, -d / 2 - 0.95, 3.5))
    # 창문·덧창·꽃화분
    for fl in range(floors):
        for x in (-w / 4, w / 4):
            z = 0.8 + 1.4 + fl * 2.6
            box(name, (0.55, 0.75, 0.9), (0.9, 0.06, 1.0), (x, -d / 2 - 0.01, z))
            box(name, WHITE, (1.05, 0.05, 0.08), (x, -d / 2 - 0.05, z + 0.5)); box(name, WHITE, (1.05, 0.05, 0.08), (x, -d / 2 - 0.05, z - 0.5))
            box(name, GREEN, (0.3, 0.05, 1.0), (x - 0.65, -d / 2 - 0.04, z)); box(name, GREEN, (0.3, 0.05, 1.0), (x + 0.65, -d / 2 - 0.04, z))
            box(name, WOOD_D, (1.0, 0.3, 0.25), (x, -d / 2 - 0.2, z - 0.65))
            for k in range(5): ball(name, random.choice([RED, PINK, YELLOW]), 0.12, (x - 0.4 + k * 0.2, -d / 2 - 0.22, z - 0.45), seg=8)
    box(name, WOOD_D, (1.0, 0.1, 2.0), (0, -d / 2 - 0.02, 1.8))  # 문
    cyl(name, STONE, 0.35, 1.5, (w / 4, d / 4, h + 1.6), seg=8)  # 굴뚝
    return name

# ---- 교회: 돌벽 + 종탑 + 뾰족 지붕 + 종 ----
def church(name):
    w, d, h = 7, 11, 5
    box(name, WHITE, (w, d, h), (0, 0, h / 2)); box(name, STONE, (w + 0.2, d + 0.2, 0.6), (0, 0, 0.3))
    prism(name, ROOF, w + 1.0, d + 0.8, 2.6, (0, 0, h))
    tw = 3.2; box(name, WHITE, (tw, tw, 11), (0, -d / 2 - tw / 2 + 0.3, 5.5))
    cone(name, ROOF, tw * 0.85, 4.5, (0, -d / 2 - tw / 2 + 0.3, 11 + 2.25), seg=4)
    ball(name, YELLOW, 0.35, (0, -d / 2 - tw / 2 + 0.3, 9.4), seg=8)
    for s in (-1, 1): box(name, BLACK, (0.8, 0.1, 1.4), (s * 0.7, -d / 2 - tw + 0.25, 9.3))
    for k in range(4): box(name, (0.4, 0.55, 0.85), (0.05, 0.9, 2.2), (w / 2 + 0.01, -d / 2 + 2 + k * 2.4, 3)); box(name, (0.4, 0.55, 0.85), (0.05, 0.9, 2.2), (-w / 2 - 0.01, -d / 2 + 2 + k * 2.4, 3))
    box(name, WOOD_D, (1.4, 0.1, 2.6), (0, -d / 2 - tw + 0.24, 1.3))
    cyl(name, YELLOW, 0.06, 1.2, (0, -d / 2 - tw / 2 + 0.3, 16.0), seg=6); box(name, YELLOW, (0.6, 0.06, 0.06), (0, -d / 2 - tw / 2 + 0.3, 16.3))
    return name

# ---- 울타리 한 칸(2m), 물레방아, 건초더미, 이정표, 버섯집, 소, 양, 야생화 덩어리 ----
def fence(name):
    for x in (-1, 1): box(name, WOOD, (0.14, 0.14, 1.2), (x, 0, 0.6))
    for z in (0.5, 0.95): box(name, WOOD_D, (2.1, 0.08, 0.12), (0, 0, z))
    return name
def waterwheel(name):
    bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.18, major_segments=24, minor_segments=8, location=(0, 0, 2.4), rotation=(0, math.radians(90), 0))
    add(name, bpy.context.object, WOOD_D)
    for k in range(10):
        a = k * math.pi * 2 / 10
        box(name, WOOD, (0.12, 0.12, 4.2), (0, 0, 2.4), (a, 0, 0))
        box(name, WOOD, (0.9, 0.6, 0.06), (0, math.sin(a) * 2.2, 2.4 + math.cos(a) * 2.2), (a, 0, 0))
    box(name, STONE, (1.6, 2.4, 2.6), (1.6, 0, 1.3)); prism(name, ROOF, 2.2, 3.0, 1.2, (1.6, 0, 2.6))
    cyl(name, WOOD_D, 0.15, 2.6, (0.5, 0, 2.4), rot=(0, math.radians(90), 0), seg=8)
    return name
def haystack(name):
    cone(name, HAY, 1.8, 2.6, (0, 0, 1.3), seg=14); cyl(name, WOOD_D, 0.08, 3.2, (0, 0, 1.6), seg=6)
    return name
def signpost(name):
    cyl(name, WOOD_D, 0.1, 2.6, (0, 0, 1.3), seg=8)
    for k, z in enumerate((2.3, 1.9, 1.5)):
        box(name, WOOD, (1.3, 0.08, 0.3), (0.55 * (1 if k % 2 == 0 else -1), 0, z), (0, 0, k * 0.5))
    return name
def mushroom_house(name):
    cyl(name, CREAM, 2.0, 3.0, (0, 0, 1.5), seg=18, r2=1.7)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=3.2, location=(0, 0, 2.6))
    cap = bpy.context.object; cap.scale = (1, 1, 0.62); bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.bisect(plane_co=(0, 0, 2.6), plane_no=(0, 0, -1), clear_inner=True); bpy.ops.object.mode_set(mode='OBJECT')
    add(name, cap, RED)
    for k in range(9):
        a = random.uniform(0, 6.28); r = random.uniform(0.6, 2.6); z = 2.6 + math.sqrt(max(0, 1 - (r / 3.2) ** 2)) * 3.2 * 0.62
        ball(name, WHITE, random.uniform(0.25, 0.45), (math.cos(a) * r, math.sin(a) * r, z - 0.1), scale=(1, 1, 0.5), seg=10)
    box(name, WOOD_D, (0.9, 0.1, 1.6), (0, -1.95, 0.8)); ball(name, YELLOW, 0.08, (0.3, -2.02, 0.8), seg=6)
    box(name, (0.55, 0.75, 0.9), (0.7, 0.1, 0.7), (1.5, -1.3, 1.8), (0, 0, 0.7)); box(name, (0.55, 0.75, 0.9), (0.7, 0.1, 0.7), (-1.5, -1.3, 1.8), (0, 0, -0.7))
    cyl(name, STONE, 0.22, 1.2, (0.9, 0.9, 4.2), seg=8)
    return name
def cow(name):
    ball(name, COW, 1.0, (0, 0, 1.25), scale=(0.75, 1.3, 0.75))
    for k in range(5): ball(name, BLACK, random.uniform(0.25, 0.45), (random.uniform(-0.6, 0.6), random.uniform(-1.0, 1.0), 1.25 + random.uniform(-0.3, 0.5)), scale=(1, 1, 0.6), seg=8)
    ball(name, COW, 0.5, (0, -1.5, 1.45), scale=(0.9, 1.1, 0.9)); ball(name, PINK, 0.3, (0, -2.0, 1.3), scale=(1.1, 0.6, 0.8), seg=8)
    for s in (-1, 1): cone(name, CREAM, 0.08, 0.4, (s * 0.35, -1.5, 1.95), seg=6); ball(name, BLACK, 0.06, (s * 0.2, -1.95, 1.5), seg=6)
    for x in (-0.4, 0.4):
        for y in (-0.8, 0.8): cyl(name, COW, 0.14, 0.9, (x, y, 0.45), seg=8)
    ball(name, PINK, 0.3, (0, 0.5, 0.65), scale=(1, 1, 0.8), seg=8)
    return name
def sheep(name):
    ball(name, SHEEP, 0.8, (0, 0, 0.95), scale=(0.9, 1.2, 0.85), seg=10)
    for k in range(10): ball(name, SHEEP, random.uniform(0.3, 0.45), (random.uniform(-0.5, 0.5), random.uniform(-0.8, 0.8), 0.95 + random.uniform(-0.3, 0.5)), seg=8)
    ball(name, BLACK, 0.32, (0, -1.0, 1.1), scale=(0.8, 1.1, 0.9), seg=10)
    for s in (-1, 1): ball(name, BLACK, 0.12, (s * 0.3, -0.9, 1.2), scale=(1, 0.5, 0.7), seg=6)
    for x in (-0.3, 0.3):
        for y in (-0.5, 0.5): cyl(name, BLACK, 0.08, 0.7, (x, y, 0.35), seg=6)
    return name
def flowers(name):
    for k in range(26):
        a = random.uniform(0, 6.28); r = random.uniform(0, 1.4)
        c = random.choice([RED, PINK, YELLOW, WHITE, (0.5, 0.4, 0.9)])
        cyl(name, GREEN, 0.015, 0.4, (math.cos(a) * r, math.sin(a) * r, 0.2), seg=4)
        ball(name, c, 0.09, (math.cos(a) * r, math.sin(a) * r, 0.42), scale=(1, 1, 0.5), seg=6)
    return name
def pine_log_bridge(name):
    for k in range(9): cyl(name, WOOD, 0.16, 3.0, (k * 0.36 - 1.44, 0, 0.3), rot=(math.radians(90), 0, 0), seg=8)
    for y in (-1.3, 1.3): box(name, WOOD_D, (3.2, 0.1, 0.1), (0, y, 1.0));
    for x in (-1.4, 0, 1.4):
        for y in (-1.3, 1.3): box(name, WOOD_D, (0.1, 0.1, 0.8), (x, y, 0.7))
    return name

names = [chalet('chalet_a', 6, 7, 2), chalet('chalet_b', 5, 6, 1), chalet('chalet_c', 7, 8, 2), church('church'), fence('fence'), waterwheel('waterwheel'),
         haystack('haystack'), signpost('signpost'), mushroom_house('mushroom'), cow('cow'), sheep('sheep'), flowers('flowers'), pine_log_bridge('bridge')]

# 이름별로 합치고 원점 기준 정리
joined = []
for name, objs in parts.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name
    bpy.ops.object.shade_smooth() if name in ('cow', 'sheep', 'flowers', 'mushroom') else bpy.ops.object.shade_flat()
    joined.append(o)
# 소품을 멀리 떨어뜨려 놓아 서로 겹치지 않게(Three.js에서 이름으로 가져가 쓰므로 위치는 무관)
for i, o in enumerate(joined): o.location.x = i * 30
bpy.ops.object.select_all(action='DESELECT')
for o in joined: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('exported', out, [o.name for o in joined], 'faces', sum(len(o.data.polygons) for o in joined))
