# Authors: enthralpy, Llama.jpg
# Setup Wizard Integration by michael-gh1
# Honkai: Star Rail Rigging Script (Enhanced with ZZZ Master Rig Architecture)

import os
import re
from math import pi
import addon_utils
import bpy
from mathutils import Color, Vector

from setup_wizard.geometry_nodes_setup.lighting_panel_names import LightingPanelNames
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
    lighting_panel_version=0,
):
    # Rig log: collects warnings to display in Blender's Text Editor as 'RIG_LOG'
    _rig_log = []

    # Blender version check
    is_version_4 = bpy.app.version[0] >= 4

    head_bone_arm_target = bpy.context.active_object

    # Blender 5.0 compatibility: active_object can be None after certain operations
    if head_bone_arm_target is None:
        armatures = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
        if not armatures:
            armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE' and 'Rig' not in obj.name and obj.name != 'metarig']
        if not armatures:
            armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
        if armatures:
            head_bone_arm_target = armatures[0]
            bpy.context.view_layer.objects.active = head_bone_arm_target
            head_bone_arm_target.select_set(True)
        else:
            raise RuntimeError("No armature found. Please select the character's armature and try again.")

    # Normalize Bip prefix (e.g. Bip002 -> Bip001) for models with non-standard biped names
    bip_pattern = re.compile(r'^Bip\d{3}')
    if any(bip_pattern.match(b.name) and not b.name.startswith("Bip001") for b in head_bone_arm_target.data.bones):
        try:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        bpy.context.view_layer.objects.active = head_bone_arm_target
        head_bone_arm_target.select_set(True)
        bpy.ops.object.mode_set(mode='POSE')
        for pb in head_bone_arm_target.pose.bones:
            if bip_pattern.match(pb.name) and not pb.name.startswith("Bip001"):
                pb.name = re.sub(r'^Bip\d{3}', 'Bip001', pb.name)
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for vg in obj.vertex_groups:
                    if bip_pattern.match(vg.name) and not vg.name.startswith("Bip001"):
                        vg.name = re.sub(r'^Bip\d{3}', 'Bip001', vg.name)

    temp_armature = head_bone_arm_target.data

    bpy.ops.object.mode_set(mode='EDIT')

    # Check if toe bones exist
    toe_bones_exist = True
    if (
        "Toes_L" not in temp_armature.edit_bones
        and "Bip001 L Toe0" not in temp_armature.edit_bones
        and "DEF-toe.L" not in temp_armature.edit_bones
        and "toe.L" not in temp_armature.edit_bones
    ):
        toe_bones_exist = False

    # Check if eyes exist
    possible_eye_L = [
        "eye_L", "eye_All_L", "eye.L", "EYE_L", "Eye_L",
        "+EyeBone L A02", "+EyeBone L A01", "Skn_L_Eye", "Bdy_L_Eye",
        "Bdy_L_Eye_Skin", "Skn_L_Pupil", "Skn_Bn_Eye_L", "Skn_L_Eye_New", "Bn_Eye_L", "PT_L_Eye"
    ]
    possible_eye_R = [
        "eye_R", "eye_All_R", "eye.R", "EYE_R", "Eye_R",
        "+EyeBone R A02", "+EyeBone R A01", "Skn_R_Eye", "Bdy_R_Eye",
        "Bdy_R_Eye_Skin", "Skn_R_Pupil", "Skn_Bn_Eye_R", "Skn_R_Eye_New", "Bn_Eye_R", "PT_R_Eye"
    ]

    left_eye_exists = False
    left_eye_bone_name = None
    for name in possible_eye_L:
        if name in temp_armature.edit_bones:
            left_eye_exists = True
            left_eye_bone_name = name
            break

    right_eye_exists = False
    right_eye_bone_name = None
    for name in possible_eye_R:
        if name in temp_armature.edit_bones:
            right_eye_exists = True
            right_eye_bone_name = name
            break

    # Dynamic fallback for character-specific eye bone names
    if not left_eye_exists:
        for b in temp_armature.edit_bones:
            b_low = b.name.lower()
            if "eye" in b_low and ("_l" in b_low or ".l" in b_low or "l_" in b_low or "left" in b_low):
                if not any(ex in b_low for ex in ["track", "ctrl", "mch", "target", "brow", "lid", "lash", "star", "end", "conner", "dn", "up"]):
                    left_eye_exists = True
                    left_eye_bone_name = b.name
                    break
    if not right_eye_exists:
        for b in temp_armature.edit_bones:
            b_low = b.name.lower()
            if "eye" in b_low and ("_r" in b_low or ".r" in b_low or "r_" in b_low or "right" in b_low):
                if not any(ex in b_low for ex in ["track", "ctrl", "mch", "target", "brow", "lid", "lash", "star", "end", "conner", "dn", "up"]):
                    right_eye_exists = True
                    right_eye_bone_name = b.name
                    break

    no_eyes = not (left_eye_exists or right_eye_exists)

    # Correct head bone shape: line up head bone's tail X & Y to head bone's head, eye bone Z as height
    possible_head = ["Head_M", "head_m", "Bip001 Head", "Bip001-Head", "Bip001_Head", "Head", "head", "DEF-head", "DEF-spine.006"]
    head_bone_temp = None
    for hname in possible_head:
        if hname in temp_armature.edit_bones:
            head_bone_temp = temp_armature.edit_bones[hname]
            break
    if not head_bone_temp:
        for b in temp_armature.edit_bones:
            if "head" in b.name.lower():
                head_bone_temp = b
                break

    if head_bone_temp:
        if not no_eyes:
            eye_bone_head = temp_armature.edit_bones[left_eye_bone_name] if left_eye_exists else temp_armature.edit_bones[right_eye_bone_name]
            eye_bone_head_z = eye_bone_head.head[2]
            head_bone_head_x = head_bone_temp.head[0]
            head_bone_head_y = head_bone_temp.head[1]
            head_bone_temp.tail[0] = head_bone_head_x
            head_bone_temp.tail[1] = head_bone_head_y
            head_bone_temp.tail[2] = eye_bone_head_z
        else:
            head_bone_head_x = head_bone_temp.head[0]
            head_bone_head_y = head_bone_temp.head[1]
            head_bone_temp.tail[0] = head_bone_head_x
            head_bone_temp.tail[1] = head_bone_head_y
            head_bone_temp.tail[2] = head_bone_temp.head[2] + 0.0538

    if not toe_bones_exist:
        r_foot_bone = (
            temp_armature.edit_bones.get("Ankle_R")
            or temp_armature.edit_bones.get("Bip001 R Foot")
            or temp_armature.edit_bones.get("Foot.R")
            or temp_armature.edit_bones.get("foot.R")
        )
        if r_foot_bone:
            r_foot_bone.tail = (-0.040187, -0.078244, 0.005803)
            r_foot_bone.roll = 1.5708

        l_foot_bone = (
            temp_armature.edit_bones.get("Ankle_L")
            or temp_armature.edit_bones.get("Bip001 L Foot")
            or temp_armature.edit_bones.get("Foot.L")
            or temp_armature.edit_bones.get("foot.L")
        )
        if l_foot_bone:
            l_foot_bone.tail = (0.040187, -0.078244, 0.005803)
            l_foot_bone.roll = 1.5708

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = head_bone_arm_target

    context = bpy.context
    obj = context.object
    if obj.name[-4:] == ".001":
        obj.name = obj.name[:-4]
    print("New Run\n\n")

    original_name = obj.name

    abadidea = {
        'Hip_L': 'DEF-thigh.L',
        'Knee_L': 'DEF-shin.L',
        'Ankle_L': 'DEF-foot.L',
        'Toes_L': 'DEF-toe.L',
        'Hip_R': 'DEF-thigh.R',
        'Knee_R': 'DEF-shin.R',
        'Ankle_R': 'DEF-foot.R',
        'Toes_R': 'DEF-toe.R',
        'Scapula_L': 'DEF-shoulder.L',
        'Shoulder_L': 'DEF-upper_arm.L',
        'Elbow_L': 'DEF-forearm.L',
        'Wrist_L': 'DEF-hand.L',
        'ThumbFinger1_L': 'DEF-thumb.01.L',
        'ThumbFinger2_L': 'DEF-thumb.02.L',
        'ThumbFinger3_L': 'DEF-thumb.03.L',
        'IndexFinger1_L': 'DEF-f_index.01.L',
        'IndexFinger2_L': 'DEF-f_index.02.L',
        'IndexFinger3_L': 'DEF-f_index.03.L',
        'MiddleFinger1_L': 'DEF-f_middle.01.L',
        'MiddleFinger2_L': 'DEF-f_middle.02.L',
        'MiddleFinger3_L': 'DEF-f_middle.03.L',
        'RingFinger1_L': 'DEF-f_ring.01.L',
        'RingFinger2_L': 'DEF-f_ring.02.L',
        'RingFinger3_L': 'DEF-f_ring.03.L',
        'PinkyFinger1_L': 'DEF-f_pinky.01.L',
        'PinkyFinger2_L': 'DEF-f_pinky.02.L',
        'PinkyFinger3_L': 'DEF-f_pinky.03.L',
        'Neck_M': 'DEF-spine.004',
        'Head_M': 'DEF-spine.006',
        'Scapula_R': 'DEF-shoulder.R',
        'Shoulder_R': 'DEF-upper_arm.R',
        'Elbow_R': 'DEF-forearm.R',
        'Wrist_R': 'DEF-hand.R',
        'ThumbFinger1_R': 'DEF-thumb.01.R',
        'ThumbFinger2_R': 'DEF-thumb.02.R',
        'ThumbFinger3_R': 'DEF-thumb.03.R',
        'IndexFinger1_R': 'DEF-f_index.01.R',
        'IndexFinger2_R': 'DEF-f_index.02.R',
        'IndexFinger3_R': 'DEF-f_index.03.R',
        'MiddleFinger1_R': 'DEF-f_middle.01.R',
        'MiddleFinger2_R': 'DEF-f_middle.02.R',
        'MiddleFinger3_R': 'DEF-f_middle.03.R',
        'RingFinger1_R': 'DEF-f_ring.01.R',
        'RingFinger2_R': 'DEF-f_ring.02.R',
        'RingFinger3_R': 'DEF-f_ring.03.R',
        'PinkyFinger1_R': 'DEF-f_pinky.01.R',
        'PinkyFinger2_R': 'DEF-f_pinky.02.R',
        'PinkyFinger3_R': 'DEF-f_pinky.03.R',
        'eye_R': 'DEF-eye.R',
        'eye_L': 'DEF-eye.L',
        'breast_L': 'DEF-breast.L',
        'breast_R': 'DEF-breast.R',
        'breastM_L': 'DEF-breast.L',
        'breastM_R': 'DEF-breast.R',

        'HipPart1_R': 'DEF-thigh.R.001',
        'HipPart1_L': 'DEF-thigh.L.001',
        'ElbowPart1_L': 'DEF-forearm.L.001',
        'ElbowPart1_R': 'DEF-forearm.R.001',
        'ShoulderPart1_R': 'DEF-upperarm.R.001',
        'ShoulderPart1_L': 'DEF-upperarm.L.001',
        'head_m': 'DEF-spine.006',

        # Biped fallback for converted MMD / custom models
        'Bip001 Pelvis': 'DEF-spine',
        'Bip001 L Thigh': 'DEF-thigh.L',
        'Bip001 L Calf': 'DEF-shin.L',
        'Bip001 L Foot': 'DEF-foot.L',
        'Bip001 L Toe0': 'DEF-toe.L',
        'Bip001 R Thigh': 'DEF-thigh.R',
        'Bip001 R Calf': 'DEF-shin.R',
        'Bip001 R Foot': 'DEF-foot.R',
        'Bip001 R Toe0': 'DEF-toe.R',
        'Bip001 Spine': 'DEF-spine.001',
        'Bip001 Spine1': 'DEF-spine.002',
        'Bip001 Spine2': 'DEF-spine.003',
        'Bip001 L Clavicle': 'DEF-shoulder.L',
        'Bip001 L UpperArm': 'DEF-upper_arm.L',
        'Bip001 L Forearm': 'DEF-forearm.L',
        'Bip001 L Hand': 'DEF-hand.L',
        'Bip001 L Finger0': 'DEF-thumb.01.L',
        'Bip001 L Finger01': 'DEF-thumb.02.L',
        'Bip001 L Finger02': 'DEF-thumb.03.L',
        'Bip001 L Finger1': 'DEF-f_index.01.L',
        'Bip001 L Finger11': 'DEF-f_index.02.L',
        'Bip001 L Finger12': 'DEF-f_index.03.L',
        'Bip001 L Finger2': 'DEF-f_middle.01.L',
        'Bip001 L Finger21': 'DEF-f_middle.02.L',
        'Bip001 L Finger22': 'DEF-f_middle.03.L',
        'Bip001 L Finger3': 'DEF-f_ring.01.L',
        'Bip001 L Finger31': 'DEF-f_ring.02.L',
        'Bip001 L Finger32': 'DEF-f_ring.03.L',
        'Bip001 L Finger4': 'DEF-f_pinky.01.L',
        'Bip001 L Finger41': 'DEF-f_pinky.02.L',
        'Bip001 L Finger42': 'DEF-f_pinky.03.L',
        'Bip001 R Clavicle': 'DEF-shoulder.R',
        'Bip001 R UpperArm': 'DEF-upper_arm.R',
        'Bip001 R Forearm': 'DEF-forearm.R',
        'Bip001 R Hand': 'DEF-hand.R',
        'Bip001 R Finger0': 'DEF-thumb.01.R',
        'Bip001 R Finger01': 'DEF-thumb.02.R',
        'Bip001 R Finger02': 'DEF-thumb.03.R',
        'Bip001 R Finger1': 'DEF-f_index.01.R',
        'Bip001 R Finger11': 'DEF-f_index.02.R',
        'Bip001 R Finger12': 'DEF-f_index.03.R',
        'Bip001 R Finger2': 'DEF-f_middle.01.R',
        'Bip001 R Finger21': 'DEF-f_middle.02.R',
        'Bip001 R Finger22': 'DEF-f_middle.03.R',
        'Bip001 R Finger3': 'DEF-f_ring.01.R',
        'Bip001 R Finger31': 'DEF-f_ring.02.R',
        'Bip001 R Finger32': 'DEF-f_ring.03.R',
        'Bip001 R Finger4': 'DEF-f_pinky.01.R',
        'Bip001 R Finger41': 'DEF-f_pinky.02.R',
        'Bip001 R Finger42': 'DEF-f_pinky.03.R',
        'Bip001 Neck': 'DEF-spine.004',
        'Bip001 Head': 'DEF-spine.006',
    }

    # Dynamically map spine bones
    pose_bone_names = [b.name for b in obj.pose.bones]
    pelvis_candidates = ['Pelvis_M', 'pelvis_m', 'Pelvis', 'pelvis', 'Bip001 Pelvis', 'Root_M', 'root_m']
    pelvis_bone = None
    for cand in pelvis_candidates:
        if cand in obj.data.bones:
            db = obj.data.bones[cand]
            is_high = max(abs(db.head_local.y), abs(db.head_local.z)) > 0.3
            has_hip_child = any(any(k in c.name.lower() for k in ['hip', 'thigh', 'spine']) for c in db.children)
            if is_high or has_hip_child:
                pelvis_bone = cand
                break

    if pelvis_bone:
        abadidea[pelvis_bone] = 'DEF-spine'
        abadidea['Spine1_M'] = 'DEF-spine.001'
        abadidea['Spine2_M'] = 'DEF-spine.002'
        abadidea['Chest_M'] = 'DEF-spine.003'
    elif 'Spine1_M' in pose_bone_names:
        abadidea['Spine1_M'] = 'DEF-spine'
        abadidea['Spine2_M'] = 'DEF-spine.001'
        if 'Chest_M' in pose_bone_names:
            abadidea['Chest_M'] = 'DEF-spine.002'
        abadidea['Spine1_scale'] = 'DEF-spine'
        abadidea['Spine2_scale'] = 'DEF-spine.001'
        abadidea['Chest_scale'] = 'DEF-spine.002'

    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.context.selected_objects[0].data

    bpy.ops.armature.select_all(action='DESELECT')
    def select_bone(bone):
        bone.select = True
        bone.select_head = True
        bone.select_tail = True

    bones_list = obj.pose.bones
    for bone in bones_list:
        if bone.name in abadidea:
            bone.name = abadidea[bone.name]

    # For making it possible to symmetrically pose bones properly.
    for bone in bones_list:
        if ".L" in bone.name and bone.name not in ['DEF-spine.002','DEF-spine.001','DEF-spine.003','DEF-thigh.R.001','DEF-thigh.L.001','DEF-forearm.L.001','DEF-forearm.R.001','DEF-upperarm.R.001','DEF-upperarm.L.001','DEF-spine.006']:
            whee = bone.name[:-2] + ".R"
            if whee in armature.edit_bones and bone.name in armature.edit_bones:
                armature.edit_bones[whee].roll = -armature.edit_bones[bone.name].roll

    def realign(bone):
        bone.head.x = 0
        bone.tail.x = 0
        bone.tail.y = bone.head.y
        if bone.tail.z < bone.head.z:
            bone.tail.z = bone.head.z + .1
        else:
            bone.tail.z += .1
        bone.roll = 0

    if 'DEF-spine.006' in armature.edit_bones:
        realign(armature.edit_bones['DEF-spine.006'])

    def attachfeets(foot, toe):
        if foot in armature.edit_bones and toe in armature.edit_bones:
            armature.edit_bones[foot].tail.x = armature.edit_bones[toe].head.x
            armature.edit_bones[foot].tail.y = armature.edit_bones[toe].head.y
            armature.edit_bones[foot].tail.z = armature.edit_bones[toe].head.z
            armature.edit_bones[foot].roll = 0

    attachfeets('DEF-foot.L', 'DEF-toe.L')
    attachfeets('DEF-foot.R', 'DEF-toe.R')
    attachfeets('DEF-upper_arm.L', 'DEF-forearm.L')
    attachfeets('DEF-upper_arm.R', 'DEF-forearm.R')
    attachfeets('DEF-thigh.L', 'DEF-shin.L')
    attachfeets('DEF-thigh.R', 'DEF-shin.R')
    attachfeets('DEF-forearm.L', 'DEF-hand.L')
    attachfeets('DEF-forearm.R', 'DEF-hand.R')

    attachfeets('DEF-shoulder.R', 'DEF-upper_arm.R')
    attachfeets('DEF-shoulder.L', 'DEF-upper_arm.L')

    attachfeets('DEF-spine', 'DEF-spine.001')
    attachfeets('DEF-spine.001', 'DEF-spine.002')
    if 'DEF-spine.003' in armature.edit_bones:
        attachfeets('DEF-spine.002', 'DEF-spine.003')
        attachfeets('DEF-spine.003', 'DEF-spine.004')
    else:
        attachfeets('DEF-spine.002', 'DEF-spine.004')
    attachfeets('DEF-spine.004', 'DEF-spine.006')

    for x in ['.L', '.R']:
        toe = 'DEF-toe'
        if toe + x in armature.edit_bones:
            armature.edit_bones[toe + x].tail.z = armature.edit_bones[toe + x].head.z
            armature.edit_bones[toe + x].tail.y -= 0.05
            armature.edit_bones[toe + x].roll = 0

    bpy.ops.armature.select_all(action='DESELECT')
    try:
        if "breast.R" in armature.edit_bones:
            select_bone(armature.edit_bones["breast.R"])
            bpy.ops.armature.symmetrize()
            bpy.ops.armature.select_all(action='DESELECT')
    except Exception:
        pass

    joint_skin_grp_bone = armature.edit_bones.get("joint_skin_GRP")
    if joint_skin_grp_bone is not None:
        armature.edit_bones.remove(joint_skin_grp_bone)

    joint_face_bone = armature.edit_bones.get("joint_face")
    if joint_face_bone is not None and "DEF-spine.006" in armature.edit_bones:
        armature.edit_bones["joint_face"].parent = armature.edit_bones["DEF-spine.006"]

    if "Main" in armature.edit_bones:
        armature.edit_bones["Main"].tail.z = 0.1
        armature.edit_bones["Main"].tail.y = 0

    bpy.ops.object.mode_set(mode='POSE')

    if hasattr(bpy.types, 'Action') and not hasattr(bpy.types.Action, 'fcurves'):
        try:
            bpy.types.Action.fcurves = property(lambda self: getattr(self, 'curves', []))
        except Exception:
            pass

    try:
        bpy.ops.object.expykit_extract_metarig(rig_preset='Rigify_Metarig.py', assign_metarig=True)
    except Exception as ex:
        print(f"Notice: Expykit extract_metarig handled: {ex}")

    ## Part 2
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    armature = obj.data

    for o in bpy.data.objects:
        if o.name in ("metarig", armature.name):
            o.select_set(True)

    metarig_obj = bpy.data.objects.get("metarig")
    if metarig_obj:
        bpy.context.view_layer.objects.active = metarig_obj
        metarm = metarig_obj.data
    else:
        metarm = bpy.data.objects["metarig"].data

    bpy.ops.object.mode_set(mode='EDIT')
    for bone in metarm.edit_bones:
        if "f_" in bone.name or "thumb" in bone.name:
            if "DEF-" + bone.name in armature.edit_bones:
                bone.roll = armature.edit_bones["DEF-" + bone.name].roll

    # Breast bones in metarig
    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.data.objects[obj.name].data

    def getboob(bone, tip):
        if tip == "head":
            return armature.edit_bones[bone].head.x, armature.edit_bones[bone].head.y, armature.edit_bones[bone].head.z
        else:
            return armature.edit_bones[bone].tail.x, armature.edit_bones[bone].tail.y, armature.edit_bones[bone].tail.z

    try:
        xh, yh, zh = getboob("DEF-breast.L", "head")
        xt, yt, zt = getboob("DEF-breast.L", "tail")

        def fixboob(bone, xh, yh, zh, xt, yt, zt):
            bone.head.x = xh
            bone.head.y = yh
            bone.head.z = zh
            bone.tail.x = xt
            bone.tail.y = yt
            bone.tail.z = zt

        boobL = metarm.edit_bones["breast.L"]
        fixboob(boobL, xh, yh, zh, xt, yt, zt)
        boobR = metarm.edit_bones["breast.R"]
        fixboob(boobR, -xh, yh, zh, -xt, yt, zt)

        boobL.roll = armature.edit_bones["DEF-breast.L"].roll
        boobR.roll = -boobL.roll
    except Exception:
        if "breast.L" in metarm.edit_bones:
            if "spine.003" in metarm.edit_bones:
                chest_b = metarm.edit_bones["spine.003"]
                ch_head = chest_b.head.copy()
                boobL = metarm.edit_bones["breast.L"]
                boobR = metarm.edit_bones["breast.R"]

                boobL.head.x = 0.055
                boobL.head.y = ch_head.y - 0.1
                boobL.head.z = ch_head.z + 0.05
                boobL.tail.x = 0.055
                boobL.tail.y = ch_head.y - 0.2
                boobL.tail.z = ch_head.z + 0.05

                boobR.head.x = -0.055
                boobR.head.y = ch_head.y - 0.1
                boobR.head.z = ch_head.z + 0.05
                boobR.tail.x = -0.055
                boobR.tail.y = ch_head.y - 0.2
                boobR.tail.z = ch_head.z + 0.05
    except Exception as ex:
        print(f"[DEBUG] breast metarig setup warning: {ex}")

    ##########  DETACH PHYSICS BONES
    metanames = ['eye.L', 'eye.R', 'spine', 'thigh.L', 'shin.L', 'foot.L', 'toe.L', 'thigh.R', 'shin.R', 'foot.R', 'toe.R', 'spine.001', 'spine.002', 'spine.003', 'breast.L', 'breast.R', 'shoulder.L', 'upper_arm.L', 'forearm.L', 'hand.L', 'thumb.01.L', 'thumb.02.L', 'thumb.03.L', 'f_index.01.L', 'f_index.02.L', 'f_index.03.L', 'f_middle.01.L', 'f_middle.02.L', 'f_middle.03.L', 'f_ring.01.L', 'f_ring.02.L', 'f_ring.03.L', 'f_pinky.01.L', 'f_pinky.02.L', 'f_pinky.03.L', 'spine.004', 'spine.006', 'shoulder.R', 'upper_arm.R', 'forearm.R', 'hand.R', 'thumb.01.R', 'thumb.02.R', 'thumb.03.R', 'f_index.01.R', 'f_index.02.R', 'f_index.03.R', 'f_middle.01.R', 'f_middle.02.R', 'f_middle.03.R', 'f_ring.01.R', 'f_ring.02.R', 'f_ring.03.R', 'f_pinky.01.R', 'f_pinky.02.R', 'f_pinky.03.R']
    pre_res = ["DEF-" + bonename for bonename in metanames]
    armature = obj.data

    savethechildren = {}
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.edit_bones:
        if bone.name in pre_res:
            childlist = []
            for childbone in armature.edit_bones[bone.name].children:
                if childbone.name not in pre_res:
                    childlist.append(childbone.name)
            if childlist:
                savethechildren[bone.name] = childlist

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    bones = armature.edit_bones[:]
    for bone in bones:
        if bone.name not in pre_res:
            bone.use_connect = False
            bone.select = True
            bone.select_tail = True
            bone.select_head = True

    bpy.ops.armature.separate()

    metarig_obj = bpy.data.objects.get("metarig")
    if metarig_obj:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        metarig_obj.select_set(True)
        bpy.context.view_layer.objects.active = metarig_obj
        bpy.ops.object.mode_set(mode='POSE')

    bpy.ops.pose.rigify_generate()

    bpy.data.objects[obj.name].name = "rigify"
    bpy.context.view_layer.objects.active = bpy.data.objects[armature.name + ".001"]

    for o in bpy.data.objects:
        if o.name in ("rigify", armature.name):
            o.select_set(True)

    bpy.ops.object.mode_set(mode='OBJECT')
    newrig = armature.name + ".001"
    objList = bpy.context.selected_objects
    unselected = [o for o in objList if o != context.active_object]
    rigifyr = unselected[0]

    obs = [bpy.data.objects[rigifyr.name], bpy.data.objects[newrig]]
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    with bpy.context.temp_override(active_object=bpy.data.objects.get("rigify"), selected_editable_objects=obs):
        bpy.ops.object.join()

    bpy.context.view_layer.objects.active = bpy.data.objects["rigify"]
    bpy.ops.object.mode_set(mode='EDIT')

    for mainbone in savethechildren:
        for childbone in savethechildren[mainbone]:
            if childbone in rigifyr.data.edit_bones and mainbone in rigifyr.data.edit_bones:
                rigifyr.data.edit_bones[childbone].parent = rigifyr.data.edit_bones[mainbone]

    for x in [".L", ".R"]:
        if "DEF-forearm" + x + ".002" in rigifyr.data.edit_bones and "DEF-forearm" + x in rigifyr.data.edit_bones:
            rigifyr.data.edit_bones["DEF-forearm" + x + ".002"].parent = rigifyr.data.edit_bones["DEF-forearm" + x]

    # Ensure Root_M and pelvic/hip root bones follow DEF-spine
    target_hip_parent = (
        rigifyr.data.edit_bones.get("DEF-spine")
        or rigifyr.data.edit_bones.get("hips")
        or rigifyr.data.edit_bones.get("torso")
    )
    if target_hip_parent:
        root_m_candidates = [
            b.name for b in rigifyr.data.edit_bones
            if b.name.lower() in ["root_m", "hip_m", "root_scale", "root_m_scale", "pelvis_m"]
            or b.name.lower().startswith("root_m.")
            or b.name.lower().startswith("hip_m.")
        ]
        for r_name in root_m_candidates:
            r_bone = rigifyr.data.edit_bones.get(r_name)
            if r_bone and r_bone.name != target_hip_parent.name:
                if not r_bone.parent or r_bone.parent.name in ["Main", "root", "root_2", ""]:
                    r_bone.parent = target_hip_parent
                    r_bone.use_connect = False

    # Also HipPart1, ElbowPart1, ShoulderPart1
    for side in [".L", ".R"]:
        for part, parent_name in [
            (f"DEF-thigh{side}.001", f"DEF-thigh{side}"),
            (f"DEF-forearm{side}.001", f"DEF-forearm{side}"),
            (f"DEF-upperarm{side}.001", f"DEF-upper_arm{side}"),
            (f"DEF-upper_arm{side}.001", f"DEF-upper_arm{side}"),
        ]:
            if part in rigifyr.data.edit_bones and parent_name in rigifyr.data.edit_bones:
                rigifyr.data.edit_bones[part].parent = rigifyr.data.edit_bones[parent_name]
                rigifyr.data.edit_bones[part].use_connect = False

    #### Symmetrize clothes/hair bones
    eb = rigifyr.data.edit_bones
    for bone in eb:
        if "L_" in bone.name:
            try:
                y = bone.name.find('L_')
                orgname = bone.name
                newname = orgname[:y] + "_" + orgname[y+2:]
                oppbone = orgname[:y] + "R_" + orgname[y+2:]
                bone.name = newname + ".L"
                eb[oppbone].name = newname + ".R"
                if round(bone.head[0], 3) == round(-eb[newname+".R"].head[0], 3):
                    eb[newname+".R"].roll = -bone.roll
            except Exception:
                pass

    char_name = extract_clean_character_name(original_name)
    if "rigify" in bpy.data.objects:
        bpy.data.objects["rigify"].name = char_name + "Rig"
    our_char = bpy.data.objects.get(char_name + "Rig") or rigifyr

    try:
        from setup_wizard.ui.character_settings_utils import stamp_rig_game
        stamp_rig_game(our_char, "HONKAI_STAR_RAIL", char_name)
    except Exception:
        pass

    bpy.ops.object.mode_set(mode='OBJECT')
    try:
        head_driver_obj = bpy.data.objects.get("Head Driver") or bpy.data.objects.get("Head Origin") or bpy.data.objects.get("Head Direction")
        if head_driver_obj and "Child Of" in head_driver_obj.constraints:
            bpy.context.view_layer.objects.active = head_driver_obj
            bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')
    except Exception:
        pass

