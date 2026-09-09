import bpy
import math
from mathutils import Vector, Matrix

HEAD_BONE_NAME = None
CLEAN_REBUILD = True
FLIP_HORIZONTAL = True
FLIP_VERTICAL = False
FLIP_EYE_LR = False

BONE_LEN_F = 0.020
OFFSET_F = 0.120
TRAVEL_F = 0.050
SPACING_F = 0.045
WIDGET_F = 1.0
FACERIG_COLLECTION = "Face"
RIGIFY_UI_ROW = 1

EYE_HL_F = 0.013
TRI_F = 0.022
EMOTE_W_F = 0.011
EMOTE_H_F = 0.006
EMOTE_LIM_F = 0.022
EMOTE_SPACING_F = 0.040
EMOTE_FWD_F = 0.050
MOUTH_SHIFT_F = 0.55
MOUTH_RAISE_F = 0.040

COL_MOUTH = (0.90, 0.20, 0.20)
COL_CORNER = (0.15, 0.85, 0.30)
COL_VISEME = (0.95, 0.85, 0.20)
COL_EYELID = (0.90, 0.15, 0.15)
COL_EYEAIM = (0.20, 0.85, 0.90)
COL_EXPRESSION = (0.65, 0.35, 0.90)
COL_LABEL = (0.95, 0.95, 0.95)

HEAD_CANDIDATES = [
    "DEF-spine.006", "spine.006", "head", "Head", "Head_M", "head_M",
    "Bip001 Head", "Bip001_Head", "Bip001Head"
]


def is_blender_3():
    return bpy.app.version[0] == 3


def find_armature_and_head(mesh_obj):
    armature = None
    for m in mesh_obj.modifiers:
        if m.type == 'ARMATURE' and m.object:
            armature = m.object
            break
    if armature is None:
        for o in bpy.data.objects:
            if o.type == 'ARMATURE' and o.name in bpy.context.view_layer.objects:
                armature = o
                break
    if armature is None:
        raise Exception("No armature found to attach the HSR face rig to.")

    names = [HEAD_BONE_NAME] if HEAD_BONE_NAME else []
    names += HEAD_CANDIDATES
    head_name = None
    for cand in names:
        if cand and cand in armature.data.bones:
            head_name = cand
            break
    if head_name is None:
        for b in armature.data.bones:
            if 'head' in b.name.lower():
                head_name = b.name
                break
    if head_name is None:
        head_name = armature.data.bones[0].name
    return armature, head_name


def face_frame(mesh_obj):
    me = mesh_obj.data
    mw = mesh_obj.matrix_world
    fwd = Vector((0.0, 0.0, 0.0))
    for v in me.vertices:
        fwd += v.normal
    fwd = mw.to_3x3() @ fwd
    if fwd.length < 1e-6:
        fwd = Vector((0.0, -1.0, 0.0))
    fwd.normalize()

    world_up = Vector((0.0, 0.0, 1.0))
    if abs(fwd.dot(world_up)) > 0.95:
        world_up = Vector((0.0, 1.0, 0.0))
    right = world_up.cross(fwd).normalized()
    up = fwd.cross(right).normalized()

    corners = [mw @ Vector(c) for c in mesh_obj.bound_box]
    mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    face_size = (mx - mn).length
    return fwd, right, up, face_size


def feature_centroid(mesh_obj, key_names):
    kb = mesh_obj.data.shape_keys.key_blocks
    basis = kb.get("Basis")
    if basis is None:
        return None
    key = None
    for kn in key_names:
        if kn in kb:
            key = kb[kn]
            break
    if key is None:
        return None

    n = len(basis.data)
    deltas = [0.0] * n
    maxd = 0.0
    for i in range(n):
        d = (key.data[i].co - basis.data[i].co).length
        deltas[i] = d
        if d > maxd:
            maxd = d
    if maxd <= 1e-9:
        return None

    thr = maxd * 0.30
    idx = [i for i in range(n) if deltas[i] >= thr]
    if not idx:
        return None

    c = Vector((0.0, 0.0, 0.0))
    for i in idx:
        c += basis.data[i].co
    c /= len(idx)
    return mesh_obj.matrix_world @ c


def pick_primary_key(keyblock, candidates):
    for c in candidates:
        if c in keyblock:
            return c
    return None


