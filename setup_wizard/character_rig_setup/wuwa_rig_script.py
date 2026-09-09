# Based on Blender-WuWa-Character-Setup by @fnoji (https://github.com/fnoji/Blender-WuWa-Character-Setup)
# Gustling Waters Shader by @nytsjared (https://github.com/nytsjared)
# Adapted for Gacha Setup by PaoloESAN
# Licensed under GPL-3.0-or-later

import bpy
import os
import math
import mathutils
import bmesh
from mathutils import Vector
from math import pi, cos, sin
from collections import defaultdict, deque

from setup_wizard.character_rig_setup.rig_ui_utils import (
    setup_standard_bone_collections,
    distribute_standard_rig_bones,
    bone_to_layer_or_collection,
    modify_and_run_rig_ui_script,
    extract_clean_character_name,
)

# Supported model prefixes — order matters for matching
_MODEL_PREFIX_PATTERNS = [
    ("R2T1", "R2T1"),
    ("NHT1", "NHT1"),
    ("NH_",  "NH_"),
    ("MB1",  "MB1"),
    ("ML1",  "ML1"),
    ("NA0",  "NA0"),
    ("NM0",  "NM0"),
]

ALWAYS_BIPED_PREFIXES = {"R2T1", "NHT1", "NH_"}
BIPED_CHECK_PREFIXES = {"MB1", "ML1", "NA0", "NM0"}

REQUIRED_BIPED_BONES = [
    "Bip001Pelvis", "Bip001Spine", "Bip001Spine1", "Bip001Spine2",
    "Bip001Neck", "Bip001Head",
    "Bip001LClavicle", "Bip001RClavicle",
    "Bip001LUpperArm", "Bip001RUpperArm",
    "Bip001LForearm", "Bip001RForearm",
    "Bip001LHand", "Bip001RHand",
    "Bip001LThigh", "Bip001RThigh",
    "Bip001LCalf", "Bip001RCalf",
    "Bip001LFoot", "Bip001RFoot",
    "Bip001LToe0", "Bip001RToe0",
    "Bip001LFinger0", "Bip001RFinger0",
]

left_bone_pairs = [
    ("Bip001LFinger1", "Bip001LFinger11"),
    ("Bip001LFinger11", "Bip001LFinger12"),
    ("Bip001LFinger12", "Bip001LFinger13"),
    ("Bip001LFinger2", "Bip001LFinger21"),
    ("Bip001LFinger21", "Bip001LFinger22"),
    ("Bip001LFinger22", "Bip001LFinger23"),
    ("Bip001LFinger3", "Bip001LFinger31"),
    ("Bip001LFinger31", "Bip001LFinger32"),
    ("Bip001LFinger32", "Bip001LFinger33"),
    ("Bip001LFinger4", "Bip001LFinger41"),
    ("Bip001LFinger41", "Bip001LFinger42"),
    ("Bip001LFinger42", "Bip001LFinger43"),
]

right_bone_pairs = [
    ("Bip001RFinger1", "Bip001RFinger11"),
    ("Bip001RFinger11", "Bip001RFinger12"),
    ("Bip001RFinger12", "Bip001RFinger13"),
    ("Bip001RFinger2", "Bip001RFinger21"),
    ("Bip001RFinger21", "Bip001RFinger22"),
    ("Bip001RFinger22", "Bip001RFinger23"),
    ("Bip001RFinger3", "Bip001RFinger31"),
    ("Bip001RFinger31", "Bip001RFinger32"),
    ("Bip001RFinger32", "Bip001RFinger33"),
    ("Bip001RFinger4", "Bip001RFinger41"),
    ("Bip001RFinger41", "Bip001RFinger42"),
    ("Bip001RFinger42", "Bip001RFinger43"),
]

skip_if_finger13 = {
    ("Bip001LFinger1", "Bip001LFinger11"),
    ("Bip001LFinger2", "Bip001LFinger21"),
    ("Bip001LFinger3", "Bip001LFinger31"),
    ("Bip001LFinger4", "Bip001LFinger41"),
    ("Bip001RFinger1", "Bip001RFinger11"),
    ("Bip001RFinger2", "Bip001RFinger21"),
    ("Bip001RFinger3", "Bip001RFinger31"),
    ("Bip001RFinger4", "Bip001RFinger41"),
}

ALIGN_THRESHOLD = math.radians(5)
move_amount = 0.0001
NEIGHBOR_DEPTH = 4


def extract_clean_character_name(name: str, title_case: bool = True) -> str:
    if name.endswith("_Skeleton"):
        name = name[:-9]
    if name.startswith("RIG-"):
        name = name[4:]

    import re
    if match := re.search(r"R2T1(.+?)Md\d+_LOD\d+", name):
        extracted = match.group(1)
        return extracted.title() if title_case else extracted
    if match := re.search(r"MB1(.+?)Md\d+(?:_\w+)?_LOD\d+", name):
        extracted = match.group(1)
        return extracted.title() if title_case else extracted
    if match := re.search(r"ML1(.+?)Md\d+(?:_\w+)?_LOD\d+", name):
        extracted = match.group(1)
        return extracted.title() if title_case else extracted
    if match := re.search(r"((?:NA0|NM0).+?)_LOD\d+", name):
        extracted = match.group(1)
        return extracted.title() if title_case else extracted
    if match := re.search(r"NHT1(.+?)_LOD\d+", name):
        extracted = match.group(1)
        return extracted.title() if title_case else extracted
    if match := re.search(r"NH_(.+?)_LOD\d+", name):
        extracted = match.group(1)
        return extracted.title() if title_case else extracted

    # General cleanup
    clean = name.split(".")[0].replace("Skeleton", "").replace("Rig", "").strip("_ ")
    return clean.title() if title_case and clean else (clean or name)


def get_model_prefix(name: str):
    if name.endswith("_Skeleton"):
        name = name[:-9]
    for prefix, pattern in _MODEL_PREFIX_PATTERNS:
        if name.startswith(pattern):
            return prefix
    return None


def is_biped_skeleton(armature) -> bool:
    bone_names = {b.name for b in armature.data.bones}
    return all(name in bone_names for name in REQUIRED_BIPED_BONES)


def get_local_x(bone):
    return bone.matrix.to_3x3().col[0].normalized()


def angle_between(v1, v2):
    if v1.length == 0 or v2.length == 0:
        return math.pi
    return v1.angle(v2)


def all_bone_pairs():
    return left_bone_pairs + right_bone_pairs


def remove_bone_collections(armature):
    if hasattr(armature.data, "collections") and armature.data.collections:
        for collection in list(armature.data.collections):
            try:
                armature.data.collections.remove(collection)
            except Exception:
                pass


def process_bone_collections_and_rigify(armature, bone_data):
    for collection_name, index, row in bone_data:
        coll = armature.data.collections.get(collection_name)
        if not coll:
            coll = armature.data.collections.new(collection_name)
        try:
            coll.rigify_ui_row = row
        except Exception:
            pass
        if hasattr(bpy.ops.armature, "rigify_collection_set_ui_row"):
            try:
                bpy.ops.armature.rigify_collection_set_ui_row(index=index, row=row)
            except Exception:
                pass


def lock_bone_transformations(bone, armature=None):
    """Safely unlocks transformations if bone is a PoseBone or by looking up the PoseBone from armature."""
    pbone = None
    if hasattr(bone, "lock_location"):
        pbone = bone
    elif armature and hasattr(armature, "pose") and armature.pose:
        bname = bone.name if hasattr(bone, "name") else str(bone)
        pbone = armature.pose.bones.get(bname)

    if pbone:
        try:
            pbone.lock_location[:] = (False, False, False)
            pbone.lock_rotation_w = False
            pbone.lock_rotation[:] = (False, False, False)
        except Exception:
            pass


def select_bone(b):
    """Safely selects a bone across Blender versions, whether Bone, EditBone, or PoseBone."""
    if hasattr(b, "bone"):
        b = b.bone
    if hasattr(b, "select_set"):
        try:
            b.select_set(True)
        except Exception:
            pass
    elif hasattr(b, "select"):
        try:
            b.select = True
        except Exception:
            pass


def assign_bone_to_collection(armature, bone_or_name, collection_name_or_index, exclusive=True):
    """
    Directly assigns a bone to a bone collection on armature.data.collections in Blender 4.0+ / 5.x.
    collection_name_or_index: str (name) or int (index).
    If exclusive is True, unassigns the bone from all other collections first.
    """
    if not armature or not armature.data or not hasattr(armature.data, "collections"):
        return None

    if isinstance(bone_or_name, str):
        bone = armature.data.bones.get(bone_or_name)
    elif hasattr(bone_or_name, "bone"):  # PoseBone
        bone = bone_or_name.bone
    else:
        bone = bone_or_name

    if not bone:
        return None

    coll = None
    if isinstance(collection_name_or_index, int):
        if 0 <= collection_name_or_index < len(armature.data.collections):
            coll = armature.data.collections[collection_name_or_index]
    elif isinstance(collection_name_or_index, str):
        coll = armature.data.collections.get(collection_name_or_index)
        if not coll:
            coll = armature.data.collections.new(collection_name_or_index)

    if not coll:
        return None

    if exclusive and hasattr(bone, "collections"):
        for other_coll in list(bone.collections):
            if other_coll != coll:
                try:
                    other_coll.unassign(bone)
                except Exception:
                    pass

    try:
        coll.assign(bone)
    except Exception as e:
        print(f"[WUWA RIG] Notice assigning {bone.name} to {coll.name}: {e}")

    return coll


def move_bones_by_keyword(armature, keyword, collection_name_or_index):
    count = 0
    for bone in armature.data.bones:
        if keyword in bone.name:
            assign_bone_to_collection(armature, bone, collection_name_or_index, exclusive=True)
            lock_bone_transformations(bone, armature)
            count += 1
    return count


def get_hair_chain_length(bone):
    root = bone
    while root.parent and "Hair" in root.parent.name:
        root = root.parent
    length = 1
    current = root
    while current.children:
        hair_children = [c for c in current.children if "Hair" in c.name]
        if not hair_children:
            break
        current = hair_children[0]
        length += 1
    return length


def move_hair_bones(armature, hair1_coll="Hair 1", hair2_coll="Hair 2"):
    hair_bones = [bone for bone in armature.data.bones if "Hair" in bone.name]
    for bone in hair_bones:
        chain_length = get_hair_chain_length(bone)
        target_coll = hair2_coll if chain_length >= 4 else hair1_coll
        assign_bone_to_collection(armature, bone, target_coll, exclusive=True)
        lock_bone_transformations(bone, armature)


