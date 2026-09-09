import bpy
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
    meshes_joined=False):

    context = bpy.context
    obj = context.object
    if obj.name[-4:] == ".001":
        obj.name = obj.name[:-4]
    print("New Run\n\n")
    ## Rename all bones in selected armature to ORG

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
        'Neck_M': 'DEF-spine.004', #YO
        'Head_M': 'DEF-spine.006', #RUHROH
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
    }

    # Dynamically map spine bones (do NOT map ground root Root_M to DEF-spine)
    pose_bone_names = [b.name for b in obj.pose.bones]
    if 'Pelvis_M' in pose_bone_names:
        abadidea['Pelvis_M'] = 'DEF-spine'
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
                armature.edit_bones[whee].roll = -armature.edit_bones[bone.name].roll # R to L because rolls suck less

    ## Fixes the weirdass head bone alignment.
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

    ## Attaches the feet to the toes and the upperarms to lowerarms
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

    ## Points toe bones in correct direction
    for x in ['.L', '.R']:
        toe = 'DEF-toe'
        armature.edit_bones[toe + x].tail.z = armature.edit_bones[toe + x].head.z
        armature.edit_bones[toe + x].tail.y -= 0.05
        armature.edit_bones[toe + x].roll = 0


    bpy.ops.armature.select_all(action='DESELECT')
    try:
        select_bone(armature.edit_bones["breast.R"])
        bpy.ops.armature.symmetrize()
        bpy.ops.armature.select_all(action='DESELECT')

    except Exception:
        pass

    # Delete joint_skin_GRP if it exists (may not exist on models without face, like Sam)
    joint_skin_grp_bone = armature.edit_bones.get("joint_skin_GRP")
    if joint_skin_grp_bone is not None:
        armature.edit_bones.remove(joint_skin_grp_bone)

    # Replace joint_face parent with DEF-spine.006 if joint_face exists
    joint_face_bone = armature.edit_bones.get("joint_face")
    if joint_face_bone is not None:
      armature.edit_bones["joint_face"].parent = armature.edit_bones["DEF-spine.006"]

    #armature.edit_bones["joint_skin_GRP"].head.z = armature.edit_bones["joint_skin_GRP"].tail.z
    #armature.edit_bones["joint_skin_GRP"].tail.z += 0.1
    armature.edit_bones["Main"].tail.z = 0.1
    armature.edit_bones["Main"].tail.y = 0
    # DELETE MAIN BONE??
    #armature.edit_bones.remove(armature.edit_bones["Main"])

    try:  # If tall woman, fix their pinky finger
        if armature.edit_bones["DEF-breast.R"] and armature.edit_bones["DEF-spine.003"].tail.z > 1.3 and armature.edit_bones["DEF-spine.003"].tail.z < 1.4:
            bpy.context.object.data.use_mirror_x = True
            armature.edit_bones["DEF-f_pinky.01.L"].tail.x += 0.00164
            armature.edit_bones["DEF-f_pinky.02.L"].tail.x += 0.00164
            armature.edit_bones["DEF-f_pinky.02.L"].head.x += 0.00164
            armature.edit_bones["DEF-f_pinky.03.L"].head.x += 0.00164
            bpy.context.object.data.use_mirror_x = False

    except:
        pass

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

    # Deselect all objects
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    armature = obj.data

    for o in bpy.data.objects:
        # Check for given object names
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
            bone.roll = armature.edit_bones["DEF-" + bone.name].roll

    ## Fixes the tiddy bones.  Expykit, why did you neglect them
    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.data.objects[obj.name].data

    ## Left side first, right side's xyz is same as left, but x is negative
    def getboob(bone, tip):
        if tip == "head":
            return armature.edit_bones[bone].head.x, armature.edit_bones[bone].head.y, armature.edit_bones[bone].head.z
        else:
            return armature.edit_bones[bone].tail.x, armature.edit_bones[bone].tail.y, armature.edit_bones[bone].tail.z


    try:
        xh, yh, zh = getboob("DEF-breast.L", "head")
        xt, yt, zt = getboob("DEF-breast.L", "tail")

        ## Change the meta arm's boob positions

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
        # If breast bones dont exist in the orig rig, then delete from the meta rig
        metarm.edit_bones.remove(metarm.edit_bones["breast.L"])
        metarm.edit_bones.remove(metarm.edit_bones["breast.R"])

    # Update metarig spine bone positions from armature DEF- bones
    spines = ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
    for s_name in spines:
        def_b = armature.edit_bones.get("DEF-" + s_name)
        mb = metarm.edit_bones.get(s_name)
        if def_b and mb:
            mb.head = def_b.head.copy()
            mb.tail = def_b.tail.copy()

    # Interpolate spine.003 if unmapped (placed transitionally between spine.002 and spine.004)
    s002 = metarm.edit_bones.get("spine.002")
    s003 = metarm.edit_bones.get("spine.003")
    s004 = metarm.edit_bones.get("spine.004")
    if s002 and s003 and s004 and "DEF-spine.003" not in armature.edit_bones:
        s003.head = s002.tail.copy()
        s003.tail = s004.head.copy()

    # Subdivide neck for spine.005 if unmapped (placed transitionally between spine.004 and spine.006)
    s005 = metarm.edit_bones.get("spine.005")
    s006 = metarm.edit_bones.get("spine.006")
    if s004 and s005 and s006 and "DEF-spine.005" not in armature.edit_bones:
        neck_h = s004.head.copy()
        head_h = s006.head.copy()
        mid_x = (neck_h.x + head_h.x) / 2.0
        mid_y = (neck_h.y + head_h.y) / 2.0
        mid_z = (neck_h.z + head_h.z) / 2.0
        s004.tail.x, s004.tail.y, s004.tail.z = mid_x, mid_y, mid_z
        s005.head.x, s005.head.y, s005.head.z = mid_x, mid_y, mid_z
        s005.tail = head_h.copy()
        s006.head = head_h.copy()

    # Enforce continuous parenting and connections across full spine chain in metarig
    for idx in range(len(spines) - 1):
        pb = metarm.edit_bones.get(spines[idx])
        cb = metarm.edit_bones.get(spines[idx + 1])
        if pb and cb:
            cb.parent = pb
            pb.tail = cb.head.copy()
            cb.use_connect = True




    ##########  DETACH PHYSICS BONES,

    metanames = ['eye.L', 'eye.R', 'spine', 'thigh.L', 'shin.L', 'foot.L', 'toe.L', 'thigh.R', 'shin.R', 'foot.R', 'toe.R', 'spine.001', 'spine.002', 'spine.003', 'breast.L', 'breast.R', 'shoulder.L', 'upper_arm.L', 'forearm.L', 'hand.L', 'thumb.01.L', 'thumb.02.L', 'thumb.03.L', 'f_index.01.L', 'f_index.02.L', 'f_index.03.L', 'f_middle.01.L', 'f_middle.02.L', 'f_middle.03.L', 'f_ring.01.L', 'f_ring.02.L', 'f_ring.03.L', 'f_pinky.01.L', 'f_pinky.02.L', 'f_pinky.03.L', 'spine.004', 'spine.006', 'shoulder.R', 'upper_arm.R', 'forearm.R', 'hand.R', 'thumb.01.R', 'thumb.02.R', 'thumb.03.R', 'f_index.01.R', 'f_index.02.R', 'f_index.03.R', 'f_middle.01.R', 'f_middle.02.R', 'f_middle.03.R', 'f_ring.01.R', 'f_ring.02.R', 'f_ring.03.R', 'f_pinky.01.R', 'f_pinky.02.R', 'f_pinky.03.R']

    pre_res = ["DEF-" + bonename for bonename in metanames]
    armature = obj.data ## Original char rig


    ## Make a dictionary.  Key is a main body bone that exists in the Rigify (arm, leg, spine, etc), and the value is a list of all the children bones that aren't other main body bones (usually hair, clothes, deform, etc.)
    savethechildren = {

    }
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.edit_bones:
        if bone.name in pre_res:
            childlist = []
            for childbone in armature.edit_bones[bone.name].children:
                if childbone.name not in pre_res: # Adds only non-main body bones, avoids like forearm or knee etc
                    childlist.append(childbone.name)
            if childlist: # If list isn't empty, add it to dict
                wtf = bone.name
                savethechildren[wtf] = childlist


    ## Selects and separates the physics bones
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    bones = armature.edit_bones[:]
    for bone in bones:
        if bone.name not in pre_res:
            #this is a physics bone, so select it.
            bone.use_connect = False
            bone.select = True
            bone.select_tail = True
            bone.select_head = True

    bpy.ops.armature.separate()

    # Ensure metarig is active and in POSE mode before generating rigify rig
    metarig_obj = bpy.data.objects.get("metarig")
    if metarig_obj:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        metarig_obj.select_set(True)
        bpy.context.view_layer.objects.active = metarig_obj
        bpy.ops.object.mode_set(mode='POSE')

    # Generates rigify rig and renames it to 'rigify'
    bpy.ops.pose.rigify_generate()

    bpy.data.objects[obj.name].name = "rigify"
    bpy.context.view_layer.objects.active = bpy.data.objects[armature.name + ".001"]


    for o in bpy.data.objects:
        # Check for given object names
        if o.name in ("rigify", armature.name):
            o.select_set(True)

    # THEN REATTACH PHYSICS

    bpy.ops.object.mode_set(mode='OBJECT')
    ### BLENDER ARE U GOOD LMAO WTF IS THIS (this joins two objects together)
    newrig = armature.name + ".001" ## New temporary armature with the physics bones. Hopefully you didnt touch any names lmao

    ## Why's the list for selected objects ordered alphabetically instead of by selection order
    objList = bpy.context.selected_objects
    unselected = [obj for obj in objList if obj != context.active_object]
    rigifyr = unselected[0]  ## Rigified Rig

    obs = [bpy.data.objects[rigifyr.name], bpy.data.objects[newrig]]
    c={}
    c["object"] = c["active_object"] = bpy.data.objects[rigifyr.name]
    c["selected_objects"] = c["selected_editable_objects"] = obs
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    with bpy.context.temp_override(active_object=bpy.data.objects.get("rigify"), selected_editable_objects=obs):
        bpy.ops.object.join()


    bpy.context.view_layer.objects.active = bpy.data.objects["rigify"]
    bpy.ops.object.mode_set(mode='EDIT')

    ## Reattach the physics bones to their parents
    #Go back into rigify, find the main body bones, and reattach every bone in the corresponding dict list
    for mainbone in savethechildren:
        for childbone in savethechildren[mainbone]:
            rigifyr.data.edit_bones[childbone].parent = rigifyr.data.edit_bones[mainbone]

    for x in [".L", ".R"]:
        rigifyr.data.edit_bones["DEF-forearm" + x + ".002"].parent = rigifyr.data.edit_bones["DEF-forearm"+x]

    # Ensure Root_M and pelvic/hip root bones follow DEF-spine (or hips) so lower body moves with caderas/torso
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

    print("donelol\n")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects["rigify"].show_in_front = True
    rigifyr.data.display_type = 'STICK'

    # Append custom bone shape collections from RootShape.blend
    try:
        if file_path:
            path_to_file = file_path if "/Collection" in file_path else file_path + "/Collection"
            for coll_name in ['append_Root', 'append_Eyes', 'append_Pelvis', 'append_Foot', 'append_Hand', 'append_Props', 'append_Face Plate']:
                try:
                    bpy.ops.wm.append(filename=coll_name, directory=path_to_file)
                except Exception as e:
                    print(f"Skipped appending collection {coll_name}: {e}")
    except Exception as e:
        print(f"Error appending custom bone shapes: {e}")

    # Join eyerig armature if present (copied from ZZZ eye rig architecture)
    eye_rig_obj = bpy.data.objects.get("eyerig")
    if eye_rig_obj:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            rigifyr.select_set(True)
            eye_rig_obj.select_set(True)
            bpy.context.view_layer.objects.active = rigifyr
            bpy.ops.object.join()
            print("Successfully joined eyerig to HSR rig.")
        except Exception as e:
            print(f"Notice joining eyerig: {e}")

    # Set up eye rig bone parenting and positioning in EDIT mode
    left_eye_bone_name = None
    right_eye_bone_name = None
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        armature = rigifyr.data

        possible_eye_L = ["+EyeBone L A02", "+EyeBone L A01", "eye.L", "EYE_L", "Eye_L", "DEF-eye.L", "Skn_L_Eye", "Bdy_L_Eye"]
        possible_eye_R = ["+EyeBone R A02", "+EyeBone R A01", "eye.R", "EYE_R", "Eye_R", "DEF-eye.R", "Skn_R_Eye", "Bdy_R_Eye"]

        left_eye_bone_name = next((b for b in possible_eye_L if b in armature.edit_bones), None)
        right_eye_bone_name = next((b for b in possible_eye_R if b in armature.edit_bones), None)

        final_eye_L_name = left_eye_bone_name or "DEF-eye.L"
        final_eye_R_name = right_eye_bone_name or "DEF-eye.R"

        head_bone = armature.edit_bones.get("head") or armature.edit_bones.get("DEF-spine.006")
        # Delete eyetrack, eyetrack_L, eyetrack_R bones if present
        for eb_name in ["eyetrack", "eyetrack_L", "eyetrack_R", "eyetrack.L", "eyetrack.R"]:
            if eb_name in armature.edit_bones:
                try:
                    armature.edit_bones.remove(armature.edit_bones[eb_name])
                except Exception:
                    pass
    except Exception as e:
        print(f"Eye edit mode setup notice: {e}")

    bpy.ops.object.mode_set(mode='POSE')

    # Assign custom shapes to main control bones and disable bone length scaling ONLY for specific custom shapes
    this_obj = rigifyr

    def safe_set_custom_shape(bone_name, shape_name=None, scale=None, translation=None, rotation_euler=None, disable_bone_size=True):
        pbone = this_obj.pose.bones.get(bone_name)
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
    safe_set_custom_shape("foot_ik.L", "foot1")
    safe_set_custom_shape("foot_ik.R", "foot1")

    if bpy.data.objects.get("primo-joint"):
        safe_set_custom_shape("thigh_ik_target.L", "primo-joint", scale=(0.75, 0.75, 0.75), disable_bone_size=False)
        safe_set_custom_shape("thigh_ik_target.R", "primo-joint", scale=(0.75, 0.75, 0.75), disable_bone_size=False)
        safe_set_custom_shape("upper_arm_ik_target.L", "primo-joint", disable_bone_size=False)
        safe_set_custom_shape("upper_arm_ik_target.R", "primo-joint", disable_bone_size=False)

    safe_set_custom_shape("torso", "pelvis2")
    safe_set_custom_shape("hips", "hips", scale=(1, 1, 1), translation=(0.0, -0.04, 0.044), rotation_euler=(1.309, 0, 0))
    safe_set_custom_shape("chest", "chest", scale=(0.45, 0.45, 0.45), translation=(0.0, -0.04, 0.0), rotation_euler=(1.5708, 0, 0))

    safe_set_custom_shape("shoulder.L", None, scale=(1.6, 1.6, 1.6), disable_bone_size=False)
    safe_set_custom_shape("shoulder.R", None, scale=(1.6, 1.6, 1.6), disable_bone_size=False)

    safe_set_custom_shape("foot_heel_ik.L", None, translation=(0.0, 0.06, 0.0), disable_bone_size=False)
    safe_set_custom_shape("foot_heel_ik.R", None, translation=(0.0, 0.06, 0.0), disable_bone_size=False)

    safe_set_custom_shape("foot_spin_ik.L", None, translation=(0.0, -0.05, 0.02), disable_bone_size=False)
    safe_set_custom_shape("foot_spin_ik.R", None, translation=(0.0, -0.05, 0.02), disable_bone_size=False)

    safe_set_custom_shape("toe_ik.L", None, scale=(0.781, 0.781, 0.350), translation=(0.0, 0.06, 0.00), disable_bone_size=False)
    safe_set_custom_shape("toe_ik.R", None, scale=(0.781, 0.781, 0.350), translation=(0.0, 0.06, 0.00), disable_bone_size=False)

    safe_set_custom_shape("hand_ik.L", "hand", scale=(1.0, 1.0, 1.0), translation=(0.0, 0.0, 0.0), rotation_euler=(0.0, 0.0, 0.0), disable_bone_size=True)
    safe_set_custom_shape("hand_ik.R", "hand", scale=(1.0, 1.0, 1.0), translation=(0.0, 0.0, 0.0), rotation_euler=(0.0, 0.0, 0.0), disable_bone_size=True)

    def add_eye_bone_const(bone_name, to_bone):
        pbone = rigifyr.pose.bones.get(bone_name)
        if pbone and to_bone in rigifyr.pose.bones:
            co = pbone.constraints.new('COPY_ROTATION')
            co.target = rigifyr
            co.subtarget = to_bone
            co.target_space = "LOCAL_OWNER_ORIENT"
            co.owner_space = "LOCAL"

    try:
        if left_eye_bone_name:
            add_eye_bone_const(left_eye_bone_name, "+EyeBone L A01.001")
        if right_eye_bone_name:
            add_eye_bone_const(right_eye_bone_name, "+EyeBone R A01.001")
    except Exception as e:
        print(f"Eye bone constraint notice: {e}")

    safe_set_custom_shape("palm.L", None, scale=(1.2, 1.2, 1.2), disable_bone_size=False)
    safe_set_custom_shape("palm.R", None, scale=(1.2, 1.2, 1.2), disable_bone_size=False)

    rigifyr.pose.bones["thigh_parent.L"]["IK_Stretch"] = 0
    rigifyr.pose.bones["thigh_parent.R"]["IK_Stretch"] = 0
    rigifyr.pose.bones["upper_arm_parent.L"]["IK_Stretch"] = 0
    rigifyr.pose.bones["upper_arm_parent.R"]["IK_Stretch"] = 0
    rigifyr.pose.bones["upper_arm_parent.L"]["FK_limb_follow"] = 1
    rigifyr.pose.bones["upper_arm_parent.R"]["FK_limb_follow"] = 1

    if "torso" in rigifyr.pose.bones:
        if "neck_follow" in rigifyr.pose.bones["torso"]:
            rigifyr.pose.bones["torso"]["neck_follow"] = 1.0
        if "head_follow" in rigifyr.pose.bones["torso"]:
            rigifyr.pose.bones["torso"]["head_follow"] = 1.0

    bpy.ops.object.mode_set(mode='EDIT')
    #### Symmetrize clothes/hair bones
    eb = rigifyr.data.edit_bones
    for bone in eb:
        if "L_" in bone.name: # Finds clothes/hair bones with symmetrical bones
            try:
                y = bone.name.find('L_')  # Finds index of "HairL_1"
                orgname = bone.name
                newname = orgname[:y] + "_" + orgname[y+2:]  # newname = "Hair_1
                oppbone = orgname[:y] + "R_" + orgname[y+2:] # oppbone = "HairR_1"
                bone.name = newname + ".L"    # Renames bone to _L format
                eb[oppbone].name = newname + ".R"   # Renames opposite bone to _R format
                if (round(bone.head[0], 3) == round(-eb[newname+".R"].head[0], 3)): # Not every bone with a symmetrical name is actually *physically* symmetrical. This checks to make sure that they are.
                    eb[newname+".R"].roll = -bone.roll   # Symmetrizes rolls
            except:
                pass

    # This part puts all the main bones I use into the second bone layer/collection
    bpy.ops.object.mode_set(mode='OBJECT')
    listofbones = ["root", "foot_heel_ik.R", "foot_heel_ik.L", "toe_ik.R", "toe_ik.L", "foot_ik.R", "foot_ik.L", "thigh_ik_target.R", "thigh_ik_target.L", "hips", "torso", "chest", "neck", "head", "eyeRoot", "shoulder.L", "shoulder.R", "upper_arm_fk.L", "upper_arm_fk.R", "forearm_fk.L", "forearm_fk.R", "hand_fk.L", "hand_fk.R", "upper_arm_ik_target.L", "upper_arm_ik_target.R", "hand_ik.R", "hand_ik.L"]

    for bone in listofbones:
        try:
            bpy.context.active_object.pose.bones[bone].bone.layers[1] = True
        except:
            pass

    # Separates physics-related bones into their own bone layer/collection
    clothes_bone_name_subtsrings = ["ribbon", "sleeve", "strap", "skirt", "button", "belt", "cloth"]
    hair_bone_name_substrings = ["hair", "eardrop"]

    for armature_bone in rigifyr.pose.bones:
        for bone_name_substring in clothes_bone_name_subtsrings:
            if bone_name_substring in armature_bone.name.lower():
                assign_bone_to_bone_collection(rigifyr.data, rigifyr, armature_bone, collection_name='Clothes', collection_idx=22)
                break
        for bone_name_substring in hair_bone_name_substrings:
            if bone_name_substring in armature_bone.name.lower():
                assign_bone_to_bone_collection(rigifyr.data, rigifyr, armature_bone, collection_name='Hair', collection_idx=23)
                break

    # Change any physics bones attached to shoulder to be attached to spine instead bc it's a pain in the ass to animate
    bpy.ops.object.mode_set(mode='EDIT')
    bones = rigifyr.data.edit_bones[:]
    for bone in bones:
        if bone.parent:
            if bone.name not in pre_res and bone.parent.name in ["DEF-shoulder.L", "DEF-shoulder.R"]:
                print(bone)

                bone.parent = rigifyr.data.edit_bones["DEF-spine.003"]

    # makes a root #2 bone
    newroot = rigifyr.data.edit_bones.new("root_2")
    root = rigifyr.data.edit_bones["root"]
    newroot.head = root.head.copy()
    newroot.tail = root.tail.copy()
    newroot.roll = root.roll
    newroot.matrix = root.matrix.copy()
    newroot.tail.y += 0.5
    root.parent = newroot

    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='DESELECT')
    bones_list = rigifyr.pose.bones
    try:
        rigifyr.pose.bones["root_2"].custom_shape = bpy.data.objects["WGT-" + original_name + "_root"]
    except:
        pass

    bpy.ops.pose.select_all(action='DESELECT')
    bone = rigifyr.pose.bones["root_2"].bone
    rigifyr.data.bones.active = bone
    assign_root_bone_to_bone_collection(rigifyr.data, bone, collection_name='Root', collection_idx=1)

    try:
        bpy.ops.pose.select_all(action='DESELECT')
        bone = rigifyr.pose.bones["palm.L"].bone
        rigifyr.data.bones.active = bone
        assign_bone_to_bone_collection(rigifyr.data, rigifyr, bone, collection_name='Palms', collection_idx=21)
        unassign_bone_from_bone_collection(rigifyr.data, rigifyr, bone, collection_name='Fingers', collection_idx_range=(0, 28))

        bpy.ops.pose.select_all(action='DESELECT')
        bone = rigifyr.pose.bones["palm.R"].bone
        rigifyr.data.bones.active = bone
        assign_bone_to_bone_collection(rigifyr.data, rigifyr, bone, collection_name='Palms', collection_idx=21)
        unassign_bone_from_bone_collection(rigifyr.data, rigifyr, bone, collection_name='Fingers', collection_idx_range=(0, 28))
    except:
        pass

    ### Makes it able to scale only the fingertips by scaling the X axis on the finger scale controls
    rig = rigifyr
    if rig.animation_data and rig.animation_data.drivers:
        for oDrv in rig.animation_data.drivers:
            for variable in oDrv.driver.variables:
                for target in variable.targets:
                    if ".03" in oDrv.data_path and target.data_path[-7:] == "scale.y":
                        target.data_path = target.data_path[:-1] + "x"

            # Invert scale driver direction for index master R
            if any(k in oDrv.data_path for k in ["f_index.02_drv.R", "f_index.03_drv.R"]):
                oDrv.driver.expression = "(sy-1)*pi"

    fingerlist = ["thumb.01_master", "f_index.01_master", "f_middle.01_master", "f_ring.01_master", "f_pinky.01_master"]
    for side in [".L", ".R"]:
        for bone in fingerlist:
            if bone + side in rig.pose.bones:
                rig.pose.bones[bone + side].lock_scale[0] = False

    # Change the body outline and the hair and face outline values match.
    def add_driver(source, target, path, dataPath):
        d = source.driver_add( path).driver
        v = d.variables.new()
        d.type = "AVERAGE"
        v.name                 = "Input_7"
        v.targets[0].id        = target
        v.targets[0].data_path = dataPath

    try:
        bod = bpy.data.objects["Body"]
        face = bpy.data.objects["Face"]
        hair = bpy.data.objects["Hair"]

        add_driver(face, bod, 'modifiers["Outlines Face"]["Input_7"]', 'modifiers["Outlines Body"]["Input_7"]')
        add_driver(hair, bod, 'modifiers["Outlines Hair"]["Input_7"]', 'modifiers["Outlines Body"]["Input_7"]')
    except:
        pass

    # Puts these into a selection set (you need the addon (well no u dont bc i put this in a try block lmao))
    try:
        bpy.ops.pose.select_all(action='DESELECT')
        ## Arms
        arms = ['upper_arm_fk', 'forearm_fk', 'hand_fk', 'shoulder']
        for side in ['.L', '.R']:
            for bone in arms:
                bonename = bone + side
                rigifyr.pose.bones[bonename].bone.select= True
        bpy.ops.pose.selection_set_add()
        bpy.ops.pose.selection_set_assign()
        bpy.ops.pose.select_all(action='DESELECT')
        bpy.context.object.selection_sets[0].name = "FK Arms"
    except:
        pass

    bpy.ops.object.mode_set(mode='OBJECT')
    ## If you want no poles, delete these next few lines before 'face_mask' hide
    try:
        rigifyr.pose.bones["upper_arm_parent.L"]["pole_parent"] = 2
        rigifyr.pose.bones["upper_arm_parent.R"]["pole_parent"] = 2
        rigifyr.pose.bones["thigh_parent.L"]["pole_parent"] = 2
        rigifyr.pose.bones["thigh_parent.R"]["pole_parent"] = 2
        rigifyr.pose.bones["upper_arm_parent.R"]["pole_vector"] = True
        rigifyr.pose.bones["upper_arm_parent.L"]["pole_vector"] = True
        rigifyr.pose.bones["thigh_parent.L"]["pole_vector"] = True
        rigifyr.pose.bones["thigh_parent.R"]["pole_vector"] = True
    except:
        pass

    # Standardized bone collections setup matching Genshin Impact
    is_version_4 = bpy.app.version[0] >= 4

    char_name = extract_clean_character_name(original_name)
    try:
        if "rigify" in bpy.data.objects and bpy.data.objects["rigify"].users_collection:
            bpy.data.objects["rigify"].users_collection[0].name = char_name
    except:
        pass
    if "rigify" in bpy.data.objects:
        bpy.data.objects["rigify"].name = char_name + "Rig"
    try:
        from setup_wizard.ui.character_settings_utils import stamp_rig_game
        _rig = bpy.data.objects.get(char_name + "Rig") or rigifyr
        stamp_rig_game(_rig, "HONKAI_STAR_RAIL", char_name)
    except Exception:
        pass

    if is_version_4:
        setup_standard_bone_collections(rigifyr, is_version_4)
        distribute_standard_rig_bones(
            rigifyr,
            is_version_4=is_version_4,
            toe_bones_exist=True,
            use_arm_ik_poles=use_arm_ik_poles,
            use_leg_ik_poles=use_leg_ik_poles,
            has_lighting_panel=False
        )
    else:
        for i in range(1, 32):
            if i not in [0, 1]:
                try:
                    rigifyr.data.layers[i] = False
                except:
                    pass

    # Clean up appended shape collections and orphaned armatures like eyerig
    for coll_name in ["append_Root", "append_Eyes", "append_Pelvis", "append_Foot", "append_Hand", "append_Props", "append_Face Plate"]:
        coll = bpy.data.collections.get(coll_name)
        if coll:
            for obj in list(coll.objects):
                if obj.type == "ARMATURE" and obj.name != rigifyr.name:
                    bpy.data.objects.remove(obj, do_unlink=True)
            try:
                bpy.data.collections.remove(coll, do_unlink=True)
            except:
                pass

    # Delete unnecessary utility armatures (metarig) so they don't block Finish Setup
    for extra_arm in ["metarig"]:
        m_obj = bpy.data.objects.get(extra_arm)
        if m_obj:
            try:
                bpy.data.objects.remove(m_obj, do_unlink=True)
            except:
                pass

    # Genshin-style: per-character head/light empties (multi-char + Append safe).
    # Head* go to WGTS_<Char> via isolation below (prefix match covers _Char suffix).
    # Light Direction stays in the character collection.
    def get_and_rename_empty(empty_name):
        obj = bpy.data.objects.get(empty_name)
        if obj:
            obj.name = f"{empty_name}_{char_name}"
            return obj.name
        return None

    get_and_rename_empty("Face Light Direction")
    get_and_rename_empty("Head Driver")
    get_and_rename_empty("Head Origin")
    get_and_rename_empty("Head Forward")
    get_and_rename_empty("Head Up")
    new_name = get_and_rename_empty("Main Light Direction")
    if new_name:
        move_into_collection(new_name, char_name)
    new_name = get_and_rename_empty("Light Direction")
    if new_name:
        move_into_collection(new_name, char_name)

    # Head ChildOf inverse BEFORE isolation (object must be visible/accessible
    # in the view layer for the operator to evaluate).
    try:
        head_obj = (
            bpy.data.objects.get(f"Head Origin_{char_name}")
            or bpy.data.objects.get(f"Head Driver_{char_name}")
            or bpy.data.objects.get("Head Origin")
            or bpy.data.objects.get("Head Driver")
        )
        if head_obj:
            saved_mat = head_obj.matrix_world.copy()
            bpy.context.view_layer.objects.active = head_obj
            bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')
            head_obj.matrix_world = saved_mat
    except Exception:
        pass

    # Move widget objects into per-character WGTS_<Char> (Append-safe, no global wgt)
    try:
        from setup_wizard.character_rig_setup.wgts_isolation import isolate_wgts_for_character
        isolate_wgts_for_character(rigifyr, char_name)
    except Exception as e_wgts:
        print(f"[HSR RIG] WGTS isolation notice: {e_wgts}")
        widget_keywords = [
            "head-control-shape", "root plate", "eye circle", "eye controller", "WGT-"
        ]
        for obj in list(bpy.data.objects):
            if any(keyword in obj.name for keyword in widget_keywords):
                move_into_collection(obj.name, "wgt")
                try:
                    obj.hide_viewport = True
                    obj.hide_render = True
                except:
                    pass

        wgt_coll = bpy.data.collections.get("wgt")
        if wgt_coll:
            wgt_coll.hide_viewport = True
            wgt_coll.hide_select = True
            wgt_coll.hide_render = True

        try:
            def find_layer_coll(lc, name):
                if lc.name == name:
                    return lc
                for child in lc.children:
                    res = find_layer_coll(child, name)
                    if res:
                        return res
                return None
            wgt_lc = find_layer_coll(bpy.context.view_layer.layer_collection, "wgt")
            if wgt_lc:
                wgt_lc.exclude = True
        except:
            pass

        # Remove empty WGTS collections left by Rigify
        for coll in list(bpy.data.collections):
            if coll.name.startswith("WGTS"):
                if len(coll.objects) == 0 and len(coll.children) == 0:
                    try:
                        bpy.data.collections.remove(coll, do_unlink=True)
                    except:
                        pass

    try:
        bpy.data.objects["Face_Mask"].hide_viewport = True
        bpy.data.objects["Face_Mask"].hide_render = True
    except:
        pass

    # Update Rigify UI script to standard Genshin layout with stars and version
    modify_and_run_rig_ui_script(rigifyr, original_name, char_name=char_name)

    lis = ["Body", "Face", "Hair"]
    for obj_name in lis:
        obj = bpy.data.objects.get(obj_name) or bpy.context.scene.objects.get(obj_name)
        if obj:
            for mod in obj.modifiers:
                if 'outline' in mod.name.lower() or (mod.type == 'NODES' and mod.node_group and 'outline' in mod.node_group.name.lower()):
                    mod.show_viewport = True

    # Final sweep: catch widgets created after the first isolation
    # (wm.append duplicates like head-control-shape.001, Rigify UI run, etc.)
    try:
        from setup_wizard.character_rig_setup.wgts_isolation import isolate_wgts_for_character as _iso_final
        _iso_final(rigifyr, char_name)
    except Exception:
        pass