def plan_hsr_controls(mesh_obj, fwd, right, up, face_size, keyblock):
    OFFSET = face_size * OFFSET_F
    LIM = face_size * TRAVEL_F
    SPACING = face_size * SPACING_F

    def place(feature, h=0.0, v=0.0):
        return feature + fwd * OFFSET + right * h + up * v

    controls = []
    handled_keys = set()

    mouth_keys = [k for k in keyblock.keys() if "mouth" in k.lower() or "mth" in k.lower()]
    eye_keys = [k for k in keyblock.keys() if "eye" in k.lower()]
    brow_keys = [k for k in keyblock.keys() if "brow" in k.lower() or "ebr" in k.lower()]

    mouth = feature_centroid(mesh_obj, mouth_keys) or feature_centroid(mesh_obj, ["Mouth_01_A", "Mouth_00_A"])
    eyeC = feature_centroid(mesh_obj, ["00_Close01_Eye", "Eye_Close", "00_Default_Eye"]) or feature_centroid(mesh_obj, eye_keys)
    brow = feature_centroid(mesh_obj, brow_keys)

    fcx = mesh_obj.matrix_world @ (0.125 * sum((Vector(c) for c in mesh_obj.bound_box), Vector()))
    if mouth is None:
        mouth = fcx - up * face_size * 0.12
    if eyeC is None:
        eyeC = fcx + up * face_size * 0.10
    if brow is None:
        brow = eyeC + up * face_size * 0.08

    mouth = mouth + up * (face_size * MOUTH_RAISE_F)
    tri_scale = Vector((face_size * TRI_F,) * 3)

    # 0. Ignore default rest keys (Basis, Default, Rest, N, Max, Minimum)
    for k in keyblock.keys():
        kl = k.lower()
        if "default" in kl or kl in ["basis", "00_default_brow", "00_default_eye", "00_default_mouth", "mouth_00_n", "mouth_01_n", "mouth_00_max", "mouth_01_max", "mouth_00_minimum", "mouth_01_minimum"]:
            handled_keys.add(k)

    # 1. Main Direct Face Controls (Pads/Toggles right on face)
    primary_close = pick_primary_key(keyblock, ["00_Close01_Eye", "Eye_Close", "00_Close02_Eye"])
    if primary_close and primary_close not in handled_keys:
        handled_keys.add(primary_close)
        controls.append({
            'name': 'CTRL-Eye_Close',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYELID,
            'group': 'Face Eyelid',
            'head': place(eyeC, v=face_size * 0.04),
            'widget': 'triangle_down',
            'lim': LIM,
            'free': ('Z',),
            'range': 'neg',
            'shape_scale': tri_scale,
            'drivers': [{'key': primary_close, 'axis': 'Z', 'dir': -1}]
        })

    p_wide = pick_primary_key(keyblock, ["Mouth_01_Wide", "Mouth_00_Wide", "Mouth_Wide"])
    p_narrow = pick_primary_key(keyblock, ["Mouth_01_Narrow", "Mouth_00_Narrow", "Mouth_Narrow"])
    p_up = pick_primary_key(keyblock, ["Mouth_01_Up", "Mouth_00_Up", "Mouth_Up"])
    p_down = pick_primary_key(keyblock, ["Mouth_01_Down", "Mouth_00_Down", "Mouth_Down"])

    drv_shift = []
    if p_wide and p_wide not in handled_keys:
        drv_shift.append({'key': p_wide, 'axis': 'X', 'dir': +1})
        handled_keys.add(p_wide)
    if p_narrow and p_narrow not in handled_keys:
        drv_shift.append({'key': p_narrow, 'axis': 'X', 'dir': -1})
        handled_keys.add(p_narrow)
    if p_up and p_up not in handled_keys:
        drv_shift.append({'key': p_up, 'axis': 'Z', 'dir': +1})
        handled_keys.add(p_up)
    if p_down and p_down not in handled_keys:
        drv_shift.append({'key': p_down, 'axis': 'Z', 'dir': -1})
        handled_keys.add(p_down)

    if False and drv_shift:  # Disabled CTRL-Mouth-Shift bone creation per user request
        mouth_scale = Vector((LIM * 0.9, LIM, LIM * 0.4))
        controls.append({
            'name': 'CTRL-Mouth-Shift',
            'collection': FACERIG_COLLECTION,
            'color': COL_MOUTH,
            'group': 'Face Mouth',
            'head': place(mouth),
            'widget': 'pad',
            'lim': LIM,
            'free': ('X', 'Z'),
            'range': 'both',
            'shape_scale': mouth_scale,
            'drivers': drv_shift
        })

    label_scale = Vector((face_size * 0.045, face_size * 0.045, face_size * 0.045))

    # 2. Left-side Panel: Eyebrows and Eyes (A la IZQUIERDA de la cabeza)
    left_panel_origin = fcx - right * (face_size * 0.45) + up * (face_size * 0.45)
    current_left_v = 0.0
    MAX_PER_ROW = 12  # Máximo 12 controles por fila
    ROW_Z_GAP = 0.120    # Separación vertical en Z entre filas (0.120)
    ITEM_SP = 0.035

    def add_left_panel_grid(items_list, group_name, color, widget_type='slider'):
        nonlocal current_left_v
        if not items_list:
            return
        total = len(items_list)
        for i, item in enumerate(items_list):
            if isinstance(item, tuple):
                c_name, drv_list = item[0], item[1]
            else:
                c_name = item.get('name') if isinstance(item, dict) else f"CTRL-{item}"
                drv_list = item.get('drivers') if isinstance(item, dict) else [{'key': item, 'axis': 'Z', 'dir': +1}]
                if isinstance(item, str):
                    handled_keys.add(item)

            row_idx = i // MAX_PER_ROW
            col_idx = i % MAX_PER_ROW

            # Se extiende hacia la izquierda (-right)
            h = -col_idx * (face_size * ITEM_SP)
            v = current_left_v - row_idx * (face_size * ROW_Z_GAP)

            controls.append({
                'name': c_name,
                'collection': FACERIG_COLLECTION,
                'color': color,
                'group': group_name,
                'head': place(left_panel_origin, h=h, v=v),
                'widget': widget_type,
                'lim': LIM,
                'free': ('Z',),
                'range': 'pos',
                'drivers': drv_list
            })

        num_rows = (total + MAX_PER_ROW - 1) // MAX_PER_ROW
        current_left_v -= num_rows * (face_size * ROW_Z_GAP) + (face_size * 0.01)

    # A. Brow Keys (Cejas - Panel Izquierdo)
    unhandled_brows = [k for k in keyblock.keys() if k in brow_keys and k not in handled_keys]
    if unhandled_brows:
        add_left_panel_grid(unhandled_brows, 'Face Eyebrow', (0.30, 0.80, 0.35))

    # B. Eye Keys (Ojos - Panel Izquierdo)
    unhandled_eyes = [k for k in keyblock.keys() if k in eye_keys and k not in handled_keys]
    if unhandled_eyes:
        add_left_panel_grid(unhandled_eyes, 'Face Eye Expressions', COL_EYEAIM)

    # Add Left Panel Header Label (Brows & Eyes)
    if unhandled_brows or unhandled_eyes:
        total_left = len(unhandled_brows) + len(unhandled_eyes)
        num_cols_left = max(1, min(MAX_PER_ROW, total_left))
        center_h_left = - (num_cols_left - 1) / 2.0 * (face_size * ITEM_SP)
        controls.append({
            'name': 'LABEL-Brows_Eyes',
            'collection': FACERIG_COLLECTION,
            'color': COL_LABEL,
            'group': 'Face Labels',
            'head': place(left_panel_origin, h=center_h_left, v=face_size * 0.075),
            'widget': 'text:BROWS & EYES',
            'lim': 0.0,
            'free': (),
            'range': 'pos',
            'shape_scale': label_scale,
            'is_label': True,
            'drivers': []
        })

    # 3. Right-side Panel: Mouth, Visemes, Phonemes, Extra (A la DERECHA de la cabeza)
    right_panel_origin = fcx + right * (face_size * 0.45) + up * (face_size * 0.45)
    current_right_v_col1 = 0.0
    current_right_v_col2 = 0.0

    col2_offset = face_size * (ITEM_SP * MAX_PER_ROW + 0.05)

    def add_right_panel_grid(items_list, group_name, color, widget_type='slider', is_col2=False):
        nonlocal current_right_v_col1, current_right_v_col2
        if not items_list:
            return
        col_offset = col2_offset if is_col2 else 0.0
        v_base = current_right_v_col2 if is_col2 else current_right_v_col1

        total = len(items_list)
        for i, item in enumerate(items_list):
            if isinstance(item, tuple):
                c_name, drv_list = item[0], item[1]
            else:
                c_name = item.get('name') if isinstance(item, dict) else f"CTRL-{item}"
                drv_list = item.get('drivers') if isinstance(item, dict) else [{'key': item, 'axis': 'Z', 'dir': +1}]
                if isinstance(item, str):
                    handled_keys.add(item)

            row_idx = i // MAX_PER_ROW
            col_idx = i % MAX_PER_ROW

            # Se extiende hacia la derecha (+right) con col_offset
            h = col_idx * (face_size * ITEM_SP) + col_offset
            v = v_base - row_idx * (face_size * ROW_Z_GAP)

            controls.append({
                'name': c_name,
                'collection': FACERIG_COLLECTION,
                'color': color,
                'group': group_name,
                'head': place(right_panel_origin, h=h, v=v),
                'widget': widget_type,
                'lim': LIM,
                'free': ('Z',),
                'range': 'pos',
                'drivers': drv_list
            })

        num_rows = (total + MAX_PER_ROW - 1) // MAX_PER_ROW
        v_drop = num_rows * (face_size * ROW_Z_GAP) + (face_size * 0.01)
        if is_col2:
            current_right_v_col2 -= v_drop
        else:
            current_right_v_col1 -= v_drop

    # A. Visemas (A, E, I, O, U - Panel Derecho, Columna 1)
    viseme_letters = ["A", "E", "I", "O", "U"]
    active_visemes = []
    for letter in viseme_letters:
        pk = pick_primary_key(keyblock, [f"Mouth_01_{letter}", f"Mouth_00_{letter}", f"Mouth_{letter}"])
        if pk and pk not in handled_keys:
            active_visemes.append((f"CTRL-Viseme_{letter}", [{'key': pk, 'axis': 'Z', 'dir': +1}]))
            handled_keys.add(pk)
    if active_visemes:
        add_right_panel_grid(active_visemes, 'Face Visemes', COL_VISEME, is_col2=False)

    # B. Mouth Expression Keys (Expresiones de Boca - Panel Derecho, Columna 1)
    unhandled_mouth = [k for k in keyblock.keys() if k in mouth_keys and k not in handled_keys and "phoneme" not in k.lower()]
    if unhandled_mouth:
        mouth_items = []
        for k in unhandled_mouth:
            clean_k = k.replace("Mouth_00_", "").replace("Mouth_01_", "").replace("Mouth_", "")
            c_name = f"CTRL-Expr_{clean_k}" if clean_k != k else f"CTRL-{k}"
            handled_keys.add(k)
            mouth_items.append((c_name, [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_right_panel_grid(mouth_items, 'Face Expressions', COL_EXPRESSION, is_col2=False)

    # Add Right Panel Col 1 Header Label (Mouth)
    if active_visemes or unhandled_mouth:
        total_col1 = len(active_visemes) + len(unhandled_mouth)
        num_cols1 = max(1, min(MAX_PER_ROW, total_col1))
        center_h_col1 = (num_cols1 - 1) / 2.0 * (face_size * ITEM_SP)
        controls.append({
            'name': 'LABEL-Mouth',
            'collection': FACERIG_COLLECTION,
            'color': COL_LABEL,
            'group': 'Face Labels',
            'head': place(right_panel_origin, h=center_h_col1, v=face_size * 0.075),
            'widget': 'text:MOUTH',
            'lim': 0.0,
            'free': (),
            'range': 'pos',
            'shape_scale': label_scale,
            'is_label': True,
            'drivers': []
        })

    # C. Phoneme Keys (Fonemas - Panel Derecho, COLUMNA 2 a la Derecha de las expresiones moradas)
    phoneme_keys = [k for k in keyblock.keys() if "phoneme" in k.lower() and k not in handled_keys]
    if phoneme_keys:
        ph_items = []
        for k in phoneme_keys:
            idx_p = k.lower().find("phoneme_cn_")
            sub = k[idx_p + len("phoneme_cn_"):] if idx_p != -1 else k
            c_name = f"CTRL-ph_{sub}"
            handled_keys.add(k)
            ph_items.append((c_name, [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_right_panel_grid(ph_items, 'Face Phonemes', (0.30, 0.80, 0.35), is_col2=True)

    # D. Extra Keys (Dynamic Fallback - Panel Derecho, COLUMNA 2 a la Derecha)
    remaining = [k for k in keyblock.keys() if k not in handled_keys]
    if remaining:
        rem_items = []
        for k in remaining:
            handled_keys.add(k)
            rem_items.append((f"CTRL-{k}", [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_right_panel_grid(rem_items, 'Face Extra Keys', (0.25, 0.75, 0.35), is_col2=True)

    # Add Right Panel Col 2 Header Label (Phonemes & Extra)
    if phoneme_keys or remaining:
        total_col2 = len(phoneme_keys) + len(remaining)
        num_cols2 = max(1, min(MAX_PER_ROW, total_col2))
        center_h_col2 = col2_offset + (num_cols2 - 1) / 2.0 * (face_size * ITEM_SP)
        if phoneme_keys and remaining:
            lbl_text = 'PHONEMES & EXTRA'
            lbl_name = 'LABEL-Phonemes_Extra'
        elif phoneme_keys:
            lbl_text = 'PHONEMES'
            lbl_name = 'LABEL-Phonemes'
        else:
            lbl_text = 'EXTRA'
            lbl_name = 'LABEL-Extra'

        controls.append({
            'name': lbl_name,
            'collection': FACERIG_COLLECTION,
            'color': COL_LABEL,
            'group': 'Face Labels',
            'head': place(right_panel_origin, h=center_h_col2, v=face_size * 0.075),
            'widget': f'text:{lbl_text}',
            'lim': 0.0,
            'free': (),
            'range': 'pos',
            'shape_scale': label_scale,
            'is_label': True,
            'drivers': []
        })

    return controls


def make_widget(kind, coll):
    name = "WGT-Face_" + kind
    obj = bpy.data.objects.get(name)
    if obj:
        return obj
    if kind == 'pad':
        s = 1.0
        verts = [(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    elif kind == 'slider':
        verts = [(0, 0, -1), (0, 0, 1), (-0.35, 0, 1), (0.35, 0, 1)]
        edges = [(0, 1), (2, 3)]
    elif kind == 'ring':
        verts, edges, N = [], [], 20
        for i in range(N):
            a = 2 * math.pi * i / N
            verts.append((math.cos(a), 0.0, math.sin(a)))
            edges.append((i, (i + 1) % N))
    elif kind == 'triangle':
        verts = [(0, 0, 1), (-0.9, 0, -0.7), (0.9, 0, -0.7)]
        edges = [(0, 1), (1, 2), (2, 0)]
    elif kind == 'triangle_down':
        verts = [(0, 0, -1), (-0.9, 0, 0.7), (0.9, 0, 0.7)]
        edges = [(0, 1), (1, 2), (2, 0)]
    else:
        verts, edges = [(0, 0, 0)], []
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    return obj


def make_text_widget(text_string, wgt_coll):
    safe_name = text_string.replace(' ', '_').replace('&', 'AND').replace('/', '_')
    name = "WGT-Face_Label_" + safe_name
    obj = bpy.data.objects.get(name)
    if obj:
        return obj

    try:
        curve_data = bpy.data.curves.new(name=name + "_Curve", type='FONT')
        curve_data.body = text_string
        curve_data.size = 1.0
        curve_data.align_x = 'CENTER'
        curve_data.align_y = 'CENTER'
        curve_data.fill_mode = 'NONE'

        temp_obj = bpy.data.objects.new(name + "_Temp", curve_data)
        bpy.context.scene.collection.objects.link(temp_obj)

        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = temp_obj.evaluated_get(depsgraph)
        mesh_from_eval = bpy.data.meshes.new_from_object(eval_obj)
        mesh_from_eval.name = name

        # Rotate mesh vertices so text stands upright facing the front camera
        # Text X (width) -> Bone -X (which is +X in world)
        # Text Y (height) -> Bone +Z (which is +Z in world)
        # Text Z (normal) -> Bone Y (0 depth)
        for v in mesh_from_eval.vertices:
            v.co = Vector((-v.co.x, 0.0, v.co.y))

        bpy.context.scene.collection.objects.unlink(temp_obj)
        bpy.data.objects.remove(temp_obj, do_unlink=True)
        bpy.data.curves.remove(curve_data, do_unlink=True)

        wgt_obj = bpy.data.objects.new(name, mesh_from_eval)
        wgt_coll.objects.link(wgt_obj)
        return wgt_obj
    except Exception as ex:
        # Fallback wireframe bounding box with center line
        s_w = max(1.0, len(text_string) * 0.4)
        s_h = 0.5
        verts = [(-s_w, 0, -s_h), (s_w, 0, -s_h), (s_w, 0, s_h), (-s_w, 0, s_h)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, edges, [])
        wgt_obj = bpy.data.objects.new(name, mesh)
        wgt_coll.objects.link(wgt_obj)
        return wgt_obj


def lighten(rgb, amt):
    return tuple(min(1.0, c + amt) for c in rgb)


def apply_color(armature, pb, group_name, rgb, cache):
    if is_blender_3():
        grp = cache.get(group_name)
        if grp is None:
            grp = armature.pose.bone_groups.get(group_name)
            if grp is None:
                grp = armature.pose.bone_groups.new(name=group_name)
            grp.color_set = 'CUSTOM'
            grp.colors.normal = rgb
            grp.colors.select = lighten(rgb, 0.25)
            grp.colors.active = lighten(rgb, 0.5)
            cache[group_name] = grp
        pb.bone_group = grp
    else:
        try:
            pb.color.palette = 'CUSTOM'
            cc = pb.color.custom
            cc.normal = rgb
            cc.select = lighten(rgb, 0.25)
            cc.active = lighten(rgb, 0.5)
        except Exception:
            pass


def purge_previous(armature):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    eb = armature.data.edit_bones
    for b in list(eb):
        if b.name.startswith("CTRL-") or b.name.startswith("LABEL-") or b.name == "Face-Root":
            eb.remove(b)
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        if o.name.startswith("WGT-Face_"):
            bpy.data.objects.remove(o, do_unlink=True)


def get_widget_collection(name="WGTS_FaceRig"):
    # Prefer per-character WGTS_<Char> (Append-safe): resolve from active/selected rig
    try:
        from setup_wizard.ui.character_settings_utils import resolve_settings_armature, resolve_character_name
        arm = resolve_settings_armature(bpy.context)
        if arm is not None:
            char_name = resolve_character_name(arm)
            if char_name:
                per_char = bpy.data.collections.get(f"WGTS_{char_name}")
                if per_char is not None:
                    return per_char
                # If the rig already lives in a character collection, create nested WGTS there
                try:
                    from setup_wizard.character_rig_setup.wgts_isolation import get_or_create_char_wgts, get_char_collection
                    char_coll = get_char_collection(arm, char_name)
                    if char_coll is not None:
                        return get_or_create_char_wgts(char_coll, char_name)
                except Exception:
                    pass
    except Exception:
        pass
    for name_candidate in ("WGTS", "wgt", "WGTS_FaceRig"):
        coll = bpy.data.collections.get(name_candidate)
        if coll:
            return coll

    for c in bpy.data.collections:
        c_low = c.name.lower()
        if "wgts" in c_low or "wgt" in c_low:
            return c

    coll = bpy.data.collections.new(name)
    return coll


def finalize_widget_collection(wgt_coll):
    if not wgt_coll:
        return
    try:
        wgt_coll.hide_viewport = True
    except Exception:
        pass
    if wgt_coll.name in bpy.context.scene.collection.children:
        try:
            bpy.context.scene.collection.children.unlink(wgt_coll)
        except Exception:
            pass


def setup_hsr_face_rig(mesh_obj, controls, armature, head_name, fwd, up, face_size, keyblock):
    print(f"Building {len(controls)} HSR face controls on '{armature.name}' under '{head_name}'")

    amw_inv = armature.matrix_world.inverted()
    bone_len = face_size * BONE_LEN_F

    def to_arm_point(p):
        return amw_inv @ p

    def to_arm_vec(v):
        return amw_inv.to_3x3() @ v

    fwd_arm = to_arm_vec(fwd).normalized()
    up_arm = to_arm_vec(up).normalized()

    bpy.context.view_layer.objects.active = armature
    try:
        armature.data.use_mirror_x = False
    except Exception:
        pass

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    eb = armature.data.edit_bones

    root = eb.get("Face-Root") or eb.new("Face-Root")
    head_edit = eb.get(head_name)
    root.head = head_edit.head.copy() if head_edit else Vector((0, 0, 0))
    root.tail = root.head + up_arm * bone_len * 2.0
    root.use_deform = False
    if head_edit:
        root.parent = head_edit

    for c in controls:
        b = eb.get(c['name']) or eb.new(c['name'])
        h = to_arm_point(c['head'])
        b.head = h
        b.tail = h + fwd_arm * bone_len
        b.use_deform = False
        try:
            b.align_roll(up_arm)
        except Exception:
            pass
        b.parent = root
        b.use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')

    coll_names = [c['collection'] for c in controls if c.get('collection')]
    if not is_blender_3() and hasattr(armature.data, "collections"):
        for cn in set(coll_names):
            coll = armature.data.collections.get(cn) or armature.data.collections.new(cn)
            try:
                coll.is_visible = True
            except Exception:
                pass
            try:
                coll.rigify_ui_row = RIGIFY_UI_ROW
            except Exception:
                pass
        for c in controls:
            bone = armature.data.bones.get(c['name'])
            coll = armature.data.collections.get(c.get('collection', FACERIG_COLLECTION))
            if bone and coll:
                coll.assign(bone)

    wgt_coll = get_widget_collection()
    bpy.ops.object.mode_set(mode='POSE')
    color_cache = {}

    for c in controls:
        pb = armature.pose.bones.get(c['name'])
        if not pb:
            continue

        is_lbl = c.get('is_label', False)

        if is_lbl:
            # Lock all transforms for header label bones
            for i in range(3):
                pb.lock_location[i] = True
                pb.lock_rotation[i] = True
                pb.lock_scale[i] = True
            pb.lock_rotation_w = True
        else:
            lim = c['lim']
            free = c['free']
            rng = c['range']
            if rng == 'both':
                lo, hi = -lim, lim
            elif rng == 'neg':
                lo, hi = -lim, 0.0
            else:
                lo, hi = 0.0, lim

            pb.lock_location[0] = 'X' not in free
            pb.lock_location[1] = True
            pb.lock_location[2] = 'Z' not in free
            for i in range(3):
                pb.lock_rotation[i] = True
                pb.lock_scale[i] = True
            pb.lock_rotation_w = True

            con = pb.constraints.new(type='LIMIT_LOCATION')
            con.owner_space = 'LOCAL'
            con.use_transform_limit = True
            con.use_min_x = con.use_max_x = True
            con.use_min_y = con.use_max_y = True
            con.use_min_z = con.use_max_z = True
            con.min_y = con.max_y = 0.0
            con.min_x = lo if 'X' in free else 0.0
            con.max_x = hi if 'X' in free else 0.0
            con.min_z = lo if 'Z' in free else 0.0
            con.max_z = hi if 'Z' in free else 0.0

        if c['widget'].startswith('text:'):
            text_str = c['widget'].split(':', 1)[1]
            pb.custom_shape = make_text_widget(text_str, wgt_coll)
        else:
            pb.custom_shape = make_widget(c['widget'], wgt_coll)

        try:
            pb.use_custom_shape_bone_size = False
        except Exception:
            pass
        ss = c.get('shape_scale')
        pb.custom_shape_scale_xyz = ss if ss is not None else Vector((c.get('lim', 0.02) * WIDGET_F,) * 3)

        apply_color(armature, pb, c['group'], c['color'], color_cache)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Build Drivers on Shape Keys
    agg = {}
    for c in controls:
        for d in c.get('drivers', []):
            agg.setdefault(d['key'], []).append(
                {'bone': c['name'], 'axis': d['axis'], 'dir': d['dir'],
                 'lim': c['lim'], 'bidir': d.get('bidir', False)})

    for key, entries in agg.items():
        sk = keyblock.get(key)
        if sk is None:
            continue
        sk.slider_min = -1.0 if any(e['bidir'] for e in entries) else 0.0
        try:
            sk.driver_remove("value")
        except Exception:
            pass
        drv = sk.driver_add("value").driver
        drv.type = 'SCRIPTED'
        terms = []
        for i, e in enumerate(entries):
            vn = f"v{i}"
            var = drv.variables.new()
            var.name = vn
            var.type = 'TRANSFORMS'
            tgt = var.targets[0]
            tgt.id = armature
            tgt.bone_target = e['bone']
            tgt.transform_type = 'LOC_' + e['axis']
            tgt.transform_space = 'LOCAL_SPACE'
            sign = '' if e['dir'] > 0 else '-'
            if e['bidir']:
                terms.append(f"{sign}{vn} / {e['lim']!r}")
            else:
                terms.append(f"max(0.0, {sign}{vn} / {e['lim']!r})")
        drv.expression = terms[0] if len(terms) == 1 else "max(" + ", ".join(terms) + ")"

    # Hide stick facial bones, extra bones, tweak collections, FK collections, Fingers (Detail), and Face-Root
    hidden_colls = [
        "DEF", "ORG", "MCH", "Face", "Face (Secondary)", "Face (Primary)", "Face (Tweaks)", "Face Bones", "Face_Bones",
        "Extra Bones", "Extra_Bones", "Extra",
        "Torso (Tweak)", "Arm.L (Tweak)", "Arm.R (Tweak)", "Leg.L (Tweak)", "Leg.R (Tweak)",
        "Arm.L (FK)", "Arm.R (FK)", "Leg.L (FK)", "Leg.R (FK)",
        "Fingers (Detail)"
    ]
    for cn in hidden_colls:
        c = armature.data.collections.get(cn)
        if c:
            try:
                c.is_visible = False
            except Exception:
                pass

    palms_coll = armature.data.collections.get("Palms")
    if palms_coll:
        palms_coll.is_visible = True

    # Create visible "Face" collection for eye/face control bones
    facerig_coll = armature.data.collections.get("Face") or armature.data.collections.get("Facerig") or armature.data.collections.new("Face")
    facerig_coll.is_visible = True

    eye_ctrl_bone_names = ["eyetrack", "eyetrack_L", "eyetrack_R"]
    for bname in eye_ctrl_bone_names:
        if bname in armature.data.bones:
            b = armature.data.bones[bname]
            try:
                facerig_coll.assign(b)
                b.hide = False
            except Exception:
                pass

    # Hide helper tracking bones (+EyeBone L/R A01.001)
    for bname in ["+EyeBone L A01.001", "+EyeBone R A01.001"]:
        if bname in armature.data.bones:
            try:
                armature.data.bones[bname].hide = True
            except Exception:
                pass

    face_bones_coll = armature.data.collections.get("Face Bones") or armature.data.collections.new("Face Bones")
    face_bones_coll.is_visible = False

    extra_bones_coll = armature.data.collections.get("Extra Bones") or armature.data.collections.new("Extra Bones")
    extra_bones_coll.is_visible = False

    face_keywords = [
        "joint_", "brow", "eye", "eyelid", "cheek", "nose", 
        "mouth", "lip", "jaw", "teeth", "tongue", "skn", "face-root"
    ]
    main_ctrls = ["root", "torso", "hips", "chest", "neck", "head"]

    for bone in armature.data.bones:
        b_name = bone.name
        b_low = b_name.lower()
        if b_name.startswith("CTRL-") or b_name.startswith("LABEL-") or b_name in main_ctrls or b_name in eye_ctrl_bone_names:
            continue

        is_face_bone = any(kw in b_low for kw in face_keywords)
        target_coll = face_bones_coll if is_face_bone else extra_bones_coll

        if is_face_bone or b_low.startswith("def-") or b_low.startswith("org-") or b_low.startswith("mch-") or len(bone.collections) == 0:
            try:
                target_coll.assign(bone)
            except Exception:
                pass
            for c in list(bone.collections):
                if c != target_coll and c != facerig_coll and c.name not in hidden_colls:
                    try:
                        c.unassign(bone)
                    except Exception:
                        pass
            bone.hide = True

    # Set up dynamic Y location drivers for eye bones driven by eye shape key activation (up to -0.0040 max offset)
    setup_dynamic_eye_y_drivers(mesh_obj, armature, max_offset=-0.0040)

    print("HSR Face rig build complete.")


def setup_dynamic_eye_y_drivers(mesh_obj, armature, max_offset=-0.0040):
    """
    Drives eye.L and eye.R Y location backwards up to max_offset (-0.0040)
    proportionally when eye expression/close shape keys are activated by the facial rig.
    Replaces static fixed eye location offset hack.
    """
    candidate_eye_L = ["eye.L", "DEF-eye.L", "+EyeBone L A01", "+EyeBone L A02", "EYE_L", "Eye_L"]
    candidate_eye_R = ["eye.R", "DEF-eye.R", "+EyeBone R A01", "+EyeBone R A02", "EYE_R", "Eye_R"]

    eye_L_pbone = next((armature.pose.bones.get(b) for b in candidate_eye_L if armature.pose.bones.get(b)), None)
    eye_R_pbone = next((armature.pose.bones.get(b) for b in candidate_eye_R if armature.pose.bones.get(b)), None)

    # Reset any static pose location offsets
    if eye_L_pbone:
        eye_L_pbone.location = (0.0, 0.0, 0.0)
    if eye_R_pbone:
        eye_R_pbone.location = (0.0, 0.0, 0.0)

    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return

    keyblock = mesh_obj.data.shape_keys.key_blocks
    sk_id = mesh_obj.data.shape_keys

    eye_sk_L = []
    eye_sk_R = []

    for k_name in keyblock.keys():
        kl = k_name.lower()
        if "default" in kl or kl == "basis":
            continue
        # Only select eye shape keys (excluding brow/mouth)
        if any(kw in kl for kw in ["eye", "wink"]) and not any(ex in kl for ex in ["brow", "mouth"]):
            is_r_only = kl.endswith("_r") or kl.endswith(".r") or kl.endswith("right") or "_r_" in kl
            is_l_only = kl.endswith("_l") or kl.endswith(".l") or kl.endswith("left") or "_l_" in kl

            if not is_r_only:
                eye_sk_L.append(k_name)
            if not is_l_only:
                eye_sk_R.append(k_name)

    def attach_driver(pbone, sk_list):
        if not pbone or not sk_list:
            return
        try:
            pbone.driver_remove("location", 1)
        except Exception:
            pass

        driver_obj = pbone.driver_add("location", 1)
        drv = driver_obj.driver
        drv.type = 'SCRIPTED'

        var_names = []
        for i, sk_name in enumerate(sk_list):
            vn = f"v{i}"
            var = drv.variables.new()
            var.name = vn
            var.type = 'SINGLE_PROP'
            tgt = var.targets[0]
            try:
                tgt.id_type = 'KEY'
            except Exception:
                pass
            tgt.id = sk_id
            tgt.data_path = f'key_blocks["{sk_name}"].value'
            var_names.append(vn)

        if len(var_names) == 1:
            drv.expression = f"{max_offset!r} * max(0.0, min(1.0, {var_names[0]}))"
        else:
            terms_str = ", ".join(var_names)
            drv.expression = f"{max_offset!r} * max(0.0, min(1.0, max({terms_str})))"

    if eye_L_pbone:
        attach_driver(eye_L_pbone, eye_sk_L)
    if eye_R_pbone:
        attach_driver(eye_R_pbone, eye_sk_R)


def hsr_face_rig_main():
    faceobj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            n = obj.name.lower()
            if "face" in n or (obj.data.shape_keys and any(k.startswith("Mouth_") or k.startswith("Brow_") or k.startswith("Eye_") for k in obj.data.shape_keys.key_blocks.keys())):
                faceobj = obj
                break

    if faceobj is None:
        print("HSR Face Rig: No face mesh found.")
        return
    if faceobj.data.shape_keys is None:
        print("HSR Face Rig: Face mesh has no shape keys.")
        return

    keyblock = faceobj.data.shape_keys.key_blocks
    armature, head_name = find_armature_and_head(faceobj)
    fwd, right, up, face_size = face_frame(faceobj)
    controls = plan_hsr_controls(faceobj, fwd, right, up, face_size, keyblock)

    if not controls:
        print("HSR Face Rig: No drivable shape keys found.")
        return

    if CLEAN_REBUILD:
        purge_previous(armature)

    setup_hsr_face_rig(faceobj, controls, armature, head_name, fwd, up, face_size, keyblock)

    wgt_coll = get_widget_collection()
    finalize_widget_collection(wgt_coll)

    print(f"\nHSR Face Rig complete: {len(controls)} controls built on '{armature.name}'.\n")
