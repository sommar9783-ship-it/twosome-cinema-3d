# 블렌더로 반듯한(하이폴리곤·둥근 모서리) 모델을 직접 만들어 GLB로 내보내는 스크립트.
# 실행:  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P tools/build_models.py -- <출력 폴더>
# 만드는 것: loc.glb (극장 외관), claw.glb (인형뽑기), door.glb (뒷문).  정면 = 블렌더 -Y (게임에서는 +Z)
import bpy, bmesh, math, sys, os
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.getcwd()
FONT_SERIF = r"C:\Windows\Fonts\georgiab.ttf"
FONT_KR = r"C:\Windows\Fonts\malgunbd.ttf"

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, metal=0.0, rough=0.5, emit=None, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 1.0
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception:
            try: m.blend_method = 'BLEND'
            except Exception: pass
    return m

def finish(o, m, bevel=0.02, seg=3):
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if bevel > 0:
        md = o.modifiers.new("bevel", "BEVEL"); md.width = bevel; md.segments = seg; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(40)
    try:
        wn = o.modifiers.new("wn", "WEIGHTED_NORMAL"); wn.keep_sharp = False
    except Exception: pass
    return o

def box(size, loc, m, bevel=0.02, rot=(0, 0, 0), seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object
    o.scale = size; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, m, bevel, seg)

def cyl(r, depth, loc, m, rot=(0, 0, 0), verts=40, bevel=0.0, r2=None):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    else: bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=depth, vertices=verts, location=loc, rotation=rot)
    return finish(bpy.context.object, m, bevel, 2)

def sphere(r, loc, m, seg=20, rings=12, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=loc); o = bpy.context.object
    o.scale = scale; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, m, 0)

def text(body, size, loc, m, font=FONT_SERIF, extrude=0.03, rot=(math.pi / 2, 0, 0), spacing=1.0):
    cu = bpy.data.curves.new("txt", 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude; cu.bevel_depth = size * 0.012; cu.bevel_resolution = 2
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.space_character = spacing; cu.resolution_u = 6
    try: cu.font = bpy.data.fonts.load(font)
    except Exception as e: print("font load failed", e)
    o = bpy.data.objects.new("txt", cu); bpy.context.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = False
    return o

def prism(points, z0, z1, m, bevel=0.03):
    """위에서 본 다각형(points: [(x,y)...])을 z0~z1로 세운 기둥"""
    me = bpy.data.meshes.new("prism"); bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in points]; f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f]); up = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=up, vec=(0, 0, z1 - z0)); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new("prism", me); bpy.context.collection.objects.link(o)
    return finish(o, m, bevel)

def half_ring(R, r, loc, m, seg=64):
    """문 위 아치 테두리: 반원 고리 (정면 -Y 를 향해 세움)"""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=14, location=(0, 0, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -1e-4], context='VERTS'); bm.to_mesh(o.data); bm.free()
    o.rotation_euler = (math.pi / 2, 0, 0); o.location = loc
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.ops.object.transform_apply(rotation=True)
    return finish(o, m, 0)

def cut(target, cutter):
    md = target.modifiers.new("cut", "BOOLEAN"); md.operation = 'DIFFERENCE'; md.object = cutter
    try: md.solver = 'EXACT'
    except Exception: pass
    bpy.context.view_layer.objects.active = target; bpy.ops.object.select_all(action='DESELECT'); target.select_set(True)
    # 불리언은 다른 모디파이어보다 먼저 적용
    while target.modifiers[0].name != "cut": bpy.ops.object.modifier_move_up(modifier="cut")
    bpy.ops.object.modifier_apply(modifier="cut")

def bulbs_line(p0, p1, z, m, step=0.22, r=0.045, out=(0, -1)):
    d = Vector((p1[0] - p0[0], p1[1] - p0[1])); L = d.length; n = max(1, int(L / step)); d.normalize()
    for i in range(n + 1):
        t = L * i / n if n else 0
        sphere(r, (p0[0] + d.x * t + out[0] * 0.02, p0[1] + d.y * t + out[1] * 0.02, z), m, 14, 8)