def get_character_meshes(armature_obj):
    """
    Returns only meshes that belong to this specific character / armature.
    Never includes objects in base 'Collection' or objects unrelated to the character (e.g. Eye Highlight, Head Origin, etc.).
    """
    if not armature_obj:
        return []

    char_meshes = []
    arm_name = armature_obj.name

    for child in armature_obj.children:
        if child.type == 'MESH' and not child.name.startswith(('WGT-', 'Highlight', 'Eye Highlight', 'Eye_Highlight', 'Sun')):
            char_meshes.append(child)

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj not in char_meshes and not obj.name.startswith(('WGT-', 'Highlight', 'Eye Highlight', 'Eye_Highlight', 'Sun')):
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object and (mod.object == armature_obj or mod.object.name == arm_name):
                    char_meshes.append(obj)
                    break

    if not char_meshes:
        for coll in armature_obj.users_collection:
            if coll.name not in ("Collection", "Master Collection", "Scene Collection"):
                for obj in coll.objects:
                    if obj.type == 'MESH' and obj not in char_meshes and not obj.name.startswith(('WGT-', 'Highlight', 'Eye Highlight', 'Eye_Highlight', 'Sun')):
                        char_meshes.append(obj)

    return char_meshes


def get_or_create_wgts_collection():
    for col in bpy.data.collections:
        if col.name.startswith("WGTS_RIG-") or col.name.startswith("WGTS"):
            return col
    wgts = bpy.data.collections.new("WGTS_RIG")
    bpy.context.scene.collection.children.link(wgts)
    wgts.hide_viewport = True
    return wgts


def create_circle_widget(name, radius=0.1, location=(0, 0, 0)):
    if name in bpy.data.objects:
        return bpy.data.objects[name]

    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    wgts_coll = get_or_create_wgts_collection()
    if obj.name not in wgts_coll.objects:
        wgts_coll.objects.link(obj)

    bm = bmesh.new()
    segments = 32
    verts = []
    for i in range(segments):
        angle = 2 * pi * i / segments
        x = cos(angle) * radius
        y = sin(angle) * radius
        verts.append(bm.verts.new((x, y, 0)))
    for i in range(segments):
        bm.edges.new((verts[i], verts[(i + 1) % segments]))
    bm.to_mesh(mesh)
    bm.free()

    obj.location = (0, 0, 0)
    obj.rotation_euler[0] = pi / 2
    obj.name = name
    return obj


def create_capsule_path(bm, radius=0.030, spacing=0.076):
    segments = 16
    left_x = -spacing / 2
    right_x = spacing / 2
    verts = []

    for i in range(segments + 1):
        angle = pi / 2 + pi * i / segments
        x = left_x + cos(angle) * radius
        y = sin(angle) * radius
        verts.append(bm.verts.new((x, y, 0)))

    for i in range(segments + 1):
        angle = -pi / 2 + pi * i / segments
        x = right_x + cos(angle) * radius
        y = sin(angle) * radius
        verts.append(bm.verts.new((x, y, 0)))

    return verts


def create_double_capsule_widget(name, inner_radius=0.030, outer_radius=0.040, spacing=0.076):
    if name in bpy.data.objects:
        return bpy.data.objects[name]

    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    wgts_coll = get_or_create_wgts_collection()
    if obj.name not in wgts_coll.objects:
        wgts_coll.objects.link(obj)
    bm = bmesh.new()

    verts_inner = create_capsule_path(bm, inner_radius, spacing)
    for i in range(len(verts_inner)):
        bm.edges.new((verts_inner[i], verts_inner[(i + 1) % len(verts_inner)]))

    verts_outer = create_capsule_path(bm, outer_radius, spacing)
    for i in range(len(verts_outer)):
        bm.edges.new((verts_outer[i], verts_outer[(i + 1) % len(verts_outer)]))

    bm.to_mesh(mesh)
    bm.free()

    obj.rotation_euler[0] = pi / 2
    obj.name = name
    return obj


