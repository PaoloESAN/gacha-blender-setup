# BIG CREDITS to these people <3:
# Poke/Enthralpy | Driver Logic
# Isaac/Just_ScaasI | Facerig Logic + Widgets
# The_Crabnuts/Kan_Natto | Facerig Logic + Widgets

import bpy
import os
import tempfile
import mathutils
from mathutils import Vector, Matrix

HEAD_BONE_NAME   = None
CLEAN_REBUILD    = True
FLIP_HORIZONTAL  = True
FLIP_VERTICAL    = False
FLIP_EYE_LR      = False

BONE_LEN_F   = 0.020
OFFSET_F     = 0.120
TRAVEL_F     = 0.050
SPACING_F    = 0.055
WIDGET_F     = 1.0
EYE_LOOK_FWD_F = 0.45
SPINE_REF_Z = None
FACERIG_COLLECTION = "Face"
RIGIFY_UI_ROW = 1

EYE_HL_F     = 0.013
TRI_F        = 0.022
EMOTE_W_F    = 0.011
EMOTE_H_F    = 0.006
EMOTE_LIM_F  = 0.022
EMOTE_SPACING_F = 0.045
EMOTE_FWD_F  = 0.050
MOUTH_SHIFT_F = 0.55
MOUTH_RAISE_F = 0.040
EBR_WGT_F    = 0.016
EBR_MASTER_F = 0.030

COL_MOUTH   = (0.90, 0.20, 0.20)
COL_CORNER  = (0.15, 0.85, 0.30)
COL_VISEME  = (0.95, 0.85, 0.20)
COL_EYELID  = (0.90, 0.15, 0.15)
COL_EYEAIM  = (0.20, 0.85, 0.90)
COL_EYEGREEN = (0.20, 0.85, 0.30)
COL_EYEMOTE = (0.90, 0.20, 0.20)
COL_BROW    = (0.30, 0.80, 0.35)
COL_BROWSAD = (0.95, 0.45, 0.75)
COL_EBRBONE = (0.20, 0.55, 0.95)
COL_EBRMASTER = (0.65, 0.35, 0.90)

HEAD_CANDIDATES = [
    "DEF-spine.006", "spine.006", "head", "Head", "Head_M", "head_M",
    "Bip001 Head", "Bip001_Head", "Bip001Head", "Bip001 头", "頭", "头",
]


def is_blender_5():
    return bpy.app.version[0] == 5


def is_blender_4():
    return bpy.app.version[0] == 4


def is_blender_3():
    return bpy.app.version[0] == 3


_blender_ver = bpy.app.version[0]
if _blender_ver < 3:
    raise Exception("This script targets Blender 3.x, 4.x, or 5.x.")

ver = _blender_ver


def shapekeyrename(keyblock):
    for sk in keyblock:
        if sk.name.endswith("_Unagi") or sk.name.endswith("_Anton") or sk.name.endswith("_Corin"):
            sk.name = sk.name[:-6]
        if sk.name.endswith("_NuoCha"):
            sk.name = sk.name[:-7]
    rename_map = {
        "Mouth_↖_Ben": "Fac_Mth_R_Up",   "Mouth_↗_Ben": "Fac_Mth_L_Up",
        "Mouth_↙_Ben": "Fac_Mth_R_Down", "Mouth_↘_Ben": "Fac_Mth_L_Down",
        "Mouth_上颌↑_Ben": "Fac_Mth_Up",  "Mouth_下颌↓_Ben": "Fac_Mth_Down",
        "Mouth_呲_L_Ben": "Fac_Mth_L_In", "Mouth_呲_R_Ben": "Fac_Mth_R_In",
        "Eye_Open_↑_Ben": "Fac_Eye_R_Open", "Mouth_Oo_Ben": "Fac_Mth_UuOo",
        "Eye_Close2_Ben": "Fac_Eye_Sad",
        "Eye_Ball_↑_Ben": "Eye_Up", "Eye_Ball_↓_Ben": "Eye_Down",
        "Eye_Ball_→_Ben": "Eye_Left", "Eye_Ball_←_Ben": "Eye_Right",
        "Eye_Ball_No_Ben": "O_O",
        "Mouth_啧_R_Ben": "Fac_Mth_R_Out", "Mouth_啧_L_Ben": "Fac_Mth_L_Out",
        "Mouth_Ii1": "Fac_Mth_Ii",
        "Fac_Mth_Aa": "Fac_Mth_Aa1",
        "Fac_Mth_ooR": "Fac_Mth_R_Out", "Fac_Mth_Roo": "Fac_Mth_R_In",
        "Fac_Mth_Loo": "Fac_Mth_L_Out", "Fac_Mth_ooL": "Fac_Mth_L_In",
        "Fac_Mth_oo_RDown": "Fac_Mth_R_Down", "Fac_Mth_LDown_oo": "Fac_Mth_L_Down",
        "Fac_Mth_LUp_oo": "Fac_Mth_L_Up",
        "Fac_Eye_Open_L": "Fac_Eye_L_Open",
        "Fac_Eye_LowEyeUP": "Fac_Eye_LowlidUp",
        "Fac_Mth_Laugh1": "Fac_Mth_Laugh",
        "EB_↑": "Fac_Ebr_Up", "EB_↓": "Fac_Ebr_Down",
        "EB_Angry": "Fac_Ebr_Angry", "EB_Relax": "Fac_Ebr_Relax",
        "EB_困扰": "Fac_Ebr_Sad",
        "Fac_Eyebrow_↓": "Fac_Ebr_Down", "Fac_Eyebrow_Angry": "Fac_Ebr_Angry",
        "Fac_Eyebrow_L↑": "Fac_Ebr_L_Up", "Fac_Eyebrow_R↑": "Fac_Ebr_R_Up",
        "Fac_Eyebrow_Relax": "Fac_Ebr_Relax", "Fac_Eyebrow_困扰": "Fac_Ebr_Relax",
        "Eye_↙↘": "Fac_Eye_BLBR", "Eye_Angry": "Fac_Eye_Angry",
        "Eye_Close": "Fac_Eye_Close",
        "Eye_Open_L": "Fac_Eye_L_Open", "Eye_Open_R": "Fac_Eye_R_Open",
        "Eye_Wink_L": "Fac_Eye_L_Wink", "Eye_Wink_R": "Fac_Eye_R_Wink",
        "EYE_Wink_L": "Fac_Eye_L_Wink", "EYE_Wink_R": "Fac_Eye_R_Wink",
        "Eye_半闭": "Fac_Eye_HalfClose", "Eye_困扰": "Fac_Eye_Sad",
        "Eye_认真": "Fac_Eye_MidDown", "Eye_下眼睑↑": "Fac_Eye_LowlidUp",
        "Mouth_△": "Fac_Mth_Triangle", "Mouth_↑": "Fac_Mth_Up",
        "Mouth_→": "Fac_Mth_Left", "Mouth_↓": "Fac_Mth_Down", "Mouth_←": "Fac_Mth_Right",
        "Mouth_Aa1": "Fac_Mth_Aa1", "Mouth_Aa2": "Fac_Mth_Aa2",
        "Mouth_Aa3Shout": "Fac_Mth_Aa3Shout", "Mouth_AaTalk": "Fac_Mth_AaTalk",
        "Mouth_Ee": "Fac_Mth_Ee", "Mouth_Ii": "Fac_Mth_Ii",
        "Mouth_Uu_Ben": "Fac_Mth_Uu", "Mouth_Laugh": "Fac_Mth_Laugh",
        "Mouth_Laugh2": "Fac_Mth_Laugh2",
        "Mouth_oo←": "Fac_Mth_L_In", "Mouth_↖oo": "Fac_Mth_L_Up",
        "Mouth_←oo": "Fac_Mth_R_Out", "Mouth_↙oo": "Fac_Mth_R_Down",
        "Mouth_→oo": "Fac_Mth_R_In", "Mouth_oo↗": "Fac_Mth_R_Up",
        "Mouth_oo→": "Fac_Mth_L_Out", "Mouth_oo↘": "Fac_Mth_L_Down",
        "Mouth_Oo": "Fac_Mth_Oo", "Mouth_Uu": "Fac_Mth_Uu", "Mouth_UuOo": "Fac_Mth_UuOo",
    }
    for key in rename_map.keys():
        try:
            keyblock[key].name = rename_map[key]
        except Exception:
            for sk in keyblock:
                if key in sk.name:
                    sk.name = rename_map[key]
    for sk in keyblock:
        if sk.name.endswith("_Ben"):
            sk.name = sk.name[:-4]


def find_armature_and_head(mesh_obj):
    armature = None
    if mesh_obj:
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
        raise Exception("No armature found to attach the face rig to.")

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
    if head_name is None and len(armature.data.bones) > 0:
        head_name = armature.data.bones[0].name
    return armature, head_name


def find_eyebrow_bones(armature):
    out = []
    for b in armature.data.bones:
        low = b.name.strip().lower()
        if low.startswith("ctrl-") or low.startswith("face-root") or low.startswith("mch-") or low.startswith("def-") or low.startswith("org-"):
            continue
        if low.startswith("skneyebrow_") or "eyebrow" in low or (low.startswith("ctr_") and "hair" not in low and "eyebrow" in low):
            out.append(b.name)
        elif (low.startswith("ebr_") or low.startswith("ebr ")) and low.endswith("bone"):
            out.append(b.name)
    return out


def find_mouth_bones(armature):
    out = []
    for b in armature.data.bones:
        low = b.name.strip().lower()
        if low.startswith("ctrl-") or low.startswith("face-root") or low.startswith("mch-") or low.startswith("def-") or low.startswith("org-"):
            continue
        if any(k in low for k in ["skn_l_mouth", "skn_r_mouth", "skn_m_mouth", "bdymouth", "bdy_m_mouth", "ptmouth", "pt_m_mouth", "bn_mouthcontrol", "mouth_a", "mouth_b", "mouth_c", "ctr_up_teeth", "ctr_down_teeth"]):
            out.append(b.name)
    return out


def find_extra_face_bones(armature):
    out = []
    for b in armature.data.bones:
        low = b.name.strip().lower()
        if low.startswith("ctrl-") or low.startswith("face-root") or low.startswith("mch-") or low.startswith("def-") or low.startswith("org-"):
            continue
        if any(k in low for k in ["highlight", "remimk", "facemark", "face_mark", "mole", "tear"]):
            out.append(b.name)
    return out


def build_mouth_bone_controls(armature, fwd, up, right, face_size):
    controls = []
    mouth_bones = find_mouth_bones(armature)
    if not mouth_bones:
        return controls

    positions = [armature.matrix_world @ armature.data.bones[bn].head_local for bn in mouth_bones]
    center = sum(positions, Vector((0.0, 0.0, 0.0))) / len(positions)
    master_name = 'CTRL-Mouth_Master'
    controls.append({
        'name': master_name,
        'collection': FACERIG_COLLECTION,
        'color': COL_MOUTH,
        'group': 'Face Mouth',
        'head': center + fwd * (face_size * 0.15),
        'widget': 'lipsmaster',
        'lim': face_size * TRAVEL_F,
        'free': ('X', 'Y', 'Z'),
        'range': 'both',
        'shape_scale': Vector((face_size * 0.08,) * 3),
        'kind': 'master',
        'drivers': []
    })

    for bn in mouth_bones:
        head_world = armature.matrix_world @ armature.data.bones[bn].head_local
        front = center + (head_world - center) * 0.85 + fwd * (face_size * 0.12)
        ctrl_name = 'CTRL-' + bn.strip().replace(' ', '_')
        low = bn.lower()
        if '_l' in low or '.l' in low:
            wgt = 'lip00.L'
        elif '_r' in low or '.r' in low:
            wgt = 'lip00.R'
        else:
            wgt = 'eyeblink'
        controls.append({
            'name': ctrl_name,
            'collection': FACERIG_COLLECTION,
            'color': COL_CORNER,
            'group': 'Face Mouth',
            'head': front,
            'widget': wgt,
            'lim': face_size * TRAVEL_F,
            'free': ('X', 'Y', 'Z'),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.035,) * 3),
            'kind': 'fk',
            'target_bone': bn,
            'parent': master_name,
            'hook_name': ctrl_name + '_Hook',
            'hook_head': head_world,
            'drivers': []
        })
    return controls