def export(name):
    # 모디파이어를 적용해 메시로 만들고, 한 덩어리로 합쳐서(재질별로 묶임) 내보냄
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target='MESH'); bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    path = os.path.join(OUT, name + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    print("EXPORTED", name, "tris", tris, "size", os.path.getsize(path))

def palette():
    return dict(
        wine=mat("wine", (0.36, 0.035, 0.07), 0, 0.45), rose=mat("rose", (0.60, 0.09, 0.14), 0, 0.5),
        dark=mat("dark", (0.10, 0.02, 0.03), 0, 0.5), gold=mat("gold", (0.83, 0.56, 0.20), 0.85, 0.3),
        cream=mat("cream", (0.90, 0.84, 0.70), 0, 0.6), bulb=mat("bulb", (1, 0.92, 0.72), 0, 0.3, emit=(1, 0.86, 0.6)),
        black=mat("black", (0.01, 0.005, 0.006), 0, 0.9), glass=mat("glass", (0.80, 0.90, 1.0), 0.1, 0.05, alpha=0.16),
        red=mat("red", (0.62, 0.03, 0.06), 0, 0.8), ink=mat("ink", (0.05, 0.05, 0.06), 0.2, 0.4),
        rosein=mat("rosein", (0.80, 0.42, 0.48), 0, 0.8), tint=mat("tint", (0.10, 0.13, 0.16), 0.5, 0.12))

# ---------------------------------------------------------------- 극장 외관
def build_loc():
    reset(); P = palette(); F = -0.45  # 건물 앞면 y
    base = box((5.5, 1.0, 0.95), (0, 0, 0.475), P["dark"], 0.03)
    body = box((5.4, 0.9, 2.75), (0, 0, 2.325), P["rose"], 0.03)
    # 입구 (아치) 뚫기: 뒤쪽 15cm는 남겨 어두운 안쪽 면으로
    c1 = box((1.5, 1.6, 1.9), (0, -0.7, 0.95), None, 0); c2 = cyl(0.75, 1.6, (0, -0.7, 1.9), None, (math.pi / 2, 0, 0), 64)
    rail1 = box((5.56, 1.06, 0.07), (0, 0, 0.97), P["gold"], 0.02); rail2 = box((5.56, 1.06, 0.06), (0, 0, 0.03), P["gold"], 0.02)
    for t in (base, body, rail1, rail2):
        cut(t, c1)
    cut(body, c2)
    bpy.data.objects.remove(c1); bpy.data.objects.remove(c2)
    box((1.5, 0.02, 2.66), (0, 0.105, 1.33), P["black"], 0)
    # 입구 테두리
    for s in (-1, 1): box((0.12, 0.16, 1.9), (s * 0.81, F - 0.02, 0.95), P["gold"], 0.025)
    half_ring(0.81, 0.07, (0, F - 0.02, 1.9), P["gold"])
    box((0.9, 0.12, 0.16), (0, F - 0.03, 2.74), P["gold"], 0.03); sphere(0.07, (0, F - 0.1, 2.74), P["gold"])
    # 받침 금테 + 기둥
    for x in (-2.62, -1.1, 1.1, 2.62):
        box((0.16, 0.1, 2.72), (x, F - 0.03, 2.33), P["wine"], 0.02)
        for dx in (-0.055, 0.055): box((0.012, 0.012, 2.5), (x + dx, F - 0.085, 2.33), P["gold"], 0.004, seg=1)
    # 받침 장식 패널
    for x, w in ((-2.25, 0.62), (-1.5, 0.62), (1.5, 0.62), (2.25, 0.62)):
        box((w, 0.03, 0.6), (x, -0.505, 0.5), P["wine"], 0.012)
        box((w + 0.05, 0.02, 0.65), (x, -0.5, 0.5), P["gold"], 0.008)
    # 위쪽 장식 패널(프리즈)
    for x, w in ((-1.86, 1.3), (1.86, 1.3)):
        box((w + 0.07, 0.02, 0.5), (x, F - 0.012, 3.3), P["gold"], 0.008); box((w, 0.03, 0.43), (x, F - 0.022, 3.3), P["wine"], 0.012)
    # 매표 창구 (왼쪽)
    bx = -1.86
    box((1.36, 0.55, 0.95), (bx, -0.72, 0.475), P["dark"], 0.03); box((1.44, 0.63, 0.07), (bx, -0.72, 0.98), P["gold"], 0.025)
    box((1.2, 0.012, 1.0), (bx, -0.985, 1.52), P["glass"], 0)
    for s in (-1, 1): box((0.012, 0.5, 1.0), (bx + s * 0.6, -0.74, 1.52), P["glass"], 0)
    for sx in (-1, 1):
        for y in (-0.985, -0.5): box((0.07, 0.07, 1.02), (bx + sx * 0.62, y, 1.52), P["gold"], 0.02)
    box((1.25, 0.03, 0.04), (bx, -0.985, 1.05), P["gold"], 0.01); cyl(0.14, 0.03, (bx, -0.99, 1.1), P["gold"], (math.pi / 2, 0, 0))
    box((1.44, 0.63, 0.34), (bx, -0.72, 2.2), P["wine"], 0.04); box((1.5, 0.69, 0.05), (bx, -0.72, 2.02), P["gold"], 0.02); box((1.5, 0.69, 0.05), (bx, -0.72, 2.39), P["gold"], 0.02)
    text("TICKETS", 0.2, (bx, -1.045, 2.2), P["gold"], extrude=0.02, spacing=1.05)
    # 포스터 액자 (오른쪽)
    px = 1.86
    box((1.06, 0.08, 1.5), (px, F - 0.04, 1.85), P["gold"], 0.035); box((0.9, 0.03, 1.34), (px, F - 0.085, 1.85), P["cream"], 0.01)
    box((0.9, 0.035, 0.42), (px, F - 0.087, 2.31), P["wine"], 0.008); sphere(0.2, (px, F - 0.09, 1.72), P["red"], 24, 14, (0.9, 0.25, 1.15))
    sphere(0.09, (px, F - 0.06, 2.66), P["gold"], 16, 10)
    text("NOW SHOWING", 0.085, (px, F - 0.11, 2.31), P["gold"], extrude=0.008, spacing=1.05)
    # 입구 위 커튼 장식(고정)
    box((1.5, 0.08, 0.3), (0, -0.3, 2.5), P["red"], 0.06)
    # 본체와 차양 사이 금테
    box((5.6, 1.1, 0.1), (0, 0, 3.74), P["gold"], 0.03)
    # 차양(마키): 앞 모서리를 딴 육각 지붕
    FP = [(-2.95, 0.5), (2.95, 0.5), (2.95, -0.8), (2.25, -1.4), (-2.25, -1.4), (-2.95, -0.8)]
    prism(FP, 3.82, 4.98, P["wine"], 0.04)
    grow = lambda k: [(x * (1 + k / 2.95) if abs(x) > 2.5 else x * (1 + k / 2.25), y - k if y < 0 else y + k) for x, y in FP]
    prism(grow(0.06), 3.79, 3.87, P["gold"], 0.025); prism(grow(0.06), 4.93, 5.03, P["gold"], 0.025); prism(grow(0.0), 5.03, 5.12, P["dark"], 0.02)
    # 간판판 + 입체 글자
    box((3.9, 0.05, 0.96), (0, -1.415, 4.4), P["gold"], 0.03); box((3.74, 0.06, 0.82), (0, -1.43, 4.4), P["dark"], 0.02)
    text("TWOSOME", 0.34, (0, -1.47, 4.58), P["gold"], extrude=0.03, spacing=1.08)
    text("CINEMA", 0.34, (0, -1.47, 4.2), P["gold"], extrude=0.03, spacing=1.12)
    for s in (-1, 1):  # 간판 양옆 금색 딸기
        sphere(0.13, (s * 1.62, -1.47, 4.4), P["gold"], 20, 12, (0.95, 0.35, 1.2)); cyl(0.02, 0.07, (s * 1.62, -1.47, 4.585), P["gold"], verts=12)
    # 모서리 딴 면의 크림색 안내판
    ang = math.atan2(0.6, 0.7)
    for s in (-1, 1):
        cx, cy = s * 2.6, -1.1; nx, ny = s * 0.651, -0.759
        box((0.86, 0.04, 0.96), (cx + nx * 0.03, cy + ny * 0.03, 4.4), P["gold"], 0.02, rot=(0, 0, s * ang))
        box((0.74, 0.05, 0.84), (cx + nx * 0.045, cy + ny * 0.045, 4.4), P["cream"], 0.015, rot=(0, 0, s * ang))
        for k in range(4): box((0.74, 0.056, 0.012), (cx + nx * 0.046, cy + ny * 0.046, 4.14 + k * 0.17), P["gold"], 0, rot=(0, 0, s * ang))
    # 전구: 차양 위·아래 줄 + 처마 밑
    for z in (3.93, 4.87):
        bulbs_line((-2.2, -1.43), (2.2, -1.43), z, P["bulb"]); bulbs_line((2.3, -1.4), (2.97, -0.83), z, P["bulb"], out=(0.65, -0.76)); bulbs_line((-2.3, -1.4), (-2.97, -0.83), z, P["bulb"], out=(-0.65, -0.76))
    for x in [i * 0.42 - 2.1 for i in range(11)]:
        for y in (-1.15, -0.85, -0.6): sphere(0.05, (x, y, 3.78), P["bulb"], 14, 8)
    export("loc")

# ---------------------------------------------------------------- 인형뽑기
def build_claw():
    reset(); P = palette()
    box((1.5, 1.3, 0.98), (0, 0, 0.49), P["dark"], 0.04)
    box((1.56, 1.36, 0.06), (0, 0, 0.985), P["gold"], 0.02); box((1.56, 1.36, 0.07), (0, 0, 0.035), P["gold"], 0.025)
    for x in (-0.38, 0.38):
        box((0.6, 0.02, 0.66), (x, -0.655, 0.5), P["gold"], 0.008); box((0.55, 0.03, 0.61), (x, -0.66, 0.5), P["wine"], 0.012)
    box((0.36, 0.05, 0.32), (0.38, -0.67, 0.42), P["gold"], 0.03); box((0.28, 0.06, 0.24), (0.38, -0.675, 0.42), P["black"], 0.015)
    # 유리 칸: 바닥·뒷판·기둥·유리 (안은 비어 있음 → 게임의 집게·인형이 들어감)
    box((1.4, 1.2, 0.03), (0, 0, 1.005), P["rosein"], 0); box((1.4, 0.03, 1.42), (0, 0.6, 1.72), P["rosein"], 0)
    for sx in (-1, 1):
        for sy in (-1, 1): box((0.075, 0.075, 1.46), (sx * 0.71, sy * 0.61, 1.73), P["gold"], 0.02)
    box((1.36, 0.012, 1.42), (0, -0.61, 1.72), P["glass"], 0)
    for sx in (-1, 1): box((0.012, 1.16, 1.42), (sx * 0.71, 0, 1.72), P["glass"], 0)
    for sy in (-0.61, 0.61): box((1.38, 0.05, 0.05), (0, sy, 2.42), P["gold"], 0.015)
    # 지붕
    box((1.56, 1.36, 0.24), (0, 0, 2.57), P["wine"], 0.05); box((1.62, 1.42, 0.05), (0, 0, 2.45), P["gold"], 0.02); box((1.62, 1.42, 0.05), (0, 0, 2.69), P["gold"], 0.02)
    # 아치 간판 + 전구
    box((1.36, 0.1, 0.36), (0, -0.6, 2.88), P["gold"], 0.03)
    o = cyl(0.68, 0.1, (0, -0.6, 3.06), P["gold"], (math.pi / 2, 0, 0), 64); o.scale = (1, 1, 0.42); bpy.ops.object.transform_apply(scale=True)
    box((1.24, 0.11, 0.3), (0, -0.615, 2.88), P["wine"], 0.025)
    o = cyl(0.62, 0.11, (0, -0.615, 3.04), P["wine"], (math.pi / 2, 0, 0), 64); o.scale = (1, 1, 0.38); bpy.ops.object.transform_apply(scale=True)
    text("인형뽑기", 0.2, (0, -0.68, 2.93), P["gold"], font=FONT_KR, extrude=0.018)
    for i in range(15):  # 아치를 따라 전구
        a = math.pi * i / 14; sphere(0.034, (math.cos(a) * 0.65, -0.665, 3.06 + math.sin(a) * 0.65 * 0.42), P["bulb"], 14, 8)
    for i in range(9): sphere(0.034, (-0.6 + i * 0.15, -0.665, 2.73), P["bulb"], 14, 8)
    # 조작대
    box((1.5, 0.44, 0.14), (0, -0.84, 1.02), P["wine"], 0.05); box((1.54, 0.48, 0.04), (0, -0.84, 0.95), P["gold"], 0.018)
    cyl(0.07, 0.025, (-0.32, -0.86, 1.1), P["gold"]); cyl(0.018, 0.17, (-0.32, -0.86, 1.18), P["ink"], verts=14); sphere(0.055, (-0.32, -0.86, 1.28), P["red"])
    for x, c in ((0.05, (1, 0.72, 0.15)), (0.22, (0.12, 0.5, 0.95)), (0.39, (1, 0.25, 0.35))):
        cyl(0.06, 0.02, (x, -0.86, 1.095), P["gold"]); cyl(0.048, 0.04, (x, -0.86, 1.115), mat("btn", c, 0, 0.3), bevel=0.01)
    export("claw")

# ---------------------------------------------------------------- 뒷문
def build_door():
    reset(); P = palette()
    for s in (-1, 1):
        box((0.26, 0.22, 2.9), (s * 1.24, 0, 1.45), P["wine"], 0.03); box((0.32, 0.28, 0.14), (s * 1.24, 0, 0.07), P["dark"], 0.03); box((0.32, 0.28, 0.1), (s * 1.24, 0, 2.86), P["gold"], 0.03)
        for dx in (-0.07, 0.07): box((0.014, 0.014, 2.5), (s * 1.24 + dx, -0.115, 1.45), P["gold"], 0.004, seg=1)
    box((2.96, 0.34, 0.26), (0, 0, 3.05), P["wine"], 0.04); box((3.06, 0.4, 0.06), (0, 0, 2.92), P["gold"], 0.02); box((3.06, 0.4, 0.07), (0, 0, 3.2), P["gold"], 0.025)
    box((2.3, 0.02, 0.12), (0, -0.175, 3.05), P["gold"], 0.008)
    box((2.24, 0.1, 2.9), (0, 0.06, 1.45), P["dark"], 0)   # 문틀 안쪽
    for s in (-1, 1):
        x = s * 0.56
        box((1.08, 0.09, 2.82), (x, -0.02, 1.43), P["rose"], 0.025)
        # 유리창 + 금테
        box((0.74, 0.02, 1.34), (x, -0.066, 1.95), P["gold"], 0.012); box((0.66, 0.03, 1.26), (x, -0.07, 1.95), P["tint"], 0.008)
        # 아래 장식 패널
        box((0.74, 0.02, 0.8), (x, -0.066, 0.62), P["gold"], 0.012); box((0.66, 0.03, 0.72), (x, -0.07, 0.62), P["wine"], 0.012)
        # 손잡이
        hx = s * 0.1
        cyl(0.022, 0.8, (hx, -0.13, 1.35), P["gold"], verts=20)
        for z in (1.02, 1.68): cyl(0.016, 0.08, (hx, -0.095, z), P["gold"], (math.pi / 2, 0, 0), 14)
    export("door")

for fn in (build_loc, build_claw, build_door):
    try: fn()
    except Exception as e:
        import traceback; traceback.print_exc(); print("FAILED", fn.__name__, e)
