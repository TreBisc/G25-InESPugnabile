"""
InESPugnabile - "Monolite" (proposta A): generatore parametrico della cassaforte stampabile.

Uso (dalla cartella inESPugnabile/):
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python stampa/cad/genera_monolite.py

Produce:
    stampa/cad/monolite.blend        modello assemblato (parti + componenti di riferimento)
    stampa/stl/*.stl                 ogni parte orientata per la stampa (mm)
    stampa/cad/render/*.png          render di controllo
    in console: report parti (ingombro, volume, mesh) e controllo collisioni

Riferimento (mm): X = larghezza (0 al centro), Y = profondita' (Y=0 faccia frontale, retro verso +Y),
Z = altezza (0 = piano d'appoggio). La porta e' a sinistra-cerniera, si apre verso l'esterno.

Tutte le quote dei componenti sono nominali: vanno verificate col calibro (fase "Rilievo") e
corrette qui sotto. Ogni parte stampata e' di un solo colore (niente multimateriale).
"""

import bpy, bmesh, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STL_DIR = os.path.join(ROOT, "stl")
RENDER_DIR = os.path.join(HERE, "render")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

# ==========================================================================
# PARAMETRI
# ==========================================================================
# --- Corpo ---------------------------------------------------------------
W, H, D = 180.0, 210.0, 150.0       # ingombro esterno
T = 1.6                             # pareti (4 linee da 0.4)
T_FLOOR = 2.0                       # fondo
XI = W / 2 - T                      # faccia interna pareti laterali (87)
ZI0, ZI1 = T_FLOOR, H - T           # fondo interno, cielo interno
R_OUT = 14.0                        # raggio spigoli (token brand)
R_IN = R_OUT - T
CH_FRONT, CH_BACK = 1.0, 1.5        # smussi perimetrali

# --- Porta ---------------------------------------------------------------
G = 0.6                             # gioco porta / telaio
DOOR_X = 73.0                       # semi-larghezza porta
DOOR_Z0, DOOR_Z1 = 10.0, 106.0       # porta bassa: la fascia ospita tastierino, semaforo, display e PIR
DOOR_Y0, DOOR_Y1 = 2.0, 17.0        # porta rientrata di 2 mm, spessa 15
DOOR_R = 8.0                        # raggio angoli lato maniglia (token brand)
def door_r(r):
    """Raggi della porta: arrotondati a destra, vivi dal lato cerniera (la porta deve poter ruotare)."""
    return (r, r, 0.0, 0.0)
EDGE_R = (DOOR_Y1 - DOOR_Y0) / 2    # bordi laterali a toro intero (7.5)
AX = -DOOR_X + EDGE_R               # asse cerniera (= albero stepper)
AY = (DOOR_Y0 + DOOR_Y1) / 2
SKIN = 1.6                          # pelle frontale porta
DW = 1.6                            # pareti porta
RIB = 1.2                           # nervature porta
RIB_D = 7.0                         # profondita' nervature (non arrivano al retro)
SLEEVE_T, SLEEVE_D = 2.0, 20.0      # cornice del vano porta
PIN_R, PIN_L = 3.0, 4.0             # perno inferiore stampato sulla porta

# --- Soffitto caveau = pavimento della fascia comandi ---------------------
CEIL_Z0 = DOOR_Z1 + G               # 148.6
CEIL_Z1 = CEIL_Z0 + 2.0             # 150.6

# --- Paratia caveau / vano elettronica ------------------------------------
BAY_D = 48.4                        # profondita' del vano elettronica (breadboard + ESP32 + cavi)
COVER_Y0 = D - T                    # coperchio posteriore
PART_Y1 = COVER_Y0 - BAY_D
PART_Y0 = PART_Y1 - 1.6
CEIL_Y1 = PART_Y1
TB_Y0 = COVER_Y0 - 21.4             # inizio torrette del coperchio
NUT_Y = COVER_Y0 - 7.9              # sede dado del coperchio

# --- Pannello interfaccia (sostituibile, a scatto) ------------------------
PAN_X = 73.0
PAN_Z0, PAN_Z1 = DOOR_Z1 + 6.0, 200.0
LIP_Z = (PAN_Z0 + 6.0, 170.0)       # battute laterali (sopra restano libere per i cavi del semaforo)
PAN_R, PAN_T, PG = 8.0, 3.0, 0.3
ARMS_TOP = [(-34.0, -18.0), (18.0, 34.0)]   # ganci a scatto (x0, x1)
ARMS_BOT = [(-30.0, -18.0), (4.0, 16.0)]
HOOK_Y = 14.6                       # faccia di presa del gancio

# OLED 0,96" 128x64 SSD1306 (da verificare col calibro)
OLED_GLASS = (26.7, 19.3)
OLED_PCB = (27.3, 27.8)
OLED_HOLES = (23.5, 23.8)           # interasse fori Ø2
OLED_WIN = (24.0, 13.0)             # finestra visibile
OLED_X = -52.0                      # colonna sinistra: semaforo, poi display + buzzer, poi PIR
OLED_WIN_Z = 159.0                  # centro finestra
OLED_AA_DZ = 2.5                    # area attiva sopra il centro del vetro
OLED_PCB_DZ = -0.6                  # centro PCB rispetto al centro vetro
GLASS_Z = OLED_WIN_Z - OLED_AA_DZ

# Modulo semaforo (ordine R-G-V sulla scheda): montato ruotato di 180 gradi, da sinistra verde, giallo, rosso.
# Misure tipiche, da verificare col calibro.
TL_CX, LED_Z = -28.0, 183.0         # centro del gruppo LED
TL_LED_D = 8.0                      # diametro LED
TL_PITCH = 12.0                     # passo dei LED
TL_BAR = (40.0, 12.5)               # barra dei LED (lunghezza, altezza)
TL_STEM = (8.0, 6.0)                # gambo verso la croce
TL_CROSS = (8.0, 20.0)              # croce con i 2 fori e il connettore
TL_HOLE_DZ, TL_HOLE_D = 7.0, 3.0
TL_STANDOFF = 5.0                   # scheda 5 mm dietro il pannello: i LED sporgono di circa 3 mm
TL_PCB_T = 1.6
TL_PEG_X = TL_CX - TL_BAR[0] / 2 - TL_STEM[0] - TL_CROSS[0] / 2    # croce a sinistra (modulo ruotato)
LED_X = (TL_CX - TL_PITCH, TL_CX, TL_CX + TL_PITCH)   # verde (aperta), giallo (in apertura / guasto), rosso (chiusa)
LED_ICONS = ("aperto", "ingranaggio", "chiuso")
ICON_Z = LED_Z + 9.5                # icone incise sopra i LED
BUZ_ARC_C = (-16.0, 150.0)          # centro archi griglia buzzer
BUZ_POS = (-16.0, 156.0)            # buzzer Ø12
# PIR HC-SR501: cupola sul fronte, in basso a sinistra
PIR_C = (-29.0, 130.0)
PIR_PCB = (32.0, 24.0)
PIR_DOME_D = 23.0
PIR_HOLES = 28.0                    # interasse fori Ø2
PIR_STANDOFF = 3.0
# Tastierino a membrana 4x4 (adesivo): metà destra del pannello
KEYPAD = (69.0, 77.0, 0.8)          # larghezza, altezza, spessore
KEY_X0, KEY_Z0 = 1.5, PAN_Z0 + 5.5
KEY_RIBBON = 22.0                   # larghezza del flat (8 poli)
BUZ_R = 6.0

# --- Stepper 28BYJ-48 (apre la porta, albero = asse cerniera) -------------
ST_R, ST_H = 14.0, 19.0
ST_OFF = 8.0                        # albero fuori centro
ST_EAR = 17.5                       # fori orecchie a ±17.5 dal centro
ST_SHAFT_L = 10.0                   # albero sotto la flangia (boss compreso)
SCX, SCY = AX, AY + ST_OFF          # centro motore
CAP_SCREWS = [(-80.0, 40.0), (-51.0, 40.0)]

# --- Servo SG90 (serratura) -----------------------------------------------
SV_L, SV_W, SV_H = 22.8, 12.2, 22.7
SV_TAB_L, SV_TAB_T, SV_TAB_D = 32.2, 2.5, 4.3   # alette 4.3 mm sotto la faccia superiore
SV_SHAFT_E = 5.9                    # albero a 5.9 mm da un'estremita'
SV_FACE_Y = 32.0                    # faccia superiore servo (albero verso la porta)
SVX = XI - 0.5 - SV_W / 2           # 80.4
SVZ = (DOOR_Z0 + DOOR_Z1) / 2       # 79
SV_Z0 = SVZ - SV_SHAFT_E            # corpo servo da SV_Z0 a SV_Z0 + SV_L
LATCH_Y0, LATCH_Y1 = 27.0, 31.0
LATCH_L, LATCH_W = 21.0, 6.0
KP_X0, KP_X1 = 62.0, 65.0           # piastra di riscontro sulla porta
KP_Y1 = 34.5

# --- Sensore Hall KY-024 (HW-484) + magnete al neodimio nella porta ------
MAG_D, MAG_T = 18.0, 4.0            # magnete dell'utente: poco meno di una moneta da 10 cent, alto due monete
MAG_X = 47.0                        # angolo in alto a destra della porta
MAG_Y0 = DOOR_Y0 + SKIN             # appoggiato alla pelle frontale, asse lungo Y
MAG_Z = DOOR_Z1 - DW - MAG_D / 2 - 0.4
HALL_PCB = (15.0, 36.0)             # schedina (x, y) sul pavimento della fascia
HALL_Y0 = 10.0                      # inizio schedina, lato sensore

# --- IR HW-201 (tipo FC-51) ------------------------------------------------
IR_PCB = (31.0, 14.0, 1.6)          # lunghezza, larghezza, spessore
IR_LED_DZ = 4.0                     # LED Ø5 a ±4 mm dal centro
IR1_X, IR1_Z = -82.0, 60.0          # n.1 fine corsa porta aperta: spalla sinistra, dietro la cornice
IR1_ANG = 25.0                      # fori inclinati: guidano i LED verso la porta aperta a 90 gradi
IR2_X, IR2_Z = 45.0, 26.0           # n.2 oggetto nel caveau: in basso sulla paratia, lato vano