def move_into_collection(object_name, collection_name):
    obj = bpy.data.objects.get(object_name)
    if not obj:
        return
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        coll = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
    for ucoll in list(obj.users_collection):
        ucoll.objects.unlink(obj)
    coll.objects.link(obj)


def use_bone_collections():
    version_tuple = bpy.app.version
    return version_tuple[0] >= 4


def assign_bone_to_bone_collection(armature, armature_obj, bone, collection_name, collection_idx):
    if use_bone_collections():
        clothes_bone_collection = armature.collections.get(collection_name) if \
            armature.collections.get(collection_name) else armature.collections.new(collection_name)
        clothes_bone_collection.assign(bone)
    else:
        armature_obj.pose.bones[bone.name].bone.layers[collection_idx] = True
        armature_obj.pose.bones[bone.name].bone.layers[0] = False


def unassign_bone_from_bone_collection(armature, armature_obj, bone, collection_name, collection_idx_range):
    if use_bone_collections():
        clothes_bone_collection = armature.collections.get(collection_name) if \
            armature.collections.get(collection_name) else armature.collections.new(collection_name)
        clothes_bone_collection.unassign(bone)
    else:
        for i in range(collection_idx_range[0], collection_idx_range[1]):
            armature_obj.pose.bones[bone.name].bone.layers[i] = False


def assign_root_bone_to_bone_collection(armature, bone, collection_name, collection_idx):
    if use_bone_collections():
        root_bone_collection = armature.collections.get(collection_name) if \
            armature.collections.get(collection_name) else armature.collections.new(collection_name)
        if root_bone_collection:
            root_bone_collection.assign(bone)
    else:
        bpy.ops.pose.group_assign(type=6)
        for x in range(0, 28):
            bone.layers[x] = False
        bone.layers[collection_idx] = True