def rig_wuthering_waves_character(context=None):
    """
    Main rigging function for Wuthering Waves characters using Rigify in Blender 5.2+.
    """
    if context is None:
        context = bpy.context

    obj = context.active_object
    if not obj or obj.type != 'ARMATURE' or obj.name.startswith('RIG-'):
        raw_armatures = [o for o in context.scene.objects if o.type == 'ARMATURE' and not o.name.startswith('RIG-')]
        if raw_armatures:
            obj = raw_armatures[0]
            context.view_layer.objects.active = obj
            obj.select_set(True)
        elif obj and obj.type == 'ARMATURE':
            print(f"[WUWA RIG] Armature {obj.name} is already a generated rig. Re-organizing bone collections...")
            organize_rigify_bone_collections(obj)
            return True
        else:
            armatures = [o for o in context.scene.objects if o.type == 'ARMATURE']
            if armatures:
                obj = armatures[0]
                context.view_layer.objects.active = obj
                obj.select_set(True)
            else:
                print("[WUWA RIG] Error: Select an armature first.")
                return False
    else:
        obj.select_set(True)

    # 1. Model Type & Biped Skeleton Validation
    model_prefix = obj.get("ww_model_prefix") or get_model_prefix(obj.name)

    if model_prefix in ALWAYS_BIPED_PREFIXES:
        pass
    elif model_prefix in BIPED_CHECK_PREFIXES:
        if not is_biped_skeleton(obj):
            bone_names = {b.name for b in obj.data.bones}
            missing = [n for n in REQUIRED_BIPED_BONES if n not in bone_names]
            print(f"[WUWA RIG] Warning: Non-biped skeleton. Missing: {', '.join(missing)}")
            return False
    else:
        print(f"[WUWA RIG] Info: Proceeding with armature {obj.name}")

    # 2. Fix Bone Rotation & Finger Alignment
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = obj.data.edit_bones

    finger13_exists_left = "Bip001LFinger13" in edit_bones
    finger13_exists_right = "Bip001RFinger13" in edit_bones

    def check_alignment():
        for name1, name2 in all_bone_pairs():
            if (finger13_exists_left and (name1, name2) in skip_if_finger13) or \
               (finger13_exists_right and (name1, name2) in skip_if_finger13):
                continue
            b1 = edit_bones.get(name1)
            b2 = edit_bones.get(name2)
            if b1 and b2:
                x1 = get_local_x(b1)
                x2 = get_local_x(b2)
                angle = angle_between(x1, x2)
                if angle < ALIGN_THRESHOLD:
                    return True
        return False

    def apply_adjustment():
        if "Bip001LFinger13" in edit_bones:
            outward_bones = [
                "Bip001LFinger11", "Bip001LFinger21", "Bip001LFinger31", "Bip001LFinger41",
                "Bip001RFinger11", "Bip001RFinger21", "Bip001RFinger31", "Bip001RFinger41"
            ]
            inward_bones = [
                "Bip001LFinger13", "Bip001LFinger23", "Bip001LFinger33", "Bip001LFinger43",
                "Bip001RFinger13", "Bip001RFinger23", "Bip001RFinger33", "Bip001RFinger43"
            ]
        else:
            outward_bones = [
                "Bip001LFinger1", "Bip001LFinger2", "Bip001LFinger3", "Bip001LFinger4",
                "Bip001RFinger1", "Bip001RFinger2", "Bip001RFinger3", "Bip001RFinger4"
            ]
            inward_bones = [
                "Bip001LFinger12", "Bip001LFinger22", "Bip001LFinger32", "Bip001LFinger42",
                "Bip001RFinger12", "Bip001RFinger22", "Bip001RFinger32", "Bip001RFinger42"
            ]

        for bone_name in outward_bones:
            bone = edit_bones.get(bone_name)
            if bone:
                x_axis = get_local_x(bone)
                bone.tail += x_axis * move_amount

        for bone_name in inward_bones:
            bone = edit_bones.get(bone_name)
            if bone:
                x_axis = get_local_x(bone)
                bone.tail -= x_axis * move_amount

    align_iterations = 0
    while check_alignment() and align_iterations < 200:
        apply_adjustment()
        align_iterations += 1

    bpy.ops.object.mode_set(mode='OBJECT')

    # 3. Setup Target Names & Mesh
    selected_object = context.active_object
    OrigArmature = selected_object.name
    char_base_name = extract_clean_character_name(OrigArmature)
    RigArmature = "RIG-" + char_base_name
    CharacterMesh = None

    for o in context.scene.objects:
        if o.type == 'MESH':
            for modifier in o.modifiers:
                if modifier.type == 'ARMATURE' and modifier.object and modifier.object.name == OrigArmature:
                    CharacterMesh = o
                    break
            if CharacterMesh:
                break

    try:
        bpy.ops.object.select_all(action='DESELECT')
        selected_object.select_set(True)
        context.view_layer.objects.active = selected_object
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception as e:
        print(f"[WUWA RIG] Notice applying scale: {e}")

    rig_armature_object = context.view_layer.objects.active
    if rig_armature_object and rig_armature_object.type == 'ARMATURE':
        bpy.ops.object.mode_set(mode='EDIT')
        spine_bone = rig_armature_object.data.edit_bones.get("Bip001Spine2")
        if spine_bone:
            bone_length = (spine_bone.tail - spine_bone.head).length
            if bone_length < 0.06:
                direction = spine_bone.tail - spine_bone.head
                direction.normalize()
                spine_bone.tail = spine_bone.head + direction * 0.15
                spine_bone.tail.y = spine_bone.head.y
                spine_bone.head.z += 0.03
                spine_bone.tail.z += 0.03
        bpy.ops.object.mode_set(mode='OBJECT')

    if context.object and context.object.type == 'ARMATURE':
        armature = context.object
        remove_bone_collections(armature)

        bpy.ops.object.mode_set(mode='EDIT')

        bone_pairs = [
            ('Bip001Spine1', 'Bip001Spine2'),
            ('Bip001Pelvis', 'Bip001Spine'),
            ('Bip001RThigh', 'Bip001RCalf'),
            ('Bip001LThigh', 'Bip001LCalf'),
            ('Bip001RCalf', 'Bip001RFoot'),
            ('Bip001LCalf', 'Bip001LFoot'),
            ('Bip001LUpperArm', 'Bip001LForearm'),
            ('Bip001RUpperArm', 'Bip001RForearm'),
            ('Bip001LForearm', 'Bip001LHand'),
            ('Bip001RForearm', 'Bip001RHand'),
            ('Bip001LThigh', 'Bip001LCalf'),
            ('Bip001LCalf', 'Bip001LFoot'),
            ('Bip001LFoot', 'Bip001LToe0'),
            ('Bip001RThigh', 'Bip001RCalf'),
            ('Bip001RCalf', 'Bip001RFoot'),
            ('Bip001RFoot', 'Bip001RToe0'),
        ]

        for bone1_name, bone2_name in bone_pairs:
            try:
                if bone1_name in armature.data.edit_bones and bone2_name in armature.data.edit_bones:
                    bone1 = armature.data.edit_bones[bone1_name]
                    bone2 = armature.data.edit_bones[bone2_name]
                    bone1.tail = bone2.head
            except Exception as e:
                print(f"[WUWA RIG] Notice connecting bones {bone1_name} -> {bone2_name}: {e}")

        twist_bones = {
            'Bip001RForeTwist': 'Bip001RForearm',
            'Bip001LForeTwist': 'Bip001LForearm'
        }
        for twist_bone, correct_parent in twist_bones.items():
            if twist_bone in armature.data.edit_bones and correct_parent in armature.data.edit_bones:
                bone = armature.data.edit_bones[twist_bone]
                if bone.parent != armature.data.edit_bones[correct_parent]:
                    bone.parent = armature.data.edit_bones[correct_parent]

        spine_bones = [
            'Bip001Spine', 'Bip001Spine1', 'Bip001Spine2',
            'Bip001LForearm', 'Bip001LHand', 'Bip001LFinger01',
            'Bip001LFinger02', 'Bip001LFinger11', 'Bip001LFinger12',
            'Bip001LFinger21', 'Bip001LFinger22', 'Bip001LFinger31',
            'Bip001LFinger32', 'Bip001LFinger41', 'Bip001LFinger42',
            'Bip001RForearm', 'Bip001RHand', 'Bip001RFinger01',
            'Bip001RFinger02', 'Bip001RFinger11', 'Bip001RFinger12',
            'Bip001RFinger21', 'Bip001RFinger22', 'Bip001RFinger31',
            'Bip001RFinger32', 'Bip001RFinger41', 'Bip001RFinger42',
            'Bip001LCalf', 'Bip001LFoot', 'Bip001LToe0',
            'Bip001RCalf', 'Bip001RFoot', 'Bip001RToe0',
            'Bip001Head',
            'Bip001LFinger13', 'Bip001LFinger23', 'Bip001LFinger33', 'Bip001LFinger43',
            'Bip001RFinger13', 'Bip001RFinger23', 'Bip001RFinger33', 'Bip001RFinger43',
        ]
        for bone_name in spine_bones:
            if bone_name in armature.data.edit_bones:
                armature.data.edit_bones[bone_name].use_connect = True

        bones_to_adjust_roll = [
            'Bip001Pelvis', 'Bip001Spine', 'Bip001Spine1',
            'Bip001Spine2', 'Bip001LClavicle', 'Bip001RClavicle'
        ]
        for bone_name in bones_to_adjust_roll:
            if bone_name in armature.data.edit_bones:
                armature.data.edit_bones[bone_name].roll = 0

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='POSE')

        bone_data = [
            ('Torso', 0, 1), ('Torso (Tweak)', 1, 2), ('Fingers', 2, 3), ('Fingers (Details)', 3, 4),
            ('Arm.L (IK)', 4, 5), ('Arm.R (IK)', 5, 5), ('Arm.L (FK)', 6, 6), ('Arm.R (FK)', 7, 6),
            ('Arm.L (Tweak)', 8, 7), ('Arm.R (Tweak)', 9, 7), ('Leg.L (IK)', 10, 8), ('Leg.R (IK)', 11, 8),
            ('Leg.L (FK)', 12, 9), ('Leg.R (FK)', 13, 9), ('Leg.L (Tweak)', 14, 10), ('Leg.R (Tweak)', 15, 10),
            ('Hair 1', 16, 11), ('Hair 2', 17, 11),
            ('Cloth', 18, 12), ('Skirt', 19, 12),
            ('Breast / Tail', 20, 13),
            ('Root', 21, 14),
            ('Others', 22, 15),
        ]
        process_bone_collections_and_rigify(armature, bone_data)

        move_hair_bones(armature, "Hair 1", "Hair 2")

        keywords_and_collections = [
            ("Earrings", "Hair 1"),
            ("Piao", "Cloth"),
            ("Skirt", "Skirt"), ("Trousers", "Skirt"),
            ("Tail", "Breast / Tail"), ("Chest", "Breast / Tail"),
            ("Other", "Others"), ("Weapon", "Others"), ("Prop", "Others"), ("Chibang", "Others"),
            ("Bip001Neck.001", "Others"), ("Bip001Head.001", "Others"),
            ("EyeTracker", "Torso"), ("Eye.L", "Torso"), ("Eye.R", "Torso"),
        ]
        for keyword, col_target in keywords_and_collections:
            move_bones_by_keyword(armature, keyword, col_target)

        bones_and_rig_types = [
            ('Bip001Pelvis', 'spines.basic_spine', None),
            ('Bip001LClavicle', 'basic.super_copy', 'shoulder'),
            ('Bip001RClavicle', 'basic.super_copy', 'shoulder'),
            ('Bip001LUpperArm', 'limbs.arm', None),
            ('Bip001RUpperArm', 'limbs.arm', None),
            ('Bip001LThigh', 'limbs.leg', None),
            ('Bip001RThigh', 'limbs.leg', None),
            ('Bip001RFinger0', 'limbs.super_finger', None),
            ('Bip001LFinger0', 'limbs.super_finger', None),
            ('Bip001Neck', 'basic.super_copy', 'circle'),
            ('Bip001Head', 'basic.super_copy', 'circle'),
        ]

        if 'Bip001LFinger13' in armature.pose.bones:
            bones_and_rig_types.extend([
                ('Bip001LFinger11', 'limbs.super_finger', None), ('Bip001LFinger21', 'limbs.super_finger', None),
                ('Bip001LFinger31', 'limbs.super_finger', None), ('Bip001LFinger41', 'limbs.super_finger', None),
                ('Bip001RFinger11', 'limbs.super_finger', None), ('Bip001RFinger21', 'limbs.super_finger', None),
                ('Bip001RFinger31', 'limbs.super_finger', None), ('Bip001RFinger41', 'limbs.super_finger', None),
            ])
        else:
            bones_and_rig_types.extend([
                ('Bip001LFinger1', 'limbs.super_finger', None), ('Bip001LFinger2', 'limbs.super_finger', None),
                ('Bip001LFinger3', 'limbs.super_finger', None), ('Bip001LFinger4', 'limbs.super_finger', None),
                ('Bip001RFinger1', 'limbs.super_finger', None), ('Bip001RFinger2', 'limbs.super_finger', None),
                ('Bip001RFinger3', 'limbs.super_finger', None), ('Bip001RFinger4', 'limbs.super_finger', None),
            ])

        for bone_name, rig_type, widget_type in bones_and_rig_types:
            bone = armature.pose.bones.get(bone_name)
            if bone:
                select_bone(armature.data.bones[bone_name])
                armature.data.bones.active = armature.data.bones[bone_name]
                bone.rigify_type = rig_type
                if widget_type and bone.rigify_parameters:
                    bone.rigify_parameters.super_copy_widget_type = widget_type

        bpy.ops.object.mode_set(mode='EDIT')

        def duplicate_and_adjust_heel_bone(foot_bone_name, toe_bone_name, heel_bone_name, rotation_angle=1.5708):
            try:
                if toe_bone_name in armature.data.edit_bones:
                    toe_bone = armature.data.edit_bones[toe_bone_name]
                    heel_bone = armature.data.edit_bones.new(name=heel_bone_name)
                    heel_bone.head = toe_bone.head
                    heel_bone.tail = toe_bone.tail
                    heel_bone.roll = toe_bone.roll
                    rotation_matrix = mathutils.Matrix.Rotation(rotation_angle, 4, 'Y')
                    heel_bone.tail = heel_bone.head + rotation_matrix @ (heel_bone.tail - heel_bone.head)
                    if foot_bone_name in armature.data.edit_bones:
                        foot_bone = armature.data.edit_bones[foot_bone_name]
                        foot_head_y = foot_bone.head[1]
                        heel_bone.head[1] = foot_head_y
                        heel_bone.tail[1] = foot_head_y
                    heel_bone.parent = armature.data.edit_bones[foot_bone_name]
            except Exception as e:
                print(f"[WUWA RIG] Notice heel bone {heel_bone_name}: {e}")

        duplicate_and_adjust_heel_bone('Bip001LFoot', 'Bip001LToe0', 'Bip001LHeel0', rotation_angle=1.5708)
        duplicate_and_adjust_heel_bone('Bip001RFoot', 'Bip001RToe0', 'Bip001RHeel0', rotation_angle=-1.5708)

        bpy.ops.object.mode_set(mode='OBJECT')

        # 4. Rename bones to Rigify standards
        bpy.ops.object.mode_set(mode='EDIT')
        name_mapping = {
            "Bip001Neck": "neck", "Bip001Head": "head", "Bip001Clavicle": "shoulder",
            "Bip001UpperArm": "upper_arm", "Bip001Forearm": "forearm", "Bip001Hand": "hand",
            "Bip001Thigh": "thigh", "Bip001Calf": "shin", "Bip001Foot": "foot", "Bip001Toe0": "toe_ik",
            "Bip001Spine": "Spine", "Bip001Spine1": "Spine1", "Bip001Spine2": "Spine2", "Bip001Pelvis": "Pelvis",
            "Bip001Finger0": "thumb.01", "Bip001Finger01": "thumb.02", "Bip001Finger02": "thumb.03",
        }

        if finger13_exists_left or finger13_exists_right:
            name_mapping.update({
                "Bip001Finger11": "f_index.01", "Bip001Finger12": "f_index.02", "Bip001Finger13": "f_index.03",
                "Bip001Finger21": "f_middle.01", "Bip001Finger22": "f_middle.02", "Bip001Finger23": "f_middle.03",
                "Bip001Finger31": "f_ring.01", "Bip001Finger32": "f_ring.02", "Bip001Finger33": "f_ring.03",
                "Bip001Finger41": "f_pinky.01", "Bip001Finger42": "f_pinky.02", "Bip001Finger43": "f_pinky.03",
            })
        else:
            name_mapping.update({
                "Bip001Finger1": "f_index.01", "Bip001Finger11": "f_index.02", "Bip001Finger12": "f_index.03",
                "Bip001Finger2": "f_middle.01", "Bip001Finger21": "f_middle.02", "Bip001Finger22": "f_middle.03",
                "Bip001Finger3": "f_ring.01", "Bip001Finger31": "f_ring.02", "Bip001Finger32": "f_ring.03",
                "Bip001Finger4": "f_pinky.01", "Bip001Finger41": "f_pinky.02", "Bip001Finger42": "f_pinky.03",
            })

        final_renames = {}
        current_bones = list(armature.data.edit_bones)

        for bone in current_bones:
            original_name = bone.name
            new_name = original_name

            if new_name.startswith("Bip001R") and not new_name.endswith(".R"):
                new_name += ".R"
            elif new_name.startswith("Bip001L") and not new_name.endswith(".L"):
                new_name += ".L"

            base_name_check = new_name
            suffix = ""
            if base_name_check.endswith(".L"):
                base_name_check = base_name_check[:-2]; suffix = ".L"
            elif base_name_check.endswith(".R"):
                base_name_check = base_name_check[:-2]; suffix = ".R"

            if base_name_check.startswith("Bip001R"):
                base_name_check = base_name_check.replace("Bip001R", "Bip001", 1)
            elif base_name_check.startswith("Bip001L"):
                base_name_check = base_name_check.replace("Bip001L", "Bip001", 1)

            if base_name_check in name_mapping:
                new_name = name_mapping[base_name_check] + suffix
            else:
                if base_name_check != original_name:
                    if new_name.startswith("Bip001L") or new_name.startswith("Bip001R"):
                        new_name = base_name_check + suffix

            if new_name != original_name:
                final_renames[original_name] = new_name

        for old_name, new_name in final_renames.items():
            if old_name in armature.data.edit_bones:
                armature.data.edit_bones[old_name].name = new_name

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        context.view_layer.objects.active = armature
        context.view_layer.update()

        bpy.ops.object.mode_set(mode='POSE')
        for bone in armature.pose.bones:
            for key in list(bone.keys()):
                if key.startswith("_"):
                    continue
                val = bone[key]
                if isinstance(val, str) and val in final_renames:
                    bone[key] = final_renames[val]

        # 5. Generate Rigify Rig
        orig_obj_names = set(bpy.data.objects.keys())
        generation_success = False
        try:
            from rigify.generate import generate_rig
            generate_rig(context, armature)
            generation_success = True
        except Exception as e1:
            print(f"[WUWA RIG] Direct generate_rig notice: {e1}")
            try:
                bpy.ops.pose.rigify_generate()
                generation_success = True
            except Exception as e2:
                try:
                    bpy.ops.armature.rigify_generate()
                    generation_success = True
                except Exception as e3:
                    print(f"[WUWA RIG] Rigify generation failed: {e1}, {e2}, {e3}")
                    return False

    # 6. Post Generation Setup
    bpy.ops.object.mode_set(mode='OBJECT')

    new_armatures = [
        bpy.data.objects[name] for name in bpy.data.objects.keys()
        if name not in orig_obj_names and bpy.data.objects[name].type == 'ARMATURE'
    ]
    if new_armatures:
        RigArmatureObj = new_armatures[0]
    else:
        RigArmatureObj = bpy.data.objects.get(RigArmature) or bpy.data.objects.get(f"RIG-{OrigArmature}") or bpy.data.objects.get("rig") or bpy.data.objects.get("rigify") or context.active_object

    if RigArmatureObj and RigArmatureObj.type == 'ARMATURE':
        if RigArmatureObj.name != RigArmature:
            RigArmatureObj.name = RigArmature
        if RigArmatureObj.data:
            RigArmatureObj.data.name = RigArmature
        try:
            from setup_wizard.ui.character_settings_utils import stamp_rig_game
            stamp_rig_game(RigArmatureObj, "WUTHERING_WAVES", char_base_name if 'char_base_name' in locals() else None)
        except Exception:
            pass

        # Link RigArmatureObj to character's collection (e.g. Chun) and move scene objects into character collection
        orig_arm_obj = bpy.data.objects.get(OrigArmature) or armature
        char_collection = None
        if orig_arm_obj:
            for coll in orig_arm_obj.users_collection:
                if coll.name not in ("Collection", "Master Collection", "Scene Collection"):
                    char_collection = coll
                    break
        if not char_collection and char_base_name:
            char_collection = bpy.data.collections.get(char_base_name)

        if char_collection:
            if RigArmatureObj.name not in char_collection.objects:
                char_collection.objects.link(RigArmatureObj)
            for c in list(RigArmatureObj.users_collection):
                if c != char_collection and not c.name.startswith("WGTS"):
                    try:
                        c.objects.unlink(RigArmatureObj)
                    except Exception:
                        pass

            # Move all objects from default 'Collection' into the character's collection
            main_coll = bpy.data.collections.get("Collection")
            if main_coll and main_coll != char_collection:
                for child_c in list(main_coll.children):
                    if child_c != char_collection:
                        if child_c.name not in context.scene.collection.children:
                            context.scene.collection.children.link(child_c)
                        try:
                            main_coll.children.unlink(child_c)
                        except Exception:
                            pass
                for obj_c in list(main_coll.objects):
                    if obj_c.name not in char_collection.objects:
                        char_collection.objects.link(obj_c)
                    try:
                        main_coll.objects.unlink(obj_c)
                    except Exception:
                        pass
                try:
                    context.scene.collection.children.unlink(main_coll)
                except Exception:
                    pass
                try:
                    bpy.data.collections.remove(main_coll, do_unlink=True)
                except Exception:
                    pass

        # Delete rogue Cube objects and duplicate .001 control objects
        for obj in list(bpy.data.objects):
            if obj.name.lower().startswith("cube") and obj.type == 'MESH':
                if not any(k in obj.name.lower() for k in ["body", "cloth", "face", "hair", "eye", "head"]):
                    try:
                        bpy.data.objects.remove(obj, do_unlink=True)
                    except Exception:
                        pass

        for base_name in ['Head Origin', 'Head Forward', 'Head Up', 'Light Direction', 'Sun', 'Eye Highlight', 'Highlight Top', 'Highlight Bottom']:
            orig_obj = bpy.data.objects.get(base_name)
            for obj in list(bpy.data.objects):
                if obj != orig_obj and (obj.name.startswith(f"{base_name}.") or (base_name.lower() in obj.name.lower() and ('.00' in obj.name or '.01' in obj.name))):
                    try:
                        bpy.data.objects.remove(obj, do_unlink=True)
                    except Exception:
                        pass

        # Clear any constraints on scene empties (Head Origin, Light Direction) so they remain untouched
        for obj_name in ["Head Origin", "Head Driver", "Light Direction", "Main Light", "Main Light Direction"]:
            empty_obj = bpy.data.objects.get(obj_name)
            if empty_obj:
                for con in list(empty_obj.constraints):
                    if con.type == "CHILD_OF":
                        empty_obj.constraints.remove(con)

        bpy.ops.object.select_all(action='DESELECT')
        RigArmatureObj.select_set(True)
        context.view_layer.objects.active = RigArmatureObj
        bpy.ops.object.mode_set(mode='POSE')

        # Adjust Neck/Head Custom Shapes
        pose_bone_neck = RigArmatureObj.pose.bones.get("neck")
        if pose_bone_neck:
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bone_neck = RigArmatureObj.data.edit_bones.get("neck")
            neck_length = (edit_bone_neck.tail - edit_bone_neck.head).length / 2 if edit_bone_neck else 0.1
            bpy.ops.object.mode_set(mode='POSE')
            pose_bone_neck.custom_shape_translation.y = neck_length
            pose_bone_neck.custom_shape_scale_xyz = (1.5, 1.5, 1.5)

        pose_bone_head = RigArmatureObj.pose.bones.get("head")
        if pose_bone_head:
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bone_head = RigArmatureObj.data.edit_bones.get("head")
            head_length = (edit_bone_head.tail - edit_bone_head.head).length if edit_bone_head else 0.1
            bpy.ops.object.mode_set(mode='POSE')
            pose_bone_head.custom_shape_translation.y = head_length * 1.2
            pose_bone_head.custom_shape_scale_xyz = (2, 2, 2)

        bpy.ops.object.mode_set(mode='OBJECT')

        # IK Stretch & Parents
        for side in [".L", ".R"]:
            b_name = "upper_arm_parent" + side
            if b_name in RigArmatureObj.pose.bones:
                RigArmatureObj.pose.bones[b_name]["IK_Stretch"] = 0.000
                RigArmatureObj.pose.bones[b_name]["IK_parent"] = 4
                RigArmatureObj.pose.bones[b_name]["pole_parent"] = 2

        for b_name in ["thigh_parent.L", "thigh_parent.R"]:
            if b_name in RigArmatureObj.pose.bones:
                RigArmatureObj.pose.bones[b_name]["IK_Stretch"] = 0.000

        # ORG Deform
        context.view_layer.objects.active = RigArmatureObj
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in RigArmatureObj.data.edit_bones:
            if bone.name.startswith('ORG-'):
                bone.use_deform = True
        bpy.ops.object.mode_set(mode='OBJECT')

        # Mesh updates - only for meshes belonging to this character/armature
        bpy.ops.object.select_all(action='DESELECT')
        char_meshes = get_character_meshes(bpy.data.objects.get(OrigArmature) or armature)
        if not char_meshes and CharacterMesh:
            char_meshes = [CharacterMesh]

        # Weight transfer mapping
        weight_mappings = {
            "ORG-Bip001UpArmTwist.L": "DEF-upper_arm.L", "ORG-Bip001UpArmTwist1.L": "DEF-upper_arm.L",
            "ORG-Bip001UpArmTwist2.L": "DEF-upper_arm.L.001", "ORG-upper_arm.L": "DEF-upper_arm.L.001",
            "ORG-forearm.L": "DEF-forearm.L", "ORG-Bip001ForeTwist.L": "DEF-forearm.L.001",
            "ORG-Bip001ForeTwist1.L": "DEF-forearm.L.001", "ORG-Bone_HandTwist_L": "DEF-forearm.L.001",
            "ORG-Bip001ForeTwist2.L": "DEF-forearm.L.001", "ORG-Bip001_L_Elbow_F": "DEF-upper_arm.L.001",
            "ORG-Bip001_L_Elbow_B": "DEF-upper_arm.L.001",
            "ORG-Bip001UpArmTwist.R": "DEF-upper_arm.R", "ORG-Bip001UpArmTwist1.R": "DEF-upper_arm.R",
            "ORG-Bip001UpArmTwist2.R": "DEF-upper_arm.R.001", "ORG-upper_arm.R": "DEF-upper_arm.R.001",
            "ORG-forearm.R": "DEF-forearm.R", "ORG-Bip001ForeTwist.R": "DEF-forearm.R.001",
            "ORG-Bip001ForeTwist1.R": "DEF-forearm.R.001", "ORG-Bone_HandTwist_R": "DEF-forearm.R.001",
            "ORG-Bip001ForeTwist2.R": "DEF-forearm.R.001", "ORG-Bip001_R_Elbow_F": "DEF-upper_arm.R.001",
            "ORG-Bip001_R_Elbow_B": "DEF-upper_arm.R.001",
            "ORG-Bip001ThighTwist.L": "DEF-thigh.L", "ORG-thigh.L": "DEF-thigh.L.001",
            "ORG-Bip001_L_Calf": "DEF-shin.L", "ORG-Bip001_L_Knee_B": "DEF-thigh.L.001",
            "ORG-Bip001_L_Knee_F": "DEF-thigh.L.001", "ORG-Bip001ThighTwist1.L": "DEF-thigh.L",
            "ORG-Bip001_L_CalfTwist": "DEF-shin.L.001",
            "ORG-Bip001ThighTwist.R": "DEF-thigh.R", "ORG-thigh.R": "DEF-thigh.R.001",
            "ORG-Bip001_R_Calf": "DEF-shin.R", "ORG-Bip001_R_Knee_B": "DEF-thigh.R.001",
            "ORG-Bip001_R_Knee_F": "DEF-thigh.R.001", "ORG-Bip001ThighTwist1.R": "DEF-thigh.R",
            "ORG-Bip001_R_CalfTwist": "DEF-shin.R.001",
        }

        for m_obj in char_meshes:
            for group in m_obj.vertex_groups:
                if not group.name.startswith("ORG-") and not group.name.startswith("DEF-") and not group.name.startswith("MCH-"):
                    group.name = "ORG-" + group.name

            vgroups = m_obj.vertex_groups
            for source, target in weight_mappings.items():
                if source in vgroups:
                    src_grp = vgroups[source]
                    if target not in vgroups:
                        tgt_grp = vgroups.new(name=target)
                    else:
                        tgt_grp = vgroups[target]

                    for vert in m_obj.data.vertices:
                        w = 0.0
                        has_w = False
                        for g in vert.groups:
                            if g.group == src_grp.index:
                                w += g.weight
                                has_w = True
                                break
                        if has_w:
                            for g in vert.groups:
                                if g.group == tgt_grp.index:
                                    w += g.weight
                                    break
                            tgt_grp.add([vert.index], w, 'REPLACE')
                            src_grp.remove([vert.index])

            for modifier in m_obj.modifiers:
                if modifier.type == 'ARMATURE' and (not modifier.object or modifier.object.name == OrigArmature or modifier.object == RigArmatureObj):
                    modifier.object = RigArmatureObj

            m_obj.parent = RigArmatureObj
            m_obj.matrix_parent_inverse = RigArmatureObj.matrix_world.inverted()

            # Handle SEETHRU mesh reparenting if present
            seethru_mesh_name = m_obj.name + "_SEETHRU"
            seethru_mesh = bpy.data.objects.get(seethru_mesh_name)
            if seethru_mesh:
                seethru_mesh.parent = RigArmatureObj
                seethru_mesh.matrix_parent_inverse = RigArmatureObj.matrix_world.inverted()
                for modifier in seethru_mesh.modifiers:
                    if modifier.type == 'ARMATURE':
                        modifier.object = RigArmatureObj
                for group in seethru_mesh.vertex_groups:
                    if not group.name.startswith("ORG-"):
                        group.name = "ORG-" + group.name

        # Find eye mesh (mesh with Eye material or shape keys)
        eye_mesh = CharacterMesh
        if not (eye_mesh and eye_mesh.data and eye_mesh.data.shape_keys and any("Eye" in slot.name for slot in eye_mesh.material_slots)):
            for o in char_meshes:
                if o.data and o.data.shape_keys and any("Eye" in slot.name for slot in o.material_slots):
                    eye_mesh = o
                    break
        if not eye_mesh and CharacterMesh:
            eye_mesh = CharacterMesh

        # Secondary Shape Keys (Pupil)
        source_shape_keys = ["Pupil_R", "Pupil_L", "Pupil_Up", "Pupil_Down"]
        target_material_name = None
        if eye_mesh:
            for slot in eye_mesh.material_slots:
                if "Eye" in slot.name:
                    target_material_name = slot.name
                    break

        offset_connected = Vector((0.0, -0.001, 0.0))
        offset_unconnected = Vector((0.0, 0.001, 0.0))

        if eye_mesh and eye_mesh.data.shape_keys and target_material_name:
            CharacterMesh = eye_mesh
            keys = CharacterMesh.data.shape_keys.key_blocks
            basis = CharacterMesh.data.shape_keys.reference_key

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            CharacterMesh.select_set(True)
            context.view_layer.objects.active = CharacterMesh

            mat_slots = CharacterMesh.material_slots
            relevant_face_vert_indices = set()
            for poly in CharacterMesh.data.polygons:
                if poly.material_index < len(mat_slots) and mat_slots[poly.material_index].name == target_material_name:
                    relevant_face_vert_indices.update(poly.vertices)

            if relevant_face_vert_indices:
                connectivity = defaultdict(set)
                for poly in CharacterMesh.data.polygons:
                    if poly.material_index < len(mat_slots) and mat_slots[poly.material_index].name == target_material_name:
                        verts = poly.vertices
                        for i in range(len(verts)):
                            for j in range(i + 1, len(verts)):
                                vi, vj = verts[i], verts[j]
                                if vi in relevant_face_vert_indices and vj in relevant_face_vert_indices:
                                    connectivity[vi].add(vj)
                                    connectivity[vj].add(vi)

                seed_vertices = {v for v, linked in connectivity.items() if len(linked) > 10}
                connected_vertices = set()
                visited = set()
                for seed in seed_vertices:
                    queue = deque([(seed, 0)])
                    visited.add(seed)
                    connected_vertices.add(seed)
                    while queue:
                        current, depth = queue.popleft()
                        if depth >= NEIGHBOR_DEPTH:
                            continue
                        for neighbor in connectivity[current]:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                connected_vertices.add(neighbor)
                                queue.append((neighbor, depth + 1))

                for source_name in source_shape_keys:
                    if source_name not in keys:
                        continue
                    source_key = keys[source_name]
                    index = next(i for i, k in enumerate(keys) if k.name == source_key.name)
                    CharacterMesh.active_shape_key_index = index

                    bpy.ops.object.shape_key_add(from_mix=False)
                    key_L = CharacterMesh.data.shape_keys.key_blocks[-1]
                    key_L.name = f"{source_name}.L"

                    bpy.ops.object.shape_key_add(from_mix=False)
                    key_R = CharacterMesh.data.shape_keys.key_blocks[-1]
                    key_R.name = f"{source_name}.R"

                    for i in relevant_face_vert_indices:
                        base_co = basis.data[i].co
                        source_co = source_key.data[i].co
                        delta = source_co - base_co
                        offset = offset_connected if i in connected_vertices else offset_unconnected

                        if base_co.x >= 0:
                            key_L.data[i].co = base_co + delta * 2 + offset
                        else:
                            key_R.data[i].co = base_co + delta * 2 + offset

                    bpy.ops.object.select_all(action='DESELECT')

            # Eye Tracker Bone Creation
            context.view_layer.objects.active = RigArmatureObj
            bpy.ops.object.mode_set(mode='EDIT')
            target_bone = RigArmatureObj.data.edit_bones.get("ORG-head")
            if target_bone:
                new_bone = RigArmatureObj.data.edit_bones.new("EyeTracker")
                new_bone.head = target_bone.head.copy()
                new_bone.head.y -= 0.10
                new_bone.head.z += 0.03
                new_bone.tail = new_bone.head + Vector((0, 0, 0.03))
                new_bone.parent = target_bone
                new_bone.use_connect = False

                et_head = new_bone.head
                y_off = new_bone.tail.y - new_bone.head.y
                z_off = new_bone.tail.z - new_bone.head.z

                eye_l = RigArmatureObj.data.edit_bones.new("Eye.L")
                eye_l.head = et_head + Vector((0.03, 0, 0))
                eye_l.tail = eye_l.head + Vector((0, y_off, z_off))
                eye_l.parent = new_bone
                eye_l.use_connect = False

                eye_r = RigArmatureObj.data.edit_bones.new("Eye.R")
                eye_r.head = et_head + Vector((-0.03, 0, 0))
                eye_r.tail = eye_r.head + Vector((0, y_off, z_off))
                eye_r.parent = new_bone
                eye_r.use_connect = False

            bpy.ops.object.mode_set(mode='OBJECT')

            # Custom Shapes / Widgets
            create_circle_widget("WGT-rig_eye.L", radius=0.1, location=(-0.3, 0, 0))
            create_circle_widget("WGT-rig_eye.R", radius=0.1, location=(0.3, 0, 0))
            create_double_capsule_widget("WGT-rig_eyes", inner_radius=0.14, outer_radius=0.17, spacing=0.6)

            context.view_layer.objects.active = RigArmatureObj
            bpy.ops.object.mode_set(mode='POSE')
            custom_shapes = {"EyeTracker": "WGT-rig_eyes", "Eye.L": "WGT-rig_eye.L", "Eye.R": "WGT-rig_eye.R"}
            for b_name, s_name in custom_shapes.items():
                if b_name in RigArmatureObj.pose.bones and s_name in bpy.data.objects:
                    RigArmatureObj.pose.bones[b_name].custom_shape = bpy.data.objects[s_name]
                    RigArmatureObj.pose.bones[b_name].custom_shape_scale_xyz = (4.0, 4.0, 4.0)

            # Drivers for Pupils
            if CharacterMesh and CharacterMesh.data and CharacterMesh.data.shape_keys:
                shape_key_names = {
                    "Pupil_L": "LOC_X", "Pupil_R": "LOC_X",
                    "Pupil_Up": "LOC_Y", "Pupil_Down": "LOC_Y"
                }
                expressions = {
                    "Pupil_L": 'max(min((bone_x * 10), 1), 0) if bone_x > 0 else 0',
                    "Pupil_R": 'max(min((-bone_x * 10), 1), 0) if bone_x < 0 else 0',
                    "Pupil_Up": 'max(min((bone_y * 10), 1), 0) if bone_y > 0 else 0',
                    "Pupil_Down": 'max(min((-bone_y * 10), 1), 0) if bone_y < 0 else 0'
                }

                for shape_key_name, transform_axis in shape_key_names.items():
                    if shape_key_name in CharacterMesh.data.shape_keys.key_blocks:
                        shape_key = CharacterMesh.data.shape_keys.key_blocks[shape_key_name]
                        try:
                            shape_key.driver_remove('value')
                        except Exception:
                            pass
                        driver = shape_key.driver_add('value').driver
                        driver.type = 'SCRIPTED'
                        var = driver.variables.new()
                        var.name = 'bone_' + transform_axis[-1].lower()
                        var.type = 'TRANSFORMS'
                        var.targets[0].id = RigArmatureObj
                        var.targets[0].bone_target = "EyeTracker"
                        var.targets[0].transform_type = transform_axis
                        var.targets[0].transform_space = 'LOCAL_SPACE'
                        driver.expression = expressions[shape_key_name]

            # Pupil Scale Driver
            if CharacterMesh and CharacterMesh.data and CharacterMesh.data.shape_keys and "Pupil_Scale" in CharacterMesh.data.shape_keys.key_blocks:
                shape_key = CharacterMesh.data.shape_keys.key_blocks["Pupil_Scale"]
                try:
                    shape_key.driver_remove('value')
                except Exception:
                    pass
                driver = shape_key.driver_add('value').driver
                driver.type = 'SCRIPTED'
                var = driver.variables.new()
                var.name = 'bone_scale'
                var.type = 'TRANSFORMS'
                var.targets[0].id = RigArmatureObj
                var.targets[0].bone_target = "EyeTracker"
                var.targets[0].transform_type = 'SCALE_Y'
                var.targets[0].transform_space = 'LOCAL_SPACE'
                driver.expression = 'max(min((1.0 - bone_scale), 1.0), -1.0)'

            # Left and Right Eye Independent Combined Drivers
            if CharacterMesh and CharacterMesh.data and CharacterMesh.data.shape_keys:
                side_driver_map = {
                    "Pupil_L.L": ("Eye.L", "+X"),
                    "Pupil_R.L": ("Eye.L", "-X"),
                    "Pupil_Up.L": ("Eye.L", "+Y"),
                    "Pupil_Down.L": ("Eye.L", "-Y"),
                    "Pupil_L.R": ("Eye.R", "+X"),
                    "Pupil_R.R": ("Eye.R", "-X"),
                    "Pupil_Up.R": ("Eye.R", "+Y"),
                    "Pupil_Down.R": ("Eye.R", "-Y"),
                }
                for sk_name, (indep_bone, dir_axis) in side_driver_map.items():
                    if sk_name in CharacterMesh.data.shape_keys.key_blocks:
                        shape_key = CharacterMesh.data.shape_keys.key_blocks[sk_name]
                        try:
                            shape_key.driver_remove('value')
                        except Exception:
                            pass
                        driver = shape_key.driver_add('value').driver
                        driver.type = 'SCRIPTED'

                        axis = 'LOC_' + dir_axis[1]
                        v_master = driver.variables.new()
                        v_master.name = "v_m"
                        v_master.type = 'TRANSFORMS'
                        v_master.targets[0].id = RigArmatureObj
                        v_master.targets[0].bone_target = "EyeTracker"
                        v_master.targets[0].transform_type = axis
                        v_master.targets[0].transform_space = 'LOCAL_SPACE'

                        v_indep = driver.variables.new()
                        v_indep.name = "v_i"
                        v_indep.type = 'TRANSFORMS'
                        v_indep.targets[0].id = RigArmatureObj
                        v_indep.targets[0].bone_target = indep_bone
                        v_indep.targets[0].transform_type = axis
                        v_indep.targets[0].transform_space = 'LOCAL_SPACE'

                        sign = "+" if dir_axis[0] == "+" else "-"
                        driver.expression = f"max(min(({sign}(v_m + v_i) * 10.0), 1.0), 0.0)"

            bpy.ops.object.mode_set(mode='OBJECT')

            # Move Widgets to per-character WGTS_<Char> nested in char collection (Append-safe)
            try:
                from setup_wizard.character_rig_setup.wgts_isolation import isolate_wgts_for_character
                _char_coll = char_collection if 'char_collection' in locals() else None
                _char_name = char_base_name if 'char_base_name' in locals() else None
                isolate_wgts_for_character(RigArmatureObj, _char_name, _char_coll)
            except Exception as e_wgts:
                print(f"[WUWA RIG] WGTS isolation notice: {e_wgts}")
                wgts_collection = None
                for col in bpy.data.collections:
                    if col.name.startswith("WGTS_RIG-") or col.name.startswith("WGTS"):
                        wgts_collection = col
                        break
                if not wgts_collection:
                    wgts_collection = bpy.data.collections.new("WGTS_Custom")
                    context.scene.collection.children.link(wgts_collection)

                for n in ["WGT-rig_eyes", "WGT-rig_eye.R", "WGT-rig_eye.L"]:
                    o = bpy.data.objects.get(n)
                    if o:
                        if o.name not in wgts_collection.objects:
                            wgts_collection.objects.link(o)
                        for col in list(o.users_collection):
                            if col != wgts_collection:
                                col.objects.unlink(o)

                wgts_collection.hide_viewport = True

            # IK Pole property
            ik_pole_targets = ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.L", "thigh_parent.R"]
            for b_name in ik_pole_targets:
                bone = RigArmatureObj.pose.bones.get(b_name)
                if bone and "pole_vector" in bone:
                    bone["pole_vector"] = True
            # Themes for Eye controls (All red THEME01)
            theme_assignments = {"EyeTracker": "THEME01", "Eye.L": "THEME01", "Eye.R": "THEME01"}
            for b_name, theme in theme_assignments.items():
                bone = RigArmatureObj.pose.bones.get(b_name)
                if bone and hasattr(bone, "color"):
                    bone.color.palette = theme

            # Create FK toe bones (toe_fk.L/R)
            bpy.ops.object.mode_set(mode='EDIT')
            arm = RigArmatureObj.data
            for side in ['.L', '.R']:
                org_toe = arm.edit_bones.get(f'ORG-toe_ik{side}')
                foot_fk = arm.edit_bones.get(f'foot_fk{side}')
                if org_toe and foot_fk:
                    new_bone = arm.edit_bones.new(f'toe_fk{side}')
                    new_bone.head = org_toe.head.copy()
                    new_bone.tail = org_toe.tail.copy()
                    new_bone.roll = org_toe.roll
                    new_bone.parent = foot_fk
                    new_bone.use_connect = True
            bpy.ops.object.mode_set(mode='POSE')

            foot_fk_l = RigArmatureObj.pose.bones.get('foot_fk.L')
            for side in ['.L', '.R']:
                toe_fk = RigArmatureObj.pose.bones.get(f'toe_fk{side}')
                if toe_fk and foot_fk_l:
                    toe_fk.custom_shape = foot_fk_l.custom_shape
                    if hasattr(toe_fk, "color"):
                        toe_fk.color.palette = 'THEME03'

            for side in ['.L', '.R']:
                toe_fk_bone = RigArmatureObj.pose.bones.get(f'toe_fk{side}')
                org_toe = RigArmatureObj.pose.bones.get(f'ORG-toe_ik{side}')
                toe_ik_bone = RigArmatureObj.pose.bones.get(f'toe_ik{side}')
                thigh_parent = RigArmatureObj.pose.bones.get(f'thigh_parent{side}')

                if toe_fk_bone and org_toe and thigh_parent and toe_ik_bone:
                    for con in org_toe.constraints:
                        if con.type == 'COPY_TRANSFORMS' and con.subtarget == f'toe_ik{side}':
                            ik_driver = con.driver_add('influence').driver
                            ik_driver.type = 'SCRIPTED'
                            ik_var = ik_driver.variables.new()
                            ik_var.name = 'ik_fk'
                            ik_var.type = 'SINGLE_PROP'
                            ik_var.targets[0].id = RigArmatureObj
                            ik_var.targets[0].data_path = f'pose.bones["thigh_parent{side}"]["IK_FK"]'
                            ik_driver.expression = '1 - ik_fk'
                            break

                    fk_constraint = org_toe.constraints.new('COPY_ROTATION')
                    fk_constraint.name = 'Copy Rotation FK'
                    fk_constraint.target = RigArmatureObj
                    fk_constraint.subtarget = f'toe_fk{side}'
                    fk_constraint.target_space = 'LOCAL'
                    fk_constraint.owner_space = 'LOCAL'

                    driver = fk_constraint.driver_add('influence').driver
                    driver.type = 'SCRIPTED'
                    var = driver.variables.new()
                    var.name = 'ik_fk'
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = RigArmatureObj
                    var.targets[0].data_path = f'pose.bones["thigh_parent{side}"]["IK_FK"]'
                    driver.expression = 'ik_fk'

            # Move toe_fk bones to FK leg collections
            assign_bone_to_collection(RigArmatureObj, 'toe_fk.L', 'Leg.L (FK)')
            assign_bone_to_collection(RigArmatureObj, 'toe_fk.R', 'Leg.R (FK)')

            # Neck Tweak
            bpy.ops.object.mode_set(mode='EDIT')
            arm = RigArmatureObj.data
            if 'ORG-Bip001Neck' in arm.edit_bones:
                arm.edit_bones['ORG-Bip001Neck'].name = 'Bip001Neck'
            if 'ORG-Bip001Head' in arm.edit_bones:
                arm.edit_bones['ORG-Bip001Head'].name = 'Bip001Head'

            if 'Bip001Neck' in arm.edit_bones:
                neck_bone = arm.edit_bones['Bip001Neck']
                new_bone = arm.edit_bones.new('Bip001Neck._fk')
                new_bone.head = neck_bone.head.copy()
                new_bone.tail = neck_bone.tail.copy()
                new_bone.roll = neck_bone.roll
                new_bone.parent = neck_bone.parent
                rot_mat = mathutils.Matrix.Rotation(-1.5708, 4, 'X')
                new_bone.tail = new_bone.head + rot_mat @ (new_bone.tail - new_bone.head)
                new_bone.tail.z = new_bone.head.z
                new_bone.tail = new_bone.head + (new_bone.tail - new_bone.head).normalized() * 0.05
                neck_bone.use_connect = False
                neck_bone.parent = new_bone

            if 'Bip001Head' in arm.edit_bones:
                head_bone = arm.edit_bones['Bip001Head']
                new_bone = arm.edit_bones.new('Bip001Head._fk')
                new_bone.head = head_bone.head.copy()
                new_bone.tail = head_bone.tail.copy()
                new_bone.roll = head_bone.roll
                new_bone.parent = head_bone.parent
                rot_mat = mathutils.Matrix.Rotation(-1.5708, 4, 'X')
                new_bone.tail = new_bone.head + rot_mat @ (new_bone.tail - new_bone.head)
                new_bone.tail.z = new_bone.head.z
                new_bone.tail = new_bone.head + (new_bone.tail - new_bone.head).normalized() * 0.05
                head_bone.use_connect = False
                head_bone.parent = new_bone

            bpy.ops.object.mode_set(mode='POSE')
            spine2_fk = RigArmatureObj.pose.bones.get("Spine2_fk")
            if "Bip001Neck._fk" in RigArmatureObj.pose.bones:
                tb = RigArmatureObj.pose.bones["Bip001Neck._fk"]
                if spine2_fk:
                    tb.custom_shape = spine2_fk.custom_shape
                tb.custom_shape_transform = RigArmatureObj.pose.bones.get("Bip001Neck")
            if "Bip001Head._fk" in RigArmatureObj.pose.bones:
                tb = RigArmatureObj.pose.bones["Bip001Head._fk"]
                if spine2_fk:
                    tb.custom_shape = spine2_fk.custom_shape
                tb.custom_shape_transform = RigArmatureObj.pose.bones.get("Bip001Head")

            assign_bone_to_collection(RigArmatureObj, 'Bip001Neck', 'Torso')
            assign_bone_to_collection(RigArmatureObj, 'Bip001Head', 'Torso')
            assign_bone_to_collection(RigArmatureObj, 'Bip001Neck._fk', 'Torso (Tweak)')
            assign_bone_to_collection(RigArmatureObj, 'Bip001Head._fk', 'Torso (Tweak)')

            # Final cleanups
            bpy.ops.object.mode_set(mode='OBJECT')
            RigArmatureObj.data.display_type = 'STICK'
            RigArmatureObj.data.show_bone_custom_shapes = True
            RigArmatureObj.show_in_front = True

            # Ensure character meshes maintain proper armature modifier and parenting
            for m_obj in char_meshes:
                for mod in m_obj.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = RigArmatureObj
                m_obj.parent = RigArmatureObj
                m_obj.matrix_parent_inverse = RigArmatureObj.matrix_world.inverted()

            # Create breast circle controls for character
            create_wuwa_breast_controls(RigArmatureObj)

            # First organize Rigify collections and UI
            clean_name = extract_clean_character_name(OrigArmature)
            organize_rigify_bone_collections(RigArmatureObj, orig_arm_name=OrigArmature, char_name=clean_name)

            # Then build Face Rig controls, drivers and widgets
            try:
                from setup_wizard.character_rig_setup.wuwa_face_panel import wuwa_face_rig_main
                wuwa_face_rig_main(RigArmatureObj)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[WUWA FACE RIG] Notice: {e}")

            # Ensure Face collection is visible
            if hasattr(RigArmatureObj.data, "collections"):
                for fc in ["Face", "Face (Primary)"]:
                    if fc in RigArmatureObj.data.collections:
                        RigArmatureObj.data.collections[fc].is_visible = True

            # Apply Hair & Clothes physics if enabled in setup settings
            props = getattr(context.scene, "character_rigger_props", None)
            enable_physics = False
            if props:
                enable_physics = getattr(props, "enable_hair_clothes_physics", getattr(props, "enable_hair_dress_physics", False))
            if not enable_physics:
                enable_physics = getattr(context.scene, "enable_hair_clothes_physics", getattr(context.scene, "enable_hair_dress_physics", False))

            if enable_physics and RigArmatureObj:
                from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics
                apply_hair_and_clothes_physics(RigArmatureObj, context)

            orig_arm = bpy.data.objects.get(OrigArmature)
            if orig_arm and orig_arm != RigArmatureObj:
                try:
                    bpy.data.objects.remove(orig_arm, do_unlink=True)
                except Exception:
                    pass

    return True