# --- Simbolo blu sulla porta ----------------------------------------------
BADGE_C = (0.0, (DOOR_Z0 + DOOR_Z1) / 2)    # simbolo centrato sulla porta
BADGE_S = 0.40                      # mm per unita' del viewBox del logo
BADGE_CLR = 0.15
BADGE_PROUD = 0.6
SIMBOLO_COLORE = "nero"             # "blu" (logo-blu) o "nero" (logo-inchiostro, monocromo: una bobina in meno)

# --- DHT22 nella paratia --------------------------------------------------
DHT = (25.1, 15.1, 7.7)
DHT_POS = (-50.0, 70.0)             # dentro il caveau, sulla paratia
TSL = (19.0, 13.5)                  # GY-2561 (TSL2561): misura la luce nel caveau
TSL_POS = (-15.0, 70.0)
MPU = (21.0, 16.0)                  # GY-521 (MPU-6050): sollevamento / scossoni
MPU_POS = (-15.0, 95.0)

# --- Vano elettronica ------------------------------------------------------
BB = (-82.5, 82.5, 132.0, 187.0)    # breadboard 830 punti (165 x 55), con EVA-ZM1 e HW-131 sopra
ULN = (20.0, 55.0, 60.0, 92.0)      # driver ULN2003
ULN_HOLES = (29.5, 26.5)
POSTS = [(-80.0, 30.0), (80.0, 30.0), (-80.0, 120.0), (80.0, 120.0)]
BATT = (48.5, 26.5, 17.5)           # batteria 9V (x, y, z), sdraiata sul fondo del vano
BATT_Z0 = T_FLOOR + 4.3             # appoggiata su due slitte: esce dallo sportello
HW_SW = (66.0, 142.0)               # interruttore dell'HW-131 visto dal retro (da verificare)
RESET_POS = (-70.0, 120.0)          # pulsante di reset incassato nel coperchio
IR1_HOLE = (-66.0, 12.0)            # passaggio del cavo dell'IR n.1 nella paratia
COVER_SCREWS = [(-79.0, 12.0), (79.0, 12.0), (-79.0, 199.0), (79.0, 199.0)]

# Stima del costo (come uno slicer: 2 perimetri + strati pieni ~0.85 mm su ogni superficie, riempimento 15%)
SHELL_T, INFILL, PLA_DENS = 0.85, 0.15, 1.24
PLA_EUR_KG = 20.0                   # prezzo indicativo PLA, euro al kg
SCARTO = 1.07                       # brim, supporti, spurgo

NUT_F, NUT_T = 5.6, 2.5             # sede dado M3 (chiave 5.5 + gioco)
M3_CLR = 1.7                        # raggio foro passante M3

# ==========================================================================
# SCENA
# ==========================================================================
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
C_REF = new_coll("Riferimenti_componenti")
TMP = new_coll("_tmp")

# ==========================================================================
# HELPER GEOMETRIA
# ==========================================================================
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
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
    return bm_to_obj(bm, name, coll or TMP)

def cyl(name, c, r, axis, a0, a1, seg=64, r2=None, coll=None):
    """Cilindro lungo 'X','Y','Z' da a0 ad a1; c = centro nel piano ortogonale
    (per 'Y': (x, z); per 'Z': (x, y); per 'X': (y, z))."""
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
    """Prisma da un poligono 2D. plane 'XZ': pts=(x,z) estruso lungo Y; 'XY': pts=(x,y) lungo Z."""
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
    bmesh.ops.triangulate(bm, faces=caps, ngon_method='EAR_CLIP')
    return bm_to_obj(bm, name, coll or TMP)

def rrect_pts(u0, u1, v0, v1, r, seg=10):
    """Rettangolo raccordato antiorario. r scalare oppure (basso-dx, alto-dx, alto-sx, basso-sx)."""
    rs = tuple(r) if isinstance(r, (tuple, list)) else (r, r, r, r)
    lim = min(u1 - u0, v1 - v0) / 2 - 1e-3
    pts = []
    for (U, V, a0, su, sv), rr in zip(((u1, v0, -90, -1, 1), (u1, v1, 0, -1, -1), (u0, v1, 90, 1, -1), (u0, v0, 180, 1, 1)), rs):
        rr = max(0.0, min(rr, lim))
        if rr < 1e-3:
            pts.append((U, V))
            continue
        cu, cv = U + su * rr, V + sv * rr
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cu + rr * math.cos(a), cv + rr * math.sin(a)))
    return pts

def hull_obj(name, pts3, coll=None):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts3]
    res = bmesh.ops.convex_hull(bm, input=vs)
    dead = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    bmesh.ops.delete(bm, geom=dead, context='VERTS')
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    return bm_to_obj(bm, name, coll or TMP)

def rounded_slab(name, x0, x1, z0, z1, r, sections, coll=None):
    """Profilo XZ raccordato estruso lungo Y; sections=[(y, rientro)] per gli smussi a 45 gradi."""
    pts3 = []
    for y, ins in sections:
        pts3 += [(u, y, v) for u, v in rrect_pts(x0 + ins, x1 - ins, z0 + ins, z1 - ins, r - ins)]
    return hull_obj(name, pts3, coll)

def rr_y(name, x0, x1, z0, z1, r, y0, y1, coll=None):
    """Lastra con angoli raccordati in vista frontale, da y0 a y1."""
    return prism(name, rrect_pts(x0, x1, z0, z1, r), y0, y1, 'XZ', coll)

def cap_pts(p, q, h, seg=8):
    """Capsula (segmento p-q con estremi tondi, semi-larghezza h) nel piano."""
    (x0, y0), (x1, y1) = p, q
    a = math.atan2(y1 - y0, x1 - x0)
    pts = []
    for k in range(seg + 1):
        t = a - math.pi / 2 - math.pi * k / seg
        pts.append((x0 + h * math.cos(t), y0 + h * math.sin(t)))
    for k in range(seg + 1):
        t = a + math.pi / 2 - math.pi * k / seg
        pts.append((x1 + h * math.cos(t), y1 + h * math.sin(t)))
    return pts