def build_extra_face_bone_controls(armature, fwd, up, right, face_size):
    controls = []
    extra_bones = find_extra_face_bones(armature)
    for bn in extra_bones:
        head_world = armature.matrix_world @ armature.data.bones[bn].head_local
        front = head_world + fwd * (face_size * 0.10)
        ctrl_name = 'CTRL-' + bn.strip().replace(' ', '_')
        controls.append({
            'name': ctrl_name,
            'collection': FACERIG_COLLECTION,
            'color': COL_EYEAIM,
            'group': 'Face Extra',
            'head': front,
            'widget': 'ring' if 'highlight' in bn.lower() else 'diamond',
            'lim': face_size * TRAVEL_F,
            'free': ('X', 'Y', 'Z'),
            'range': 'both',
            'shape_scale': Vector((face_size * 0.030,) * 3),
            'kind': 'fk',
            'target_bone': bn,
            'hook_name': ctrl_name + '_Hook',
            'hook_head': head_world,
            'drivers': []
        })
    return controls


def eyebrow_side(name):
    low = name.strip().lower()
    if low.endswith(".r") or low.endswith("_r") or "_r_" in low or "_r " in low or ".r " in low:
        return 'R'
    if low.endswith(".l") or low.endswith("_l") or "_l_" in low or "_l " in low or ".l " in low:
        return 'L'
    return 'C'


def is_eyebrow_key(name):
    low = name.strip().lower()
    return (low.startswith("fac_ebr_") or low.startswith("ebr_")
            or low.startswith("ebr ") or "_ebr_" in low or "eyebrow" in low)


def skneyebrow_pos(armature, seg, side):
    for b in armature.data.bones:
        low = b.name.strip().lower()
        if ("skneyebrow_" + seg) in low or ("eyebrow_" + seg) in low:
            if eyebrow_side(b.name) == side:
                return armature.matrix_world @ b.head_local
    return None


def build_brow_shapekey_controls(mesh_obj, armature, fwd, up, face_size):
    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return []
    kb = mesh_obj.data.shape_keys.key_blocks
    right = up.cross(fwd).normalized()
    OFFSET = face_size * OFFSET_F

    def place_s(feature, h=0.0, v=0.0):
        return feature + fwd * OFFSET + right * h + up * v

    ebkeys = [sk.name for sk in kb if is_eyebrow_key(sk.name)]

    out = []

    brow_c = feature_centroid(mesh_obj, ebkeys)
    seg_positions = [skneyebrow_pos(armature, s, sd)
                     for s in ("01", "02", "03") for sd in ("L", "R")]
    seg_positions = [p for p in seg_positions if p is not None]
    if brow_c is None and seg_positions:
        brow_c = sum(seg_positions, Vector()) / len(seg_positions)
    if brow_c is None:
        bb = [mesh_obj.matrix_world @ Vector(c) for c in mesh_obj.bound_box]
        brow_c = sum(bb, Vector()) / len(bb) + up * face_size * 0.12

    eyeL = feature_centroid(mesh_obj, ["Fac_Eye_L_Wink", "Fac_Eye_L_Open"])\
           or feature_centroid(mesh_obj, ["Fac_Eye_Close"], side='L')
    eyeR = feature_centroid(mesh_obj, ["Fac_Eye_R_Wink", "Fac_Eye_R_Open"])\
           or feature_centroid(mesh_obj, ["Fac_Eye_Close"], side='R')
    if eyeL is not None and eyeR is not None:
        eyeC = (eyeL + eyeR) * 0.5
    else:
        eyeC = brow_c

    kbnames = {sk.name for sk in kb}

    perside = any(("Fac_Ebr_%s_%s" % (s, k)) in kbnames
                  for s in ("L", "R") for k in ("Angry", "Down", "Sad"))
    if perside:
        for side, xoff in (('R', 1.0), ('L', -1.0)):
            lr = ("Fac_Ebr_%s_Sad" % side, "Fac_Ebr_%s_Angry" % side) if FLIP_HORIZONTAL \
                else ("Fac_Ebr_%s_Angry" % side, "Fac_Ebr_%s_Sad" % side)
            drv = []
            if ("Fac_Ebr_%s_Up" % side) in kbnames:
                drv.append({'key': "Fac_Ebr_%s_Up" % side, 'axis': 'Z', 'dir': +1})
            if ("Fac_Ebr_%s_Down" % side) in kbnames:
                drv.append({'key': "Fac_Ebr_%s_Down" % side, 'axis': 'Z', 'dir': -1})
            if lr[0] in kbnames:
                drv.append({'key': lr[0], 'axis': 'X', 'dir': +1})
            if lr[1] in kbnames:
                drv.append({'key': lr[1], 'axis': 'X', 'dir': -1})
            if drv:
                out.append({'name': 'CTRL-Eyebrow-Viseme-Pad.%s' % side,
                            'collection': FACERIG_COLLECTION, 'color': COL_EBRMASTER,
                            'group': 'Face Eyebrow',
                            'head': place_s(brow_c, h=xoff * face_size * 0.06),
                            'widget': 'pad', 'lim': face_size * EMOTE_LIM_F,
                            'free': ('X', 'Z'), 'range': 'both',
                            'shape_scale': Vector((face_size * 0.09, 1.0, face_size * 0.025)),
                            'shape_rotation': (0.0, -0.15 if side == 'L' else 0.15,
                                               0.43825 if side == 'L' else -0.43825),
                            'drivers': drv})
            relaxk = "Fac_Ebr_%s_Relax" % side
            if relaxk in kbnames:
                if side == 'L':
                    brow_range = 'neg'
                    brow_dir = -1
                else:
                    brow_range = 'pos'
                    brow_dir = +1
                out.append({'name': 'CTRL-Brow-%s_Up' % side,
                            'collection': FACERIG_COLLECTION, 'color': COL_BROW,
                            'group': 'Face Eyebrow',
                            'head': place_s(brow_c, h=xoff * face_size * 0.03),
                            'widget': 'eyeblink', 'lim': face_size * EMOTE_LIM_F,
                            'free': ('X',), 'range': brow_range,
                            'shape_scale': Vector((face_size * 0.028, face_size * 0.05, face_size * 0.028)),
                            'drivers': [{'key': relaxk, 'axis': 'X', 'dir': brow_dir}]})
        return out

    ebr_lr = ("Fac_Ebr_Angry", "Fac_Ebr_Sad") if FLIP_HORIZONTAL else ("Fac_Ebr_Sad", "Fac_Ebr_Angry")
    ebr_drv = []
    if "Fac_Ebr_Relax" in kbnames: ebr_drv.append({'key': "Fac_Ebr_Relax", 'axis': 'Z', 'dir': +1})
    if "Fac_Ebr_Down" in kbnames: ebr_drv.append({'key': "Fac_Ebr_Down", 'axis': 'Z', 'dir': -1})
    if ebr_lr[0] in kbnames: ebr_drv.append({'key': ebr_lr[0], 'axis': 'X', 'dir': +1})
    if ebr_lr[1] in kbnames: ebr_drv.append({'key': ebr_lr[1], 'axis': 'X', 'dir': -1})
    if ebr_drv:
        out.append({'name': 'CTRL-Eyebrow-Viseme-Pad',
                    'collection': FACERIG_COLLECTION, 'color': COL_EBRMASTER,
                    'group': 'Face Eyebrow', 'head': place_s(eyeC), 'widget': 'eyeblink',
                    'lim': face_size * EMOTE_LIM_F, 'free': ('X', 'Z'), 'range': 'both',
                    'shape_scale': Vector((face_size * 0.0455, face_size * 0.05, face_size * 0.0416)),
                    'drivers': ebr_drv})

    for side, xoff in (('R', -1.0), ('L', 1.0)):
        key = "Fac_Ebr_%s_Up" % side
        if key in kbnames:
            if side == 'L':
                brow_range = 'neg'
                brow_dir = -1
            else:
                brow_range = 'pos'
                brow_dir = +1
            out.append({'name': 'CTRL-Brow-%s_Up' % side,
                        'collection': FACERIG_COLLECTION, 'color': COL_BROW,
                        'group': 'Face Eyebrow',
                        'head': place_s(eyeC, h=xoff * face_size * 0.03), 'widget': 'eyeblink',
                        'lim': face_size * EMOTE_LIM_F, 'free': ('X',), 'range': brow_range,
                        'shape_scale': Vector((face_size * 0.028, face_size * 0.05, face_size * 0.028)),
                        'drivers': [{'key': key, 'axis': 'X', 'dir': brow_dir}]})
    return out


def feature_centroid(mesh_obj, key_names, side=None):
    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return None
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

    if side in ('L', 'R'):
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


def feature_extent(mesh_obj, key_names, right, up):
    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return None
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
    deltas = [(key.data[i].co - basis.data[i].co).length for i in range(n)]
    maxd = max(deltas) if deltas else 0.0
    if maxd <= 1e-9:
        return None
    thr = maxd * 0.30
    mw = mesh_obj.matrix_world
    pts = [mw @ basis.data[i].co for i in range(n) if deltas[i] >= thr]
    if not pts:
        return None
    rs = [p.dot(right) for p in pts]
    us = [p.dot(up) for p in pts]
    return (max(rs) - min(rs), max(us) - min(us))


def feature_extreme(mesh_obj, key_names, axis):
    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return None
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
    deltas = [(key.data[i].co - basis.data[i].co).length for i in range(n)]
    maxd = max(deltas) if deltas else 0.0
    if maxd <= 1e-9:
        return None
    thr = maxd * 0.30
    mw = mesh_obj.matrix_world
    pts = [mw @ basis.data[i].co for i in range(n) if deltas[i] >= thr]
    if not pts:
        return None
    pmax = max(pts, key=lambda p: p.dot(axis))
    pmin = min(pts, key=lambda p: p.dot(axis))
    return (pmax, pmin)


def face_frame(mesh_obj, armature=None):
    mw = mesh_obj.matrix_world
    fwd = Vector((0.0, -1.0, 0.0))
    right = Vector((1.0, 0.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))

    face_size = 0.20
    if armature:
        eb_L = armature.data.bones.get("eye.L") or armature.data.bones.get("DEF-eye.L") or armature.data.bones.get("Skn_L_Eye")
        eb_R = armature.data.bones.get("eye.R") or armature.data.bones.get("DEF-eye.R") or armature.data.bones.get("Skn_R_Eye")
        if eb_L and eb_R:
            sep = (eb_L.head_local - eb_R.head_local).length
            if 0.01 < sep < 0.3:
                face_size = sep * 3.5
        else:
            head_b = armature.data.bones.get("Head") or armature.data.bones.get("head") or armature.data.bones.get("spine.006")
            if head_b and 0.05 < head_b.length < 0.5:
                face_size = head_b.length * 1.2
    else:
        corners = [mw @ Vector(c) for c in mesh_obj.bound_box]
        mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        bb_size = (mx - mn).length
        if 0.05 < bb_size < 0.45:
            face_size = bb_size

    if face_size < 1e-4 or face_size > 0.35:
        face_size = 0.20
    return fwd, right, up, face_size


