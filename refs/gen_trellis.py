import sys, shutil, os, json
from gradio_client import Client, handle_file
n = sys.argv[1]
c = Client("trellis-community/TRELLIS")
try: c.predict(api_name="/start_session")
except Exception as e: print('start_session', str(e)[:120])
views = [f"views/{n}_front.png", f"views/{n}_side.png", f"views/{n}_back.png"]
pre = c.predict(images=[{"image": handle_file(v), "caption": None} for v in views], api_name="/preprocess_images")
pre = [{"image": handle_file(x["image"]), "caption": None} for x in pre]
print('pre', str(pre)[:300])
r = c.predict(image=None, multiimages=pre, seed=1234, ss_guidance_strength=7.5, ss_sampling_steps=12,
              slat_guidance_strength=3.0, slat_sampling_steps=12, multiimage_algo='stochastic', mesh_simplify=0.9, texture_size=1024,
              api_name="/generate_and_extract_glb")
print('res', str(r)[:400])
def path(x):
    if isinstance(x, dict): return x.get('value') or x.get('path') or (x.get('video') or {}).get('path')
    return x
for x in (r if isinstance(r, (list, tuple)) else [r]):
    p = path(x)
    if p and str(p).endswith('.glb') and os.path.exists(p): shutil.copy(p, f"trellis_{n}.glb"); print('SAVED', f"trellis_{n}.glb", os.path.getsize(p))