def circle_pts(cx, cy, r, seg=48):
    return [(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]

def arc_slot_pts(cx, cz, r, w, half_deg, seg=24, cap=8):
    """Settore di corona circolare (come gli archi del logo): angoli misurati dalla verticale."""
    h = w / 2
    a0, a1 = math.radians(-half_deg), math.radians(half_deg)
    P = lambda R, a: (cx + R * math.sin(a), cz + R * math.cos(a))
    pts = [P(r + h, a0 + (a1 - a0) * k / seg) for k in range(seg + 1)]
    e = P(r, a1)
    for k in range(1, cap):          # tappo tondo all'estremo a1
        t = a1 + math.pi * k / cap
        d = (math.sin(t), math.cos(t))
        pts.append((e[0] + h * d[0], e[1] + h * d[1]))
    pts += [P(r - h, a1 - (a1 - a0) * k / seg) for k in range(seg + 1)]
    s = P(r, a0)
    for k in range(1, cap):
        t = a0 + math.pi + math.pi * k / cap
        d = (math.sin(t), math.cos(t))
        pts.append((s[0] + h * d[0], s[1] + h * d[1]))
    return pts

def offset_convex(pts, c):
    """Allarga un poligono convesso antiorario di c."""
    n = len(pts)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = dy / L, -dx / L
        lines.append(((x0 + nx * c, y0 + ny * c), (dx, dy)))
    out = []
    for i in range(n):
        (p, d), (q, e) = lines[i - 1], lines[i]
        den = d[0] * e[1] - d[1] * e[0]
        t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        out.append((p[0] + d[0] * t, p[1] + d[1] * t))
    return out

def hex_pts(cx, cy, flats):
    R = flats / math.sqrt(3)
    return [(cx + R * math.cos(math.radians(30 + 60 * k)), cy + R * math.sin(math.radians(30 + 60 * k))) for k in range(6)]

def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = ob.name
    bpy.data.meshes.remove(old)

def boolean(target, tools, op, keep=False):
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
        if not keep:
            bpy.data.objects.remove(t, do_unlink=True)

def cut(target, tools):
    boolean(target, tools, 'DIFFERENCE')

def fuse(target, tools):
    boolean(target, tools, 'UNION')

def inter(target, tools):
    boolean(target, tools, 'INTERSECT')

def move_to(ob, coll):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

def tag(ob, rgba, coll=None):
    ob.color = rgba
    mat = bpy.data.materials.new(ob.name + "_mat")
    mat.diffuse_color = rgba
    ob.data.materials.append(mat)
    if coll:
        move_to(ob, coll)
    return ob

def union_all(name, objs):
    base = objs[0]
    base.name = name
    for o in objs[1:]:
        fuse(base, o)
    return base

# Colori dei filamenti (Workbench, colore oggetto)
NERO = (0.075, 0.08, 0.09, 1)
BIANCO = (0.93, 0.93, 0.915, 1)
BLU = (0.10, 0.26, 1.0, 1)

# Logo (simbolo del brand) in coordinate del viewBox, convertito nel piano XZ
LOGO_VC = (8.7 + 96.0) / 2
def logo_polys(cx, cz, s, c=0.0):
    X = lambda u: cx + (u - 50) * s
    Z = lambda v: cz - (v - LOGO_VC) * s
    ccx, ccz = X(50), Z(50)
    w = 6.6 * s + 2 * c
    polys = [arc_slot_pts(ccx, ccz, 38 * s, w, 52.0), arc_slot_pts(ccx, ccz, 24 * s, w, 52.0),
             circle_pts(ccx, ccz, 13.7 * s + c)]
    trap = [(X(36.7), Z(96)), (X(63.3), Z(96)), (X(57.6), Z(56)), (X(42.4), Z(56))]   # antiorario in XZ
    polys.append(offset_convex(trap, c) if c else trap)
    return polys

def logo_bbox(cx, cz, s):
    return (cx - 33.24 * s, cx + 33.24 * s, cz - (96 - LOGO_VC) * s, cz + (LOGO_VC - 8.7) * s)

# ==========================================================================
# 1) CORPO (nero) - stampato con la faccia frontale sul piatto
# ==========================================================================
def fuse_in(target, ob):
    """Unisce al corpo un volume ritagliato 1 mm dentro la sagoma esterna (niente sporgenze sugli spigoli tondi)."""
    inter(ob, rr_y("clip", -W / 2 + 1, W / 2 - 1, 1.0, H - 1.0, R_OUT - 1, -1, D + 1))
    fuse(target, ob)

body = rounded_slab("corpo", -W / 2, W / 2, 0, H, R_OUT,
                    [(0, CH_FRONT), (CH_FRONT, 0), (D - CH_BACK, 0), (D, CH_BACK)])
cut(body, hull_obj("cav", [(u, y, v) for y in (T, D + 1) for u, v in rrect_pts(-XI, XI, ZI0, ZI1, R_IN)]))

# cornice del vano porta, soffitto del caveau, blocco del perno inferiore
so = DOOR_X + G + SLEEVE_T
fuse(body, rr_y("cornice", -so, so, DOOR_Z0 - G - SLEEVE_T, DOOR_Z1 + G + SLEEVE_T, door_r(DOOR_R + G + SLEEVE_T), 1.0, SLEEVE_D))
fuse(body, box("soffitto", -XI - 0.5, XI + 0.5, T - 0.5, PART_Y0 - 0.2, CEIL_Z0, CEIL_Z1))
fuse(body, box("blocco_perno", AX - 4.5, AX + 4.5, 1.0, SLEEVE_D, ZI0 - 0.5, DOOR_Z0 - G))
# vano porta
cut(body, rr_y("vano_porta", -DOOR_X - G, DOOR_X + G, DOOR_Z0 - G, DOOR_Z1 + G, door_r(DOOR_R + G), -1, SLEEVE_D + 0.01))
# sede del perno inferiore: asola aperta verso il fronte (la porta si infila da davanti)
cut(body, [box("asola", AX - PIN_R - 0.2, AX + PIN_R + 0.2, -1, AY, DOOR_Z0 - PIN_L - 0.4, DOOR_Z0 - G + 0.01),
           cyl("asola_fondo", (AX, AY), PIN_R + 0.2, 'Z', DOOR_Z0 - PIN_L - 0.4, DOOR_Z0 - G + 0.01)])

# apertura del pannello interfaccia + battute laterali
cut(body, rr_y("vano_pannello", -PAN_X - PG, PAN_X + PG, PAN_Z0 - PG, PAN_Z1 + PG, PAN_R + PG, -1, T + 0.01))
for s in (-1, 1):
    x0, x1 = sorted((s * (PAN_X + PG - 2.0), s * (PAN_X + PG + 3.0)))
    xo0, xo1 = sorted((s * (PAN_X + PG), s * (PAN_X + PG + 3.0)))
    fuse(body, box("battuta", x0, x1, PAN_T, PAN_T + 1.5, LIP_Z[0], LIP_Z[1]))
    fuse(body, box("battuta_attacco", xo0, xo1, T - 0.2, PAN_T + 0.01, LIP_Z[0], LIP_Z[1]))
# nervature su cui scattano i ganci del pannello
for x0, x1 in ARMS_TOP:
    fuse(body, box("nerv_sup", x0, x1, HOOK_Y - 3.0, HOOK_Y, PAN_Z1 - 0.5, ZI1 + 0.5))
for x0, x1 in ARMS_BOT:
    fuse(body, box("nerv_inf", x0, x1, HOOK_Y - 3.0, HOOK_Y, CEIL_Z1 - 0.5, PAN_Z0 + 0.5))

# stepper: foro albero + incavo per il boss
cut(body, [cyl("foro_albero", (AX, AY), 3.0, 'Z', CEIL_Z0 - 1, CEIL_Z1 + 1),
           cyl("incavo_boss", (AX, AY), 5.0, 'Z', CEIL_Z1 - 1.6, CEIL_Z1 + 1)])
# torrette con dado per la staffa dello stepper (sotto il soffitto, dietro la porta)
for bx, by in CAP_SCREWS:
    fuse(body, box("torretta", bx - 4.5, bx + 4.5, by - 4.5, by + 4.5, CEIL_Z0 - 4.0, CEIL_Z0 + 0.5))
    cut(body, [cyl("foro", (bx, by), M3_CLR, 'Z', CEIL_Z0 - 5, CEIL_Z1 + 1),
               prism("dado", hex_pts(bx, by, NUT_F), CEIL_Z0 - 3.2, CEIL_Z0 - 3.2 + NUT_T, 'XY'),
               box("dado_slot", bx - NUT_F / 2, bx + NUT_F / 2, by, by + 6, CEIL_Z0 - 3.2, CEIL_Z0 - 3.2 + NUT_T)])

# colonna del servo con slitta a T (il servo entra di lato, da sinistra)
PIL_Z1 = SV_Z0 + SV_L + 6.0
fuse(body, box("colonna_servo", 72.0, XI + 0.5, SV_FACE_Y, 60.0, SV_Z0 - 9.0, PIL_Z1))
fuse(body, box("canalina_cavo", 76.8, XI + 0.5, 48.8, 58.2, PIL_Z1 - 1.0, CEIL_Z0 + 0.5))
cut(body, [box("slitta_corpo", 70.0, XI - 0.2, SV_FACE_Y - 0.1, SV_FACE_Y + SV_H + 0.5, SV_Z0 - 0.2, SV_Z0 + SV_L + 0.2),
           box("slitta_alette", 70.0, XI - 0.2, SV_FACE_Y + SV_TAB_D - 0.2, SV_FACE_Y + SV_TAB_D + SV_TAB_T + 0.3,
               SV_Z0 + SV_L / 2 - SV_TAB_L / 2 - 0.2, SV_Z0 + SV_L / 2 + SV_TAB_L / 2 + 0.2),
           box("canale_cavo_servo", 78.4, XI - 1.2, 50.4, 56.6, SV_Z0 + SV_L - 1, CEIL_Z1 + 1)])

# sensore Hall: culla della schedina sul pavimento della fascia + foro per il sensore sopra il magnete
hx0, hx1 = MAG_X - HALL_PCB[0] / 2 - 0.3, MAG_X + HALL_PCB[0] / 2 + 0.3
hy1 = HALL_Y0 + HALL_PCB[1] + 0.3
culla = box("culla_hall", hx0 - 1.6, hx1 + 1.6, HALL_Y0, hy1 + 1.6, CEIL_Z1 - 0.5, CEIL_Z1 + 4)
cut(culla, [box("int", hx0, hx1, HALL_Y0 - 1, hy1, CEIL_Z1 - 1, CEIL_Z1 + 5),
            box("uscita_cavo", MAG_X - 4, MAG_X + 4, hy1 - 1, hy1 + 3, CEIL_Z1 + 1, CEIL_Z1 + 5)])
fuse(body, culla)
cut(body, box("foro_hall", MAG_X - 3, MAG_X + 3, MAG_Y0 - 0.5, MAG_Y0 + MAG_T + 1.0, CEIL_Z0 - 1, CEIL_Z1 + 1))

# IR n.1 (fine corsa porta aperta): fori inclinati nella cornice sinistra + guide per la schedina
IR1_DIR = Vector((math.sin(math.radians(IR1_ANG)), -math.cos(math.radians(IR1_ANG)), 0))
def ir1_led_axis(dz, r, back, front):
    """Cilindro coassiale al foro inclinato del LED (centro sulla faccia frontale)."""
    c = cyl("led_ir", (IR1_X, IR1_Z + dz), r, 'Y', -front, back, seg=32)
    m = Matrix.Translation((IR1_X, 0.8, 0)) @ Matrix.Rotation(math.radians(IR1_ANG), 4, 'Z') @ Matrix.Translation((-IR1_X, -0.8, 0))
    c.data.transform(m)
    return c
cut(body, [ir1_led_axis(sz * IR_LED_DZ, 2.7, 4.0, 3.0) for sz in (-1, 1)])
IR1_PX = (-81.5, -79.9)             # schedina verticale, componenti verso la parete
iz0, iz1 = IR1_Z - IR_PCB[1] / 2, IR1_Z + IR_PCB[1] / 2
for zr, zs in (((iz0 - 2.6, iz0 + 0.6), (iz0 - 0.2, iz0 + 1.6)), ((iz1 - 0.6, iz1 + 2.6), (iz1 - 1.6, iz1 + 0.2))):
    rail = box("guida_ir1", -XI - 0.5, IR1_PX[1] + 1.0, 6.0, 34.0, *zr)
    cut(rail, box("cava", IR1_PX[0] - 0.2, IR1_PX[1] + 0.2, 5.0, 35.0, *zs))
    fuse_in(body, rail)

# slitte per la batteria 9V sul fondo del vano elettronica
for s in (-1, 1):
    x0, x1 = sorted((s * (BATT[0] / 2 - 6.0), s * (BATT[0] / 2 + 0.4)))
    fuse_in(body, box("slitta_batt", x0, x1, COVER_Y0 - BATT[1] - 6.0, COVER_Y0 - 0.2, ZI0 - 0.5, BATT_Z0))
    gx0, gx1 = sorted((s * (BATT[0] / 2 + 0.4), s * (BATT[0] / 2 + 2.0)))
    fuse_in(body, box("sponda_batt", gx0, gx1, COVER_Y0 - BATT[1] - 6.0, COVER_Y0 - 0.2, ZI0 - 0.5, BATT_Z0 + 6.0))

# battute della paratia
for s in (-1, 1):
    x0, x1 = sorted((s * (XI - 3.0), s * (XI + 0.5)))
    fuse_in(body, box("batt_par_lat", x0, x1, PART_Y0 - 3, PART_Y0, ZI0 - 0.5, ZI1 + 0.5))
fuse_in(body, box("batt_par_fondo", -XI - 0.5, XI + 0.5, PART_Y0 - 3, PART_Y0, ZI0 - 0.5, ZI0 + 3))
fuse(body, box("batt_par_cielo", -XI, XI, PART_Y0 - 3, PART_Y0, CEIL_Z0 - 3, CEIL_Z0 + 0.5))
fuse_in(body, box("batt_par_tetto", -XI - 0.5, XI + 0.5, PART_Y0 - 3, PART_Y0, ZI1 - 3, ZI1 + 0.5))

# torrette d'angolo per il coperchio posteriore (vite + dado in sede laterale)
for sx, cz in COVER_SCREWS:
    s = 1 if sx > 0 else -1
    x0, x1 = sorted((s * 73.0, s * (XI + 0.5)))
    z0, z1 = (ZI0 - 0.5, 21.0) if cz < H / 2 else (190.0, ZI1 + 0.5)
    # torretta con smusso a 45 gradi verso il piatto (si stampa senza supporti)
    xw = s * (XI + 0.5)
    zw = z0 if cz < H / 2 else z1
    pts = [(x, y, z) for x in (x0, x1) for y in (TB_Y0, COVER_Y0) for z in (z0, z1)]
    pts += [(xw, TB_Y0 - 14.0, z) for z in (z0, z1)] + [(x, TB_Y0 - 14.0, zw) for x in (x0, x1)]
    fuse_in(body, hull_obj("torretta_cop", pts))
    nx0, nx1 = sorted((sx, s * 72.0))
    cut(body, [cyl("foro_cop", (sx, cz), M3_CLR, 'Y', TB_Y0 - 7, COVER_Y0 + 1),
               prism("dado_cop", hex_pts(sx, cz, NUT_F), NUT_Y, NUT_Y + NUT_T, 'XZ'),
               box("slot_cop", nx0, nx1, NUT_Y, NUT_Y + NUT_T, cz - NUT_F / 2, cz + NUT_F / 2)])
tag(body, NERO, C_PRINT)

# ==========================================================================
# 2) PORTA (bianca) - stampata con la faccia frontale sul piatto
# ==========================================================================
def door_plan_pts(inset=0.0):
    """Pianta della porta (antioraria): bordi laterali con smusso frontale a 45 gradi (corda del cerchio
    di raggio EDGE_R attorno all'asse: la porta ruota senza toccare il telaio) e quarto di cerchio sul retro.
    inset > 0 restituisce la stessa sagoma rientrata (pareti di spessore costante)."""
    r = EDGE_R
    pts = [(-AX, AY - r)]                        # smusso destro: da davanti al fianco
    for k in range(9):                           # quarto di cerchio destro, dal fianco al retro
        a = math.radians(90 * k / 8)
        pts.append((-AX + r * math.cos(a), AY + r * math.sin(a)))
    for k in range(9):                           # quarto di cerchio sinistro, dal retro al fianco
        a = math.radians(90 + 90 * k / 8)
        pts.append((AX + r * math.cos(a), AY + r * math.sin(a)))
    pts.append((AX, AY - r))                     # smusso sinistro: dal fianco al fronte
    return offset_convex(pts, -inset) if inset else pts

door = rr_y("porta", -DOOR_X, DOOR_X, DOOR_Z0, DOOR_Z1, door_r(DOOR_R), DOOR_Y0, DOOR_Y1)
inter(door, prism("pianta", door_plan_pts(), DOOR_Z0 - 1, DOOR_Z1 + 1, 'XY'))
# vaschetta aperta dietro: pelle frontale SKIN, pareti DW
cav = prism("cav_porta", door_plan_pts(DW), DOOR_Z0 + DW, DOOR_Z1 - DW, 'XY')
fuse(cav, box("cav_retro", AX, -AX, AY, DOOR_Y1 + 1, DOOR_Z0 + DW, DOOR_Z1 - DW))
inter(cav, rr_y("lim", -DOOR_X + DW, DOOR_X - DW, DOOR_Z0 + DW, DOOR_Z1 - DW, door_r(DOOR_R - DW), DOOR_Y0 + SKIN, DOOR_Y1 + 1))
cut(door, cav)

def door_solid(ob):
    """Limita un volume a 0.3 mm dentro la sagoma della porta e lo unisce alla porta."""
    e = 0.3
    inter(ob, rr_y("lim", -DOOR_X + e, DOOR_X - e, DOOR_Z0 + e, DOOR_Z1 - e, door_r(DOOR_R - e), DOOR_Y0 + e, DOOR_Y1 - e))
    inter(ob, prism("pianta", door_plan_pts(e), DOOR_Z0 - 1, DOOR_Z1 + 1, 'XY'))
    fuse(door, ob)

bx0, bx1, bz0, bz1 = logo_bbox(BADGE_C[0], BADGE_C[1], BADGE_S)
BK = (bx0 - 2.5, bx1 + 2.5, bz0 - 2.5, bz1 + 2.5)     # piastrina del simbolo
door_solid(box("blocco_cerniera_sup", -DOOR_X, AX + 8.5, DOOR_Y0, DOOR_Y1, DOOR_Z1 - 14, DOOR_Z1))
door_solid(box("blocco_cerniera_inf", -DOOR_X, AX + 8.5, DOOR_Y0, DOOR_Y1, DOOR_Z0, DOOR_Z0 + 12))
for zc in (DOOR_Z0 + 0.25 * (DOOR_Z1 - DOOR_Z0), DOOR_Z0 + 0.75 * (DOOR_Z1 - DOOR_Z0)):
    door_solid(box("nerv_orizz", -DOOR_X, DOOR_X, DOOR_Y0, DOOR_Y0 + SKIN + RIB_D, zc - RIB / 2, zc + RIB / 2))
for xc in (-28.0, 28.0):
    door_solid(box("nerv_vert", xc - RIB / 2, xc + RIB / 2, DOOR_Y0, DOOR_Y0 + SKIN + RIB_D, DOOR_Z0, DOOR_Z1))
door_solid(box("nerv_riscontro", KP_X0 - 0.5, KP_X1 + 0.5, DOOR_Y0, DOOR_Y1, SVZ - 19, SVZ + 21))
# anello del magnete a disco (inserito da dietro, contro la pelle frontale)
ring = cyl("anello_magnete", (MAG_X, MAG_Z), MAG_D / 2 + 0.2 + 1.2, 'Y', DOOR_Y0, MAG_Y0 + MAG_T + 0.6, seg=64)
cut(ring, cyl("sede", (MAG_X, MAG_Z), MAG_D / 2 + 0.2, 'Y', MAG_Y0 - 0.01, DOOR_Y1 + 2, seg=64))
door_solid(ring)
# piastra di riscontro del chiavistello (sporge dietro la porta)
kp = box("riscontro", KP_X0, KP_X1, DOOR_Y1 - 2, KP_Y1, SVZ - 9, SVZ + 9)
cut(kp, box("finestra", KP_X0 - 1, KP_X1 + 1, LATCH_Y0 - 0.7, LATCH_Y1 + 0.7, SVZ - LATCH_W / 2 - 0.7, SVZ + LATCH_W / 2 + 0.7))
fuse(door, kp)
# perno inferiore e sede a D per l'albero dello stepper
pin = cyl("perno", (AX, AY), PIN_R, 'Z', DOOR_Z0 - PIN_L + 0.6, DOOR_Z0 + 1, seg=48)
fuse(pin, cyl("smusso_perno", (AX, AY), PIN_R - 0.6, 'Z', DOOR_Z0 - PIN_L, DOOR_Z0 - PIN_L + 0.61, r2=PIN_R, seg=48))
fuse(door, pin)
dsock = cyl("sede_albero", (AX, AY), 2.65, 'Z', DOOR_Z1 - 8, DOOR_Z1 + 1, seg=48)
inter(dsock, box("piatti", AX - 1.6, AX + 1.6, AY - 5, AY + 5, DOOR_Z1 - 9, DOOR_Z1 + 2))
cut(door, dsock)
# finestre del simbolo blu nella pelle frontale
cut(door, union_all("fin_logo", [prism("fin_logo", p, DOOR_Y0 - 1, DOOR_Y0 + SKIN + 0.01 + 0.3 * i, 'XZ')
                                  for i, p in enumerate(logo_polys(BADGE_C[0], BADGE_C[1], BADGE_S, BADGE_CLR))]))
tag(door, BIANCO, C_PRINT)

# ==========================================================================
# 3) SIMBOLO (blu) - piastrina inserita da dietro, i rilievi escono dalle finestre
# ==========================================================================
badge = rr_y("simbolo", BK[0], BK[1], BK[2], BK[3], 3.0, DOOR_Y0 + SKIN, DOOR_Y0 + SKIN + 1.6)
for p in logo_polys(BADGE_C[0], BADGE_C[1], BADGE_S):
    fuse(badge, prism("rilievo", p, DOOR_Y0 - BADGE_PROUD, DOOR_Y0 + SKIN + 0.5, 'XZ'))
tag(badge, BLU if SIMBOLO_COLORE == "blu" else NERO, C_PRINT)

# ==========================================================================
# 4) PANNELLO INTERFACCIA (nero) - sostituibile, a scatto
# ==========================================================================
panel = rr_y("pannello_interfaccia", -PAN_X, PAN_X, PAN_Z0, PAN_Z1, PAN_R, 0.0, PAN_T)
# finestra OLED con svaso frontale
ww, wh = OLED_WIN
cut(panel, hull_obj("fin_oled", [(u, y, v) for y, e in ((-0.01, 1.0), (1.0, 0.0), (PAN_T + 0.1, 0.0))
                                 for u, v in rrect_pts(OLED_X - ww / 2 - e, OLED_X + ww / 2 + e, OLED_WIN_Z - wh / 2 - e, OLED_WIN_Z + wh / 2 + e, 1.0 + e)]))
gw, gh = OLED_GLASS
cut(panel, box("sede_vetro", OLED_X - gw / 2 - 0.2, OLED_X + gw / 2 + 0.2, 1.6, PAN_T + 0.1, GLASS_Z - gh / 2 - 0.2, GLASS_Z + gh / 2 + 0.2))
pcz = GLASS_Z + OLED_PCB_DZ
for sx in (-1, 1):
    for sz in (-1, 1):
        fuse(panel, cyl("perno_oled", (OLED_X + sx * OLED_HOLES[0] / 2, pcz + sz * OLED_HOLES[1] / 2), 0.9, 'Y', PAN_T - 0.5, PAN_T + 4.0, seg=24))
# semaforo: fori per i LED + 2 distanziali con piolo nei fori della croce
cut(panel, [cyl("foro_led", (x, LED_Z), TL_LED_D / 2 + 0.2, 'Y', -1, PAN_T + 1, seg=48) for x in LED_X])
for sz in (-1, 1):
    fuse(panel, cyl("distanziale_tl", (TL_PEG_X, LED_Z + sz * TL_HOLE_DZ), 3.0, 'Y', PAN_T - 0.5, PAN_T + TL_STANDOFF, seg=32))
    fuse(panel, cyl("piolo_tl", (TL_PEG_X, LED_Z + sz * TL_HOLE_DZ), TL_HOLE_D / 2 - 0.2, 'Y', PAN_T + TL_STANDOFF - 0.1,
                    PAN_T + TL_STANDOFF + TL_PCB_T + 1.4, seg=24))
# PIR: foro per la cupola + 2 distanziali con piolo
cut(panel, cyl("foro_pir", PIR_C, PIR_DOME_D / 2 + 0.25, 'Y', -1, PAN_T + 1, seg=64))
for sx in (-1, 1):
    fuse(panel, cyl("distanziale_pir", (PIR_C[0] + sx * PIR_HOLES / 2, PIR_C[1]), 2.0, 'Y', PAN_T - 0.5, PAN_T + PIR_STANDOFF, seg=24))
    fuse(panel, cyl("piolo_pir", (PIR_C[0] + sx * PIR_HOLES / 2, PIR_C[1]), 0.85, 'Y', PAN_T + PIR_STANDOFF - 0.1, PAN_T + PIR_STANDOFF + 3.0, seg=16))
# icone incise sopra i LED (stato = colore + icona): lucchetto aperto, ingranaggio, lucchetto chiuso
def gear_cutter(cx, cz):
    """Ingranaggio pieno a 6 denti con foro centrale, come un'unica sagoma (niente schegge tra tratti)."""
    pts = []
    for k in range(72):
        a = math.radians(5 * k)
        r = 2.5 if (5 * k) % 60 < 25 else 1.9
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    g = prism("ico_ingranaggio", pts, -0.5, 0.5, 'XZ')
    cut(g, cyl("foro", (cx, cz), 0.85, 'Y', -1, 1, seg=24))
    return g

def icon_segments(kind, cx, cz):
    arc = [(cx + 1.3 * math.cos(math.radians(180 - 30 * k)), cz + 1.0 + 1.3 * math.sin(math.radians(180 - 30 * k))) for k in range(7)]
    segs = list(zip(arc[:-1], arc[1:])) + [((cx - 1.3, cz - 0.4), (cx - 1.3, cz + 1.0))]
    if kind == "chiuso":
        return segs + [((cx + 1.3, cz - 0.4), (cx + 1.3, cz + 1.0))]
    return segs + [((cx + 1.3, cz + 1.0), (cx + 1.3, cz + 0.7))]      # aperto: gamba destra corta
icons = []
for kind, x in zip(LED_ICONS, LED_X):
    if kind == "ingranaggio":
        icons.append(gear_cutter(x, ICON_Z))
        continue
    for p, q in icon_segments(kind, x, ICON_Z):
        icons.append(prism("ico", cap_pts(p, q, 0.35), -0.5, 0.5, 'XZ'))
    if kind in ("aperto", "chiuso"):
        icons.append(box("ico_corpo", x - 2.0, x + 2.0, -0.5, 0.5, ICON_Z - 2.6, ICON_Z - 0.4))
cut(panel, icons)
# tastierino a membrana: zona piana a destra + asola per il flat (nascosta sotto il tastierino)
kx = KEY_X0 + KEYPAD[0] / 2
cut(panel, rr_y("asola_flat", kx - KEY_RIBBON / 2, kx + KEY_RIBBON / 2, KEY_Z0 + 2.0, KEY_Z0 + 4.5, 1.0, -1, PAN_T + 1))

# buzzer: griglia ad archi (come i segnali del logo) + anello di tenuta
cut(panel, [prism("arco", arc_slot_pts(BUZ_ARC_C[0], BUZ_ARC_C[1], r, 2.2, 52.0), -1, PAN_T + 1, 'XZ') for r in (6.0, 11.0)])
fuse(panel, cyl("anello_buzzer", BUZ_POS, BUZ_R + 1.4, 'Y', PAN_T - 0.5, PAN_T + 6, seg=48))
cut(panel, cyl("sede_buzzer", BUZ_POS, BUZ_R + 0.2, 'Y', PAN_T + 0.01, PAN_T + 7, seg=48))
# ganci a scatto
def tooth_obj(x0, x1, yz):
    """Dente: profilo nel piano YZ estruso lungo X."""
    bm = bmesh.new()
    b = [bm.verts.new((x0, y, z)) for y, z in yz]
    t = [bm.verts.new((x1, y, z)) for y, z in yz]
    caps = [bm.faces.new(b[::-1]), bm.faces.new(t)]
    n = len(yz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))
    bmesh.ops.triangulate(bm, faces=caps, ngon_method='EAR_CLIP')
    return bm_to_obj(bm, "dente", TMP)