def plan_controls(mesh_obj, fwd, right, up, face_size):
    if not mesh_obj or not mesh_obj.data or not mesh_obj.data.shape_keys:
        return []
    keyblock = mesh_obj.data.shape_keys.key_blocks
    OFFSET  = face_size * OFFSET_F
    LIM     = face_size * TRAVEL_F
    SPACING = face_size * SPACING_F

    def place(feature, h=0.0, v=0.0):
        return feature + fwd * OFFSET + right * h + up * v

    def hkey(pos, neg):
        return (pos, neg) if not FLIP_HORIZONTAL else (neg, pos)

    def vkey(pos, neg):
        return (pos, neg) if not FLIP_VERTICAL else (neg, pos)

    controls = []

    MOUTH_KEYS = ["Fac_Mth_Ii", "Fac_Mth_Ee", "Fac_Mth_Triangle",
                  "Fac_Mth_Left", "Fac_Mth_Right", "Fac_Mth_Up", "Fac_Mth_Down",
                  "Fac_Mth_L_Up", "Fac_Mth_R_Up", "Fac_Mth_L_Out", "Fac_Mth_R_Out",
                  "Fac_Mth_L_In", "Fac_Mth_R_In", "Fac_Mth_Aa1", "Fac_Mth_AaTalk"]

    mouth = feature_centroid(mesh_obj, MOUTH_KEYS)
    eyeL = feature_centroid(mesh_obj, ["Fac_Eye_L_Wink", "Fac_Eye_L_Open"])\
           or feature_centroid(mesh_obj, ["Fac_Eye_Close"], side='L')
    eyeR = feature_centroid(mesh_obj, ["Fac_Eye_R_Wink", "Fac_Eye_R_Open"])\
           or feature_centroid(mesh_obj, ["Fac_Eye_Close"], side='R')
    brow = feature_centroid(mesh_obj, ["Fac_Ebr_Up", "Fac_Ebr_Down", "Fac_Ebr_Angry"]
                            + [sk.name for sk in keyblock if is_eyebrow_key(sk.name)])

    fcx = mesh_obj.matrix_world @ (0.125 * sum((Vector(c) for c in mesh_obj.bound_box), Vector()))
    if mouth is None:
        mouth = fcx - up * face_size * 0.12
    if eyeL is None:
        eyeL = fcx + up * face_size * 0.10 + right * face_size * 0.10
    if eyeR is None:
        eyeR = fcx + up * face_size * 0.10 - right * face_size * 0.10
    if brow is None:
        brow = ((eyeL + eyeR) * 0.5) + up * face_size * 0.10
    eyeC = (eyeL + eyeR) * 0.5

    mouth_raise = up * (face_size * MOUTH_RAISE_F)
    mouth = mouth + mouth_raise

    mouth_edges = feature_extreme(mesh_obj, MOUTH_KEYS, right)

    def corner(side):
        cc = feature_centroid(mesh_obj,
            ["Fac_Mth_%s_Up" % side, "Fac_Mth_%s_Down" % side,
             "Fac_Mth_%s_Out" % side, "Fac_Mth_%s_In" % side])
        if mouth_edges is not None:
            pmax, pmin = mouth_edges
            if cc is not None:
                return pmax if (pmax - cc).length <= (pmin - cc).length else pmin
            return pmax if (side == 'L') != FLIP_EYE_LR else pmin
        if cc is not None:
            return cc
        s = 1.0 if (side == 'L') != FLIP_EYE_LR else -1.0
        return mouth + right * (s * face_size * 0.06)

    mouth_ext = feature_extent(mesh_obj, MOUTH_KEYS, right, up)
    if mouth_ext:
        mw2, mh2 = mouth_ext[0] * 0.5 * MOUTH_SHIFT_F, mouth_ext[1] * 0.5 * MOUTH_SHIFT_F
    else:
        mw2, mh2 = LIM * 0.9, LIM * 0.4
    mouth_scale = Vector((max(mw2, LIM * 0.3), LIM, max(mh2, LIM * 0.18)))
    hl = face_size * EYE_HL_F
    corner_scale = Vector((hl, hl, hl))
    tri = face_size * TRI_F
    tri_scale = Vector((tri, tri, tri))
    emote_scale = Vector((face_size * 0.035, LIM, face_size * 0.032))

    lr = hkey("Fac_Mth_Left", "Fac_Mth_Right")
    ud = vkey("Fac_Mth_Up", "Fac_Mth_Down")
    drv = []
    if lr[0] in keyblock: drv.append({'key': lr[0], 'axis': 'X', 'dir': +1})
    if lr[1] in keyblock: drv.append({'key': lr[1], 'axis': 'X', 'dir': -1})
    if ud[0] in keyblock: drv.append({'key': ud[0], 'axis': 'Z', 'dir': +1})
    if ud[1] in keyblock: drv.append({'key': ud[1], 'axis': 'Z', 'dir': -1})
    if drv:
        controls.append({'name': 'CTRL-Mouth-Shift', 'collection': 'Face Main',
                         'color': COL_VISEME, 'group': 'Face Mouth',
                         'head': place(mouth), 'widget': 'lipsmaster', 'lim': LIM,
                         'free': ('X', 'Z'), 'range': 'both', 'shape_scale': Vector((face_size * 0.09,) * 3),
                         'drivers': drv})

    vud = vkey("Fac_Mth_Ii", "Fac_Mth_Aa1")
    vdrv = []
    right_dir = +1 if FLIP_HORIZONTAL else -1
    left_dir = -1 if FLIP_HORIZONTAL else +1
    for k in ("Fac_Mth_L_In", "Fac_Mth_R_In"):
        if k in keyblock: vdrv.append({'key': k, 'axis': 'X', 'dir': right_dir})
    for k in ("Fac_Mth_L_Out", "Fac_Mth_R_Out"):
        if k in keyblock: vdrv.append({'key': k, 'axis': 'X', 'dir': left_dir})
    if vud[0] in keyblock: vdrv.append({'key': vud[0], 'axis': 'Z', 'dir': +1})
    if vud[1] in keyblock: vdrv.append({'key': vud[1], 'axis': 'Z', 'dir': -1, 'gain': 0.5})
    if vdrv:
        controls.append({'name': 'CTRL-Mouth-Viseme-Pad', 'collection': 'Face Main',
                         'color': COL_MOUTH, 'group': 'Face Visemes',
                         'head': place(mouth), 'widget': 'pad', 'lim': LIM,
                         'free': ('X', 'Z'), 'range': 'both',
                         'shape_scale': mouth_scale * 1.25,
                         'drivers': vdrv})

    for side in ('L', 'R'):
        out_name = "Fac_Mth_%s_Out" % side
        in_name = "Fac_Mth_%s_In" % side
        if side == 'R':
            outk = hkey(in_name, out_name)
        else:
            outk = hkey(out_name, in_name)
        udk = vkey("Fac_Mth_%s_Up" % side, "Fac_Mth_%s_Down" % side)
        drv = []
        if outk[0] in keyblock: drv.append({'key': outk[0], 'axis': 'X', 'dir': +1})
        if outk[1] in keyblock: drv.append({'key': outk[1], 'axis': 'X', 'dir': -1})
        if udk[0] in keyblock:  drv.append({'key': udk[0], 'axis': 'Z', 'dir': +1})
        if udk[1] in keyblock:  drv.append({'key': udk[1], 'axis': 'Z', 'dir': -1})
        if drv:
            controls.append({'name': 'CTRL-Mouth-Corner.%s' % side,
                             'collection': 'Face Main', 'color': COL_MOUTH,
                             'group': 'Face Corner', 'head': place(corner(side) + mouth_raise),
                             'widget': 'lip00.%s' % side, 'lim': LIM, 'free': ('X', 'Z'),
                             'range': 'both', 'shape_scale': corner_scale,
                             'drivers': drv})

    visemes = [k for k in ["Fac_Mth_Aa1", "Fac_Mth_Aa2", "Fac_Mth_Aa3Shout",
               "Fac_Mth_AaTalk", "Fac_Mth_Ee", "Fac_Mth_Ii", "Fac_Mth_Oo",
               "Fac_Mth_Uu", "Fac_Mth_UuOo", "Fac_Mth_Laugh", "Fac_Mth_Laugh2",
               "Fac_Mth_Triangle"] if k in keyblock]
    if visemes:
        n = len(visemes)
        for i, k in enumerate(visemes):
            h = (i - (n - 1) / 2.0) * SPACING
            controls.append({'name': 'CTRL-%s' % k[4:], 'collection': 'Face Visemes',
                             'color': COL_VISEME, 'group': 'Face Visemes',
                             'head': place(mouth, h=h, v=-face_size * 0.16),
                             'widget': 'eyeblink', 'lim': LIM, 'free': ('Z',),
                             'range': 'pos', 'shape_scale': Vector((face_size * 0.045,) * 3),
                             'drivers': [{'key': k, 'axis': 'Z', 'dir': +1}]})

    for side, pos in (('L', eyeL), ('R', eyeR)):
        openk = "Fac_Eye_%s_Open" % side
        winkk = "Fac_Eye_%s_Wink" % side
        if openk in keyblock:
            controls.append({'name': 'CTRL-Eye_Open.%s' % side,
                             'collection': 'Face Main', 'color': COL_EYELID,
                             'group': 'Face Eyelid',
                             'head': place(pos, v=face_size * 0.055),
                             'widget': 'isaac_blink_top', 'lim': LIM, 'free': ('Z',),
                             'range': 'pos', 'shape_scale': tri_scale,
                             'drivers': [{'key': openk, 'axis': 'Z', 'dir': +1}]})
        if winkk in keyblock:
            wdrv = [{'key': winkk, 'axis': 'Z', 'dir': -1}]
            if "Fac_Eye_Angry" in keyblock:
                wdrv.append({'key': "Fac_Eye_Angry", 'axis': 'Z', 'dir': +1})
            controls.append({'name': 'CTRL-Eye_Wink.%s' % side,
                             'collection': 'Face Main', 'color': COL_EYELID,
                             'group': 'Face Eyelid',
                             'head': place(pos, v=-face_size * 0.06),
                             'widget': 'isaac_blink_bot', 'lim': LIM, 'free': ('Z',),
                             'range': 'both', 'shape_scale': tri_scale,
                             'drivers': wdrv})

    lr = hkey("Eye_Left", "Eye_Right")
    ud = vkey("Eye_Up", "Eye_Down")
    drv = []
    if lr[0] in keyblock: drv.append({'key': lr[0], 'axis': 'X', 'dir': +1})
    if lr[1] in keyblock: drv.append({'key': lr[1], 'axis': 'X', 'dir': -1})
    if ud[0] in keyblock: drv.append({'key': ud[0], 'axis': 'Z', 'dir': +1})
    if ud[1] in keyblock: drv.append({'key': ud[1], 'axis': 'Z', 'dir': -1})
    if drv:
        controls.append({'name': 'CTRL-Eye-Aim', 'collection': 'Face Main',
                         'color': COL_EYEAIM, 'group': 'Face Eye-Aim',
                         'head': place(eyeC, v=face_size * 0.02), 'widget': 'ring',
                         'lim': LIM, 'free': ('X', 'Z'), 'range': 'both', 'drivers': drv})

    emote_lim = face_size * EMOTE_LIM_F
    emote_spacing = face_size * EMOTE_SPACING_F
    emote_fwd = fwd * (face_size * EMOTE_FWD_F)
    eye_pad_lr = hkey("Fac_Eye_MidDown", "Fac_Eye_LowlidUp")
    eye_pad_drv = []
    if "Fac_Eye_Close" in keyblock: eye_pad_drv.append({'key': "Fac_Eye_Close", 'axis': 'Z', 'dir': +1})
    if "Fac_Eye_HalfClose" in keyblock: eye_pad_drv.append({'key': "Fac_Eye_HalfClose", 'axis': 'Z', 'dir': -1})
    if eye_pad_lr[0] in keyblock: eye_pad_drv.append({'key': eye_pad_lr[0], 'axis': 'X', 'dir': +1})
    if eye_pad_lr[1] in keyblock: eye_pad_drv.append({'key': eye_pad_lr[1], 'axis': 'X', 'dir': -1})
    if eye_pad_drv:
        controls.append({'name': 'CTRL-Eye-Viseme-Pad', 'collection': 'Face Eyes',
                         'color': COL_EYEMOTE, 'group': 'Face Eye-Emote',
                         'head': place(eyeC) + emote_fwd, 'widget': 'eyeblink',
                         'lim': emote_lim, 'free': ('X', 'Z'), 'range': 'both',
                         'shape_scale': emote_scale * 1.3, 'drivers': eye_pad_drv})
    if "Fac_Eye_MidUp" in keyblock:
        controls.append({'name': 'CTRL-Eye_MidUp', 'collection': 'Face Eyes',
                         'color': COL_EYEMOTE, 'group': 'Face Eye-Emote',
                         'head': place(eyeC, v=emote_spacing) + emote_fwd, 'widget': 'eyeblink',
                         'lim': emote_lim, 'free': ('Z',), 'range': 'both',
                         'shape_scale': emote_scale,
                         'drivers': [{'key': "Fac_Eye_MidUp", 'axis': 'Z', 'dir': +1}]})
    if "Fac_Eye_Sad" in keyblock:
        controls.append({'name': 'CTRL-Eye_Sad', 'collection': 'Face Eyes',
                         'color': COL_EYEMOTE, 'group': 'Face Eye-Emote',
                         'head': place(eyeC, v=-emote_spacing) + emote_fwd, 'widget': 'eyeblink',
                         'lim': emote_lim, 'free': ('Z',), 'range': 'pos',
                         'shape_scale': emote_scale,
                         'drivers': [{'key': "Fac_Eye_Sad", 'axis': 'Z', 'dir': +1}]})
    if "O_O" in keyblock:
        controls.append({'name': 'CTRL-O_O', 'collection': 'Face Eyes',
                         'color': COL_EYEMOTE, 'group': 'Face Eye-Emote',
                         'head': place(eyeC, h=face_size * 0.14) + emote_fwd, 'widget': 'eyeblink',
                         'lim': emote_lim, 'free': ('Z',), 'range': 'pos',
                         'shape_scale': emote_scale,
                         'drivers': [{'key': "O_O", 'axis': 'Z', 'dir': +1}]})

    for c in controls:
        c['collection'] = FACERIG_COLLECTION
    return controls