# POST RIGIFY SCRIPT EXECUTION ----------------->

    # Delete metarig
    bpy.data.objects.remove(bpy.data.objects['metarig'])

    # Moves specified param and it's children into the collection
    def move_into_collection(object,collection,include_children=True):
        
        # Get object
        this_obj = bpy.context.scene.objects.get(object)
        # Never move objects that belong to the 'lights' collection
        if this_obj and any(c.name == "lights" for c in this_obj.users_collection):
            return
        # Get existing collection or make new one
        this_coll = bpy.data.collections.get(collection)
        if not this_coll:
            this_coll = bpy.data.collections.new(collection)
            bpy.context.scene.collection.children.link(this_coll)
            
        # Move object into collection
        if this_obj:
            # Unlink it from all previous collections before moving it to new one
            for coll in this_obj.users_collection:
                coll.objects.unlink(this_obj)
                
            # Move it to our specified collection (This only does the parent obj)
            this_coll.objects.link(this_obj)
            
            if include_children:
                # Now we move the children of this object
                for child_obj in this_obj.children:
                    # Same thing, unlink previous collections
                    for coll in child_obj.users_collection:
                        coll.objects.unlink(child_obj)
                    this_coll.objects.link(child_obj)

    # Automatic code to just loop through and delete excess collections on append - thanks cgpt for regeex
    def merge_duplicate_collections(base_name):
        pattern = re.compile(rf"{re.escape(base_name)}\.\d{{3}}$")  # Matches "base_name.001", "base_name.002", etc.

        # Iterate through collections and find matching ones
        for coll in list(bpy.data.collections):
            if pattern.match(coll.name):
                for obj in list(coll.objects):
                    move_into_collection(obj.name, base_name)

                # Remove the now-empty collection
                bpy.data.collections.remove(coll)
                
    # Move the rig into the char name's collection                        
    move_into_collection(char_name+"Rig",char_name)

    # Let's make a new wgt collection inside the char coll.
    char_coll = bpy.data.collections.get(char_name)
    wgt_coll = bpy.data.collections.new("wgt")
    char_coll.children.link(wgt_coll)

    # Rename our WGT collection and put the metarig into it.
    for coll in bpy.data.collections:
        if coll.name.startswith("WGTS"):
            coll.name = "WG"

    move_into_collection("metarig","wgt")


    # Unlink all inner objects from the old WGT collection. We want them inside the new one.
    for obj in bpy.data.objects:
        if obj.name.startswith("WGT"):
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            
            wgt_coll.objects.link(obj)
            
    # Remove old unused wgt collection                
    wg_coll = bpy.data.collections.get("WG")
    if wg_coll:
        bpy.data.collections.remove(wg_coll)

    def get_and_rename_empty(empty_name):
        obj = bpy.data.objects.get(empty_name)
        if obj:
            obj.name = f"{empty_name}_{char_name}"
            return obj.name
        return None

    # Obfuscate light driving stuff not needed, keep the main light.        
    new_name = get_and_rename_empty("Face Light Direction")
    if new_name: move_into_collection(new_name,"wgt")
    
    new_name = get_and_rename_empty("Head Driver")
    if new_name: move_into_collection(new_name,"wgt")
    
    new_name = get_and_rename_empty("Main Light Direction")
    if new_name: move_into_collection(new_name,char_name)

    # V3 Shader Support - New empty names
    new_name = get_and_rename_empty("Head Origin")
    if new_name: move_into_collection(new_name,"wgt")
    
    new_name = get_and_rename_empty("Light Direction")
    if new_name: move_into_collection(new_name,char_name)

    bpy.data.collections["wgt"].hide_select = True
    bpy.data.collections["wgt"].hide_viewport = True
    bpy.data.collections["wgt"].hide_render = True

    new_name = get_and_rename_empty("Head Forward")
    if new_name: move_into_collection(new_name, "wgt")
    
    new_name = get_and_rename_empty("Head Up")
    if new_name: move_into_collection(new_name, "wgt")


    # remove lighting colls - also move the RGB wheels into the rig obj
    lighting_panel_rig_obj = bpy.data.objects.get(
        LightingPanelNames.Objects.LIGHTING_PANEL
    )
    if lighting_panel_rig_obj:
        to_del_coll = bpy.data.collections.get(
            LightingPanelNames.Collections.WIDGET_COLLECTION
        )
        if to_del_coll:
            for obj in to_del_coll.objects:
                move_into_collection(obj.name, "wgt")
        to_del_coll = bpy.data.collections.get(LightingPanelNames.Collections.PICKER)
        if to_del_coll:
            for obj in to_del_coll.objects:
                move_into_collection(obj.name, "wgt")
        to_del_coll = bpy.data.collections.get(LightingPanelNames.Collections.WHEEL)
        if to_del_coll:
            for obj in to_del_coll.objects:
                move_into_collection(obj.name, char_name)
        # DO NOT INCLUDE CHILDREN. This will cause ColorPickers to be moved into the rig object.
        move_into_collection(
            LightingPanelNames.Objects.LIGHTING_PANEL, char_name, include_children=False
        )
        l_coll = bpy.data.collections.get(LightingPanelNames.Collections.LIGHTING_PANEL)
        if l_coll:
            bpy.data.collections.remove(l_coll, do_unlink=True)

    # If default collection exists and is empty, get rid of it.
    camera_coll = bpy.data.collections.get("Collection")
    if camera_coll and len(camera_coll.objects) == 0 and len(camera_coll.children) == 0:
        bpy.data.collections.remove(camera_coll, do_unlink=True)

    layer_collection = bpy.context.view_layer.layer_collection
    layerColl = searchForLayerCollection(layer_collection, "wgt")
    bpy.context.view_layer.active_layer_collection = layerColl

    layerColl.exclude = True

    # NOTE: no aislar WGTS aquí (como en HSR): el inverse del Head Driver y el
    # código posterior (appends wgt.00X, sliders) necesitan los objetos visibles.
    # El barrido final al cierre de rig_character consolida todo en WGTS_<Char>.

    # Make our lives easier, display the bones as sticks and make sure we can view from front.    
    bpy.data.armatures[original_name].display_type = 'STICK'
    bpy.data.objects[char_name+"Rig"].show_in_front = True

    # Going into pose mode with our character selected.
    bpy.ops.object.select_all(action='DESELECT')
    our_char =  bpy.data.objects.get(char_name+"Rig")
    if our_char:
        our_char.select_set(True)
        bpy.context.view_layer.objects.active = our_char
        
        bpy.ops.object.mode_set(mode='POSE')

    # Function to automatically move a bone (if it exists) to the specified bone layer. pass in num+1 than layer desired.        
    def move_bone(bone_name,to_layers):
        armature =  bpy.context.active_object
        armature_data = armature.data
        
        if bone_name in armature_data.bones:
            bone = armature_data.bones[bone_name]
            
            for i in range(32):
                bone.layers[i] = False
            
            to_layers = [to_layers] if isinstance(to_layers, int) else to_layers
            
            for layer in to_layers:
                bone.layers[layer] = True
                print("enabling layer: " + str(layer) + " for " + bone_name)
            


    if not is_version_4:
        # Put away every other bone to the physics layer (22)
        for bone in bpy.context.active_object.data.bones:
            if bone.layers[0]:  # Check if the bone is on layer face
                move_bone(bone.name, 25)  # Move the bone to layer 23
            
    # Let's append our root_shape custom bones
    path_to_file = file_path + "/Collection"

    # Bring in our collections: root shapes and the eye rig

    bpy.ops.wm.append(filename='append_Root', directory=path_to_file)

    bpy.ops.wm.append(filename='append_Eyes', directory=path_to_file)
    
    bpy.ops.wm.append(filename='append_Pelvis', directory=path_to_file)
    
    bpy.ops.wm.append(filename='append_Foot', directory=path_to_file)
    
    bpy.ops.wm.append(filename='append_Hand', directory=path_to_file)
    
    bpy.ops.wm.append(filename='append_Props', directory=path_to_file)

    this_obj = None
    for obj in bpy.data.objects:
        if "Rig" in obj.name:
            this_obj = obj

    if "root" in this_obj.pose.bones and "root plate.002" in bpy.data.objects:
        this_obj.pose.bones["root"].custom_shape = bpy.data.objects["root plate.002"]
        this_obj.pose.bones["root"].use_custom_shape_bone_size = False
    
    this_obj.pose.bones["head"].custom_shape_scale_xyz = (1.25, 1.25, 1.25)
    this_obj.pose.bones["head"].custom_shape = bpy.data.objects["neck"]
    this_obj.pose.bones["head"].custom_shape_translation = (0.0,0.255,0.0)
    this_obj.pose.bones["head"].custom_shape_rotation_euler[0] = 1.5708
    this_obj.pose.bones["head"].use_custom_shape_bone_size = False
    
    this_obj.pose.bones["neck"].use_custom_shape_bone_size = False
    this_obj.pose.bones["neck"].custom_shape = bpy.data.objects["neck"]
    this_obj.pose.bones["neck"].custom_shape_scale_xyz = (1,1,1)
    this_obj.pose.bones["neck"].custom_shape_translation = (0.0,0.035,0.007)
    this_obj.pose.bones["neck"].custom_shape_rotation_euler[0] = 1.5708
    
    this_obj.pose.bones["foot_ik.L"].use_custom_shape_bone_size = False
    this_obj.pose.bones["foot_ik.R"].use_custom_shape_bone_size = False
    this_obj.pose.bones["foot_ik.L"].custom_shape = bpy.data.objects["foot1"]
    this_obj.pose.bones["foot_ik.R"].custom_shape = bpy.data.objects["foot1"]

    try:
        primo_joint = bpy.data.objects["primo-joint"]
        this_obj.pose.bones["thigh_ik_target.L"].custom_shape = primo_joint
        this_obj.pose.bones["thigh_ik_target.R"].custom_shape = primo_joint
        this_obj.pose.bones["upper_arm_ik_target.R"].custom_shape = primo_joint
        this_obj.pose.bones["upper_arm_ik_target.L"].custom_shape = primo_joint
    except KeyError:
        pass

    this_obj.pose.bones["thigh_ik_target.L"].custom_shape_scale_xyz[0] = 0.75
    this_obj.pose.bones["thigh_ik_target.L"].custom_shape_scale_xyz[1] = 0.75
    this_obj.pose.bones["thigh_ik_target.L"].custom_shape_scale_xyz[2] = 0.75
    this_obj.pose.bones["thigh_ik_target.R"].custom_shape_scale_xyz[0] = 0.75
    this_obj.pose.bones["thigh_ik_target.R"].custom_shape_scale_xyz[1] = 0.75
    this_obj.pose.bones["thigh_ik_target.R"].custom_shape_scale_xyz[2] = 0.75

    this_obj.pose.bones["torso"].custom_shape = bpy.data.objects["pelvis2"]
    this_obj.pose.bones["torso"].use_custom_shape_bone_size = False
  
    this_obj.pose.bones["hips"].custom_shape = bpy.data.objects["hips"]
    this_obj.pose.bones["hips"].custom_shape_scale_xyz = (1,1,1)
    this_obj.pose.bones["hips"].custom_shape_translation = (0.0,-0.04,0.044)
    this_obj.pose.bones["hips"].custom_shape_rotation_euler[0] = 1.309
    this_obj.pose.bones["hips"].use_custom_shape_bone_size = False
    
    this_obj.pose.bones["chest"].custom_shape = bpy.data.objects["chest"]
    this_obj.pose.bones["chest"].custom_shape_scale_xyz = (0.6,0.6,0.6)
    this_obj.pose.bones["chest"].custom_shape_translation = (0.0,0.18,0.0)
    this_obj.pose.bones["chest"].custom_shape_rotation_euler[0] = 1.5708
    this_obj.pose.bones["chest"].use_custom_shape_bone_size = False
    
    this_obj.pose.bones["shoulder.L"].custom_shape_scale_xyz = (1.6,1.6,1.6)
    this_obj.pose.bones["shoulder.R"].custom_shape_scale_xyz = (1.6,1.6,1.6)

    this_obj.pose.bones["foot_heel_ik.L"].custom_shape_translation = (0.0,0.0,0.0)
    this_obj.pose.bones["foot_heel_ik.R"].custom_shape_translation = (0.0,0.0,0.0)

    this_obj.pose.bones["foot_spin_ik.R"].custom_shape_translation = (0.0,-0.05,0.02)
    this_obj.pose.bones["foot_spin_ik.L"].custom_shape_translation = (0.0,-0.05,0.02)

    this_obj.pose.bones["toe_ik.L"].custom_shape_translation = (0.0,0.06,0.00)
    this_obj.pose.bones["toe_ik.R"].custom_shape_translation = (0.0,0.06,0.00)
    this_obj.pose.bones["toe_ik.L"].custom_shape_scale_xyz = (0.781,0.781,0.350)
    this_obj.pose.bones["toe_ik.R"].custom_shape_scale_xyz = (0.781,0.781,0.350)

    this_obj.pose.bones["hand_ik.R"].use_custom_shape_bone_size = False
    this_obj.pose.bones["hand_ik.R"].custom_shape = bpy.data.objects["wrist"]
    
    this_obj.pose.bones["hand_ik.L"].use_custom_shape_bone_size = False
    this_obj.pose.bones["hand_ik.L"].custom_shape = bpy.data.objects["wrist"]

    this_obj.pose.bones["palm.L"].custom_shape_scale_xyz = (1.2,1.2,1.2)
    this_obj.pose.bones["palm.R"].custom_shape_scale_xyz = (1.2,1.2,1.2)
    

    # Merge the armatures; go into object mode and make sure nothing is selected
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # Select lighting panel armature
    lighting_panel_rig_obj = bpy.data.objects.get(
        LightingPanelNames.Objects.LIGHTING_PANEL
    )
    if lighting_panel_rig_obj:
        lighting_panel_rig_obj.select_set(True)

    # Remove eyerig from RootShape.blend (eye tracking is provided by Isaac FaceRig)
    eye_rig_obj = bpy.data.objects.get("eyerig")
    if eye_rig_obj:
        bpy.data.objects.remove(eye_rig_obj, do_unlink=True)
    
    # Select root rig    
    root_rig_obj = bpy.data.objects.get("rootrig")
    if root_rig_obj:
        root_rig_obj.select_set(True)
        
    # Select pelvis rig    
    pelvis_rig_obj = bpy.data.objects.get("pelvisrig")
    if pelvis_rig_obj:
        pelvis_rig_obj.select_set(True)
        
    # Select foot L rig    
    foot_l_rig_obj = bpy.data.objects.get("footrig-L")
    if foot_l_rig_obj:
        foot_l_rig_obj.select_set(True)
        
    # Select foot R rig    
    foot_r_rig_obj = bpy.data.objects.get("footrig-R")
    if foot_r_rig_obj:
        foot_r_rig_obj.select_set(True)
        
    # Select hand R rig    
    hand_r_rig_obj = bpy.data.objects.get("handrig-R")
    if hand_r_rig_obj:
        hand_r_rig_obj.select_set(True)
        
    # Select hand L rig    
    hand_l_rig_obj = bpy.data.objects.get("handrig-L")
    if hand_l_rig_obj:
        hand_l_rig_obj.select_set(True)
        
    # Select prop rig   
    prop_rig_obj = bpy.data.objects.get("prop-rig")
    if prop_rig_obj:
        prop_rig_obj.select_set(True)
            
    # Select char armature
    if our_char:
        our_char.select_set(True)

    # Join them
    bpy.ops.object.join()
     
    # We want to save all the VG names here, perhaps we can use them to identify weighted def bones.  
    bpy.context.view_layer.objects.active = bpy.data.objects.get("Body")    
    try:
        vertex_groups_list = [vg.name for vg in bpy.context.object.vertex_groups]
    except:
        vertex_groups_list = []
    bpy.context.view_layer.objects.active = head_bone_arm_target
    
    # Get the intersection point of a line with a perpendicular plane
    def project_line_in_space(points1, points2, axis):
        x1, y1, z1 = points1
        x2, y2, z2 = points2

        m = (y2 - y1) / (x2 - x1) if (x2 - x1) != 0 else None
        b = y1 - m * x1 if m is not None else None

        if m is None:
            return None

        # Intersection point
        intersection_x = axis
        intersection_y = m * intersection_x + b
        intersection_z = z1 + (intersection_y - y1) * (z2 - z1) / (y2 - y1)

        intersection_point = (intersection_x, intersection_y, intersection_z)
        return intersection_point

    # Select the object then access it's rig (its obj data)
    ob = bpy.data.objects[char_name+"Rig"]
    armature = ob.data

    # In edit mode, set parent bones.
    bpy.ops.object.mode_set(mode='EDIT')
    head_b = armature.edit_bones.get('head')
    head_z = head_b.head.z if head_b else 1.45

    # Ensure plate-settings control bone above head (settings gear bone)
    if 'PROPERTIES' in armature.edit_bones:
        armature.edit_bones.remove(armature.edit_bones['PROPERTIES'])

    if 'plate-settings' not in armature.edit_bones:
        plate_settings_bone = armature.edit_bones.new('plate-settings')
    else:
        plate_settings_bone = armature.edit_bones['plate-settings']
    head_b = armature.edit_bones.get('head')
    if head_b:
        plate_settings_bone.parent = head_b
    if armature.edit_bones.get(LightingPanelNames.Bones.LIGHTING_PANEL):
        armature.edit_bones[LightingPanelNames.Bones.LIGHTING_PANEL].parent = armature.edit_bones['head']
    
    plate_settings_bone.head = Vector((0.0, 0.0, head_z + 0.35))
    plate_settings_bone.tail = Vector((0.0, 0.0, head_z + 0.45))
    plate_settings_bone.roll = 0
    
    # While here, set inherit scales as needed.
    armature.edit_bones['upper_arm_parent.L'].inherit_scale="NONE"
    armature.edit_bones['upper_arm_parent.R'].inherit_scale="NONE"
    armature.edit_bones['thigh_parent.L'].inherit_scale="NONE"
    armature.edit_bones['thigh_parent.R'].inherit_scale="NONE"
    armature.edit_bones['torso-outer'].inherit_scale="AVERAGE"
    armature.edit_bones['torso-inner'].inherit_scale="FULL"
    armature.edit_bones['torso'].inherit_scale="FULL"
    # fix the bad rolls of the torso bone
    armature.edit_bones['torso'].roll = 0
    armature.edit_bones['torso-inner'].roll = 0
    armature.edit_bones['torso-outer'].roll = 0
    
    armature.edit_bones['forearm_tweak-pin.R'].inherit_scale="AVERAGE"
    armature.edit_bones['forearm_tweak-pin.L'].inherit_scale="AVERAGE"
    armature.edit_bones['shin_tweak-pin.L'].inherit_scale="AVERAGE"
    armature.edit_bones['shin_tweak-pin.R'].inherit_scale="AVERAGE"
    armature.edit_bones['hand-ik-L'].inherit_scale="AVERAGE"
    armature.edit_bones['hand-ik-R'].inherit_scale="AVERAGE"
    armature.edit_bones['hand_ik.L'].inherit_scale="FULL"
    armature.edit_bones['hand_ik.R'].inherit_scale="FULL"
           
    # Fixing Foot spin bone pos for chars with generated feet bones.
    if not toe_bones_exist:
        armature.edit_bones['foot_spin_ik.L'].head.z = 0
        armature.edit_bones['foot_spin_ik.L'].tail.z = 0
        
        armature.edit_bones['foot_spin_ik.R'].head.z = 0
        armature.edit_bones['foot_spin_ik.R'].tail.z = 0
    
    # SET RELATIONSHIPS as needed after bringing in new bones  
    if 'root' in armature.edit_bones and 'root-inner' in armature.edit_bones:
        armature.edit_bones['root'].parent = armature.edit_bones['root-inner']
    
    armature.edit_bones['torso-outer'].parent = armature.edit_bones['MCH-torso.parent']
    armature.edit_bones['torso'].parent = armature.edit_bones['torso-inner']
    armature.edit_bones['torso_pivot.002'].parent = armature.edit_bones['torso']
    armature.edit_bones['hips'].parent = armature.edit_bones['MCH-torso_pivot.002']
    armature.edit_bones['chest'].parent = armature.edit_bones['MCH-torso_pivot.002']
    armature.edit_bones['MCH-spine.001'].parent = armature.edit_bones['MCH-torso_pivot.002']
    armature.edit_bones['MCH-spine.002'].parent = armature.edit_bones['MCH-torso_pivot.002']
    
    armature.edit_bones['ik-pivot-L'].parent = armature.edit_bones['foot_ik.L']    
    armature.edit_bones['ik-pivot-R'].parent = armature.edit_bones['foot_ik.R']    
    armature.edit_bones['foot_spin_ik.L'].parent = armature.edit_bones['ik-target-L']    
    armature.edit_bones['foot_spin_ik.R'].parent = armature.edit_bones['ik-target-R']   

    armature.edit_bones['hand-ik-L'].parent = armature.edit_bones['MCH-hand_ik.parent.L']    
    armature.edit_bones['hand-ik-R'].parent = armature.edit_bones['MCH-hand_ik.parent.R']    
    armature.edit_bones['hand_ik.L'].parent = armature.edit_bones['mch-hand-ik-pivot-L']
    armature.edit_bones['hand_ik.R'].parent = armature.edit_bones['mch-hand-ik-pivot-R']    
    armature.edit_bones['mch-hand-ik-wrist-L'].parent = armature.edit_bones['hand_ik.L']    
    armature.edit_bones['mch-hand-ik-wrist-R'].parent = armature.edit_bones['hand_ik.R']    
    armature.edit_bones['MCH-upper_arm_ik_target.L'].parent = armature.edit_bones['mch-hand-ik-wrist-L']    
    armature.edit_bones['MCH-upper_arm_ik_target.R'].parent = armature.edit_bones['mch-hand-ik-wrist-R']
    
    # Shoulders setup (matching Miyabi reference rig):
    # shoulder.L and shoulder.R are parented directly to chest/spine with NO damped track / follow constraints
    spine03 = armature.edit_bones.get('ORG-spine.003') or armature.edit_bones.get('chest') or armature.edit_bones.get('spine_fk.003')
    if spine03:
        if 'shoulder.L' in armature.edit_bones:
            armature.edit_bones['shoulder.L'].parent = spine03
        if 'shoulder.R' in armature.edit_bones:
            armature.edit_bones['shoulder.R'].parent = spine03

    # Remove any unwanted shoulder driver / follow helper bones so shoulders are clean and free (like Miyabi)
    for sb in ['shoulder_driver.L', 'shoulder_driver.R', 'MCH-shoulder_follow.L', 'MCH-shoulder_follow.R']:
        if sb in armature.edit_bones:
            armature.edit_bones.remove(armature.edit_bones[sb])

    # Chain sequential tail bones (e.g. Skn_Tail_01 -> 02 -> 03 ...)
    # In raw game FBX, all tail bones are often flatly parented to spine/root,
    # so rotating a parent tail bone did not rotate its children.
    # We chain them hierarchically so rotating any parent bone rotates all child
    # bones down the tail smoothly without kinks.
    # import re
    tail_groups = {}
    for eb in armature.edit_bones:
        b_low = eb.name.lower()
        if "tail" in b_low and not any(k in b_low for k in ["pendant", "hook", "mch-", "org-", "def-", "ctrl-", "ik"]):
            m = re.match(r'^(.*?[_\-\.\s]?)(?:0*(\d+))$', eb.name)
            if m:
                pfx, num_str = m.group(1), m.group(2)
                tail_groups.setdefault(pfx.lower(), []).append((int(num_str), eb.name))

    for pfx, num_names in tail_groups.items():
        if len(num_names) >= 2:
            num_names.sort(key=lambda x: x[0])
            for i in range(1, len(num_names)):
                prev_name = num_names[i - 1][1]
                curr_name = num_names[i][1]
                prev_eb = armature.edit_bones.get(prev_name)
                curr_eb = armature.edit_bones.get(curr_name)
                if prev_eb and curr_eb:
                    if curr_eb.parent != prev_eb:
                        curr_eb.parent = prev_eb
                        curr_eb.use_connect = False
                        print(f"[TAIL CHAIN] Chained {curr_name} -> parent: {prev_name}")

    # Weapon / Prop bones setup in Edit Mode:
    # 1. Detect weapon bones (prop1, prop2, bip001 prop, weapon, equip, etc.)
    #    CRITICAL: EXCLUDE weaponbox or box (these are back/spine bones, NOT hand weapons)
    #    CRITICAL: EXCLUDE clothing / body / accessory false positives (e.g. skirtBow, bowknot, elbow, etc.)
    #    CRITICAL: Recursively collect ALL children / descendants of weapon bones (e.g. umbrellaBase, umbrellaTop under Weapon_All_JNT)
    # 2. Unparent weapon roots from DEF-hand / hand bones
    # 3. Snap prop.L / prop.R to weapon root or hand
    # 4. Parent weapon roots to prop.L / prop.R
    # 5. Parent prop.L / prop.R to root
    non_weapon_keywords = [
        "skirt", "hair", "dress", "cloth", "ribbon", "bowknot", "knot", "tie",
        "flower", "body", "elbow", "chest", "spine", "sleeve", "pant", "belt",
        "cape", "coat", "tail", "face", "head", "neck", "leg", "arm", "hand",
        "finger", "toe", "foot", "shoulder", "collar"
    ]

    weapon_keywords = [
        "weapon_all_jnt", "weapon", "prop1", "prop2", "bip001 prop", "equip",
        "sword", "lance", "gun", "staff", "dagger", "scroll", "shield", "scythe",
        "umbrella", "garape", "grape"
    ]

    initial_weapon_bones = []
    for b in armature.edit_bones:
        b_low = b.name.lower()
        if "box" in b_low or "weaponbox" in b_low:
            continue
        if b.name in ["prop.L", "prop.R"]:
            continue
        if b.name.startswith("MCH-") or b.name.startswith("ORG-") or b.name.startswith("DEF-"):
            continue

        # Explicit weapon indicators that override non-weapon filters (unless it's an elbow/body bone)
        is_explicit_weapon = (
            b_low.startswith(("weapon", "prop1", "prop2", "equip"))
            or "_weapon_" in b_low
            or "weapon_" in b_low
            or "_weapon" in b_low
            or "_wpn_" in b_low
            or "bip001 prop" in b_low
            or ("prop_" in b_low and "parent" not in b_low)
            or ("_prop" in b_low and "parent" not in b_low)
        )

        if not is_explicit_weapon:
            if any(nw in b_low for nw in non_weapon_keywords):
                continue

        is_weapon = (
            is_explicit_weapon
            or any(k in b_low for k in weapon_keywords)
            or ("prop" in b_low and "parent" not in b_low)
            or (
                ("bow" in b_low)
                and not any(nw in b_low for nw in non_weapon_keywords)
                and (
                    b_low in ["bow", "weapon_bow"]
                    or b_low.startswith(("bow_", "bow.", "bow-"))
                    or "_bow_" in b_low
                    or "-bow" in b_low
                    or "_bow" in b_low
                )
            )
        )

        if is_weapon:
            initial_weapon_bones.append(b)

    # Check if scene has a Weapon or Equip mesh object and include its vertex group bones
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and any(k in obj.name.lower() for k in ["weapon", "equip"]):
            for vg in obj.vertex_groups:
                eb = armature.edit_bones.get(vg.name)
                if eb and eb not in initial_weapon_bones:
                    eb_low = eb.name.lower()
                    if not any(ex in eb_low for ex in ["hand", "root", "spine", "head", "neck", "arm", "leg"]):
                        if eb.name not in ["prop.L", "prop.R"] and not eb.name.startswith(("MCH-", "ORG-", "DEF-")):
                            initial_weapon_bones.append(eb)

    # Recursively collect ALL children and descendants of every detected weapon bone
    weapon_bones_set = set(initial_weapon_bones)
    def collect_descendants(eb):
        for child in eb.children:
            if child.name in ["prop.L", "prop.R"] or child.name.startswith(("MCH-", "ORG-", "DEF-")):
                continue
            c_low = child.name.lower()
            if "box" in c_low or "weaponbox" in c_low:
                continue
            if child not in weapon_bones_set:
                weapon_bones_set.add(child)
                collect_descendants(child)

    for wb in initial_weapon_bones:
        collect_descendants(wb)

    raw_weapon_bones = list(weapon_bones_set)
    print(f"[HSR RIG] Detected {len(raw_weapon_bones)} weapon bones: {[b.name for b in raw_weapon_bones]}")

    def get_weapon_roots(b_list):
        roots = []
        for b in b_list:
            if not b.parent or b.parent not in b_list:
                roots.append(b)
        return roots

    all_roots = get_weapon_roots(raw_weapon_bones)

    roots_L = []
    roots_R = []
    for r in all_roots:
        r_low = r.name.lower()
        p_name = r.parent.name.lower() if r.parent else ""

        is_left = (
            "prop2" in r_low or ".l" in r_low or "_l" in r_low or "left" in r_low
            or "hand.l" in p_name or "l hand" in p_name or ".l" in p_name or "_l" in p_name or "left" in p_name
            or r.head.x > 0.02
        )
        is_right = (
            "prop1" in r_low or ".r" in r_low or "_r" in r_low or "right" in r_low
            or "hand.r" in p_name or "r hand" in p_name or ".r" in p_name or "_r" in p_name or "right" in p_name
            or r.head.x < -0.02
        )

        if ("prop2" in r_low or ".l" in r_low or "hand.l" in p_name or "l hand" in p_name) and not ("prop1" in r_low or ".r" in r_low):
            roots_L.append(r)
        elif ("prop1" in r_low or ".r" in r_low or "hand.r" in p_name or "r hand" in p_name) and not ("prop2" in r_low or ".l" in r_low):
            roots_R.append(r)
        elif is_left and not is_right:
            roots_L.append(r)
        elif is_right and not is_left:
            roots_R.append(r)
        elif r.head.x > 0.02:
            roots_L.append(r)
        elif r.head.x < -0.02:
            roots_R.append(r)
        else:
            # Centered weapon (abs(head.x) <= 0.02) -> Default to dominant Right hand (prop.R)
            if not roots_R:
                roots_R.append(r)
            else:
                roots_L.append(r)

    # Master root bone to parent props to - prioritize root (renamed to root.002) so weapons follow root.002
    root_master = (
        armature.edit_bones.get("root")
        or armature.edit_bones.get("root.002")
        or armature.edit_bones.get("root-inner")
        or armature.edit_bones.get("root.001")
        or armature.edit_bones.get("root-outer")
    )

    # Disconnect weapon root bones from hard-parented hand bones so moving hand doesn't move weapon unless constrained
    for rwb in roots_L + roots_R:
        if rwb.parent and ("hand" in rwb.parent.name.lower() or "wrist" in rwb.parent.name.lower()):
            rwb.parent = None

    # Handle prop.L
    eb_prop_l = armature.edit_bones.get("prop.L")
    if eb_prop_l:
        if roots_L:
            primary_w_l = roots_L[0]
            eb_prop_l.head = primary_w_l.head.copy()
            eb_prop_l.tail = primary_w_l.tail.copy()
            eb_prop_l.roll = primary_w_l.roll
            for rwb in roots_L:
                rwb.parent = eb_prop_l
            if root_master:
                eb_prop_l.parent = root_master
            eb_prop_l.inherit_scale = "FULL"
        else:
            # No weapon for left hand: remove unused prop.L to avoid confusion
            armature.edit_bones.remove(eb_prop_l)
            print("[HSR RIG] No left-hand weapon detected: removed unused 'prop.L'")

    # Handle prop.R
    eb_prop_r = armature.edit_bones.get("prop.R")
    if eb_prop_r:
        if roots_R:
            primary_w_r = roots_R[0]
            eb_prop_r.head = primary_w_r.head.copy()
            eb_prop_r.tail = primary_w_r.tail.copy()
            eb_prop_r.roll = primary_w_r.roll
            for rwb in roots_R:
                rwb.parent = eb_prop_r
            if root_master:
                eb_prop_r.parent = root_master
            eb_prop_r.inherit_scale = "FULL"
        else:
            # No weapon for right hand: remove unused prop.R to avoid confusion
            armature.edit_bones.remove(eb_prop_r)
            print("[HSR RIG] No right-hand weapon detected: removed unused 'prop.R'")

    detected_weapon_bone_names = [b.name for b in raw_weapon_bones]

    # Tail IK bones setup in Edit Mode:
    # Create IK controller bone at the tip of each tail chain, parented to root_master
    tail_ik_info = []
    for pfx, num_names in tail_groups.items():
        if len(num_names) >= 1:
            num_names.sort(key=lambda x: x[0])
            last_name = num_names[-1][1]
            last_eb = armature.edit_bones.get(last_name)
            if last_eb:
                ik_name = "tail_ik" if len(tail_groups) == 1 else f"tail_ik_{pfx.strip('_- ')}"
                if ik_name in armature.edit_bones:
                    ik_eb = armature.edit_bones[ik_name]
                else:
                    ik_eb = armature.edit_bones.new(ik_name)
                ik_eb.head = last_eb.tail.copy()
                dir_vec = (last_eb.tail - last_eb.head).normalized() if (last_eb.tail - last_eb.head).length > 1e-4 else Vector((0, 0, 1))
                ik_eb.tail = last_eb.tail.copy() + dir_vec * max(last_eb.length * 2.0, 0.15)
                ik_eb.roll = last_eb.roll
                if root_master:
                    ik_eb.parent = root_master
                ik_eb.use_deform = False
                tail_ik_info.append((ik_name, last_name, len(num_names)))
                print(f"[TAIL IK] Created {ik_name} at tip of {last_name} with chain count {len(num_names)}")

    # RENAME imported bones (Genshin 3-tier root: root=Master, root.001=Offset, root.002=Rigify internal)
    rename_bones_list = [("root", "root.002")]
    rename_bones_list.append(("root-inner", "root.001"))
    rename_bones_list.append(("root-outer", "root"))
    
    rename_bones_list.append(("torso", "torso.002"))
    rename_bones_list.append(("torso-inner", "torso.001"))
    rename_bones_list.append(("torso-outer", "torso"))
    
    rename_bones_list.append(("ik-pivot-L", "foot_ik_pivot.L"))
    rename_bones_list.append(("mch-ik-pivot-L", "MCH-foot_ik_pivot.L"))
    rename_bones_list.append(("ik-sub-pivot-L", "foot_ik_sub.L"))
    rename_bones_list.append(("ik-target-L", "MCH-thigh_ik_target_sub.L"))
    
    rename_bones_list.append(("ik-pivot-R", "foot_ik_pivot.R"))
    rename_bones_list.append(("mch-ik-pivot-R", "MCH-foot_ik_pivot.R"))
    rename_bones_list.append(("ik-sub-pivot-R", "foot_ik_sub.R"))
    rename_bones_list.append(("ik-target-R", "MCH-thigh_ik_target_sub.R"))
    
    rename_bones_list.append(("hand_ik.L", "hand_ik_wrist.L"))
    rename_bones_list.append(("hand-ik-L", "hand_ik.L"))
    rename_bones_list.append(("hand-ik-pivot-L", "hand_ik_pivot.L"))
    rename_bones_list.append(("mch-hand-ik-pivot-L", "MCH-hand_ik_pivot.L"))
    rename_bones_list.append(("mch-hand-ik-wrist-L", "MCH-hand_ik_wrist.L"))
    
    rename_bones_list.append(("hand_ik.R", "hand_ik_wrist.R"))
    rename_bones_list.append(("hand-ik-R", "hand_ik.R"))
    rename_bones_list.append(("hand-ik-pivot-R", "hand_ik_pivot.R"))
    rename_bones_list.append(("mch-hand-ik-pivot-R", "MCH-hand_ik_pivot.R"))
    rename_bones_list.append(("mch-hand-ik-wrist-R", "MCH-hand_ik_wrist.R"))

    
    # TORSO POS fixing
    # armature.edit_bones['torso'].roll = -1.5708
    torso_head_pos = armature.edit_bones['torso'].head.copy()
    torso_tail_pos = armature.edit_bones['torso'].tail.copy()
    
    armature.edit_bones['torso-inner'].head = torso_head_pos
    armature.edit_bones['torso-inner'].tail = torso_tail_pos
    armature.edit_bones['torso-inner'].tail.y += 0.05
    
    armature.edit_bones['torso-outer'].head = torso_head_pos
    armature.edit_bones['torso-outer'].tail = torso_tail_pos
    armature.edit_bones['torso-outer'].tail.y += 0.1
    
    armature.edit_bones['torso_pivot.002'].head = torso_head_pos
    armature.edit_bones['torso_pivot.002'].tail = torso_tail_pos
    
    armature.edit_bones['MCH-torso_pivot.002'].head = torso_head_pos
    armature.edit_bones['MCH-torso_pivot.002'].tail = torso_tail_pos
    armature.edit_bones['MCH-torso_pivot.002'].length -= 0.09
    
    # FOOT POS fixing: Remember to use old bone names pre renaming
    foot_L_z_diff = armature.edit_bones['foot_ik.L'].tail.z - armature.edit_bones['foot_spin_ik.L'].tail.z
    foot_R_z_diff = armature.edit_bones['foot_ik.R'].tail.z - armature.edit_bones['foot_spin_ik.R'].tail.z
       
    armature.edit_bones['ik-sub-pivot-L'].head = armature.edit_bones['foot_ik.L'].head.copy()
    armature.edit_bones['ik-sub-pivot-L'].tail = armature.edit_bones['foot_ik.L'].tail.copy()
    
    armature.edit_bones['ik-sub-pivot-R'].head = armature.edit_bones['foot_ik.R'].head.copy()
    armature.edit_bones['ik-sub-pivot-R'].tail = armature.edit_bones['foot_ik.R'].tail.copy()
    
    armature.edit_bones['ik-pivot-L'].head = armature.edit_bones['MCH-heel.02_roll2.L'].head.copy()
    armature.edit_bones['ik-pivot-L'].tail = armature.edit_bones['MCH-heel.02_roll2.L'].tail.copy()
    armature.edit_bones['ik-pivot-L'].tail.y += 0.05
    
    armature.edit_bones['ik-pivot-R'].head = armature.edit_bones['MCH-heel.02_roll2.R'].head.copy()
    armature.edit_bones['ik-pivot-R'].tail = armature.edit_bones['MCH-heel.02_roll2.R'].tail.copy()
    armature.edit_bones['ik-pivot-R'].tail.y += 0.05
    
    armature.edit_bones['mch-ik-pivot-L'].head = armature.edit_bones['MCH-heel.02_roll2.L'].head.copy()
    armature.edit_bones['mch-ik-pivot-L'].tail = armature.edit_bones['MCH-heel.02_roll2.L'].tail.copy()
    
    armature.edit_bones['mch-ik-pivot-R'].head = armature.edit_bones['MCH-heel.02_roll2.R'].head.copy()
    armature.edit_bones['mch-ik-pivot-R'].tail = armature.edit_bones['MCH-heel.02_roll2.R'].tail.copy()
    
    armature.edit_bones['ik-target-L'].head = armature.edit_bones['foot_tweak.L'].head.copy()
    armature.edit_bones['ik-target-L'].tail = armature.edit_bones['foot_tweak.L'].tail.copy()
    
    armature.edit_bones['ik-target-R'].head = armature.edit_bones['foot_tweak.R'].head.copy()
    armature.edit_bones['ik-target-R'].tail = armature.edit_bones['foot_tweak.R'].tail.copy()

    # HEEL: move foot_heel_ik back to the anatomical heel like Miyabi Foot_Roll.
    # Minimal/safe: only translate the control (orientation, parent and MCH
    # constraints untouched, widget shape untouched), so rest pose cannot deform:
    # the MCH chain copies heel LOCAL rotation only, and it stays zero at rest.
    for _side in ('.L', '.R'):
        _heel = f'foot_heel_ik{_side}'
        _foot_ik = f'foot_ik{_side}'
        _spin = f'foot_spin_ik{_side}'
        if _heel in armature.edit_bones and _foot_ik in armature.edit_bones:
            try:
                _hb = armature.edit_bones[_heel]
                _ankle = armature.edit_bones[_foot_ik].head.copy()
                if _spin in armature.edit_bones:
                    _ball = armature.edit_bones[_spin].head.copy()
                else:
                    _ball = armature.edit_bones[_foot_ik].tail.copy()
                _y_span = _ankle.y - _ball.y
                _z_span = _ankle.z - _ball.z
                if abs(_y_span) < 1e-5:
                    _toe = f'toe_ik{_side}'
                    if _toe in armature.edit_bones:
                        _ball = armature.edit_bones[_toe].head.copy()
                        _y_span = _ankle.y - _ball.y
                        _z_span = _ankle.z - _ball.z
                if abs(_y_span) < 1e-5:
                    continue
                _vec = _hb.tail - _hb.head
                _heel_y = _ankle.y + _y_span * 0.88
                if abs(_z_span) > 1e-5:
                    _heel_z = _ankle.z - _z_span * 0.37
                else:
                    _heel_z = _hb.head.z
                _hb.head = Vector((_ankle.x, _heel_y, _heel_z))
                _hb.tail = _hb.head + _vec
            except Exception as _e:
                print(f"[HSR RIG] heel translate skipped {_heel}: {_e}")
    
    foot_L_x_diff = armature.edit_bones['ik-sub-pivot-L'].tail.x - armature.edit_bones['foot_spin_ik.L'].tail.x
    foot_R_x_diff = armature.edit_bones['ik-sub-pivot-R'].tail.x - armature.edit_bones['foot_spin_ik.R'].tail.x
    
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].head = armature.edit_bones['MCH-shin_ik.L'].head.copy()
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].tail.z = armature.edit_bones['MCH-shin_ik.L'].tail.z
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].tail.x = armature.edit_bones['MCH-shin_ik.L'].tail.x
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].roll = 0
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].length = .02
    
    armature.edit_bones['shin_tweak-pin.L'].head = armature.edit_bones['MCH-shin_ik.L'].head.copy()
    armature.edit_bones['shin_tweak-pin.L'].tail = armature.edit_bones['MCH-shin_ik.L'].tail.copy()
    armature.edit_bones['shin_tweak-pin.L'].roll = armature.edit_bones['MCH-shin_ik.L'].roll
    armature.edit_bones['shin_tweak-pin.L'].length -= 0.15
    
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].head = armature.edit_bones['MCH-shin_ik.R'].head.copy()
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].tail.z = armature.edit_bones['MCH-shin_ik.R'].tail.z
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].tail.x = armature.edit_bones['MCH-shin_ik.R'].tail.x
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].roll = 0
    armature.edit_bones['MCH-shin_tweak-pin.parent.R'].length = .02
    
    armature.edit_bones['shin_tweak-pin.R'].head = armature.edit_bones['MCH-shin_ik.R'].head.copy()
    armature.edit_bones['shin_tweak-pin.R'].tail = armature.edit_bones['MCH-shin_ik.R'].tail.copy()
    armature.edit_bones['shin_tweak-pin.R'].roll = armature.edit_bones['MCH-shin_ik.R'].roll
    armature.edit_bones['shin_tweak-pin.R'].length -= 0.15
    
    # HAND POS Fixing
    armature.edit_bones['hand-ik-L'].head = armature.edit_bones['hand_ik.L'].head.copy()
    armature.edit_bones['hand-ik-L'].tail = armature.edit_bones['hand_ik.L'].tail.copy()
    armature.edit_bones['hand-ik-L'].roll = armature.edit_bones['hand_ik.L'].roll
    
    armature.edit_bones['hand-ik-pivot-L'].head = armature.edit_bones['hand_ik.L'].head.copy()
    armature.edit_bones['hand-ik-pivot-L'].tail = armature.edit_bones['hand_ik.L'].tail.copy()
    armature.edit_bones['hand-ik-pivot-L'].roll = armature.edit_bones['hand_ik.L'].roll
    
    armature.edit_bones['mch-hand-ik-pivot-L'].head = armature.edit_bones['hand_ik.L'].head.copy()
    armature.edit_bones['mch-hand-ik-pivot-L'].tail = armature.edit_bones['hand_ik.L'].tail.copy()
    armature.edit_bones['mch-hand-ik-pivot-L'].roll = armature.edit_bones['hand_ik.L'].roll
    armature.edit_bones['mch-hand-ik-pivot-L'].length -= 0.03
    
    armature.edit_bones['mch-hand-ik-wrist-L'].head = armature.edit_bones['hand_ik.L'].head.copy()
    armature.edit_bones['mch-hand-ik-wrist-L'].tail = armature.edit_bones['hand_ik.L'].tail.copy()
    armature.edit_bones['mch-hand-ik-wrist-L'].roll = armature.edit_bones['hand_ik.L'].roll
    armature.edit_bones['mch-hand-ik-wrist-L'].length -= 0.04
    
    armature.edit_bones['hand-ik-R'].head = armature.edit_bones['hand_ik.R'].head.copy()
    armature.edit_bones['hand-ik-R'].tail = armature.edit_bones['hand_ik.R'].tail.copy()
    armature.edit_bones['hand-ik-R'].roll = armature.edit_bones['hand_ik.R'].roll
    
    armature.edit_bones['hand-ik-pivot-R'].head = armature.edit_bones['hand_ik.R'].head.copy()
    armature.edit_bones['hand-ik-pivot-R'].tail = armature.edit_bones['hand_ik.R'].tail.copy()
    armature.edit_bones['hand-ik-pivot-R'].roll = armature.edit_bones['hand_ik.R'].roll
    
    armature.edit_bones['mch-hand-ik-pivot-R'].head = armature.edit_bones['hand_ik.R'].head.copy()
    armature.edit_bones['mch-hand-ik-pivot-R'].tail = armature.edit_bones['hand_ik.R'].tail.copy()
    armature.edit_bones['mch-hand-ik-pivot-R'].roll = armature.edit_bones['hand_ik.R'].roll
    armature.edit_bones['mch-hand-ik-pivot-R'].length -= 0.03
    
    armature.edit_bones['mch-hand-ik-wrist-R'].head = armature.edit_bones['hand_ik.R'].head.copy()
    armature.edit_bones['mch-hand-ik-wrist-R'].tail = armature.edit_bones['hand_ik.R'].tail.copy()
    armature.edit_bones['mch-hand-ik-wrist-R'].roll = armature.edit_bones['hand_ik.R'].roll
    armature.edit_bones['mch-hand-ik-wrist-R'].length -= 0.04
    
    armature.edit_bones['MCH-forearm_tweak-pin.parent.L'].head = armature.edit_bones['MCH-forearm_ik.L'].head.copy()
    armature.edit_bones['MCH-forearm_tweak-pin.parent.L'].tail.z = armature.edit_bones['MCH-forearm_ik.L'].tail.z
    armature.edit_bones['MCH-forearm_tweak-pin.parent.L'].tail.x = armature.edit_bones['MCH-forearm_ik.L'].tail.x
    armature.edit_bones['MCH-forearm_tweak-pin.parent.L'].roll = 0
    armature.edit_bones['MCH-forearm_tweak-pin.parent.L'].length = .02
    
    armature.edit_bones['forearm_tweak-pin.L'].head = armature.edit_bones['MCH-forearm_ik.L'].head.copy()
    armature.edit_bones['forearm_tweak-pin.L'].tail = armature.edit_bones['MCH-forearm_ik.L'].tail.copy()
    armature.edit_bones['forearm_tweak-pin.L'].roll = armature.edit_bones['MCH-forearm_ik.L'].roll
    armature.edit_bones['forearm_tweak-pin.L'].length -= 0.15
    
    armature.edit_bones['MCH-forearm_tweak-pin.parent.R'].head = armature.edit_bones['MCH-forearm_ik.R'].head.copy()
    armature.edit_bones['MCH-forearm_tweak-pin.parent.R'].tail.z = armature.edit_bones['MCH-forearm_ik.R'].tail.z
    armature.edit_bones['MCH-forearm_tweak-pin.parent.R'].tail.x = armature.edit_bones['MCH-forearm_ik.R'].tail.x
    armature.edit_bones['MCH-forearm_tweak-pin.parent.R'].roll = 0
    armature.edit_bones['MCH-forearm_tweak-pin.parent.R'].length = .02
    
    armature.edit_bones['forearm_tweak-pin.R'].head = armature.edit_bones['MCH-forearm_ik.R'].head.copy()
    armature.edit_bones['forearm_tweak-pin.R'].tail = armature.edit_bones['MCH-forearm_ik.R'].tail.copy()
    armature.edit_bones['forearm_tweak-pin.R'].roll = armature.edit_bones['MCH-forearm_ik.R'].roll
    armature.edit_bones['forearm_tweak-pin.R'].length -= 0.15
    


   
    # Eye tracking is handled entirely by Isaac FaceRig (Eye-Track-Master)
    pass

    # Still in edit mode, select Neck/Head bone and extract the Z loc 
    neck_bone = armature.edit_bones.get('neck')
    neck_pos = neck_bone.head[2] if neck_bone else 1.0

    # Let's position our head controller bone here. We need it to match our head bone's position
    head_bone = armature.edit_bones.get('head')
    head_pos_head2 = head_bone.head[2] if head_bone else 1.2
    head_pos_tail2 = head_bone.tail[2] if head_bone else 1.3
    head_pos_head1 = head_bone.head[1] if head_bone else 0.0
    head_pos_tail1 = head_bone.tail[1] if head_bone else 0.0

    # Select the head controller bone and position w/ head bone's location.
    if 'head-controller' not in armature.edit_bones:
        head_cont_bone = armature.edit_bones.new('head-controller')
        head_cont_bone.head = (0, 0, 0)
        head_cont_bone.tail = (0, 0, 1)
    head_cont_bone = armature.edit_bones['head-controller']
    head_cont_bone.head[0] = 0
    head_cont_bone.head[1] = -0.3
    head_cont_bone.head[2] = head_pos_head2
    head_cont_bone.tail[0] = 0
    head_cont_bone.tail[1] = -0.3
    head_cont_bone.tail[2] = head_pos_tail2
    # Create MCH-head-controller-parent so head-controller NEVER parents to head
    # (prevents cyclic dependency and infinite rotation loop with head Damped Track)
    if 'MCH-head-controller-parent' not in armature.edit_bones:
        mch_hp = armature.edit_bones.new('MCH-head-controller-parent')
    else:
        mch_hp = armature.edit_bones['MCH-head-controller-parent']
    mch_hp.head = head_cont_bone.head.copy()
    mch_hp.tail = head_cont_bone.tail.copy()
    mch_hp.length = 0.05
    mch_hp.roll = 0
    mch_hp.parent = None
    head_cont_bone.parent = mch_hp

    # Delete ugly lines that connect to the pole bones.
    def del_bone(bone_name):
        to_del = armature.edit_bones.get(bone_name)
        armature.edit_bones.remove(to_del)
        
    del_bone("VIS_upper_arm_ik_pole.L")
    del_bone("VIS_upper_arm_ik_pole.R")
    del_bone("VIS_thigh_ik_pole.L")
    del_bone("VIS_thigh_ik_pole.R")
    
    del_bone("palm.L")
    del_bone("palm.R")

    # Skirt collisions disabled for now per user request
    all_skirt_ctrl_bones = []
    all_skirt_deform_bones = []
    all_skirt_tip_bones = []
    skirt_ctrl_chains_data = []                                                            

    # Switch to pose mode for subsequent operations
    bpy.ops.object.mode_set(mode='POSE')
    faceplate_arm = bpy.context.scene.objects[char_name+"Rig"]

    # Begin moving extra wgt bones to the wgt collection while discarding old collections
    # 1 Root and Eye Bones
    move_into_collection("eye circle","wgt")
    move_into_collection("eye controller","wgt")
    move_into_collection("root plate","wgt")
    move_into_collection("head-control-shape","wgt")

    # 2 Pelvis Bones
    to_del_coll = bpy.data.collections.get("wgt.002")
    if to_del_coll:
        for obj in to_del_coll.objects:
            move_into_collection(obj.name,"wgt")
    
    # 3 feet Bones
    to_del_coll = bpy.data.collections.get("wgt.003")
    if to_del_coll:
        for obj in to_del_coll.objects:
            move_into_collection(obj.name,"wgt")
        
    # 4 hand Bones
    to_del_coll = bpy.data.collections.get("wgt.004")
    if to_del_coll:
        for obj in to_del_coll.objects:
            move_into_collection(obj.name,"wgt")
        
    # idk bro math is wrong delete whatever this is too
    to_del_coll = bpy.data.collections.get("wgt.005")
    if to_del_coll:
        for obj in to_del_coll.objects:
            move_into_collection(obj.name,"wgt")
        
    to_del_coll = bpy.data.collections.get("wgt.006")
    if to_del_coll:
        for obj in to_del_coll.objects:
            move_into_collection(obj.name,"wgt")

    # After moving into collection, delete the old empty ones.
    for append_name in ["append_Root", "append_Eyes", "append_Pelvis", "append_Foot", "append_Hand", "append_Props"]:
        app_coll = bpy.data.collections.get(append_name)
        if app_coll:
            bpy.data.collections.remove(app_coll, do_unlink=True)

    # Adding Shape Key Drivers
    ourRig = char_name+"Rig"
    
    # Initialize UI properties and gear shape on plate-settings (Genshin convention)
    rig_obj_ref = bpy.data.objects.get(ourRig)
    if rig_obj_ref and hasattr(rig_obj_ref, "pose") and rig_obj_ref.pose:
        plate = rig_obj_ref.pose.bones.get("plate-settings")
        if plate:
            # Match the exact gear mesh of arm controls (upper_arm_parent.L/R)
            gear_obj = None
            for arm_bname in ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.L", "thigh_parent.R"]:
                pb_gear = rig_obj_ref.pose.bones.get(arm_bname)
                if pb_gear and pb_gear.custom_shape:
                    gear_obj = pb_gear.custom_shape
                    break
            if not gear_obj:
                gear_obj = bpy.data.objects.get("setting-circle")

            if gear_obj:
                plate.custom_shape = gear_obj
                plate.use_custom_shape_bone_size = False
                plate.custom_shape_scale_xyz = (0.05, 0.05, 0.05)
                plate.custom_shape_rotation_euler = (1.5708, 0.0, 0.0)
                plate.custom_shape_translation = (0.0, 0.0, 0.0)

            def set_prop(pb_bone, prop_name, default_val, min_val=0.0, max_val=1.0, description=""):
                if not pb_bone:
                    return
                if prop_name not in pb_bone:
                    pb_bone[prop_name] = default_val
                try:
                    pb_bone.id_properties_ui(prop_name).update(
                        default=default_val,
                        min=min_val,
                        max=max_val,
                        soft_min=min_val,
                        soft_max=max_val,
                        description=description
                    )
                except Exception:
                    pass

            if "Toggle Shoulder Constraints" in plate:
                del plate["Toggle Shoulder Constraints"]
            if "Viewport Outlines" in plate:
                del plate["Viewport Outlines"]
            set_prop(plate, "Head Follow", 1.00, 0.0, 1.0, "Head Follow")
            set_prop(plate, "Neck Follow", 1.00, 0.0, 1.0, "Neck Follow")
            set_prop(plate, "Use Head Controller", 0.00, 0.0, 1.0, "Use Head Tracker Controller")
            set_prop(plate, "Adjust Pupil Distance", 1.00, 0.0, 1.0, "Adjust Pupil Distance")
            plate["EyeCorrection"] = 1.00
            set_prop(plate, "Shirt_Follow", 1.00, 0.0, 1.0, "Shirt Follow")

    # Let's go into object mode and select the three face parts to begin adding shape key drivers
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.object.select_all(action='DESELECT')


    def makeCon(shape_key,bone_name,expression,transform):
        # Get the bone object by name
        armature = bpy.context.scene.objects[ourRig]  
        bone = armature.pose.bones[bone_name]

        # Create a driver for the shape key
        shape_key = obj.data.shape_keys.key_blocks[shape_key]  
        driver = shape_key.driver_add("value").driver

        # Create variables for the driver
        var = driver.variables.new()
        var.name = "bone"
        var.type = 'TRANSFORMS'
        var.targets[0].id = armature
        var.targets[0].bone_target = bone_name
        var.targets[0].transform_space = 'LOCAL_SPACE'
        var.targets[0].transform_type = transform

        # Create the scripted expression driver
        driver.type = 'SCRIPTED'
        driver.expression = expression  

        # Update the dependencies
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        

    # Since we're still in object mode, here we can add the head pole object in the neck to track head movement
    head_pole_obj = bpy.data.objects.get("Head_Pole")
    if not head_pole_obj:
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        head_pole_obj = bpy.context.active_object
        head_pole_obj.name = "Head_Pole"
    head_pole_obj.empty_display_size = 0.01
    head_pole_obj.parent = bpy.data.objects.get(char_name+"Rig") or bpy.context.object
    head_pole_obj.parent_type = "BONE"
    head_pole_obj.parent_bone = "neck"


    # Remove any drivers on viewport outlines so user has direct control
    def setup_viewport_outlines(prop):
        try:
            prop.driver_remove("show_viewport")
        except:
            pass
        try:
            prop.driver_remove("show_render")
        except:
            pass

    for mesh in [obj for obj in bpy.data.objects if obj.type == 'MESH']:
        for modifier in mesh.modifiers:
            if "Outline" in modifier.name or "outlines" in modifier.name.lower() or "Outlines" in modifier.name:
                setup_viewport_outlines(modifier)

    # handled list of face SK
    handled_sks = ['Basis', 'Mouth_Default', 'Mouth_A01', 'Mouth_Open01', 'Mouth_Smile01', 'Mouth_Smile02', 'Mouth_Angry01', 'Mouth_Angry02',
    'Mouth_Angry03', 'Mouth_Fury01', 'Mouth_Doya01', 'Mouth_Doya02', 'Mouth_Neko01', 'Mouth_Pero01', 'Mouth_Pero02', 'Mouth_Line01', 'Mouth_Line02',
    'Mouth_BigTongue01', 'Brow_Default', 'Brow_Trouble_L', 'Brow_Trouble_R', 'Brow_Smily_L', 'Brow_Smily_R',
    'Brow_Angry_L', 'Brow_Angry_R', 'Brow_Shy_L', 'Brow_Shy_R', 'Brow_Up_L', 'Brow_Up_R', 'Brow_Down_L', 'Brow_Down_R', 'Brow_Squeeze_L', 'Brow_Squeeze_R', 
    'Eye_Default', 'Eye_WinkA_L', 'Eye_WinkA_R', 'Eye_WinkB_L', 'Eye_WinkB_R', 'Eye_WinkC_L', 'Eye_WinkC_R', 'Eye_Ha', 'Eye_Jito', 'Eye_Wail', 
    'Eye_Hostility', 'Eye_Tired', 'Eye_WUp', 'Eye_WDown', 'Eye_Lowereyelid']


    def get_shape_keys(obj_name, handled_sks):
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.data.shape_keys:
            return [shape_key.name for shape_key in obj.data.shape_keys.key_blocks if shape_key.name not in handled_sks]
        return []

    # Get shape keys for the face. We can dynamically make SK sliders for shapekeys we do not handle in the face panel
    face_shape_keys = get_shape_keys("Face", handled_sks)

    try:
        lp_ver_num = float(lighting_panel_version)
    except (ValueError, TypeError):
        lp_ver_num = 4.0 if lighting_panel_version else 0.0
    if lp_ver_num >= 4 and len(face_shape_keys) > 0:
        bpy.ops.wm.append(filename='append_extras', directory=path_to_file)

        # Select the rigs in question
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects["extras"].select_set(True) # select the extras
        bpy.data.objects[char_name+"Rig"].select_set(True) # select the char rig
        bpy.context.view_layer.objects.active = bpy.data.objects[char_name+"Rig"] # ensure the rig is the active object
        bpy.ops.object.join() # join them
        bpy.ops.object.mode_set(mode='EDIT')
        armature.edit_bones['extras-panel'].parent = armature.edit_bones['plate-settings']
        armature.edit_bones['extras-panel'].head = armature.edit_bones['plate-settings'].head
        armature.edit_bones['extras-panel'].head.x += 0.723336
        armature.edit_bones['extras-panel'].tail.x = armature.edit_bones['extras-panel'].head.x
        armature.edit_bones['extras-panel'].head.z -= 0.01397
        armature.edit_bones['extras-panel'].tail.z = armature.edit_bones['extras-panel'].head.z + 1

        extras_position = armature.edit_bones['extras-panel'].head

        bpy.ops.object.mode_set(mode='OBJECT')

        to_del_coll = bpy.data.collections.get("wgt.008") # note to future self, at some point, we can switch to a single mechanism that identifies wgt.00X and moves into wgt
        if to_del_coll:
            for obj in to_del_coll.objects:
                move_into_collection(obj.name,"wgt")

        ext_coll = bpy.data.collections.get("append_extras")
        if ext_coll:
            bpy.data.collections.remove(ext_coll,do_unlink=True)

        # From extra header's position, we can setup the first position to use
        slider_starting_position = extras_position.copy()
        slider_starting_position[0] -= 0.058497
        slider_starting_position[1] = slider_starting_position[2] - 0.04631
        slider_starting_position[2] = 0

        count = 0

        # For each shapekey, we can append a copy of the slider needed to support it.
        for sk in face_shape_keys:
            bpy.ops.wm.append(filename='append_slider', directory=path_to_file)

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            # Select custom face armature
            bpy.data.objects["slider_rig"].select_set(True)

            bpy.data.objects[char_name+"Rig"].select_set(True)
            
            bpy.context.view_layer.objects.active = bpy.data.objects[char_name+"Rig"]

            bpy.ops.object.join()

            bpy.ops.object.mode_set(mode='EDIT')
            # Position the Slider Frame
            armature.edit_bones['slider-frame'].parent = armature.edit_bones['extras-panel']
            armature.edit_bones['slider-frame'].head = armature.edit_bones['extras-panel'].head
            armature.edit_bones['slider-frame'].head.x -= 0.058479
            armature.edit_bones['slider-frame'].tail.x = armature.edit_bones['slider-frame'].head.x
            armature.edit_bones['slider-frame'].head.z -= (0.0466 + (count*0.03042)) 
            armature.edit_bones['slider-frame'].tail.z = armature.edit_bones['slider-frame'].head.z + 1

            # Position the slider itself
            armature.edit_bones['slider'].head = armature.edit_bones['slider-frame'].head
            armature.edit_bones['slider'].tail = armature.edit_bones['slider-frame'].tail
            armature.edit_bones['slider'].head.x -= 0.030134
            armature.edit_bones['slider'].tail.x = armature.edit_bones['slider'].head.x

            count += 1
            
            bpy.ops.object.mode_set(mode='POSE')

            bpy.context.object.pose.bones.get('slider-frame').name = f'slider-frame-{sk}'
            bpy.context.object.pose.bones.get('slider').name = f'slider-{sk}'

            this_obj.pose.bones[f"slider-frame-{sk}"].bone.hide_select = True

            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.data.objects.get("Face")

            obj = bpy.data.objects.get("Face")
            makeCon(sk,f"slider-{sk}","bone * 16.7","LOC_X")
            merge_duplicate_collections("wgt")
            merge_duplicate_collections("append_slider")
            slider_coll = bpy.data.collections.get("append_slider")
            if slider_coll:
                bpy.data.collections.remove(slider_coll,do_unlink=True)


    # Let's go into object mode and select the body for the pupil shape keys, and to control our glow sliders.
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects.get("Body")  
    bpy.ops.object.select_all(action='DESELECT')


    # Going into pose mode with our character selected.
    bpy.ops.object.select_all(action='DESELECT')
    our_char =  bpy.data.objects.get(char_name+"Rig")
    if our_char:
        our_char.select_set(True)
        bpy.context.view_layer.objects.active = our_char
        
        bpy.ops.object.mode_set(mode='POSE')
        
        
    def add_driver_to_bone_transform(bone, transform, channel, variables, expr):
        this_bone = bpy.context.scene.objects[char_name+"Rig"].pose.bones[bone]
        driver = this_bone.driver_add(transform, channel).driver
        
        # Iterate through the list of variables and create each one
        for var_info in variables:
            var = driver.variables.new()
            var.name = var_info['var_name']
            if var_info['var_type'] == 'TRANSFORMS':
                var.type = 'TRANSFORMS'
                var.targets[0].id = bpy.data.objects.get(ourRig)
                var.targets[0].bone_target = var_info['target']
                var.targets[0].transform_space = var_info['trans_space']
                var.targets[0].transform_type = var_info['trans_type']
            elif var_info['var_type'] == 'SINGLE_PROP':
                var.type = 'SINGLE_PROP'
                var.targets[0].id = bpy.data.objects.get(ourRig)
                var.targets[0].data_path = var_info["data_path"]
            
        
        # Create the scripted expression driver
        driver.type = 'SCRIPTED'
        driver.expression = expr

        # Update the dependencies
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()

    try:
        add_driver_to_bone_transform("eyelid-invis-control", 
        "location", 1, [
            {"var_name":"var", "var_type":"TRANSFORMS", "target":"eyetrack", "trans_space":"LOCAL_SPACE", "trans_type":"LOC_Y"}
        ], "var * 5")
    except: 
        pass
        
    # Note: EyeCorrection (pupil wink pushback) is configured dynamically on fused Isaac FaceRig (eye_L/R)
    

    # Default limbs to IK mode (0.0) with zero stretch; controls stay native on limb gears (Genshin convention)
    rig_obj = bpy.data.objects.get(char_name + "Rig") or bpy.data.objects.get("rigify") or bpy.context.object
    if rig_obj and hasattr(rig_obj, "pose") and rig_obj.pose:
        for b_name in ["thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"]:
            pb = rig_obj.pose.bones.get(b_name)
            if pb:
                pb["IK_FK"] = 0.0
                pb["IK_Stretch"] = 0.0
                if "FK_limb_follow" in pb:
                    pb["FK_limb_follow"] = 1.0
        
    if use_arm_ik_poles:
        if "upper_arm_parent.L" in bpy.data.objects[char_name+"Rig"].pose.bones:
            bpy.data.objects[char_name+"Rig"].pose.bones["upper_arm_parent.L"]["pole_vector"] = True
        if "upper_arm_parent.R" in bpy.data.objects[char_name+"Rig"].pose.bones:
            bpy.data.objects[char_name+"Rig"].pose.bones["upper_arm_parent.R"]["pole_vector"] = True
        
    if use_leg_ik_poles:
        if "thigh_parent.L" in bpy.data.objects[char_name+"Rig"].pose.bones:
            bpy.data.objects[char_name+"Rig"].pose.bones["thigh_parent.L"]["pole_vector"] = True
        if "thigh_parent.R" in bpy.data.objects[char_name+"Rig"].pose.bones:
            bpy.data.objects[char_name+"Rig"].pose.bones["thigh_parent.R"]["pole_vector"] = True

    for t_name in ["torso", "torso.002"]:
        if t_name in bpy.data.objects[char_name+"Rig"].pose.bones:
            pb_t = bpy.data.objects[char_name+"Rig"].pose.bones[t_name]
            if "head_follow" in pb_t:
                pb_t["head_follow"] = 1.0
            if "neck_follow" in pb_t:
                pb_t["neck_follow"] = 1.0
    # Configure IK_parent with dropdown items matching Rigify's Pole Parent dropdown
    def setup_ik_parent_dropdown(bone_name, default_val=1):
        rig_obj = bpy.data.objects.get(char_name + "Rig")
        if not rig_obj or not hasattr(rig_obj, "pose") or not rig_obj.pose:
            return
        pb = rig_obj.pose.bones.get(bone_name)
        if not pb or "IK_parent" not in pb:
            return
        try:
            ui = pb.id_properties_ui("IK_parent")
            curr = ui.as_dict()
            curr_items = curr.get("items")
            if curr_items:
                items_tuples = [(it[0], it[1], it[2]) for it in curr_items]
            else:
                items_tuples = [
                    ("P0", "None", ""),
                    ("P1", "Root", ""),
                    ("P2", "Torso", ""),
                    ("P3", "Hips", ""),
                    ("P4", "Chest", ""),
                    ("P5", "Head", ""),
                ]
            ui.update(items=items_tuples, default=default_val)
            pb["IK_parent"] = default_val
        except Exception as ex:
            print(f"[Rig Warning] Failed to setup dropdown for {bone_name}.IK_parent: {ex}")

    setup_ik_parent_dropdown("upper_arm_parent.L", default_val=1)
    setup_ik_parent_dropdown("upper_arm_parent.R", default_val=1)
    setup_ik_parent_dropdown("thigh_parent.L", default_val=1)
    setup_ik_parent_dropdown("thigh_parent.R", default_val=1)

    # Ensure shoulders are completely clean and free with NO constraints (matching Miyabi reference rig)
    for sh_name in ['shoulder.L', 'shoulder.R']:
        pb_sh = bpy.context.scene.objects[ourRig].pose.bones.get(sh_name)
        if pb_sh:
            for c in list(pb_sh.constraints):
                if c.type in ['DAMPED_TRACK', 'COPY_LOCATION', 'TRACK_TO', 'LOCKED_TRACK']:
                    pb_sh.constraints.remove(c)

    # Configure prop bones: make widgets large and visible, completely free from hand constraints
    arm_obj_ref = bpy.context.scene.objects.get(ourRig) or our_char
    if arm_obj_ref and hasattr(arm_obj_ref, "pose") and arm_obj_ref.pose:
        for prop_name in ["prop.L", "prop.R"]:
            pb_prop = arm_obj_ref.pose.bones.get(prop_name)
            if pb_prop:
                for c in list(pb_prop.constraints):
                    if c.type == 'CHILD_OF' and (c.name == "Poner en mano" or "hand" in (c.subtarget or "").lower()):
                        pb_prop.constraints.remove(c)
                if "Poner en mano" in pb_prop:
                    del pb_prop["Poner en mano"]
                if "_RNA_UI" in pb_prop and "Poner en mano" in pb_prop["_RNA_UI"]:
                    del pb_prop["_RNA_UI"]["Poner en mano"]
                pb_prop.use_custom_shape_bone_size = False
                pb_prop.custom_shape_scale_xyz = (0.35, 0.35, 0.35)
        for h_bone in ["hand_ik.L", "hand_fk.L", "hand_ik.R", "hand_fk.R"]:
            h_pb = arm_obj_ref.pose.bones.get(h_bone)
            if h_pb:
                if "Poner en mano" in h_pb:
                    del h_pb["Poner en mano"]
                if "_RNA_UI" in h_pb and "Poner en mano" in h_pb["_RNA_UI"]:
                    del h_pb["_RNA_UI"]["Poner en mano"]
    
    # Eye bone constraints handled by Isaac FaceRig
    pass

    # Let's add empty 'child of' constraints to limbs, torso and root. Ready to use in case char holds obj/stands on obj
    def add_child_of(bone_name):
        this_bone = bpy.context.scene.objects[char_name+"Rig"].pose.bones[bone_name]
        co = this_bone.constraints.new('CHILD_OF')

    if add_child_of_constraints: 
        add_child_of("hand-ik-L")
        add_child_of("hand-ik-R")
        add_child_of("foot_ik.R")
        add_child_of("foot_ik.L")
        add_child_of("torso-outer")
        add_child_of("root")
        
        
    # Here we can set up the two damped track constraints to make the head follow the controller bone.
    # This makes the head bone follow the controller
    head_controller = bpy.context.scene.objects[char_name+"Rig"].pose.bones["head"]
    co = head_controller.constraints.new('DAMPED_TRACK')
    head_track_const = bpy.data.objects[char_name+"Rig"].pose.bones["head"].constraints["Damped Track"]
    head_track_const.target = our_char 
    head_track_const.subtarget = "head-controller"
    head_track_const.track_axis = "TRACK_Z"
    # driver
    head_track_driver = head_track_const.driver_add("influence").driver
    head_track_driver.type = 'SCRIPTED'
    head_track_driver.expression = 'bone'
    head_var = head_track_driver.variables.new()
    head_var.name = "bone"
    head_var.type = 'SINGLE_PROP'
    head_var.targets[0].id = bpy.context.scene.objects[ourRig]
    head_var.targets[0].data_path = 'pose.bones["plate-settings"]["Use Head Controller"]'
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

    if not use_head_tracker:
        if "plate-settings" in this_obj.pose.bones:
            this_obj.pose.bones["plate-settings"]["Use Head Controller"] = 0.00
 
    # This makes the controller follow the obj in the neck to keep it 'on' the head.
    head_pole_cont = bpy.context.scene.objects[char_name+"Rig"].pose.bones["head-controller"]
    co2 = head_pole_cont.constraints.new('DAMPED_TRACK')
    head_pole_const = bpy.data.objects[char_name+"Rig"].pose.bones["head-controller"].constraints["Damped Track"]
    head_pole_const.target = bpy.data.objects.get("Head_Pole") 
    head_pole_const.track_axis = "TRACK_NEGATIVE_Z"
    # driver
    head_pole_driver = head_pole_const.driver_add("influence").driver
    head_pole_driver.type = 'SCRIPTED'
    head_pole_driver.expression = 'bone'
    head_pole_var = head_pole_driver.variables.new()
    head_pole_var.name = "bone"
    head_pole_var.type = 'SINGLE_PROP'
    head_pole_var.targets[0].id = bpy.context.scene.objects[ourRig]
    head_pole_var.targets[0].data_path = 'pose.bones["plate-settings"]["Use Head Controller"]'
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

    # Set star custom shape on head-controller / head direction (Genshin primo-joint star style)
    star_obj = bpy.data.objects.get("primo-joint") or bpy.data.objects.get("head-control-shape")
    for h_name in ["head-controller", "Head Direction", "head direction", "Head_Direction"]:
        pb_h = bpy.context.scene.objects[char_name+"Rig"].pose.bones.get(h_name)
        if pb_h and star_obj:
            pb_h.custom_shape = star_obj
            pb_h.use_custom_shape_bone_size = False
            pb_h.custom_shape_scale_xyz = (0.022, 0.022, 0.022)

    # We can now make our final bone groups look good! (Both 3.6 and 4.0 functionality.)
    def assign_bone_to_group(bone_name, group_name):
        # Perform old functionality to make BGs to then color.
        if not is_version_4:
            # Switch to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Get the armature object
            armature_obj = our_char
            if not armature_obj or armature_obj.type != 'ARMATURE':
                return

            # Switch to pose mode
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='POSE')

            # Get the pose bone
            pose_bone = armature_obj.pose.bones.get(bone_name)
            if not pose_bone:
                return

            # Get the bone group
            bone_group = armature_obj.pose.bone_groups.get(group_name)
            if not bone_group:
                # Create a new bone group if it doesn't exist
                bone_group = armature_obj.pose.bone_groups.new(name=group_name)

            # Assign the bone to the bone group
            pose_bone.bone_group = bone_group
        
        # New 4.0 functionality: change the bone itself to the color of the group it was originally assigned to.
        else:
            # 4.0: Armature bones or Pose bones?
            if not bpy.context.object or not hasattr(bpy.context.object, "pose") or bone_name not in bpy.context.object.pose.bones:
                return
            bone = bpy.context.object.pose.bones[bone_name]
            
            if group_name == "Root":
                bone.color.palette = 'CUSTOM'
                bone.color.custom.normal = (0,1,0.169)
                bone.color.custom.select = (0.596,0.898,1.00)
                bone.color.custom.active = (0.769,1.00,1.00)
            elif group_name == "Torso":
                bone.color.palette = 'CUSTOM'
                bone.color.custom.normal = (1,0.867,0)
                bone.color.custom.select = (0.596,0.898,1.00)
                bone.color.custom.active = (0.769,1.00,1.00)
            elif group_name == "Limbs L":
                bone.color.palette = 'CUSTOM'
                bone.color.custom.normal = (1,0,1)
                bone.color.custom.select = (0.596,0.898,1.00)
                bone.color.custom.active = (0.769,1.00,1.00)
            elif group_name == "Limbs R":
                bone.color.palette = 'CUSTOM'
                bone.color.custom.normal = (0,0.839,1)
                bone.color.custom.select = (0.596,0.898,1.00)
                bone.color.custom.active = (0.769,1.00,1.00)
            elif group_name == "Face":
                bone.color.palette = 'CUSTOM'
                bone.color.custom.normal = (1,0,0)
                bone.color.custom.select = (0.596,0.898,1.00)
                bone.color.custom.active = (0.769,1.00,1.00)         

    # Root BG
    assign_bone_to_group("root", "Root")
    assign_bone_to_group("root-outer", "Root")
    assign_bone_to_group("root-inner", "Root")
    
    # Torso BG
    assign_bone_to_group("torso", "Torso")
    assign_bone_to_group("torso-inner", "Torso")
    assign_bone_to_group("torso-outer", "Torso")
    assign_bone_to_group("torso_pivot.002", "Torso")
    assign_bone_to_group("hips", "Torso")
    assign_bone_to_group("chest", "Torso")
    assign_bone_to_group("neck", "Torso")
    assign_bone_to_group("head-controller", "Torso")
    assign_bone_to_group("head", "Torso")

    # Left Arm BG
    assign_bone_to_group("hand_ik.L", "Limbs L")
    assign_bone_to_group("upper_arm_ik_target.L", "Limbs L")
    assign_bone_to_group("shoulder.L", "Limbs L")
    assign_bone_to_group("hand-ik-pivot-L", "Limbs L")
    assign_bone_to_group("hand-ik-L", "Limbs L")
    assign_bone_to_group("upper_arm_parent.L", "Limbs L")
    assign_bone_to_group("forearm_tweak-pin.L", "Limbs L")
    assign_bone_to_group("prop.L", "Limbs L")
    if not use_arm_ik_poles:
        assign_bone_to_group("upper_arm_ik.L", "Limbs L")

    # Right Arm BG
    assign_bone_to_group("hand_ik.R", "Limbs R")
    assign_bone_to_group("upper_arm_ik_target.R", "Limbs R")
    assign_bone_to_group("shoulder.R", "Limbs R")
    assign_bone_to_group("hand-ik-pivot-R", "Limbs R")
    assign_bone_to_group("hand-ik-R", "Limbs R")
    assign_bone_to_group("upper_arm_parent.R", "Limbs R")
    assign_bone_to_group("forearm_tweak-pin.R", "Limbs R")
    assign_bone_to_group("prop.R", "Limbs R")
    if not use_arm_ik_poles:
        assign_bone_to_group("upper_arm_ik.R", "Limbs R")

    # Left Foot BG
    assign_bone_to_group("foot_ik.L", "Limbs L")
    assign_bone_to_group("toe_ik.L", "Limbs L")
    assign_bone_to_group("foot_spin_ik.L", "Limbs L")
    assign_bone_to_group("foot_heel_ik.L", "Limbs L")
    assign_bone_to_group("thigh_ik_target.L", "Limbs L")
    assign_bone_to_group("ik-pivot-L", "Limbs L")
    assign_bone_to_group("ik-sub-pivot-L", "Limbs L")
    assign_bone_to_group("thigh_parent.L", "Limbs L")
    assign_bone_to_group("shin_tweak-pin.L", "Limbs L")
    if not use_leg_ik_poles:
        assign_bone_to_group("thigh_ik.L", "Limbs L")

    # Right Foot BG
    assign_bone_to_group("foot_ik.R", "Limbs R")
    assign_bone_to_group("toe_ik.R", "Limbs R")
    assign_bone_to_group("foot_spin_ik.R", "Limbs R")
    assign_bone_to_group("foot_heel_ik.R", "Limbs R")
    assign_bone_to_group("thigh_ik_target.R", "Limbs R")
    assign_bone_to_group("ik-pivot-R", "Limbs R")
    assign_bone_to_group("ik-sub-pivot-R", "Limbs R")
    assign_bone_to_group("thigh_parent.R", "Limbs R")
    assign_bone_to_group("shin_tweak-pin.R", "Limbs R")
    if not use_leg_ik_poles:
        assign_bone_to_group("thigh_ik.R", "Limbs R")

    # Root settings plate
    assign_bone_to_group("plate-settings", "Root")

    # Default bone group colors are ugly. We can change them.
    def change_bone_group_colors(bone_group_name, color1, color2, color3):
        active_bg = bpy.context.active_object.pose.bone_groups[bone_group_name]
        active_bg.color_set = "CUSTOM"
        active_bg.colors.normal = Color((color1))
        active_bg.colors.select = Color((color2))
        active_bg.colors.active = Color((color3))
    
    if not is_version_4:    
        change_bone_group_colors('Root',(0,1,0.169),(0.596,0.898,1.00),(0.769,1.00,1.00))
        change_bone_group_colors('Torso',(1,0.867,0),(0.596,0.898,1.00),(0.769,1.00,1.00))
        change_bone_group_colors('Limbs L',(1,0,1),(0.596,0.898,1.00),(0.769,1.00,1.00))
        change_bone_group_colors('Limbs R',(0,0.839,1),(0.596,0.898,1.00),(0.769,1.00,1.00))
        change_bone_group_colors('Face',(1,0,0),(0.596,0.898,1.00),(0.769,1.00,1.00))



    def generate_switch_parent_constraints(toggle_parent, location_of_switcher):
        pb_tp = this_obj.pose.bones.get(toggle_parent)
        if not pb_tp:
            return
        const = pb_tp.constraints.get("SWITCH PARENT")
        if not const:
            const = pb_tp.constraints.new('ARMATURE')
            const.name = "SWITCH PARENT"
        while len(const.targets) < 5:
            const.targets.new()
        const.targets[0].target = bpy.data.objects[char_name+"Rig"]
        const.targets[0].subtarget = "root"

        const.targets[1].target = bpy.data.objects[char_name+"Rig"]
        const.targets[1].subtarget = "root.001"

        const.targets[2].target = bpy.data.objects[char_name+"Rig"]
        const.targets[2].subtarget = "root.002"

        const.targets[3].target = bpy.data.objects[char_name+"Rig"]
        const.targets[3].subtarget = "torso.002"

        const.targets[4].target = bpy.data.objects[char_name+"Rig"]
        const.targets[4].subtarget = "chest"
        
        location_str = "pose.bones[\"" + location_of_switcher + "\"][\"parent_switch\"]"
        
        for x in range(5):
            driver = const.targets[x].driver_add("weight").driver
            var = driver.variables.new()
            var.name = "toggle"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = bpy.context.scene.objects[ourRig]
            var.targets[0].data_path = location_str

            driver.type = 'SCRIPTED'
            driver.expression = "toggle == " + str(x+1) 
        
        # Toggle the constraint off, we HAVE to reenable it later to work!!
        const.enabled = False
    
    
    # REENABLE CONSTRAINTS BELOW

    switch_parent_dropdown_items = [
        ("P0", "None", ""),
        ("P1", "root", ""),
        ("P2", "root.001", ""),
        ("P3", "root.002", ""),
        ("P4", "torso", ""),
        ("P5", "chest", ""),
    ]

    # 1. Adjustments to positioning (using pre-renamed bone names)
    if "foot_ik.L" in this_obj.pose.bones and "mch-ik-pivot-L" in bpy.data.objects[char_name+"Rig"].pose.bones:
        this_obj.pose.bones["foot_ik.L"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-ik-pivot-L"]
    if "foot_ik.R" in this_obj.pose.bones and "mch-ik-pivot-R" in bpy.data.objects[char_name+"Rig"].pose.bones:
        this_obj.pose.bones["foot_ik.R"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-ik-pivot-R"]
    if "hand-ik-L" in this_obj.pose.bones and "mch-hand-ik-pivot-L" in bpy.data.objects[char_name+"Rig"].pose.bones:
        this_obj.pose.bones["hand-ik-L"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-hand-ik-pivot-L"]
    if "hand-ik-R" in this_obj.pose.bones and "mch-hand-ik-pivot-R" in bpy.data.objects[char_name+"Rig"].pose.bones:
        this_obj.pose.bones["hand-ik-R"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-hand-ik-pivot-R"]
    
    # Align custom shape of hand IK controller bones (wrist) straight to center
    for b_name in ["hand-ik-L", "hand-ik-R", "hand_ik.L", "hand_ik.R", "hand_ik_wrist.L", "hand_ik_wrist.R"]:
        pb = this_obj.pose.bones.get(b_name)
        if pb and hasattr(pb, "custom_shape_rotation_euler"):
            pb.custom_shape_rotation_euler[0] = 0.0
            pb.custom_shape_rotation_euler[1] = 0.0
            pb.custom_shape_rotation_euler[2] = 0.0
    
    if "ik-sub-pivot-L" in this_obj.pose.bones:
        this_obj.pose.bones["ik-sub-pivot-L"].custom_shape_translation = (foot_L_x_diff*-1.0, 0.0, foot_L_z_diff*-1.0)
    if "ik-sub-pivot-R" in this_obj.pose.bones:
        this_obj.pose.bones["ik-sub-pivot-R"].custom_shape_translation = (foot_R_x_diff*-1.0, 0.0, foot_R_z_diff*-1.0)
   
    # Delete palm constraints on ORG-palm bones and any constraint referencing deleted palm.L/palm.R
    for pb in this_obj.pose.bones:
        if "palm" in pb.name.lower():
            for c in list(pb.constraints):
                if c.type in ['COPY_TRANSFORMS', 'COPY_ROTATION'] or getattr(c, "subtarget", None) in ["palm.L", "palm.R"]:
                    pb.constraints.remove(c)
        
    # 2. Rename bones to final standard names FIRST so all downstream constraints target valid bones
    for oldname, newname in rename_bones_list:
        bone = this_obj.pose.bones.get(oldname)
        if bone is None:
            print(f"[RIG WARNING] Rename skipped: bone '{oldname}' not found")
            continue
        bone.name = newname
        print(f"[RIG OK] Renamed bone '{oldname}' -> '{newname}'")

    # 3. Ensure prop.L, prop.R, and weapon bones are parented to root.002
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        eb_r002 = this_obj.data.edit_bones.get("root.002")
        if eb_r002:
            for pb_name in ["prop.L", "prop.R"]:
                eb_p = this_obj.data.edit_bones.get(pb_name)
                if eb_p:
                    eb_p.parent = eb_r002
            for wb_name in detected_weapon_bone_names:
                w_eb = this_obj.data.edit_bones.get(wb_name)
                if w_eb and (w_eb.parent is None or w_eb.parent.name in ["root", "root.001"]):
                    is_l = ".l" in wb_name.lower() or "garape" in wb_name.lower() or "grape" in wb_name.lower()
                    eb_p = this_obj.data.edit_bones.get("prop.L" if is_l else "prop.R")
                    w_eb.parent = eb_p if eb_p else eb_r002
        bpy.ops.object.mode_set(mode='POSE')
    except Exception as e_parent_props:
        print(f"[HSR Rig Warning] Failed to ensure prop parenting to root.002: {e_parent_props}")
        try:
            bpy.ops.object.mode_set(mode='POSE')
        except Exception:
            pass 

    # 4. Torso custom properties
    def make_torso_custom():
        cust_bone = this_obj.pose.bones.get("torso")
        if not cust_bone:
            return
        cust_bone["torso_parent"] = 1
        try:
            id_prop = cust_bone.id_properties_ui("torso_parent")
            id_prop.update(items=[("P0", "None", ""), ("P1", "Root", "")], default=1)
        except Exception:
            pass
        try:
            cust_bone.property_overridable_library_set('["torso_parent"]', True)
        except Exception:
            pass
    
    make_torso_custom()
    bpy.data.armatures[original_name].property_overridable_library_set('["rig_id"]', True)

    # 5. Tweak bone custom properties and copy location
    def prepare_tweak_bone(tweak_bone, pin_bone):
        cust_bone = this_obj.pose.bones.get(tweak_bone)
        if not cust_bone or pin_bone not in this_obj.pose.bones:
            return
        cust_bone["tweak_pin"] = 0.00
        try:
            id_prop = cust_bone.id_properties_ui("tweak_pin")
            id_prop.update(min=0.0, max=1.0)    
            cust_bone.property_overridable_library_set('["tweak_pin"]', True)    
        except Exception:
            pass

        con = cust_bone.constraints.new('COPY_LOCATION')
        con.target = our_char
        con.subtarget = pin_bone
        
        path_str = f'pose.bones["{tweak_bone}"]["tweak_pin"]'
        driver = con.driver_add("influence").driver
        driver.type = 'SUM'
        var = driver.variables.new()
        var.name = "bone"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = bpy.context.scene.objects[ourRig]
        var.targets[0].data_path = path_str
    
    prepare_tweak_bone("forearm_tweak.L", "forearm_tweak-pin.L")
    prepare_tweak_bone("forearm_tweak.R", "forearm_tweak-pin.R")
    prepare_tweak_bone("shin_tweak.L", "shin_tweak-pin.L")
    prepare_tweak_bone("shin_tweak.R", "shin_tweak-pin.R")

    # 6. Build SWITCH PARENT constraints (Now that bones are properly named!)
    def generate_switch_parent_constraints(toggle_parent, location_of_switcher):
        pb_tp = this_obj.pose.bones.get(toggle_parent)
        if not pb_tp:
            return
        const = pb_tp.constraints.get("SWITCH PARENT")
        if not const:
            const = pb_tp.constraints.new('ARMATURE')
            const.name = "SWITCH PARENT"
        while len(const.targets) < 5:
            const.targets.new()
        const.targets[0].target = bpy.data.objects[char_name+"Rig"]
        const.targets[0].subtarget = "root"

        const.targets[1].target = bpy.data.objects[char_name+"Rig"]
        const.targets[1].subtarget = "root.001"

        const.targets[2].target = bpy.data.objects[char_name+"Rig"]
        const.targets[2].subtarget = "root.002"

        const.targets[3].target = bpy.data.objects[char_name+"Rig"]
        const.targets[3].subtarget = "torso.002"

        const.targets[4].target = bpy.data.objects[char_name+"Rig"]
        const.targets[4].subtarget = "chest"
        
        location_str = f'pose.bones["{location_of_switcher}"]["parent_switch"]'
        
        for x in range(5):
            driver = const.targets[x].driver_add("weight").driver
            var = driver.variables.new()
            var.name = "toggle"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = bpy.context.scene.objects[ourRig]
            var.targets[0].data_path = location_str

            driver.type = 'SCRIPTED'
            driver.expression = f"toggle == {x+1}"
        
        const.enabled = False

    switch_parent_dropdown_items = [
        ("P0", "None", ""),
        ("P1", "root", ""),
        ("P2", "root.001", ""),
        ("P3", "root.002", ""),
        ("P4", "torso", ""),
        ("P5", "chest", ""),
    ]

    if "head-controller" in this_obj.pose.bones:
        this_obj.pose.bones["head-controller"]["parent_switch"] = 3
        try:
            this_obj.pose.bones["head-controller"].id_properties_ui("parent_switch").update(
                items=switch_parent_dropdown_items, default=3, description="Head Controller Parent"
            )
        except Exception:
            pass

    if "MCH-head-controller-parent" in this_obj.pose.bones:
        generate_switch_parent_constraints("MCH-head-controller-parent", "head-controller")
    
    for p_bone in ["forearm_tweak-pin.L", "forearm_tweak-pin.R", "shin_tweak-pin.L", "shin_tweak-pin.R"]:
        if p_bone in this_obj.pose.bones:
            this_obj.pose.bones[p_bone]["parent_switch"] = 3
            try:
                this_obj.pose.bones[p_bone].id_properties_ui("parent_switch").update(
                    items=switch_parent_dropdown_items, default=3, description=f"{p_bone} Parent"
                )
            except Exception:
                pass

    generate_switch_parent_constraints("MCH-forearm_tweak-pin.parent.L", "forearm_tweak-pin.L")
    generate_switch_parent_constraints("MCH-forearm_tweak-pin.parent.R", "forearm_tweak-pin.R")
    generate_switch_parent_constraints("MCH-shin_tweak-pin.parent.L", "shin_tweak-pin.L")
    generate_switch_parent_constraints("MCH-shin_tweak-pin.parent.R", "shin_tweak-pin.R") 
    def nuke_old_torso_const():       
        const = this_obj.pose.bones["MCH-torso.parent"].constraints
        to_del = [c for c in const]
        for c in to_del:
            const.remove(c)
            
        new = const.new('ARMATURE')
        new.name = 'SWITCH_PARENT'
        # add target
        new.targets.new()
        new.targets[0].target = bpy.data.objects[char_name+"Rig"]
        new.targets[0].subtarget = "root.002"
        
        location_str = "pose.bones[\"torso\"][\"torso_parent\"]"

        driver = new.targets[0].driver_add("weight").driver
        driver.type = 'SCRIPTED'
        
        # Create the 'var' variable (was missing, causing NameError)
        var = driver.variables.new()
        var.name = "var"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = bpy.data.objects[char_name+"Rig"]
        var.targets[0].data_path = location_str

        driver.expression = "var == 1"

        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        
        # Toggle the constraint off, we HAVE to reenable it later to work!!
        new.enabled = False
   
    nuke_old_torso_const()
    
    # Use this to swap a variable in a constraint
    def swap_const_follow_in_const(bone, constraint_type, new_var, target_bone="torso.002"):
        if bone not in this_obj.pose.bones:
            return
        const = this_obj.pose.bones[bone].constraints     
        for c in const:
            if c.type == constraint_type:
                const.remove(c)   
        
        new = const.new(constraint_type)
        new.target = bpy.data.objects[char_name+"Rig"]
        new.subtarget = target_bone       
        new.owner_space = 'LOCAL'
        new.target_space = 'LOCAL'
        
        driver = new.driver_add("influence").driver
        driver.type = 'SUM'
        
        # Create the variable (was missing - iterating empty driver.variables)
        var = driver.variables.new()
        var.name = "var"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = bpy.data.objects[char_name+"Rig"]
        var.targets[0].data_path = new_var

        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
    # Connect Head Follow and Neck Follow from plate-settings directly to Rigify's head and neck constraints
    if this_obj.animation_data:
        for fcurve in this_obj.animation_data.drivers:
            drv = fcurve.driver
            for var in drv.variables:
                for target in var.targets:
                    if target.id == this_obj and target.data_path:
                        if '["head_follow"]' in target.data_path:
                            target.data_path = 'pose.bones["plate-settings"]["Head Follow"]'
                        elif '["neck_follow"]' in target.data_path:
                            target.data_path = 'pose.bones["plate-settings"]["Neck Follow"]'

    # Retarget head and neck follow Copy Rotation constraints to root instead of torso/COG,
    # ensuring that when Head/Neck Follow = 0, the head stays upright in world/root space
    # instead of rotating with COG while ignoring chest.
    root_bname = "root" if "root" in this_obj.pose.bones else ("root.002" if "root.002" in this_obj.pose.bones else "root.001")
    for b_name in ["MCH-ROT-head", "MCH-ROT-neck"]:
        pb_rot = this_obj.pose.bones.get(b_name)
        if pb_rot:
            for c in pb_rot.constraints:
                if c.type == 'COPY_ROTATION' and root_bname:
                    c.subtarget = root_bname

    for t_name in ["torso", "torso.002"]:
        pb_t = this_obj.pose.bones.get(t_name)
        if pb_t:
            try:
                d_hf = pb_t.driver_add('["head_follow"]').driver
                d_hf.type = 'SCRIPTED'
                d_hf.expression = "var"
                var_hf = d_hf.variables.new()
                var_hf.name = "var"
                var_hf.type = 'SINGLE_PROP'
                var_hf.targets[0].id = this_obj
                var_hf.targets[0].data_path = 'pose.bones["plate-settings"]["Head Follow"]'
            except Exception:
                pass
            try:
                d_nf = pb_t.driver_add('["neck_follow"]').driver
                d_nf.type = 'SCRIPTED'
                d_nf.expression = "var"
                var_nf = d_nf.variables.new()
                var_nf.name = "var"
                var_nf.type = 'SINGLE_PROP'
                var_nf.targets[0].id = this_obj
                var_nf.targets[0].data_path = 'pose.bones["plate-settings"]["Neck Follow"]'
            except Exception:
                pass
        
    # Delete all existing bone collections, and make new ones.   
    if is_version_4:
        setup_standard_bone_collections(this_obj, is_version_4)
        armature = this_obj.data
        collections = armature.collections
        
        # Ensure standard collections Face and Weapon exist
        if "Face" not in collections:
            collections.new("Face")
        if "Weapon" not in collections:
            collections.new("Weapon")
        if "Other" not in collections:
            collections.new("Other")

        # Clean up any residual collections: dissolve facerig controls into Face, hook bones into Other
        for extra_cname in ["facerig", "Facerig Hooks", "Face Hooks", "facerig_hooks"]:
            ec = collections.get(extra_cname)
            if ec:
                for b in list(ec.bones):
                    if "hook" in b.name.lower():
                        collections["Other"].assign(b)
                    else:
                        collections["Face"].assign(b)
                collections.remove(ec)

        # Dissolve Props into Weapon
        props_c = collections.get("Props")
        if props_c:
            for b in list(props_c.bones):
                collections["Weapon"].assign(b)
            collections.remove(props_c)

        # Dissolve WeaponBox into Clothes or Other (these are spine/back accessories, NOT hand weapons)
        for wbox_cname in ["WeaponBox", "weaponbox", "Weaponbox"]:
            wbc = collections.get(wbox_cname)
            if wbc:
                target_box_coll = collections.get("Clothes") or collections["Other"]
                for b in list(wbc.bones):
                    target_box_coll.assign(b)
                collections.remove(wbc)
        
        for bone in armature.bones:
            if "hook" in bone.name.lower():
                collections["Other"].assign(bone)
                if "Face" in collections:
                    collections["Face"].unassign(bone)
            elif 'slider-' in bone.name:
                collections["Face"].assign(bone)
                if 'frame-' not in bone.name:
                    assign_bone_to_group(bone.name, "Face")
            else:    
                collections["Other"].assign(bone)
          
    #Thanks Enthralpy for the code to ensure that the arm/leg "gears" are moveable.
    for bone in ['thigh_parent.L', 'thigh_parent.R', 'upper_arm_parent.L', 'upper_arm_parent.R']:
        this_obj.pose.bones[bone].custom_shape_transform = None
        this_obj.pose.bones[bone].lock_location[0] = False
        this_obj.pose.bones[bone].lock_location[1] = False
        this_obj.pose.bones[bone].lock_location[2] = False
        this_obj.pose.bones[bone].lock_rotation_w = False
        this_obj.pose.bones[bone].lock_rotation[0] = False
        this_obj.pose.bones[bone].lock_rotation[1] = False
        this_obj.pose.bones[bone].lock_rotation[2] = False
        this_obj.pose.bones[bone].lock_scale[0] = False
        this_obj.pose.bones[bone].lock_scale[1] = False
        this_obj.pose.bones[bone].lock_scale[2] = False
               
        # Customize bones
        setting_circle = bpy.data.objects.get("setting-circle")
        if setting_circle:
            this_obj.pose.bones[bone].custom_shape = setting_circle
            this_obj.pose.bones[bone].custom_shape_scale_xyz=(0.38,0.38,0.38)
            this_obj.pose.bones[bone].use_custom_shape_bone_size = False
        
        if "upper_arm" in bone:
            if ".L" in bone:
                this_obj.pose.bones[bone].custom_shape_translation=(-0.02,0.0,0.0)
                this_obj.pose.bones[bone].custom_shape_rotation_euler=(0,-1.5708,0)
                this_obj.pose.bones[bone].custom_shape_transform = this_obj.pose.bones["MCH-upper_arm_parent_widget.L"]
            else:
                this_obj.pose.bones[bone].custom_shape_translation=(0.02,0.0,0.0)
                this_obj.pose.bones[bone].custom_shape_rotation_euler=(0,-1.5708,0)
                this_obj.pose.bones[bone].custom_shape_transform = this_obj.pose.bones["MCH-upper_arm_parent_widget.R"]
        else:
            if ".L" in bone:
                this_obj.pose.bones[bone].custom_shape_translation=(0.02,0,0)
                this_obj.pose.bones[bone].custom_shape_rotation_euler=(-0.0820305, -1.5708, 0)
                this_obj.pose.bones[bone].custom_shape_transform = this_obj.pose.bones["MCH-thigh_parent_widget.L"]
            else:
                this_obj.pose.bones[bone].custom_shape_translation=(-0.02,0,0)
                this_obj.pose.bones[bone].custom_shape_rotation_euler=(-0.0820305, 1.5708, 0)
                this_obj.pose.bones[bone].custom_shape_transform = this_obj.pose.bones["MCH-thigh_parent_widget.R"]
        
    # ENABLE CONSTRAINTS AGAIN HERE
    if "MCH-head-controller-parent" in this_obj.pose.bones:
        this_obj.pose.bones["MCH-head-controller-parent"].constraints[0].enabled = True
    this_obj.pose.bones["MCH-forearm_tweak-pin.parent.L"].constraints[0].enabled = True
    this_obj.pose.bones["MCH-forearm_tweak-pin.parent.R"].constraints[0].enabled = True
    this_obj.pose.bones["MCH-shin_tweak-pin.parent.L"].constraints[0].enabled = True
    this_obj.pose.bones["MCH-shin_tweak-pin.parent.R"].constraints[0].enabled = True
    this_obj.pose.bones["MCH-torso.parent"].constraints[0].enabled = True
    
    # Deselect everything, we're done.
    try:
        for bone in bpy.context.active_object.pose.bones:
            bone.bone.select = False
    except AttributeError:
        # Blender 5.1+: Bone.select was removed from the data API
        try:
            bpy.ops.pose.select_all(action='DESELECT')
        except:
            pass
        
    # EDITING ui.py TEXT FILE --------------------------------------------
    rig_file = bpy.data.texts.get(original_name + '_ui.py') or bpy.data.texts.get('rig_ui.py')
    rig_char_id = char_name
    if rig_file:
        try:
            rig_char_id = rig_file.as_string().split('rig_id = "')[1].split('"')[0]
        except Exception:
            pass

    def generate_string_for_limb_pin(pin_bone, gear_bone, tweak_bone, text):
        return "\n        if is_selected({'"+pin_bone+"'}):\n            layout.prop(pose_bones['"+tweak_bone+"'], '[\"tweak_pin\"]', text='"+text+"', slider=True)\n        if is_selected({'"+gear_bone+"'}):\n            layout.prop(pose_bones['"+tweak_bone+"'], '[\"tweak_pin\"]', text='"+text+"', slider=True)"
    
    def generate_string_for_parent_switch(bone):
        return "\n        if is_selected({'"+bone+"'}):\n            group1 = layout.row(align=True)\n            group2 = group1.split(factor=0.55, align=True)\n            props = group2.operator('pose.rigify_switch_parent_"+rig_char_id+"\', text=\'Parent Switch\', icon=\'DOWNARROW_HLT\')\n            props.bone = \'"+bone+"\'\n            props.prop_bone = \'"+bone+"\'\n            props.prop_id=\'parent_switch\'\n            props.parent_names = '[\"None\", \"root\", \"root.001\", \"root.002\", \"torso\", \"chest\"]'\n            props.locks = (False, False, False)\n            group2.prop(pose_bones['"+bone+"'], '[\"parent_switch\"]', text='')\n            props = group1.operator('pose.rigify_switch_parent_bake_"+rig_char_id+"', text='', icon='ACTION_TWEAK')\n            props.bone = '"+bone+"'\n            props.prop_bone='"+bone+"'\n            props.prop_id='parent_switch'\n            props.parent_names='[\"None\", \"root\", \"root.001\", \"root.002\", \"torso\", \"chest\"]'\n            props.locks = (False, False, False)"

    def generate_string_for_ik_switch(bone, prop1, prop2):
        return "\n        if is_selected({'"+bone+"'}):\n            group1 = layout.row(align=True)\n            group2 = group1.split(factor=0.55, align=True)\n            props = group2.operator('pose.rigify_switch_parent_"+rig_char_id+"\', text=\'Parent Switch\', icon=\'DOWNARROW_HLT\')\n            props.bone = \'"+prop1+"\'\n            props.prop_bone = \'"+prop2+"\'\n            props.prop_id=\'IK_parent\'\n            props.parent_names = '[\"None\", \"root\", \"root.001\", \"root.002\", \"torso\", \"chest\"]'\n            props.locks = (False, False, False)\n            group2.prop(pose_bones['"+prop2+"'], '[\"IK_parent\"]', text='')\n            props = group1.operator('pose.rigify_switch_parent_bake_"+rig_char_id+"', text='', icon='ACTION_TWEAK')\n            props.bone = '"+prop1+"'\n            props.prop_bone='"+prop2+"'\n            props.prop_id='IK_parent'\n            props.parent_names='[\"None\", \"root\", \"root.001\", \"root.002\", \"torso\", \"chest\"]'\n            props.locks = (False, False, False)"
        
    def generate_string_for_settings_slider():
        return '\n        if is_selected({"plate-settings"}):\n            layout.prop(pose_bones["plate-settings"], \'["Use Head Controller"]\', text="Use Head Tracker Controller", slider=True)\n            layout.prop(pose_bones["plate-settings"], \'["Head Follow"]\', text="Head Follow", slider=True)\n            layout.prop(pose_bones["plate-settings"], \'["Neck Follow"]\', text="Neck Follow", slider=True)\n            layout.prop(pose_bones["plate-settings"], \'["Adjust Pupil Distance"]\', text="Adjust Pupil Distance", slider=True)'

    def generate_string_for_head_controller_slider():
        return '\n        if is_selected({"head-controller"}):\n            layout.prop(pose_bones["plate-settings"], \'["Use Head Controller"]\', text="Use Head Tracker Controller", slider=True)\n        if is_selected({"head"}):\n            layout.prop(pose_bones["plate-settings"], \'["Use Head Controller"]\', text="Use Head Tracker Controller", slider=True)'

    def generate_string_for_tail_ik(ik_name, chain_bones):
        sel = "{" + ", ".join("'" + b + "'" for b in [ik_name] + chain_bones) + "}"
        return ("\n        if is_selected(" + sel + "):"
                "\n            if \"" + ik_name + "\" in pose_bones and \"IK\" in pose_bones[\"" + ik_name + "\"]:"
                "\n                layout.prop(pose_bones[\"" + ik_name + "\"], '[\"IK\"]', text='FK -> IK', slider=True)"
                "\n            if \"" + ik_name + "\" in pose_bones and \"Flexibility\" in pose_bones[\"" + ik_name + "\"]:"
                "\n                layout.prop(pose_bones[\"" + ik_name + "\"], '[\"Flexibility\"]', text='Flexibility', slider=True)")

    # Tail IK sliders (same system as limb gears: show when tail bones selected).
    # Chain members resolved by walking parents from the constrained tip.
    tail_splices = []
    try:
        for _ik_name, _last_name, _chain_len in tail_ik_info:
            _members = []
            try:
                _b = this_obj.pose.bones.get(_last_name)
                for _i in range(int(_chain_len)):
                    if _b is None:
                        break
                    if not _b.name.startswith(("DEF-", "MCH-", "ORG-")):
                        _members.append(_b.name)
                    _b = _b.parent
            except Exception:
                pass
            tail_splices.append(
                {"divider": "num_rig_separators[0] += 1",
                 "text": generate_string_for_tail_ik(_ik_name, _members)})
    except Exception as e_tail_ui:
        print(f"[TAIL UI] splice notice: {e_tail_ui}")

    splices = [
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_parent_switch("forearm_tweak-pin.L")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_limb_pin("forearm_tweak-pin.L", "upper_arm_parent.L", "forearm_tweak.L", "Elbow Pin")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_parent_switch("forearm_tweak-pin.R")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_limb_pin("forearm_tweak-pin.R", "upper_arm_parent.R", "forearm_tweak.R", "Elbow Pin")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_ik_switch("hand_ik_pivot.L", "hand_ik.L", "upper_arm_parent.L")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_ik_switch("hand_ik_pivot.R", "hand_ik.R", "upper_arm_parent.R")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_ik_switch("foot_ik_pivot.L", "foot_ik.L", "thigh_parent.L")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_ik_switch("foot_ik_pivot.R", "foot_ik.R", "thigh_parent.R")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_parent_switch("shin_tweak-pin.L")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_limb_pin("shin_tweak-pin.L", "thigh_parent.L", "shin_tweak.L", "Knee Pin")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_parent_switch("shin_tweak-pin.R")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_limb_pin("shin_tweak-pin.R", "thigh_parent.R", "shin_tweak.R", "Knee Pin")},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_settings_slider()},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_head_controller_slider()},
        {"divider": "num_rig_separators[0] += 1", "text": generate_string_for_parent_switch("head-controller")},
    ]
    splices.extend(tail_splices)

    modify_and_run_rig_ui_script(this_obj, original_name, char_name=char_name, extra_splices=splices)
    
    # Ensure all breast sub-bones (breast.L.001 - breast.L.005, breast.R.001 - breast.R.005, etc.) are parented to DEF-breast.L / DEF-breast.R
    try:
        if bpy.context.object and bpy.context.object.type == 'ARMATURE':
            bpy.ops.object.mode_set(mode='EDIT')
            eb = bpy.context.object.data.edit_bones

            def_l = eb.get("DEF-breast.L") or eb.get("breast.L")
            def_r = eb.get("DEF-breast.R") or eb.get("breast.R")

            for b in eb:
                b_low = b.name.lower()
                if b.name in ["breast.L", "breast.R", "DEF-breast.L", "DEF-breast.R", "ORG-breast.L", "ORG-breast.R", "MCH-breast.L", "MCH-breast.R"]:
                    continue
                if ("breast.l" in b_low or "breast_l" in b_low or "skn_l_chest" in b_low or "chest_l" in b_low or "+breast l" in b_low) and def_l:
                    b.parent = def_l
                    b.use_connect = False
                elif ("breast.r" in b_low or "breast_r" in b_low or "skn_r_chest" in b_low or "chest_r" in b_low or "+breast r" in b_low) and def_r:
                    b.parent = def_r
                    b.use_connect = False

            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception as ex:
        print(f"[DEBUG] breast sub-bones parenting warning: {ex}")
    
    # DONE MODIFYING ui.py FILE --------------------------------------------
    
    
    # Tie the visibility of the RGB circle meshes to the visibility of the lighting layer/collection
    def drive_visibility_with_prop(obj_name, path):
        driver_obj = bpy.data.objects.get(obj_name)
        if not driver_obj:
            return
        try:
            driver = driver_obj.driver_add("hide_viewport").driver
            
            driver.type = 'SCRIPTED'
            driver.expression = 'not is_visible'
            
            var = driver.variables.new() if not driver.variables else driver.variables[0]
            var.name = "is_visible"
            var.type = "SINGLE_PROP"
            var.targets[0].id_type = "ARMATURE"
            var.targets[0].id = armature
            if is_version_4:
                var.targets[0].data_path = path
            else:
                var.targets[0].data_path = "layers[1]"
        except Exception as ex:
            print(f"[HSR] drive_visibility_with_prop notice for {obj_name}: {ex}")
        
    drive_visibility_with_prop("ColorWheel-Ambient", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-Fresnel", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-Lit", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-RimLit", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-RimShadow", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-Shadow", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-SoftLit", "collections[\"Lighting\"].is_visible")
    drive_visibility_with_prop("ColorWheel-SoftShadow", "collections[\"Lighting\"].is_visible")
  
    
    # Post modification, Adjustment of bone layers/collections.
    if not is_version_4:
        for x in range(29):
            if x>0:
                bpy.context.object.data.layers[x] = False
                
        # Disable/Enable Rig UI layers we care about
        bpy.context.object.data.layers[0] = True
        bpy.context.object.data.layers[1] = True if lighting_panel_rig_obj else False  # Lighting
        bpy.context.object.data.layers[3] = True
        bpy.context.object.data.layers[4] = False
        bpy.context.object.data.layers[5] = True
        bpy.context.object.data.layers[6] = False
        bpy.context.object.data.layers[7] = True
        bpy.context.object.data.layers[8] = False
        bpy.context.object.data.layers[10] = True
        bpy.context.object.data.layers[11] = False
        bpy.context.object.data.layers[13] = True
        bpy.context.object.data.layers[14] = False
        bpy.context.object.data.layers[16] = True
        bpy.context.object.data.layers[17] = False
        bpy.context.object.data.layers[20] = False
        bpy.context.object.data.layers[21] = False
        bpy.context.object.data.layers[22] = False
        bpy.context.object.data.layers[28] = True
        bpy.context.object.data.layers[26] = False
        bpy.context.object.data.collections["Tweaks"].is_visible = False
        if "Props" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Props"].is_visible = False
        if "Weapon" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Weapon"].is_visible = False
        if "Face" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Face"].is_visible = True
        bpy.context.object.data.collections["Pivots & Pins"].is_visible = False
        bpy.context.object.data.collections["Offsets"].is_visible = False
        bpy.context.object.data.collections["Torso (FK)"].is_visible = False
        bpy.context.object.data.collections["Fingers (Detail)"].is_visible = False
        bpy.context.object.data.collections["Arm.L (FK)"].is_visible = False
        bpy.context.object.data.collections["Arm.R (FK)"].is_visible = False
        bpy.context.object.data.collections["Leg.L (FK)"].is_visible = False
        bpy.context.object.data.collections["Leg.R (FK)"].is_visible = False
        bpy.context.object.data.collections["Hair"].is_visible = False
        bpy.context.object.data.collections["Clothes"].is_visible = False
        bpy.context.object.data.collections["Cage"].is_visible = False
        bpy.context.object.data.collections["Other"].is_visible = False
        if "Light Panel Extras" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Light Panel Extras"].is_visible = False
        if "Light Panel" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Light Panel"].is_visible = True
    
    # Send the given bone to its new location for either version. Adjusted for actual layer num.
    # MOVING OF BONES BELOW -------------------------------
    def bone_to_layer(bone, layer, collection, second_coll="None"):
        arm = bpy.context.object
        if bone in arm.data.bones:
            if is_version_4:
                target_coll = arm.data.collections.get(collection)
                if not target_coll:
                    target_coll = arm.data.collections.new(collection)
                target_coll.assign(arm.data.bones[bone])
                if collection != "Other" and "Other" in arm.data.collections:
                    try:
                        arm.data.collections["Other"].unassign(arm.data.bones[bone])
                    except Exception:
                        pass
                if second_coll != "None":
                    scoll = arm.data.collections.get(second_coll)
                    if not scoll:
                        scoll = arm.data.collections.new(second_coll)
                    scoll.assign(arm.data.bones[bone])
            else:
                move_bone(bone,layer)
                
    # Since we've looped through ever 4.0 bone to place in 'other' above, we'll have to do so as well for 3.6
    if not is_version_4:
        for bone in bpy.context.active_object.pose.bones:
            bone_to_layer(bone.name, 25, "Other")            
    
    loop_arm = bpy.context.object.data
    for bone in loop_arm.bones:
        if "tweak" in bone.name and "MCH" not in bone.name and "pin" not in bone.name:
            bone_to_layer(bone.name, 2, "Tweaks")  
    
    # Moving to Tweaks (werent catched in loop)
    bone_to_layer("tweak_spine", 2, "Tweaks") 
    bone_to_layer("tweak_spine.001", 2, "Tweaks") 
    bone_to_layer("tweak_spine.002", 2, "Tweaks") 
    bone_to_layer("tweak_spine.003", 2, "Tweaks") 
    bone_to_layer("tweak_spine.004", 2, "Tweaks") 
    bone_to_layer("tweak_spine.005", 2, "Tweaks") 
    # MOVING PIVOTS AND PINS
    bone_to_layer("torso_pivot.002", 19, "Pivots & Pins") 
    bone_to_layer("forearm_tweak-pin.L", 19, "Pivots & Pins") 
    bone_to_layer("hand_ik_pivot.L", 19, "Pivots & Pins") 
    bone_to_layer("hand_ik_pivot.R", 19, "Pivots & Pins") 
    bone_to_layer("forearm_tweak-pin.R", 19, "Pivots & Pins") 
    bone_to_layer("shin_tweak-pin.L", 19, "Pivots & Pins") 
    bone_to_layer("shin_tweak-pin.R", 19, "Pivots & Pins") 
    bone_to_layer("foot_ik_pivot.L", 19, "Pivots & Pins") 
    bone_to_layer("foot_ik_pivot.R", 19, "Pivots & Pins") 
    
    # MOVING FACE (head-controller, face in Face collection, plate-settings in Root)
    bone_to_layer("plate-settings", 28, "Root")
    bone_to_layer("head-controller", 0, "Face")
    bone_to_layer("Face-Root", 0, "Face")
    
    # Moving Torso
    bone_to_layer("head", 3, "Torso (IK)")  
    bone_to_layer("neck", 3, "Torso (IK)")  
    bone_to_layer("chest", 3, "Torso (IK)")  
    bone_to_layer("torso", 3, "Torso (IK)")  
    bone_to_layer("torso.001", 26, "Offsets")  
    bone_to_layer("torso.002", 26, "Offsets")  
    bone_to_layer("hips", 3, "Torso (IK)")  
    
    bone_to_layer("spine_fk.003", 4, "Torso (FK)")  
    bone_to_layer("spine_fk.002", 4, "Torso (FK)")  
    bone_to_layer("spine_fk.001", 4, "Torso (FK)")  
    bone_to_layer("spine_fk", 4, "Torso (FK)")  
    
    # Moving Fingers
    bone_to_layer("thumb.01_master.L", 5, "Fingers")  
    bone_to_layer("thumb.01_master.R", 5, "Fingers")  
    bone_to_layer("f_index.01_master.L", 5, "Fingers")  
    bone_to_layer("f_index.01_master.R", 5, "Fingers")  
    bone_to_layer("f_middle.01_master.L", 5, "Fingers")  
    bone_to_layer("f_middle.01_master.R", 5, "Fingers")  
    bone_to_layer("f_ring.01_master.L", 5, "Fingers")  
    bone_to_layer("f_ring.01_master.R", 5, "Fingers")  
    bone_to_layer("f_pinky.01_master.L", 5, "Fingers")  
    bone_to_layer("f_pinky.01_master.R", 5, "Fingers")  
    
    bone_to_layer("thumb.01.L", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.01.R", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.02.L", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.02.R", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.03.L", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.03.R", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.01.L.001", 6, "Fingers (Detail)")  
    bone_to_layer("thumb.01.R.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.01.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.01.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.02.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.02.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.03.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.03.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.01.L.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_index.01.R.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.01.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.01.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.02.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.02.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.03.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.03.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.01.L.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_middle.01.R.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.01.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.01.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.02.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.02.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.03.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.03.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.01.L.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_ring.01.R.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.01.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.01.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.02.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.02.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.03.L", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.03.R", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.01.L.001", 6, "Fingers (Detail)")  
    bone_to_layer("f_pinky.01.R.001", 6, "Fingers (Detail)") 

    # IK Fingers
    try:
        bone_to_layer("thumb.01_ik.L", 6, "Fingers (Detail)") 
        bone_to_layer("thumb.01_ik.R", 6, "Fingers (Detail)") 
        bone_to_layer("f_index.01_ik.L", 6, "Fingers (Detail)") 
        bone_to_layer("f_index.01_ik.R", 6, "Fingers (Detail)") 
        bone_to_layer("f_middle.01_ik.L", 6, "Fingers (Detail)") 
        bone_to_layer("f_middle.01_ik.R", 6, "Fingers (Detail)") 
        bone_to_layer("f_ring.01_ik.L", 6, "Fingers (Detail)") 
        bone_to_layer("f_ring.01_ik.R", 6, "Fingers (Detail)") 
        bone_to_layer("f_pinky.01_ik.L", 6, "Fingers (Detail)") 
        bone_to_layer("f_pinky.01_ik.R", 6, "Fingers (Detail)") 
    except:
        pass

    if lighting_panel_rig_obj:
        bone_to_layer("Lighting Panel", 1, "Lighting")
        bone_to_layer("FresnelToggle", 1, "Lighting")
        bone_to_layer("Fresnel", 1, "Lighting")
        bone_to_layer("FresnelSize", 1, "Lighting")
        bone_to_layer("Ambient", 1, "Lighting")
        bone_to_layer("SoftLit", 1, "Lighting")
        bone_to_layer("Lit", 1, "Lighting")  # Sharp Lit
        bone_to_layer("SoftShadow", 1, "Lighting")
        bone_to_layer("Shadow", 1, "Lighting")  # Sharp Shadow
        bone_to_layer("RimShadow", 1, "Lighting")
        bone_to_layer("Rim Lit", 1, "Lighting")
        bone_to_layer("RimX", 1, "Lighting")
        bone_to_layer("RimY", 1, "Lighting")
        bone_to_layer("RimLitPin", 1, "Lighting")
        bone_to_layer("ShadowOffset", 1, "Lighting")
        bone_to_layer("ShadowPin", 1, "Lighting")
        bone_to_layer("LitPin", 1, "Lighting")
        bone_to_layer("AmbientPin", 1, "Lighting")
        bone_to_layer("RimShadowPin", 1, "Lighting")
        bone_to_layer("SoftShadowPin", 1, "Lighting")
        bone_to_layer("SoftLitPin", 1, "Lighting")
        bone_to_layer("FresnelPin", 1, "Lighting")

    # Pass in a list, all of those bones will be moved accordingly.
    def fast_bone_move(bone_list, layer, collection):
        for bone in bone_list:
            bone_to_layer(bone, layer, collection)
    
    # Refactoring old bone move functionalities
    list_move_to_other = ["+UpperArmTwistA02.L","+UpperArmTwistA01.L","+UpperArmTwistA01.R","+UpperArmTwistA02.R","eye.R","eye.L","+ToothBone D A01","+ToothBone U A01","+ToothBone A A01"]
    fast_bone_move(list_move_to_other, 25, "Other")
    
    if toe_bones_exist:
        bone_to_layer("toe_ik.L", 13, "Leg.L (IK)")
        bone_to_layer("toe_ik.R", 16, "Leg.R (IK)")
    else:
        bone_to_layer("toe_ik.L", 25, "Other")
        bone_to_layer("toe_ik.R", 25, "Other")
    
    bone_to_layer("upper_arm_ik.L", 7, "Arm.L (IK)")
    bone_to_layer("upper_arm_ik.R", 10, "Arm.R (IK)")
    
    bone_to_layer("thigh_ik.L", 13, "Leg.L (IK)")
    bone_to_layer("thigh_ik.R", 16, "Leg.R (IK)")
        
    pass
           
    # New bones, post append 
    list_to_send_other = [
        "MCH-thigh_ik_target_sub.L", "MCH-thigh_ik_target_sub.R",
        "MCH-foot_ik_pivot.L", "MCH-foot_ik_pivot.R",
        "MCH-hand_ik_pivot.L", "MCH-hand_ik_pivot.R",
        "MCH-hand_ik_wrist.L", "MCH-hand_ik_wrist.R",
        "MCH-torso_pivot.002",
        "MCH-head-controller-parent",
        "MCH-Skirt_Parent", "MCH-Skirt_Parent02", "MCH-INT-Skirt_Parent02",
        "MCH-Skirt_Auto_Calc_X.L", "MCH-Skirt_Auto_Calc_Z.L",
        "MCH-Skirt_Auto_Calc_X.R", "MCH-Skirt_Auto_Calc_Z.R",
    ] + all_skirt_tip_bones
    
    fast_bone_move(list_to_send_other, 25, "Other")
    fast_bone_move(all_skirt_deform_bones, 29, "Cage")
    fast_bone_move(all_skirt_ctrl_bones, 22, "Clothes")
    for cb in all_skirt_ctrl_bones:
        cb_low = cb.lower()
        if ".l" in cb_low or "_l" in cb_low or " l" in cb_low:
            assign_bone_to_group(cb, "Limbs L")
        elif ".r" in cb_low or "_r" in cb_low or " r" in cb_low:
            assign_bone_to_group(cb, "Limbs R")
        else:
            assign_bone_to_group(cb, "Torso")
    
    send_to_pivots = ["foot_ik_pivot.L","foot_ik_pivot.R","hand_ik_pivot.L","hand_ik_pivot.R","torso_pivot.002","forearm_tweak-pin.L","forearm_tweak-pin.R","shin_tweak-pin.L","shin_tweak-pin.R"]
    fast_bone_move(send_to_pivots, 19, "Pivots & Pins")
    
    bone_to_layer("root", 28, "Root")
    bone_to_layer("root.001", 28, "Root")
    bone_to_layer("root.002", 28, "Root")
    assign_bone_to_group("root", "Root")
    assign_bone_to_group("root.001", "Root")
    assign_bone_to_group("root.002", "Root")
    bone_to_layer("plate-settings", 28, "Root")
    assign_bone_to_group("plate-settings", "Root")
    
    bone_to_layer("hand_ik.L",7,"Arm.L (IK)")
    bone_to_layer("hand_ik_wrist.L",26,"Offsets")
    bone_to_layer("upper_arm_parent.L",[7,8],"Arm.L (IK)","Arm.L (FK)")
    bone_to_layer("upper_arm_ik_target.L",7,"Arm.L (IK)")
    bone_to_layer("shoulder.L",[7,8],"Arm.L (IK)","Arm.L (FK)")
    
    bone_to_layer("hand_ik.R",10,"Arm.R (IK)")
    bone_to_layer("upper_arm_parent.R",[10,11],"Arm.R (IK)","Arm.R (FK)")
    bone_to_layer("hand_ik_wrist.R",26,"Offsets")
    bone_to_layer("upper_arm_ik_target.R",10,"Arm.R (IK)")
    bone_to_layer("shoulder.R",[10,11],"Arm.R (IK)","Arm.R (FK)")
    
    bone_to_layer("upper_arm_fk.L",8,"Arm.L (FK)")
    bone_to_layer("forearm_fk.L",8,"Arm.L (FK)")
    bone_to_layer("hand_fk.L",8,"Arm.L (FK)")
    
    bone_to_layer("upper_arm_fk.R",11,"Arm.R (FK)")
    bone_to_layer("forearm_fk.R",11,"Arm.R (FK)")
    bone_to_layer("hand_fk.R",11,"Arm.R (FK)")
    
    bone_to_layer("foot_ik.L",13,"Leg.L (IK)")
    bone_to_layer("thigh_parent.L",[13,14],"Leg.L (IK)","Leg.L (FK)")
    bone_to_layer("thigh_ik_target.L",13,"Leg.L (IK)")
    bone_to_layer("foot_ik_sub.L",26,"Offsets")
    bone_to_layer("foot_spin_ik.L",13,"Leg.L (IK)")
    bone_to_layer("foot_heel_ik.L",13,"Leg.L (IK)")
    
    bone_to_layer("thigh_fk.L",14,"Leg.L (FK)")
    bone_to_layer("shin_fk.L",14,"Leg.L (FK)")
    bone_to_layer("foot_fk.L",14,"Leg.L (FK)")
    bone_to_layer("toe_fk.L",14,"Leg.L (FK)")
    
    bone_to_layer("foot_ik.R",16,"Leg.R (IK)")
    bone_to_layer("thigh_parent.R",[16,17],"Leg.R (IK)","Leg.R (FK)")    
    bone_to_layer("thigh_ik_target.R",16,"Leg.R (IK)")
    bone_to_layer("foot_ik_sub.R",26,"Offsets")
    bone_to_layer("foot_spin_ik.R",16,"Leg.R (IK)")
    bone_to_layer("foot_heel_ik.R",16,"Leg.R (IK)")
    
    bone_to_layer("thigh_fk.R",17,"Leg.R (FK)")
    bone_to_layer("shin_fk.R",17,"Leg.R (FK)")
    bone_to_layer("foot_fk.R",17,"Leg.R (FK)")
    bone_to_layer("toe_fk.R",17,"Leg.R (FK)")
    
    # Move main circular controls to Torso (IK)
    main_breast_controls = ["breast.L", "breast.R", "breast_master", "breath", "breath.L", "breath.R", "breath_master", "bust.L", "bust.R"]
    for c_name in main_breast_controls:
        bone_to_layer(c_name, 3, "Torso (IK)")

    # Move all stick / deform breast bones to 'Other' collection so only circular widgets remain in Torso (IK)
    for b in loop_arm.bones:
        b_low = b.name.lower()
        if ("breast" in b_low or "breath" in b_low or "bust" in b_low or "chest" in b_low or "boob" in b_low):
            if b.name not in main_breast_controls:
                bone_to_layer(b.name, 25, "Other")
    
    bone_to_layer("prop.L", 21, "Weapon")
    bone_to_layer("prop.R", 21, "Weapon")

    # Assign all detected weapon bones to Weapon collection
    for wb_name in detected_weapon_bone_names:
        bone_to_layer(wb_name, 21, "Weapon")

    # Catch any remaining weapon bones (excluding back/spine weaponbox and clothing false positives)
    for b in loop_arm.bones:
        b_low = b.name.lower()
        if "box" in b_low or "weaponbox" in b_low:
            continue
        if any(nw in b_low for nw in ["skirt", "hair", "dress", "cloth", "ribbon", "bowknot", "knot", "tie", "flower", "body", "elbow"]):
            continue
        if any(k in b_low for k in ["prop1", "prop2", "weapon", "garape", "grape", "equip", "umbrella"]) or "_wpn_" in b_low or "_weapon_" in b_low or "_garape_" in b_low or "_grape_" in b_low or "garape" in b_low or "grape" in b_low:
            bone_to_layer(b.name, 21, "Weapon")

    # Ensure all face bones (slider-, frame-, eyetrack, plate-, Face-, Wink, etc.) are in Face (excluding plate-settings which is Root)
    for b in loop_arm.bones:
        b_low = b.name.lower()
        if "plate-settings" in b_low:
            continue
        if any(k in b_low for k in ["slider-", "frame-", "brow-", "eye-", "mouth-", "plate-", "face-", "wgt-eye", "wink"]):
            bone_to_layer(b.name, 0, "Face")

    # Explicitly enforce plate-settings in Root collection and Root group
    bone_to_layer("plate-settings", 28, "Root")
    assign_bone_to_group("plate-settings", "Root")
    if is_version_4:
        c_face = loop_arm.collections.get("Face")
        if c_face and "plate-settings" in loop_arm.bones:
            try:
                c_face.unassign(loop_arm.bones["plate-settings"])
            except Exception:
                pass
        c_root = loop_arm.collections.get("Root")
        if c_root and "plate-settings" in loop_arm.bones:
            try:
                c_root.assign(loop_arm.bones["plate-settings"])
            except Exception:
                pass

    print("Done.")
    
    def loop_place_physics():
        # This list contains every bone that we should simply not handle as part of physics.
        ignore_list = {
            "+UpperArmTwistA02.L",
            "+UpperArmTwistA01.L",
            "+UpperArmTwistA01.R",
            "+UpperArmTwistA02.R",
            "eye.R",
            "eye.L",
            "+ToothBone D A01",
            "+ToothBone U A01",
            "+ToothBone A A01",
            "+EyeBone L A01",
            "+EyeBoneA02.L",
            "+EyeBone R A01",
            "+EyeBoneA02.R",
            "+EyeBone R A01.001",
            "+EyeBone L A01.001",
            "+PelvisTwist CF A01",
            "+ForeArmTwistSA01.R",
            "+ForeArmTwistSA01.L",
            "+ShoulderSA01.L",
            "+ShoulderSA01.R",
            "+ElbowSA01.R",
            "+ElbowSA01.L",
            "+KneeFA01.R",
            "+KneeFA01.L",
            "+SkirtAllF CF A01",
            "+ForearmTwistSA01.R",
            "+ForearmTwistSA01.L",
            "+ThighTwistSA01.R",
            "+ThighTwistSA01.L"
        }

        hair_keywords = [
            "hair", "eardrop", "headline", "ahoge", "bangs", "ponytail", "twintail", "bone00"
        ]
        clothes_keywords = [
            "ribbon", "sleeve", "strap", "skirt", "button", "belt", "cloth", "dress",
            "cape", "coat", "hem", "scarf", "tassel", "string", "chain", "acc",
            "qun", "xiu", "sce", "tail", "amice", "pants", "sock", "shoe",
            "necklace", "earring", "pendant", "badge", "prop", "breast"
        ]

        rigify_keywords = [
            "tweak", "_fk", "_ik", "master", "thumb", "f_index", "f_middle", "f_ring", "f_pinky",
            "forearm", "upper_arm", "thigh", "shin", "foot", "toe", "hand", "shoulder",
            "spine", "torso", "head", "neck", "root", "twist"
        ]

        arm_bones = this_obj.data.bones if is_version_4 else bpy.context.active_object.pose.bones

        for bone in arm_bones:
            b_name = bone.name
            b_low = b_name.lower()

            if b_name.startswith("DEF-") or b_name.startswith("ORG-") or b_name.startswith("MCH-"):
                continue

            if b_name.endswith("_tip") or b_name in all_skirt_tip_bones:
                bone_to_layer(b_name, 25, "Other")
                continue

            if b_name in all_skirt_deform_bones:
                bone_to_layer(b_name, 24, "Cage")
                continue

            if b_name in ignore_list:
                bone_to_layer(b_name, 25, "Other")
                continue

            # Skip standard Rigify controls unless explicitly hair or clothes
            if any(rk in b_low for rk in rigify_keywords) and not (
                b_name.startswith("+") or any(k in b_low for k in ["hair", "skirt", "dress", "cloth", "ribbon", "tail", "amice"])
            ):
                continue

            # 1. Hair matching (handles ZZZ "Hair 1.L", "Hair", "+Hair", etc.)
            if any(hk in b_low for hk in hair_keywords) or "+Hair" in b_name or "+hair" in b_name:
                bone_to_layer(b_name, 20, "Hair")
            # 2. Clothes / Dress matching (handles ZZZ "Amice", "Skirt", secondary bones, "+", etc.)
            elif any(ck in b_low for ck in clothes_keywords) or (b_name.startswith("+") and b_name not in ignore_list):
                bone_to_layer(b_name, 22, "Clothes")
            elif "amice" in b_low or (("fk" not in b_low and "tweak" not in b_low and "twist" not in b_low and "hair" not in b_low) and (b_name[-1].isdigit() or (len(b_name) >= 3 and b_name[-3].isdigit())) and not any(rk in b_low for rk in rigify_keywords)):
                bone_to_layer(b_name, 22, "Clothes")

    loop_place_physics()
    
    def loop_place_def():
        # Handpicked bones to serve as the def layer.
        list_custom_skel = ["DEF-thigh.L", "DEF-thigh.R","DEF-shin.L","DEF-shin.R","DEF-foot.L","DEF-foot.R","DEF-spine.001","DEF-spine.002","DEF-spine.003","DEF-spine.004","DEF-spine.006","+UpperArmTwistA02.L","+UpperArmTwistA02.R","DEF-forearm.L","DEF-forearm.R","DEF-hand.R","DEF-hand.L","DEF-shoulder.R","DEF-shoulder.L"]
        
        for bone in list_custom_skel:
            bone_to_layer(bone,24,"Cage")
        
        # Otherwise, anything picked up by VG scan, enable below and disable above.
        #for bone in armature.bones:
        #    if bone.name in vertex_groups_list:
        #        bone_to_layer(bone.name,24,"Cage")

        
    loop_place_def()
    fast_bone_move(all_skirt_deform_bones, 24, "Cage")
    fast_bone_move(all_skirt_ctrl_bones, 22, "Clothes")
    fast_bone_move(all_skirt_tip_bones, 25, "Other")

    # Dedicated Tails bone collection (Rig Layers): tail chains + tail_ik controls.
    # Runs after loop_place_physics (which drops "tail" bones into Clothes).
    # Ponytail/twintail stay in Hair; deform/mechanism bones stay out.
    if is_version_4 and hasattr(this_obj.data, "collections"):
        try:
            tails_coll = this_obj.data.collections.get("Tails") or this_obj.data.collections.new("Tails")
            try:
                tails_coll.is_visible = True
            except Exception:
                pass
            for b in this_obj.data.bones:
                bn = b.name
                bl = bn.lower()
                if "tail" not in bl:
                    continue
                if bn.startswith(("DEF-", "MCH-", "ORG-")):
                    continue
                if any(k in bl for k in ("hook", "tweak", "eyetrack", "pendant", "hair", "ponytail", "twintail", "eardrop", "ahoge")):
                    continue
                tails_coll.assign(b)
                for _oc in ("Other", "Clothes"):
                    _c = this_obj.data.collections.get(_oc)
                    if _c:
                        try:
                            _c.unassign(b)
                        except Exception:
                            pass
        except Exception as e_tails:
            print(f"[TAILS] Bone collection notice: {e_tails}")

    # Final sweep: dissolve any facerig or props collections into Face and Weapon, hooks to Other, all roots to Root
    if is_version_4 and hasattr(this_obj.data, "collections"):
        colls = this_obj.data.collections
        face_coll = colls.get("Face") or colls.new("Face")
        root_coll = colls.get("Root") or colls.new("Root")
        other_coll = colls.get("Other") or colls.new("Other")
        to_remove = []
        for c in colls:
            c_low = c.name.lower()
            if "facerig" in c_low or "face hook" in c_low:
                for b in list(c.bones):
                    if "hook" in b.name.lower():
                        other_coll.assign(b)
                    else:
                        face_coll.assign(b)
                to_remove.append(c)
            elif c.name in ["Props", "props"]:
                w_coll = colls.get("Weapon") or colls.new("Weapon")
                for b in list(c.bones):
                    w_coll.assign(b)
                to_remove.append(c)
            elif "weaponbox" in c_low:
                target_c = colls.get("Clothes") or colls.get("Other")
                if target_c:
                    for b in list(c.bones):
                        target_c.assign(b)
                to_remove.append(c)
        for c in to_remove:
            try:
                colls.remove(c)
            except Exception:
                pass

        # Move all hook bones (e.g. CTRL-Skn_L_highlights_hook) to Other and remove from Face
        for b in this_obj.data.bones:
            if "hook" in b.name.lower():
                other_coll.assign(b)
                if face_coll:
                    face_coll.unassign(b)

        # Ensure all 3 root bones (root, root.001, root.002) and plate-settings are in Root collection
        for r_name in ["root", "root.001", "root.002", "plate-settings"]:
            rb = this_obj.data.bones.get(r_name)
            if rb:
                root_coll.assign(rb)
                if "Offsets" in colls:
                    colls["Offsets"].unassign(rb)
                if other_coll:
                    other_coll.unassign(rb)
                if r_name == "plate-settings" and face_coll:
                    face_coll.unassign(rb)

        face_coll.is_visible = True
        root_coll.is_visible = True
        if "Weapon" in colls:
            actual_w_bones = [b for b in colls["Weapon"].bones if b.name not in ["prop.L", "prop.R"]]
            colls["Weapon"].is_visible = len(actual_w_bones) > 0
    else:
        actual_w_bones = [b for b in this_obj.data.bones if b.layers[21] and b.name not in ["prop.L", "prop.R"]]
        this_obj.data.layers[21] = len(actual_w_bones) > 0

    # MOVING OF BONES END -------------------------------    

    # Assign tweak custom shape to all tail bones (_Tail_) except IK bones
    tweak_shape = (
        next((o for o in bpy.data.objects if o.type == 'MESH' and "tweak_spine" in o.name), None)
        or next((o for o in bpy.data.objects if o.type == 'MESH' and "_tweak" in o.name), None)
    )
    if tweak_shape and this_obj and hasattr(this_obj, "pose") and this_obj.pose:
        for pb in this_obj.pose.bones:
            if ("_tail_" in pb.name.lower() or "_tail" in pb.name.lower() or pb.name.lower().startswith("tail")) and "ik" not in pb.name.lower():
                pb.custom_shape = tweak_shape
                pb.use_custom_shape_bone_size = False
                pb.custom_shape_scale_xyz = (0.08, 0.08, 0.08)
                pb.rotation_mode = 'XYZ'

    # Configure Tail IK constraints, widgets, and controls
    prop_wgt = bpy.data.objects.get("prop-wgt")
    if this_obj and hasattr(this_obj, "pose") and this_obj.pose:
        for ik_name, last_name, chain_len in tail_ik_info:
            pb_last = this_obj.pose.bones.get(last_name)
            pb_ik = this_obj.pose.bones.get(ik_name)
            if pb_last and pb_ik:
                # Add IK constraint to the last bone of the tail chain (active by default).
                # use_tail: the tip aims at the controller instead of collapsing onto it
                # (fixes the "weird spin" when reaching for the IK target).
                ik_c = pb_last.constraints.get("Tail_IK") or pb_last.constraints.new('IK')
                ik_c.name = "Tail_IK"
                ik_c.target = this_obj
                ik_c.subtarget = ik_name
                ik_c.chain_count = chain_len
                ik_c.use_rotation = True
                try:
                    ik_c.use_tail = True
                except Exception:
                    pass
                ik_c.influence = 1.0

                # Configure tail_ik controller with prop cube widget
                pb_ik.rotation_mode = 'XYZ'
                if prop_wgt:
                    pb_ik.custom_shape = prop_wgt
                    pb_ik.use_custom_shape_bone_size = False
                    pb_ik.custom_shape_scale_xyz = (0.35, 0.35, 0.35)

                # Custom properties on the tail_ik control, shown in Rig Main
                # Properties when the bone is selected: IK->FK switch + stiffness.
                # Limits via id_properties_ui() (official API) so sliders clamp 0..1.
                def _set_tail_prop(pbone, key, value, description=""):
                    try:
                        if key in pbone:
                            try:
                                del pbone[key]
                            except Exception:
                                pass
                        pbone[key] = value
                    except Exception as e_prop:
                        print(f"[TAIL IK] Property notice for {key}: {e_prop}")
                        return
                    try:
                        ui_data = pbone.id_properties_ui(key)
                        ui_data.update(
                            min=0.0, max=1.0,
                            soft_min=0.0, soft_max=1.0,
                            description=description, default=value,
                        )
                    except Exception:
                        try:
                            ui = pbone.get("_RNA_UI")
                            if ui is None:
                                pbone["_RNA_UI"] = {}
                                ui = pbone["_RNA_UI"]
                            ui[key] = {
                                "min": 0.0, "max": 1.0,
                                "soft_min": 0.0, "soft_max": 1.0,
                                "description": description, "default": value,
                            }
                        except Exception as e_ui:
                            print(f"[TAIL IK] RNA UI notice for {key}: {e_ui}")

                _set_tail_prop(pb_ik, "IK", 1.0, "Tail FK -> IK (1.0 = IK, 0.0 = FK)")
                _set_tail_prop(pb_ik, "Flexibility", 1.0,
                               "Tail chain stiffness when following IK (0 = bend freely, 1 = rigid)")

                def _link_prop_driver(drv_holder, data_path_prop, prop_key, var_name="tail_val"):
                    try:
                        drv_holder.driver_remove(data_path_prop)
                    except Exception:
                        pass
                    try:
                        fcu = drv_holder.driver_add(data_path_prop)
                        drv = fcu.driver if hasattr(fcu, "driver") else fcu
                        drv.type = 'SCRIPTED'
                        drv.expression = var_name
                        var = drv.variables.new()
                        var.name = var_name
                        var.type = 'SINGLE_PROP'
                        target = var.targets[0]
                        target.id_type = 'OBJECT'
                        target.id = this_obj
                        target.data_path = f'pose.bones["{ik_name}"]["{prop_key}"]'
                        return True
                    except Exception as e_drv:
                        print(f"[TAIL IK DRIVER ERROR] {data_path_prop}: {e_drv}")
                        return False

                _link_prop_driver(ik_c, "influence", "IK", var_name="ik_val")

                # Chain bones: walk parents from the constrained tip so stiffness
                # drives exactly the IK chain members.
                chain_bones = []
                try:
                    _b = pb_last
                    for _i in range(int(chain_len)):
                        if _b is None:
                            break
                        if not _b.name.startswith(("DEF-", "MCH-", "ORG-")):
                            chain_bones.append(_b.name)
                        _b = _b.parent
                except Exception:
                    pass
                for _cb_name in chain_bones:
                    _pb = this_obj.pose.bones.get(_cb_name)
                    if not _pb:
                        continue
                    for _axis in ("ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"):
                        _link_prop_driver(_pb, _axis, "Flexibility", var_name="stiff_val")

                # Assign bone group and color (Torso theme, gold/yellow)
                assign_bone_to_group(ik_name, "Torso")

                # Place in collections: Torso (IK) (visible by default), Tails and Clothes
                bone_to_layer(ik_name, 3, "Torso (IK)", "Tails")
                print(f"[TAIL IK] Configured {ik_name} with prop cube widget and IK constraint on {last_name}")

    # Write rig log to Blender Text block (ALWAYS, so user can verify code ran)
    log_text = bpy.data.texts.get("RIG_LOG")
    if log_text:
        bpy.data.texts.remove(log_text)
    log_text = bpy.data.texts.new("RIG_LOG")
    log_text.write(f"=== RIG LOG ({len(_rig_log)} entries) ===\n\n")
    if _rig_log:
        for i, msg in enumerate(_rig_log, 1):
            log_text.write(f"{i}. {msg}\n")
    else:
        log_text.write("No warnings or messages recorded.\n")
    log_text.write("\n=== END ===")

    # Final Append-safe sweep: consolidate scene-root wgt / wgt.00X / WGTS leftovers
    # created later in this function (merge_duplicate_collections, slider appends...)
    # into WGTS_<Char> nested in the character collection.
    try:
        from setup_wizard.character_rig_setup.wgts_isolation import isolate_wgts_for_character
        _rig_final = bpy.data.objects.get(char_name + "Rig")
        if _rig_final is None:
            try:
                _rig_final = this_obj
            except Exception:
                _rig_final = None
        isolate_wgts_for_character(_rig_final, char_name)
    except Exception as e_wgts:
        print(f"[HSR RIG] Final WGTS sweep notice: {e_wgts}")
    
def setup_neck_and_head_follow(neck_follow_value=1.0, head_follow_value=1.0):
    if bpy.context.object and hasattr(bpy.context.object, "pose") and bpy.context.object.pose:
        for t_name in ["torso", "torso.002"]:
            torso_pb = bpy.context.object.pose.bones.get(t_name)
            if torso_pb:
                if "neck_follow" in torso_pb:
                    torso_pb["neck_follow"] = neck_follow_value
                if "head_follow" in torso_pb:
                    torso_pb["head_follow"] = head_follow_value


# Make it so that the finger scale controls can be scaled on the X axis to curl in just the fingertips instead of the entire finger.
def setup_finger_scale_controls_on_x_axis_to_curl_just_the_fingertips(rigified_rig):
    bpy.ops.object.mode_set(mode='POSE')

    for oDrv in rigified_rig.animation_data.drivers:
        for variable in oDrv.driver.variables:
            for target in variable.targets:
                if ".03" in oDrv.data_path and target.data_path[-7:] == "scale.y":
                    target.data_path = target.data_path[:-1] + "x"


    fingerlist = ["thumb.01_master", "f_index.01_master", "f_middle.01_master", "f_ring.01_master", "f_pinky.01_master"]
    for side in [".L", ".R"]:
        for bone in fingerlist:
            rigified_rig.pose.bones[bone + side].lock_scale[0] = False


# Let's 'exclude' that wgt collection: https://blenderartists.org/t/disable-exlude-from-view-layer-in-collection/1324744
def searchForLayerCollection(layerColl, coll_name):
    found = None
    if (layerColl.name == coll_name):
        return layerColl
    for layer in layerColl.children:
        found = searchForLayerCollection(layer, coll_name)
        if found:
            return found


def searchForParentLayerCollection(layerColl, coll_name):
    found = None
    for layer in layerColl.children:
        if (layer.name == coll_name):
            return layerColl
        found = searchForParentLayerCollection(layer, coll_name)
        if found:
            return found


def disable_collection(collection_name):
    view_layer_collection = bpy.context.view_layer.layer_collection

    layer_collection_to_disable = searchForLayerCollection(view_layer_collection, collection_name)
    if layer_collection_to_disable:
        layer_collection_to_disable.exclude = True
        return True
    return False


def move_collection_into_collection(source, destination, collection):  
    destination.children.link(collection)
    source.children.unlink(collection)