for x0, x1 in ARMS_TOP:
    zr = PAN_Z1 - 3.5
    fuse(panel, box("braccio", x0, x1, PAN_T - 0.5, HOOK_Y + 1.5, zr, zr + 1.5))
    fuse(panel, tooth_obj(x0 + 0.3, x1 - 0.3, [(HOOK_Y, zr + 1.0), (HOOK_Y + 2.4, zr + 1.0), (HOOK_Y + 2.4, zr + 2.0),
                                   (HOOK_Y + 0.7, zr + 4.0), (HOOK_Y, zr + 4.0)]))
for x0, x1 in ARMS_BOT:
    zr = PAN_Z0 + 2.0
    fuse(panel, box("braccio", x0, x1, PAN_T - 0.5, HOOK_Y + 1.5, zr, zr + 1.5))
    fuse(panel, tooth_obj(x0 + 0.3, x1 - 0.3, [(HOOK_Y, zr + 0.5), (HOOK_Y, zr - 2.5), (HOOK_Y + 0.7, zr - 2.5),
                                   (HOOK_Y + 2.4, zr - 1.5), (HOOK_Y + 2.4, zr + 0.5)]))
tag(panel, NERO, C_PRINT)

# ==========================================================================
# 6) STAFFA STEPPER (nera) - blocca il motore sulle orecchie, 2 viti M3
# ==========================================================================
cap = box("staffa_stepper", -84.0, -47.0, 5.6, 44.0, CEIL_Z1 + 1.0, CEIL_Z1 + ST_H + 2.0)
for bx, by in CAP_SCREWS:
    fuse(cap, box("piede", bx - 4.0, bx + 4.0, by - 4.0, by + 4.0, CEIL_Z1, CEIL_Z1 + 1.5))