def get_widget_collection():
    for name_candidate in ("WGTS", "wgt"):
        coll = bpy.data.collections.get(name_candidate)
        if coll:
            return coll

    for c in bpy.data.collections:
        c_low = c.name.lower()
        if "wgts" in c_low or "wgt" in c_low:
            return c

    coll = bpy.data.collections.get("WGTS")
    if not coll:
        coll = bpy.data.collections.new("WGTS")
    return coll


def finalize_widget_collection(wgt_coll):
    if not wgt_coll:
        return

    try:
        wgt_coll.hide_viewport = True
    except Exception:
        pass

    main_wgts = None
    for name_candidate in ("WGTS", "wgt"):
        c = bpy.data.collections.get(name_candidate)
        if c and c != wgt_coll:
            main_wgts = c
            break

    if main_wgts:
        if wgt_coll.name not in main_wgts.children:
            try:
                main_wgts.children.link(wgt_coll)
            except Exception:
                pass
        if wgt_coll.name in bpy.context.scene.collection.children:
            try:
                bpy.context.scene.collection.children.unlink(wgt_coll)
            except Exception:
                pass
    else:
        if wgt_coll.name in bpy.context.scene.collection.children:
            try:
                bpy.context.scene.collection.children.unlink(wgt_coll)
            except Exception:
                pass


EYE_MASTER_VERTS = [[-0.40348, 0.0, 0.32632], [-0.28803, 0.0, 0.29715], [-0.21194, 0.0, 0.24992], [0.0, 0.0, -0.19968], [0.0, 0.0, 0.19968], [-0.21194, 0.0, -0.24992], [-0.28803, 0.0, -0.29715], [-0.40348, 0.0, -0.32632], [-0.53133, 0.0, -0.31136], [-0.64684, 0.0, -0.24534], [-0.72806, 0.0, -0.13551], [-0.7574, 0.0, 0.0], [-0.72806, 0.0, 0.13551], [-0.64684, 0.0, 0.24534], [-0.53133, 0.0, 0.31136], [-0.11372, 0.0, 0.1995], [-0.11372, 0.0, -0.1995], [-0.03778, 0.0, -0.19971], [-0.03778, 0.0, 0.19971], [-0.16207, 0.0, 0.20723], [-0.16207, 0.0, -0.20723], [-0.34203, 0.0, 0.3157], [-0.24529, 0.0, 0.2746], [-0.0037, 0.0, -0.19969], [-0.07706, 0.0, 0.1997], [-0.24529, 0.0, -0.2746], [-0.34203, 0.0, -0.3157], [-0.4676, 0.0, -0.32523], [-0.59202, 0.0, -0.28451], [-0.693, 0.0, -0.19498], [-0.74991, 0.0, -0.06945], [-0.74991, 0.0, 0.06945], [-0.693, 0.0, 0.19498], [-0.59202, 0.0, 0.28451], [-0.4676, 0.0, 0.32523], [-0.18492, 0.0, 0.22542], [-0.07706, 0.0, -0.1997], [-0.0037, 0.0, 0.19969], [-0.14053, 0.0, -0.20011], [-0.14053, 0.0, 0.20011], [-0.18492, 0.0, -0.22542], [0.40348, 0.0, 0.32632], [0.28803, 0.0, 0.29715], [0.21194, 0.0, 0.24992], [-0.0, 0.0, -0.19968], [-0.0, 0.0, 0.19968], [0.21194, 0.0, -0.24992], [0.28803, 0.0, -0.29715], [0.40348, 0.0, -0.32632], [0.53133, 0.0, -0.31136], [0.64684, 0.0, -0.24534], [0.72806, 0.0, -0.13551], [0.7574, 0.0, 0.0], [0.72806, 0.0, 0.13551], [0.64684, 0.0, 0.24534], [0.53133, 0.0, 0.31136], [0.11372, 0.0, 0.1995], [0.11372, 0.0, -0.1995], [0.03778, 0.0, -0.19971], [0.03778, 0.0, 0.19971], [0.16207, 0.0, 0.20723], [0.16207, 0.0, -0.20723], [0.34203, 0.0, 0.3157], [0.24529, 0.0, 0.2746], [0.0037, 0.0, -0.19969], [0.07706, 0.0, 0.1997], [0.24529, 0.0, -0.2746], [0.34203, 0.0, -0.3157], [0.4676, 0.0, -0.32523], [0.59202, 0.0, -0.28451], [0.693, 0.0, -0.19498], [0.74991, 0.0, -0.06945], [0.74991, 0.0, 0.06945], [0.693, 0.0, 0.19498], [0.59202, 0.0, 0.28451], [0.4676, 0.0, 0.32523], [0.18492, 0.0, 0.22542], [0.07706, 0.0, -0.1997], [0.0037, 0.0, 0.19969], [0.14053, 0.0, -0.20011], [0.14053, 0.0, 0.20011], [0.18492, 0.0, -0.22542]]
EYE_MASTER_EDGES = [[1, 21], [0, 21], [2, 22], [1, 22], [17, 23], [3, 23], [18, 24], [15, 24], [6, 25], [5, 25], [7, 26], [6, 26], [8, 27], [7, 27], [9, 28], [8, 28], [10, 29], [9, 29], [11, 30], [10, 30], [12, 31], [11, 31], [13, 32], [12, 32], [14, 33], [13, 33], [0, 34], [14, 34], [19, 35], [2, 35], [16, 36], [17, 36], [4, 37], [18, 37], [20, 38], [16, 38], [15, 39], [19, 39], [5, 40], [20, 40], [42, 62], [41, 62], [43, 63], [42, 63], [58, 64], [44, 64], [59, 65], [56, 65], [47, 66], [46, 66], [48, 67], [47, 67], [49, 68], [48, 68], [50, 69], [49, 69], [51, 70], [50, 70], [52, 71], [51, 71], [53, 72], [52, 72], [54, 73], [53, 73], [55, 74], [54, 74], [41, 75], [55, 75], [60, 76], [43, 76], [57, 77], [58, 77], [45, 78], [59, 78], [61, 79], [57, 79], [56, 80], [60, 80], [46, 81], [61, 81]]
EYE_CIRCLE_VERTS = [[0.0, 0.0, 0.5], [-0.09755, 0.0, 0.49039], [-0.19134, 0.0, 0.46194], [-0.27779, 0.0, 0.41574], [-0.35355, 0.0, 0.35355], [-0.41574, 0.0, 0.27779], [-0.46194, 0.0, 0.19134], [-0.49039, 0.0, 0.09755], [-0.5, 0.0, -0.0], [-0.49039, 0.0, -0.09755], [-0.46194, 0.0, -0.19134], [-0.41574, 0.0, -0.27779], [-0.35355, 0.0, -0.35355], [-0.27779, 0.0, -0.41574], [-0.19134, 0.0, -0.46194], [-0.09755, 0.0, -0.49039], [0.0, 0.0, -0.5], [0.09755, 0.0, -0.49039], [0.19134, 0.0, -0.46194], [0.27779, 0.0, -0.41574], [0.35355, 0.0, -0.35355], [0.41574, 0.0, -0.27779], [0.46194, 0.0, -0.19134], [0.49039, 0.0, -0.09755], [0.5, 0.0, 0.0], [0.49039, 0.0, 0.09755], [0.46194, 0.0, 0.19134], [0.41573, 0.0, 0.27779], [0.35355, 0.0, 0.35355], [0.27779, 0.0, 0.41574], [0.19134, 0.0, 0.46194], [0.09754, 0.0, 0.49039]]
EYE_CIRCLE_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [25, 26], [26, 27], [27, 28], [28, 29], [29, 30], [30, 31], [0, 31]]

