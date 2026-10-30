# 몸통 뒤쪽 경계보다 멀리 뻗은 꼬리 정점을 경계 쪽으로 당겨 짧게 만든다
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]; src, dst, k = argv[0], argv[1], float(argv[2])
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects: o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
vs = obj.data.vertices
zmin = min(v.co.z for v in vs); zmax = max(v.co.z for v in vs); H = zmax - zmin
xs = [abs(v.co.x) for v in vs]; xw = max(xs)
backs = []
for i in range(10, 70):
    z0 = zmin + H * i / 100; sl = [v.co.y for v in vs if z0 <= v.co.z < z0 + H * 0.02 and abs(v.co.x) < xw * 0.3]
    if sl: backs.append(max(sl))
backs.sort(); yb = backs[len(backs) // 4] + H * 0.04
n = 0
for v in vs:
    if v.co.y > yb: v.co.y = yb + (v.co.y - yb) * k; n += 1
print('trimmed verts', n, 'boundary', round(yb, 3))
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_image_format='AUTO')
