# Author: michael-gh1, PaoloESAN
# Arknights: Endfield - Isaac Face Rig Integration

import os
import bpy
from bpy.types import Operator
from mathutils import Vector, Matrix

from setup_wizard.domain.game_types import GameType
from setup_wizard.setup_wizard_operator_base_classes import BasicSetupUIOperator


ENDFIELD_FACE_MAPPING = {
    # Eyebrows Left
    "browLf01Joint": {"master": "Eyebrow-Master.L", "deform": "brow_Inn_L"},
    "browLf02Joint": {"master": "Eyebrow-Master.L", "deform": "brow_Inn_L"},
    "browLf03Joint": {"master": "Eyebrow-Master.L", "deform": "brow_Mid_L"},
    "browLf04Joint": {"master": "Eyebrow-Master.L", "deform": "brow_Mid_L"},
    "browLf05Joint": {"master": "Eyebrow-Master.L", "deform": "brow_Out_L"},
    "browLineLf01Joint": {"master": "Eyebrow-Master.L", "deform": "eyebrow_Inn_L"},
    "browLineLf02Joint": {"master": "Eyebrow-Master.L", "deform": "eyebrow_Mid_L"},
    "browLineLf03Joint": {"master": "Eyebrow-Master.L", "deform": "eyebrow_Out_L"},

    # Eyebrows Right
    "browRt01Joint": {"master": "Eyebrow-Master.R", "deform": "brow_Inn_R"},
    "browRt02Joint": {"master": "Eyebrow-Master.R", "deform": "brow_Inn_R"},
    "browRt03Joint": {"master": "Eyebrow-Master.R", "deform": "brow_Mid_R"},
    "browRt04Joint": {"master": "Eyebrow-Master.R", "deform": "brow_Mid_R"},
    "browRt05Joint": {"master": "Eyebrow-Master.R", "deform": "brow_Out_R"},
    "browLineRt01Joint": {"master": "Eyebrow-Master.R", "deform": "eyebrow_Inn_R"},
    "browLineRt02Joint": {"master": "Eyebrow-Master.R", "deform": "eyebrow_Mid_R"},
    "browLineRt03Joint": {"master": "Eyebrow-Master.R", "deform": "eyebrow_Out_R"},

    # Eyes & Eyelids Left
    "eyeLf01Joint": {"master": "Eye-Master.L", "deform": "eyeconner_inn_L"},
    "eyeLf02Joint": {"master": "Eye-Master.L", "deform": "eyeup_inn_L"},
    "eyeLf03Joint": {"master": "Eye-Master.L", "deform": "eyeup_M_L"},
    "eyeLf04Joint": {"master": "Eye-Master.L", "deform": "eyeup_out_L"},
    "eyeLf05Joint": {"master": "Eye-Master.L", "deform": "eyeconner_out_L"},
    "eyeLf06Joint": {"master": "Eye-Master.L", "deform": "eyedn_out_L"},
    "eyeLf07Joint": {"master": "Eye-Master.L", "deform": "eyedn_M_L"},
    "eyeLf08Joint": {"master": "Eye-Master.L", "deform": "eyedn_inn_L"},

    # Eyes & Eyelids Right
    "eyeRt01Joint": {"master": "Eye-Master.R", "deform": "eyeconner_inn_R"},
    "eyeRt02Joint": {"master": "Eye-Master.R", "deform": "eyeup_inn_R"},
    "eyeRt03Joint": {"master": "Eye-Master.R", "deform": "eyeup_M_R"},
    "eyeRt04Joint": {"master": "Eye-Master.R", "deform": "eyeup_out_R"},
    "eyeRt05Joint": {"master": "Eye-Master.R", "deform": "eyeconner_out_R"},
    "eyeRt06Joint": {"master": "Eye-Master.R", "deform": "eyedn_out_R"},
    "eyeRt07Joint": {"master": "Eye-Master.R", "deform": "eyedn_M_R"},
    "eyeRt08Joint": {"master": "Eye-Master.R", "deform": "eyedn_inn_R"},

    # Mouth & Lips
    "lipMupJoint": {"mouth_chain": True, "deform": "lipUpper_M"},
    "lipMdnJoint": {"mouth_chain": True, "deform": "lipLower_M"},
    "lipLup1Joint": {"mouth_chain": True, "deform": "lipConner_L"},
    "lipLup2Joint": {"mouth_chain": True, "deform": "lipUpper_01_L"},
    "lipLup3Joint": {"mouth_chain": True, "deform": "lipUpper_00_L"},
    "lipLup4Joint": {"mouth_chain": True, "deform": "lipUpper_00_L"},
    "lipLdn1Joint": {"mouth_chain": True, "deform": "lipConner_L"},
    "lipLdn2Joint": {"mouth_chain": True, "deform": "lipLower_01_L"},
    "lipLdn3Joint": {"mouth_chain": True, "deform": "lipLower_00_L"},
    "lipLdn4Joint": {"mouth_chain": True, "deform": "lipLower_00_L"},
    "lipRup1Joint": {"mouth_chain": True, "deform": "lipConner_R"},
    "lipRup2Joint": {"mouth_chain": True, "deform": "lipUpper_01_R"},
    "lipRup3Joint": {"mouth_chain": True, "deform": "lipUpper_00_R"},
    "lipRup4Joint": {"mouth_chain": True, "deform": "lipUpper_00_R"},
    "lipRdn1Joint": {"mouth_chain": True, "deform": "lipConner_R"},
    "lipRdn2Joint": {"mouth_chain": True, "deform": "lipLower_01_R"},
    "lipRdn3Joint": {"mouth_chain": True, "deform": "lipLower_00_R"},
    "lipRdn4Joint": {"mouth_chain": True, "deform": "lipLower_00_R"},

    # Cheeks Left & Right
    "faceLfCheekOtJoint": {"mouth_master": True, "deform": "chhek_L"},
    "faceLfCheekOtUpJoint": {"mouth_master": True, "deform": "chhek_L"},
    "faceLfCheekOtDnJoint": {"mouth_master": True, "deform": "mouthUpper_03_L"},
    "faceLfCheekOtInJoint": {"mouth_master": True, "deform": "mouthUpper_01_L"},
    "faceRtCheekOtJoint": {"mouth_master": True, "deform": "chhek_R"},
    "faceRtCheekOtUpJoint": {"mouth_master": True, "deform": "chhek_R"},
    "faceRtCheekOtDnJoint": {"mouth_master": True, "deform": "mouthUpper_03_R"},
    "faceRtCheekOtInJoint": {"mouth_master": True, "deform": "mouthUpper_01_R"},

    # Jaw & Teeth
    "jawJoint": {"deform": "JawdnEnd_M"},
    "faceMdJawDnJoint": {"deform": "JawdnEnd_M"},
    "faceMdToothUpJoint": {"mouth_chain": True, "deform": "UpTeeth"},
    "faceMdToothDnJoint": {"mouth_chain": True, "deform": "DownTeeth"},
    "line_toothJoint": {"mouth_chain": True, "deform": "DownTeeth"},

    # Tongue
    "TongueMd01Joint": {"mouth_chain": True, "deform": "tongue_01"},
    "TongueMd02Joint": {"mouth_chain": True, "deform": "tongue_02"},
    "TongueMd03Joint": {"mouth_chain": True, "deform": "tongue_03"},
    "TongueMd04Joint": {"mouth_chain": True, "deform": "tongue_04"},

    # Nose
    "NoseMd01Joint": {"deform": "nosetip_M"},
}


