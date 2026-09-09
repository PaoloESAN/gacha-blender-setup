# Author: PaoloESAN
# Face Rig Logic for Neverness to Everness (NTE)
# Integrates Isaac/ZZZ direct face widgets and controls with HSR-style side panel expression sliders

import bpy
import math
from mathutils import Vector, Matrix

HEAD_BONE_NAME   = None
CLEAN_REBUILD    = True
FLIP_HORIZONTAL  = True
FLIP_VERTICAL    = False
FLIP_EYE_LR      = False

BONE_LEN_F   = 0.020
OFFSET_F     = 0.080
TRAVEL_F     = 0.040
SPACING_F    = 0.050
WIDGET_F     = 1.0
FACERIG_COLLECTION = "Face"
RIGIFY_UI_ROW = 1

COL_MOUTH      = (0.90, 0.20, 0.20)
COL_CORNER     = (0.15, 0.85, 0.30)
COL_VISEME     = (0.95, 0.85, 0.20)
COL_EYELID     = (0.90, 0.15, 0.15)
COL_EYEAIM     = (0.20, 0.85, 0.90)
COL_EYEGREEN   = (0.20, 0.85, 0.30)
COL_EYEMOTE    = (0.90, 0.20, 0.20)
COL_BROW       = (0.30, 0.80, 0.35)
COL_BROWSAD    = (0.95, 0.45, 0.75)
COL_EBRBONE    = (0.20, 0.55, 0.95)
COL_EBRMASTER  = (0.65, 0.35, 0.90)
COL_EXPRESSION = (0.65, 0.35, 0.90)
COL_TD_SPECIAL = (0.90, 0.40, 0.60)
COL_LABEL      = (0.95, 0.95, 0.95)

HEAD_CANDIDATES = [
    "DEF-spine.006", "ORG-spine.006", "spine.006", "head", "Head", "Head_M", "head_M",
    "Bip001-Head", "Bip001 Head", "Bip001_Head", "Bip001Head", "Bip001 头", "頭", "头",
]


def is_blender_3():
    return bpy.app.version[0] == 3


def find_face_mesh():
    nte_signatures = ["look_U", "EL_", "EB_", "jawOpen", "biyan", "TD_", "TDS_", "mouthPucker"]
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data and obj.data.shape_keys:
            kb = obj.data.shape_keys.key_blocks
            if any(any(sig in k for sig in nte_signatures) for k in kb.keys()):
                return obj

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data and obj.data.shape_keys:
            n = obj.name.lower()
            if any(k in n for k in ["face", "head", "skin", "player_", "npc_"]):
                if not any(ign in n for ign in ["weapon", "gun", "sword"]):
                    return obj

    for obj in bpy.context.view_layer.objects:
        if obj.type == 'MESH' and obj.data and obj.data.shape_keys:
            return obj

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data and obj.data.shape_keys:
            return obj

    return None


def find_armature_and_head(mesh_obj):
    armature = None
    for m in mesh_obj.modifiers:
        if m.type == 'ARMATURE' and m.object:
            armature = m.object
            break
    if armature is None:
        for o in bpy.data.objects:
            if o.type == 'ARMATURE' and o.name in bpy.context.view_layer.objects:
                if not any(ign in o.name.lower() for ign in ['metarig', 'backup']):
                    armature = o
                    break
    if armature is None:
        for o in bpy.data.objects:
            if o.type == 'ARMATURE':
                armature = o
                break
    if armature is None:
        raise Exception("No armature found to attach the NTE face rig to.")

    names = [HEAD_BONE_NAME] if HEAD_BONE_NAME else []
    names += HEAD_CANDIDATES
    head_name = None
    for cand in names:
        if cand and cand in armature.data.bones:
            head_name = cand
            break
    if head_name is None:
        for b in armature.data.bones:
            if 'head' in b.name.lower() or 'spine.006' in b.name.lower():
                head_name = b.name
                break
    if head_name is None:
        head_name = armature.data.bones[0].name
    return armature, head_name


def get_face_metrics(mesh_obj, armature, head_name):
    head_pos = None
    head_tail = None
    head_bone = None

    if armature and head_name and hasattr(armature, 'data') and hasattr(armature.data, 'bones'):
        head_bone = armature.data.bones.get(head_name)
        if head_bone:
            head_pos = armature.matrix_world @ head_bone.head_local
            head_tail = armature.matrix_world @ head_bone.tail_local

    if head_pos and head_tail:
        head_len = (head_tail - head_pos).length
        face_size = max(0.18, min(0.28, head_len * 1.15 if head_len > 0.05 else 0.22))
        fwd_guess = Vector((0.0, -1.0, 0.0))
        up_guess = (head_tail - head_pos).normalized() if head_len > 1e-4 else Vector((0.0, 0.0, 1.0))
        fcx = head_pos + up_guess * (head_len * 0.55) + fwd_guess * (face_size * 0.25)
    else:
        face_size = 0.22
        fcx = Vector((0.0, -0.05, 1.45))

    fwd = Vector((0.0, -1.0, 0.0))
    world_up = Vector((0.0, 0.0, 1.0))

    if head_bone and head_pos and head_tail:
        bone_vec = (head_tail - head_pos).normalized() if (head_tail - head_pos).length > 1e-4 else world_up
        if abs(bone_vec.dot(world_up)) > 0.5:
            world_up = bone_vec

    right = world_up.cross(fwd).normalized()
    up = fwd.cross(right).normalized()

    return fwd, right, up, face_size, fcx