cut(cap, [cyl("alloggio_motore", (SCX, SCY), ST_R + 0.2, 'Z', CEIL_Z1 - 1, CEIL_Z1 + ST_H + 0.2),
          box("uscita_cavi", SCX - 8.5, SCX + 8.5, SCY + 7, SCY + 20.5, CEIL_Z1 - 1, CEIL_Z1 + 17.0)])
for bx, by in CAP_SCREWS:
    cut(cap, [cyl("foro", (bx, by), M3_CLR, 'Z', CEIL_Z1 - 1, CEIL_Z1 + 30),
              cyl("lamatura", (bx, by), 3.2, 'Z', CEIL_Z1 + 3.0, CEIL_Z1 + 30)])
tag(cap, NERO, C_PRINT)

# ==========================================================================
# 7) CHIAVISTELLO (nero) - montato sulla squadretta del servo (posizione: chiuso)
# ==========================================================================
latch = prism("chiavistello", cap_pts((SVX, SVZ), (SVX - LATCH_L + LATCH_W / 2, SVZ), LATCH_W / 2), LATCH_Y0, LATCH_Y1, 'XZ')
fuse(latch, cyl("mozzo", (SVX, SVZ), 6.0, 'Y', LATCH_Y0, LATCH_Y1))
cut(latch, [cyl("foro_vite", (SVX, SVZ), 1.5, 'Y', LATCH_Y0 - 1, LATCH_Y1 + 1, seg=24),
            cyl("sede_mozzo", (SVX, SVZ), 3.7, 'Y', LATCH_Y0 + 0.5, LATCH_Y1 + 1, seg=32),
            prism("sede_squadretta", [(SVX + 1, SVZ - 3.3), (SVX - 18, SVZ - 2.3), (SVX - 18, SVZ + 2.3), (SVX + 1, SVZ + 3.3)],
                  LATCH_Y1 - 1.6, LATCH_Y1 + 1, 'XZ')])
tag(latch, NERO, C_PRINT)

# ==========================================================================
# 8) PARATIA (nera) - separa caveau e vano, porta breadboard e driver
# ==========================================================================
pz0, pz1 = ZI0 + 0.25, ZI1 - 0.25        # alta fino al cielo: chiude anche la fascia verso il vano
part = rr_y("paratia", -XI + 0.25, XI - 0.25, pz0, pz1, R_IN - 0.25, PART_Y0, PART_Y1)
cut(part, rr_y("finestra_cavi", -60, 60, 190, 204, 3.0, PART_Y0 - 1, PART_Y1 + 1))
cut(part, cyl("passaggio_ir1", IR1_HOLE, 5.0, 'Y', PART_Y0 - 1, PART_Y1 + 1, seg=32))
dx, dz = DHT_POS
fuse(part, box("rinforzo_dht", dx - DHT[0] / 2 - 2, dx + DHT[0] / 2 + 2, PART_Y1 - 0.5, PART_Y1 + 1.6, dz - DHT[1] / 2 - 2, dz + DHT[1] / 2 + 2))
cut(part, box("sede_dht", dx - DHT[0] / 2 - 0.2, dx + DHT[0] / 2 + 0.2, PART_Y0 + 0.8, PART_Y1 + 2, dz - DHT[1] / 2 - 0.2, dz + DHT[1] / 2 + 0.2))
# TSL2561: finestra verso il caveau, schedina sul lato vano (sensore rivolto alla paratia)
tx, tz = TSL_POS
cut(part, [cyl("finestra_tsl", (tx - 2.0, tz), 3.0, 'Y', PART_Y0 - 1, PART_Y1 + 1, seg=32),
           cyl("svaso_tsl", (tx - 2.0, tz), 4.2, 'Y', PART_Y0 - 0.01, PART_Y0 + 1.0, r2=3.0, seg=32)])