def create_breast_widget_for_bone(name, bone_matrix, world_center_offset, radius=0.11):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)

    wgts_coll = get_or_create_wgts_collection()
    if obj.name not in wgts_coll.objects:
        wgts_coll.objects.link(obj)

    bm = bmesh.new()
    segments = 32
    inv_mat = bone_matrix.inverted()

    for i in range(segments):
        angle = 2 * pi * i / segments
        w_x = world_center_offset.x + cos(angle) * radius
        w_y = world_center_offset.y
        w_z = world_center_offset.z + sin(angle) * radius
        local_pos = inv_mat.to_3x3() @ mathutils.Vector((w_x, w_y, w_z))
        bm.verts.new(local_pos)

    bm.verts.ensure_lookup_table()
    for i in range(segments):
        bm.edges.new((bm.verts[i], bm.verts[(i + 1) % segments]))
    bm.to_mesh(mesh)
    bm.free()
    obj.location = (0, 0, 0)
    return obj


def create_wuwa_breast_controls(rig_obj):
    """
    Creates circular breast controllers ('breast.L', 'breast.R') on the Torso collection
    parented to 'chest', with a front-facing circle custom widget (WGT-rig_breast.L / R),
    and binds the deformation bones (ORG-Bone_Chest001_L / R) to follow them with zero rest shift.
    """
    if not rig_obj or rig_obj.type != 'ARMATURE':
        return

    arm_data = rig_obj.data

    # Detect chest / breast bones on the rig
    chest_l = None
    chest_r = None
    for b in arm_data.bones:
        b_low = b.name.lower()
        if "chest" in b_low or "breast" in b_low:
            if b.name.startswith("ORG-"):
                if ("001_l" in b_low or "01_l" in b_low or "_l" in b_low or ".l" in b_low) and not chest_l:
                    chest_l = b.name
                elif ("001_r" in b_low or "01_r" in b_low or "_r" in b_low or ".r" in b_low) and not chest_r:
                    chest_r = b.name

    if not chest_l or not chest_r:
        return

    # 1. Edit mode: Create breast.L and breast.R bones at EXACT rest position of ORG bones
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    eb_org_l = eb.get(chest_l)
    eb_org_r = eb.get(chest_r)
    if not eb_org_l or not eb_org_r:
        bpy.ops.object.mode_set(mode='OBJECT')
        return

    chest_parent = eb.get("chest") or eb.get("torso") or eb.get("Spine2_fk") or eb.get("ORG-Spine2")

    for ctrl_name, org_bone in [("breast.L", eb_org_l), ("breast.R", eb_org_r)]:
        b_ctrl = eb.get(ctrl_name) or eb.new(ctrl_name)

        # Match EXACT head, tail, roll of the org bone so COPY_TRANSFORMS causes 0.000 shift/stretch
        b_ctrl.head = org_bone.head.copy()
        b_ctrl.tail = org_bone.tail.copy()
        b_ctrl.roll = org_bone.roll
        if chest_parent:
            b_ctrl.parent = chest_parent
        b_ctrl.use_connect = False

    mat_l = eb.get("breast.L").matrix.copy()
    mat_r = eb.get("breast.R").matrix.copy()

    bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Create Circle Widgets for Breasts (WGT-rig_breast.L, WGT-rig_breast.R)
    # Circle radius 0.25m positioned in front of the model (offset Y = -0.16m)
    wgt_l = create_breast_widget_for_bone("WGT-rig_breast.L", mat_l, mathutils.Vector((0.0, -0.16, 0.0)), radius=0.25)
    wgt_r = create_breast_widget_for_bone("WGT-rig_breast.R", mat_r, mathutils.Vector((0.0, -0.16, 0.0)), radius=0.25)

    # 3. Pose mode: Configure Custom Shape, Theme, and Constraints
    bpy.ops.object.mode_set(mode='POSE')
    for ctrl_name, org_name, wgt_obj in [("breast.L", chest_l, wgt_l), ("breast.R", chest_r, wgt_r)]:
        pb_ctrl = rig_obj.pose.bones.get(ctrl_name)
        if pb_ctrl:
            if wgt_obj:
                pb_ctrl.custom_shape = wgt_obj
                pb_ctrl.custom_shape_scale_xyz = (1.0, 1.0, 1.0)
            if hasattr(pb_ctrl, "color"):
                pb_ctrl.color.palette = 'THEME09'  # Yellow, matching Torso controls
            lock_bone_transformations(pb_ctrl, rig_obj)

        pb_org = rig_obj.pose.bones.get(org_name)
        if pb_org:
            for c in list(pb_org.constraints):
                if c.name in ["Copy Transforms Breast", "Breast_Follow"]:
                    pb_org.constraints.remove(c)
            con = pb_org.constraints.new('COPY_TRANSFORMS')
            con.name = "Copy Transforms Breast"
            con.target = rig_obj
            con.subtarget = ctrl_name

    # 4. Collection Assignments
    assign_bone_to_collection(rig_obj, 'breast.L', 'Torso (IK)')
    assign_bone_to_collection(rig_obj, 'breast.R', 'Torso (IK)')

    # Ensure all ORG-Bone_Chest* bones are moved to Other collection and unhidden
    for b in rig_obj.data.bones:
        b_low = b.name.lower()
        if "chest00" in b_low or "chest01" in b_low or "chest02" in b_low or "chest_l" in b_low or "chest_r" in b_low:
            if b.name not in ["chest", "breast.L", "breast.R"]:
                assign_bone_to_collection(rig_obj, b.name, 'Other')
                b.hide = False


