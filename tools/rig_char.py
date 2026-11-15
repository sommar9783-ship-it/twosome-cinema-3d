# 뷰 3장으로 만든 캐릭터 모델(디자인과 가장 닮은 통짜 메시)에 블렌더로 뼈대를 직접 심는 스크립트.
# 실행:  blender -b -P tools/rig_char.py -- <입력 char.glb> <출력 char.glb>
# - 표면을 살짝 펴고(스무스) 부드러운 음영으로 바꿈
# - 뼈대: Hips, Spine, Head, Left/RightArm, Left/RightHand, Left/RightUpLeg, Left/RightLeg  (게임 코드가 쓰는 이름)
# - 가중치는 영역으로 직접 지정: 목 위(머리+딸기 모자)는 통째로 Head → 얼굴·모자가 절대 찌그러지지 않음
import bpy, bmesh, math, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = args[0], args[1]
H = 1.2

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
ob = bpy.context.object
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in list(bpy.context.scene.objects):
    if o != ob: bpy.data.objects.remove(o)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 정면을 -Y 로 (Tripo 결과물은 정면이 +X), 키 1.2m, 발이 바닥, 가운데 정렬
ob.rotation_euler = (0, 0, -math.pi / 2); bpy.ops.object.transform_apply(rotation=True)
vs = [v.co.copy() for v in ob.data.vertices]
mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
k = H / (mx.z - mn.z)
for v in ob.data.vertices:
    v.co = Vector(((v.co.x - (mn.x + mx.x) / 2) * k, (v.co.y - (mn.y + mx.y) / 2) * k, (v.co.z - mn.z) * k))

# 방향을 모델에서 직접 판별: 몸통 높이에서 더 넓은 쪽이 팔 방향(X 여야 함), 발끝이 나온 쪽이 정면(-Y 여야 함)
def rotz(a):
    c, s = math.cos(a), math.sin(a)
    for v in ob.data.vertices: v.co = Vector((v.co.x * c - v.co.y * s, v.co.x * s + v.co.y * c, v.co.z))
mid = [v.co for v in ob.data.vertices if 0.26 * H / 1.2 < v.co.z < 0.50]
ex = max(abs(c.x) for c in mid); ey = max(abs(c.y) for c in mid)
if ey > ex: rotz(math.pi / 2)
feet = [v.co.y for v in ob.data.vertices if v.co.z < 0.07]
if sum(feet) / max(1, len(feet)) > 0: rotz(math.pi)
print("ORIENT ex=%.3f ey=%.3f feetY=%.3f" % (ex, ey, sum(feet) / max(1, len(feet))))
for i in range(12):
    sl = [v.co for v in ob.data.vertices if i * 0.1 <= v.co.z < (i + 1) * 0.1]
    if sl: print("SLICE z%.1f  x[%.2f,%.2f] y[%.2f,%.2f] n=%d" % (i * 0.1, min(c.x for c in sl), max(c.x for c in sl), min(c.y for c in sl), max(c.y for c in sl), len(sl)))

# 표면 펴기 + 부드러운 음영
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0004); bpy.ops.object.mode_set(mode='OBJECT')
sm = ob.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.5; sm.iterations = 8
bpy.ops.object.modifier_apply(modifier="smooth")
for p in ob.data.polygons: p.use_smooth = True
# 폴리곤 줄이기 (캐릭터가 화면에 30명 넘게 나오므로). 세 번째 인자로 목표 삼각형 수를 줄 수 있음 (기본 18000)
TARGET = int(args[2]) if len(args) > 2 else 18000
tri_n = sum(len(p.vertices) - 2 for p in ob.data.polygons)
if tri_n > TARGET:
    dm = ob.modifiers.new("dec", "DECIMATE"); dm.ratio = TARGET / tri_n
    bpy.ops.object.modifier_apply(modifier="dec")
    for p in ob.data.polygons: p.use_smooth = True