LIPS_MASTER_VERTS = [[0.0, 0.19233, 0.11033], [0.13499, 0.18609, 0.10769], [0.2648, 0.15671, 0.10386], [0.38443, 0.10515, 0.09906], [0.48929, 0.03669, 0.09225], [0.57534, -0.04048, 0.08167], [0.63928, -0.11576, 0.0649], [0.67866, -0.17692, 0.03916], [0.69195, -0.21104, 0.00157], [0.67866, -0.20938, -0.04918], [0.63928, -0.17943, -0.10838], [0.57534, -0.13291, -0.1699], [0.48929, -0.08096, -0.22793], [0.38443, -0.03318, -0.27744], [0.2648, 0.00301, -0.31449], [0.13499, 0.02292, -0.33643], [-0.0, 0.02596, -0.34248], [-0.135, 0.02292, -0.33643], [-0.2648, 0.00301, -0.31449], [-0.38443, -0.03318, -0.27744], [-0.48929, -0.08096, -0.22793], [-0.57534, -0.13291, -0.1699], [-0.63928, -0.17943, -0.10838], [-0.67866, -0.20938, -0.04917], [-0.69195, -0.21104, 0.00157], [-0.67866, -0.17692, 0.03916], [-0.63928, -0.11576, 0.0649], [-0.57534, -0.04048, 0.08167], [-0.48928, 0.03669, 0.09225], [-0.38442, 0.10515, 0.09906], [-0.26479, 0.15671, 0.10386], [-0.13499, 0.1861, 0.10769]]
LIPS_MASTER_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [25, 26], [26, 27], [27, 28], [28, 29], [29, 30], [30, 31], [0, 31]]
EYEBLINK_VERTS = [[-0.42167, 0.0, -0.22917], [0.42167, 0.0, -0.22917], [-0.42167, -0.0, 0.22917], [0.42167, -0.0, 0.22917], [0.46, 0.0, -0.125], [0.46, 0.0, -0.0], [0.46, -0.0, 0.125], [-0.23, 0.0, -0.25], [-0.0, 0.0, -0.25], [0.23, 0.0, -0.25], [-0.46, 0.0, -0.125], [-0.46, -0.0, 0.0], [-0.46, -0.0, 0.125], [-0.23, -0.0, 0.25], [0.0, -0.0, 0.25], [0.23, -0.0, 0.25], [0.4594, -0.0, 0.15592], [0.45521, -0.0, 0.1849], [0.44383, -0.0, 0.20996], [0.2869, 0.0, -0.24968], [0.34021, 0.0, -0.2474], [0.38633, 0.0, -0.24121], [-0.4594, -0.0, 0.15592], [-0.45521, -0.0, 0.1849], [-0.44383, -0.0, 0.20996], [0.2869, -0.0, 0.24968], [0.34021, -0.0, 0.2474], [0.38633, -0.0, 0.24121], [0.44383, 0.0, -0.20996], [0.45521, 0.0, -0.1849], [0.4594, 0.0, -0.15592], [0.46, 0.0, -0.0625], [0.46, -0.0, 0.0625], [-0.38633, 0.0, -0.24121], [-0.34021, 0.0, -0.2474], [-0.2869, 0.0, -0.24967], [-0.115, 0.0, -0.25], [0.115, 0.0, -0.25], [-0.44383, 0.0, -0.20996], [-0.45521, 0.0, -0.1849], [-0.4594, 0.0, -0.15592], [-0.46, 0.0, -0.0625], [-0.46, -0.0, 0.0625], [-0.38633, -0.0, 0.24121], [-0.34021, -0.0, 0.2474], [-0.2869, -0.0, 0.24967], [-0.115, -0.0, 0.25], [0.115, -0.0, 0.25], [-0.39485, -0.00338, -0.20822], [0.39485, 0.00338, -0.20822], [-0.39485, -0.00338, 0.20822], [0.39485, 0.00338, 0.20822], [0.43075, 0.00369, -0.11357], [0.43075, 0.00369, 0.11358], [-0.43075, -0.00369, -0.11357], [-0.43075, -0.00369, 0.11358], [0.43018, 0.00368, 0.14167], [0.42626, 0.00365, 0.168], [0.4156, 0.00356, 0.19077], [0.31857, 0.00273, -0.22478], [0.36176, 0.0031, -0.21916], [-0.43018, -0.00368, 0.14167], [-0.42626, -0.00365, 0.168], [-0.4156, -0.00356, 0.19077], [0.31857, 0.00273, 0.22479], [0.36176, 0.0031, 0.21917], [0.4156, 0.00356, -0.19077], [0.42626, 0.00365, -0.16799], [0.43018, 0.00368, -0.14167], [-0.36176, -0.0031, -0.21916], [-0.31857, -0.00273, -0.22478], [-0.4156, -0.00356, -0.19077], [-0.42626, -0.00365, -0.16799], [-0.43018, -0.00368, -0.14167], [-0.36176, -0.0031, 0.21917], [-0.31857, -0.00273, 0.22479]]
EYEBLINK_EDGES = [[6, 16], [16, 17], [17, 18], [3, 18], [9, 19], [19, 20], [20, 21], [1, 21], [12, 22], [22, 23], [23, 24], [2, 24], [15, 25], [25, 26], [26, 27], [3, 27], [1, 28], [28, 29], [29, 30], [4, 30], [4, 31], [5, 31], [5, 32], [6, 32], [0, 33], [33, 34], [34, 35], [7, 35], [7, 36], [8, 36], [8, 37], [9, 37], [0, 38], [38, 39], [39, 40], [10, 40], [10, 41], [11, 41], [11, 42], [12, 42], [2, 43], [43, 44], [44, 45], [13, 45], [13, 46], [14, 46], [14, 47], [15, 47], [53, 56], [56, 57], [57, 58], [51, 58], [59, 60], [49, 60], [55, 61], [61, 62], [62, 63], [50, 63], [64, 65], [51, 65], [49, 66], [66, 67], [67, 68], [52, 68], [48, 69], [69, 70], [48, 71], [71, 72], [72, 73], [54, 73], [50, 74], [74, 75]]
EBROW_MASTER_L_VERTS = [[-1.70158, 0.5298, -0.39297], [1.54361, -0.5298, -0.81676], [-1.54361, 0.5298, 0.81676], [1.70158, -0.5298, 0.39297]]
EBROW_MASTER_L_EDGES = [[2, 3], [0, 1], [0, 2], [1, 3]]
EBROW_MASTER_R_VERTS = [[-1.70158, 0.5298, -0.39297], [1.54361, -0.5298, -0.81676], [-1.54361, 0.5298, 0.81676], [1.70158, -0.5298, 0.39297]]
EBROW_MASTER_R_EDGES = [[2, 3], [0, 1], [0, 2], [1, 3]]
EBROW_TWEAK_VERTS = [[-0.8305, 0.4681, 0.52663], [0.8305, 0.4681, 0.52663], [-0.8305, -0.4681, 0.52663], [0.8305, -0.4681, 0.52663], [-0.8305, 0.4681, -0.59077], [0.8305, 0.4681, -0.59077], [-0.8305, -0.4681, -0.59077], [0.8305, -0.4681, -0.59077], [1.53746, -0.0, -0.03207], [0.8305, -0.0, 0.00804], [0.8305, -0.0, -0.07218], [1.40016, -0.0, 0.08826], [1.40016, -0.0, -0.15241], [1.40016, -0.0, 0.00804], [1.40016, -0.0, -0.07218], [0.0, 0.0, -1.29822], [0.04011, 0.0, -0.59126], [-0.04011, 0.0, -0.59126], [0.12033, 0.0, -1.16092], [-0.12033, 0.0, -1.16092], [0.04011, 0.0, -1.16092], [-0.04011, 0.0, -1.16092], [-1.53746, -0.0, -0.03207], [-0.8305, -0.0, 0.00804], [-0.8305, -0.0, -0.07218], [-1.40016, -0.0, 0.08826], [-1.40016, -0.0, -0.15241], [-1.40016, -0.0, 0.00804], [-1.40016, -0.0, -0.07218]]
EBROW_TWEAK_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]

ARROW_UP_VERTS = [[-0.55, 0.0, -0.45], [0.55, 0.0, -0.45], [0.0, 0.0, 0.6]]
ARROW_UP_EDGES = [[0, 1], [1, 2], [2, 0]]
ARROW_DOWN_VERTS = [[-0.55, 0.0, 0.45], [0.55, 0.0, 0.45], [0.0, 0.0, -0.6]]
ARROW_DOWN_EDGES = [[0, 1], [1, 2], [2, 0]]
EBROW_TWEAK2_L_VERTS = [[0.57815, -0.19227, -0.02967], [0.55841, -0.19624, -0.14754], [0.51721, -0.19268, -0.25975], [0.45613, -0.18171, -0.36197], [0.37753, -0.16376, -0.45028], [0.28442, -0.13952, -0.52129], [0.18038, -0.10992, -0.57226], [-0.04424, -0.03933, -0.60712], [-0.15618, -0.00107, -0.58967], [-0.26212, 0.03724, -0.54955], [-0.35798, 0.07411, -0.48832], [-0.44009, 0.10814, -0.40832], [-0.50529, 0.13801, -0.31263], [-0.55107, 0.16258, -0.20492], [-0.57567, 0.1809, -0.08934], [-0.57815, 0.19227, 0.02967], [-0.55841, 0.19624, 0.14754], [-0.51721, 0.19268, 0.25975], [-0.45613, 0.18171, 0.36197], [-0.37753, 0.16376, 0.45028], [-0.28442, 0.13952, 0.52129], [-0.18038, 0.10992, 0.57226], [-0.0694, 0.07609, 0.60124], [0.04424, 0.03933, 0.60712], [0.15618, 0.00107, 0.58967], [0.26212, -0.03724, 0.54955], [0.35798, -0.07411, 0.48832], [0.44009, -0.10814, 0.40832], [0.50529, -0.13801, 0.31263], [0.55107, -0.16258, 0.20492], [0.57567, -0.1809, 0.08934], [0.60157, -0.06474, 0.07763], [0.60434, 0.0539, 0.06294], [0.5839, 0.17047, 0.04583], [0.54102, 0.28049, 0.02696], [0.47734, 0.37973, 0.00705], [0.39532, 0.46438, -0.01313], [0.29811, 0.53118, -0.03281], [0.0735, 0.60176, -0.06767], [-0.04527, 0.60283, -0.08151], [-0.16231, 0.58073, -0.09223], [-0.2731, 0.53632, -0.09939], [-0.3734, 0.47129, -0.10274], [-0.45935, 0.38815, -0.10214], [-0.52765, 0.2901, -0.09762], [0.0, 0.0, 0.0], [-0.03111, 0.1873, 0.5797], [0.00838, 0.29132, 0.53587], [0.04754, 0.38414, 0.47146], [0.08488, 0.4622, 0.38892], [0.11896, 0.5225, 0.29144], [0.14846, 0.56272, 0.18276], [0.17226, 0.58132, 0.06706], [0.18945, 0.57757, -0.05122], [0.19934, 0.55163, -0.16753], [0.20158, 0.50449, -0.27741], [0.19608, 0.43796, -0.37662], [0.18303, 0.3546, -0.46136], [0.16296, 0.25762, -0.52837], [0.13662, 0.15073, -0.57508], [0.10503, 0.03805, -0.59968], [0.0694, -0.07609, -0.60124]]
EBROW_TWEAK2_L_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [25, 26], [26, 27], [27, 28], [28, 29], [30, 31], [31, 32], [32, 33], [33, 34], [34, 35], [35, 36], [36, 37], [38, 39], [39, 40], [40, 41], [41, 42], [42, 43], [43, 44], [14, 45], [30, 45], [46, 47], [47, 48], [48, 49], [49, 50], [50, 51], [51, 52], [52, 53], [53, 54], [54, 55], [55, 56], [56, 57], [57, 58], [58, 59], [59, 60], [60, 61], [0, 30], [6, 61], [7, 61], [29, 30], [37, 53], [38, 53], [14, 44], [22, 46], [45, 61], [22, 45]]
EBROW_TWEAK2_R_VERTS = [[-0.57815, -0.19227, -0.02967], [-0.55841, -0.19624, -0.14754], [-0.51721, -0.19268, -0.25975], [-0.45613, -0.18171, -0.36197], [-0.37753, -0.16376, -0.45028], [-0.28442, -0.13952, -0.52129], [-0.18038, -0.10992, -0.57226], [0.04424, -0.03933, -0.60712], [0.15618, -0.00107, -0.58967], [0.26212, 0.03724, -0.54955], [0.35798, 0.07411, -0.48832], [0.44009, 0.10814, -0.40832], [0.50529, 0.13801, -0.31263], [0.55107, 0.16258, -0.20492], [0.57567, 0.1809, -0.08934], [0.57815, 0.19227, 0.02967], [0.55841, 0.19624, 0.14754], [0.51721, 0.19268, 0.25975], [0.45613, 0.18171, 0.36197], [0.37753, 0.16376, 0.45028], [0.28442, 0.13952, 0.52129], [0.18038, 0.10992, 0.57226], [0.0694, 0.07609, 0.60124], [-0.04424, 0.03933, 0.60712], [-0.15618, 0.00107, 0.58967], [-0.26212, -0.03724, 0.54955], [-0.35798, -0.07411, 0.48832], [-0.44009, -0.10814, 0.40832], [-0.50529, -0.13801, 0.31263], [-0.55107, -0.16258, 0.20492], [-0.57567, -0.1809, 0.08934], [-0.60157, -0.06474, 0.07763], [-0.60434, 0.0539, 0.06294], [-0.5839, 0.17047, 0.04583], [-0.54102, 0.28049, 0.02696], [-0.47734, 0.37973, 0.00705], [-0.39532, 0.46438, -0.01313], [-0.29811, 0.53118, -0.03281], [-0.0735, 0.60176, -0.06767], [0.04527, 0.60283, -0.08151], [0.16231, 0.58073, -0.09223], [0.2731, 0.53632, -0.09939], [0.3734, 0.47129, -0.10274], [0.45935, 0.38815, -0.10214], [0.52765, 0.2901, -0.09762], [-0.0, 0.0, 0.0], [0.03111, 0.1873, 0.5797], [-0.00838, 0.29132, 0.53587], [-0.04754, 0.38414, 0.47146], [-0.08488, 0.4622, 0.38892], [-0.11896, 0.5225, 0.29144], [-0.14846, 0.56272, 0.18276], [-0.17226, 0.58132, 0.06706], [-0.18945, 0.57757, -0.05122], [-0.19934, 0.55163, -0.16753], [-0.20158, 0.50449, -0.27741], [-0.19608, 0.43796, -0.37662], [-0.18303, 0.3546, -0.46136], [-0.16296, 0.25762, -0.52837], [-0.13662, 0.15073, -0.57508], [-0.10503, 0.03805, -0.59968], [-0.0694, -0.07609, -0.60124]]
EBROW_TWEAK2_R_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [25, 26], [26, 27], [27, 28], [28, 29], [30, 31], [31, 32], [32, 33], [33, 34], [34, 35], [35, 36], [36, 37], [38, 39], [39, 40], [40, 41], [41, 42], [42, 43], [43, 44], [14, 45], [30, 45], [46, 47], [47, 48], [48, 49], [49, 50], [50, 51], [51, 52], [52, 53], [53, 54], [54, 55], [55, 56], [56, 57], [57, 58], [58, 59], [59, 60], [60, 61], [0, 30], [6, 61], [7, 61], [29, 30], [37, 53], [38, 53], [14, 44], [22, 46], [45, 61], [22, 45]]