for sz in (-1, 1):
    p = (tx + 6.5, tz + sz * 4.5)
    fuse(part, cyl("distanziale_tsl", p, 2.5, 'Y', PART_Y1 - 0.5, PART_Y1 + 1.2, seg=24))
    fuse(part, cyl("piolo_tsl", p, 1.3, 'Y', PART_Y1 + 1.1, PART_Y1 + 4.2, seg=16))
# MPU-6050: due pioli, scheda rigida sulla paratia
mx, mzp = MPU_POS
for sx in (-1, 1):
    p = (mx + sx * 7.6, mzp - MPU[1] / 2 + 2.5)
    fuse(part, cyl("distanziale_mpu", p, 2.5, 'Y', PART_Y1 - 0.5, PART_Y1 + 3.0, seg=24))
    fuse(part, cyl("piolo_mpu", p, 1.3, 'Y', PART_Y1 + 2.9, PART_Y1 + 6.0, seg=16))
# IR n.2 (oggetto nel caveau): LED nei fori verso il caveau, schedina su un distanziale lato vano
cut(part, [cyl("foro_ir2", (IR2_X - 12.5, IR2_Z + sz * IR_LED_DZ), 2.7, 'Y', PART_Y0 - 1, PART_Y1 + 1, seg=32) for sz in (-1, 1)])
fuse(part, cyl("distanziale_ir2", (IR2_X + 7.5, IR2_Z), 3.0, 'Y', PART_Y1 - 0.5, PART_Y1 + 7.4, seg=24))
fuse(part, cyl("piolo_ir2", (IR2_X + 7.5, IR2_Z), 1.3, 'Y', PART_Y1 + 7.3, PART_Y1 + 10.4, seg=16))
cut(part, [box("griglia_dht", dx - 10.5, dx + 10.5, PART_Y0 - 1, PART_Y0 + 1.5, dz - 6 + 3.5 * k, dz - 6 + 3.5 * k + 2.0) for k in range(4)])
x0, x1, z0, z1 = BB
for cx, cz, sx, sz in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x0, z1, 1, -1), (x1, z1, -1, -1)):
    xa, xb = sorted((cx - sx * 1.5, cx + sx * 10))
    za, zb = sorted((cz - sz * 1.5, cz + sz * 10))
    fuse(part, box("guida_bb", xa, xb, PART_Y1 - 0.5, PART_Y1 + 3, *sorted((cz - sz * 1.5, cz))))
    fuse(part, box("guida_bb", *sorted((cx - sx * 1.5, cx)), PART_Y1 - 0.5, PART_Y1 + 3, za, zb))
ux = (ULN[0] + ULN[1]) / 2
uz = (ULN[2] + ULN[3]) / 2
for sx in (-1, 1):
    for sz in (-1, 1):
        p = (ux + sx * ULN_HOLES[0] / 2, uz + sz * ULN_HOLES[1] / 2)
        fuse(part, cyl("distanziale", p, 3.0, 'Y', PART_Y1 - 0.5, PART_Y1 + 5, seg=32))
        fuse(part, cyl("piolo", p, 1.3, 'Y', PART_Y1 + 4.9, PART_Y1 + 8, seg=24))
for px, pz in POSTS:
    fuse(part, cyl("colonnina", (px, pz), 4.0, 'Y', PART_Y1 - 0.5, COVER_Y0 - 0.2, seg=32))
    cut(part, cyl("colonnina_cava", (px, pz), 2.2, 'Y', PART_Y1 + 1.0, COVER_Y0, seg=32))
tag(part, NERO, C_PRINT)

# ==========================================================================
# 9) COPERCHIO POSTERIORE (nero) - 4 viti M3
# ==========================================================================
cover = rr_y("coperchio_posteriore", -XI + 0.25, XI - 0.25, ZI0 + 0.25, ZI1 - 0.25, R_IN - 0.25, COVER_Y0, D)
cut(cover, [cyl("foro", (sx, cz), M3_CLR, 'Y', COVER_Y0 - 1, D + 1, seg=24) for sx, cz in COVER_SCREWS])
cut(cover, rr_y("passacavo_usb", -8, 8, 190, 201, 2.0, COVER_Y0 - 1, D + 1))       # cavo USB per programmare la scheda
cut(cover, [rr_y("feritoia", 8 if sx > 0 else -60, 60 if sx > 0 else -8, 30 + 9 * k, 34.5 + 9 * k, 2.25, COVER_Y0 - 1, D + 1)
           for sx in (-1, 1) for k in range(18)])
# vano batteria: apertura per lo sportello, tacca per l'unghia, scanalature per i dentini
DOOR_OP = (-27.0, 27.0, BATT_Z0 - 0.3, BATT_Z0 + 19.7)
cut(cover, rr_y("apertura_batt", DOOR_OP[0], DOOR_OP[1], DOOR_OP[2], DOOR_OP[3], 2.0, COVER_Y0 - 1, D + 1))
cut(cover, rr_y("tacca_unghia", DOOR_OP[0] - 3.0, DOOR_OP[0] + 1.0, DOOR_OP[2] + 6, DOOR_OP[3] - 6, 1.5, COVER_Y0 - 1, D + 1))
cut(cover, [cyl("scanalatura", (COVER_Y0 + T / 2, zz), 0.65, 'X', -20, 20, seg=16) for zz in (DOOR_OP[2], DOOR_OP[3])])
# interruttore dell'HW-131 e pulsante di reset incassato
cut(cover, rr_y("foro_interruttore", HW_SW[0] - 7, HW_SW[0] + 7, HW_SW[1] - 7, HW_SW[1] + 7, 3.0, COVER_Y0 - 1, D + 1))
rx, rz = RESET_POS
cup = box("sede_reset", rx - 4.5, rx + 4.5, COVER_Y0 - 5.0, COVER_Y0 + 0.2, rz - 4.5, rz + 4.5)
cut(cup, box("int", rx - 3.2, rx + 3.2, COVER_Y0 - 6.0, COVER_Y0 + 0.1, rz - 3.2, rz + 3.2))
fuse(cover, cup)
cut(cover, cyl("foro_reset", RESET_POS, 1.75, 'Y', COVER_Y0 - 1, D + 1, seg=24))
tag(cover, NERO, C_PRINT)

# ==========================================================================
# 9b) SPORTELLO BATTERIA (nero) - a scatto nel coperchio, si apre con l'unghia
# ==========================================================================
sport = rr_y("sportello_batteria", DOOR_OP[0] + 0.25, DOOR_OP[1] - 0.25, DOOR_OP[2] + 0.25, DOOR_OP[3] - 0.25, 1.75, COVER_Y0, D)
fuse(sport, [cyl("dentino", (COVER_Y0 + T / 2, zz), 0.5, 'X', -18, 18, seg=16) for zz in (DOOR_OP[2], DOOR_OP[3])])
tag(sport, NERO, C_PRINT)

# ==========================================================================
# 10) COMPONENTI DI RIFERIMENTO (non si stampano)
# ==========================================================================
REF_COL = {"pcb": (0.08, 0.38, 0.22, 1), "metal": (0.72, 0.74, 0.77, 1), "servo": (0.2, 0.35, 0.85, 1),
           "dark": (0.03, 0.03, 0.035, 1), "sensor": (0.92, 0.92, 0.95, 1), "bb": (0.96, 0.96, 0.93, 1)}
def ref(ob, col):
    tag(ob, REF_COL[col] if isinstance(col, str) else col, C_REF)
    return ob

def shaft_d():
    sh = cyl("albero", (AX, AY), 2.5, 'Z', CEIL_Z1 - ST_SHAFT_L, CEIL_Z1 - 1.4, seg=24)
    inter(sh, box("piatti", AX - 1.5, AX + 1.5, AY - 4, AY + 4, CEIL_Z1 - ST_SHAFT_L - 1, CEIL_Z1))
    return sh

st = cyl("rif_stepper", (SCX, SCY), ST_R, 'Z', CEIL_Z1 + 1.0, CEIL_Z1 + ST_H)
fuse(st, [box("flangia", SCX - 21, SCX + 21, SCY - 3.5, SCY + 3.5, CEIL_Z1, CEIL_Z1 + 1.0),
          cyl("boss", (AX, AY), 4.5, 'Z', CEIL_Z1 - 1.5, CEIL_Z1 + 0.01),
          shaft_d(),
          box("scatola_cavi", SCX - 8, SCX + 8, SCY + 10, SCY + 17.5, CEIL_Z1 + 2, CEIL_Z1 + 16)])
ref(st, "metal")
sv = box("rif_servo_SG90", SVX - SV_W / 2, SVX + SV_W / 2, SV_FACE_Y, SV_FACE_Y + SV_H, SV_Z0, SV_Z0 + SV_L)
fuse(sv, [box("alette", SVX - SV_W / 2, SVX + SV_W / 2, SV_FACE_Y + SV_TAB_D, SV_FACE_Y + SV_TAB_D + SV_TAB_T,
              SV_Z0 + SV_L / 2 - SV_TAB_L / 2, SV_Z0 + SV_L / 2 + SV_TAB_L / 2),
          cyl("albero", (SVX, SVZ), 2.4, 'Y', LATCH_Y1 - 1.0, SV_FACE_Y + 0.01, seg=24)])
ref(sv, "servo")
ref(box("rif_OLED_vetro", OLED_X - gw / 2, OLED_X + gw / 2, 1.7, 3.0, GLASS_Z - gh / 2, GLASS_Z + gh / 2), "dark")
ref(box("rif_OLED_pcb", OLED_X - OLED_PCB[0] / 2, OLED_X + OLED_PCB[0] / 2, 3.0, 4.6, pcz - OLED_PCB[1] / 2, pcz + OLED_PCB[1] / 2), "pcb")
def holes(ob, pts, r, a0, a1):
    cut(ob, [cyl("foro", p, r, 'Y', a0, a1, seg=16) for p in pts])
    return ob
