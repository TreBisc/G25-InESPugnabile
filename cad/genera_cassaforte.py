"""
Caveu IOT - generatore parametrico della cassaforte stampabile 3D.

Uso (da terminale, nella cartella del progetto):
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python cad/genera_cassaforte.py

Produce:
    cad/caveu_cassaforte.blend   modello assemblato (parti + componenti di riferimento)
    stl/*.stl                    ogni parte gia' orientata per la stampa (mm)
    cad/render/*.png             render di controllo

Sistema di riferimento (mm): X = larghezza, Y = profondita' (fronte verso -Y),
Z = altezza. Il piano Y=0 e' la faccia frontale del corpo; la porta sta davanti (Y<0).
"""

import bpy, bmesh, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STL_DIR = os.path.join(ROOT, "stl")
RENDER_DIR = os.path.join(HERE, "render")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# PARAMETRI PRINCIPALI
# --------------------------------------------------------------------------
W, D, H = 200.0, 170.0, 160.0      # corpo esterno
T = 5.0                            # spessore pareti corpo
DOOR_T = 25.0                      # spessore totale porta (guscio + coperchio)
COVER_T = 3.0                      # coperchio posteriore porta
SHELL_T = 3.0                      # pareti guscio porta
DX0, DX1 = -99.0, 100.0            # estensione X della porta (1 mm gioco lato cerniera)
CX = (DX0 + DX1) / 2               # centro porta
HX, HY = -107.0, -DOOR_T / 2       # asse cerniera
KN_R, PIN_R = 7.0, 1.65            # raggio nocche, foro perno (tondino 3 mm)

# Serratura: chiavistello a cremagliera + pignone (modulo 1.5, 16 denti)
GEAR_M, GEAR_Z = 1.5, 16
RP = GEAR_M * GEAR_Z / 2           # raggio primitivo 12
BOLT_Y0, BOLT_Y1 = 27.2, 35.2      # spessore chiavistello / pignone
BOLT_ZROOT, BOLT_ZTOP = 76.0, 86.0 # barra piena
PZ_LINE = BOLT_ZROOT - 1.25 * GEAR_M
PX, PZ = 56.0, PZ_LINE - RP        # asse pignone (= asse albero servo/stepper)
BOLT_LEN, BOLT_TRAVEL = 60.0, 16.0
BOLT_X_LOCK = 94.0                 # punta chiavistello in posizione chiusa
BASE_T = 4.0                       # piastra supporti motore
H1, H2 = (36.0, 47.0), (80.0, 47.0)  # fori comuni supporto servo/stepper sul coperchio

# Componenti elettronici
LCD_Z = 128.0                      # centro LCD 1602
KEY_Z = 62.0                       # centro tastierino 4x4 a membrana
MAG = (90.0, 140.0)                # magnete porta / sensore hall

# Cella di carico TAL220 80x12.7x12.7
LC_Y = 65.0
LC_Z0 = 12.0
LC_S = 12.7

# --------------------------------------------------------------------------
# SCENA
# --------------------------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = 'MILLIMETERS'

def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c

C_PRINT = new_coll("Parti_stampa")
C_ALT = new_coll("Alternativa_stepper")
C_REF = new_coll("Riferimenti_componenti")
TMP = new_coll("_tmp")

# --------------------------------------------------------------------------
# HELPER GEOMETRIA
# --------------------------------------------------------------------------
def bm_to_obj(bm, name, coll):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob

