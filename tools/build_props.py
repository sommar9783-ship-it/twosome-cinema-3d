# 블렌더로 로비 소품을 직접 만드는 스크립트 (반듯한 면 + 둥근 모서리 + 입체 글자 + 전구).
# 실행:  blender -b -P tools/build_props.py -- <출력 폴더>
# 만드는 것: kiosk, booth, camera, mole, claw, scanner, seat  (.glb)
# 좌표는 "게임 좌표"로 적음: x 오른쪽, y 위, z 앞(로비 쪽). 블렌더로는 (x, -z, y) 로 바꿔 넣음. 원점·크기는 게임에서 그대로 씀(자동 맞춤 없음).
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.getcwd()
FONT_SERIF = r"C:\Windows\Fonts\georgiab.ttf"; FONT_KR = r"C:\Windows\Fonts\malgunbd.ttf"

def reset(): bpy.ops.wm.read_factory_settings(use_empty=True)
def B(x, y, z): return (x, -z, y)            # 게임 위치 → 블렌더 위치
def S(w, h, d): return (w, d, h)             # 게임 크기(폭,높이,깊이) → 블렌더 크기

def mat(name, color, metal=0.0, rough=0.5, emit=None, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 1.0
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m

def palette():
    return dict(wine=mat("wine", (0.36, 0.035, 0.07), 0, 0.45), rose=mat("rose", (0.60, 0.09, 0.14), 0, 0.5), dark=mat("dark", (0.10, 0.02, 0.03), 0, 0.5),
        gold=mat("gold", (0.83, 0.56, 0.20), 0.85, 0.3), cream=mat("cream", (0.93, 0.88, 0.76), 0, 0.55), bulb=mat("bulb", (1, 0.92, 0.72), 0, 0.3, emit=(1, 0.86, 0.6)),
        black=mat("black", (0.012, 0.008, 0.01), 0, 0.6), glass=mat("glass", (0.80, 0.90, 1.0), 0.1, 0.05, alpha=0.16), red=mat("red", (0.62, 0.03, 0.06), 0, 0.8),
        ink=mat("ink", (0.035, 0.035, 0.04), 0.3, 0.35), chrome=mat("chrome", (0.80, 0.82, 0.85), 0.95, 0.18), rosein=mat("rosein", (0.85, 0.50, 0.55), 0, 0.8),
        lens=mat("lens", (0.02, 0.03, 0.08), 0.6, 0.05), marble=mat("marble", (0.94, 0.91, 0.86), 0, 0.25), velvet=mat("red", (0.62, 0.03, 0.06), 0, 0.85),
        screen=mat("screen", (0.02, 0.015, 0.02), 0.2, 0.25), prose=mat("prose", (0.50, 0.07, 0.11), 0, 0.5), pwine=mat("pwine", (0.22, 0.02, 0.035), 0, 0.5), pdark=mat("pdark", (0.06, 0.012, 0.016), 0, 0.5), light=mat("light", (1, 0.96, 0.88), 0, 0.3, emit=(1, 0.95, 0.85)))

def finish(o, m, bevel=0.02, seg=3):
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if bevel > 0:
        md = o.modifiers.new("bevel", "BEVEL"); md.width = bevel; md.segments = seg; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(40)
    try: wn = o.modifiers.new("wn", "WEIGHTED_NORMAL"); wn.keep_sharp = False
    except Exception: pass
    return o

def gbox(w, h, d, x, y, z, m, bevel=0.02, rx=0.0, ry=0.0, seg=3):
    """게임 좌표 상자. rx = 게임 X축 회전(위가 뒤로 넘어가면 음수), ry = 게임 Y축(세로축) 회전"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=B(x, y, z), rotation=(rx, 0, ry)); o = bpy.context.object
    o.scale = S(w, h, d); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, m, bevel, seg)

def gcyl(r, length, x, y, z, m, axis='y', verts=40, bevel=0.0, r2=None, rx=0.0):
    """게임 좌표 원기둥. axis: 'y' 세로, 'z' 앞뒤, 'x' 좌우"""
    rot = {'y': (0, 0, 0), 'z': (math.pi / 2, 0, 0), 'x': (0, math.pi / 2, 0)}[axis]
    rot = (rot[0] + rx, rot[1], rot[2])
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length, vertices=verts, location=B(x, y, z), rotation=rot)
    else: bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=length, vertices=verts, location=B(x, y, z), rotation=rot)
    return finish(bpy.context.object, m, bevel, 2)

def gsphere(r, x, y, z, m, seg=18, rings=10, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=B(x, y, z)); o = bpy.context.object
    o.scale = S(*scale); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, m, 0)

def gtext(body, size, x, y, z, m, font=FONT_SERIF, extrude=0.02, spacing=1.05, back=False, rx=0.0):
    """앞(+z)을 보는 입체 글자. back=True 면 뒤(-z)를 봄"""
    cu = bpy.data.curves.new("txt", 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude; cu.bevel_depth = size * 0.012; cu.bevel_resolution = 2
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.space_character = spacing; cu.resolution_u = 6
    try: cu.font = bpy.data.fonts.load(font)
    except Exception as e: print("font load failed", e)
    o = bpy.data.objects.new("txt", cu); bpy.context.collection.objects.link(o); o.location = B(x, y, z); o.rotation_euler = (math.pi / 2 + rx, 0, math.pi if back else 0)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object; o.data.materials.append(m)
    return o

def cut(target, cutter):
    md = target.modifiers.new("cut", "BOOLEAN"); md.operation = 'DIFFERENCE'; md.object = cutter
    try: md.solver = 'EXACT'
    except Exception: pass
    bpy.context.view_layer.objects.active = target; bpy.ops.object.select_all(action='DESELECT'); target.select_set(True)
    while target.modifiers[0].name != "cut": bpy.ops.object.modifier_move_up(modifier="cut")
    bpy.ops.object.modifier_apply(modifier="cut")

def arch_ring(R, r, x, y, z, m, seg=64):
    """앞을 보는 반원 고리 (문 위 아치 테두리)"""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=14, location=(0, 0, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -1e-4], context='VERTS'); bm.to_mesh(o.data); bm.free()
    o.rotation_euler = (math.pi / 2, 0, 0); o.location = B(x, y, z)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.ops.object.transform_apply(rotation=True)
    return finish(o, m, 0)

def marquee(P, w, yb, z, label, font=FONT_SERIF, tsize=0.17, arch=0.42):
    """아치형 전구 간판: 폭 w, 아래쪽 높이 yb, 앞면 z. 글자는 금색 입체"""
    hb = 0.34
    gbox(w + 0.1, hb + 0.08, 0.1, 0, yb + hb / 2, z - 0.03, P["gold"], 0.03)
    o = gcyl(w / 2 + 0.05, 0.1, 0, yb + hb, z - 0.03, P["gold"], 'z', 64); o.scale = (1, arch, 1); bpy.ops.object.transform_apply(scale=True)
    gbox(w, hb, 0.11, 0, yb + hb / 2, z - 0.015, P["wine"], 0.025)
    o = gcyl(w / 2 - 0.01, 0.11, 0, yb + hb - 0.01, z - 0.015, P["wine"], 'z', 64); o.scale = (1, arch * 0.9, 1); bpy.ops.object.transform_apply(scale=True)
    gtext(label, tsize, 0, yb + hb * 0.56, z + 0.05, P["gold"], font=font, extrude=0.016)
    n = max(7, int(w / 0.13)); R = w / 2 + 0.01
    for i in range(n + 1):
        a = math.pi * i / n; gsphere(0.03, math.cos(a) * R, yb + hb + math.sin(a) * R * arch, z + 0.035, P["bulb"], 12, 8)
    for i in range(int(w / 0.14) + 1): gsphere(0.03, -w / 2 + 0.02 + i * (w - 0.04) / max(1, int(w / 0.14)), yb - 0.005, z + 0.035, P["bulb"], 12, 8)

def export(name):
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target='MESH'); bpy.ops.object.join(); o = bpy.context.object; o.name = name
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons); path = os.path.join(OUT, name + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    print("EXPORTED", name, "tris", tris, "size", os.path.getsize(path))

def panel(P, w, h, x, y, z, inner="wine", d=0.03):
    """금테 두른 장식 패널 (앞을 봄)"""
    gbox(w + 0.05, h + 0.05, d * 0.7, x, y, z - 0.004, P["gold"], 0.008); gbox(w, h, d, x, y, z, P[inner], 0.012)

# ---- 참고 시안 스타일 도우미: 금색 가는 선 액자, 도드라진 패널, 반원통 지붕
def frame_z(P, w, h, x, y, z, t=0.014, d=0.014, m="gold"):
    for sy in (-1, 1): gbox(w + t, t, d, x, y + sy * h / 2, z, P[m], 0.004, seg=1)
    for sx in (-1, 1): gbox(t, h, d, x + sx * w / 2, y, z, P[m], 0.004, seg=1)
def frame_x(P, l, h, x, y, z, t=0.014, d=0.014, m="gold"):
    for sy in (-1, 1): gbox(d, t, l + t, x, y + sy * h / 2, z, P[m], 0.004, seg=1)
    for sz in (-1, 1): gbox(d, h, t, x, y, z + sz * l / 2, P[m], 0.004, seg=1)
def mold_z(P, w, h, x, y, z, body, sgn=1):
    gbox(w, h, 0.03, x, y, z, P[body], 0.014); frame_z(P, w - 0.09, h - 0.09, x, y, z + sgn * 0.015)
def mold_x(P, l, h, x, y, z, body, sgn=1):
    gbox(0.03, h, l, x, y, z, P[body], 0.014); frame_x(P, l - 0.09, h - 0.09, x + sgn * 0.015, y, z)
def barrel(P, w, d, x, y, z, rise, m):
    """앞뒤로 긴 반원통 지붕: 폭 w, 깊이 d, 바닥 높이 y, 솟은 높이 rise"""
    o = gcyl(w / 2, d, x, y, z, P[m], 'z', 56); o.scale = (1, rise / (w / 2), 1); bpy.ops.object.transform_apply(scale=True)
    c = gbox(w + 0.2, rise + 0.2, d + 0.2, x, y - (rise + 0.2) / 2, z, None, 0); cut(o, c); bpy.data.objects.remove(c)
    return o
def P2(P): return dict(P, wine=P["pwine"])

# ------------------------------------------------------------ 티켓 발권기 (시안: 짙은 받침 + 장밋빛 몸통 + 전구 간판)
def build_kiosk():
    reset(); P = palette()
    gbox(1.02, 0.06, 0.9, 0, 0.03, 0, P["pdark"], 0.025); gbox(1.04, 0.035, 0.92, 0, 0.078, 0, P["gold"], 0.014)
    gbox(0.94, 0.5, 0.82, 0, 0.35, 0, P["pdark"], 0.04)                          # 받침
    mold_z(P, 0.66, 0.32, 0, 0.35, 0.41, "pdark")
    for s in (-1, 1): mold_x(P, 0.56, 0.32, s * 0.47, 0.35, 0, "pdark", s)
    gbox(0.98, 0.045, 0.86, 0, 0.622, 0, P["gold"], 0.018)
    gbox(0.9, 0.5, 0.78, 0, 0.89, 0, P["prose"], 0.05)                           # 가운데 몸통 (티켓 나오는 곳)
    gbox(0.4, 0.15, 0.05, 0, 0.76, 0.385, P["chrome"], 0.02); gbox(0.3, 0.04, 0.06, 0, 0.775, 0.39, P["black"], 0.006)
    gbox(0.3, 0.02, 0.1, 0, 0.72, 0.43, P["chrome"], 0.008, rx=0.25)
    for s in (-1, 1): mold_x(P, 0.5, 0.34, s * 0.45, 0.89, 0, "pwine", s)
    # 조작 선반 (앞으로 기울어짐): 카드 단말기 · 키패드 · 영수증
    gbox(0.9, 0.1, 0.36, 0, 1.1, 0.2, P["prose"], 0.04, rx=0.32)
    gbox(0.2, 0.05, 0.2, -0.26, 1.16, 0.22, P["ink"], 0.018, rx=0.32); gbox(0.13, 0.012, 0.1, -0.26, 1.196, 0.2, P["chrome"], 0.004, rx=0.32)
    gbox(0.2, 0.03, 0.18, 0.0, 1.155, 0.22, P["chrome"], 0.01, rx=0.32)
    for i in range(3):
        for j in range(3): gbox(0.04, 0.012, 0.035, -0.055 + i * 0.055, 1.178 - (j - 1) * 0.018, 0.205 + (j - 1) * 0.052, P["ink"], 0.004, rx=0.32, seg=1)
    gbox(0.17, 0.035, 0.15, 0.27, 1.155, 0.22, P["gold"], 0.012, rx=0.32); gbox(0.11, 0.012, 0.09, 0.27, 1.178, 0.215, P["black"], 0.004, rx=0.32)
    # 윗몸통 + 화면 (금색 테두리 안에 검은 화면. 게임 화면이 그 앞에 붙음)
    gbox(0.88, 1.0, 0.52, 0, 1.62, -0.1, P["prose"], 0.05)
    for s in (-1, 1): mold_x(P, 0.36, 0.78, s * 0.44, 1.62, -0.1, "pwine", s)
    cy, cz = 1.6, 0.185
    frame = gbox(0.76, 0.94, 0.07, 0, cy, cz, P["gold"], 0.025)
    hole = gbox(0.62, 0.8, 0.2, 0, cy, cz, None, 0); cut(frame, hole); bpy.data.objects.remove(hole)
    gbox(0.64, 0.82, 0.02, 0, cy - 0.004, cz - 0.03, P["screen"], 0)
    # 머리(짙은 와인색 둥근 덮개) + 전구 간판
    gbox(0.98, 0.34, 0.66, 0, 2.29, -0.08, P["pwine"], 0.07, seg=5)
    gbox(0.94, 0.03, 0.6, 0, 2.115, -0.08, P["gold"], 0.012)
    marquee(P2(P), 0.86, 2.16, 0.27, "TICKETS", tsize=0.155)
    export("kiosk")

# ------------------------------------------------------------ 포토부스 (안이 빈 진짜 부스. 시안: 짙은 허리판 + 장밋빛 벽 + 와인색 기둥·처마)
def build_booth():
    reset(); P = palette(); W, D, H = 2.0, 1.7, 2.62
    gbox(W, 0.05, D, 0, 0.025, 0, P["pdark"], 0.01)
    gbox(W, H, 0.08, 0, H / 2, -0.87, P["prose"], 0.02)                               # 뒷벽 (게임의 배경막이 그 앞에 섬)
    gbox(W + 0.06, 0.64, 0.06, 0, 0.32, -0.92, P["pdark"], 0.02); mold_z(P, 1.3, 0.42, 0, 0.32, -0.955, "pdark", -1)
    mold_z(P, 1.3, 1.5, 0, 1.55, -0.915, "pwine", -1)
    for s in (-1, 1):
        gbox(0.08, H, D, s * 0.96, H / 2, 0, P["prose"], 0.02)                        # 옆벽
        gbox(0.06, 0.64, D + 0.06, s * 1.01, 0.32, 0, P["pdark"], 0.02); mold_x(P, 0.9, 0.42, s * 1.045, 0.32, 0, "pdark", s)
        mold_x(P, 0.95, 1.5, s * 1.005, 1.55, 0, "pwine", s)
        gbox(0.06, 0.04, D + 0.1, s * 1.02, 0.66, 0, P["gold"], 0.014)
        for z in (-0.82, 0.82):                                                       # 모서리 기둥
            gbox(0.22, H, 0.22, s * 0.92, H / 2, z, P["pwine"], 0.03)
            gbox(0.27, 0.64, 0.27, s * 0.92, 0.32, z, P["pdark"], 0.03); gbox(0.29, 0.04, 0.29, s * 0.92, 0.66, z, P["gold"], 0.014)
            gbox(0.27, 0.16, 0.27, s * 0.92, H - 0.2, z, P["pwine"], 0.03)
        frame_z(P, 0.1, 1.5, s * 0.92, 1.55, 0.935)
    gbox(W + 0.1, 0.04, 0.06, 0, 0.66, -0.93, P["gold"], 0.014)
    # 앞벽 + 아치 입구 (폭 1.2, 곧은 부분 1.5, 아치 반지름 0.6 → 높이 2.1)
    front = gbox(W, H, 0.1, 0, H / 2, 0.8, P["prose"], 0.02)
    c1 = gbox(1.2, 1.5, 0.6, 0, 0.75, 0.8, None, 0); c2 = gcyl(0.6, 0.6, 0, 1.5, 0.8, None, 'z', 64)
    cut(front, c1); cut(front, c2); bpy.data.objects.remove(c1); bpy.data.objects.remove(c2)
    for s in (-1, 1): gbox(0.07, 1.5, 0.14, s * 0.635, 0.75, 0.82, P["gold"], 0.025)
    arch_ring(0.635, 0.045, 0, 1.5, 0.83, P["gold"])
    # 처마(겹겹이) + 꼭대기 장식
    gbox(W + 0.3, 0.035, D + 0.3, 0, H - 0.06, 0, P["gold"], 0.014)
    gbox(W + 0.24, 0.2, D + 0.24, 0, H + 0.06, 0, P["pwine"], 0.04); gbox(W + 0.34, 0.04, D + 0.34, 0, H + 0.18, 0, P["gold"], 0.016)
    gbox(W + 0.3, 0.07, D + 0.3, 0, H + 0.235, 0, P["pwine"], 0.03)
    gbox(1.1, 0.1, 0.1, 0, H + 0.32, 0.84, P["pwine"], 0.03); gbox(1.16, 0.03, 0.12, 0, H + 0.385, 0.84, P["gold"], 0.012)
    o = gcyl(0.5, 0.09, 0, H + 0.4, 0.84, P["pwine"], 'z', 56); o.scale = (1, 0.5, 1); bpy.ops.object.transform_apply(scale=True)
    c = gbox(1.3, 0.4, 0.3, 0, H + 0.2, 0.84, None, 0); cut(o, c); bpy.data.objects.remove(c)
    gcyl(0.1, 0.11, 0, H + 0.5, 0.84, P["gold"], 'z', 32, 0.008); gcyl(0.07, 0.12, 0, H + 0.5, 0.84, P["pwine"], 'z', 32)
    # 간판 + 전구
    gbox(1.46, 0.32, 0.06, 0, 2.36, 0.86, P["gold"], 0.05, seg=4); gbox(1.36, 0.22, 0.07, 0, 2.36, 0.865, P["light"], 0.04, seg=4)
    gtext("PHOTO BOOTH", 0.115, 0, 2.36, 0.905, P["pwine"], extrude=0.008, spacing=1.08)
    for i in range(14):
        for y in (2.49, 2.23): gsphere(0.024, -0.65 + i * 0.1, y, 0.9, P["bulb"], 12, 8)
    for y in (2.3, 2.36, 2.42):
        for s in (-1, 1): gsphere(0.024, s * 0.7, y, 0.9, P["bulb"], 12, 8)
    # 입구 안쪽 커튼 (양옆으로 묶인 천) + 위쪽 드레이프
    for s in (-1, 1):
        for k in range(6): gcyl(0.042, 1.98, s * (0.57 - k * 0.045), 1.0, 0.71 - (k % 2) * 0.035, P["red"], 'y', 14)
        gbox(0.3, 0.05, 0.1, s * 0.47, 1.0, 0.72, P["gold"], 0.02)
    gbox(1.2, 0.26, 0.08, 0, 1.97, 0.72, P["red"], 0.06)
    export("booth")

# ------------------------------------------------------------ 포토부스 카메라 (삼각대 + 카메라, 렌즈는 -z = 부스 쪽)
def build_camera():
    reset(); P = palette()
    hub_y = 1.12
    for i in range(3):
        a = math.pi / 2 + i * 2 * math.pi / 3; fx, fz = math.cos(a) * 0.36, math.sin(a) * 0.36
        v = Vector(B(fx, 0.02, fz)) - Vector(B(0, hub_y, 0)); L = v.length
        bpy.ops.mesh.primitive_cone_add(radius1=0.02, radius2=0.014, depth=L, vertices=16, location=(Vector(B(0, hub_y, 0)) + v / 2))
        o = bpy.context.object; o.rotation_euler = Vector((0, 0, -1)).rotation_difference(v.normalized()).to_euler(); finish(o, P["ink"], 0)
        gsphere(0.03, fx, 0.025, fz, P["ink"], 12, 8); gcyl(0.024, 0.05, fx * 0.5, hub_y * 0.52, fz * 0.5, P["chrome"], 'y', 14)
    gcyl(0.05, 0.1, 0, hub_y, 0, P["ink"], 'y', 20, 0.01); gcyl(0.018, 0.34, 0, hub_y + 0.2, 0, P["chrome"], 'y', 16)
    gcyl(0.06, 0.05, 0, hub_y + 0.37, 0, P["ink"], 'y', 24, 0.008); gbox(0.2, 0.03, 0.14, 0, hub_y + 0.405, 0, P["chrome"], 0.008)
    by = hub_y + 0.55
    gbox(0.4, 0.26, 0.2, 0, by, 0, P["ink"], 0.03)                                    # 카메라 몸통
    gbox(0.41, 0.05, 0.205, 0, by + 0.12, 0, P["chrome"], 0.015); gbox(0.41, 0.03, 0.205, 0, by - 0.125, 0, P["chrome"], 0.012)
    gbox(0.1, 0.27, 0.215, -0.16, by, 0, P["dark"], 0.03)                              # 손잡이 가죽
    gcyl(0.105, 0.05, 0.03, by - 0.005, -0.12, P["chrome"], 'z', 40, 0.008)            # 렌즈 마운트
    gcyl(0.095, 0.12, 0.03, by - 0.005, -0.19, P["ink"], 'z', 40, 0.006); gcyl(0.1, 0.03, 0.03, by - 0.005, -0.255, P["chrome"], 'z', 40, 0.004)
    gcyl(0.08, 0.012, 0.03, by - 0.005, -0.268, P["lens"], 'z', 40); gcyl(0.035, 0.006, 0.03, by - 0.005, -0.275, mat("lens2", (0.12, 0.16, 0.35), 0.8, 0.05), 'z', 24)
    gbox(0.12, 0.07, 0.1, 0.02, by + 0.18, 0.0, P["ink"], 0.02)                        # 뷰파인더 혹
    gcyl(0.022, 0.02, -0.13, by + 0.155, -0.02, P["chrome"], 'y', 20); gcyl(0.012, 0.012, 0.15, by + 0.06, -0.103, mat("rec", (0.9, 0.05, 0.05), 0, 0.3, emit=(0.9, 0.05, 0.05)), 'z', 14)
    gbox(0.22, 0.12, 0.1, 0.02, by + 0.29, 0.0, P["ink"], 0.025); gbox(0.18, 0.085, 0.02, 0.02, by + 0.29, -0.052, P["light"], 0.008)   # 플래시
    gbox(0.05, 0.04, 0.05, 0.02, by + 0.22, 0.0, P["chrome"], 0.008)
    export("camera")

# ------------------------------------------------------------ 딸기 으깨기 (구멍·딸기·점수판·컵은 게임이 그림)
def build_mole():
    reset(); P = palette()
    gbox(1.26, 0.1, 0.96, 0, 0.05, 0, P["dark"], 0.03); gbox(1.3, 0.04, 1.0, 0, 0.115, 0, P["gold"], 0.015)
    gbox(1.2, 0.84, 0.9, 0, 0.53, 0, P["wine"], 0.035)
    for x in (-0.3, 0.3): panel(P, 0.48, 0.56, x, 0.52, 0.452)
    for s in (-1, 1):
        gbox(0.07, 0.86, 0.07, s * 0.6, 0.53, 0.45, P["gold"], 0.02)
        panel(P, 0.6, 0.56, 0, 0, 0) if False else None
    gbox(1.28, 0.04, 0.98, 0, 0.97, 0, P["marble"], 0.015); gbox(1.3, 0.025, 1.0, 0, 0.945, 0, P["gold"], 0.01)   # 윗면(구멍판) 높이 0.99
    gbox(1.24, 1.34, 0.1, 0, 1.64, -0.42, P["wine"], 0.03)                              # 뒷판 (앞면 z=-0.37)
    gbox(1.3, 0.05, 0.14, 0, 2.3, -0.42, P["gold"], 0.02)
    for s in (-1, 1): gbox(0.06, 1.3, 0.12, s * 0.62, 1.64, -0.41, P["gold"], 0.02)
    gbox(0.72, 0.56, 0.02, 0.17, 1.72, -0.372, P["gold"], 0.012)                        # 점수판 테두리 (게임 화면이 그 앞에)
    gcyl(0.17, 0.02, -0.38, 1.68, -0.372, P["gold"], 'z', 40)                           # 컵 뒤 원판
    marquee(P, 1.06, 2.36, -0.36, "BERRY SMASH", tsize=0.115)
    gbox(1.2, 0.44, 0.08, 0, 2.5, -0.44, P["wine"], 0.03)
    export("mole")

# ------------------------------------------------------------ 인형뽑기 (유리 칸은 비어 있음 → 게임의 집게·인형이 들어감. 시안: 짙은 받침 + 장밋빛 틀 + 둥근 지붕)
def build_claw():
    reset(); P = palette()
    gbox(1.64, 0.07, 1.44, 0, 0.035, 0, P["pdark"], 0.03); gbox(1.66, 0.035, 1.46, 0, 0.085, 0, P["gold"], 0.014)
    gbox(1.5, 0.84, 1.3, 0, 0.52, 0, P["pdark"], 0.04)                                  # 받침
    mold_z(P, 0.56, 0.6, -0.37, 0.5, 0.652, "pdark"); mold_z(P, 0.56, 0.6, 0.37, 0.5, 0.652, "pdark")
    mold_z(P, 1.2, 0.6, 0, 0.5, -0.652, "pdark", -1)
    for s in (-1, 1):
        for z in (-0.31, 0.31): mold_x(P, 0.52, 0.6, s * 0.752, 0.5, z, "pdark", s)
        for z in (-0.64, 0.64): gbox(0.13, 0.86, 0.13, s * 0.74, 0.52, z, P["pdark"], 0.03)
    gbox(0.36, 0.4, 0.05, 0.37, 0.42, 0.685, P["gold"], 0.06, seg=5); gbox(0.27, 0.31, 0.06, 0.37, 0.42, 0.69, P["black"], 0.04, seg=4)   # 상품 출구
    gbox(1.6, 0.05, 1.4, 0, 0.955, 0, P["gold"], 0.02)
    gbox(1.58, 0.06, 1.38, 0, 0.99, 0, P["gold"], 0.02)
    gbox(1.42, 0.03, 1.22, 0, 1.012, 0, P["rosein"], 0)                                 # 유리 칸 바닥
    gbox(1.42, 1.44, 0.03, 0, 1.73, -0.6, P["prose"], 0); frame_z(P, 1.1, 1.1, 0, 1.75, -0.58)   # 뒷판 (안쪽에 금색 선)
    gbox(1.46, 1.46, 0.03, 0, 1.73, -0.635, P["prose"], 0.01); mold_z(P, 1.1, 1.15, 0, 1.73, -0.655, "pwine", -1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            gbox(0.12, 1.5, 0.12, sx * 0.71, 1.74, sz * 0.61, P["prose"], 0.03)         # 모서리 기둥 (장밋빛) + 금색 선
            gbox(0.016, 1.3, 0.016, sx * 0.71, 1.74, sz * 0.675, P["gold"], 0.005, seg=1); gbox(0.016, 1.3, 0.016, sx * 0.775, 1.74, sz * 0.61, P["gold"], 0.005, seg=1)
    gbox(1.36, 1.42, 0.012, 0, 1.73, 0.61, P["glass"], 0)
    for sx in (-1, 1): gbox(0.012, 1.42, 1.16, sx * 0.71, 1.73, 0, P["glass"], 0)
    frame_z(P, 1.3, 1.38, 0, 1.73, 0.625, t=0.03, d=0.03)                               # 유리창 금테
    for sx in (-1, 1): frame_x(P, 1.1, 1.38, sx * 0.725, 1.73, 0, t=0.03, d=0.03)
    gbox(1.3, 0.02, 1.1, 0, 2.455, 0, P["light"], 0)                                    # 안쪽 조명판
    for sz in (-0.5, 0.5): gcyl(0.012, 1.3, 0, 2.38, sz, P["chrome"], 'x', 12)          # 집게 레일
    gbox(1.6, 0.05, 1.4, 0, 2.49, 0, P["gold"], 0.02)
    gbox(1.56, 0.16, 1.36, 0, 2.59, 0, P["pwine"], 0.03); gbox(1.62, 0.04, 1.42, 0, 2.685, 0, P["gold"], 0.016)
    barrel(P, 1.5, 1.3, 0, 2.7, 0, 0.42, "pwine")                                       # 둥근 지붕
    for sx in (-1, 1): gbox(0.14, 0.14, 0.14, sx * 0.72, 2.56, 0.66, P["gold"], 0.03)   # 모서리 금장식
    marquee(P2(P), 1.3, 2.62, 0.72, "CLAW MACHINE", tsize=0.125, arch=0.5)
    # 조작대
    gbox(1.5, 0.15, 0.46, 0, 1.03, 0.86, P["pwine"], 0.06, seg=5); gbox(1.56, 0.035, 0.5, 0, 0.95, 0.86, P["gold"], 0.016)
    gbox(1.36, 0.016, 0.34, 0, 1.108, 0.87, P["gold"], 0.006); gbox(1.31, 0.02, 0.29, 0, 1.11, 0.87, P["prose"], 0.006)
    gcyl(0.075, 0.025, -0.4, 1.13, 0.88, P["gold"], 'y'); gcyl(0.018, 0.17, -0.4, 1.21, 0.88, P["ink"], 'y', 14); gsphere(0.055, -0.4, 1.31, 0.88, P["red"])
    for x, c in ((-0.08, (1, 0.72, 0.15)), (0.1, (0.12, 0.5, 0.95)), (0.28, (1, 0.25, 0.35))):
        gcyl(0.062, 0.02, x, 1.125, 0.88, P["gold"], 'y'); gcyl(0.05, 0.04, x, 1.145, 0.88, mat("btn", c, 0, 0.3), 'y', 32, 0.01)
    gbox(0.14, 0.02, 0.18, 0.52, 1.125, 0.88, P["chrome"], 0.008); gbox(0.012, 0.024, 0.08, 0.52, 1.128, 0.88, P["black"], 0.003)   # 동전 투입구
    export("claw")

# ------------------------------------------------------------ 티켓 스캐너 스탠드 (화면은 게임이 그림)
def build_scanner():
    reset(); P = palette()
    gcyl(0.17, 0.03, 0, 0.015, 0, P["gold"], 'y', 40, 0.008); gcyl(0.13, 0.03, 0, 0.045, 0, P["dark"], 'y', 40, 0.008)
    gcyl(0.022, 0.98, 0, 0.55, 0, P["gold"], 'y', 20); gsphere(0.04, 0, 0.3, 0, P["gold"], 16, 10); gsphere(0.035, 0, 1.03, 0, P["gold"], 16, 10)
    gbox(0.34, 0.26, 0.04, 0, 1.12, -0.012, P["gold"], 0.018, rx=-0.5); gbox(0.31, 0.23, 0.045, 0, 1.12, -0.004, P["ink"], 0.015, rx=-0.5)
    export("scanner")

# ------------------------------------------------------------ 상영관 좌석 (화면 쪽 = -z 를 봄)
def build_seat():
    reset(); P = palette(); T = -0.13
    def back(dy, dz):   # 등받이 기준점(0,0.5,0.3)에서 기울인 위치
        return (0.5 + dy * math.cos(T) - dz * math.sin(T), 0.3 + dy * math.sin(T) + dz * math.cos(T))
    gbox(0.5, 0.26, 0.34, 0, 0.15, 0.05, P["dark"], 0.03); gbox(0.56, 0.04, 0.4, 0, 0.02, 0.05, P["ink"], 0.012)
    gbox(0.58, 0.17, 0.52, 0, 0.46, -0.03, P["velvet"], 0.07, seg=5)                    # 앉는 쿠션
    gbox(0.5, 0.05, 0.44, 0, 0.555, -0.03, P["velvet"], 0.025, seg=3)
    y, z = back(0.42, -0.02); gbox(0.6, 0.88, 0.16, 0, y, z, P["velvet"], 0.07, rx=T, seg=5)                    # 등받이
    for k, dy in enumerate((0.16, 0.42, 0.68)):                                         # 누빔 패드 3단
        y, z = back(dy, -0.1); gbox(0.5, 0.22, 0.06, 0, y, z, P["velvet"], 0.028, rx=T, seg=4)
    y, z = back(0.9, -0.03); gbox(0.48, 0.2, 0.15, 0, y, z, P["velvet"], 0.06, rx=T, seg=5)                    # 머리받이
    y, z = back(0.42, 0.07); gbox(0.62, 0.9, 0.04, 0, y, z, P["dark"], 0.015, rx=T)                              # 등판 뒤 커버
    for s in (-1, 1):
        gbox(0.1, 0.34, 0.56, s * 0.37, 0.53, 0.0, P["dark"], 0.035); gbox(0.105, 0.035, 0.42, s * 0.37, 0.715, 0.06, P["ink"], 0.014)
        gcyl(0.062, 0.05, s * 0.37, 0.715, -0.2, P["ink"], 'y', 28, 0.006); gcyl(0.05, 0.012, s * 0.37, 0.742, -0.2, P["gold"], 'y', 28)
        gbox(0.012, 0.012, 0.5, s * 0.318, 0.69, 0.0, P["gold"], 0.004, seg=1)
    export("seat")

for fn in (build_kiosk, build_booth, build_camera, build_mole, build_claw, build_scanner, build_seat):
    try: fn()
    except Exception as e:
        import traceback; traceback.print_exc(); print("FAILED", fn.__name__, e)