ty0 = PAN_T + TL_STANDOFF
tlx0 = TL_CX - TL_BAR[0] / 2
tl = box("rif_semaforo", tlx0, TL_CX + TL_BAR[0] / 2, ty0, ty0 + TL_PCB_T, LED_Z - TL_BAR[1] / 2, LED_Z + TL_BAR[1] / 2)
fuse(tl, [box("gambo", tlx0 - TL_STEM[0], tlx0 + 0.1, ty0, ty0 + TL_PCB_T, LED_Z - TL_STEM[1] / 2, LED_Z + TL_STEM[1] / 2),
          box("croce", tlx0 - TL_STEM[0] - TL_CROSS[0], tlx0 - TL_STEM[0] + 0.1, ty0, ty0 + TL_PCB_T, LED_Z - TL_CROSS[1] / 2, LED_Z + TL_CROSS[1] / 2),
          box("pettine", tlx0 - TL_STEM[0] - TL_CROSS[0] - 20.0, tlx0 - TL_STEM[0] - TL_CROSS[0] + 0.1, ty0 + 0.3, ty0 + 2.8, LED_Z - 5.0, LED_Z + 5.0)])
ref(holes(tl, [(TL_PEG_X, LED_Z + sz * TL_HOLE_DZ) for sz in (-1, 1)], TL_HOLE_D / 2, ty0 - 1, ty0 + 3), "dark")
for x, nm, c in zip(LED_X, ("verde", "giallo", "rosso"), ((0.15, 0.75, 0.3, 1), (0.95, 0.75, 0.1, 1), (0.9, 0.15, 0.15, 1))):
    led = cyl("rif_LED_" + nm, (x, LED_Z), TL_LED_D / 2, 'Y', ty0 - 11.2, ty0 - 0.01, seg=32)
    ref(led, c)
pir = box("rif_PIR", PIR_C[0] - PIR_PCB[0] / 2, PIR_C[0] + PIR_PCB[0] / 2, PAN_T + PIR_STANDOFF, PAN_T + PIR_STANDOFF + 1.6,
          PIR_C[1] - PIR_PCB[1] / 2, PIR_C[1] + PIR_PCB[1] / 2)
fuse(pir, [box("componenti", PIR_C[0] - 12, PIR_C[0] + 12, PAN_T + PIR_STANDOFF + 1.59, PAN_T + PIR_STANDOFF + 11, PIR_C[1] - 10, PIR_C[1] + 10),
           box("base_lente", PIR_C[0] - 12, PIR_C[0] + 12, PAN_T + 0.2, PAN_T + PIR_STANDOFF + 0.01, PIR_C[1] - 11.5, PIR_C[1] + 11.5)])
cut(pir, box("spazio_pannello", PIR_C[0] - 13, PIR_C[0] + 13, PAN_T - 1, PAN_T + 0.2, PIR_C[1] - 13, PIR_C[1] + 13))
fuse(pir, cyl("cupola", PIR_C, PIR_DOME_D / 2, 'Y', -7.0, PAN_T + 0.3, seg=48))
ref(holes(pir, [(PIR_C[0] + sx * PIR_HOLES / 2, PIR_C[1]) for sx in (-1, 1)], 1.0, PAN_T, PAN_T + PIR_STANDOFF + 2), (0.93, 0.93, 0.9, 1))
ref(cyl("rif_buzzer", BUZ_POS, BUZ_R, 'Y', PAN_T + 0.3, PAN_T + 9.8), "dark")
tsl = box("rif_TSL2561", tx - TSL[0] / 2, tx + TSL[0] / 2, PART_Y1 + 1.2, PART_Y1 + 2.8, tz - TSL[1] / 2, tz + TSL[1] / 2)
fuse(tsl, box("chip", tx - 3.5, tx - 0.5, PART_Y1 + 0.3, PART_Y1 + 1.21, tz - 1.5, tz + 1.5))
ref(holes(tsl, [(tx + 6.5, tz + sz * 4.5) for sz in (-1, 1)], 1.5, PART_Y1, PART_Y1 + 4), "pcb")
mpu = box("rif_MPU6050", mx - MPU[0] / 2, mx + MPU[0] / 2, PART_Y1 + 3.0, PART_Y1 + 4.6, mzp - MPU[1] / 2, mzp + MPU[1] / 2)
ref(holes(mpu, [(mx + sx * 7.6, mzp - MPU[1] / 2 + 2.5) for sx in (-1, 1)], 1.5, PART_Y1 + 2, PART_Y1 + 6), (0.12, 0.25, 0.6, 1))
ir2 = box("rif_IR2", IR2_X - IR_PCB[0] / 2, IR2_X + IR_PCB[0] / 2, PART_Y1 + 7.4, PART_Y1 + 9.0, IR2_Z - IR_PCB[1] / 2, IR2_Z + IR_PCB[1] / 2)
fuse(ir2, [cyl("led", (IR2_X - 12.5, IR2_Z + sz * IR_LED_DZ), 2.5, 'Y', PART_Y0 + 0.4, PART_Y1 + 7.41, seg=24) for sz in (-1, 1)])
fuse(ir2, box("trimmer", IR2_X - 4, IR2_X + 3, PART_Y1 + 0.6, PART_Y1 + 7.41, IR2_Z - 3.5, IR2_Z + 3.5))
ref(holes(ir2, [(IR2_X + 7.5, IR2_Z)], 1.5, PART_Y1 + 7, PART_Y1 + 10), (0.12, 0.25, 0.6, 1))
ir1 = box("rif_IR1", IR1_PX[0], IR1_PX[1], 5.0, 5.0 + IR_PCB[0], iz0, iz1)
fuse(ir1, [ir1_led_axis(sz * IR_LED_DZ, 2.5, 3.0, 5.0) for sz in (-1, 1)])
fuse(ir1, box("trimmer", IR1_PX[0] - 6.5, IR1_PX[0] + 0.01, 14.0, 21.0, IR1_Z - 3.5, IR1_Z + 3.5))
ref(ir1, (0.12, 0.25, 0.6, 1))
ref(box("rif_batteria", -BATT[0] / 2, BATT[0] / 2, COVER_Y0 - BATT[1], COVER_Y0 - 0.05, BATT_Z0, BATT_Z0 + BATT[2]), (0.95, 0.65, 0.1, 1))
ref(box("rif_HW131", 49.5, 82.5, PART_Y1 + 8.5, PART_Y1 + 26.0, BB[2] + 1, BB[3] - 1), "dark")
ref(box("rif_reset", rx - 3.0, rx + 3.0, COVER_Y0 - 5.0, COVER_Y0 - 0.05, rz - 3.0, rz + 3.0), "dark")
hall = box("rif_hall", MAG_X - HALL_PCB[0] / 2, MAG_X + HALL_PCB[0] / 2, HALL_Y0 + 0.3, HALL_Y0 + 0.3 + HALL_PCB[1], CEIL_Z1, CEIL_Z1 + 1.6)
fuse(hall, box("sensore_49E", MAG_X - 2.0, MAG_X + 2.0, MAG_Y0 + 1.0, MAG_Y0 + 2.6, CEIL_Z0 + 0.3, CEIL_Z0 + 3.3))
ref(hall, (0.75, 0.12, 0.12, 1))
ref(box("rif_tastierino", KEY_X0, KEY_X0 + KEYPAD[0], -KEYPAD[2], 0.0, KEY_Z0, KEY_Z0 + KEYPAD[1]), "dark")
ref(box("rif_DHT22", dx - DHT[0] / 2, dx + DHT[0] / 2, PART_Y0 + 1.05, PART_Y0 + 1.05 + DHT[2], dz - DHT[1] / 2, dz + DHT[1] / 2), "sensor")
ref(cyl("rif_magnete", (MAG_X, MAG_Z), MAG_D / 2, 'Y', MAG_Y0, MAG_Y0 + MAG_T, seg=48), "metal")
ref(box("rif_breadboard", BB[0], BB[1], PART_Y1, PART_Y1 + 8.5, BB[2], BB[3]), "bb")
ref(box("rif_ESP32", -55.0, 0.0, PART_Y1 + 8.5, PART_Y1 + 21.0, 145.0, 173.0), "dark")
ref(box("rif_ULN2003", ULN[0], ULN[1], PART_Y1 + 5.0, PART_Y1 + 6.6, ULN[2], ULN[3]), "pcb")