def box(name, x0, x1, y0, y1, z0, z1, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((x1 if v.co.x > 0 else x0,
                       y1 if v.co.y > 0 else y0,
                       z1 if v.co.z > 0 else z0))
    return bm_to_obj(bm, name, coll or TMP)

def cyl(name, c, r, axis, a0, a1, seg=64, r2=None, coll=None):
    """Cilindro/cono lungo asse 'X','Y','Z' da a0 ad a1. c = centro nel piano ortogonale.
    r = raggio all'estremo a0, r2 = raggio all'estremo a1."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r if r2 is None else r2, depth=a1 - a0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, (a0 + a1) / 2))
    if axis == 'Y':
        bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Rotation(math.radians(-90), 4, 'X'))
        bmesh.ops.translate(bm, verts=bm.verts, vec=(c[0], 0, c[1]))
    elif axis == 'X':
        bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Rotation(math.radians(90), 4, 'Y'))
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, c[0], c[1]))
    else:
        bmesh.ops.translate(bm, verts=bm.verts, vec=(c[0], c[1], 0))
    return bm_to_obj(bm, name, coll or TMP)

def prism(name, pts, a0, a1, plane='XZ', coll=None):
    bm = bmesh.new()
    def P(u, v, w):
        return (u, w, v) if plane == 'XZ' else (u, v, w)
    b = [bm.verts.new(P(u, v, a0)) for u, v in pts]
    t = [bm.verts.new(P(u, v, a1)) for u, v in pts]
    caps = [bm.faces.new(b[::-1]), bm.faces.new(t)]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))
    bmesh.ops.triangulate(bm, faces=caps)
    return bm_to_obj(bm, name, coll or TMP)

def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = ob.name
    bpy.data.meshes.remove(old)

def boolean(target, tools, op):
    if not isinstance(tools, (list, tuple)):
        tools = [tools]
    for t in tools:
        if t is None:
            continue
        m = target.modifiers.new("B", 'BOOLEAN')
        m.operation = op
        m.solver = 'EXACT'
        m.object = t
        apply_mods(target)
        bpy.data.objects.remove(t, do_unlink=True)

def cut(target, tools):
    boolean(target, tools, 'DIFFERENCE')

def fuse(target, tools):
    boolean(target, tools, 'UNION')

def move_to(ob, coll):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

def text_tool(s, size, x, y, z, depth):
    """Mesh di testo nel piano XZ, leggibile da davanti, profonda 2*depth centrata in y."""
    try:
        cu = bpy.data.curves.new("txt", 'FONT')
        cu.body = s
        cu.size = size
        cu.extrude = depth
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.space_character = 1.2   # lettere separate: evita glifi sovrapposti nella booleana
        ob = bpy.data.objects.new("txt_c", cu)
        TMP.objects.link(ob)
        ob.rotation_euler = (math.radians(90), 0, 0)
        ob.location = (x, y, z)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        me.transform(ob.matrix_world)
        bpy.data.objects.remove(ob, do_unlink=True)
        tool = bpy.data.objects.new("txt", me)
        TMP.objects.link(tool)
        return tool
    except Exception as e:  # il testo e' solo estetico
        print("Testo saltato:", e)
        return None

def gear_pts(z, m, cx, cy, phase=0.0, pa=20.0, backlash=0.15, n_inv=8):
    rp = m * z / 2
    rb = rp * math.cos(math.radians(pa))
    ra = rp + m
    rf = rp - 1.25 * m
    inv = lambda a: math.tan(a) - a
    a_p = math.radians(pa)
    def psi(r):
        a = math.acos(min(1.0, rb / r))
        return math.pi / (2 * z) - backlash / (2 * rp) + inv(a_p) - inv(a)
    r0 = max(rb, rf)
    pts = []
    for i in range(z):
        tc = phase + 2 * math.pi * i / z
        rs = [r0 + (ra - r0) * k / n_inv for k in range(n_inv + 1)]
        seq = [(rf, tc - psi(r0))]
        seq += [(r, tc - psi(r)) for r in rs]
        seq += [(ra, tc - psi(ra) + 2 * psi(ra) * k / 3) for k in (1, 2)]
        seq += [(r, tc + psi(r)) for r in reversed(rs)]
        seq += [(rf, tc + psi(r0))]
        a0, a1 = tc + psi(r0), tc + 2 * math.pi / z - psi(r0)
        seq += [(rf, a0 + (a1 - a0) * k / 4) for k in (1, 2, 3)]
        pts += [(cx + r * math.cos(a), cy + r * math.sin(a)) for r, a in seq]
    return pts

def pinion(name, coll):
    g = prism(name, gear_pts(GEAR_Z, GEAR_M, PX, PZ, phase=math.pi / 2 + math.pi / GEAR_Z),
              BOLT_Y0, BOLT_Y1, coll=coll)
    fuse(g, cyl("hub", (PX, PZ), 6.0, 'Y', BOLT_Y0 + 0.01, BOLT_Y1 - 0.01))  # nessun effetto visivo, garantisce mozzo pieno
    return g

def tag(ob, rgba, coll=None):
    ob.color = rgba
    mat = bpy.data.materials.new(ob.name + "_mat")
    mat.diffuse_color = rgba
    ob.data.materials.append(mat)
    if coll:
        move_to(ob, coll)
    return ob

# --------------------------------------------------------------------------
# 1) CORPO
# --------------------------------------------------------------------------
body = box("corpo", -W / 2, W / 2, 0, D, 0, H)
cut(body, box("cav", -W / 2 + T, W / 2 - T, -1, D - T, T, H - T))

parts = []
# guide per il pannello del vano elettronica (canale 3.4 mm a y=129..132.4)
for sx in (-1, 1):
    x0, x1 = (91.0, 95.5) if sx > 0 else (-95.5, -91.0)
    parts += [box("rib", x0, x1, 127.0, 129.0, T - 0.5, H - T + 0.5),
              box("rib", x0, x1, 132.4, 134.4, T - 0.5, H - T + 0.5)]
# blocco riscontro del chiavistello (parete destra)
parts.append(box("riscontro", 83.0, 95.5, 20.0, 45.0, 64.0, 94.0))
# supporto sensore hall porta chiusa
parts.append(box("hall", 86.0, 95.5, 1.0, 12.0, 118.0, 148.0))
# nocche cerniera lato corpo
for z0, z1 in ((T, 45.0), (115.0, H - T)):
    parts.append(cyl("nocca", (HX, HY), KN_R, 'Z', z0, z1))
    parts.append(box("ponte", HX, -99.5, HY, 8.0, z0, z1))
fuse(body, parts)

holes = [
    box("tunnel_riscontro", 82.0, 94.6, BOLT_Y0 - 0.6, BOLT_Y1 + 0.6, 71.8, 86.8),
    box("tasca_hall", 87.7, 92.3, 2.0, 5.8, 136.0, 144.5),
    box("canale_hall", 88.0, 92.0, 2.5, 5.0, 117.0, 136.1),
    cyl("jack_dc", (60.0, 22.0), 4.0, 'Y', D - T - 1, D + 1),
    box("usb_c", 24.0, 36.0, D - T - 1, D + 1, 19.0, 25.0),
    cyl("perno", (HX, HY), PIN_R, 'Z', -1, H + 1, seg=32),
]
for i in range(-4, 5):  # feritoie di ventilazione posteriori
    holes.append(box("vent", i * 8 - 1.5, i * 8 + 1.5, D - T - 1, D + 1, 115.0, 140.0))
for sx in (-1, 1):
    holes.append(cyl("vite_base", (sx * 45.0, LC_Y), 1.7, 'Z', -1, T + 1, seg=32))
    holes.append(cyl("dado_base", (sx * 45.0, LC_Y), 3.75, 'Z', -0.1, 2.6, seg=6))
    holes.append(cyl("ancoraggio", (sx * 60.0, 148.0), 3.25, 'Z', -1, T + 1, seg=32))
    for fy in (15.0, 155.0):
        holes.append(cyl("piedino", (sx * 85.0, fy), 6.0, 'Z', -0.1, 1.0, seg=48))
cut(body, holes)
tag(body, (0.16, 0.17, 0.19, 1), C_PRINT)

# --------------------------------------------------------------------------
# 2) PORTA - GUSCIO FRONTALE
# --------------------------------------------------------------------------
YF = -DOOR_T                 # faccia frontale porta
YB = -COVER_T                # retro guscio (appoggio coperchio)
YI = YF + SHELL_T            # faccia interna della parete frontale
door = box("porta_guscio", DX0, DX1, YF, YB, 0, H)
cut(door, box("int", DX0 + SHELL_T, DX1 - SHELL_T, YI, YB + 1, SHELL_T, H - SHELL_T))

BOSS = [(-90.0, 9.0), (91.0, 9.0), (-90.0, 151.0), (91.0, 151.0)]
LCD_HOLES = [(CX + sx * 37.5, LCD_Z + sz * 15.5) for sx in (-1, 1) for sz in (-1, 1)]
parts = [cyl("boss", p, 4.0, 'Y', YI - 0.5, YB, seg=32) for p in BOSS]
parts += [cyl("standoff_lcd", p, 3.0, 'Y', YI - 0.5, YI + 4.0, seg=32) for p in LCD_HOLES]
parts.append(cyl("anello_buzzer", (CX, 12.0), 8.0, 'Y', YI - 0.5, YI + 6.0))
parts.append(cyl("nocca_porta", (HX, HY), KN_R, 'Z', 46.0, 114.0))
parts.append(box("ponte_porta", HX, DX0 + 1, HY - KN_R, HY + KN_R, 46.0, 114.0))
fuse(door, parts)

holes = [cyl("pilota", p, 1.4, 'Y', YI + 3, YB + 0.1, seg=24) for p in BOSS]
holes += [cyl("pilota_lcd", p, 1.1, 'Y', YI, YI + 4.1, seg=24) for p in LCD_HOLES]
holes += [
    box("finestra_lcd", CX - 36, CX + 36, YF - 1, YI + 0.1, LCD_Z - 12.5, LCD_Z + 12.5),
    box("incasso_tastierino", CX - 35, CX + 35, YF - 0.1, YF + 1.0, KEY_Z - 39, KEY_Z + 39),
    box("slot_flat", CX - 11, CX + 11, YF - 1, YI + 0.1, KEY_Z - 38.5, KEY_Z - 35.5),
    cyl("led_rosso", (CX - 20, 150.0), 2.6, 'Y', YF - 1, YI + 0.1, seg=32),
    cyl("led_verde", (CX + 20, 150.0), 2.6, 'Y', YF - 1, YI + 0.1, seg=32),
    cyl("sede_buzzer", (CX, 12.0), 6.2, 'Y', YI, YI + 6.1),
    box("tasca_rfid", -93.0, -51.0, YI - 1.8, YI + 0.1, 38.0, 102.0),
    cyl("maniglia_a", (82.0, 48.0), 2.15, 'Y', YF - 1, YI + 0.1, seg=32),
    cyl("maniglia_b", (82.0, 112.0), 2.15, 'Y', YF - 1, YI + 0.1, seg=32),
    cyl("perno", (HX, HY), PIN_R, 'Z', -1, H + 1, seg=32),
]
holes += [cyl("grill", (CX + dx, 12.0 + dz), 0.9, 'Y', YF - 1, YI + 0.1, seg=16)
          for dx, dz in ((0, 0), (-3, 0), (3, 0), (0, -3), (0, 3), (-2.6, -2.6), (2.6, 2.6), (-2.6, 2.6), (2.6, -2.6))]
ring = box("cornice_rfid", -88.0, -56.0, YF - 0.6, YF + 0.6, 50.0, 90.0)
cut(ring, box("ci", -86.8, -57.2, YF - 1, YF + 1, 51.2, 88.8))
holes.append(ring)
holes.append(text_tool("RFID", 5.0, -72.0, YF, 70.0, 0.6))
holes.append(text_tool("CAVEU IOT", 6.0, CX, YF, 105.5, 0.6))
cut(door, holes)
tag(door, (0.22, 0.24, 0.28, 1), C_PRINT)

# --------------------------------------------------------------------------
# 3) PORTA - COPERCHIO POSTERIORE CON GUIDE DEL CHIAVISTELLO
# --------------------------------------------------------------------------
cover = box("porta_coperchio", DX0, DX1, YB, 0, 0, H)
fuse(cover, [
    box("guida_1", 34.0, 42.0, -0.5, 39.0, 70.0, 92.0),
    box("guida_2", 68.0, 76.0, -0.5, 39.0, 70.0, 92.0),
    box("pad_finecorsa", -4.0, 16.0, -0.5, 27.4, 72.0, 90.0),
])
holes = [box("tunnel", 33.0, 77.0, BOLT_Y0 - 0.4, BOLT_Y1 + 0.4, 72.2, 86.4)]
for p in BOSS:
    holes.append(cyl("vite", p, 1.7, 'Y', YB - 1, 1, seg=32))
    holes.append(cyl("svasatura", p, 1.5, 'Y', -1.9, 0.01, r2=3.5, seg=40))
holes += [cyl("foro_supporto", p, 1.7, 'Y', YB - 1, 1, seg=32) for p in (H1, H2)]
holes += [
    box("passacavi", -92.0, -68.0, YB - 1, 1, 74.0, 86.0),
    box("passacavi_motore", 10.0, 26.0, YB - 1, 1, 41.0, 49.0),
    cyl("tasca_magnete", MAG, 3.1, 'Y', -2.2, 0.1, seg=32),
    cyl("pilota_fc1", (1.25, 81.0), 0.9, 'Y', 17.0, 27.5, seg=16),
    cyl("pilota_fc2", (10.75, 81.0), 0.9, 'Y', 17.0, 27.5, seg=16),
]
cut(cover, holes)
tag(cover, (0.90, 0.47, 0.12, 1), C_PRINT)

# --------------------------------------------------------------------------
# 4) CHIAVISTELLO A CREMAGLIERA
# --------------------------------------------------------------------------
p = math.pi * GEAR_M
bl = 0.15
w = p / 4 - bl / 2
t20 = math.tan(math.radians(20))
w_tip, w_root = w - GEAR_M * t20, w + 1.25 * GEAR_M * t20
z_tip = PZ_LINE - GEAR_M
bx0, bx1 = BOLT_X_LOCK - BOLT_LEN, BOLT_X_LOCK
pts = [(bx0, BOLT_ZTOP), (bx0, BOLT_ZROOT)]
for k in range(-2, 7):
    xc = PX + k * p
    if xc - w_root < bx0 + 2 or xc + w_root > bx1 - 2:
        continue
    pts += [(xc - w_root, BOLT_ZROOT), (xc - w_tip, z_tip), (xc + w_tip, z_tip), (xc + w_root, BOLT_ZROOT)]
pts += [(bx1, BOLT_ZROOT), (bx1, BOLT_ZTOP)]
bolt = prism("chiavistello", pts, BOLT_Y0, BOLT_Y1)
tag(bolt, (0.72, 0.73, 0.76, 1), C_PRINT)

# --------------------------------------------------------------------------
# 5) PIGNONI E SUPPORTI MOTORE (servo SG90/MG90S oppure stepper 28BYJ-48)
# --------------------------------------------------------------------------
pin_servo = pinion("pignone_servo", TMP)
cut(pin_servo, [
    cyl("spline", (PX, PZ), 2.4, 'Y', BOLT_Y0 - 0.1, BOLT_Y0 + 3.5, seg=32),
    cyl("vite_squadretta", (PX, PZ), 1.1, 'Y', BOLT_Y0 - 0.1, BOLT_Y1 + 0.1, seg=24),
    cyl("lamatura", (PX, PZ), 2.5, 'Y', BOLT_Y1 - 2.5, BOLT_Y1 + 0.1, seg=32),
])
tag(pin_servo, (0.95, 0.80, 0.15, 1), C_PRINT)

pin_step = pinion("pignone_stepper", TMP)
dd = cyl("albero_dd", (PX, PZ), 2.55, 'Y', BOLT_Y0 - 0.1, BOLT_Y1 + 0.1, seg=32)
boolean(dd, box("piatti", PX - 1.6, PX + 1.6, BOLT_Y0 - 1, BOLT_Y1 + 1, PZ - 5, PZ + 5), 'INTERSECT')
cut(pin_step, dd)
tag(pin_step, (0.95, 0.80, 0.15, 1), C_ALT)

# supporto servo SG90: albero a 6 mm dall'estremita' del corpo (22.5 mm)
S_BODY_CX = PX + (22.5 / 2 - 6.0)
S_FLANGE_Y = BASE_T + 15.9
sb = box("supporto_servo", 33.0, 84.0, 0, BASE_T, 40.0, 56.0)
fuse(sb, [box("pad", 44.0, 80.0, 0, BASE_T, 55.5, 65.5)] +
     [cyl("colonna", (S_BODY_CX + s * 13.9, PZ), 3.0, 'Y', BASE_T - 0.5, S_FLANGE_Y, seg=32) for s in (-1, 1)])
cut(sb, [cyl("pilota", (S_BODY_CX + s * 13.9, PZ), 0.9, 'Y', BASE_T, S_FLANGE_Y + 0.1, seg=16) for s in (-1, 1)] +
    [cyl("foro", h, 1.7, 'Y', -1, BASE_T + 1, seg=32) for h in (H1, H2)])
tag(sb, (0.20, 0.45, 0.85, 1), C_PRINT)

# supporto stepper 28BYJ-48: albero a 8 mm dal centro motore, orecchie a 35 mm
M_CX, M_CZ = PX, PZ - 8.0
st = box("supporto_stepper", 30.0, 84.0, 0, BASE_T, 36.0, 58.0)
fuse(st, [cyl("colonna", (M_CX + s * 17.5, M_CZ), 3.5, 'Y', BASE_T - 0.5, BASE_T + 18.2, seg=32) for s in (-1, 1)])
cut(st, [cyl("pilota", (M_CX + s * 17.5, M_CZ), 1.4, 'Y', BASE_T + 4, BASE_T + 18.3, seg=16) for s in (-1, 1)] +
    [cyl("foro", h, 1.7, 'Y', -1, BASE_T + 1, seg=32) for h in (H1, H2)])
tag(st, (0.20, 0.45, 0.85, 1), C_ALT)

# --------------------------------------------------------------------------
# 6) MANIGLIA
# --------------------------------------------------------------------------
hd = box("maniglia", 76.0, 88.0, YF - 20, YF - 12, 42.0, 118.0)
fuse(hd, [box("st", 76.0, 88.0, YF - 12.5, YF, 42.0, 54.0),
          box("st", 76.0, 88.0, YF - 12.5, YF, 106.0, 118.0)])
cut(hd, [cyl("pil", (82.0, z), 1.65, 'Y', YF - 12, YF + 0.1, seg=24) for z in (48.0, 112.0)])
tag(hd, (0.08, 0.08, 0.09, 1), C_PRINT)

# --------------------------------------------------------------------------
# 7) SENSORE DI PESO: BASE CELLA + PIATTO
# --------------------------------------------------------------------------
ly0, ly1 = LC_Y - LC_S / 2, LC_Y + LC_S / 2
lcb = box("base_cella", -50.0, 50.0, LC_Y - 10, LC_Y + 10, T, T + 3)
fuse(lcb, box("rialzo", -42.0, -18.0, ly0, ly1, T + 2.5, LC_Z0))
cut(lcb, [cyl("vf", (sx * 45.0, LC_Y), 1.7, 'Z', T - 1, T + 4, seg=32) for sx in (-1, 1)] +
    [cyl("vc", (x, LC_Y), 2.2, 'Z', T - 1, LC_Z0 + 1, seg=32) for x in (-35.0, -25.0)] +
    [cyl("lam", (x, LC_Y), 4.0, 'Z', T - 0.1, T + 3.5, seg=32) for x in (-35.0, -25.0)])
tag(lcb, (0.30, 0.65, 0.45, 1), C_PRINT)

LC_TOP = LC_Z0 + LC_S
PL_Z0 = LC_TOP + 4
plat = box("piatto_peso", -88.0, 88.0, 9.0, 121.0, PL_Z0, PL_Z0 + 4)
rim = box("bordo", -88.0, 88.0, 9.0, 121.0, PL_Z0 + 3.5, PL_Z0 + 7)
cut(rim, box("bi", -86.0, 86.0, 11.0, 119.0, PL_Z0 + 3, PL_Z0 + 8))
fuse(plat, [rim, box("distanziale", 18.0, 42.0, ly0, ly1, LC_TOP, PL_Z0 + 0.5)])
cut(plat, [cyl("vp", (x, LC_Y), 2.65, 'Z', LC_TOP - 1, PL_Z0 + 5, seg=32) for x in (25.0, 35.0)] +
    [cyl("sv", (x, LC_Y), 2.65, 'Z', PL_Z0 + 4 - 2.4, PL_Z0 + 4.01, r2=5.0, seg=32) for x in (25.0, 35.0)])
tag(plat, (0.30, 0.65, 0.45, 1), C_PRINT)

# --------------------------------------------------------------------------
# 8) PANNELLO VANO ELETTRONICA (scorre nelle guide posteriori)
# --------------------------------------------------------------------------
pn = box("pannello_elettronica", -94.6, 94.6, 129.3, 132.1, T + 0.5, 152.0)
PB = [(sx * 23.0, z) for sx in (-1, 1) for z in (27.0, 93.0)]
fuse(pn, [cyl("so", q, 3.0, 'Y', 131.6, 137.0, seg=32) for q in PB])
cut(pn, [box("passacavi", -20.0, 20.0, 129.0, 133.0, 30.0, 44.0),
         box("presa", -15.0, 15.0, 129.0, 133.0, 140.0, 147.0)] +
    [cyl("pil", q, 1.1, 'Y', 132.5, 137.1, seg=16) for q in PB])
tag(pn, (0.78, 0.79, 0.80, 1), C_PRINT)

# --------------------------------------------------------------------------
# 9) COMPONENTI DI RIFERIMENTO (non si stampano)
# --------------------------------------------------------------------------
REF = []
def ref(ob, col):
    tag(ob, col, C_REF)
    REF.append(ob)
ref(box("rif_LCD1602_pcb", CX - 40, CX + 40, YI + 4, YI + 5.6, LCD_Z - 18, LCD_Z + 18), (0.1, 0.45, 0.2, 1))
ref(box("rif_LCD1602_display", CX - 35.5, CX + 35.5, YF + 0.05, YI + 4, LCD_Z - 12, LCD_Z + 12), (0.15, 0.35, 0.9, 1))
ref(box("rif_tastierino_4x4", CX - 34.5, CX + 34.5, YF - 0.6, YF + 0.95, KEY_Z - 38.5, KEY_Z + 38.5), (0.05, 0.05, 0.06, 1))
ref(box("rif_RC522", -92.0, -52.0, YI - 1.7, YI - 0.1, 40.0, 100.0), (0.1, 0.3, 0.7, 1))
sv = box("rif_servo_SG90", PX - 6.0, PX + 16.5, BASE_T, BASE_T + 22.7, PZ - 6.1, PZ + 6.1)
fuse(sv, [box("fl", S_BODY_CX - 16.1, S_BODY_CX + 16.1, S_FLANGE_Y, S_FLANGE_Y + 2.5, PZ - 6.1, PZ + 6.1),
          cyl("sh", (PX, PZ), 2.3, 'Y', BASE_T + 22.6, BOLT_Y0 + 3.3, seg=24)])
ref(sv, (0.15, 0.3, 0.8, 1))
ref(box("rif_finecorsa", -4.0, 16.0, 27.4, 33.8, 76.0, 86.0), (0.1, 0.1, 0.1, 1))
lc = box("rif_cella_carico", -40.0, 40.0, ly0, ly1, LC_Z0, LC_TOP)
cut(lc, cyl("foro_cella", (0, LC_Y), 5.0, 'Y', ly0 - 1, ly1 + 1))
ref(lc, (0.75, 0.76, 0.78, 1))
ref(box("rif_ESP32", -14.0, 14.0, 137.0, 138.6, 35.0, 90.0), (0.05, 0.05, 0.05, 1))
ref(box("rif_HX711", 30.0, 51.0, 137.0, 138.6, 40.0, 74.0), (0.6, 0.1, 0.1, 1))

# rimuove l'eventuale residuo temporaneo
for ob in list(TMP.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.collections.remove(TMP)

# --------------------------------------------------------------------------
# 10) EXPORT STL ORIENTATI PER LA STAMPA
# --------------------------------------------------------------------------
RX = lambda d: Matrix.Rotation(math.radians(d), 4, 'X')
RY = lambda d: Matrix.Rotation(math.radians(d), 4, 'Y')
PRINT_ORIENT = {
    "corpo": RX(-90),              # apertura frontale verso l'alto
    "porta_guscio": RX(90),        # faccia frontale sul piatto
    "porta_coperchio": RX(90),     # piano sul piatto, guide verso l'alto
    "chiavistello": RX(90),
    "pignone_servo": RX(90),
    "pignone_stepper": RX(90),
    "supporto_servo": RX(90),
    "supporto_stepper": RX(90),
    "maniglia": RY(90),
    "base_cella": Matrix.Identity(4),
    "piatto_peso": RX(180),        # bordo sul piatto, distanziale verso l'alto
    "pannello_elettronica": RX(90),
}

report = []
for name, rot in PRINT_ORIENT.items():
    src = bpy.data.objects[name]
    # pulizia: unisce vertici quasi coincidenti lasciati dalle booleane
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0005)
    # ripara giunzioni a T (vertice di un bordo che giace sul lato di un altro bordo)
    for _ in range(200):
        bnd = [e for e in bm.edges if len(e.link_faces) == 1]
        bverts = {v for e in bnd for v in e.verts}
        found = None
        for e in bnd:
            a, b = e.verts[0].co, e.verts[1].co
            ab = b - a
            L2 = ab.length_squared
            if L2 < 1e-12:
                continue
            for v in bverts:
                if v in e.verts:
                    continue
                t = (v.co - a).dot(ab) / L2
                if 1e-4 < t < 1 - 1e-4 and (a + ab * t - v.co).length < 1e-3:
                    found = (e, v, t)
                    break
            if found:
                break
        if not found:
            break
        e, v, t = found
        _, nv = bmesh.utils.edge_split(e, e.verts[0], t)
        bmesh.ops.pointmerge(bm, verts=[nv, v], merge_co=v.co.copy())
    bm.to_mesh(src.data)
    bm.free()
    me = src.data.copy()
    me.transform(rot)
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    me.transform(Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
    tmp = bpy.data.objects.new(name + "_export", me)
    scene.collection.objects.link(tmp)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    tmp.select_set(True)
    bpy.context.view_layer.objects.active = tmp
    bpy.ops.wm.stl_export(filepath=os.path.join(STL_DIR, name + ".stl"),
                          export_selected_objects=True, ascii_format=False, global_scale=1.0)
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    report.append((name, dims, len(me.polygons)))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.meshes.remove(me)

print("\n=== PARTI ESPORTATE (ingombro di stampa mm) ===")
for name, d, nf in report:
    print(f"{name:24s} {d[0]:7.1f} x {d[1]:7.1f} x {d[2]:7.1f}   facce={nf}")

# --------------------------------------------------------------------------
# 11) RENDER DI CONTROLLO + SALVATAGGIO
# --------------------------------------------------------------------------
C_ALT.hide_viewport = True
C_ALT.hide_render = True

world = bpy.data.worlds.new("Mondo")
world.color = (0.93, 0.93, 0.95)
scene.world = world
scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'STUDIO'
sh.color_type = 'OBJECT'
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.show_object_outline = True
scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
scene.render.film_transparent = False

cam_data = bpy.data.cameras.new("Camera")
cam_data.clip_start, cam_data.clip_end = 1, 5000
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

DOOR_SET = {"porta_guscio", "porta_coperchio", "maniglia", "chiavistello", "pignone_servo", "supporto_servo",
            "rif_LCD1602_pcb", "rif_LCD1602_display", "rif_tastierino_4x4", "rif_RC522", "rif_servo_SG90", "rif_finecorsa"}

def shot(fname, loc, target, hidden=(), lens=50, ortho=None):
    for o in scene.objects:
        if o.type == 'MESH' and o.users_collection[0] is not C_ALT:
            o.hide_render = o.name in hidden
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam_data.type = 'ORTHO'; cam_data.ortho_scale = ortho
    else:
        cam_data.type = 'PERSP'; cam_data.lens = lens
    scene.render.filepath = os.path.join(RENDER_DIR, fname)
    bpy.ops.render.render(write_still=True)

all_names = {o.name for o in scene.objects if o.type == 'MESH'}
shot("01_assemblato.png", (330, -460, 330), (0, 50, 75))
shot("02_fronte_porta.png", (CX, -600, 80), (CX, 0, 80), ortho=230)
shot("03_meccanismo_serratura.png", (190, 260, 190), (55, 15, 72),
     hidden=all_names - {"porta_coperchio", "chiavistello", "pignone_servo", "supporto_servo",
                         "rif_servo_SG90", "rif_finecorsa", "corpo"} | {"corpo"}, lens=55)
shot("04_interno_corpo.png", (150, -330, 330), (0, 90, 50), hidden=DOOR_SET, lens=40)
shot("05_retro.png", (-300, 520, 260), (0, 85, 75))
for o in scene.objects:
    o.hide_render = False

# vista in viewport: colori per oggetto
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.color_type = 'OBJECT'
                    sp.clip_start, sp.clip_end = 0.5, 5000

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "caveu_cassaforte.blend"))
print("Salvato:", os.path.join(HERE, "caveu_cassaforte.blend"))
