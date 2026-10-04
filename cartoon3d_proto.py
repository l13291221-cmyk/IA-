"""
PROTOTIPO motore 3D per i reel (work in progress).

Costruisce l'omino VcriptoV come modello 3D (Blender via modulo bpy) e lo
renderizza da piu angolazioni con Cycles (headless, CPU). NON ancora
collegato alla produzione: serve Blender/bpy e un render piu potente del
worker attuale. Base per la futura pipeline 3D (animazione + lip-sync +
camera + voce). Uso: python cartoon3d_proto.py <tag>
"""
import bpy, math, os, sys

OUT = os.environ.get("OMINO_OUT", os.getcwd())
TAG = sys.argv[-1] if len(sys.argv) > 1 else "v"

# --- pulizia ---
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for c in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.objects):
    for b in list(c):
        try: c.remove(b)
        except Exception: pass

def mat(name, rgb, rough=0.55, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value = rough
    return m

M_WHITE = mat("white", (0.96, 0.96, 0.96), 0.5)
M_SUIT  = mat("suit",  (0.015, 0.015, 0.02), 0.45)
M_DARK  = mat("dark",  (0.012, 0.012, 0.018), 0.4)
M_YEL   = mat("yel",   (0.98, 0.76, 0.10), 0.35)
M_EYE   = mat("eyew",  (0.99, 0.99, 0.99), 0.3)
M_PUP   = mat("pup",   (0.02, 0.02, 0.02), 0.2)
M_MOUTH = mat("mouth", (0.5, 0.18, 0.18), 0.4)

def add(prim, mt, loc, scale=(1,1,1), rot=(0,0,0), smooth=True, subs=0, **kw):
    getattr(bpy.ops.mesh, prim)(location=loc, **kw)
    o = bpy.context.active_object
    o.scale = scale; o.rotation_euler = rot
    if subs:
        m = o.modifiers.new("s", 'SUBSURF'); m.levels = subs; m.render_levels = subs
    o.data.materials.append(mt)
    if smooth: bpy.ops.object.shade_smooth()
    return o

# --- corpo ---
# giacca: corpo morbido (sfera schiacciata) + cono per la base
add("primitive_uv_sphere_add", M_SUIT, (0, 0, 1.62), scale=(0.72, 0.6, 0.72))
add("primitive_cone_add", M_SUIT, (0, 0, 1.18), scale=(1, 0.8, 1),
    radius1=0.82, radius2=0.62, depth=0.9)
# camicia a V (bianca)
add("primitive_cone_add", M_WHITE, (0, -0.5, 1.72), scale=(0.34, 0.22, 0.55),
    radius1=0.26, radius2=0.015, depth=0.75)
# bottoni
for z in (1.45, 1.28):
    add("primitive_uv_sphere_add", M_DARK, (0, -0.62, z), scale=(0.035, 0.035, 0.035))
# papillon giallo (due triangoli = due coni)
add("primitive_cone_add", M_YEL, (-0.11, -0.63, 1.96), scale=(0.11, 0.08, 0.14),
    rot=(math.pi/2, 0, math.radians(90)), radius1=0.5, radius2=0.08, depth=1)
add("primitive_cone_add", M_YEL, (0.11, -0.63, 1.96), scale=(0.11, 0.08, 0.14),
    rot=(math.pi/2, 0, math.radians(-90)), radius1=0.5, radius2=0.08, depth=1)
add("primitive_uv_sphere_add", M_YEL, (0, -0.64, 1.96), scale=(0.05, 0.05, 0.06))
# badge "V" giallo sul petto
add("primitive_cylinder_add", M_YEL, (0.36, -0.52, 1.52), scale=(0.1, 0.1, 0.025),
    rot=(math.pi/2, 0, 0), radius=1, depth=1)

# --- testa ---
add("primitive_uv_sphere_add", M_WHITE, (0, 0, 2.62), scale=(0.66, 0.6, 0.64), subs=1)
# occhi (bianco + pupilla)
for sx in (-1, 1):
    add("primitive_uv_sphere_add", M_EYE, (sx*0.22, -0.5, 2.68), scale=(0.12, 0.09, 0.14))
    add("primitive_uv_sphere_add", M_PUP, (sx*0.22, -0.58, 2.67), scale=(0.055, 0.05, 0.07))
# sopracciglia
for sx in (-1, 1):
    add("primitive_cube_add", M_PUP, (sx*0.22, -0.56, 2.86), scale=(0.11, 0.03, 0.022),
        rot=(0, 0, sx*0.12))
# bocca (aperta, come se parlasse)
add("primitive_uv_sphere_add", M_MOUTH, (0, -0.55, 2.42), scale=(0.11, 0.07, 0.08))

# --- braccia (capsule: cilindro + 2 sfere) ---
for sx in (-1, 1):
    add("primitive_cylinder_add", M_SUIT, (sx*0.86, 0.0, 1.4), scale=(0.16, 0.16, 0.5),
        rot=(0, sx*0.5, 0), radius=1, depth=1.2, subs=1)
    add("primitive_uv_sphere_add", M_WHITE, (sx*1.12, 0.0, 1.02), scale=(0.2, 0.2, 0.2), subs=1)
# --- gambe ---
for sx in (-1, 1):
    add("primitive_cylinder_add", M_DARK, (sx*0.3, 0, 0.44), scale=(0.19, 0.19, 0.5),
        radius=1, depth=1.05, subs=1)
    add("primitive_uv_sphere_add", M_DARK, (sx*0.3, -0.2, 0.12), scale=(0.24, 0.37, 0.15), subs=1)

# pavimento
add("primitive_plane_add", mat("floor", (0.96, 0.94, 0.90), 0.8), (0, 0, -0.02),
    scale=(30, 30, 1), size=1, smooth=False)

# --- target ---
tgt = bpy.data.objects.new("tgt", None); bpy.context.collection.objects.link(tgt)
tgt.location = (0, 0, 1.6)

def light(name, loc, energy, size=6):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    o.constraints.new('TRACK_TO').target = tgt
    return o
light("key", (-4.5, -5.5, 6.5), 1200, 8)
light("fill", (5.5, -3.5, 3.5), 500, 7)
light("rim", (0, 5.5, 5.5), 700, 6)

# mondo panna
w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.97, 0.94, 0.88, 1); bg.inputs[1].default_value = 0.9

# camera
cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd)
bpy.context.collection.objects.link(cam); bpy.context.scene.camera = cam
cd.lens = 55
cam.constraints.new('TRACK_TO').target = tgt

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 28
sc.render.resolution_x = 460; sc.render.resolution_y = 820
# profilo colore STANDARD (niente AgX che ingrigisce)
try: sc.view_settings.view_transform = 'Standard'
except Exception as e: print("vt err", e)

R = 9.0
for name, deg in (("front", 0), ("tqsx", -38), ("lato", -85), ("tqdx", 38)):
    a = math.radians(deg)
    cam.location = (R*math.sin(a), -R*math.cos(a), 3.5)
    sc.render.filepath = os.path.join(OUT, f"3d_{TAG}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
print("DONE")
