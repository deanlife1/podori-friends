# 정규화한 모델의 앞·뒤·옆 실루엣을 같은 직교 프레임(x,y∈[-0.65,0.65], z∈[-0.15,1.15])으로 렌더해 저장
import bpy, sys, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]; src, outdir = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects: o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
def bounds():
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))), Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
lo, hi = bounds(); s = 1.0 / (hi.z - lo.z); obj.scale = (s, s, s); bpy.ops.object.transform_apply(scale=True)
lo, hi = bounds(); obj.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z); bpy.ops.object.transform_apply(location=True)
scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; scene.display.shading.light = 'FLAT'; scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (1, 1, 1); scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 512; scene.render.image_settings.color_mode = 'RGBA'
cam_data = bpy.data.cameras.new('Cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 1.3
cam = bpy.data.objects.new('Cam', cam_data); bpy.context.collection.objects.link(cam); scene.camera = cam
# front: 카메라 -Y에서 봄(프레임 왼쪽 = -X). side: 카메라 +X(프레임 왼쪽 = -Y = 코). back: 카메라 +Y(프레임 왼쪽 = +X)
for nm, loc, rot in (('front', (0, -5, 0.5), (90, 0, 0)), ('side', (5, 0, 0.5), (90, 0, 90)), ('back', (0, 5, 0.5), (90, 0, 180))):
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    scene.render.filepath = f'{outdir}/sil_{nm}.png'; bpy.ops.render.render(write_still=True)
print('sil done')