def setup_endfield_isaac_face_rig(body_rig, context=None):
    """Sets up the Isaac Face Rig controls for Arknights: Endfield characters.
    
    Preserves original Endfield bone positions and geometry while binding
    face deformations to Isaac FaceRig control widgets.
    """
    if not body_rig or body_rig.type != 'ARMATURE':
        print("[AKE FACE RIG] Error: Invalid body armature provided.")
        return None

    if not context:
        context = bpy.context

    blend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'isaacfacerig.blend')
    if not os.path.exists(blend_path):
        print(f"[AKE FACE RIG] Error: File not found: {blend_path}")
        return None

    objects_before = set(bpy.data.objects)
    facerig_obj = None
    appended_coll = None

    # Check if isaac FaceRig already exists in the scene
    facerig_obj = bpy.data.objects.get("isaac FaceRig")
    if not facerig_obj:
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and any(k in obj.name.lower() for k in ['facerig', 'isaac']):
                facerig_obj = obj
                break

    # If not already in scene, append from isaacfacerig.blend
    if not facerig_obj:
        try:
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                if data_from.collections:
                    first_coll_name = data_from.collections[0]
                    data_to.collections = [first_coll_name]
                    print(f"[AKE FACE RIG] Loading collection from blend: '{first_coll_name}'")

            for collection in data_to.collections:
                if collection:
                    appended_coll = collection
                    if collection.name not in context.scene.collection.children:
                        context.scene.collection.children.link(collection)
        except Exception as err:
            print(f"[AKE FACE RIG] Library load error: {err}")

        new_objects = set(bpy.data.objects) - objects_before
        for obj in new_objects:
            if obj.type == 'ARMATURE':
                facerig_obj = obj
                break

        if not facerig_obj:
            facerig_obj = bpy.data.objects.get("isaac FaceRig")

    if not facerig_obj:
        print("[AKE FACE RIG] Error: Could not find or append 'isaac FaceRig' armature.")
        return None

    print(f"[AKE FACE RIG] Using FaceRig armature: '{facerig_obj.name}'")

    # Organize collections: FaceRig armature to character collection,
    # widget planes to per-character WGTS_<Char> nested inside it (Append-safe)
    target_armature_coll = body_rig.users_collection[0] if body_rig.users_collection else context.scene.collection
    char_name = target_armature_coll.name if target_armature_coll != context.scene.collection else (body_rig.name.replace("Rig", "") or "Character")
    wgts_name = f"WGTS_{char_name}"
    wgt_coll = bpy.data.collections.get(wgts_name)
    if not wgt_coll:
        wgt_coll = bpy.data.collections.new(wgts_name)
    if wgt_coll.name not in target_armature_coll.children:
        try:
            target_armature_coll.children.link(wgt_coll)
        except Exception:
            pass
    if wgt_coll.name in context.scene.collection.children:
        try:
            context.scene.collection.children.unlink(wgt_coll)
        except Exception:
            pass
    try:
        wgt_coll.hide_viewport = True
        wgt_coll.hide_select = True
        wgt_coll.hide_render = True
    except Exception:
        pass

    if facerig_obj and target_armature_coll:
        if facerig_obj.name not in target_armature_coll.objects:
            target_armature_coll.objects.link(facerig_obj)
        for coll in list(facerig_obj.users_collection):
            if coll != target_armature_coll:
                coll.objects.unlink(facerig_obj)

    plane_objs = [
        obj for obj in bpy.data.objects
        if obj.type == 'MESH' and ('Plane.' in obj.name or 'wgt' in obj.name.lower()) and obj != facerig_obj
    ]
    if appended_coll:
        plane_objs.extend([obj for obj in appended_coll.objects if obj != facerig_obj and obj not in plane_objs])

    for p_obj in plane_objs:
        if p_obj.name not in wgt_coll.objects:
            wgt_coll.objects.link(p_obj)
        for coll in list(p_obj.users_collection):
            if coll != wgt_coll:
                coll.objects.unlink(p_obj)

    # Clean up appended collection if necessary
    if appended_coll:
        try:
            for parent_coll in bpy.data.collections:
                if appended_coll.name in parent_coll.children:
                    parent_coll.children.unlink(appended_coll)
            if appended_coll.name in context.scene.collection.children:
                context.scene.collection.children.unlink(appended_coll)
            bpy.data.collections.remove(appended_coll, do_unlink=True)
            print(f"[AKE FACE RIG] Cleaned up temporary collection '{appended_coll.name}'")
        except Exception as c_err:
            print(f"[AKE FACE RIG] Collection cleanup notice: {c_err}")

    # Set display properties
    facerig_obj.show_in_front = True

    # Identify head bone on body rig
    body_head_bone_name = None
    for candidate in ["DEF-spine.006", "head", "Head", "Head_M", "Bip001_Head"]:
        if candidate in body_rig.data.bones:
            body_head_bone_name = candidate
            break
    if not body_head_bone_name:
        for b in body_rig.data.bones.keys():
            if "head" in b.lower() or "spine.006" in b.lower():
                body_head_bone_name = b
                break

    if not body_head_bone_name:
        print("[AKE FACE RIG] Error: Could not find head bone on body rig.")
        return None

    facerig_head_bone_name = "DEF-spine.006" if "DEF-spine.006" in facerig_obj.data.bones else facerig_obj.data.bones[0].name

    # Align FaceRig world matrix to body head bone
    try:
        body_head_matrix_world = body_rig.matrix_world @ body_rig.pose.bones[body_head_bone_name].matrix
        facerig_head_matrix_local = facerig_obj.pose.bones[facerig_head_bone_name].matrix
        facerig_obj.matrix_world = body_head_matrix_world @ facerig_head_matrix_local.inverted()
    except Exception as e:
        print(f"[AKE FACE RIG] Matrix alignment warning: {e}")

    context.view_layer.update()

    # Constrain FaceRig head bone to body head bone
    pbone_head = facerig_obj.pose.bones.get(facerig_head_bone_name)
    if pbone_head:
        c_head = None
        for c in pbone_head.constraints:
            if c.type in ['COPY_TRANSFORMS', 'CHILD_OF', 'COPY_LOCATION']:
                c_head = c
                break
        if not c_head:
            c_head = pbone_head.constraints.new('COPY_TRANSFORMS')
            c_head.name = "Copy Head Transforms"
        c_head.target = body_rig
        c_head.subtarget = body_head_bone_name

    context.view_layer.update()

    # Visually lower Isaac FaceRig widgets to align with Endfield facial features
    if not facerig_obj.get("ake_facerig_lowered", False):
        try:
            head_pbone = body_rig.pose.bones.get(body_head_bone_name)
            if head_pbone:
                head_tail_world = body_rig.matrix_world @ head_pbone.tail
                head_head_world = body_rig.matrix_world @ head_pbone.head
                world_head_up = (head_tail_world - head_head_world).normalized()
                world_down = -world_head_up
            else:
                world_down = Vector((0.0, 0.0, -1.0))

            armature_down = (facerig_obj.matrix_world.to_3x3().inverted() @ world_down).normalized()
            shift_distance = 0.0105  # Lower by ~1.05 cm to align widgets over Endfield features
            shift_vec = armature_down * shift_distance

            orig_active = context.view_layer.objects.active
            orig_mode = facerig_obj.mode if facerig_obj.mode in ('OBJECT', 'EDIT', 'POSE') else 'OBJECT'
            context.view_layer.objects.active = facerig_obj
            bpy.ops.object.mode_set(mode='EDIT')

            eb_jf = facerig_obj.data.edit_bones.get('joint_face')
            if eb_jf:
                bones_to_shift = set()
                def collect_descendants(eb):
                    bones_to_shift.add(eb)
                    for ch in eb.children:
                        collect_descendants(ch)
                collect_descendants(eb_jf)

                for eb in bones_to_shift:
                    eb.head += shift_vec
                    eb.tail += shift_vec

            bpy.ops.object.mode_set(mode=orig_mode)
            if orig_active:
                context.view_layer.objects.active = orig_active

            facerig_obj["ake_facerig_lowered"] = True
            print(f"[AKE FACE RIG] Lowered FaceRig widgets by {shift_distance*100:.1f} cm for Endfield facial alignment.")
        except Exception as shift_err:
            print(f"[AKE FACE RIG] Warning while lowering FaceRig: {shift_err}")

    context.view_layer.update()

    # Bind Endfield facial bones to Isaac FaceRig
    assigned_count = 0
    for bone_name, mapping in ENDFIELD_FACE_MAPPING.items():
        pb = body_rig.pose.bones.get(bone_name)
        if not pb:
            continue

        # Remove existing Isaac constraints to allow clean idempotent re-runs
        for c in list(pb.constraints):
            if c.name.startswith("Isaac_"):
                pb.constraints.remove(c)

        btype = mapping.get("type", "TRANSFORMS")

        if btype == "ROTATION":
            c = pb.constraints.new('COPY_ROTATION')
            c.name = "Isaac_CopyRotation"
            c.target = facerig_obj
            c.subtarget = mapping["deform"]
            c.owner_space = 'LOCAL'
            c.target_space = 'LOCAL_OWNER_ORIENT'
            assigned_count += 1

        elif btype == "SCALE":
            c = pb.constraints.new('COPY_SCALE')
            c.name = "Isaac_CopyScale"
            c.target = facerig_obj
            c.subtarget = mapping["deform"]
            c.owner_space = 'LOCAL'
            c.target_space = 'LOCAL'
            assigned_count += 1

        elif mapping.get("mouth_chain"):
            # Mouth chain: Mouth-Master -> Lip-Master -> Specific Deform Bone
            c1 = pb.constraints.new('COPY_TRANSFORMS')
            c1.name = "Isaac_MouthMaster"
            c1.target = facerig_obj
            c1.subtarget = "Mouth-Master"
            c1.owner_space = 'LOCAL'
            c1.target_space = 'LOCAL_OWNER_ORIENT'

            c2 = pb.constraints.new('COPY_TRANSFORMS')
            c2.name = "Isaac_LipMaster"
            c2.target = facerig_obj
            c2.subtarget = "Lip-Master"
            c2.owner_space = 'LOCAL'
            c2.target_space = 'LOCAL_OWNER_ORIENT'
            c2.mix_mode = 'AFTER'

            c3 = pb.constraints.new('COPY_TRANSFORMS')
            c3.name = f"Isaac_Deform_{mapping['deform']}"
            c3.target = facerig_obj
            c3.subtarget = mapping["deform"]
            c3.owner_space = 'LOCAL'
            c3.target_space = 'LOCAL_OWNER_ORIENT'
            c3.mix_mode = 'AFTER'
            assigned_count += 1

        elif mapping.get("mouth_master"):
            # Cheeks: Mouth-Master -> Specific Deform Bone
            c1 = pb.constraints.new('COPY_TRANSFORMS')
            c1.name = "Isaac_MouthMaster"
            c1.target = facerig_obj
            c1.subtarget = "Mouth-Master"
            c1.owner_space = 'LOCAL'
            c1.target_space = 'LOCAL_OWNER_ORIENT'

            c2 = pb.constraints.new('COPY_TRANSFORMS')
            c2.name = f"Isaac_Deform_{mapping['deform']}"
            c2.target = facerig_obj
            c2.subtarget = mapping["deform"]
            c2.owner_space = 'LOCAL'
            c2.target_space = 'LOCAL_OWNER_ORIENT'
            c2.mix_mode = 'AFTER'
            assigned_count += 1

        elif "master" in mapping:
            # Eyebrows / Eyelids: Master Bone -> Specific Deform Bone
            c1 = pb.constraints.new('COPY_TRANSFORMS')
            c1.name = f"Isaac_Master_{mapping['master']}"
            c1.target = facerig_obj
            c1.subtarget = mapping["master"]
            c1.owner_space = 'LOCAL'
            c1.target_space = 'LOCAL_OWNER_ORIENT'

            c2 = pb.constraints.new('COPY_TRANSFORMS')
            c2.name = f"Isaac_Deform_{mapping['deform']}"
            c2.target = facerig_obj
            c2.subtarget = mapping["deform"]
            c2.owner_space = 'LOCAL'
            c2.target_space = 'LOCAL_OWNER_ORIENT'
            c2.mix_mode = 'AFTER'
            assigned_count += 1

        else:
            # Jaw, Nose, etc.
            c = pb.constraints.new('COPY_TRANSFORMS')
            c.name = f"Isaac_Deform_{mapping['deform']}"
            c.target = facerig_obj
            c.subtarget = mapping["deform"]
            c.owner_space = 'LOCAL'
            c.target_space = 'LOCAL_OWNER_ORIENT'
            assigned_count += 1

    # Direct binding for eye.L and eye.R (Eye Tracking movement and Eye Scale)
    for side in ("L", "R"):
        eye_name = f"eye.{side}"
        pb_eye = body_rig.pose.bones.get(eye_name) or body_rig.pose.bones.get(f"DEF-{eye_name}")
        if pb_eye:
            for c in list(pb_eye.constraints):
                if c.name.startswith("Isaac_"):
                    pb_eye.constraints.remove(c)

            # 1. Eye Rotation (looking around): Rotates exactly with Isaac's eye_L / eye_R
            c_rot = pb_eye.constraints.new('COPY_ROTATION')
            c_rot.name = f"Isaac_EyeRot_{side}"
            c_rot.target = facerig_obj
            c_rot.subtarget = f"eye_{side}"
            c_rot.owner_space = 'LOCAL'
            c_rot.target_space = 'LOCAL_OWNER_ORIENT'

            # 2. Eye Movement (translation): Shifts eye over the face plane on X/Z
            c_loc = pb_eye.constraints.new('COPY_LOCATION')
            c_loc.name = f"Isaac_EyeLoc_{side}"
            c_loc.target = facerig_obj
            c_loc.subtarget = "Eye-Track-Master"
            c_loc.owner_space = 'LOCAL'
            c_loc.target_space = 'LOCAL'
            c_loc.use_offset = True
            c_loc.use_y = False  # Keep depth locked so eyes never pop out or sink
            c_loc.influence = 0.3  # Natural subtle translation accompanying the rotation

            # 3. Eye Scale: Scale control for iris/eye size
            c_scale = pb_eye.constraints.new('COPY_SCALE')
            c_scale.name = f"Isaac_EyeScale_{side}"
            c_scale.target = facerig_obj
            c_scale.subtarget = f"Eye-Scale-Control.{side}"
            c_scale.owner_space = 'LOCAL'
            c_scale.target_space = 'LOCAL'

            assigned_count += 3

    # Hide the "Face" bone collection on the body rig as requested
    if hasattr(body_rig.data, "collections"):
        face_coll = body_rig.data.collections.get("Face")
        if face_coll:
            face_coll.is_visible = False
            print("[AKE FACE RIG] Hidden 'Face' bone collection on body rig.")

    print(f"[AKE FACE RIG] Successfully constrained {assigned_count} Endfield face bones to Isaac FaceRig!")
    context.view_layer.update()
    return facerig_obj


class AKE_OT_SetUpIsaacFaceRig(Operator, BasicSetupUIOperator):
    """Sets Up Isaac Face Rig for Arknights: Endfield Character"""
    bl_idname = "arknights_endfield.setup_face_rig"
    bl_label = "Arknights: Endfield: Set Up Isaac Face Rig"

    def execute(self, context):
        from setup_wizard.character_rig_setup.rig_ui_utils import find_target_armature
        armature = find_target_armature(context)
        if not armature:
            self.report({'ERROR'}, 'No character armature found. Please select or rig a character first.')
            return {'CANCELLED'}

        facerig = setup_endfield_isaac_face_rig(armature, context)
        if not facerig:
            self.report({'ERROR'}, 'Failed to set up Isaac Face Rig.')
            return {'CANCELLED'}

        self.report({'INFO'}, 'Successfully set up Isaac Face Rig for Arknights: Endfield character!')
        return {'FINISHED'}