co =[v.co.copy() for v in ob.data.vertices]
# 목 높이: 몸통보다 앞뒤로 튀어나온(=딸기 모자) 부분의 가장 낮은 높이
hood = [c.z for c in co if c.y > 0.17]   # 등 쪽으로 튀어나온 부분 = 모자 (몸통 등은 0.11까지)
zn = (min(hood) if hood else 0.55) - 0.005
# 몸통 반폭: 목 바로 아래 높이대에서, 팔을 뺀 중앙부 폭 추정 → 팔은 그 바깥
body = [abs(c.x) for c in co if 0.30 < c.z < zn - 0.03]
body.sort(); xs = body[int(len(body) * 0.62)] if body else 0.16     # 팔이 시작되는 x
hand = max((c for c in co if c.z < zn), key=lambda c: abs(c.x))       # 손끝
zh = 0.25                                                               # 엉덩이(다리 시작) 높이
legs = [c for c in co if c.z < 0.12]; lx = sum(abs(c.x) for c in legs) / max(1, len(legs))
print("MEASURE zn=%.3f xs=%.3f hand=(%.3f,%.3f) lx=%.3f" % (zn, xs, abs(hand.x), hand.z, lx))

# 뼈대
arm = bpy.data.armatures.new("Armature"); ao = bpy.data.objects.new("Armature", arm); bpy.context.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode='EDIT')
def bone(name, head, tail, parent=None):
    b = arm.edit_bones.new(name); b.head = head; b.tail = tail
    if parent: b.parent = arm.edit_bones[parent]
    return b
bone("Hips", (0, 0, zh), (0, 0, zh + 0.1)); bone("Spine", (0, 0, zh + 0.1), (0, 0, zn), "Hips"); bone("Head", (0, 0, zn), (0, 0, H), "Spine")
sz = zn - 0.05
for s, n in ((-1, "Right"), (1, "Left")):
    hx = s * abs(hand.x)
    bone(n + "Arm", (s * xs, 0, sz), (hx * 0.92, 0, hand.z + 0.03), "Spine")
    bone(n + "Hand", (hx * 0.92, 0, hand.z + 0.03), (hx, 0, hand.z - 0.02), n + "Arm")
    bone(n + "UpLeg", (s * lx, 0, zh), (s * lx, 0, 0.12), "Hips")
    bone(n + "Leg", (s * lx, 0, 0.12), (s * lx, 0, 0.01), n + "UpLeg")
bpy.ops.object.mode_set(mode='OBJECT')

# 가중치: 영역별로 직접 지정 (경계는 3cm에 걸쳐 섞음)
def blend(x, a, b): return max(0.0, min(1.0, (x - a) / (b - a)))
groups = {n: ob.vertex_groups.new(name=n) for n in ["Hips", "Spine", "Head", "RightArm", "LeftArm", "RightUpLeg", "LeftUpLeg", "RightLeg", "LeftLeg"]}
for i, c in enumerate(co):
    w = {}
    if c.z >= zn: w["Head"] = 1.0
    else:
        side = "Right" if c.x < 0 else "Left"
        a = blend(abs(c.x), xs - 0.01, xs + 0.025) * blend(c.z, zh - 0.02, zh + 0.03)   # 팔 (엉덩이 위, 몸통 바깥)
        if a > 0: w[side + "Arm"] = a
        rest = 1.0 - a
        if c.z < zh + 0.02:
            lg = 1.0 - blend(c.z, zh - 0.03, zh + 0.02)                                 # 다리
            kn = 1.0 - blend(c.z, 0.10, 0.14)                                           # 무릎 아래
            w[side + "Leg"] = rest * lg * kn; w[side + "UpLeg"] = rest * lg * (1 - kn); w["Hips"] = rest * (1 - lg)
        else:
            sp = blend(c.z, zh + 0.05, zh + 0.12); w["Spine"] = rest * sp; w["Hips"] = rest * (1 - sp)
    for n, val in w.items():
        if val > 1e-4: groups[n].add([i], val, 'REPLACE')

md = ob.modifiers.new("Armature", "ARMATURE"); md.object = ao; ob.parent = ao
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = ao
bpy.ops.export_scene.gltf(filepath=DST, export_format='GLB', export_yup=True, export_skins=True, export_animations=False)
print("EXPORTED", DST, "verts", len(co), "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons))
