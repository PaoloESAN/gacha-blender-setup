# Author: michael-gh1
# Arknights: Endfield Rigging Script
# Based on Genshin, HSR, and ZZZ FBX rigging architectures

import os
import re
import math
from math import pi
import bpy
from mathutils import Vector

from setup_wizard.character_rig_setup.rig_ui_utils import (
    extract_clean_character_name,
    setup_standard_bone_collections,
    distribute_standard_rig_bones,
    modify_and_run_rig_ui_script,
)


def rig_character(
    file_path,
    disallow_arm_ik_stretch,
    disallow_leg_ik_stretch,
    use_arm_ik_poles,
    use_leg_ik_poles,
    add_child_of_constraints,
    use_head_tracker,
    meshes_joined=False,
):
    context = bpy.context
    is_version_4 = bpy.app.version[0] >= 4

    def is_rigify_rig(arm_obj):
        if not arm_obj or arm_obj.type != "ARMATURE":
            return False
        b_names = arm_obj.data.bones.keys()
        return (
            "root_2" in b_names
            or "MCH-torso.parent" in b_names
            or "WGT" in arm_obj.name
            or (arm_obj.name.endswith("Rig") and "root" in b_names)
        )

    # Search for an unrigged character armature
    candidates = [
        o for o in context.selected_objects
        if o.type == "ARMATURE" and not is_rigify_rig(o) and o.name != "metarig"
    ]
    if not candidates and context.active_object and context.active_object.type == "ARMATURE" and not is_rigify_rig(context.active_object) and context.active_object.name != "metarig":
        candidates = [context.active_object]
    if not candidates:
        candidates = [
            o for o in bpy.data.objects
            if o.type == "ARMATURE" and not is_rigify_rig(o) and o.name != "metarig"
        ]
    if candidates:
        head_bone_arm_target = candidates[0]
        context.view_layer.objects.active = head_bone_arm_target
        head_bone_arm_target.select_set(True)
    else:
        existing_rig = next((o for o in bpy.data.objects if is_rigify_rig(o)), None)
        if existing_rig:
            print(f"[AKE RIG] Character is already rigged as '{existing_rig.name}'. Skipping duplicate rigging.")
            return
        raise RuntimeError("No armature found. Please select the character's armature and try again.")

    obj = head_bone_arm_target
    original_name = obj.name
    armature = obj.data

    # 1. Edit mode checks and head/eye correction
    bpy.ops.object.mode_set(mode="EDIT")

    toe_bones_exist = any(
        t in armature.edit_bones
        for t in ["Bip001_L_Toe0", "Bip001 L Toe0", "toe.L", "Bip001-L-Toe0"]
    )

    possible_eye_L = [
        "faceLfIrisJoint", "eyeLf01Joint", "+EyeBone L A02", "+EyeBone L A01",
        "eye.L", "eye_L", "EYE_L", "Eye_L", "Skn_L_Eye", "Bdy_L_Eye"
    ]
    possible_eye_R = [
        "faceRtIrisJoint", "eyeRt01Joint", "+EyeBone R A02", "+EyeBone R A01",
        "eye.R", "eye_R", "EYE_R", "Eye_R", "Skn_R_Eye", "Bdy_R_Eye"
    ]

    left_eye_bone_name = next((b for b in possible_eye_L if b in armature.edit_bones), None)
    right_eye_bone_name = next((b for b in possible_eye_R if b in armature.edit_bones), None)
    has_eyes = bool(left_eye_bone_name and right_eye_bone_name)

    head_bone_temp = None
    for hname in ["Bip001_Head", "Bip001 Head", "Bip001-Head", "Head", "head", "spine.006"]:
        if hname in armature.edit_bones:
            head_bone_temp = armature.edit_bones[hname]
            break
    if not head_bone_temp:
        for b in armature.edit_bones:
            if "head" in b.name.lower():
                head_bone_temp = b
                break

    if head_bone_temp:
        if has_eyes and left_eye_bone_name:
            eye_bone_head_z = armature.edit_bones[left_eye_bone_name].head[2]
            head_bone_temp.tail[0] = head_bone_temp.head[0]
            head_bone_temp.tail[1] = head_bone_temp.head[1]
            head_bone_temp.tail[2] = eye_bone_head_z
        else:
            head_bone_temp.tail[0] = head_bone_temp.head[0]
            head_bone_temp.tail[1] = head_bone_temp.head[1]
            head_bone_temp.tail[2] = head_bone_temp.head[2] + 0.0538

    # 2. Comprehensive abadidea mapping for Arknights: Endfield
    abadidea = {
        # Pelvis & Spine
        "Bip001_Pelvis": "spine",
        "Bip001_Spine": "spine.001",
        "Bip001_Spine1": "spine.002",
        "Bip001_Spine2": "spine.003",
        "Bip001_Neck": "spine.004",
        "Bip001_Head": "spine.006",
        # Arms (Left)
        "Bip001_L_Clavicle": "shoulder.L",
        "Bip001_L_UpperArm": "upper_arm.L",
        "Bip001_L_Forearm": "forearm.L",
        "Bip001_L_Hand": "hand.L",
        # Fingers (Left)
        "Bip001_L_Finger0": "thumb.01.L",
        "Bip001_L_Finger01": "thumb.02.L",
        "Bip001_L_Finger02": "thumb.03.L",
        "Bip001_L_Finger1": "f_index.01.L",
        "Bip001_L_Finger11": "f_index.02.L",
        "Bip001_L_Finger12": "f_index.03.L",
        "Bip001_L_Finger2": "f_middle.01.L",
        "Bip001_L_Finger21": "f_middle.02.L",
        "Bip001_L_Finger22": "f_middle.03.L",
        "Bip001_L_Finger3": "f_ring.01.L",
        "Bip001_L_Finger31": "f_ring.02.L",
        "Bip001_L_Finger32": "f_ring.03.L",
        "Bip001_L_Finger4": "f_pinky.01.L",
        "Bip001_L_Finger41": "f_pinky.02.L",
        "Bip001_L_Finger42": "f_pinky.03.L",
        # Arms (Right)
        "Bip001_R_Clavicle": "shoulder.R",
        "Bip001_R_UpperArm": "upper_arm.R",
        "Bip001_R_Forearm": "forearm.R",
        "Bip001_R_Hand": "hand.R",
        # Fingers (Right)
        "Bip001_R_Finger0": "thumb.01.R",
        "Bip001_R_Finger01": "thumb.02.R",
        "Bip001_R_Finger02": "thumb.03.R",
        "Bip001_R_Finger1": "f_index.01.R",
        "Bip001_R_Finger11": "f_index.02.R",
        "Bip001_R_Finger12": "f_index.03.R",
        "Bip001_R_Finger2": "f_middle.01.R",
        "Bip001_R_Finger21": "f_middle.02.R",
        "Bip001_R_Finger22": "f_middle.03.R",
        "Bip001_R_Finger3": "f_ring.01.R",
        "Bip001_R_Finger31": "f_ring.02.R",
        "Bip001_R_Finger32": "f_ring.03.R",
        "Bip001_R_Finger4": "f_pinky.01.R",
        "Bip001_R_Finger41": "f_pinky.02.R",
        "Bip001_R_Finger42": "f_pinky.03.R",
        # Legs
        "Bip001_L_Thigh": "thigh.L",
        "Bip001_L_Calf": "shin.L",
        "Bip001_L_Foot": "foot.L",
        "Bip001_L_Toe0": "toe.L",
        "Bip001_R_Thigh": "thigh.R",
        "Bip001_R_Calf": "shin.R",
        "Bip001_R_Foot": "foot.R",
        "Bip001_R_Toe0": "toe.R",
    }

    # Support variants with spaces instead of underscores
    for k, v in list(abadidea.items()):
        spaced = k.replace("_", " ")
        if spaced not in abadidea:
            abadidea[spaced] = v

    # Dynamic detection for breast bones
    for b in armature.edit_bones:
        b_low = b.name.lower()
        if ("breast" in b_low or "chest" in b_low or "xiong" in b_low) and not b.name.startswith(("DEF-", "ORG-", "MCH-")):
            if ("_l" in b_low or ".l" in b_low or "l_" in b_low or "left" in b_low) and "breast.L" not in abadidea.values():
                abadidea[b.name] = "breast.L"
            elif ("_r" in b_low or ".r" in b_low or "r_" in b_low or "right" in b_low) and "breast.R" not in abadidea.values():
                abadidea[b.name] = "breast.R"

    # Map eye bones
    if left_eye_bone_name:
        abadidea[left_eye_bone_name] = "eye.L"
    if right_eye_bone_name:
        abadidea[right_eye_bone_name] = "eye.R"

    if not toe_bones_exist:
        abadidea.pop("Bip001_L_Toe0", None)
        abadidea.pop("Bip001_R_Toe0", None)
        abadidea.pop("Bip001 L Toe0", None)
        abadidea.pop("Bip001 R Toe0", None)

    # 3. Disconnect spines and eyes
    def select_bone(b):
        b.select = True
        b.select_head = True
        b.select_tail = True

    bpy.ops.armature.select_all(action="DESELECT")
    for eye_name in ["eye.L", "eye.R", left_eye_bone_name, right_eye_bone_name]:
        if eye_name and eye_name in armature.edit_bones:
            select_bone(armature.edit_bones[eye_name])
    for sp in ["Bip001_Spine", "Bip001_Spine1", "Bip001_Spine2", "Bip001 Spine", "Bip001 Spine1", "Bip001 Spine2"]:
        if sp in armature.edit_bones:
            select_bone(armature.edit_bones[sp])
    bpy.ops.armature.parent_clear(type="DISCONNECT")
    bpy.ops.armature.select_all(action="DESELECT")

    # 4. Rename pose bones using abadidea
    bpy.ops.object.mode_set(mode="POSE")
    for pb in obj.pose.bones:
        if pb.name in abadidea:
            pb.name = abadidea[pb.name]

    bpy.ops.object.mode_set(mode="EDIT")
    # Align shoulder rolls so local Z points up
    if "shoulder.L" in armature.edit_bones:
        armature.edit_bones["shoulder.L"].align_roll(Vector((0, 0, 1)))
    if "shoulder.R" in armature.edit_bones:
        armature.edit_bones["shoulder.R"].align_roll(Vector((0, 0, 1)))

    # Remove Bip001 if present, reparenting children to spine
    for bone in list(armature.edit_bones):
        if bone.name in ["Bip001", "Bip001.001"]:
            for child in bone.children:
                if child.name != "spine" and "spine" in armature.edit_bones:
                    child.parent = armature.edit_bones["spine"]
            armature.edit_bones.remove(bone)
        elif ".L" not in bone.name and ".R" not in bone.name and "f_" not in bone.name and "thumb" not in bone.name:
            bone.roll = 0

    def realign(bone):
        if bone:
            bone.head.x = 0
            bone.tail.x = 0

    realign(armature.edit_bones.get("spine"))
    realign(armature.edit_bones.get("spine.006"))

    def attachfeets(parent_name, child_name):
        if parent_name in armature.edit_bones and child_name in armature.edit_bones:
            p = armature.edit_bones[parent_name]
            c = armature.edit_bones[child_name]
            p.tail.x = c.head.x
            p.tail.y = c.head.y
            p.tail.z = c.head.z

    if toe_bones_exist:
        attachfeets("foot.L", "toe.L")
        attachfeets("foot.R", "toe.R")
    attachfeets("upper_arm.L", "forearm.L")
    attachfeets("upper_arm.R", "forearm.R")
    attachfeets("thigh.L", "shin.L")
    attachfeets("thigh.R", "shin.R")
    attachfeets("forearm.L", "hand.L")
    attachfeets("forearm.R", "hand.R")
    attachfeets("shoulder.L", "upper_arm.L")
    attachfeets("shoulder.R", "upper_arm.R")
    attachfeets("spine", "spine.001")
    attachfeets("spine.001", "spine.002")
    attachfeets("spine.002", "spine.003")
    attachfeets("spine.003", "spine.004")
    attachfeets("spine.004", "spine.006")

    if toe_bones_exist and "toe.L" in armature.edit_bones:
        armature.edit_bones["toe.L"].tail.z = 0
        armature.edit_bones["toe.L"].tail.y -= 0.05
        armature.edit_bones["toe.R"].tail.z = 0
        armature.edit_bones["toe.R"].tail.y -= 0.05

    if "eye.L" in armature.edit_bones:
        armature.edit_bones["eye.L"].name = "DEF-eye.L"
    if "eye.R" in armature.edit_bones:
        armature.edit_bones["eye.R"].name = "DEF-eye.R"
    if "breast.L" in armature.edit_bones:
        armature.edit_bones["breast.L"].name = "DEF-breast.L"
    if "breast.R" in armature.edit_bones:
        armature.edit_bones["breast.R"].name = "DEF-breast.R"

    bpy.ops.object.mode_set(mode="POSE")
    if hasattr(bpy.types, "Action") and not hasattr(bpy.types.Action, "fcurves"):
        try:
            bpy.types.Action.fcurves = property(lambda self: getattr(self, "curves", []))
        except Exception:
            pass

    try:
        bpy.ops.object.expykit_convert_bone_names(src_preset="Rigify_Metarig.py", trg_preset="Rigify_Deform.py")
    except Exception as ex:
        print(f"Notice: Expykit convert_bone_names handled: {ex}")

    try:
        bpy.ops.object.expykit_extract_metarig(rig_preset="Rigify_Metarig.py", assign_metarig=True)
    except Exception as ex:
        print(f"Notice: Expykit extract_metarig handled: {ex}")

    # 5. Metarig adjustments
    metarig_obj = bpy.data.objects.get("metarig")
    if metarig_obj:
        # Extra IK control on fingers
        for side in [".L", ".R"]:
            for fname in ["thumb.01", "f_index.01", "f_middle.01", "f_ring.01", "f_pinky.01"]:
                bone = metarig_obj.pose.bones.get(fname + side)
                if bone and hasattr(bone, "rigify_parameters"):
                    bone.rigify_parameters.make_extra_ik_control = True

        # Finger primary rotation axis
        for fname in ["f_index", "f_middle", "f_ring", "f_pinky"]:
            for side in [".L", ".R"]:
                b = metarig_obj.pose.bones.get(f"{fname}.01{side}")
                if b and hasattr(b, "rigify_parameters"):
                    b.rigify_parameters.primary_rotation_axis = "X"

        # Thumb primary rotation axis (inverted -X so it curls inward toward the palm)
        for side in [".L", ".R"]:
            b = metarig_obj.pose.bones.get(f"thumb.01{side}")
            if b and hasattr(b, "rigify_parameters"):
                b.rigify_parameters.primary_rotation_axis = "-X"

        # Align hand metarig bones straight along forearm vector & copy thumb rolls
        bpy.ops.object.mode_set(mode="EDIT")
        for side in [".L", ".R"]:
            forearm_eb = metarig_obj.data.edit_bones.get("forearm" + side)
            hand_eb = metarig_obj.data.edit_bones.get("hand" + side)
            if forearm_eb and hand_eb:
                arm_vec = (forearm_eb.tail - forearm_eb.head).normalized()
                hand_eb.tail = hand_eb.head + arm_vec * 0.05
                hand_eb.roll = forearm_eb.roll

        for bone in metarig_obj.data.edit_bones:
            if "thumb" in bone.name:
                orig_b = armature.bones.get(bone.name) or armature.bones.get("DEF-" + bone.name)
                if orig_b:
                    bone.roll = orig_b.matrix_local.to_euler().y

        # Align metarig breast bones to character's actual breast bones
        boob_b_L = armature.bones.get("DEF-breast.L") or armature.bones.get("breast.L")
        boob_b_R = armature.bones.get("DEF-breast.R") or armature.bones.get("breast.R")
        meta_boob_L = metarig_obj.data.edit_bones.get("breast.L")
        meta_boob_R = metarig_obj.data.edit_bones.get("breast.R")

        if boob_b_L and meta_boob_L:
            meta_boob_L.head = boob_b_L.head_local.copy()
            meta_boob_L.tail = meta_boob_L.head + Vector((0, -0.06, 0))
            meta_boob_L.roll = 0.0

            if meta_boob_R:
                meta_boob_R.head = Vector((-meta_boob_L.head.x, meta_boob_L.head.y, meta_boob_L.head.z))
                meta_boob_R.tail = meta_boob_R.head + Vector((0, -0.06, 0))
                meta_boob_R.roll = 0.0
        else:
            if meta_boob_L:
                metarig_obj.data.edit_bones.remove(meta_boob_L)
            if meta_boob_R:
                metarig_obj.data.edit_bones.remove(meta_boob_R)

        bpy.ops.object.mode_set(mode="OBJECT")

    # 6. Separate physics / auxiliary bones before Rigify generation
    metanames = [
        "eye.L", "eye.R", "spine", "thigh.L", "shin.L", "foot.L", "toe.L",
        "thigh.R", "shin.R", "foot.R", "toe.R", "spine.001", "spine.002", "spine.003",
        "breast.L", "breast.R", "shoulder.L", "upper_arm.L", "forearm.L", "hand.L",
        "thumb.01.L", "thumb.02.L", "thumb.03.L", "f_index.01.L", "f_index.02.L", "f_index.03.L",
        "f_middle.01.L", "f_middle.02.L", "f_middle.03.L", "f_ring.01.L", "f_ring.02.L", "f_ring.03.L",
        "f_pinky.01.L", "f_pinky.02.L", "f_pinky.03.L", "spine.004", "spine.006",
        "shoulder.R", "upper_arm.R", "forearm.R", "hand.R",
        "thumb.01.R", "thumb.02.R", "thumb.03.R", "f_index.01.R", "f_index.02.R", "f_index.03.R",
        "f_middle.01.R", "f_middle.02.R", "f_middle.03.R", "f_ring.01.R", "f_ring.02.R", "f_ring.03.R",
        "f_pinky.01.R", "f_pinky.02.R", "f_pinky.03.R"
    ]
    if not toe_bones_exist:
        metanames = [n for n in metanames if not n.startswith("toe.")]

    pre_res = set(["DEF-" + bonename for bonename in metanames] + metanames)

    context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")

    # Ensure any remaining metaname bones have DEF- prefix
    for b in armature.edit_bones:
        if b.name in metanames and not b.name.startswith("DEF-"):
            target_def = "DEF-" + b.name
            if target_def not in armature.edit_bones:
                b.name = target_def

    pre_res_defs = set(["DEF-" + bonename for bonename in metanames])

    # Record direct parents of all physics/clothes bones
    original_parents = {}
    for b in armature.edit_bones:
        if b.name not in pre_res_defs and b.parent:
            original_parents[b.name] = b.parent.name

    savethechildren = {}
    for b in armature.edit_bones:
        if b.name in pre_res_defs:
            childlist = [c.name for c in b.children if c.name not in pre_res_defs]
            if childlist:
                savethechildren[b.name] = childlist

    # Separate physics bones
    bpy.ops.armature.select_all(action="DESELECT")
    for b in armature.edit_bones:
        if b.name not in pre_res_defs:
            b.select = True
            b.select_head = True
            b.select_tail = True
    bpy.ops.armature.separate()

    # 7. Generate Rigify rig
    if metarig_obj:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        metarig_obj.select_set(True)
        context.view_layer.objects.active = metarig_obj
        bpy.ops.object.mode_set(mode="POSE")

    bpy.ops.pose.rigify_generate()

    bpy.data.objects[obj.name].name = "rigify"
    newrig_name = armature.name + ".001"
    newrig_obj = bpy.data.objects.get(newrig_name)

    # 8. Reattach separated physics bones into the Rigify rig
    bpy.ops.object.mode_set(mode="OBJECT")
    rigifyr = bpy.data.objects.get("rigify")

    if newrig_obj and rigifyr:
        obs = [rigifyr, newrig_obj]
        bpy.ops.object.select_all(action="DESELECT")
        rigifyr.select_set(True)
        newrig_obj.select_set(True)
        context.view_layer.objects.active = rigifyr
        with context.temp_override(active_object=rigifyr, selected_editable_objects=obs):
            bpy.ops.object.join()

        bpy.ops.object.mode_set(mode="EDIT")

        # Clean up duplicate breast bones generated by join (e.g. breast.L.001)
        for side in [".L", ".R"]:
            dup = rigifyr.data.edit_bones.get(f"breast{side}.001")
            real = rigifyr.data.edit_bones.get(f"DEF-breast{side}") or rigifyr.data.edit_bones.get(f"breast{side}") or rigifyr.data.edit_bones.get("DEF-spine.003")
            if dup and real:
                for c in list(dup.children):
                    c.parent = real
                rigifyr.data.edit_bones.remove(dup)

        for mainbone, childlist in savethechildren.items():
            target_main = rigifyr.data.edit_bones.get(mainbone) or rigifyr.data.edit_bones.get(mainbone.replace("DEF-", ""))
            if target_main:
                for child in childlist:
                    if child in rigifyr.data.edit_bones:
                        rigifyr.data.edit_bones[child].parent = target_main

        # Restore parents using original_parents mapping
        for child_name, orig_parent in original_parents.items():
            child_eb = rigifyr.data.edit_bones.get(child_name)
            if not child_eb or child_eb.parent:
                continue
            candidates = [
                orig_parent,
                "DEF-" + orig_parent if not orig_parent.startswith("DEF-") else orig_parent[4:],
                "DEF-breast.L" if ".L" in child_name or "_L" in child_name or "_l" in child_name else "DEF-breast.R",
                "DEF-spine.003",
                "DEF-spine.002",
                "DEF-spine.001",
                "DEF-spine",
            ]
            for cand in candidates:
                p_cand = rigifyr.data.edit_bones.get(cand)
                if p_cand:
                    child_eb.parent = p_cand
                    break

        # Symmetrize clothes/cape/ribbon bones if needed and ensure cape/ribbon parented properly
        spine_chest = rigifyr.data.edit_bones.get("DEF-spine.003") or rigifyr.data.edit_bones.get("DEF-spine.002")
        for eb in rigifyr.data.edit_bones:
            eb_low = eb.name.lower()
            if any(k in eb_low for k in ["cape", "ribbon", "cloth"]):
                if eb.parent is None or eb.parent.name in ["root", "root_2"]:
                    if ".l" in eb_low or "_l" in eb_low or "left" in eb_low:
                        eb.parent = rigifyr.data.edit_bones.get("DEF-breast.L") or rigifyr.data.edit_bones.get("DEF-shoulder.L") or spine_chest
                    elif ".r" in eb_low or "_r" in eb_low or "right" in eb_low:
                        eb.parent = rigifyr.data.edit_bones.get("DEF-breast.R") or rigifyr.data.edit_bones.get("DEF-shoulder.R") or spine_chest
                    elif spine_chest:
                        eb.parent = spine_chest

        # Any unparented bones in rigifyr that are NOT Rigify root controls should be parented to "root"
        rigify_roots = {
            "root", "root_2", "MCH-root", "MCH-torso.parent",
            "MCH-hand_ik.parent.L", "MCH-hand_ik.parent.R",
            "MCH-foot_ik.parent.L", "MCH-foot_ik.parent.R",
            "MCH-upper_arm_ik_target.parent.L", "MCH-upper_arm_ik_target.parent.R",
            "MCH-thigh_ik_target.parent.L", "MCH-thigh_ik_target.parent.R"
        }
        if "root" in rigifyr.data.edit_bones:
            root_eb = rigifyr.data.edit_bones["root"]
            for eb in rigifyr.data.edit_bones:
                if eb.parent is None and eb.name not in rigify_roots and not eb.name.startswith("MCH-"):
                    eb.parent = root_eb

    bpy.ops.object.mode_set(mode="OBJECT")
    rigifyr.show_in_front = True
    if hasattr(rigifyr.data, "display_type"):
        rigifyr.data.display_type = "STICK"

    # 9. Append and assign custom bone shapes from RootShape.blend
    try:
        if file_path:
            path_to_file = file_path if "/Collection" in file_path else file_path + "/Collection"
            for coll_name in ["append_Root", "append_Eyes", "append_Pelvis", "append_Foot", "append_Hand", "append_Props", "append_Face Plate"]:
                try:
                    bpy.ops.wm.append(filename=coll_name, directory=path_to_file)
                except Exception:
                    pass
    except Exception as e:
        print(f"[AKE RIG] Notice appending bone shapes: {e}")

    bpy.ops.object.mode_set(mode="POSE")

    def safe_set_custom_shape(bone_name, shape_name=None, scale=None, translation=None, rotation_euler=None, disable_bone_size=True):
        pbone = rigifyr.pose.bones.get(bone_name)
        if not pbone:
            return
        if shape_name and bpy.data.objects.get(shape_name):
            pbone.custom_shape = bpy.data.objects[shape_name]
        if disable_bone_size and hasattr(pbone, "use_custom_shape_bone_size"):
            pbone.use_custom_shape_bone_size = False
        if scale and hasattr(pbone, "custom_shape_scale_xyz"):
            pbone.custom_shape_scale_xyz = scale
        if translation and hasattr(pbone, "custom_shape_translation"):
            pbone.custom_shape_translation = translation
        if rotation_euler and hasattr(pbone, "custom_shape_rotation_euler"):
            pbone.custom_shape_rotation_euler[0] = rotation_euler[0]
            pbone.custom_shape_rotation_euler[1] = rotation_euler[1]
            pbone.custom_shape_rotation_euler[2] = rotation_euler[2]

    safe_set_custom_shape("root", "root plate.002")
    safe_set_custom_shape("head", "neck", scale=(1.65, 1.65, 1.65), translation=(0.0, 0.255, 0.0), rotation_euler=(1.5708, 0, 0))
    safe_set_custom_shape("neck", "neck", scale=(1, 1, 1), translation=(0.0, 0.035, 0.007), rotation_euler=(1.5708, 0, 0))
    foot_l_pb = rigifyr.pose.bones.get("foot_ik.L")
    foot_z_offset = foot_l_pb.head.z if foot_l_pb else 0.15
    safe_set_custom_shape("foot_ik.L", "foot1", translation=(0.0, 0.0, -foot_z_offset))
    safe_set_custom_shape("foot_ik.R", "foot1", scale=(-1.0, 1.0, 1.0), translation=(0.0, 0.0, -foot_z_offset))
    safe_set_custom_shape("torso", "pelvis2")
    safe_set_custom_shape("hips", "hips", scale=(1, 1, 1), translation=(0.0, -0.04, 0.044), rotation_euler=(1.309, 0, 0))
    safe_set_custom_shape("chest", "chest", scale=(0.45, 0.45, 0.45), translation=(0.0, -0.04, 0.0), rotation_euler=(1.5708, 0, 0))
    safe_set_custom_shape("breast.L", rotation_euler=(0, 0, 0), scale=(0.10, 0.10, 0.10), disable_bone_size=True)
    safe_set_custom_shape("breast.R", rotation_euler=(0, 0, 0), scale=(0.10, 0.10, 0.10), disable_bone_size=True)
    safe_set_custom_shape("hand_ik.L", "hand", scale=(1.0, 1.0, 1.0), disable_bone_size=True)
    safe_set_custom_shape("hand_ik.R", "hand", scale=(1.0, 1.0, 1.0), disable_bone_size=True)

    if bpy.data.objects.get("primo-joint"):
        safe_set_custom_shape("thigh_ik_target.L", "primo-joint", scale=(0.75, 0.75, 0.75), disable_bone_size=False)
        safe_set_custom_shape("thigh_ik_target.R", "primo-joint", scale=(0.75, 0.75, 0.75), disable_bone_size=False)
        safe_set_custom_shape("upper_arm_ik_target.L", "primo-joint", disable_bone_size=False)
        safe_set_custom_shape("upper_arm_ik_target.R", "primo-joint", disable_bone_size=False)

    # 10. IK settings & poles
    for side in [".L", ".R"]:
        thigh_p = rigifyr.pose.bones.get("thigh_parent" + side)
        arm_p = rigifyr.pose.bones.get("upper_arm_parent" + side)
        if thigh_p:
            if "IK_Stretch" in thigh_p:
                thigh_p["IK_Stretch"] = 0.0 if disallow_leg_ik_stretch else 1.0
            if use_leg_ik_poles:
                thigh_p["pole_vector"] = True
                thigh_p["pole_parent"] = 2
        if arm_p:
            if "IK_Stretch" in arm_p:
                arm_p["IK_Stretch"] = 0.0 if disallow_arm_ik_stretch else 1.0
            if use_arm_ik_poles:
                arm_p["pole_vector"] = True
                arm_p["pole_parent"] = 2
            if "FK_limb_follow" in arm_p:
                arm_p["FK_limb_follow"] = 1.0

    torso_pb = rigifyr.pose.bones.get("torso")
    if torso_pb:
        if "neck_follow" in torso_pb:
            torso_pb["neck_follow"] = 1.0 if use_head_tracker else 0.0
        if "head_follow" in torso_pb:
            torso_pb["head_follow"] = 1.0 if use_head_tracker else 0.0

    # 11. Symmetrize clothes and hair bone names
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rigifyr.data.edit_bones
    for bone in eb:
        if "L_" in bone.name:
            try:
                y = bone.name.find("L_")
                orgname = bone.name
                newname = orgname[:y] + "_" + orgname[y+2:]
                oppbone = orgname[:y] + "R_" + orgname[y+2:]
                bone.name = newname + ".L"
                eb[oppbone].name = newname + ".R"
                if round(bone.head[0], 3) == round(-eb[newname+".R"].head[0], 3):
                    eb[newname+".R"].roll = -bone.roll
            except Exception:
                pass

    # Create root_2 bone
    if "root" in eb and "root_2" not in eb:
        newroot = eb.new("root_2")
        root = eb["root"]
        newroot.head = root.head.copy()
        newroot.tail = root.tail.copy()
        newroot.roll = root.roll
        newroot.matrix = root.matrix.copy()
        newroot.tail.y += 0.5
        root.parent = newroot

    bpy.ops.object.mode_set(mode="POSE")
    if "root_2" in rigifyr.pose.bones:
        try:
            shape_obj = bpy.data.objects.get("WGT-" + original_name + "_root") or bpy.data.objects.get("root plate.002")
            if shape_obj:
                rigifyr.pose.bones["root_2"].custom_shape = shape_obj
        except Exception:
            pass

    # 12. Fingertip curl drivers setup
    if rigifyr.animation_data and rigifyr.animation_data.drivers:
        for oDrv in rigifyr.animation_data.drivers:
            for variable in oDrv.driver.variables:
                for target in variable.targets:
                    if ".03" in oDrv.data_path and target.data_path[-7:] == "scale.y":
                        target.data_path = target.data_path[:-1] + "x"

    fingerlist = ["thumb.01_master", "f_index.01_master", "f_middle.01_master", "f_ring.01_master", "f_pinky.01_master"]
    for side in [".L", ".R"]:
        for bone in fingerlist:
            if bone + side in rigifyr.pose.bones:
                rigifyr.pose.bones[bone + side].lock_scale[0] = False

    # Apply exact requested Quaternion rotation to thumb.01_master controls and apply as rest pose
    bpy.ops.object.mode_set(mode="POSE")
    if "thumb.01_master.L" in rigifyr.pose.bones:
        pb_l = rigifyr.pose.bones["thumb.01_master.L"]
        pb_l.rotation_mode = 'QUATERNION'
        pb_l.rotation_quaternion = (0.93056, 0.0, -0.366139, 0.0)

    if "thumb.01_master.R" in rigifyr.pose.bones:
        pb_r = rigifyr.pose.bones["thumb.01_master.R"]
        pb_r.rotation_mode = 'QUATERNION'
        pb_r.rotation_quaternion = (0.93056, 0.0, 0.366139, 0.0)

    # Apply selected pose as rest pose so "Clear Transform" (Alt+R) retains this alignment
    try:
        bpy.ops.pose.select_all(action="DESELECT")
        if "thumb.01_master.L" in rigifyr.data.bones:
            rigifyr.data.bones["thumb.01_master.L"].select = True
        if "thumb.01_master.R" in rigifyr.data.bones:
            rigifyr.data.bones["thumb.01_master.R"].select = True
        bpy.ops.pose.armature_apply(selected=True)
        bpy.ops.pose.select_all(action="DESELECT")
    except Exception as e:
        print(f"[AKE RIG] Notice applying rest pose for thumb controls: {e}")

    bpy.ops.object.mode_set(mode="OBJECT")

    # 13. Naming and collection setup
    char_name = extract_clean_character_name(original_name)
    if char_name.lower() in ("armature", "character", "root"):
        for obj_item in bpy.data.objects:
            if obj_item.type == "MESH" and "actor_" in obj_item.name.lower():
                m_match = re.search(r"actor_([a-zA-Z0-9]+)_", obj_item.name, re.IGNORECASE)
                if m_match:
                    char_name = m_match.group(1).capitalize()
                    break

    try:
        if rigifyr.users_collection:
            rigifyr.users_collection[0].name = char_name
    except Exception:
        pass
    rigifyr.name = char_name + "Rig"
    try:
        from setup_wizard.ui.character_settings_utils import stamp_rig_game
        stamp_rig_game(rigifyr, "ARKNIGHTS_ENDFIELD", char_name)
    except Exception:
        pass

    if is_version_4:
        setup_standard_bone_collections(rigifyr, is_version_4)
        distribute_standard_rig_bones(
            rigifyr,
            is_version_4=is_version_4,
            toe_bones_exist=toe_bones_exist,
            use_arm_ik_poles=use_arm_ik_poles,
            use_leg_ik_poles=use_leg_ik_poles,
            has_lighting_panel=False,
        )

        # Distribute AKE facial bones to Face collection and hide it
        face_coll = rigifyr.data.collections.get("Face") or rigifyr.data.collections.new("Face")
        other_coll = rigifyr.data.collections.get("Other")
        if face_coll:
            for pb in rigifyr.pose.bones:
                if pb.name in ("eye.L", "eye.R", "eyes"):
                    continue
                pb_low = pb.name.lower()
                if any(k in pb_low for k in ["brow", "eye", "iris", "lip", "mouth", "jaw", "cheek", "face_", "tongue", "nose", "tooth"]):
                    if not pb.name.startswith(("DEF-", "MCH-", "ORG-")):
                        face_coll.assign(pb.bone)
                        if other_coll and pb.name in other_coll.bones:
                            try:
                                other_coll.unassign(pb.bone)
                            except Exception:
                                pass
            face_coll.is_visible = False

    # 14. Clean up utility armatures and widget objects
    for extra_arm in ["metarig"]:
        m_obj = bpy.data.objects.get(extra_arm)
        if m_obj:
            try:
                bpy.data.objects.remove(m_obj, do_unlink=True)
            except Exception:
                pass

    for coll_name in ["append_Root", "append_Eyes", "append_Pelvis", "append_Foot", "append_Hand", "append_Props", "append_Face Plate"]:
        coll = bpy.data.collections.get(coll_name)
        if coll:
            for c_obj in list(coll.objects):
                if c_obj.type == "ARMATURE" and c_obj.name != rigifyr.name:
                    bpy.data.objects.remove(c_obj, do_unlink=True)
            try:
                bpy.data.collections.remove(coll, do_unlink=True)
            except Exception:
                pass

    def move_into_char_wgts(c_obj, wgts_coll):
        if not c_obj or not wgts_coll:
            return
        if c_obj.name not in wgts_coll.objects:
            try:
                wgts_coll.objects.link(c_obj)
            except Exception:
                return
        for ucoll in list(c_obj.users_collection):
            if ucoll != wgts_coll:
                try:
                    ucoll.objects.unlink(c_obj)
                except Exception:
                    pass

    def get_or_create_char_wgts(char_coll, char_name):
        wgts_name = f"WGTS_{char_name}"
        wgts_coll = bpy.data.collections.get(wgts_name)
        if not wgts_coll:
            wgts_coll = bpy.data.collections.new(wgts_name)
        # Always nest inside character collection so Append brings only its own widgets
        if wgts_coll.name not in char_coll.children:
            try:
                char_coll.children.link(wgts_coll)
            except Exception:
                pass
        # Never leave per-character WGTS at scene root (causes cross-character pollution on Append)
        if wgts_coll.name in context.scene.collection.children:
            try:
                context.scene.collection.children.unlink(wgts_coll)
            except Exception:
                pass
        for parent_c in list(bpy.data.collections):
            if parent_c != char_coll and wgts_coll.name in parent_c.children:
                # Keep it only under char_coll
                if parent_c.name == wgts_name:
                    continue
                try:
                    parent_c.children.unlink(wgts_coll)
                except Exception:
                    pass
        return wgts_coll

    char_coll = rigifyr.users_collection[0] if rigifyr.users_collection else context.scene.collection
    wgts_coll = get_or_create_char_wgts(char_coll, char_name)

    root_shape_names = {
        "root plate", "foot", "foot1", "hand", "hand-pivot", "pelvis", "pelvis1",
        "pelvis2", "chest", "hips", "neck", "pivot", "shin-pin", "elbow-pin",
        "wrist", "torso-pivot", "prop-wgt", "primo-joint", "head-control-shape",
        "eye circle", "eye controller", "setting-circle", "Wink_L", "Wink_R",
        "Eye_WUp", "Eye_WDown", "Eye_Angry", "Mouth"
    }
    # Widgets actually referenced by this rig (custom shapes) -> must travel with it
    referenced_shapes = set()
    for pb in rigifyr.pose.bones:
        cs = getattr(pb, "custom_shape", None)
        if cs is not None:
            referenced_shapes.add(cs.name)
    for w_obj in list(bpy.data.objects):
        if w_obj.type == "MESH" and not any(mod.type == "ARMATURE" for mod in w_obj.modifiers):
            is_wgt = (
                w_obj.name in referenced_shapes
                or w_obj.name.startswith("WGT-")
                or any(s in w_obj.name.lower() for s in ["root plate", "head-control-shape", "eye circle", "eye controller"])
                or any(w_obj.name == s or w_obj.name.startswith(s + ".") for s in root_shape_names)
            )
            if is_wgt and not w_obj.name.startswith("S_actor_"):
                move_into_char_wgts(w_obj, wgts_coll)
                try:
                    w_obj.hide_viewport = True
                    w_obj.hide_render = True
                except Exception:
                    pass

    # Migrate leftovers from Rigify auto-generated WGTS_* / global wgt that belong to this rig
    for coll in list(bpy.data.collections):
        if coll == wgts_coll:
            continue
        if coll.name == "wgt" or coll.name.startswith("WGTS_") or coll.name == "WGTS":
            for c_obj in list(coll.objects):
                cs_users = [pb for pb in rigifyr.pose.bones if getattr(pb, "custom_shape", None) == c_obj]
                if cs_users or c_obj.name.startswith("WGT-") or c_obj.name in referenced_shapes:
                    move_into_char_wgts(c_obj, wgts_coll)
            if len(coll.objects) == 0 and len(coll.children) == 0 and coll.name != char_coll.name:
                try:
                    bpy.data.collections.remove(coll, do_unlink=True)
                except Exception:
                    pass

    try:
        wgts_coll.hide_viewport = True
        wgts_coll.hide_select = True
        wgts_coll.hide_render = True
    except Exception:
        pass
    try:
        def _exclude_wgts(lc, target):
            if lc.collection == target:
                lc.exclude = True
                return True
            for child in lc.children:
                if _exclude_wgts(child, target):
                    return True
            return False
        _exclude_wgts(context.view_layer.layer_collection, wgts_coll)
    except Exception:
        pass

    # 15. Re-target mesh Armature modifiers and parents to point to the new Rigify rig
    for obj_item in bpy.data.objects:
        if obj_item.type == "MESH":
            for mod in obj_item.modifiers:
                if mod.type == "ARMATURE":
                    mod.object = rigifyr
            if obj_item.parent and obj_item.parent.type == "ARMATURE" and obj_item.parent != rigifyr:
                obj_item.parent = rigifyr
            if obj_item.parent_type == 'BONE':
                if obj_item.parent_bone and obj_item.parent_bone not in rigifyr.data.bones:
                    if "DEF-spine.006" in rigifyr.data.bones:
                        obj_item.parent_bone = "DEF-spine.006"
                    elif "head" in rigifyr.data.bones:
                        obj_item.parent_bone = "head"

    # 16. Update and run Rigify UI script
    modify_and_run_rig_ui_script(rigifyr, original_name, char_name=char_name)

    # 17. Organize collections: ensure Lighting is nested in WGTS_<Char> and Light is in character collection
    try:
        from setup_wizard.set_up_head_driver import organize_ake_lighting_collections
        organize_ake_lighting_collections(context, rigifyr)
    except Exception as e_org:
        print(f"[AKE RIG] Notice organizing Lighting and WGTS collections: {e_org}")

    print(f"[AKE RIG] Character '{char_name}' rigged successfully!")
    return rigifyr