for ob in list(TMP.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.collections.remove(TMP)
TMP = new_coll("_tmp")

# ==========================================================================
# 11) CONTROLLO COLLISIONI (volumi d'intersezione, devono essere ~0)
# ==========================================================================
def copy_obj(src, name, mat=None):
    me = src.data.copy()
    if mat is not None:
        me.transform(mat)
    ob = bpy.data.objects.new(name, me)
    TMP.objects.link(ob)
    return ob

def volume(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = abs(bm.calc_volume())
    bm.free()
    return v

def clash(a, b, ma=None, mb=None):
    A = copy_obj(a, "A", ma)
    B = copy_obj(b, "B", mb)
    inter(A, B)
    v = volume(A)
    bpy.data.objects.remove(A, do_unlink=True)
    return v

def door_rot(deg):
    """Rotazione della porta attorno all'asse cerniera (negativo = verso l'esterno)."""
    return Matrix.Translation((AX, AY, 0)) @ Matrix.Rotation(math.radians(deg), 4, 'Z') @ Matrix.Translation((-AX, -AY, 0))

O = bpy.data.objects
checks = []
for a in (0, -20, -45, -70, -90):
    checks.append((f"porta aperta {abs(a)}° vs corpo", clash(O["porta"], O["corpo"], door_rot(a))))
    checks.append((f"riscontro {abs(a)}° vs chiavistello chiuso" if a == 0 else f"porta {abs(a)}° vs chiavistello aperto",
                   clash(O["porta"], O["chiavistello"], door_rot(a),
                         None if a == 0 else Matrix.Translation((SVX, 0, SVZ)) @ Matrix.Rotation(math.radians(-90), 4, 'Y') @ Matrix.Translation((-SVX, 0, -SVZ)))))
checks.append(("porta aperta 90° vs IR fine corsa", clash(O["porta"], O["rif_IR1"], door_rot(-90))))
pairs = [("pannello_interfaccia", "corpo"), ("simbolo", "porta"),
         ("staffa_stepper", "corpo"), ("staffa_stepper", "pannello_interfaccia"), ("paratia", "corpo"),
         ("coperchio_posteriore", "corpo"), ("coperchio_posteriore", "paratia"), ("sportello_batteria", "coperchio_posteriore"),
         ("chiavistello", "corpo"), ("rif_stepper", "corpo"), ("rif_stepper", "staffa_stepper"), ("rif_servo_SG90", "corpo"),
         ("rif_hall", "corpo"), ("rif_hall", "pannello_interfaccia"), ("rif_magnete", "porta"),
         ("rif_OLED_vetro", "pannello_interfaccia"), ("rif_buzzer", "pannello_interfaccia"),
         ("rif_semaforo", "pannello_interfaccia"), ("rif_semaforo", "rif_OLED_pcb"), ("rif_semaforo", "corpo"),
         ("rif_LED_verde", "pannello_interfaccia"), ("rif_LED_giallo", "pannello_interfaccia"), ("rif_LED_rosso", "pannello_interfaccia"),
         ("rif_PIR", "pannello_interfaccia"), ("rif_PIR", "staffa_stepper"), ("rif_PIR", "corpo"),
         ("rif_tastierino", "pannello_interfaccia"), ("rif_IR1", "corpo"), ("rif_IR2", "paratia"), ("rif_IR2", "corpo"),
         ("rif_TSL2561", "paratia"), ("rif_MPU6050", "paratia"), ("rif_DHT22", "paratia"),
         ("rif_breadboard", "paratia"), ("rif_HW131", "corpo"), ("rif_ESP32", "corpo"),
         ("rif_batteria", "corpo"), ("rif_batteria", "sportello_batteria"), ("rif_batteria", "coperchio_posteriore"), ("rif_batteria", "paratia"),
         ("rif_reset", "coperchio_posteriore"), ("porta", "pannello_interfaccia"), ("rif_stepper", "porta")]
for a, b in pairs:
    checks.append((f"{a} vs {b}", clash(O[a], O[b])))
print("\n=== CONTROLLO COLLISIONI (mm3) ===")
for name, v in checks:
    print(f"{'OK ' if v < 0.5 else '!! '} {name:52s} {v:9.2f}")

# ==========================================================================
# 12) EXPORT STL ORIENTATI PER LA STAMPA + REPORT
# ==========================================================================
RX = lambda d: Matrix.Rotation(math.radians(d), 4, 'X')
PRINT_ORIENT = {
    "corpo": (RX(90), "faccia frontale sul piatto"),
    "porta": (RX(90), "faccia frontale sul piatto"),
    "simbolo": (RX(-90), "piastrina sul piatto, rilievi in alto"),
    "pannello_interfaccia": (RX(90), "faccia frontale sul piatto"),
    "staffa_stepper": (RX(180), "capovolta"),
    "chiavistello": (RX(90), "piatto"),
    "paratia": (RX(90), "lato caveau sul piatto"),
    "coperchio_posteriore": (RX(-90), "faccia esterna sul piatto"),
    "sportello_batteria": (RX(-90), "faccia esterna sul piatto"),
}
COLORE = {"corpo": "nero", "porta": "bianco", "simbolo": SIMBOLO_COLORE, "pannello_interfaccia": "nero",
          "sportello_batteria": "nero", "staffa_stepper": "nero", "chiavistello": "nero",
          "paratia": "nero", "coperchio_posteriore": "nero"}

def clean_mesh(src):
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0005)
    for _ in range(300):        # giunzioni a T lasciate dalle booleane
        bnd = [e for e in bm.edges if not e.is_manifold]
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
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    V = abs(bm.calc_volume())
    A = sum(f.calc_area() for f in bm.faces)
    shell = min(V, A * SHELL_T)
    grams = (shell + (V - shell) * INFILL) / 1000.0 * PLA_DENS
    bm.to_mesh(src.data)
    bm.free()
    return nm, V / 1000.0, grams

report = []
for name, (rot, how) in PRINT_ORIENT.items():
    src = O[name]
    nm, vol, grams = clean_mesh(src)
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
    report.append((name, (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)), vol, nm, how, grams))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.meshes.remove(me)

print("\n=== PARTI ESPORTATE (ingombro di stampa mm, volume pieno, grammi stimati stampati) ===")
tot = {}
for name, d, vol, nm, how, g in report:
    print(f"{name:22s} {COLORE[name]:7s} {d[0]:6.1f} x {d[1]:6.1f} x {d[2]:6.1f}  {vol:6.1f} cm3  ~{g:4.0f} g"
          f"  non-manifold={nm}  ({how})")
    tot[COLORE[name]] = tot.get(COLORE[name], 0) + g
gt = sum(tot.values()) * SCARTO
for k, v in tot.items():
    print(f"TOTALE {k:7s} ~{v:4.0f} g")
print(f"TOTALE con scarto ~{gt:.0f} g  ->  ~{gt / 1000 * PLA_EUR_KG:.2f} euro di PLA a {PLA_EUR_KG:.0f} euro/kg")

# ==========================================================================
# 13) RENDER DI CONTROLLO + SALVATAGGIO
# ==========================================================================
for ob in list(TMP.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

world = bpy.data.worlds.new("Mondo")
world.color = (0.955, 0.955, 0.95)
scene.world = world
scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'STUDIO'
sh.color_type = 'OBJECT'
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.show_object_outline = True
sh.show_shadows = True
sh.shadow_intensity = 0.3
sh.show_specular_highlight = True
scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
scene.render.film_transparent = False

cam_data = bpy.data.cameras.new("Camera")
cam_data.clip_start, cam_data.clip_end = 1, 5000
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

def shot(fname, loc, target, hidden=(), lens=50, ortho=None):
    for o in scene.objects:
        if o.type == 'MESH':
            o.hide_render = o.name in hidden
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam_data.type = 'ORTHO'; cam_data.ortho_scale = ortho
    else:
        cam_data.type = 'PERSP'; cam_data.lens = lens
    scene.render.filepath = os.path.join(RENDER_DIR, fname)
    bpy.ops.render.render(write_still=True)

REFS = {o.name for o in C_REF.objects}
DOOR_GROUP = ["porta", "simbolo", "rif_magnete"]
shot("01_assemblato.png", (300, -430, 330), (0, 60, 100), hidden=REFS)
shot("02_fronte.png", (0, -800, 105), (0, 0, 105), hidden=REFS, ortho=300)

# porta aperta: ruoto il gruppo porta e il chiavistello in posizione aperta
saved = {n: O[n].matrix_world.copy() for n in DOOR_GROUP + ["chiavistello"]}
for n in DOOR_GROUP:
    O[n].matrix_world = door_rot(-90) @ O[n].matrix_world
O["chiavistello"].matrix_world = (Matrix.Translation((SVX, 0, SVZ)) @ Matrix.Rotation(math.radians(-90), 4, 'Y')
                                  @ Matrix.Translation((-SVX, 0, -SVZ))) @ O["chiavistello"].matrix_world
shot("03_porta_aperta.png", (230, -520, 300), (-10, 50, 95), hidden=REFS - {"rif_servo_SG90", "rif_stepper", "rif_magnete", "rif_DHT22", "rif_IR1", "rif_IR2", "rif_TSL2561"})
for n, m in saved.items():
    O[n].matrix_world = m

# sezione: copia del corpo tagliata a meta' per vedere fascia, caveau e vano
half = copy_obj(O["corpo"], "sezione_corpo")
cut(half, box("taglio", 2.0, 200, -50, 250, -50, 260))
move_to(half, scene.collection)
tag(half, NERO)
halfc = copy_obj(O["coperchio_posteriore"], "sezione_coperchio")
cut(halfc, box("taglio", 2.0, 200, -50, 250, -50, 260))
move_to(halfc, scene.collection)
tag(halfc, NERO)
everything = {o.name for o in scene.objects if o.type == 'MESH'}
shot("04_sezione.png", (600, D / 2, 105), (0, D / 2, 105),
     hidden={"corpo", "coperchio_posteriore"}, ortho=300)
shot("05_retro_vano.png", (-230, 500, 230), (0, 100, 90), hidden={"coperchio_posteriore", "sezione_corpo", "sezione_coperchio"})
shot("06_dettaglio_pannello_retro.png", (90, 140, 250), (0, 5, 175),
     hidden=everything - {"pannello_interfaccia", "rif_OLED_pcb", "rif_OLED_vetro", "rif_semaforo", "rif_LED_verde",
                          "rif_LED_giallo", "rif_LED_rosso", "rif_buzzer", "rif_PIR", "staffa_stepper", "rif_stepper", "rif_hall"}, lens=55)
bpy.data.objects.remove(half, do_unlink=True)
bpy.data.objects.remove(halfc, do_unlink=True)

# esploso
EXPL = {"porta": (0, -90, 0), "simbolo": (0, -120, 0), "rif_magnete": (0, -90, 0), "pannello_interfaccia": (0, -70, 0),
        "staffa_stepper": (0, 0, 60), "rif_stepper": (0, 0, 35), "coperchio_posteriore": (0, 110, 0),
        "sportello_batteria": (0, 140, 0), "rif_batteria": (0, 95, 0), "paratia": (0, 60, 0),
        "rif_breadboard": (0, 60, 0), "rif_ESP32": (0, 60, 0), "rif_HW131": (0, 60, 0), "rif_ULN2003": (0, 60, 0),
        "rif_DHT22": (0, 60, 0), "rif_TSL2561": (0, 60, 0), "rif_MPU6050": (0, 60, 0), "rif_IR2": (0, 60, 0),
        "chiavistello": (-40, -30, 0), "rif_servo_SG90": (-30, 0, 0)}
saved = {n: O[n].matrix_world.copy() for n in EXPL}
for n, v in EXPL.items():
    O[n].matrix_world = Matrix.Translation(v) @ O[n].matrix_world
shot("07_esploso.png", (420, -520, 380), (0, 40, 100), hidden=REFS - set(EXPL), lens=40)
for n, m in saved.items():
    O[n].matrix_world = m
for o in scene.objects:
    o.hide_render = False

for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.color_type = 'OBJECT'
                    sp.clip_start, sp.clip_end = 0.5, 5000
bpy.data.collections.remove(TMP)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "monolite.blend"))
print("Salvato:", os.path.join(HERE, "monolite.blend"))