def organize_rigify_bone_collections(rig_obj, orig_arm_name=None, char_name=None):
    """
    Sets up the standard 23 bone collections on a generated Rigify rig for Wuthering Waves,
    distributes all bones (IK, FK, Tweaks, Fingers, Face, Physics, Hair, Clothes),
    applies theme color palettes, sets standard visibility, and modifies/runs the Rig UI script
    to display layer buttons with stars (★) in the N-panel Item tab.
    """
    if not rig_obj or rig_obj.type != 'ARMATURE':
        return

    is_version_4 = hasattr(rig_obj.data, "collections")
    clean_char_name = char_name or extract_clean_character_name(rig_obj.name)

    # 1. Initialize Collections
    setup_standard_bone_collections(rig_obj, is_version_4)

    # 2. Physics & Hair/Clothes Classifier Callback for WuWa
    def wuwa_physics_classifier(armature_obj, b2c_func):
        core_biped_org = {
            "ORG-Pelvis", "ORG-Spine", "ORG-Spine1", "ORG-Spine2",
            "ORG-neck", "ORG-head",
            "ORG-shoulder.L", "ORG-shoulder.R",
            "ORG-upper_arm.L", "ORG-upper_arm.R",
            "ORG-forearm.L", "ORG-forearm.R",
            "ORG-hand.L", "ORG-hand.R",
            "ORG-thigh.L", "ORG-thigh.R",
            "ORG-shin.L", "ORG-shin.R",
            "ORG-foot.L", "ORG-foot.R",
            "ORG-toe_ik.L", "ORG-toe_ik.R",
            "ORG-Bip001LHeel0", "ORG-Bip001RHeel0",
            "ORG-Root", "ORG-root", "ORG-Bip001",
        }
        for side in [".L", ".R"]:
            for f in ["thumb", "f_index", "f_middle", "f_ring", "f_pinky"]:
                for n in ["01", "02", "03"]:
                    core_biped_org.add(f"ORG-{f}.{n}{side}")
                    core_biped_org.add(f"ORG-{f}.{n}{side}.001")

        face_control_names = {
            "EyeTracker", "Eye.L", "Eye.R", "EyeScale", "FacePanelRoot", "FacePanel", "Face-Root",
            "Smile.L", "Smile.R", "Anger.L", "Anger.R", "Sad.L", "Sad.R",
            "Focus.L", "Focus.R", "Insipid.L", "Insipid.R", "Mouth.L", "Mouth.R",
            "B_Anger", "B_Happy", "B_Cheerful", "B_Sad", "B_Flat", "B_Inside_Add",
            "Aa", "M_A", "M_O", "M_Open", "M_Laugh", "M_Scared", "M_Trapezoid", "M_Nutcracker"
        }

        for bone in armature_obj.data.bones:
            b_name = bone.name
            b_low = b_name.lower()
            if (
                b_name.startswith("DEF-")
                or b_name.startswith("MCH-")
                or b_name.startswith("CTRL-")
                or b_name.startswith("LABEL-")
                or b_name in core_biped_org
                or b_name in face_control_names
                or "tweak" in b_low
                or "_fk" in b_low
                or "_ik" in b_low
                or "master" in b_low
                or "thumb" in b_low
                or "f_index" in b_low
                or "f_middle" in b_low
                or "f_ring" in b_low
                or "f_pinky" in b_low
                or "forearm" in b_low
                or "upper_arm" in b_low
                or "thigh" in b_low
                or "shin" in b_low
                or "foot" in b_low
                or "toe" in b_low
                or "hand" in b_low
                or "shoulder" in b_low
                or "spine" in b_low
                or "torso" in b_low
                or "head" in b_low
                or "neck" in b_low
                or "root" in b_low
                or "twist" in b_low
                or "heel" in b_low
                or "camera" in b_low
                or "_elbow_" in b_low
                or "_knee_" in b_low
                or "leg_l_" in b_low
                or "leg_r_" in b_low
                or b_low in ["chest", "hips", "torso", "head", "neck", "root", "pelvis"]
                or "chest" in b_low
                or "breast" in b_low
            ):
                continue

            clean_low = b_low.replace("org-", "").replace("bip001_", "")

            if any(k in clean_low for k in ["hair", "toufa", "bang", "fringe", "ahoge", "ponytail", "earring", "eardrop"]):
                b2c_func(b_name, 20, "Hair")
                bone.hide = False
            elif any(k in clean_low for k in ["prop", "weapon", "chibang", "wingcase", "hitcase", "hulu"]):
                b2c_func(b_name, 21, "Props")
                bone.hide = False
            elif any(k in clean_low for k in ["piao", "qunzi", "skirt", "trousers", "cloth", "dress", "ribbon", "sleeve", "strap", "button", "belt", "tail", "shoulder_l_", "shoulder_r_"]):
                b2c_func(b_name, 22, "Clothes")
                bone.hide = False
            else:
                parent_name = bone.parent.name.lower() if bone.parent else ""
                if any(h in parent_name for h in ["head", "neck", "hair", "toufa", "bang", "fringe"]):
                    b2c_func(b_name, 20, "Hair")
                    bone.hide = False
                elif any(s in parent_name for s in ["pelvis", "spine", "piao", "skirt", "cloth"]):
                    b2c_func(b_name, 22, "Clothes")
                    bone.hide = False

    # 3. Distribute standard bones
    distribute_standard_rig_bones(
        rig_obj,
        is_version_4=is_version_4,
        toe_bones_exist=True,
        use_arm_ik_poles=True,
        use_leg_ik_poles=True,
        has_lighting_panel=False,
        physics_bone_callback=wuwa_physics_classifier,
    )

    # 4. Explicit bone assignments for WuWa specific controls
    def b2c(b_name, layer_num, coll_name, sec_coll="None"):
        bone_to_layer_or_collection(rig_obj, b_name, layer_num, coll_name, sec_coll, is_version_4)

    face_bones = [
        "EyeTracker", "Eye.L", "Eye.R", "EyeScale", "FacePanelRoot", "FacePanel",
        "Smile.L", "Smile.R", "Anger.L", "Anger.R", "Sad.L", "Sad.R",
        "Focus.L", "Focus.R", "Insipid.L", "Insipid.R", "Mouth.L", "Mouth.R",
        "B_Anger", "B_Happy", "B_Cheerful", "B_Sad", "B_Flat", "B_Inside_Add",
        "Aa", "M_A", "M_O", "M_Open", "M_Laugh", "M_Scared", "M_Trapezoid", "M_Nutcracker"
    ]
    for b in face_bones:
        b2c(b, 0, "Face")

    if hasattr(rig_obj.data, "bones"):
        for b in rig_obj.data.bones:
            if b.name.startswith("CTRL-") or b.name.startswith("LABEL-"):
                b2c(b.name, 0, "Face")
            elif b.name == "Face-Root":
                b2c(b.name, 25, "Other")

    b2c("breast.L", 3, "Torso (IK)")
    b2c("breast.R", 3, "Torso (IK)")

    b2c("Bip001Neck", 3, "Torso (IK)")
    b2c("Bip001Head", 3, "Torso (IK)")
    b2c("Bip001Neck._fk", 4, "Torso (FK)")
    b2c("Bip001Head._fk", 4, "Torso (FK)")
    b2c("Spine_fk", 4, "Torso (FK)")
    b2c("Spine1_fk", 4, "Torso (FK)")
    b2c("Spine2_fk", 4, "Torso (FK)")

    for b in ["tweak_Spine", "tweak_Spine1", "tweak_Spine2", "tweak_Pelvis", "tweak_neck"]:
        b2c(b, 2, "Tweaks")

    # 5. Apply Standard Theme Color Palettes to Rigify Body Collections
    theme_map = {
        "Torso (IK)": "THEME09",
        "Torso (FK)": "THEME04",
        "Torso": "THEME09",
        "Tweaks": "THEME04",
        "Pivots & Pins": "THEME04",
        "Offsets": "THEME04",
        "Fingers": "THEME14",
        "Fingers (Detail)": "THEME03",
        "Arm.L (IK)": "THEME01",
        "Arm.R (IK)": "THEME01",
        "Arm.L (FK)": "THEME03",
        "Arm.R (FK)": "THEME03",
        "Leg.L (IK)": "THEME01",
        "Leg.R (IK)": "THEME01",
        "Leg.L (FK)": "THEME03",
        "Leg.R (FK)": "THEME03",
        "Root": "THEME01",
    }
    for pbone in rig_obj.pose.bones:
        if hasattr(pbone, "bone") and hasattr(pbone.bone, "collections"):
            assigned = False
            for coll in pbone.bone.collections:
                if coll.name in theme_map and hasattr(pbone, "color"):
                    if coll.name == "Face" or pbone.name.startswith("CTRL-") or pbone.name.startswith("LABEL-") or pbone.name in ["EyeTracker", "Eye.L", "Eye.R"] or getattr(pbone.color, "palette", None) == 'CUSTOM':
                        continue
                    pbone.color.palette = theme_map[coll.name]
                    assigned = True
                    break
            if not assigned and hasattr(pbone, "color"):
                coll_names = {c.name for c in pbone.bone.collections}
                if coll_names.intersection({"Hair", "Clothes", "Props", "Other"}):
                    pbone.color.palette = 'DEFAULT'

    # 6. Apply standard visibility
    apply_wuwa_bone_collection_visibilities(rig_obj)

    # 7. Modify and execute the Rig UI script to render the standard Gacha Setup N-panel Rig Layers with stars (★)
    modify_and_run_rig_ui_script(
        rig_obj,
        orig_arm_name or rig_obj.name,
        char_name=clean_char_name
    )