def feature_centroid(mesh_obj, key_names, side=None):
    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return None
    kb = mesh_obj.data.shape_keys.key_blocks
    basis = kb.get("Basis")
    if basis is None or not hasattr(basis, 'data'):
        return None
    key = None
    for kn in key_names:
        if kn in kb:
            key = kb[kn]
            break
    if key is None or not hasattr(key, 'data'):
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

    is_already_single_sided = False
    if key.name:
        kn_low = key.name.lower()
        if "_l" in kn_low or ".l" in kn_low or "left" in kn_low or "_r" in kn_low or ".r" in kn_low or "right" in kn_low:
            is_already_single_sided = True

    if side in ('L', 'R') and not is_already_single_sided:
        xs = sorted(basis.data[i].co.x for i in idx)
        median_x = xs[len(xs) // 2]
        hi = [i for i in idx if basis.data[i].co.x >= median_x]
        lo = [i for i in idx if basis.data[i].co.x < median_x]
        pick = hi if (side == 'L') != FLIP_EYE_LR else lo
        idx = pick or idx

    c = Vector((0.0, 0.0, 0.0))
    for i in idx:
        c += basis.data[i].co
    c /= len(idx)
    return mesh_obj.matrix_world @ c


def get_shapekey_side(mesh_obj, sk_name, fcx, right):
    """
    Returns +1 if the shapekey's vertices are on the +right side of the face (Viewer's Right / +X / Blender .L),
    -1 if on the -right side (Viewer's Left / -X / Blender .R), or 0 if centered.
    """
    if not mesh_obj or not sk_name:
        return 0
    c = feature_centroid(mesh_obj, [sk_name])
    if c is not None:
        dot = (c - fcx).dot(right)
        if dot > 0.005:
            return +1
        elif dot < -0.005:
            return -1
    name_low = sk_name.lower()
    if "_r" in name_low or ".r" in name_low or "right" in name_low:
        return +1
    elif "_l" in name_low or ".l" in name_low or "left" in name_low:
        return -1
    return 0


def pick_primary_key(keyblock, candidates):
    for c in candidates:
        if c in keyblock:
            return c
    return None


def plan_nte_controls(mesh_obj, armature, head_name, keyblock):
    fwd, right, up, face_size, fcx = get_face_metrics(mesh_obj, armature, head_name)

    OFFSET  = face_size * OFFSET_F
    LIM     = face_size * TRAVEL_F

    def place(feature, h=0.0, v=0.0):
        return feature + fwd * OFFSET + right * h + up * v

    controls = []
    handled_keys = set()

    # 0. Ignore default/basis rest keys
    for k in keyblock.keys():
        kl = k.lower()
        if kl in ["basis", "default", "rest", "00_default_brow", "00_default_eye", "00_default_mouth"]:
            handled_keys.add(k)

    # -------------------------------------------------------------------------
    # Physical Side Classification:
    # +right (+X): Viewer's RIGHT / Character's LEFT (White hair side / Blender .L)
    # -right (-X): Viewer's LEFT / Character's RIGHT (Black hair side / Blender .R)
    # -------------------------------------------------------------------------

    # 1. Classify Wink shapekeys
    wink_keys_posX = []
    wink_keys_negX = []
    for k in ["biyan_R", "biyan_r", "biyan_L", "biyan_l", "biyan", "biyan1"]:
        if k in keyblock:
            s = get_shapekey_side(mesh_obj, k, fcx, right)
            if s == +1 and k not in wink_keys_posX:
                wink_keys_posX.append(k)
            elif s == -1 and k not in wink_keys_negX:
                wink_keys_negX.append(k)

    # 2. Classify Happy / Smile close shapekeys
    happy_keys_posX = []
    happy_keys_negX = []
    for k in ["EL_Happy_r_CLO", "EL_Happy_R_CLO", "EL_Happy_l_CLO", "EL_Happy_L_CLO", "EL_Smile_01_CLO", "biyan1"]:
        if k in keyblock:
            s = get_shapekey_side(mesh_obj, k, fcx, right)
            if s == +1 and k not in happy_keys_posX:
                happy_keys_posX.append(k)
            elif s == -1 and k not in happy_keys_negX:
                happy_keys_negX.append(k)

    # 3. Classify Eyebrow Up/Down shapekeys
    brow_keys_posX = []
    brow_keys_negX = []
    for k in ["EB_UD_R", "EB_UD_r", "EB_R_UD", "EB_r_UD", "EB_UD_L", "EB_UD_l", "EB_L_UD", "EB_l_UD"]:
        if k in keyblock:
            s = get_shapekey_side(mesh_obj, k, fcx, right)
            if s == +1 and k not in brow_keys_posX:
                brow_keys_posX.append(k)
            elif s == -1 and k not in brow_keys_negX:
                brow_keys_negX.append(k)

    # 4. Compute physical positions
    pos_eye_posX = feature_centroid(mesh_obj, wink_keys_posX + happy_keys_posX) or (fcx + up * (face_size * 0.06) + right * (face_size * 0.16) + fwd * (face_size * 0.04))
    pos_eye_negX = feature_centroid(mesh_obj, wink_keys_negX + happy_keys_negX) or (fcx + up * (face_size * 0.06) - right * (face_size * 0.16) + fwd * (face_size * 0.04))

    pos_brow_posX = feature_centroid(mesh_obj, brow_keys_posX) or (pos_eye_posX + up * (face_size * 0.14))
    pos_brow_negX = feature_centroid(mesh_obj, brow_keys_negX) or (pos_eye_negX + up * (face_size * 0.14))

    eyeC = (pos_eye_posX + pos_eye_negX) * 0.5
    browCenter = (pos_brow_posX + pos_brow_negX) * 0.5

    # 5. Mouth Centroid
    mouth_keys = [k for k in keyblock.keys() if "jawopen" in k.lower() or "mouth" in k.lower()]
    mouth = feature_centroid(mesh_obj, ["jawOpen", "jawOpen_a", "jawOpen_Happy_01_OP", "mouthPucker", "mouthRollLower"] + mouth_keys)
    if mouth is None:
        mouth = fcx - up * (face_size * 0.24) + fwd * (face_size * 0.04)

    tri_scale = Vector((face_size * 0.038,) * 3)

    # =========================================================================
    # 1. DIRECT FACIAL CONTROLS
    # =========================================================================

    # 1.A Eye Aim / Look Directions (8 directions)
    look_u = pick_primary_key(keyblock, ["look_U", "Look_U", "Eye_Up"])
    look_d = pick_primary_key(keyblock, ["look_D", "Look_D", "Eye_Down"])
    look_l = pick_primary_key(keyblock, ["look_L", "Look_L", "Eye_Left"])
    look_r = pick_primary_key(keyblock, ["look_R", "Look_R", "Eye_Right"])
    look_lu = pick_primary_key(keyblock, ["look_LU", "Look_LU"])
    look_ld = pick_primary_key(keyblock, ["look_LD", "Look_LD"])
    look_ru = pick_primary_key(keyblock, ["look_RU", "Look_RU"])
    look_rd = pick_primary_key(keyblock, ["look_RD", "Look_RD"])

    aim_drv = []
    right_x_dir = +1 if FLIP_HORIZONTAL else -1
    left_x_dir = -1 if FLIP_HORIZONTAL else +1

    if look_u:
        aim_drv.append({'key': look_u, 'axis': 'Z', 'dir': +1})
        handled_keys.add(look_u)
    if look_d:
        aim_drv.append({'key': look_d, 'axis': 'Z', 'dir': -1})
        handled_keys.add(look_d)
    if look_r:
        aim_drv.append({'key': look_r, 'axis': 'X', 'dir': right_x_dir})
        handled_keys.add(look_r)
    if look_l:
        aim_drv.append({'key': look_l, 'axis': 'X', 'dir': left_x_dir})
        handled_keys.add(look_l)

    if look_ru:
        aim_drv.append({'key': look_ru, 'axis': 'Z', 'dir': +1, 'extra_axis': 'X', 'extra_dir': right_x_dir, 'is_diagonal': True})
        handled_keys.add(look_ru)
    if look_rd:
        aim_drv.append({'key': look_rd, 'axis': 'Z', 'dir': -1, 'extra_axis': 'X', 'extra_dir': right_x_dir, 'is_diagonal': True})
        handled_keys.add(look_rd)
    if look_lu:
        aim_drv.append({'key': look_lu, 'axis': 'Z', 'dir': +1, 'extra_axis': 'X', 'extra_dir': left_x_dir, 'is_diagonal': True})
        handled_keys.add(look_lu)
    if look_ld:
        aim_drv.append({'key': look_ld, 'axis': 'Z', 'dir': -1, 'extra_axis': 'X', 'extra_dir': left_x_dir, 'is_diagonal': True})
        handled_keys.add(look_ld)

    if aim_drv:
        controls.append({
            'name': 'CTRL-Eye-Aim',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYEAIM,
            'group': 'Face Eye-Aim',
            'head': place(eyeC, v=face_size * 0.015),
            'widget': 'ring',
            'lim': LIM,
            'free': ('X', 'Z'),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.050,) * 3),
            'drivers': aim_drv
        })

    # 1.B Eye Open (.L at +X / Viewer Right, .R at -X / Viewer Left)
    open_cand = pick_primary_key(keyblock, ["EL_Surprised_01_OP", "EL_Surprised_01", "EL_Up"])
    if open_cand:
        controls.append({
            'name': 'CTRL-Eye_Open.L',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYELID,
            'group': 'Face Eyelid',
            'head': place(pos_eye_posX, v=face_size * 0.045),
            'widget': 'isaac_blink_top',
            'lim': LIM,
            'free': ('Z',),
            'range': 'pos',
            'shape_scale': tri_scale,
            'drivers': [{'key': open_cand, 'axis': 'Z', 'dir': +1}]
        })
        controls.append({
            'name': 'CTRL-Eye_Open.R',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYELID,
            'group': 'Face Eyelid',
            'head': place(pos_eye_negX, v=face_size * 0.045),
            'widget': 'isaac_blink_top',
            'lim': LIM,
            'free': ('Z',),
            'range': 'pos',
            'shape_scale': tri_scale,
            'drivers': [{'key': open_cand, 'axis': 'Z', 'dir': +1}]
        })

    # 1.C Eye Wink & Smile Close (.L at +X / Viewer Right, .R at -X / Viewer Left)
    wink_k_posX = wink_keys_posX[0] if wink_keys_posX else None
    happy_k_posX = happy_keys_posX[0] if happy_keys_posX else None
    wdrv_posX = []
    if wink_k_posX:
        wdrv_posX.append({'key': wink_k_posX, 'axis': 'Z', 'dir': -1})
        handled_keys.add(wink_k_posX)
    if happy_k_posX and happy_k_posX != wink_k_posX:
        wdrv_posX.append({'key': happy_k_posX, 'axis': 'Z', 'dir': +1})
        handled_keys.add(happy_k_posX)

    if wdrv_posX:
        controls.append({
            'name': 'CTRL-Eye_Wink.L',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYELID,
            'group': 'Face Eyelid',
            'head': place(pos_eye_posX, v=-face_size * 0.045),
            'widget': 'isaac_blink_bot',
            'lim': LIM,
            'free': ('Z',),
            'range': 'both',
            'shape_scale': tri_scale,
            'drivers': wdrv_posX
        })

    wink_k_negX = wink_keys_negX[0] if wink_keys_negX else None
    happy_k_negX = happy_keys_negX[0] if happy_keys_negX else None
    wdrv_negX = []
    if wink_k_negX:
        wdrv_negX.append({'key': wink_k_negX, 'axis': 'Z', 'dir': -1})
        handled_keys.add(wink_k_negX)
    if happy_k_negX and happy_k_negX != wink_k_negX:
        wdrv_negX.append({'key': happy_k_negX, 'axis': 'Z', 'dir': +1})
        handled_keys.add(happy_k_negX)

    if wdrv_negX:
        controls.append({
            'name': 'CTRL-Eye_Wink.R',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYELID,
            'group': 'Face Eyelid',
            'head': place(pos_eye_negX, v=-face_size * 0.045),
            'widget': 'isaac_blink_bot',
            'lim': LIM,
            'free': ('Z',),
            'range': 'both',
            'shape_scale': tri_scale,
            'drivers': wdrv_negX
        })

    # 1.D Center Eye Viseme / Emote Pad
    eye_pad_drv = []
    biyan_all = pick_primary_key(keyblock, ["biyan", "TD_EyesClo", "biyan1"])
    eye_down = pick_primary_key(keyblock, ["EL_Down", "eye_SF"])
    corner_up = pick_primary_key(keyblock, ["EL_CornerUp", "EL_Light_Up"])
    corner_down = pick_primary_key(keyblock, ["EL_CornerDown", "EL_Light_L"])

    if biyan_all and biyan_all not in handled_keys:
        eye_pad_drv.append({'key': biyan_all, 'axis': 'Z', 'dir': +1})
        handled_keys.add(biyan_all)
    if eye_down and eye_down not in handled_keys:
        eye_pad_drv.append({'key': eye_down, 'axis': 'Z', 'dir': -1})
        handled_keys.add(eye_down)
    if corner_up and corner_up not in handled_keys:
        eye_pad_drv.append({'key': corner_up, 'axis': 'X', 'dir': +1})
        handled_keys.add(corner_up)
    if corner_down and corner_down not in handled_keys:
        eye_pad_drv.append({'key': corner_down, 'axis': 'X', 'dir': -1})
        handled_keys.add(corner_down)

    if eye_pad_drv:
        controls.append({
            'name': 'CTRL-Eye-Viseme-Pad',
            'collection': FACERIG_COLLECTION,
            'color': COL_EYEMOTE,
            'group': 'Face Eye-Emote',
            'head': place(eyeC),
            'widget': 'eyeblink',
            'lim': LIM,
            'free': ('X', 'Z'),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.042, face_size * 0.048, face_size * 0.032)),
            'drivers': eye_pad_drv
        })

    # 1.E Eyebrows Direct Controls (.L at +X / Viewer Right, .R at -X / Viewer Left)
    eb_k_posX = brow_keys_posX[0] if brow_keys_posX else None
    if eb_k_posX:
        handled_keys.add(eb_k_posX)
        controls.append({
            'name': 'CTRL-Brow-L_Up',
            'collection': FACERIG_COLLECTION,
            'color': COL_BROW,
            'group': 'Face Eyebrow',
            'head': place(pos_brow_posX),
            'widget': 'eyeblink',
            'lim': LIM,
            'free': ('Z',),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.040, face_size * 0.045, face_size * 0.025)),
            'drivers': [{'key': eb_k_posX, 'axis': 'Z', 'dir': +1}]
        })

    eb_k_negX = brow_keys_negX[0] if brow_keys_negX else None
    if eb_k_negX:
        handled_keys.add(eb_k_negX)
        controls.append({
            'name': 'CTRL-Brow-R_Up',
            'collection': FACERIG_COLLECTION,
            'color': COL_BROW,
            'group': 'Face Eyebrow',
            'head': place(pos_brow_negX),
            'widget': 'eyeblink',
            'lim': LIM,
            'free': ('Z',),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.040, face_size * 0.045, face_size * 0.025)),
            'drivers': [{'key': eb_k_negX, 'axis': 'Z', 'dir': +1}]
        })

    # Eyebrow Center Pad
    eb_pad_drv = []
    eb_happy = pick_primary_key(keyblock, ["EB_happy_01", "EB_Happy_01", "EB_Smile_01"])
    eb_sad = pick_primary_key(keyblock, ["EB_Sad_01", "EB_Tired_01"])
    eb_angry = pick_primary_key(keyblock, ["EB_Angry_01", "EB_Evil_01"])
    eb_surprised = pick_primary_key(keyblock, ["EB_Surprised_01", "EB_Doubt_01"])

    if eb_happy: eb_pad_drv.append({'key': eb_happy, 'axis': 'Z', 'dir': +1})
    if eb_sad: eb_pad_drv.append({'key': eb_sad, 'axis': 'Z', 'dir': -1})
    if eb_angry: eb_pad_drv.append({'key': eb_angry, 'axis': 'X', 'dir': +1})
    if eb_surprised: eb_pad_drv.append({'key': eb_surprised, 'axis': 'X', 'dir': -1})

    if eb_pad_drv:
        controls.append({
            'name': 'CTRL-Eyebrow-Viseme-Pad',
            'collection': FACERIG_COLLECTION,
            'color': COL_EBRMASTER,
            'group': 'Face Eyebrow',
            'head': place(browCenter),
            'widget': 'pad',
            'lim': LIM,
            'free': ('X', 'Z'),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.055, face_size * 0.060, face_size * 0.038)),
            'drivers': eb_pad_drv
        })

    # 1.F Mouth Main Shift (Lipsmaster)
    mouth_drv = []
    jaw_open = pick_primary_key(keyblock, ["jawOpen", "jawOpen_a"])
    jaw_yi = pick_primary_key(keyblock, ["jawOpen_yi", "jawOpen_Smile_01_OP", "jawOpen_Happy_01_OP"])
    mouth_pucker = pick_primary_key(keyblock, ["mouthPucker", "jawOpen_wu"])
    mouth_funnel = pick_primary_key(keyblock, ["mouthFunnel", "jawOpen_o"])

    if jaw_yi: mouth_drv.append({'key': jaw_yi, 'axis': 'Z', 'dir': +1})
    if jaw_open:
        mouth_drv.append({'key': jaw_open, 'axis': 'Z', 'dir': -1})
        handled_keys.add(jaw_open)
    if mouth_pucker: mouth_drv.append({'key': mouth_pucker, 'axis': 'X', 'dir': +1})
    if mouth_funnel: mouth_drv.append({'key': mouth_funnel, 'axis': 'X', 'dir': -1})

    if mouth_drv:
        mouth_scale = Vector((face_size * 0.080, face_size * 0.080, face_size * 0.045))
        controls.append({
            'name': 'CTRL-Mouth-Shift',
            'collection': FACERIG_COLLECTION,
            'color': COL_MOUTH,
            'group': 'Face Mouth',
            'head': place(mouth),
            'widget': 'lipsmaster',
            'lim': LIM,
            'free': ('X', 'Z'),
            'range': 'both',
            'shape_scale': mouth_scale,
            'drivers': mouth_drv
        })

    # =========================================================================
    # 2. SIDE PANELS: HSR-STYLE LATERAL CONTROLLERS
    # =========================================================================

    MAX_PER_ROW = 10
    ROW_Z_GAP = 0.155
    ITEM_SP = 0.075

    slider_shape_scale = Vector((face_size * 0.035, face_size * 0.035, face_size * 0.035))
    label_scale = Vector((face_size * 0.045, face_size * 0.045, face_size * 0.045))

    # -------------------------------------------------------------------------
    # LEFT PANEL (A la IZQUIERDA de la cabeza, -right)
    # -------------------------------------------------------------------------
    left_panel_origin = fcx - right * (face_size * 0.72) + up * (face_size * 0.12)
    current_left_v = 0.0

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
                'shape_scale': slider_shape_scale,
                'drivers': drv_list
            })

        num_rows = (total + MAX_PER_ROW - 1) // MAX_PER_ROW
        current_left_v -= num_rows * (face_size * ROW_Z_GAP) + (face_size * 0.015)

    # 2.A Eyebrows Grid (Cejas - Verde)
    unhandled_eb = [k for k in keyblock.keys() if (k.startswith("EB_") or "eyebrow" in k.lower() or "brow" in k.lower()) and k not in handled_keys]
    if unhandled_eb:
        eb_items = []
        for k in unhandled_eb:
            clean_k = k.replace("EB_", "").replace("Eyebrow_", "").replace("brow_", "")
            c_name = f"CTRL-EB_{clean_k}"
            handled_keys.add(k)
            eb_items.append((c_name, [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_left_panel_grid(eb_items, 'Face Eyebrows', (0.30, 0.80, 0.35))

    # 2.B Eye Expressions Grid (Ojos - Cyan / Azul)
    unhandled_el = [k for k in keyblock.keys() if (k.startswith("EL_") or "eye" in k.lower() or "biyan" in k.lower()) and k not in handled_keys]
    if unhandled_el:
        el_items = []
        for k in unhandled_el:
            clean_k = k.replace("EL_", "").replace("Eye_", "")
            c_name = f"CTRL-EL_{clean_k}"
            handled_keys.add(k)
            el_items.append((c_name, [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_left_panel_grid(el_items, 'Face Eye Expressions', COL_EYEAIM)

    # Add Left Panel Header Label
    if unhandled_eb or unhandled_el:
        controls.append({
            'name': 'LABEL-Brows_Eyes',
            'collection': FACERIG_COLLECTION,
            'color': COL_LABEL,
            'group': 'Face Labels',
            'head': place(left_panel_origin, h=-4.5 * (face_size * ITEM_SP), v=face_size * 0.075),
            'widget': 'text:BROWS & EYES',
            'lim': 0.0,
            'free': (),
            'range': 'pos',
            'shape_scale': label_scale,
            'is_label': True,
            'drivers': []
        })

    # -------------------------------------------------------------------------
    # RIGHT PANEL (A la DERECHA de la cabeza, +right)
    # -------------------------------------------------------------------------
    right_panel_origin = fcx + right * (face_size * 0.72) + up * (face_size * 0.12)
    current_right_v_col1 = 0.0
    current_right_v_col2 = 0.0
    col2_offset = face_size * (ITEM_SP * MAX_PER_ROW + 0.06)

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
                'shape_scale': slider_shape_scale,
                'drivers': drv_list
            })

        num_rows = (total + MAX_PER_ROW - 1) // MAX_PER_ROW
        v_drop = num_rows * (face_size * ROW_Z_GAP) + (face_size * 0.015)
        if is_col2:
            current_right_v_col2 -= v_drop
        else:
            current_right_v_col1 -= v_drop

    # 2.C Visemes (jawOpen_a, jawOpen_yi, jawOpen_wu, jawOpen_ei, jawOpen_o - Amarillo, Columna 1)
    viseme_map = [
        ("A", ["jawOpen_a", "jawOpen_A"]),
        ("I", ["jawOpen_yi", "jawOpen_i", "jawOpen_I"]),
        ("U", ["jawOpen_wu", "jawOpen_u", "jawOpen_U"]),
        ("E", ["jawOpen_ei", "jawOpen_e", "jawOpen_E"]),
        ("O", ["jawOpen_o", "jawOpen_O"]),
    ]
    viseme_items = []
    for label, cands in viseme_map:
        pk = pick_primary_key(keyblock, cands)
        if pk and pk not in handled_keys:
            handled_keys.add(pk)
            viseme_items.append((f"CTRL-Viseme_{label}", [{'key': pk, 'axis': 'Z', 'dir': +1}]))
    if viseme_items:
        add_right_panel_grid(viseme_items, 'Face Visemes', COL_VISEME, is_col2=False)

    # 2.D Mouth Expressions (jawOpen_*_OP, jawOpen_*_CLO, mouth* - Púrpura, Columna 1)
    unhandled_mouth = [k for k in keyblock.keys() if (k.startswith("jawOpen_") or "mouth" in k.lower() or "jaw" in k.lower()) and k not in handled_keys]
    if unhandled_mouth:
        m_items = []
        for k in unhandled_mouth:
            clean_k = k.replace("jawOpen_", "").replace("mouth", "")
            c_name = f"CTRL-Mth_{clean_k}" if clean_k else f"CTRL-{k}"
            handled_keys.add(k)
            m_items.append((c_name, [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_right_panel_grid(m_items, 'Face Mouth Expressions', COL_EXPRESSION, is_col2=False)

    # Add Right Panel Col 1 Header Label (Mouth)
    if viseme_items or unhandled_mouth:
        controls.append({
            'name': 'LABEL-Mouth',
            'collection': FACERIG_COLLECTION,
            'color': COL_LABEL,
            'group': 'Face Labels',
            'head': place(right_panel_origin, h=2.0 * (face_size * ITEM_SP), v=face_size * 0.075),
            'widget': 'text:MOUTH',
            'lim': 0.0,
            'free': (),
            'range': 'pos',
            'shape_scale': label_scale,
            'is_label': True,
            'drivers': []
        })

    # 2.E 2D Special Manga Symbols (TDS_ & TD_ - Naranja / Magenta, Columna 2)
    td_keys = [k for k in keyblock.keys() if (k.startswith("TDS_") or k.startswith("TD_")) and k not in handled_keys]
    if td_keys:
        td_items = []
        for k in td_keys:
            c_name = f"CTRL-{k}"
            handled_keys.add(k)
            td_items.append((c_name, [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_right_panel_grid(td_items, 'Face 2D TDS Effects', COL_TD_SPECIAL, is_col2=True)

    # 2.F Extra Shapekeys Fallback (Cualquier otro shapekey no categorizado - Columna 2)
    remaining = [k for k in keyblock.keys() if k not in handled_keys]
    if remaining:
        rem_items = []
        for k in remaining:
            handled_keys.add(k)
            rem_items.append((f"CTRL-{k}", [{'key': k, 'axis': 'Z', 'dir': +1}]))
        add_right_panel_grid(rem_items, 'Face Extra Keys', (0.25, 0.75, 0.35), is_col2=True)

    # Add Right Panel Col 2 Header Label (2D VFX)
    if td_keys or remaining:
        controls.append({
            'name': 'LABEL-2D_VFX',
            'collection': FACERIG_COLLECTION,
            'color': COL_LABEL,
            'group': 'Face Labels',
            'head': place(right_panel_origin, h=col2_offset + 4.5 * (face_size * ITEM_SP), v=face_size * 0.075),
            'widget': 'text:2D VFX',
            'lim': 0.0,
            'free': (),
            'range': 'pos',
            'shape_scale': label_scale,
            'is_label': True,
            'drivers': []
        })

    return controls


# =============================================================================
# WIDGET BUILDER AND MESH SHAPES
# =============================================================================

EYE_MASTER_VERTS = [[-0.40348, 0.0, 0.32632], [-0.28803, 0.0, 0.29715], [-0.21194, 0.0, 0.24992], [0.0, 0.0, -0.19968], [0.0, 0.0, 0.19968], [-0.21194, 0.0, -0.24992], [-0.28803, 0.0, -0.29715], [-0.40348, 0.0, -0.32632], [-0.53133, 0.0, -0.31136], [-0.64684, 0.0, -0.24534], [-0.72806, 0.0, -0.13551], [-0.7574, 0.0, 0.0], [-0.72806, 0.0, 0.13551], [-0.64684, 0.0, 0.24534], [-0.53133, 0.0, 0.31136], [-0.11372, 0.0, 0.1995], [-0.11372, 0.0, -0.1995], [-0.03778, 0.0, -0.19971], [-0.03778, 0.0, 0.19971], [-0.16207, 0.0, 0.20723], [-0.16207, 0.0, -0.20723], [-0.34203, 0.0, 0.3157], [-0.24529, 0.0, 0.2746], [-0.0037, 0.0, -0.19969], [-0.07706, 0.0, 0.1997], [-0.24529, 0.0, -0.2746], [-0.34203, 0.0, -0.3157], [-0.4676, 0.0, -0.32523], [-0.59202, 0.0, -0.28451], [-0.693, 0.0, -0.19498], [-0.74991, 0.0, -0.06945], [-0.74991, 0.0, 0.06945], [-0.693, 0.0, 0.19498], [-0.59202, 0.0, 0.28451], [-0.4676, 0.0, 0.32523], [-0.18492, 0.0, 0.22542], [-0.07706, 0.0, -0.1997], [-0.0037, 0.0, 0.19969], [-0.14053, 0.0, -0.20011], [-0.14053, 0.0, 0.20011], [-0.18492, 0.0, -0.22542], [0.40348, 0.0, 0.32632], [0.28803, 0.0, 0.29715], [0.21194, 0.0, 0.24992], [-0.0, 0.0, -0.19968], [-0.0, 0.0, 0.19968], [0.21194, 0.0, -0.24992], [0.28803, 0.0, -0.29715], [0.40348, 0.0, -0.32632], [0.53133, 0.0, -0.31136], [0.64684, 0.0, -0.24534], [0.72806, 0.0, -0.13551], [0.7574, 0.0, 0.0], [0.72806, 0.0, 0.13551], [0.64684, 0.0, 0.24534], [0.53133, 0.0, 0.31136], [0.11372, 0.0, 0.1995], [0.11372, 0.0, -0.1995], [0.03778, 0.0, -0.19971], [0.03778, 0.0, 0.19971], [0.16207, 0.0, 0.20723], [0.16207, 0.0, -0.20723], [0.34203, 0.0, 0.3157], [0.24529, 0.0, 0.2746], [0.0037, 0.0, -0.19969], [0.07706, 0.0, 0.1997], [0.24529, 0.0, -0.2746], [0.34203, 0.0, -0.3157], [0.4676, 0.0, -0.32523], [0.59202, 0.0, -0.28451], [0.693, 0.0, -0.19498], [0.74991, 0.0, -0.06945], [0.74991, 0.0, 0.06945], [0.693, 0.0, 0.19498], [0.59202, 0.0, 0.28451], [0.4676, 0.0, 0.32523], [0.18492, 0.0, 0.22542], [0.07706, 0.0, -0.1997], [0.0037, 0.0, 0.19969], [0.14053, 0.0, -0.20011], [0.14053, 0.0, 0.20011], [0.18492, 0.0, -0.22542]]
EYE_MASTER_EDGES = [[1, 21], [0, 21], [2, 22], [1, 22], [17, 23], [3, 23], [18, 24], [15, 24], [6, 25], [5, 25], [7, 26], [6, 26], [8, 27], [7, 27], [9, 28], [8, 28], [10, 29], [9, 29], [11, 30], [10, 30], [12, 31], [11, 31], [13, 32], [12, 32], [14, 33], [13, 33], [0, 34], [14, 34], [19, 35], [2, 35], [16, 36], [17, 36], [4, 37], [18, 37], [20, 38], [16, 38], [15, 39], [19, 39], [5, 40], [20, 40], [42, 62], [41, 62], [43, 63], [42, 63], [58, 64], [44, 64], [59, 65], [56, 65], [47, 66], [46, 66], [48, 67], [47, 67], [49, 68], [48, 68], [50, 69], [49, 69], [51, 70], [50, 70], [52, 71], [51, 71], [53, 72], [52, 72], [54, 73], [53, 73], [55, 74], [54, 74], [41, 75], [55, 75], [60, 76], [43, 76], [57, 77], [58, 77], [45, 78], [59, 78], [61, 79], [57, 79], [56, 80], [60, 80], [46, 81], [61, 81]]
EYE_CIRCLE_VERTS = [[0.0, 0.0, 0.5], [-0.09755, 0.0, 0.49039], [-0.19134, 0.0, 0.46194], [-0.27779, 0.0, 0.41574], [-0.35355, 0.0, 0.35355], [-0.41574, 0.0, 0.27779], [-0.46194, 0.0, 0.19134], [-0.49039, 0.0, 0.09755], [-0.5, 0.0, -0.0], [-0.49039, 0.0, -0.09755], [-0.46194, 0.0, -0.19134], [-0.41574, 0.0, -0.27779], [-0.35355, 0.0, -0.35355], [-0.27779, 0.0, -0.41574], [-0.19134, 0.0, -0.46194], [-0.09755, 0.0, -0.49039], [0.0, 0.0, -0.5], [0.09755, 0.0, -0.49039], [0.19134, 0.0, -0.46194], [0.27779, 0.0, -0.41574], [0.35355, 0.0, -0.35355], [0.41574, 0.0, -0.27779], [0.46194, 0.0, -0.19134], [0.49039, 0.0, -0.09755], [0.5, 0.0, 0.0], [0.49039, 0.0, 0.09755], [0.46194, 0.0, 0.19134], [0.41573, 0.0, 0.27779], [0.35355, 0.0, 0.35355], [0.27779, 0.0, 0.41574], [0.19134, 0.0, 0.46194], [0.09754, 0.0, 0.49039]]
EYE_CIRCLE_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [25, 26], [26, 27], [27, 28], [28, 29], [29, 30], [30, 31], [0, 31]]
LIPS_MASTER_VERTS = [[0.0, 0.19233, 0.11033], [0.13499, 0.18609, 0.10769], [0.2648, 0.15671, 0.10386], [0.38443, 0.10515, 0.09906], [0.48929, 0.03669, 0.09225], [0.57534, -0.04048, 0.08167], [0.63928, -0.11576, 0.0649], [0.67866, -0.17692, 0.03916], [0.69195, -0.21104, 0.00157], [0.67866, -0.20938, -0.04918], [0.63928, -0.17943, -0.10838], [0.57534, -0.13291, -0.1699], [0.48929, -0.08096, -0.22793], [0.38443, -0.03318, -0.27744], [0.2648, 0.00301, -0.31449], [0.13499, 0.02292, -0.33643], [-0.0, 0.02596, -0.34248], [-0.135, 0.02292, -0.33643], [-0.2648, 0.00301, -0.31449], [-0.38443, -0.03318, -0.27744], [-0.48929, -0.08096, -0.22793], [-0.57534, -0.13291, -0.1699], [-0.63928, -0.17943, -0.10838], [-0.67866, -0.20938, -0.04917], [-0.69195, -0.21104, 0.00157], [-0.67866, -0.17692, 0.03916], [-0.63928, -0.11576, 0.0649], [-0.57534, -0.04048, 0.08167], [-0.48928, 0.03669, 0.09225], [-0.38442, 0.10515, 0.09906], [-0.26479, 0.15671, 0.10386], [-0.13499, 0.1861, 0.10769]]
LIPS_MASTER_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [25, 26], [26, 27], [27, 28], [28, 29], [29, 30], [30, 31], [0, 31]]
EYEBLINK_VERTS = [[-0.42167, 0.0, -0.22917], [0.42167, 0.0, -0.22917], [-0.42167, -0.0, 0.22917], [0.42167, -0.0, 0.22917], [0.46, 0.0, -0.125], [0.46, 0.0, -0.0], [0.46, -0.0, 0.125], [-0.23, 0.0, -0.25], [-0.0, 0.0, -0.25], [0.23, 0.0, -0.25], [-0.46, 0.0, -0.125], [-0.46, -0.0, 0.0], [-0.46, -0.0, 0.125], [-0.23, -0.0, 0.25], [0.0, -0.0, 0.25], [0.23, -0.0, 0.25], [0.4594, -0.0, 0.15592], [0.45521, -0.0, 0.1849], [0.44383, -0.0, 0.20996], [0.2869, 0.0, -0.24968], [0.34021, 0.0, -0.2474], [0.38633, 0.0, -0.24121], [-0.4594, -0.0, 0.15592], [-0.45521, -0.0, 0.1849], [-0.44383, -0.0, 0.20996], [0.2869, -0.0, 0.24968], [0.34021, -0.0, 0.2474], [0.38633, -0.0, 0.24121], [0.44383, 0.0, -0.20996], [0.45521, 0.0, -0.1849], [0.4594, 0.0, -0.15592], [0.46, 0.0, -0.0625], [0.46, -0.0, 0.0625], [-0.38633, 0.0, -0.24121], [-0.34021, 0.0, -0.2474], [-0.2869, 0.0, -0.24967], [-0.115, 0.0, -0.25], [0.115, 0.0, -0.25], [-0.44383, 0.0, -0.20996], [-0.45521, 0.0, -0.1849], [-0.4594, 0.0, -0.15592], [-0.46, 0.0, -0.0625], [-0.46, -0.0, 0.0625], [-0.38633, -0.0, 0.24121], [-0.34021, -0.0, 0.2474], [-0.2869, -0.0, 0.24967], [-0.115, -0.0, 0.25], [0.115, -0.0, 0.25], [-0.39485, -0.00338, -0.20822], [0.39485, 0.00338, -0.20822], [-0.39485, -0.00338, 0.20822], [0.39485, 0.00338, 0.20822], [0.43075, 0.00369, -0.11357], [0.43075, 0.00369, 0.11358], [-0.43075, -0.00369, -0.11357], [-0.43075, -0.00369, 0.11358], [0.43018, 0.00368, 0.14167], [0.42626, 0.00365, 0.168], [0.4156, 0.00356, 0.19077], [0.31857, 0.00273, -0.22478], [0.36176, 0.0031, -0.21916], [-0.43018, -0.00368, 0.14167], [-0.42626, -0.00365, 0.168], [-0.4156, -0.00356, 0.19077], [0.31857, 0.00273, 0.22479], [0.36176, 0.0031, 0.21917], [0.4156, 0.00356, -0.19077], [0.42626, 0.00365, -0.16799], [0.43018, 0.00368, -0.14167], [-0.36176, -0.0031, -0.21916], [-0.31857, -0.00273, -0.22478], [-0.4156, -0.00356, -0.19077], [-0.42626, -0.00365, -0.16799], [-0.43018, -0.00368, -0.14167], [-0.36176, -0.0031, 0.21917], [-0.31857, -0.00273, 0.22479]]
EYEBLINK_EDGES = [[6, 16], [16, 17], [17, 18], [3, 18], [9, 19], [19, 20], [20, 21], [1, 21], [12, 22], [22, 23], [23, 24], [2, 24], [15, 25], [25, 26], [26, 27], [3, 27], [1, 28], [28, 29], [29, 30], [4, 30], [4, 31], [5, 31], [5, 32], [6, 32], [0, 33], [33, 34], [34, 35], [7, 35], [7, 36], [8, 36], [8, 37], [9, 37], [0, 38], [38, 39], [39, 40], [10, 40], [10, 41], [11, 41], [11, 42], [12, 42], [2, 43], [43, 44], [44, 45], [13, 45], [13, 46], [14, 46], [14, 47], [15, 47], [53, 56], [56, 57], [57, 58], [51, 58], [59, 60], [49, 60], [55, 61], [61, 62], [62, 63], [50, 63], [64, 65], [51, 65], [49, 66], [66, 67], [67, 68], [52, 68], [48, 69], [69, 70], [48, 71], [71, 72], [72, 73], [54, 73], [50, 74], [74, 75]]
ISAAC_BLINK_TOP_VERTS = [[1.0, 0.0, 0.5638], [-1.0, 0.0, 0.5638], [-0.0, 0.0, 0.8878], [-0.0, 0.0, -0.484], [-0.5916, 0.0, -0.0569], [0.5916, 0.0, -0.0569], [0.6306, 0.0, 0.8199], [-0.6306, 0.0, 0.8199], [-1.0, 0.0, 0.5638], [-0.0, 0.0, -0.484], [1.0, 0.0, 0.5638]]
ISAAC_BLINK_TOP_EDGES = [[7, 1], [4, 1], [3, 4], [6, 2], [5, 3], [0, 5], [0, 6], [2, 7], [1, 8], [3, 9], [0, 10]]
ISAAC_BLINK_BOT_VERTS = [[-1.0, 0.0, -0.5638], [1.0, 0.0, -0.5638], [0.0, 0.0, -0.8878], [0.0, 0.0, 0.484], [0.5916, 0.0, 0.0569], [-0.5916, 0.0, 0.0569], [-0.6306, 0.0, -0.8199], [0.6306, 0.0, -0.8199], [1.0, 0.0, -0.5638], [0.0, 0.0, 0.484], [-1.0, 0.0, -0.5638]]
ISAAC_BLINK_BOT_EDGES = [[7, 1], [4, 1], [3, 4], [6, 2], [5, 3], [0, 5], [0, 6], [2, 7], [1, 8], [3, 9], [0, 10]]


def make_widget(kind, coll):
    name = "WGT-Face_" + kind
    obj = bpy.data.objects.get(name)
    if obj:
        return obj
    if kind == 'isaac_blink_top':
        verts = ISAAC_BLINK_TOP_VERTS
        edges = ISAAC_BLINK_TOP_EDGES
    elif kind == 'isaac_blink_bot':
        verts = ISAAC_BLINK_BOT_VERTS
        edges = ISAAC_BLINK_BOT_EDGES
    elif kind == 'lipsmaster':
        verts = LIPS_MASTER_VERTS
        edges = LIPS_MASTER_EDGES
    elif kind == 'eyeblink':
        verts = EYEBLINK_VERTS
        edges = EYEBLINK_EDGES
    elif kind == 'eyemaster':
        verts = EYE_MASTER_VERTS
        edges = EYE_MASTER_EDGES
    elif kind == 'eyecircle':
        verts = EYE_CIRCLE_VERTS
        edges = EYE_CIRCLE_EDGES
    elif kind == 'pad':
        s = 1.0
        verts = [(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    elif kind == 'slider':
        verts = [(0, 0, -1), (0, 0, 1), (-0.45, 0, 1), (0.45, 0, 1)]
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


def get_widget_collection():
    # Prefer per-character WGTS_<Char> (Append-safe), canonical name shared with rig
    try:
        from setup_wizard.ui.character_settings_utils import resolve_settings_armature, resolve_character_name
        arm = resolve_settings_armature(bpy.context)
        if arm is not None:
            char_name = resolve_character_name(arm)
            if char_name:
                per_char = bpy.data.collections.get(f"WGTS_{char_name}")
                if per_char is not None:
                    return per_char
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

    coll = bpy.data.collections.new("WGTS")
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


# =============================================================================
# FACE RIG SETUP AND DRIVER GENERATION
# =============================================================================

def setup_nte_face_rig(mesh_obj, controls, armature, head_name, fwd, up, face_size, keyblock):
    print(f"Building {len(controls)} NTE face controls on '{armature.name}' under '{head_name}'")

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

    # Bone Collections Setup
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

        # Place Face-Root into Face (Secondary)
        sec_coll = None
        for scn in ["Face (Secondary)", "Face(Secondary)", "Face Secondary"]:
            if scn in armature.data.collections:
                sec_coll = armature.data.collections[scn]
                break
        if not sec_coll:
            sec_coll = armature.data.collections.new("Face (Secondary)")
            try:
                sec_coll.is_visible = False
            except Exception:
                pass
            try:
                sec_coll.rigify_ui_row = RIGIFY_UI_ROW
            except Exception:
                pass

        root_bone = armature.data.bones.get("Face-Root")
        if root_bone and sec_coll:
            for c in list(root_bone.collections):
                c.unassign(root_bone)
            sec_coll.assign(root_bone)
    elif is_blender_3():
        root_bone = armature.data.bones.get("Face-Root")
        if root_bone:
            root_bone.layers = [i == 1 for i in range(32)]

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

    # Build Shape Key Drivers
    agg = {}
    for c in controls:
        for d in c['drivers']:
            agg.setdefault(d['key'], []).append({
                'bone': c['name'],
                'axis': d['axis'],
                'dir': d['dir'],
                'lim': c['lim'],
                'bidir': d.get('bidir', False),
                'gain': d.get('gain', 1.0),
                'is_diagonal': d.get('is_diagonal', False),
                'extra_axis': d.get('extra_axis'),
                'extra_dir': d.get('extra_dir', 1)
            })

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
        var_count = 0

        for e in entries:
            vn1 = f"v{var_count}"
            var1 = drv.variables.new()
            var1.name = vn1
            var1.type = 'TRANSFORMS'
            tgt1 = var1.targets[0]
            tgt1.id = armature
            tgt1.bone_target = e['bone']
            tgt1.transform_type = 'LOC_' + e['axis']
            tgt1.transform_space = 'LOCAL_SPACE'
            var_count += 1

            sign1 = '' if e['dir'] > 0 else '-'
            lim = e['lim']
            gain = e.get('gain', 1.0)

            if e.get('is_diagonal') and e.get('extra_axis'):
                vn2 = f"v{var_count}"
                var2 = drv.variables.new()
                var2.name = vn2
                var2.type = 'TRANSFORMS'
                tgt2 = var2.targets[0]
                tgt2.id = armature
                tgt2.bone_target = e['bone']
                tgt2.transform_type = 'LOC_' + e['extra_axis']
                tgt2.transform_space = 'LOCAL_SPACE'
                var_count += 1
                sign2 = '' if e['extra_dir'] > 0 else '-'

                term = f"max(0.0, min({sign1}{vn1} / {lim!r}, {sign2}{vn2} / {lim!r}))"
            elif e.get('bidir'):
                term = f"{sign1}{vn1} / {lim!r}"
            else:
                term = f"max(0.0, {sign1}{vn1} / {lim!r})"

            if gain != 1.0:
                term = f"({gain!r} * {term})"
            terms.append(term)

        drv.expression = terms[0] if len(terms) == 1 else "max(" + ", ".join(terms) + ")"


def setup_common_face_materials_if_present():
    """
    Ensures that any common_face (or MI_common_face_mask) material in the scene
    has the correct Mix Shader + Transparent BSDF + Image Texture nodes connected.
    """
    for mat in bpy.data.materials:
        if not mat:
            continue
        mname = mat.name.lower()
        if any(k in mname for k in ["common_face", "common_face_mask", "face_mask", "facemask"]):
            try:
                from setup_wizard.replace_default_materials_setup.game_default_material_replacers import setup_common_face_material
                setup_common_face_material(mat)
            except Exception as ex:
                print(f"Notice: Setting up common_face material {mat.name}: {ex}")


def cleanup_head_driver_to_wgts_if_present(armature=None, head_name=None):
    """
    Finds Head Origin / Head Driver object hierarchy and places them into the WGTS collection,
    ensuring Child Of constraint points to the armature's head bone.
    """
    head_origin = (
        bpy.data.objects.get("Head Origin")
        or bpy.data.objects.get("Head Driver")
        or bpy.data.objects.get("Head Direction")
    )
    if not head_origin:
        for obj in bpy.data.objects:
            if obj.type == "EMPTY" and (
                obj.name.startswith("Head Origin")
                or obj.name.startswith("Head Driver")
                or obj.name.startswith("Head Direction")
            ):
                head_origin = obj
                break

    if not head_origin:
        return

    # Find WGTS collection
    wgt_coll = None
    for c in bpy.data.collections:
        if c.name.startswith("WGTS") or c.name.lower() == "wgt":
            wgt_coll = c
            break
    if not wgt_coll:
        wgt_coll = bpy.data.collections.get("WGTS") or bpy.data.collections.get("wgt")
    if not wgt_coll:
        wgt_coll = bpy.data.collections.new("WGTS")
        try:
            bpy.context.scene.collection.children.link(wgt_coll)
        except Exception:
            pass

    # Ensure Child Of constraint on Head Origin
    if armature and head_name:
        con = None
        for c in head_origin.constraints:
            if c.type == "CHILD_OF":
                con = c
                break
        if not con:
            con = head_origin.constraints.new("CHILD_OF")
        con.target = armature
        con.subtarget = head_name

    def get_all_children(obj):
        res = []
        for ch in obj.children:
            res.append(ch)
            res.extend(get_all_children(ch))
        return res

    all_objs = [head_origin] + get_all_children(head_origin)
    for o in all_objs:
        if o.name not in wgt_coll.objects:
            wgt_coll.objects.link(o)
        for col in list(o.users_collection):
            if col != wgt_coll:
                try:
                    col.objects.unlink(o)
                except Exception:
                    pass
        try:
            o.hide_viewport = True
            o.hide_render = True
        except Exception:
            pass

    try:
        wgt_coll.hide_viewport = True
        wgt_coll.hide_render = True
    except Exception:
        pass


def nte_face_rig_main():
    faceobj = find_face_mesh()
    if faceobj is None:
        print("NTE Face Rig: No face mesh found.")
        return
    if faceobj.data.shape_keys is None:
        print("NTE Face Rig: Face mesh has no shape keys.")
        return

    keyblock = faceobj.data.shape_keys.key_blocks
    armature, head_name = find_armature_and_head(faceobj)
    fwd, right, up, face_size, fcx = get_face_metrics(faceobj, armature, head_name)
    controls = plan_nte_controls(faceobj, armature, head_name, keyblock)

    if not controls:
        print("NTE Face Rig: No drivable shape keys found.")
        return

    if CLEAN_REBUILD:
        purge_previous(armature)

    setup_nte_face_rig(faceobj, controls, armature, head_name, fwd, up, face_size, keyblock)

    wgt_coll = get_widget_collection()
    finalize_widget_collection(wgt_coll)

    setup_common_face_materials_if_present()
    cleanup_head_driver_to_wgts_if_present(armature, head_name)

    print(f"\nNTE Face Rig complete: {len(controls)} controls built on '{armature.name}'.\n")


if __name__ == "__main__":
    nte_face_rig_main()