EBROW_TWEAK1_L_VERTS = [[0.44625, -0.70296, -0.70206], [0.25719, -0.49566, 0.93507], [0.73684, 0.18352, -0.78075], [0.54778, 0.39081, 0.85638], [-0.60831, -0.3718, -0.86578], [-0.79738, -0.1645, 0.77135], [-0.31773, 0.51467, -0.94447], [-0.50679, 0.72197, 0.69266], [-0.20527, 0.20139, 1.51067], [-0.08695, 0.10127, 0.81974], [-0.16266, 0.12504, 0.80799], [-0.07608, 0.14859, 1.39297], [-0.30321, 0.21991, 1.35771], [-0.15179, 0.17236, 1.38122], [-0.2275, 0.19614, 1.36946], [-1.22522, 0.38474, -0.19021], [-0.56258, 0.18023, -0.0471], [-0.55345, 0.17022, -0.12617], [-1.10934, 0.35907, -0.05149], [-1.08194, 0.32903, -0.2887], [-1.1002, 0.34906, -0.13056], [-1.09107, 0.33904, -0.20963], [0.14474, -0.18238, -1.52007], [0.10212, -0.10603, -0.81739], [0.02641, -0.08226, -0.82914], [0.24268, -0.2009, -1.36711], [0.01554, -0.12958, -1.40237], [0.16696, -0.17713, -1.37886], [0.09125, -0.15335, -1.39061]]
EBROW_TWEAK1_L_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]
EBROW_TWEAK1_R_VERTS = [[-0.44625, -0.70296, -0.70206], [-0.25719, -0.49566, 0.93507], [-0.73684, 0.18352, -0.78075], [-0.54778, 0.39081, 0.85638], [0.60831, -0.3718, -0.86578], [0.79738, -0.1645, 0.77135], [0.31773, 0.51467, -0.94447], [0.50679, 0.72197, 0.69266], [0.20527, 0.20139, 1.51067], [0.08695, 0.10127, 0.81974], [0.16266, 0.12504, 0.80799], [0.07608, 0.14859, 1.39297], [0.30321, 0.21991, 1.35771], [0.15179, 0.17236, 1.38122], [0.2275, 0.19614, 1.36946], [1.22522, 0.38474, -0.19021], [0.56258, 0.18023, -0.0471], [0.55345, 0.17022, -0.12617], [1.10934, 0.35907, -0.05149], [1.08194, 0.32903, -0.2887], [1.1002, 0.34906, -0.13056], [1.09107, 0.33904, -0.20963], [-0.14474, -0.18238, -1.52007], [-0.10212, -0.10603, -0.81739], [-0.02641, -0.08226, -0.82914], [-0.24268, -0.2009, -1.36711], [-0.01554, -0.12958, -1.40237], [-0.16696, -0.17713, -1.37886], [-0.09125, -0.15335, -1.39061]]
EBROW_TWEAK1_R_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]
EBROW_TWEAK3_L_VERTS = [[-0.66599, -0.3537, -0.87474], [-0.85504, -0.14651, 0.76241], [-0.3755, 0.53281, -0.95339], [-0.56454, 0.73999, 0.68376], [0.3956, -0.68696, -0.70998], [0.20655, -0.47977, 0.92717], [0.68609, 0.19955, -0.78863], [0.49705, 0.40674, 0.84852], [-0.25946, 0.2183, 1.50227], [-0.2171, 0.14207, 0.79955], [-0.14089, 0.11815, 0.81138], [-0.35816, 0.23706, 1.3492], [-0.12951, 0.16528, 1.38469], [-0.28194, 0.21313, 1.36103], [-0.20572, 0.18921, 1.37286], [1.11843, -0.3511, 0.17358], [0.44222, -0.13525, 0.10888], [0.45135, -0.14526, 0.0298], [0.97429, -0.29514, 0.27194], [1.00168, -0.32516, 0.03473], [0.98342, -0.30515, 0.19287], [0.99255, -0.31515, 0.1138], [0.09051, -0.16526, -1.52849], [-0.02806, -0.06511, -0.8376], [0.04816, -0.08904, -0.82577], [-0.03944, -0.11224, -1.41091], [0.18921, -0.18402, -1.37542], [0.03678, -0.13617, -1.39908], [0.11299, -0.16009, -1.38725]]
EBROW_TWEAK3_L_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]
EBROW_TWEAK3_R_VERTS = [[0.66599, -0.3537, -0.87474], [0.85504, -0.14651, 0.76241], [0.3755, 0.53281, -0.95339], [0.56454, 0.73999, 0.68376], [-0.3956, -0.68696, -0.70998], [-0.20655, -0.47977, 0.92717], [-0.68609, 0.19955, -0.78863], [-0.49705, 0.40674, 0.84852], [0.25946, 0.2183, 1.50227], [0.2171, 0.14207, 0.79955], [0.14089, 0.11815, 0.81138], [0.35816, 0.23706, 1.3492], [0.12951, 0.16528, 1.38469], [0.28194, 0.21313, 1.36103], [0.20572, 0.18921, 1.37286], [-1.11843, -0.3511, 0.17358], [-0.44222, -0.13525, 0.10888], [-0.45135, -0.14526, 0.0298], [-0.97429, -0.29514, 0.27194], [-1.00168, -0.32516, 0.03473], [-0.98342, -0.30515, 0.19287], [-0.99255, -0.31515, 0.1138], [-0.09051, -0.16526, -1.52849], [0.02806, -0.06511, -0.8376], [-0.04816, -0.08904, -0.82577], [0.03944, -0.11224, -1.41091], [-0.18921, -0.18402, -1.37542], [-0.03678, -0.13617, -1.39908], [-0.11299, -0.16009, -1.38725]]
EBROW_TWEAK3_R_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]
LIP00_L_VERTS = [[0.25457, -0.31, -0.55], [0.25457, -0.31, 0.55], [0.25457, 0.31, -0.55], [0.25457, 0.31, 0.55], [-0.48543, -0.31, -0.55], [-0.48543, -0.31, 0.55], [-0.48543, 0.31, -0.55], [-0.48543, 0.31, 0.55], [-0.11543, 0.0, 1.01819], [-0.08887, 0.0, 0.55], [-0.142, 0.0, 0.55], [-0.03574, 0.0, 0.92726], [-0.19512, 0.0, 0.92726], [-0.08887, 0.0, 0.92726], [-0.142, 0.0, 0.92726], [-0.95394, -0.0, 0.0], [-0.48575, -0.0, 0.02656], [-0.48575, -0.0, -0.02656], [-0.86301, -0.0, 0.07969], [-0.86301, -0.0, -0.07969], [-0.86301, -0.0, 0.02656], [-0.86301, -0.0, -0.02656], [-0.11543, 0.0, -1.01819], [-0.08887, 0.0, -0.55], [-0.142, 0.0, -0.55], [-0.03574, 0.0, -0.92726], [-0.19512, 0.0, -0.92726], [-0.08887, 0.0, -0.92726], [-0.142, 0.0, -0.92726]]
LIP00_L_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]
LIP00_R_VERTS = [[-0.25457, -0.31, -0.55], [-0.25457, -0.31, 0.55], [-0.25457, 0.31, -0.55], [-0.25457, 0.31, 0.55], [0.48543, -0.31, -0.55], [0.48543, -0.31, 0.55], [0.48543, 0.31, -0.55], [0.48543, 0.31, 0.55], [0.11543, 0.0, 1.01819], [0.08887, 0.0, 0.55], [0.142, 0.0, 0.55], [0.03574, 0.0, 0.92726], [0.19512, 0.0, 0.92726], [0.08887, 0.0, 0.92726], [0.142, 0.0, 0.92726], [0.95394, -0.0, 0.0], [0.48575, -0.0, 0.02656], [0.48575, -0.0, -0.02656], [0.86301, -0.0, 0.07969], [0.86301, -0.0, -0.07969], [0.86301, -0.0, 0.02656], [0.86301, -0.0, -0.02656], [0.11543, 0.0, -1.01819], [0.08887, 0.0, -0.55], [0.142, 0.0, -0.55], [0.03574, 0.0, -0.92726], [0.19512, 0.0, -0.92726], [0.08887, 0.0, -0.92726], [0.142, 0.0, -0.92726]]
LIP00_R_EDGES = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7], [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5], [8, 12], [9, 10], [9, 13], [10, 14], [11, 13], [12, 14], [8, 11], [15, 19], [16, 17], [16, 20], [17, 21], [18, 20], [19, 21], [15, 18], [22, 26], [23, 24], [23, 27], [24, 28], [25, 27], [26, 28], [22, 25]]

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
    elif kind == 'ebrowtweak1.L':
        verts = EBROW_TWEAK1_L_VERTS
        edges = EBROW_TWEAK1_L_EDGES
    elif kind == 'ebrowtweak1.R':
        verts = EBROW_TWEAK1_R_VERTS
        edges = EBROW_TWEAK1_R_EDGES
    elif kind == 'ebrowtweak3.L':
        verts = EBROW_TWEAK3_L_VERTS
        edges = EBROW_TWEAK3_L_EDGES
    elif kind == 'ebrowtweak3.R':
        verts = EBROW_TWEAK3_R_VERTS
        edges = EBROW_TWEAK3_R_EDGES
    elif kind == 'lip00.L':
        verts = LIP00_L_VERTS
        edges = LIP00_L_EDGES
    elif kind == 'lip00.R':
        verts = LIP00_R_VERTS
        edges = LIP00_R_EDGES
    elif kind == 'arrow_up':
        verts = ARROW_UP_VERTS
        edges = ARROW_UP_EDGES
    elif kind == 'arrow_down':
        verts = ARROW_DOWN_VERTS
        edges = ARROW_DOWN_EDGES
    elif kind == 'ebrowtweak2.L':
        verts = EBROW_TWEAK2_L_VERTS
        edges = EBROW_TWEAK2_L_EDGES
    elif kind == 'ebrowtweak2.R':
        verts = EBROW_TWEAK2_R_VERTS
        edges = EBROW_TWEAK2_R_EDGES
    elif kind == 'lipsmaster':
        verts = LIPS_MASTER_VERTS
        edges = LIPS_MASTER_EDGES
    elif kind == 'eyeblink':
        verts = EYEBLINK_VERTS
        edges = EYEBLINK_EDGES
    elif kind == 'ebrowmaster.L':
        verts = EBROW_MASTER_L_VERTS
        edges = EBROW_MASTER_L_EDGES
    elif kind == 'ebrowmaster.R':
        verts = EBROW_MASTER_R_VERTS
        edges = EBROW_MASTER_R_EDGES
    elif kind == 'ebrowtweak':
        verts = EBROW_TWEAK_VERTS
        edges = EBROW_TWEAK_EDGES
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
        verts = [(0, 0, -1), (0, 0, 1), (-0.35, 0, 1), (0.35, 0, 1)]
        edges = [(0, 1), (2, 3)]
    elif kind == 'ring':
        import math
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
    elif kind == 'diamond':
        verts = [(0, 0, 1), (0.75, 0, 0), (0, 0, -1), (-0.75, 0, 0)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    elif kind == 'eyebrow':
        N = 14
        top = []
        bot = []
        for i in range(N + 1):
            x = -1.0 + 2.0 * i / N
            arch = 0.40 * (1.0 - x * x)
            ht = 0.20 * (1.0 - x * x)
            top.append((x, 0.0, arch + ht))
            bot.append((x, 0.0, arch - ht))
        verts = top + [bot[i] for i in range(N - 1, 0, -1)]
        edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    else:
        verts, edges = [(0, 0, 0)], []
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    return obj


def lighten(rgb, amt):
    return tuple(min(1.0, c + amt) for c in rgb)


def apply_color(armature, pb, group_name, rgb, cache):
    if ver != 3:
        try:
            pb.color.palette = 'CUSTOM'
            cc = pb.color.custom
            cc.normal = rgb
            cc.select = lighten(rgb, 0.25)
            cc.active = lighten(rgb, 0.5)
        except Exception:
            pass
    else:
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


def is_face_rig_bone(bone_name):
    if bone_name == "Face-Root":
        return True
    b_low = bone_name.lower()
    if any(k in b_low for k in ("skirt", "hair", "dress", "cloth", "surfboard", "weapon", "spine", "arm", "leg", "hand", "foot", "torso", "root")):
        return False
    if bone_name.startswith("CTRL-Ctr_"):
        return False
    if any(bone_name.startswith(p) for p in (
        "CTRL-Mouth", "CTRL-Eye", "CTRL-Brow", "CTRL-Eyebrow",
        "CTRL-Master-Eyebrow", "CTRL-O_O", "CTRL-Fac_", "CTRL-Face",
        "MCH-EyeAim"
    )):
        return True
    if bone_name.startswith("CTRL-") and any(k in b_low for k in ("eyebrow", "ebrow", "brow", "eye", "mouth", "lip", "jaw", "highlight", "viseme")):
        return True
    return False


def purge_previous(armature):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    eb = armature.data.edit_bones
    for b in list(eb):
        if is_face_rig_bone(b.name):
            eb.remove(b)
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        if o.name.startswith("WGT-Face_"):
            bpy.data.objects.remove(o, do_unlink=True)


def setup_face_rig(mesh_obj, controls, armature, head_name, fwd, up, face_size):
    keyblock = mesh_obj.data.shape_keys.key_blocks if (mesh_obj and mesh_obj.data and mesh_obj.data.shape_keys) else None
    amw_inv = armature.matrix_world.inverted()
    bone_len = face_size * BONE_LEN_F

    def to_arm_point(p):
        return amw_inv @ p

    def to_arm_vec(v):
        return amw_inv.to_3x3() @ v

    fwd_arm = to_arm_vec(fwd).normalized()
    up_arm = to_arm_vec(up).normalized()

    has_ebrow_sk = any(is_eyebrow_key(sk.name) for sk in keyblock) if keyblock else False
    ebrow_bones = [] if has_ebrow_sk else find_eyebrow_bones(armature)
    if has_ebrow_sk and keyblock:
        controls.extend(build_brow_shapekey_controls(mesh_obj, armature, fwd, up, face_size))
    elif ebrow_bones:
        pass

    sides = {}
    for name in ebrow_bones:
        b = armature.data.bones.get(name)
        if b is None:
            continue
        s = eyebrow_side(name)
        sides.setdefault(s, []).append((name, armature.matrix_world @ b.head_local))

    for s, items in sides.items():
        center = Vector((0.0, 0.0, 0.0))
        for _, p in items:
            center += p
        center /= len(items)
        master_name = 'CTRL-Master-Eyebrow.%s' % s
        positions = [p for _, p in items]
        ebw = 0.0
        for _ia in range(len(positions)):
            for _ib in range(_ia + 1, len(positions)):
                _d = (positions[_ia] - positions[_ib]).length
                if _d > ebw:
                    ebw = _d
        if ebw < 1e-6:
            ebw = face_size * 0.1
        controls.append({'name': master_name, 'collection': FACERIG_COLLECTION,
                         'color': COL_EBRMASTER, 'group': 'Face Eyebrow',
                         'head': center + fwd * (face_size * OFFSET_F * 0.8),
                         'widget': 'pad', 'lim': face_size * EBR_MASTER_F,
                         'free': ('X', 'Y', 'Z'), 'range': 'both',
                         'shape_scale': Vector((ebw * 0.65, 1.0, ebw * 0.14)),
                         'shape_rotation': (0.0, -0.15 if s == 'L' else 0.15, 0.43825 if s == 'L' else -0.43825),
                         'kind': 'master', 'drivers': []})
        for name, head_world in items:
            front = center + (head_world - center) * 0.75 + fwd * (face_size * OFFSET_F * 0.8)
            ctrl_name = 'CTRL-' + name.strip().replace(' ', '_')
            if '01' in name:
                tw_widget = 'ebrowtweak3.%s' % s
            elif '02' in name:
                tw_widget = 'ebrowtweak2.%s' % s
            elif '03' in name:
                tw_widget = 'ebrowtweak1.%s' % s
            else:
                tw_widget = 'ebrowtweak1.%s' % s
            controls.append({'name': ctrl_name, 'collection': FACERIG_COLLECTION,
                             'color': COL_EBRBONE, 'group': 'Face Eyebrow',
                             'head': front, 'widget': tw_widget,
                             'lim': face_size * EBR_WGT_F, 'free': ('X', 'Y', 'Z'),
                             'range': 'both',
                             'shape_scale': Vector((face_size * EBR_WGT_F,) * 3),
                             'kind': 'fk', 'target_bone': name, 'parent': master_name,
                             'hook_name': ctrl_name + '_Hook', 'hook_head': head_world,
                             'drivers': []})

    bpy.context.view_layer.objects.active = armature
    try:
        armature.data.use_mirror_x = False
    except Exception:
        pass
    try:
        armature.pose.use_mirror_x = False
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
        par = eb.get(c['parent']) if c.get('parent') else None
        b.parent = par if par else root
        b.use_connect = False
        if c.get('hook_name'):
            hk = eb.get(c['hook_name']) or eb.new(c['hook_name'])
            hh = to_arm_point(c['hook_head'])
            hk.head = hh
            hk.tail = hh + fwd_arm * bone_len
            hk.use_deform = False
            hk.parent = b
            hk.use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')

    coll_names = []
    for c in controls:
        if c['collection'] not in coll_names:
            coll_names.append(c['collection'])
    if ver != 3 and hasattr(armature.data, "collections"):
        for cn in coll_names:
            coll = armature.data.collections.get(cn)
            if not coll:
                coll = armature.data.collections.new(cn)
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
            coll = armature.data.collections.get(c['collection'])
            if bone and coll:
                coll.assign(bone)
        other_c = armature.data.collections.get("Other") or armature.data.collections.new("Other")
        face_c = armature.data.collections.get("Face")
        hook_names = [c['hook_name'] for c in controls if c.get('hook_name')]
        for hn in hook_names:
            bone = armature.data.bones.get(hn)
            if bone:
                other_c.assign(bone)
                if face_c:
                    face_c.unassign(bone)
        for b in armature.data.bones:
            if "hook" in b.name.lower():
                other_c.assign(b)
                if face_c:
                    face_c.unassign(b)

    wgt_coll = get_widget_collection()
    bpy.ops.object.mode_set(mode='POSE')
    color_cache = {}

    for c in controls:
        pb = armature.pose.bones.get(c['name'])
        if not pb:
            continue

        if c.get('kind') in ('fk', 'master'):
            is_master = c['kind'] == 'master'
            for i in range(3):
                pb.lock_location[i] = False
                pb.lock_rotation[i] = not is_master
                pb.lock_scale[i] = not is_master
            pb.lock_rotation_w = not is_master
            pb.custom_shape = make_widget(c['widget'], wgt_coll)
            try:
                pb.use_custom_shape_bone_size = False
            except Exception:
                pass
            ss = c.get('shape_scale')
            pb.custom_shape_scale_xyz = ss if ss is not None else Vector((c['lim'] * WIDGET_F,) * 3)
            sr = c.get('shape_rotation')
            if sr is not None:
                try:
                    pb.custom_shape_rotation_euler = sr
                except Exception:
                    pass
            apply_color(armature, pb, c['group'], c['color'], color_cache)
            tb = armature.pose.bones.get(c['target_bone']) if c.get('target_bone') else None
            if tb:
                for cn in [x for x in tb.constraints if x.name == 'FaceRig CopyLoc']:
                    tb.constraints.remove(cn)
                con = tb.constraints.new(type='COPY_LOCATION')
                con.name = 'FaceRig CopyLoc'
                con.target = armature
                con.subtarget = c.get('hook_name') or c['name']
            continue

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

        pb.custom_shape = make_widget(c['widget'], wgt_coll)
        try:
            pb.use_custom_shape_bone_size = False
        except Exception:
            pass
        ss = c.get('shape_scale')
        pb.custom_shape_scale_xyz = ss if ss is not None else Vector((lim * WIDGET_F,) * 3)
        sr = c.get('shape_rotation')
        if sr is not None:
            try:
                pb.custom_shape_rotation_euler = sr
            except Exception:
                pass

        apply_color(armature, pb, c['group'], c['color'], color_cache)

    bpy.ops.object.mode_set(mode='OBJECT')

    if keyblock is not None:
        agg = {}
        for c in controls:
            for d in c.get('drivers', []):
                agg.setdefault(d['key'], []).append(
                    {'bone': c['name'], 'axis': d['axis'], 'dir': d['dir'],
                     'lim': c['lim'], 'bidir': d.get('bidir', False),
                     'gain': d.get('gain', 1.0)})

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
                vn = "v%d" % i
                var = drv.variables.new()
                var.name = vn
                var.type = 'TRANSFORMS'
                tgt = var.targets[0]
                tgt.id = armature
                tgt.bone_target = e['bone']
                tgt.transform_type = 'LOC_' + e['axis']
                tgt.transform_space = 'LOCAL_SPACE'
                sign = '' if e['dir'] > 0 else '-'
                g = e.get('gain', 1.0)
                if e['bidir']:
                    base = "%s%s / %r" % (sign, vn, e['lim'])
                else:
                    base = "max(0.0, %s%s / %r)" % (sign, vn, e['lim'])
                terms.append(base if g == 1.0 else "%r * (%s)" % (g, base))
            drv.expression = terms[0] if len(terms) == 1 else "max(" + ", ".join(terms) + ")"

        _ang = keyblock.get("Fac_Ebr_Angry")
        if _ang is not None:
            _ang.slider_min = 0.0


def assign_bones_to_other_collection(armature, bone_names):
    if ver != 3 and hasattr(armature.data, "collections"):
        coll = armature.data.collections.get("Other") or armature.data.collections.new("Other")
        try:
            coll.is_visible = False
        except Exception:
            pass
        for bname in bone_names:
            b = armature.data.bones.get(bname)
            if b:
                for c in list(b.collections):
                    try:
                        c.unassign(b)
                    except Exception:
                        pass
                coll.assign(b)
    elif hasattr(armature.pose, "bone_groups"):
        bg = armature.pose.bone_groups.get("Other")
        if bg:
            for bname in bone_names:
                pb = armature.pose.bones.get(bname)
                if pb:
                    pb.bone_group = bg


def remove_eyetrack_bones(armature):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = armature.data.edit_bones
    targets = ("eyetrack", "eyetrack_L", "eyetrack_R", "eyetrack.L", "eyetrack.R",
               "EyeTrack", "EyeTrack_L", "EyeTrack_R", "EyeTrack.L", "EyeTrack.R")
    for name in targets:
        b = ebs.get(name)
        if b:
            ebs.remove(b)
    for b in list(ebs):
        if b.name.lower().startswith("eyetrack"):
            ebs.remove(b)
    bpy.ops.object.mode_set(mode='OBJECT')


def hide_mechanism_bones(armature):
    HIDE_PREFIXES = (
        "CtrEyebrow", "SknEyebrow", "SknEyeLight", "SknMouth", "Face-Root",
        "Skn_L_Mouth", "Skn_R_Mouth", "Skn_M_Mouth", "Skn_L_Highlights",
        "Skn_R_Highlights", "Skn_RemiMk_", "BdyMouth", "PTMouth"
    )

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = armature
    hidden = 0
    for b in armature.data.bones:
        if any(b.name.startswith(p) for p in HIDE_PREFIXES):
            b.hide = True
            hidden += 1

    assign_bones_to_other_collection(armature, ("MCH-EyeAim.L", "MCH-EyeAim.R", "Face-Root"))


def get_facerig_bone_collection(armature, name=FACERIG_COLLECTION):
    if ver != 3 and hasattr(armature.data, "collections"):
        coll = armature.data.collections.get(name) or armature.data.collections.new(name)
        try:
            coll.is_visible = True
        except Exception:
            pass
        return coll
    return None


def setup_lookat_eyes(armature, head_name, fwd, up, face_size):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = armature

    eye_L_name = None
    for cand in ("eye.L", "DEF-eye.L", "Skn_L_Eye", "+EyeBone L A01", "+EyeBone L A02", "EYE_L", "Eye_L", "PT_L_Eye", "Bn_Eye_L"):
        if cand in armature.data.bones:
            eye_L_name = cand
            break
    eye_R_name = None
    for cand in ("eye.R", "DEF-eye.R", "Skn_R_Eye", "+EyeBone R A01", "+EyeBone R A02", "EYE_R", "Eye_R", "PT_R_Eye", "Bn_Eye_R"):
        if cand in armature.data.bones:
            eye_R_name = cand
            break

    if not eye_L_name or not eye_R_name:
        return

    amw_inv = armature.matrix_world.inverted()
    fwd_arm = (amw_inv.to_3x3() @ fwd).normalized()
    up_arm = (amw_inv.to_3x3() @ up).normalized()

    MASTER = "CTRL-Eye_Master"
    PAIRS = ((eye_L_name, "CTRL-Eye.L", "MCH-EyeAim.L"), (eye_R_name, "CTRL-Eye.R", "MCH-EyeAim.R"))

    bpy.ops.object.mode_set(mode='EDIT')
    eb = armature.data.edit_bones
    for nm in (MASTER, "CTRL-Eye.L", "CTRL-Eye.R", "MCH-EyeAim.L", "MCH-EyeAim.R"):
        old = eb.get(nm)
        if old:
            eb.remove(old)

    e_heads = {}
    gaze_dirs = {}
    track_axes = {}
    for eye_name, ctl_name, mch_name in PAIRS:
        e = eb.get(eye_name)
        if not e:
            continue
        m = e.matrix
        cand = [(m.col[0].to_3d(), 'TRACK_X', 'TRACK_NEGATIVE_X'),
                (m.col[1].to_3d(), 'TRACK_Y', 'TRACK_NEGATIVE_Y'),
                (m.col[2].to_3d(), 'TRACK_Z', 'TRACK_NEGATIVE_Z')]
        best = None
        for vec, pax, nax in cand:
            if vec.length < 1e-9:
                continue
            v = vec.normalized()
            d = v.dot(fwd_arm)
            if best is None or abs(d) > abs(best[0]):
                best = (d, v, pax, nax)
        if best is None:
            gaze_dirs[eye_name] = fwd_arm.copy()
            track_axes[eye_name] = 'TRACK_Y'
        else:
            d, v, pax, nax = best
            if d >= 0:
                gaze_dirs[eye_name] = v
                track_axes[eye_name] = pax
            else:
                gaze_dirs[eye_name] = -v
                track_axes[eye_name] = nax
        e_heads[eye_name] = e.head.copy()

    if eye_L_name not in e_heads or eye_R_name not in e_heads:
        bpy.ops.object.mode_set(mode='OBJECT')
        return

    sep = (e_heads[eye_L_name] - e_heads[eye_R_name]).length
    if sep < 1e-6:
        sep = face_size * 0.1
    blen = max(sep * 0.5, face_size * BONE_LEN_F * 2.0)
    offset = min(face_size * EYE_LOOK_FWD_F, sep * 3.0)
    offv = fwd_arm * offset

    parent_bone = eb.get(head_name) if head_name else None
    if parent_bone is None and eye_L_name in eb:
        parent_bone = eb[eye_L_name].parent

    heads = {
        MASTER: (e_heads[eye_L_name] + e_heads[eye_R_name]) * 0.5 + offv,
        "CTRL-Eye.L": e_heads[eye_L_name] + offv,
        "CTRL-Eye.R": e_heads[eye_R_name] + offv,
    }
    mb = eb.new(MASTER)
    mb.head = heads[MASTER]
    mb.tail = heads[MASTER] + fwd_arm * blen
    try:
        mb.align_roll(up_arm)
    except Exception:
        pass
    mb.use_deform = False
    mb.parent = parent_bone
    mb.use_connect = False

    for eye_name, ctl_name, mch_name in PAIRS:
        gd = gaze_dirs[eye_name]
        ch = heads[ctl_name]
        ah = e_heads[eye_name] + gd * offset
        cb = eb.new(ctl_name)
        cb.head = ch
        cb.tail = ch + fwd_arm * blen
        try:
            cb.align_roll(up_arm)
        except Exception:
            pass
        cb.use_deform = False
        cb.parent = mb
        cb.use_connect = False
        ab = eb.new(mch_name)
        ab.head = ah
        ab.tail = ah + gd * blen
        try:
            ab.align_roll(up_arm)
        except Exception:
            pass
        ab.use_deform = False
        ab.parent = cb
        ab.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')

    wgt_coll = get_widget_collection()
    bpy.ops.object.mode_set(mode='POSE')
    pbm = armature.pose.bones.get(MASTER)
    if pbm:
        pbm.custom_shape = make_widget('eyemaster', wgt_coll)
        try:
            pbm.use_custom_shape_bone_size = False
        except Exception:
            pass
        sm = max(sep / 0.9, face_size * 0.28)
        pbm.custom_shape_scale_xyz = Vector((sm, sm, sm))
        apply_color(armature, pbm, 'Face Eye-Aim', COL_EYEGREEN, {})
    se = max(sep * 0.45, face_size * 0.12)
    for eye_name, ctl_name, mch_name in PAIRS:
        pbc = armature.pose.bones.get(ctl_name)
        if pbc:
            pbc.custom_shape = make_widget('eyecircle', wgt_coll)
            try:
                pbc.use_custom_shape_bone_size = False
            except Exception:
                pass
            pbc.custom_shape_scale_xyz = Vector((se, se, se))
            apply_color(armature, pbc, 'Face Eye-Aim', COL_EYEGREEN, {})
    for eye_name, ctl_name, mch_name in PAIRS:
        pbe = armature.pose.bones.get(eye_name)
        if not pbe:
            continue
        for con in list(pbe.constraints):
            if con.name == "CTRL-EyeAim":
                pbe.constraints.remove(con)
        con = pbe.constraints.new('DAMPED_TRACK')
        con.name = "CTRL-EyeAim"
        con.target = armature
        con.subtarget = mch_name
        con.track_axis = track_axes[eye_name]
    bpy.ops.object.mode_set(mode='OBJECT')

    fcoll = get_facerig_bone_collection(armature)
    if fcoll is not None:
        for nm in (MASTER, "CTRL-Eye.L", "CTRL-Eye.R"):
            b = armature.data.bones.get(nm)
            if not b:
                continue
            for c in list(b.collections):
                try:
                    c.unassign(b)
                except Exception:
                    pass
            fcoll.assign(b)
    for nm in ("MCH-EyeAim.L", "MCH-EyeAim.R"):
        b = armature.data.bones.get(nm)
        if b:
            b.hide = True


def zzz_face_rig_main():
    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        faceobj = None
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            n = obj.name.lower()
            if any(ign in n for ign in ["weapon_", "gun_", "sword_"]):
                continue
            if "face" in n or "_face" in n or "head" in n:
                if obj.data and obj.data.shape_keys is not None:
                    faceobj = obj
                    break
                if faceobj is None:
                    faceobj = obj

        if faceobj is None:
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and ('face' in obj.name.lower() or 'head' in obj.name.lower()):
                    faceobj = obj
                    break

        if faceobj is None:
            print("[ZZZ Face Rig] No face mesh found in the scene.")
            return

        has_shapekeys = faceobj.data and faceobj.data.shape_keys is not None
        keyblock = faceobj.data.shape_keys.key_blocks if has_shapekeys else None

        if keyblock:
            shapekeyrename(keyblock)

        armature, head_name = find_armature_and_head(faceobj)
        for _hn in (
            "eye.L", "eye.R", "eye.L.001", "eye.R.001", "SknEyeStar.L", "SknEyeStar.R", "Eye Control",
            "Skn_M_Mouth", "BdyMouth.L", "BdyMouth.R", "Bdy_M_Mouth", "PTMouth.L", "PTMouth.R", "PT_M_Mouth",
            "Mouth_A", "Mouth_B", "Mouth_C", "Ctr_Up_Teeth", "Ctr_Down_Teeth", "Bn_MouthControl_L",
            "Bn_MouthControl_R", "Bn_MouthControl_M", "SknEyebrow_01.L", "SknEyebrow_02.L", "SknEyebrow_03.L",
            "SknEyebrow_01.R", "SknEyebrow_02.R", "SknEyebrow_03.R", "SknMouth.R", "SknMouth.L",
            "eyetrack", "eyetrack_L", "eyetrack_R", "EyeTrack", "EyeTrack_L", "EyeTrack_R",
            "eyetrack.L", "eyetrack.R", "EyeTrack.L", "EyeTrack.R"
        ):
            _hb = armature.data.bones.get(_hn)
            if _hb:
                _hb.hide = True

        fwd, right, up, face_size = face_frame(faceobj, armature)
        controls = []
        if keyblock:
            controls = plan_controls(faceobj, fwd, right, up, face_size)

        # Also add bone-based mouth controls if no mouth shapekeys present
        has_mouth_sk = keyblock and any(k.startswith("Fac_Mth_") for k in keyblock.keys())
        if not has_mouth_sk:
            controls.extend(build_mouth_bone_controls(armature, fwd, up, right, face_size))

        # Add extra facial bone controls (highlights, face marks)
        controls.extend(build_extra_face_bone_controls(armature, fwd, up, right, face_size))

        if any(armature.data.bones.get(_bn) for _bn in ("Mouth_A", "Mouth_B", "Mouth_C", "Bn_MouthControl_L", "Bn_MouthControl_R", "Bn_MouthControl_M")):
            controls = [c for c in controls if not c['name'].startswith("CTRL-Mouth-Corner")]

        if any(any(_p in _b.name.lower() for _p in ("bdymouth", "bdy_m_mouth", "ptmouth", "pt_m_mouth")) for _b in armature.data.bones):
            for _cn, _frm, _to in (("CTRL-Mouth-Corner.L", "_L_", "_R_"),
                                   ("CTRL-Mouth-Corner.R", "_R_", "_L_")):
                _c = next((x for x in controls if x['name'] == _cn), None)
                if _c is not None:
                    for _d in _c['drivers']:
                        _d['key'] = _d['key'].replace(_frm, _to)
            _ms = next((x for x in controls if x['name'] == 'CTRL-Mouth-Shift'), None)
            if _ms is not None:
                for _d in _ms['drivers']:
                    if _d['axis'] == 'X':
                        _d['dir'] = -_d['dir']

        has_eye_bones = any(cand in armature.data.bones for cand in ("eye.L", "DEF-eye.L", "Skn_L_Eye", "+EyeBone L A01", "EYE_L", "Eye_L", "PT_L_Eye", "Bn_Eye_L"))

        if not controls and not has_eye_bones:
            print("[ZZZ Face Rig] No drivable shape keys or facial bones found.")
            return

        if CLEAN_REBUILD:
            purge_previous(armature)

        remove_eyetrack_bones(armature)
        if controls:
            setup_face_rig(faceobj, controls, armature, head_name, fwd, up, face_size)
        setup_lookat_eyes(armature, head_name, fwd, up, face_size)
        hide_mechanism_bones(armature)

        wgt_coll = get_widget_collection()
        finalize_widget_collection(wgt_coll)
        old_facerig_wgt = bpy.data.collections.get("WGTS_FaceRig")
        if old_facerig_wgt:
            finalize_widget_collection(old_facerig_wgt)

        print("\nZZZ Face Rig complete. %d controls built on '%s'.\n"
              % (len(controls), armature.name))

    finally:
        try:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass


if __name__ == "__main__":
    zzz_face_rig_main()