def apply_wuwa_bone_collection_visibilities(armature):
    """Sets standard visibility for bone collections, hiding tweaks, FK, secondary physics, ORG, DEF, MCH."""
    if not armature or armature.type != 'ARMATURE' or not armature.data:
        return

    collections_to_hide = {
        "Tweaks", "Pivots & Pins", "Offsets", "Props", "Face (Primary)", "Face (Secondary)",
        "Torso (FK)", "Torso (Tweak)", "Fingers (Detail)", "Fingers (Details)",
        "Arm.L (FK)", "Arm.R (FK)", "Arm.L (Tweak)", "Arm.R (Tweak)",
        "Leg.L (FK)", "Leg.R (FK)", "Leg.L (Tweak)", "Leg.R (Tweak)",
        "Hair", "Hair 2", "Clothes", "Cloth", "Skirt", "Breast / Tail", "Cage", "Other", "Others",
        "Extra", "ORG", "DEF", "MCH", "Deform",
    }
    collections_to_show = {
        "Face", "Torso (IK)", "Torso", "Fingers", "Arm.L (IK)", "Arm.R (IK)",
        "Leg.L (IK)", "Leg.R (IK)", "Root", "Lighting"
    }

    if hasattr(armature.data, "collections"):
        for coll in armature.data.collections:
            if coll.name in collections_to_hide:
                coll.is_visible = False
            elif coll.name in collections_to_show:
                coll.is_visible = True

    if hasattr(armature.data, "collections_all"):
        for coll in armature.data.collections_all:
            if coll.name in ("ORG", "DEF", "MCH", "Deform") or coll.name in collections_to_hide:
                coll.is_visible = False
