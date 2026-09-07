# Authors: enthralpy, Llama.jpg
# Setup Wizard Integration by michael-gh1

import bpy
import os
from mathutils import Color, Vector
from math import pi
import addon_utils   
import re             

from setup_wizard.geometry_nodes_setup.lighting_panel_names import LightingPanelNames
from setup_wizard.character_rig_setup.rig_ui_utils import (
    extract_clean_character_name,
    setup_standard_bone_collections,
    distribute_standard_rig_bones,
    modify_and_run_rig_ui_script,
)


def rig_character(
        file_path,
        lighting_panel_version, 
        disallow_arm_ik_stretch, 
        disallow_leg_ik_stretch,
        use_arm_ik_poles,
        use_leg_ik_poles,
        add_child_of_constraints,
        use_head_tracker,
        meshes_joined=False):
    
    # Rig log: collects warnings to display in Blender's Text Editor as 'RIG_LOG'
    _rig_log = []

    # Firstly, let's make a flag to identify the blender version.
    # Use bpy.app.version (tuple of ints) to properly detect Blender 4.0+
    # bone.layers was removed in Blender 4.0, so this applies to 4.x, 5.x, etc.
    is_version_4 = bpy.app.version[0] >= 4
               
    head_bone_arm_target = bpy.context.active_object

    # Blender 5.0 compatibility: active_object can be None after certain operations
    if head_bone_arm_target is None:
        # Try to find the armature from selected objects first
        armatures = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
        if not armatures:
            # Fallback: find any non-rigged armature in the scene
            armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE' and 'Rig' not in obj.name and obj.name != 'metarig']
        if not armatures:
            # Last resort: any armature
            armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
        if armatures:
            head_bone_arm_target = armatures[0]
            bpy.context.view_layer.objects.active = head_bone_arm_target
            head_bone_arm_target.select_set(True)
        else:
            raise RuntimeError("No armature found. Please select the character's armature and try again.")

    temp_armature = head_bone_arm_target.data

    bpy.ops.object.mode_set(mode='EDIT')

    # Check if toe bones exist
    toe_bones_exist = True
    if "Bip001 L Toe0" not in temp_armature.edit_bones:
        toe_bones_exist = False

    # Check if eyes exist:
    possible_eye_L = ["+EyeBone L A02", "+EyeBone L A01", "eye.L", "EYE_L", "Eye_L", "Skn_L_Eye", "Bdy_L_Eye", "Bdy_L_Eye_Skin", "Skn_L_Pupil", "Skn_Bn_Eye_L", "Skn_L_Eye_New", "Bn_Eye_L", "PT_L_Eye"]
    possible_eye_R = ["+EyeBone R A02", "+EyeBone R A01", "eye.R", "EYE_R", "Eye_R", "Skn_R_Eye", "Bdy_R_Eye", "Bdy_R_Eye_Skin", "Skn_R_Pupil", "Skn_Bn_Eye_R", "Skn_R_Eye_New", "Bn_Eye_R", "PT_R_Eye"]
    
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

    no_eyes = False    
    if not left_eye_exists and not right_eye_exists:
          no_eyes = True
        
    # Hoyo models have inconsistent head bone shapes. I'm correcting them to my standard. (This stabilizes the head track bone)
    # My logic: Line up the head bone's tail's X & Y to the head bone's head (so that it's straight up), and use the eye bone's head's Z as the height. - Llama    
    possible_head = ["Bip001 Head", "Bip001-Head", "Bip001_Head", "Head", "head", "DEF-head", "DEF-spine.006"]
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
            if left_eye_exists:
                eye_bone_head = temp_armature.edit_bones[left_eye_bone_name]
            elif right_eye_exists:
                eye_bone_head = temp_armature.edit_bones[right_eye_bone_name]
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
        
    left_eye_2 = []
    left_eye_1 = []
    right_eye_2 = []
    right_eye_1 = []

    if left_eye_exists:
        left_eye_2.extend(temp_armature.edit_bones[left_eye_bone_name].head[:3])
        left_eye_1_name = "+EyeBone L A01" if "+EyeBone L A01" in temp_armature.edit_bones else left_eye_bone_name
        left_eye_1.extend(temp_armature.edit_bones[left_eye_1_name].head[:3])
    if right_eye_exists:
        right_eye_2.extend(temp_armature.edit_bones[right_eye_bone_name].head[:3])
        right_eye_1_name = "+EyeBone R A01" if "+EyeBone R A01" in temp_armature.edit_bones else right_eye_bone_name
        right_eye_1.extend(temp_armature.edit_bones[right_eye_1_name].head[:3])  
            
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # THANK YOU: https://blenderartists.org/t/how-to-bpy-ops-transform-resize-in-edit-mode-using-pivot/560381/2
    def get_override(area_type, region_type):
        for area in bpy.context.screen.areas: 
            if area.type == area_type:             
                for region in area.regions:                 
                    if region.type == region_type:                    
                        override = {'area': area, 'region': region} 
                        return override
        #error message if the area or region wasn't found
        raise RuntimeError("Wasn't able to find", region_type," in area ", area_type, " Make sure it's open while executing script.")

    #we need to override the context of our operator    
    override = get_override( 'VIEW_3D', 'WINDOW' )
      
    # Function to create shape keys that works with 2 elementsa        
    def create_shape_key2(obj_get, is_basis, shape_name, transform_pivot, vertex_groups_to_parse, transform_type, transformation_1, transformation_2=0, use_eye_1=False):
        bpy.context.view_layer.objects.active = head_bone_arm_target
        bpy.ops.object.mode_set(mode='EDIT')
        if use_eye_1:
            if " R " in vertex_groups_to_parse[0]:
                if right_eye_exists:
                    bpy.context.scene.cursor.location = (right_eye_1[0],right_eye_1[1],right_eye_1[2])
            elif " L " in vertex_groups_to_parse[0]:
                if left_eye_exists:
                    bpy.context.scene.cursor.location = (left_eye_1[0],left_eye_1[1],left_eye_1[2])
        else:
            if " R " in vertex_groups_to_parse[0]:
                if right_eye_exists:
                    bpy.context.scene.cursor.location = (right_eye_2[0],right_eye_2[1],right_eye_2[2])
            elif " L " in vertex_groups_to_parse[0]:
                if left_eye_exists:
                    bpy.context.scene.cursor.location = (left_eye_2[0],left_eye_2[1],left_eye_2[2])
                        
        # AFTER MOVING 3D CURSOR
        this_obj = bpy.data.objects.get(obj_get)
        bpy.context.view_layer.objects.active = this_obj
        
        if is_basis:
            this_obj.shape_key_add(name='Basis')
            
        this_obj.shape_key_add(from_mix=False)   
        sk = this_obj.data.shape_keys.key_blocks[-1]
        sk.name = shape_name
        sk.value = 1
        shape_index = this_obj.data.shape_keys.key_blocks.keys().index(shape_name)
        bpy.context.object.active_shape_key_index = shape_index
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.transform_pivot_point = "CURSOR" 
        
        try:
            bpy.ops.object.vertex_group_set_active(group=vertex_groups_to_parse[0])
            bpy.ops.object.vertex_group_select()
            
            if transform_type == "RESIZE":
                if not is_version_4:
                    bpy.ops.transform.resize(override, value=(transformation_1), orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.object.vertex_group_deselect()
                else:
                    bpy.ops.transform.resize(value=(transformation_1), orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.object.vertex_group_deselect()
            elif transform_type == "TRANSLATE":
                if not is_version_4:
                    bpy.ops.transform.translate(override, value=transformation_1, orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.transform.resize(override, value=transformation_2)
                    bpy.ops.object.vertex_group_deselect()
                else:
                    bpy.ops.transform.translate(value=transformation_1, orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.transform.resize(override, value=transformation_2)
                    bpy.ops.object.vertex_group_deselect()                

        except:
            pass
        
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # REPEAT FOR SECOND BONE!
        
        bpy.context.view_layer.objects.active = head_bone_arm_target
        bpy.ops.object.mode_set(mode='EDIT')
        if use_eye_1:
            if " R " in vertex_groups_to_parse[1]:
                if right_eye_exists:
                    bpy.context.scene.cursor.location = (right_eye_1[0],right_eye_1[1],right_eye_1[2])
            elif " L " in vertex_groups_to_parse[1]:
                if left_eye_exists:
                    bpy.context.scene.cursor.location = (left_eye_1[0],left_eye_1[1],left_eye_1[2])
        else:
            if " R " in vertex_groups_to_parse[1]:
                if right_eye_exists:
                    bpy.context.scene.cursor.location = (right_eye_2[0],right_eye_2[1],right_eye_2[2])
            elif " L " in vertex_groups_to_parse[1]:
                if left_eye_exists:
                    bpy.context.scene.cursor.location = (left_eye_2[0],left_eye_2[1],left_eye_2[2])
                        
        # AFTER MOVING 3D CURSOR
        this_obj = bpy.data.objects.get(obj_get)
        bpy.context.view_layer.objects.active = this_obj
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT') 
        
        try:
            bpy.ops.object.vertex_group_set_active(group=vertex_groups_to_parse[1])
            bpy.ops.object.vertex_group_select()
            
            if transform_type == "RESIZE":
                if not is_version_4:
                    bpy.ops.transform.resize(override, value=(transformation_1), orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.object.vertex_group_deselect()
                else:
                    bpy.ops.transform.resize(value=(transformation_1), orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.object.vertex_group_deselect()                
            elif transform_type == "TRANSLATE":
                if not is_version_4:
                    bpy.ops.transform.translate(override, value=transformation_1, orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.transform.resize(override, value=transformation_2)
                    bpy.ops.object.vertex_group_deselect()
                else:
                    bpy.ops.transform.translate(value=transformation_1, orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
                    bpy.ops.transform.resize(override, value=transformation_2)
                    bpy.ops.object.vertex_group_deselect()                
        except:
            pass
        
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # DONE
        sk.value = 0.0
        bpy.context.scene.cursor.location = (0.0,0.0,0.0)
 
    
    try:
        # Bring back EyeStar
        bpy.data.objects["EyeStar"].hide_set(False)
        bpy.data.objects["EyeStar"].hide_viewport = False
        bpy.data.objects["EyeStar"].hide_render = False

        # Shape key to enable EyeStar growth/shrinkage
        create_shape_key2("EyeStar", True, "EyeStar", "CURSOR", ["+EyeBone R A02","+EyeBone L A02"], "RESIZE", (0,0,0))
    except:
        pass

    bpy.context.tool_settings.transform_pivot_point = "MEDIAN_POINT"

    bpy.context.view_layer.objects.active = head_bone_arm_target
    bpy.ops.object.mode_set(mode='EDIT')

    if not toe_bones_exist:
        r_foot_bone = temp_armature.edit_bones.get("Bip001 R Foot") or temp_armature.edit_bones.get("Bip001-R-Foot") or temp_armature.edit_bones.get("Foot.R") or temp_armature.edit_bones.get("foot.R")
        if r_foot_bone:
            r_foot_bone.tail = (-0.040187,-0.078244,0.005803) # X, Y, Z
            r_foot_bone.roll = 1.5708
        
        l_foot_bone = temp_armature.edit_bones.get("Bip001 L Foot") or temp_armature.edit_bones.get("Bip001-L-Foot") or temp_armature.edit_bones.get("Foot.L") or temp_armature.edit_bones.get("foot.L")
        if l_foot_bone:
            l_foot_bone.tail = (0.040187,-0.078244,0.005803)
            l_foot_bone.roll =  1.5708

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = head_bone_arm_target

    # Let's let the RigUI script that poke made execute.

    context = bpy.context
    obj = context.object
    if obj.name[-4:] == ".001":
         obj.name = obj.name[:-4]
    print("New Run\n\n")
    ## Rename all bones in selected armature to ORG
    original_name = obj.name

    kachina = False  # maybe change to 'mittens' if more mitten-wielding chars are created lol
    if "kachina" in obj.name.lower():
        kachina = True
    abadidea = {
        'Bip001 Pelvis': 'spine',
        'Bip001 L Thigh': 'thigh.L',
        'Bip001 L Calf': 'shin.L',
        'Bip001 L Foot': 'foot.L',
        'Bip001 L Toe0': 'toe.L',
        'Bip001 R Thigh': 'thigh.R',
        'Bip001 R Calf': 'shin.R',
        'Bip001 R Foot': 'foot.R',
        'Bip001 R Toe0': 'toe.R',
        'Bip001 Spine': 'spine.001',
        'Bip001 Spine1': 'spine.002',
        'Bip001 Spine2': 'spine.003',
        'Bip001 L Clavicle': 'shoulder.L',
        'Bip001 L UpperArm': 'upper_arm.L',
        'Bip001 L Forearm': 'forearm.L',
        'Bip001 L Hand': 'hand.L',
        'Bip001 L Finger0': 'thumb.01.L',
        'DMZ L 01': 'thumb.01.L',  ##WHERE DO THESE SIX COME FROM LMAO
        'DMZ L 02': 'thumb.02.L',
        'DMZ L 03': 'thumb.03.L',
        'DMZ R 01': 'thumb.01.R',
        'DMZ R 02': 'thumb.02.R',
        'DMZ R 03': 'thumb.03.R',    
        'Bip001 L Finger01': 'thumb.02.L',
        'Bip001 L Finger02': 'thumb.03.L',
        'Bip001 L Finger1': 'f_index.01.L',
        'Bip001 L Finger11': 'f_index.02.L',
        'Bip001 L Finger12': 'f_index.03.L',
        'Bip001 L Finger2': 'f_middle.01.L',
        'Bip001 L Finger21': 'f_middle.02.L',
        'Bip001 L Finger22': 'f_middle.03.L',
        'Bip001 L Finger3': 'f_ring.01.L',
        'Bip001 L Finger31': 'f_ring.02.L',
        'Bip001 L Finger32': 'f_ring.03.L',
        'Bip001 L Finger4': 'f_pinky.01.L',
        'Bip001 L Finger41': 'f_pinky.02.L',
        'Bip001 L Finger42': 'f_pinky.03.L',
        'Bip001 Neck': 'spine.004', #YO
        'Bip001 Head': 'spine.006', #RUHROH
        'Bip001 R Clavicle': 'shoulder.R',
        'Bip001 R UpperArm': 'upper_arm.R',
        'Bip001 R Forearm': 'forearm.R',
        'Bip001 R Hand': 'hand.R',
        'Bip001 R Finger0': 'thumb.01.R',
        'Bip001 R Finger01': 'thumb.02.R',
        'Bip001 R Finger02': 'thumb.03.R',
        'Bip001 R Finger1': 'f_index.01.R',
        'Bip001 R Finger11': 'f_index.02.R',
        'Bip001 R Finger12': 'f_index.03.R',
        'Bip001 R Finger2': 'f_middle.01.R',
        'Bip001 R Finger21': 'f_middle.02.R',
        'Bip001 R Finger22': 'f_middle.03.R',
        'Bip001 R Finger3': 'f_ring.01.R',
        'Bip001 R Finger31': 'f_ring.02.R',
        'Bip001 R Finger32': 'f_ring.03.R',
        'Bip001 R Finger4': 'f_pinky.01.R',
        'Bip001 R Finger41': 'f_pinky.02.R',
        'Bip001 R Finger42': 'f_pinky.03.R',
        '+EyeBone R A01': 'eye.R',
        '+EyeBone L A01': 'eye.L', 
        'EYE_R': 'eye.R',
        'EYE_L': 'eye.L',   
        'Eye_R': 'eye.R',
        'Eye_L': 'eye.L',   
        'Skn_R_Eye': 'eye.R',   
        'Skn_L_Eye': 'eye.L',   
        'Bdy_R_Eye': 'eye.R',
        'Bdy_L_Eye': 'eye.L',   
        'Bdy_R_Eye_Skin': 'eye.R',
        'Bdy_L_Eye_Skin': 'eye.L',   
        'Skn_R_Pupil': 'eye.R',
        'Skn_L_Pupil': 'eye.L',   
        'Skn_Bn_Eye_R': 'eye.R',
        'Skn_Bn_Eye_L': 'eye.L',   
        'Skn_R_Eye_New': 'eye.R',
        'Skn_L_Eye_New': 'eye.L',
        'Bn_Eye_R': 'eye.R',
        'Bn_Eye_L': 'eye.L',
        'PT_L_Eye': 'eye.L',
        'PT_R_Eye': 'eye.R',
        'breast.L': 'breast.L',
        'breast.R': 'breast.R',
        'breast.L.001': 'breast.L.001',
        'breast.R.001': 'breast.R.001',
        'breast.L.002': 'breast.L.002',
        'breast.R.002': 'breast.R.002',
        '+Breast L A01': 'breast.L',
        '+Breast R A01': 'breast.R',
        'Skn_L_Chest': 'breast.L',
        'Skn_R_Chest': 'breast.R',
        'Skn_L_Chest_01': 'breast.L.001',
        'Skn_R_Chest_01': 'breast.R.001',
        'Skn_L_Chest1': 'breast.L.001',
        'Skn_R_Chest1': 'breast.R.001',
        'Skn_L_Chest_02': 'breast.L.002',
        'Skn_R_Chest_02': 'breast.R.002',
        'Skn_Bn_Chest_L': 'breast.L',
        'Skn_Bn_Chest_R': 'breast.R',
        'Bn_L_Chest': 'breast.L',
        'Bn_R_Chest': 'breast.R',
        'Bdy_L_Chest': 'breast.L',
        'Bdy_R_Chest': 'breast.R',
        'Chest_L': 'breast.L',
        'Chest_R': 'breast.R',
    }

    # Dynamically detect any leftover chest/breast/breath bones for breast.L and breast.R mapping
    for pb in obj.pose.bones:
        p_name = pb.name
        if p_name.startswith("breast.") or p_name.startswith("breast_") or p_name.startswith("DEF-breast"):
            continue
        p_low = p_name.lower()
        if ("chest" in p_low or "breast" in p_low or "breath" in p_low or "bust" in p_low) and not p_name.startswith("DEF-") and not p_name.startswith("ORG-") and not p_name.startswith("MCH-"):
            if ("_l" in p_low or ".l" in p_low or "l_" in p_low or "left" in p_low) and p_name not in abadidea:
                if "001" in p_name or "_01" in p_name or "1" in p_name:
                    abadidea[p_name] = 'breast.L.001'
                elif "002" in p_name or "_02" in p_name or "2" in p_name:
                    abadidea[p_name] = 'breast.L.002'
                else:
                    abadidea[p_name] = 'breast.L'
            elif ("_r" in p_low or ".r" in p_low or "r_" in p_low or "right" in p_low) and p_name not in abadidea:
                if "001" in p_name or "_01" in p_name or "1" in p_name:
                    abadidea[p_name] = 'breast.R.001'
                elif "002" in p_name or "_02" in p_name or "2" in p_name:
                    abadidea[p_name] = 'breast.R.002'
                else:
                    abadidea[p_name] = 'breast.R'
    if kachina:
        # Only add Kachina thumb/fingers if it's Kachina
        # There is the potential to clash and have duplicate bone names with other characters (like Wriotheseley)
        abadidea = abadidea | {
            '+ThumbS L A01': 'thumb.01.L',
            '+ThumbS L A02': 'thumb.02.L',
            '+ThumbS R A01': 'thumb.01.R',
            '+ThumbS R A02': 'thumb.02.R',
            '+GlovesS L A01': 'f_middle.01.L',
            '+GlovesS L A02': 'f_middle.02.L',
            '+GlovesS R A01': 'f_middle.01.R',
            '+GlovesS R A02': 'f_middle.02.R',
        }

    if not toe_bones_exist:
        del abadidea['Bip001 L Toe0']
        del abadidea['Bip001 R Toe0']

    bpy.context.view_layer.objects.active = head_bone_arm_target
    head_bone_arm_target.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    armature = head_bone_arm_target.data

    if kachina:
        obj.data.edit_bones.remove(obj.data.edit_bones["Bip001 L Finger2"])
        obj.data.edit_bones.remove(obj.data.edit_bones["Bip001 L Finger0"])
        obj.data.edit_bones.remove(obj.data.edit_bones["Bip001 R Finger2"])
        obj.data.edit_bones.remove(obj.data.edit_bones["Bip001 R Finger0"])

    bpy.ops.armature.select_all(action='DESELECT')
    def select_bone(bone):
        bone.select = True
        bone.select_head = True
        bone.select_tail = True
        
    # Disconnect the eyes because it'll throw an error if I don't, disconnect the spines so the hip wiggle bone in the rigify rig works properly
    try:
        select_bone(armature.edit_bones["+EyeBone L A02"])
        select_bone(armature.edit_bones["+EyeBone R A02"])
    except:
        pass
    select_bone(armature.edit_bones["Bip001 Spine"])
    select_bone(armature.edit_bones["Bip001 Spine1"])
    select_bone(armature.edit_bones["Bip001 Spine2"])
    bpy.ops.armature.parent_clear(type='DISCONNECT')
    bpy.ops.armature.select_all(action='DESELECT')

    try:
        select_bone(armature.edit_bones["+Breast R A02"])
        select_bone(armature.edit_bones["+Breast L A02"])
        bpy.ops.armature.parent_clear(type='DISCONNECT')
        bpy.ops.armature.select_all(action='DESELECT')
    except:
        pass

    bones_list = obj.pose.bones
    for bone in bones_list:
        if bone.name in abadidea:
            bone.name = abadidea[bone.name]
    
    # Set shoulder rolls so local Z-axis points UP so crescent widgets lie flat on shoulders
    armature.edit_bones["shoulder.L"].align_roll(Vector((0, 0, 1)))
    armature.edit_bones["shoulder.R"].align_roll(Vector((0, 0, 1)))

    for bone in list(armature.edit_bones):
        ## Not sure why this bone exist but it's gotta go lmao                                                      
        if bone.name == "Bip001": 
            for childbone in bone.children:
                if childbone.name != "spine":
                    armature.edit_bones[childbone.name].parent = armature.edit_bones['spine'] 
            armature.edit_bones.remove(bone)
            for obj_acc in bpy.data.objects:
                if getattr(obj_acc, "parent_bone", None) == "Bip001":
                    obj_acc.parent_bone = "spine"
        elif ".L" not in bone.name and ".R" not in bone.name and "f_" not in bone.name and "thumb" not in bone.name:
            armature.edit_bones[bone.name].roll = 0

            
    ## Fixes the weirdass pelvis/spine bone.  Sets the spine's head and tail X to 0.  
    def realign(bone):
        bone.head.x = 0
        bone.tail.x = 0
    realign(armature.edit_bones['spine'])
    realign(armature.edit_bones['spine.006'])


    ## Attaches the feet to the toes and the upperarms to lowerarms
    def attachfeets(foot, toe):
        armature.edit_bones[foot].tail.x = armature.edit_bones[toe].head.x
        armature.edit_bones[foot].tail.y = armature.edit_bones[toe].head.y
        armature.edit_bones[foot].tail.z = armature.edit_bones[toe].head.z

    if toe_bones_exist:
        attachfeets('foot.L', 'toe.L')
        attachfeets('foot.R', 'toe.R')
        
    attachfeets('upper_arm.L', 'forearm.L')
    attachfeets('upper_arm.R', 'forearm.R')
    attachfeets('thigh.L', 'shin.L')
    attachfeets('thigh.R', 'shin.R') 
    attachfeets('forearm.L', 'hand.L')
    attachfeets('forearm.R', 'hand.R')
    attachfeets('shoulder.L', 'upper_arm.L')
    attachfeets('shoulder.R', 'upper_arm.R')
    attachfeets('spine', 'spine.001')
    attachfeets('spine.001', 'spine.002')
    attachfeets('spine.002', 'spine.003')
    attachfeets('spine.003', 'spine.004')
    attachfeets('spine.004', 'spine.006')

    ## Points toe bones in correct direction
    if toe_bones_exist:
        armature.edit_bones['toe.L'].tail.z = 0
        armature.edit_bones['toe.L'].tail.y -= 0.05

        armature.edit_bones['toe.R'].tail.z = 0
        armature.edit_bones['toe.R'].tail.y -= 0.05
            
    bpy.ops.armature.select_all(action='DESELECT')
    try:
        select_bone(armature.edit_bones["breast.L"])
        bpy.ops.armature.symmetrize()
        bpy.ops.armature.select_all(action='DESELECT')

    except Exception:
        pass

    try:
        armature.edit_bones["eye.L"].name = "DEF-eye.L"
        armature.edit_bones["eye.R"].name = "DEF-eye.R"
    except:
        pass

    bpy.ops.object.mode_set(mode='POSE')

    if hasattr(bpy.types, 'Action') and not hasattr(bpy.types.Action, 'fcurves'):
        try:
            bpy.types.Action.fcurves = property(lambda self: getattr(self, 'curves', []))
        except Exception:
            pass

    try:
        bpy.ops.object.expykit_convert_bone_names(src_preset='Rigify_Metarig.py', trg_preset='Rigify_Deform.py')
    except Exception as ex:
        print(f"Notice: Expykit convert_bone_names handled: {ex}")

    try:
        bpy.ops.object.expykit_extract_metarig(rig_preset='Rigify_Metarig.py', assign_metarig=True)
    except Exception as ex:
        print(f"Notice: Expykit extract_metarig handled: {ex}")

    # Poke's code to turn on the finger's IK.
    if not kachina:
        fuckyou = ["thumb.01", "f_index.01", "f_middle.01", "f_ring.01", "f_pinky.01"]
        for side in [".L", ".R"]:
            for fucks in fuckyou:
                bpy.context.object.pose.bones[fucks + side].rigify_parameters.make_extra_ik_control = True

    ## Fixes the tiddy bones.  Expykit, why did you neglect them

    metarm = bpy.data.objects["metarig"].data
    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.data.objects[obj.name].data

    ## Left side first, right side's xyz is same as left, but x is negative
    def getboob(bone, tip):
        if tip == "head":
            return armature.edit_bones[bone].head.x, armature.edit_bones[bone].head.y, armature.edit_bones[bone].head.z
        else:
            return armature.edit_bones[bone].tail.x, armature.edit_bones[bone].tail.y, armature.edit_bones[bone].tail.z
            
        
    try:
        boob_bone_L = None
        for candidate in ["breast.L", "breast.L.001", "DEF-breast.L", "Skn_L_Chest", "Skn_L_Chest_01", "+Breast L A01"]:
            if candidate in armature.edit_bones:
                boob_bone_L = candidate
                break

        boob_bone_R = None
        for candidate in ["breast.R", "breast.R.001", "DEF-breast.R", "Skn_R_Chest", "Skn_R_Chest_01", "+Breast R A01"]:
            if candidate in armature.edit_bones:
                boob_bone_R = candidate
                break

        def fixboob(bone, xh, yh, zh, xt, yt, zt):
            bone.head.x = xh
            bone.head.y = yh
            bone.head.z = zh
            bone.tail.x = xt
            bone.tail.y = yt
            bone.tail.z = zt

        if boob_bone_L and "breast.L" in metarm.edit_bones:
            xh, yh, zh = getboob(boob_bone_L, "head")
            xt, yt, zt = getboob(boob_bone_L, "tail")

            # Center circle controls right on front volume of breasts
            c_xh = xh * 0.70
            c_xt = xt * 0.70

            boobL = metarm.edit_bones["breast.L"]
            fixboob(boobL, c_xh, yh, zh, c_xt, yt, zt)

            if "breast.R" in metarm.edit_bones:
                boobR = metarm.edit_bones["breast.R"]
                if boob_bone_R:
                    r_xh, r_yh, r_zh = getboob(boob_bone_R, "head")
                    r_xt, r_yt, r_zt = getboob(boob_bone_R, "tail")
                    c_r_xh = r_xh * 0.70
                    c_r_xt = r_xt * 0.70
                    fixboob(boobR, c_r_xh, r_yh, r_zh, c_r_xt, r_yt, r_zt)
                else:
                    fixboob(boobR, -c_xh, yh, zh, -c_xt, yt, zt)

                boobL.roll = armature.edit_bones[boob_bone_L].roll
                boobR.roll = -boobL.roll
        elif "breast.L" in metarm.edit_bones:
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
        


    # Fixes the finger rolls
    bpy.ops.object.mode_set(mode='OBJECT')
    metapose = bpy.data.objects['metarig'].pose
    if kachina:
        for bone_name in ['f_index', 'f_middle', 'f_ring', 'f_pinky']:
            metapose.bones[f"{bone_name}.01.L"].rigify_parameters.primary_rotation_axis = '-X'
            metapose.bones[f"{bone_name}.01.R"].rigify_parameters.primary_rotation_axis = '-X'
    else:
        for bone_name in ['f_index', 'f_middle', 'f_ring', 'f_pinky']:
            metapose.bones[f"{bone_name}.01.L"].rigify_parameters.primary_rotation_axis = 'X'
            metapose.bones[f"{bone_name}.01.R"].rigify_parameters.primary_rotation_axis = 'X'
                                          

    ## This part corrects metarm finger rolls
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    armature = obj.data

    for o in bpy.data.objects:
        # Check for given object names
        if o.name in ("metarig", armature.name):
            o.select_set(True)


    bpy.ops.object.mode_set(mode='EDIT')
    # Align hand.L and hand.R metarig bones straight along forearm vector so hand_ik widget is centered on wrist
    for side in [".L", ".R"]:
        forearm_eb = metarm.edit_bones.get("forearm" + side)
        hand_eb = metarm.edit_bones.get("hand" + side)
        if forearm_eb and hand_eb:
            arm_vec = (forearm_eb.tail - forearm_eb.head).normalized()
            hand_eb.tail = hand_eb.head + arm_vec * 0.05
            hand_eb.roll = forearm_eb.roll

    for side in [".L", ".R"]:
        hand_mb = metarm.edit_bones.get("hand" + side)
        hand_ab = armature.edit_bones.get("hand" + side) or armature.edit_bones.get("DEF-hand" + side)

        # 1. Determine index finger's plane normal as reference for all fingers
        index_chain = []
        for idx in ["01", "02", "03"]:
            b_meta = metarm.edit_bones.get(f"f_index.{idx}{side}")
            if b_meta:
                index_chain.append(b_meta)

        index_plane_normal = None
        if len(index_chain) >= 2:
            dir1 = (index_chain[0].tail - index_chain[0].head).normalized()
            dir2 = (index_chain[1].tail - index_chain[1].head).normalized()
            cross_vec = dir1.cross(dir2)
            if cross_vec.length > 0.0001:
                index_plane_normal = cross_vec.normalized()

        if not index_plane_normal and hand_mb:
            index_plane_normal = hand_mb.matrix.col[2].normalized()
        elif not index_plane_normal and hand_ab:
            index_plane_normal = hand_ab.matrix.col[2].normalized()

        if not index_plane_normal:
            continue

        # 2. Align f_index, f_middle, f_ring, f_pinky directly to index_plane_normal
        for fname in ["f_index", "f_middle", "f_ring", "f_pinky"]:
            chain = []
            for idx in ["01", "02", "03"]:
                b_meta = metarm.edit_bones.get(f"{fname}.{idx}{side}")
                if b_meta:
                    chain.append(b_meta)

            if not chain:
                continue

            for b_meta in chain:
                dir_b = (b_meta.tail - b_meta.head).normalized()
                z_target = index_plane_normal.cross(dir_b)
                if z_target.length > 0.0001:
                    b_meta.align_roll(z_target)

                orig_b = (
                    armature.edit_bones.get(b_meta.name)
                    or armature.edit_bones.get("DEF-" + b_meta.name)
                    or armature.edit_bones.get(b_meta.name.replace(".0", "0"))
                )
                if orig_b:
                    orig_b.roll = b_meta.roll

    for bone in metarm.edit_bones:
        if "thumb" in bone.name:
            orig_b = armature.edit_bones.get(bone.name) or armature.edit_bones.get("DEF-" + bone.name)
            if orig_b:
                bone.roll = orig_b.roll

    # Fix hand bones being rotated 90 degrees sideways and arm deformation bones being wonky
    if "Loli" in obj.name:
        metarm.edit_bones["upper_arm.L"].tail.y += .003
        metarm.edit_bones["upper_arm.R"].tail.y += .003

    ##########  DETACH PHYSICS BONES,  

    metanames = ['eye.L', 'eye.R', 'spine', 'thigh.L', 'shin.L', 'foot.L', 'toe.L', 'thigh.R', 'shin.R', 'foot.R', 'toe.R', 'spine.001', 'spine.002', 'spine.003', 'breast.L', 'breast.R', 'shoulder.L', 'upper_arm.L', 'forearm.L', 'hand.L', 'thumb.01.L', 'thumb.02.L', 'thumb.03.L', 'f_index.01.L', 'f_index.02.L', 'f_index.03.L', 'f_middle.01.L', 'f_middle.02.L', 'f_middle.03.L', 'f_ring.01.L', 'f_ring.02.L', 'f_ring.03.L', 'f_pinky.01.L', 'f_pinky.02.L', 'f_pinky.03.L', 'spine.004', 'spine.006', 'shoulder.R', 'upper_arm.R', 'forearm.R', 'hand.R', 'thumb.01.R', 'thumb.02.R', 'thumb.03.R', 'f_index.01.R', 'f_index.02.R', 'f_index.03.R', 'f_middle.01.R', 'f_middle.02.R', 'f_middle.03.R', 'f_ring.01.R', 'f_ring.02.R', 'f_ring.03.R', 'f_pinky.01.R', 'f_pinky.02.R', 'f_pinky.03.R']
    if not toe_bones_exist:
        metanames.remove("toe.L")
        metanames.remove("toe.R")


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

        
    ## Duplicates the physics bones
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    bones = armature.edit_bones[:]
    for bone in bones:
        if bone.name not in pre_res:
            #this is a physics bone, so duplicate it.
            bone.select = True
            bone.select_tail = True
            bone.select_head = True

    bpy.ops.armature.separate()
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

    rigifyr = bpy.data.objects.get("rigify")
    if not rigifyr:
        objList = bpy.context.selected_objects
        unselected = [obj for obj in objList if obj != context.active_object]
        rigifyr = unselected[0] if unselected else context.active_object

    obs = [bpy.data.objects.get("rigify"), bpy.data.objects.get(newrig)]
    c={}
    c["object"] = c["active_object"] = bpy.data.objects.get("rigify")
    c["selected_objects"] = c["selected_editable_objects"] = obs
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    
    with bpy.context.temp_override(active_object=bpy.data.objects.get("rigify"), selected_editable_objects=obs):
        bpy.ops.object.join()


    bpy.context.view_layer.objects.active = bpy.data.objects["rigify"]

    setup_neck_and_head_follow(neck_follow_value=0.0, head_follow_value=0.0)
    setup_finger_scale_controls_on_x_axis_to_curl_just_the_fingertips(rigifyr)

    bpy.ops.object.mode_set(mode='EDIT')

    #### whats this for???
    #oh i think it's useless now bc there's only one rig LMAOLMAO
    #for bone in bones_list:
    #    armature.edit_bones[bone.name].roll = rigifyr.data.edit_bones[bone.name].roll
    ####

    ## Reattach the physics bones to their parents
    #Go back into rigify, find the main body bones, and reattach every bone in the corresponding dict list
    for mainbone in savethechildren:    
        for childbone in savethechildren[mainbone]:
            rigifyr.data.edit_bones[childbone].parent = rigifyr.data.edit_bones[mainbone]

    print("donelol\n")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects["rigify"].show_in_front = True

    # Symmetrize clothes/hair bones
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in rigifyr.data.edit_bones:
        if " L " in bone.name:  # Finds clothes/hair bones with symmetrical bones
            y = bone.name.find(' L ')  # Finds index of "Hair L 1"
            orgname = bone.name
            try:
                oppbone = orgname[:y] + " R " + orgname[y+3:] # oppbone = "Hair R 1"
                bone.name = orgname[:y] + orgname[y+3:] + ".L"  #Rename bones to "Hair 1.L/R" so Blender 
                rigifyr.data.edit_bones[oppbone].name = orgname[:y] + orgname[y+3:] + ".R" # goes ":o symmetry"
            except:
                pass

    rigifyr.pose.bones["upper_arm_parent.L"]["pole_parent"] = 2
    rigifyr.pose.bones["upper_arm_parent.R"]["pole_parent"] = 2
    rigifyr.pose.bones["thigh_parent.L"]["pole_parent"] = 2
    rigifyr.pose.bones["thigh_parent.R"]["pole_parent"] = 2

    bpy.ops.object.mode_set(mode='OBJECT')
    #change active object to rigifyr

    bpy.context.view_layer.objects.active = bpy.data.objects["rigify"]

    bpy.ops.object.mode_set(mode='OBJECT')

    # This part puts all the main bones I use into the secoond bone layer
    listofbones = ["root", "foot_heel_ik.R", "foot_heel_ik.L", "toe_ik.R", "toe_ik.L", "foot_ik.R", "foot_ik.L", "thigh_ik_target.R", "thigh_ik_target.L", "hips", "torso", "chest", "neck", "head", "shoulder.L", "shoulder.R", "upper_arm_fk.L", "upper_arm_fk.R", "forearm_fk.L", "forearm_fk.R", "hand_fk.L", "hand_fk.R", "upper_arm_ik_target.L", "upper_arm_ik_target.R", "hand_ik.R", "hand_ik.L", ]

    if not toe_bones_exist:
        listofbones.remove("toe_ik.R")
        listofbones.remove("toe_ik.L")
        
    if not is_version_4:
        for bone in listofbones:
            bpy.context.active_object.pose.bones[bone].bone.layers[1] = True
        
    try:
        bpy.data.objects["EyeStar"].hide_viewport = False
    except:
        pass

    char_name = extract_clean_character_name(original_name)
    try:
        if "rigify" in bpy.data.objects and bpy.data.objects["rigify"].users_collection:
            bpy.data.objects["rigify"].users_collection[0].name = char_name
    except:
        pass
    if "rigify" in bpy.data.objects:
        bpy.data.objects["rigify"].name = char_name + "Rig"
                
    bpy.ops.object.mode_set(mode='POSE')   
    bpy.ops.pose.select_all(action='DESELECT')
    bones_list = obj.pose.bones

    # Creates selection sets for FK arms + shoulders, hair bones, and clothes bones.  Selection Sets is an addon that comes with Blender.
    try:
        bpy.ops.object.mode_set(mode='POSE')

        arms = ['upper_arm_fk', 'forearm_fk', 'hand_fk', 'shoulder']
        bpy.ops.pose.select_all(action='DESELECT')
        for side in ['.L', '.R']:
            for bone in arms:
                bonename = bone + side
                rigifyr.pose.bones[bonename].bone.select= True
        bpy.ops.pose.selection_set_add()
        bpy.ops.pose.selection_set_assign()
        bpy.ops.pose.select_all(action='DESELECT')

        ## Hair
        for bone in bones_list:
            if "Hair" in bone.name:
                rigifyr.pose.bones[bone.name].bone.select = True
        bpy.ops.pose.selection_set_add()
        bpy.ops.pose.selection_set_assign()
        bpy.ops.pose.select_all(action='DESELECT')

        ## Clothes
        for bone in bones_list:
            if "Amice" in bone.name or ("fk" not in bone.name and "tweak" not in bone.name and "Twist" not in bone.name and "Hair" not in bone.name and (bone.name[-1].isdigit() or bone.name[-3].isdigit())):
                rigifyr.pose.bones[bone.name].bone.select = True
        bpy.ops.pose.selection_set_add()
        bpy.ops.pose.selection_set_assign()
        bpy.ops.pose.select_all(action='DESELECT')
        bpy.context.object.selection_sets[0].name = "FK Arms"
        bpy.context.object.selection_sets[1].name = "Hair"
        bpy.context.object.selection_sets[2].name = "Clothes...and teeth and eyes lmao"
    except:
        pass
    
    bpy.ops.object.mode_set(mode='EDIT') 

    rig = bpy.context.object
    if kachina:
        # Deletes the extra useless finger bones
        eatthis = ['f_index.03.L', 'f_index.01.L.001', 'f_index.01_master.L', 'thumb.03.L', 'thumb.01.L.001', 'f_middle.03.L', 'f_middle.01.L.001', 'f_ring.01_master.L', 'f_ring.01.L', 'f_ring.02.L', 'f_ring.03.L', 'f_ring.01.L.001', 'f_pinky.01_master.L', 'f_pinky.01.L', 'f_pinky.02.L', 'f_pinky.03.L', 'f_pinky.01.L.001', 'f_index.03.R', 'f_index.01.R.001', 'f_index.01_master.R', 'thumb.03.R', 'thumb.01.R.001', 'f_middle.03.R', 'f_middle.01.R.001', 'f_ring.01_master.R', 'f_ring.01.R', 'f_ring.02.R', 'f_ring.03.R', 'f_ring.01.R.001', 'f_pinky.01_master.R', 'f_pinky.01.R', 'f_pinky.02.R', 'f_pinky.03.R', 'f_pinky.01.R.001', 'ORG-palm.01.L', 'ORG-f_index.01.L', 'ORG-f_index.02.L', 'ORG-f_index.03.L', 'ORG-thumb.03.L', 'DEF-f_index.01.L', 'DEF-f_index.02.L', 'DEF-f_index.03.L', 'DEF-thumb.03.L', 'DEF-palm.01.L', 'MCH-f_index.01_drv.L', 'MCH-f_index.02_drv.L', 'MCH-f_index.03_drv.L', 'MCH-f_index.03.L', 'MCH-f_index.02.L', 'MCH-f_index.01.L', 'MCH-thumb.03_drv.L', 'MCH-thumb.03.L', 'ORG-f_middle.03.L', 'DEF-f_middle.03.L', 'MCH-f_middle.03_drv.L', 'MCH-f_middle.03.L', 'ORG-palm.03.L', 'DEF-palm.03.L', 'ORG-palm.04.L', 'DEF-palm.04.L', 'ORG-palm.01.R', 'ORG-f_index.01.R', 'ORG-f_index.02.R', 'ORG-f_index.03.R', 'ORG-thumb.03.R', 'DEF-f_index.01.R', 'DEF-f_index.02.R', 'DEF-f_index.03.R', 'DEF-thumb.03.R', 'DEF-palm.01.R', 'MCH-f_index.01_drv.R', 'MCH-f_index.02_drv.R', 'MCH-f_index.03_drv.R', 'MCH-f_index.03.R', 'MCH-f_index.02.R', 'MCH-f_index.01.R', 'MCH-thumb.03_drv.R', 'MCH-thumb.03.R', 'ORG-f_middle.03.R', 'DEF-f_middle.03.R', 'MCH-f_middle.03_drv.R', 'MCH-f_middle.03.R', 'ORG-palm.03.R', 'DEF-palm.03.R', 'ORG-palm.04.R', 'DEF-palm.04.R']
        for this in eatthis:
            ugh = rigifyr.data.edit_bones[this]
            rigifyr.data.edit_bones.remove(ugh)

        # This workaround is for an issue so stupid i dont even want to explain this lmao
        bpy.ops.object.mode_set(mode='POSE') 
        wtf = [ 'MCH-thumb.02.L', 'MCH-f_middle.02.L', 'MCH-thumb.02.R', 'MCH-f_middle.02.R']
        for this in wtf:
            rigifyr.pose.bones[this].constraints[0].enabled = False

        bpy.ops.object.mode_set(mode='EDIT') 
        # The scale controls for the fingers are big as hell lmao what.
        sizethis = ['thumb.01_master.L', 'f_middle.01_master.L', 'thumb.01_master.R', 'f_middle.01_master.R']
        for this in sizethis:
            rigifyr.data.edit_bones[this].length *= .08

        # This corrects the drivers on the superscale control. Without this fix, the scales operate opposite to how they should.
        bpy.ops.object.mode_set(mode='POSE')
        for oDrv in rigifyr.animation_data.drivers:
            for variable in oDrv.driver.variables:
                for target in variable.targets:
                    if "MCH-f_middle.02_drv" in oDrv.data_path or "MCH-f_index.02_drv" in oDrv.data_path:
                        oDrv.driver.expression += "* -1"
    else:
        # Fix scaling for finger tips.
        for oDrv in rig.animation_data.drivers:
            for variable in oDrv.driver.variables:
                for target in variable.targets:
                    if ".03" in oDrv.data_path and target.data_path[-7:] == "scale.y":
                        target.data_path = target.data_path[:-1] + "x"

    fingerlist = ["thumb.01_master", "f_index.01_master", "f_middle.01_master", "f_ring.01_master", "f_pinky.01_master"]

    for side in [".L", ".R"]:
        for bone in fingerlist:
            try:
                rig.pose.bones[bone + side].lock_scale[0] = False
            except:
                pass

    # Apply exact requested Quaternion rotation to thumb.01_master controls
    bpy.ops.object.mode_set(mode='POSE')
    if "thumb.01_master.L" in rig.pose.bones:
        pb_l = rig.pose.bones["thumb.01_master.L"]
        pb_l.rotation_mode = 'QUATERNION'
        pb_l.rotation_quaternion = (0.915334, 0.0, 0.402697, 0.0)

    if "thumb.01_master.R" in rig.pose.bones:
        pb_r = rig.pose.bones["thumb.01_master.R"]
        pb_r.rotation_mode = 'QUATERNION'
        pb_r.rotation_quaternion = (0.915334, 0.0, -0.402697, 0.0)

    # Fix face shading being offset 90 degrees
    bpy.ops.object.mode_set(mode='OBJECT')
    try:
        head_driver_obj = bpy.data.objects.get("Head Driver") or bpy.data.objects.get("Head Origin")
        bpy.context.view_layer.objects.active = head_driver_obj
        bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')
    except:
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
    
    this_obj.pose.bones["head"].custom_shape_scale_xyz = (1.65,1.65,1.65)
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

    this_obj.pose.bones["foot_heel_ik.L"].custom_shape_translation = (0.0,0.06,0.0)
    this_obj.pose.bones["foot_heel_ik.R"].custom_shape_translation = (0.0,0.06,0.0)

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

    # Select eye rig    
    eye_rig_obj = bpy.data.objects.get("eyerig")
    if eye_rig_obj:
        eye_rig_obj.select_set(True)
    
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

    # Weapon / Prop bones setup in Edit Mode:
    # 1. Detect weapon bones (prop1, prop2, bip001 prop, weapon, equip, etc.)
    #    CRITICAL: EXCLUDE weaponbox or box (these are back/spine bones, NOT hand weapons)
    # 2. Unparent weapon roots from DEF-hand / hand bones
    # 3. Snap prop.L / prop.R to weapon root or hand
    # 4. Parent weapon roots to prop.L / prop.R
    # 5. Parent prop.L / prop.R to root
    weapon_keywords = ["prop1", "prop2", "bip001 prop", "weapon", "equip"]
    raw_weapon_bones = []
    for b in armature.edit_bones:
        b_low = b.name.lower()
        if "box" in b_low or "weaponbox" in b_low:
            continue
        if b.name in ["prop.L", "prop.R"]:
            continue
        if b.name.startswith("MCH-") or b.name.startswith("ORG-"):
            continue
        if any(k in b_low for k in weapon_keywords) or ("prop" in b_low and "parent" not in b_low):
            raw_weapon_bones.append(b)

    weapon_bones_L = []
    weapon_bones_R = []
    for wb in raw_weapon_bones:
        wb_low = wb.name.lower()
        p_name = wb.parent.name.lower() if wb.parent else ""

        is_left = (
            "prop2" in wb_low or ".l" in wb_low or "_l" in wb_low or "left" in wb_low
            or "hand.l" in p_name or "l hand" in p_name or ".l" in p_name or "_l" in p_name or "left" in p_name
            or wb.head.x > 0.02
        )
        is_right = (
            "prop1" in wb_low or ".r" in wb_low or "_r" in wb_low or "right" in wb_low
            or "hand.r" in p_name or "r hand" in p_name or ".r" in p_name or "_r" in p_name or "right" in p_name
            or wb.head.x < -0.02
        )

        if ("prop2" in wb_low or ".l" in wb_low or "hand.l" in p_name or "l hand" in p_name) and not ("prop1" in wb_low or ".r" in wb_low):
            weapon_bones_L.append(wb)
        elif ("prop1" in wb_low or ".r" in wb_low or "hand.r" in p_name or "r hand" in p_name) and not ("prop2" in wb_low or ".l" in wb_low):
            weapon_bones_R.append(wb)
        elif is_left and not is_right:
            weapon_bones_L.append(wb)
        elif is_right and not is_left:
            weapon_bones_R.append(wb)
        elif wb.head.x >= 0:
            weapon_bones_L.append(wb)
        else:
            weapon_bones_R.append(wb)

    def get_weapon_roots(b_list):
        roots = []
        for b in b_list:
            if not b.parent or b.parent not in b_list:
                roots.append(b)
        return roots

    roots_L = get_weapon_roots(weapon_bones_L)
    roots_R = get_weapon_roots(weapon_bones_R)

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
        else:
            hand_ref_l = (
                armature.edit_bones.get("DEF-hand.L")
                or armature.edit_bones.get("hand.L")
                or armature.edit_bones.get("hand-ik-L")
                or armature.edit_bones.get("hand_ik.L")
            )
            if hand_ref_l:
                eb_prop_l.head = hand_ref_l.head.copy()
                eb_prop_l.tail = hand_ref_l.tail.copy()
                eb_prop_l.roll = hand_ref_l.roll
        if root_master:
            eb_prop_l.parent = root_master
        eb_prop_l.inherit_scale = "FULL"

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
        else:
            hand_ref_r = (
                armature.edit_bones.get("DEF-hand.R")
                or armature.edit_bones.get("hand.R")
                or armature.edit_bones.get("hand-ik-R")
                or armature.edit_bones.get("hand_ik.R")
            )
            if hand_ref_r:
                eb_prop_r.head = hand_ref_r.head.copy()
                eb_prop_r.tail = hand_ref_r.tail.copy()
                eb_prop_r.roll = hand_ref_r.roll
        if root_master:
            eb_prop_r.parent = root_master
        eb_prop_r.inherit_scale = "FULL"

    detected_weapon_bone_names = [b.name for b in raw_weapon_bones]

    # Add Skirt calculation bones hierarchy parented to hips (Miyabi style: dual Locked Track per leg)
    hips_b = armature.edit_bones.get("hips") or armature.edit_bones.get("torso")
    def_thigh_l = armature.edit_bones.get("DEF-thigh.L") or armature.edit_bones.get("thigh.L") or armature.edit_bones.get("thigh_fk.L")
    def_thigh_r = armature.edit_bones.get("DEF-thigh.R") or armature.edit_bones.get("thigh.R") or armature.edit_bones.get("thigh_fk.R")

    if hips_b:
        # MCH-Skirt_Parent
        eb_sk_parent = armature.edit_bones.get("MCH-Skirt_Parent") or armature.edit_bones.new("MCH-Skirt_Parent")
        eb_sk_parent.parent = hips_b
        eb_sk_parent.head = hips_b.head.copy()
        eb_sk_parent.tail = hips_b.head.copy()
        eb_sk_parent.tail.y += 0.1
        eb_sk_parent.use_deform = False

        # MCH-Skirt_Parent02 (tracks root/world)
        eb_sk_p02 = armature.edit_bones.get("MCH-Skirt_Parent02") or armature.edit_bones.new("MCH-Skirt_Parent02")
        eb_sk_p02.parent = eb_sk_parent
        eb_sk_p02.head = hips_b.head.copy()
        eb_sk_p02.tail = hips_b.head.copy()
        eb_sk_p02.tail.z -= 0.1
        eb_sk_p02.use_deform = False

        # MCH-INT-Skirt_Parent02 (damped track to Parent02 governed by Skirt_Follow)
        eb_int_p02 = armature.edit_bones.get("MCH-INT-Skirt_Parent02") or armature.edit_bones.new("MCH-INT-Skirt_Parent02")
        eb_int_p02.parent = hips_b
        eb_int_p02.head = hips_b.head.copy()
        eb_int_p02.tail = hips_b.head.copy()
        eb_int_p02.tail.z -= 0.1
        eb_int_p02.use_deform = False

        # 4 Sensor / Calc bones with Locked Track (2 per leg isolating X pitch and Z abduction)
        if def_thigh_l:
            eb_calc_xl = armature.edit_bones.get("MCH-Skirt_Auto_Calc_X.L") or armature.edit_bones.new("MCH-Skirt_Auto_Calc_X.L")
            eb_calc_xl.parent = eb_int_p02
            eb_calc_xl.head = Vector((def_thigh_l.head.x, def_thigh_l.head.y, hips_b.head.z))
            eb_calc_xl.tail = Vector((def_thigh_l.head.x, def_thigh_l.head.y, hips_b.head.z - 0.1))
            eb_calc_xl.use_deform = False

            eb_calc_zl = armature.edit_bones.get("MCH-Skirt_Auto_Calc_Z.L") or armature.edit_bones.new("MCH-Skirt_Auto_Calc_Z.L")
            eb_calc_zl.parent = eb_int_p02
            eb_calc_zl.head = eb_calc_xl.head.copy()
            eb_calc_zl.tail = eb_calc_xl.tail.copy()
            eb_calc_zl.use_deform = False

        if def_thigh_r:
            eb_calc_xr = armature.edit_bones.get("MCH-Skirt_Auto_Calc_X.R") or armature.edit_bones.new("MCH-Skirt_Auto_Calc_X.R")
            eb_calc_xr.parent = eb_int_p02
            eb_calc_xr.head = Vector((def_thigh_r.head.x, def_thigh_r.head.y, hips_b.head.z))
            eb_calc_xr.tail = Vector((def_thigh_r.head.x, def_thigh_r.head.y, hips_b.head.z - 0.1))
            eb_calc_xr.use_deform = False

            eb_calc_zr = armature.edit_bones.get("MCH-Skirt_Auto_Calc_Z.R") or armature.edit_bones.new("MCH-Skirt_Auto_Calc_Z.R")
            eb_calc_zr.parent = eb_int_p02
            eb_calc_zr.head = eb_calc_xr.head.copy()
            eb_calc_zr.tail = eb_calc_xr.tail.copy()
            eb_calc_zr.use_deform = False
   
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
    


   
    try:
        final_eye_L_name = left_eye_bone_name if left_eye_bone_name else "+EyeBone L A01"
        final_eye_R_name = right_eye_bone_name if right_eye_bone_name else "+EyeBone R A01"

        if "DEF-eye.L" in armature.edit_bones:
            armature.edit_bones["DEF-eye.L"].name = final_eye_L_name
        if "DEF-eye.R" in armature.edit_bones:
            armature.edit_bones["DEF-eye.R"].name = final_eye_R_name

        if '+EyeBone R A01.001' in armature.edit_bones and 'head' in armature.edit_bones:
            armature.edit_bones['+EyeBone R A01.001'].parent = armature.edit_bones['head']
        if '+EyeBone L A01.001' in armature.edit_bones and 'head' in armature.edit_bones:
            armature.edit_bones['+EyeBone L A01.001'].parent = armature.edit_bones['head']

        if final_eye_R_name in armature.edit_bones and '+EyeBone R A01.001' in armature.edit_bones:
            eye_R_head_pos = armature.edit_bones[final_eye_R_name].head
            armature.edit_bones['+EyeBone R A01.001'].head = eye_R_head_pos
            armature.edit_bones['+EyeBone R A01.001'].tail.x = eye_R_head_pos[0]
            armature.edit_bones['+EyeBone R A01.001'].tail.y = armature.edit_bones[final_eye_R_name].tail.y
            armature.edit_bones['+EyeBone R A01.001'].tail.z = eye_R_head_pos[2]

        if final_eye_L_name in armature.edit_bones and '+EyeBone L A01.001' in armature.edit_bones:
            eye_L_head_pos = armature.edit_bones[final_eye_L_name].head
            armature.edit_bones['+EyeBone L A01.001'].head = eye_L_head_pos
            armature.edit_bones['+EyeBone L A01.001'].tail.x = eye_L_head_pos[0]
            armature.edit_bones['+EyeBone L A01.001'].tail.y = armature.edit_bones[final_eye_L_name].tail.y
            armature.edit_bones['+EyeBone L A01.001'].tail.z = eye_L_head_pos[2]
    except Exception:
        pass

    # Ensure eyetrack bones follow head so moving root.002 or torso moves eye trackers
    head_bone_ref = armature.edit_bones.get('head') or armature.edit_bones.get('root.002') or armature.edit_bones.get('root')
    if head_bone_ref:
        for et_name in ("eyetrack", "EyeTrack"):
            b_et = armature.edit_bones.get(et_name)
            if b_et:
                b_et.parent = head_bone_ref
        for et_sub in ("eyetrack_L", "eyetrack.L", "EyeTrack_L", "EyeTrack.L"):
            b_sub = armature.edit_bones.get(et_sub)
            if b_sub and "eyetrack" in armature.edit_bones:
                b_sub.parent = armature.edit_bones["eyetrack"]
        for et_sub in ("eyetrack_R", "eyetrack.R", "EyeTrack_R", "EyeTrack.R"):
            b_sub = armature.edit_bones.get(et_sub)
            if b_sub and "eyetrack" in armature.edit_bones:
                b_sub.parent = armature.edit_bones["eyetrack"]

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

    # Universal Skirt Detection & Radial Classification
    # Identifies skirt/dress/majia chains and classifies them into 8 radial quadrants relative to hips/pelvis:
    # FRONT_C, FRONT_L, SIDE_L, BACK_L, BACK_C, BACK_R, SIDE_R, FRONT_R
    pelvis_ref = armature.edit_bones.get("DEF-spine.001") or armature.edit_bones.get("hips") or armature.edit_bones.get("pelvis")
    pelvis_pos = pelvis_ref.head.copy() if pelvis_ref else Vector((0.0, 0.0, 1.0))
    
    # Hoyoverse/ZZZ forward detection: default forward is -Y
    forward_sign = -1.0
    head_b_ref = armature.edit_bones.get("head") or armature.edit_bones.get("DEF-head")
    for b in armature.edit_bones:
        if "eye" in b.name.lower() and head_b_ref:
            if b.head.y > head_b_ref.head.y:
                forward_sign = 1.0
            else:
                forward_sign = -1.0
            break

    # Find root of each skirt/dress chain (only original deform/character bones)
    skirt_keywords = ["skirt", "dress", "hem", "qun"]
    sk_bones = []
    for b in armature.edit_bones:
        if b.name.startswith(('MCH-', 'CTRL-', 'ORG-', 'DEF-')) or b.name.endswith('_tip'):
            continue
        b_low = b.name.lower()
        if any(k in b_low for k in skirt_keywords):
            # Exclude breast, chest, arm, sleeve, furisode, hand, collar
            if any(ex in b_low for ex in ["breast", "chest", "arm", "sleeve", "furisode", "hand", "shoulder", "collar"]):
                continue
            # Also ensure parent is at or below pelvis level (not attached to upper spine like spine.002 or spine.003)
            if b.parent and any(p_ex in b.parent.name.lower() for p_ex in ["spine.002", "spine.003", "chest", "neck", "shoulder", "arm", "head"]):
                continue
            sk_bones.append(b)

    # First try hierarchy roots
    skirt_chain_roots = []
    for b in sk_bones:
        parent_is_skirt = b.parent and b.parent in sk_bones
        if not parent_is_skirt:
            skirt_chain_roots.append(b)

    # Walk children chain for each root
    chains_list = []
    for root_eb in skirt_chain_roots:
        chain = [root_eb.name]
        curr = root_eb
        while curr.children:
            sk_kids = [c for c in curr.children if c in sk_bones]
            if not sk_kids:
                break
            curr = sk_kids[0]
            chain.append(curr.name)
        chains_list.append(chain)

    # Fallback to prefix grouping if hierarchy was flat or already reparented
    if len(sk_bones) > len(chains_list) and all(len(c) == 1 for c in chains_list):
        import re
        chains_dict = {}
        for b in sk_bones:
            m = re.match(r'^(.*?)[_.]?(\d+)$', b.name)
            if m:
                prefix, num = m.group(1), int(m.group(2))
                chains_dict.setdefault(prefix, []).append((num, b.name))
            else:
                chains_dict.setdefault(b.name, []).append((0, b.name))
        chains_list = []
        for prefix, items in chains_dict.items():
            items.sort(key=lambda x: x[0])
            chains_list.append([x[1] for x in items])

    # Classify each chain root and collect bone names by quadrant and chain depth
    skirt_quadrant_chains = {
        "FRONT_C": [],
        "FRONT_L": [],
        "SIDE_L": [],
        "BACK_L": [],
        "BACK_C": [],
        "BACK_R": [],
        "SIDE_R": [],
        "FRONT_R": []
    }

    import math
    for chain in chains_list:
        root_eb = armature.edit_bones[chain[0]]
        dx = root_eb.head.x - pelvis_pos.x
        dy = (root_eb.head.y - pelvis_pos.y) * forward_sign
        angle = math.degrees(math.atan2(dx, dy))

        if -22.5 <= angle < 22.5:
            cat = "FRONT_C"
        elif 22.5 <= angle < 67.5:
            cat = "FRONT_L"
        elif 67.5 <= angle < 112.5:
            cat = "SIDE_L"
        elif 112.5 <= angle < 157.5:
            cat = "BACK_L"
        elif angle >= 157.5 or angle < -157.5:
            cat = "BACK_C"
        elif -157.5 <= angle < -112.5:
            cat = "BACK_R"
        elif -112.5 <= angle < -67.5:
            cat = "SIDE_R"
        elif -67.5 <= angle < -22.5:
            cat = "FRONT_R"
        else:
            cat = "FRONT_C"

        skirt_quadrant_chains[cat].append(chain)

    print(f"[ZZZ RIG] Detected skirt chains in {len(chains_list)} locations across 8 radial quadrants.")
    front_skirt_bones = [b for ch in skirt_quadrant_chains["FRONT_C"] + skirt_quadrant_chains["FRONT_L"] + skirt_quadrant_chains["FRONT_R"] for b in ch]
    side_skirt_bones = [b for ch in skirt_quadrant_chains["SIDE_L"] + skirt_quadrant_chains["SIDE_R"] for b in ch]
    back_skirt_bones = [b for ch in skirt_quadrant_chains["BACK_C"] + skirt_quadrant_chains["BACK_L"] + skirt_quadrant_chains["BACK_R"] for b in ch]

    # Build Miyabi-style CTRL chains and tip helper bones for clean Stretch To without dependency cycles
    skirt_ctrl_chains_data = []
    all_skirt_ctrl_bones = []
    all_skirt_deform_bones = []
    all_skirt_tip_bones = []

    for cat, chains in skirt_quadrant_chains.items():
        for chain in chains:
            c_chain = []
            root_orig = armature.edit_bones[chain[0]]
            orig_parent = root_orig.parent
            for i, bname in enumerate(chain):
                orig_eb = armature.edit_bones[bname]
                all_skirt_deform_bones.append(bname)
                cname = f"CTRL-{bname}"
                ctrl_eb = armature.edit_bones.get(cname) or armature.edit_bones.new(cname)
                ctrl_eb.head = orig_eb.head.copy()
                ctrl_eb.use_deform = False
                c_chain.append(cname)
                all_skirt_ctrl_bones.append(cname)

            # Align tails along the chain towards the next head so bone axes point cleanly down the skirt
            for i in range(len(chain)):
                bname = chain[i]
                cname = c_chain[i]
                orig_eb = armature.edit_bones[bname]
                ctrl_eb = armature.edit_bones[cname]
                if i < len(chain) - 1:
                    next_head = armature.edit_bones[chain[i+1]].head.copy()
                    orig_eb.tail = next_head
                    ctrl_eb.tail = next_head.copy()
                else:
                    if len(chain) > 1:
                        prev_head = armature.edit_bones[chain[i-1]].head.copy()
                        dir_v = (orig_eb.head - prev_head).normalized()
                        seg_len = (orig_eb.head - prev_head).length
                    else:
                        dir_v = Vector((0, 0, -1))
                        seg_len = 0.05
                    orig_eb.tail = orig_eb.head + dir_v * seg_len
                    ctrl_eb.tail = orig_eb.tail.copy()

            for i, cname in enumerate(c_chain):
                ctrl_eb = armature.edit_bones[cname]
                if i == 0:
                    ctrl_eb.parent = orig_parent if (orig_parent and not orig_parent.name.startswith("CTRL-")) else hips_b
                else:
                    ctrl_eb.parent = armature.edit_bones[c_chain[i-1]]

            tip_name = f"CTRL-{chain[-1]}_tip"
            tip_eb = armature.edit_bones.get(tip_name) or armature.edit_bones.new(tip_name)
            last_ctrl = armature.edit_bones[c_chain[-1]]
            tip_eb.head = last_ctrl.tail.copy()
            if len(chain) > 1:
                prev_head = armature.edit_bones[chain[-1]].head.copy()
                dir_v = (tip_eb.head - prev_head).normalized()
            else:
                dir_v = Vector((0, 0, -1))
            tip_eb.tail = tip_eb.head + dir_v * 0.03
            tip_eb.parent = last_ctrl
            tip_eb.use_deform = False
            all_skirt_tip_bones.append(tip_name)

            # Re-parent deform bones to their respective CTRL bones (disconnected)
            for i, bname in enumerate(chain):
                def_eb = armature.edit_bones[bname]
                def_eb.parent = armature.edit_bones[c_chain[i]]
                def_eb.use_connect = False
                def_eb.use_deform = True

            skirt_ctrl_chains_data.append({
                "cat": cat,
                "deform_chain": chain,
                "ctrl_chain": c_chain,
                "tip_name": tip_name
            })                                                            

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

            set_prop(plate, "Skirt_Auto", 1.00, 0.0, 1.0, "Auto Skirt Collision")
            set_prop(plate, "Toggle Skirt Constraints", 1.00, 0.0, 1.0, "Auto Skirt Collision")
            if "Toggle Shoulder Constraints" in plate:
                del plate["Toggle Shoulder Constraints"]
            if "Viewport Outlines" in plate:
                del plate["Viewport Outlines"]
            set_prop(plate, "Head Follow", 0.00, 0.0, 1.0, "Head Follow")
            set_prop(plate, "Neck Follow", 0.50, 0.0, 1.0, "Neck Follow")
            set_prop(plate, "Use Head Controller", 0.00, 0.0, 1.0, "Use Head Tracker Controller")
            set_prop(plate, "EyeCorrection", 1.00, 0.0, 1.0, "Adjust Pupil Wink Distance")
            set_prop(plate, "Skirt_Follow", 0.00, 0.0, 1.0, "Skirt Follow (Torso)")
            set_prop(plate, "Shirt_Follow", 1.00, 0.0, 1.0, "Shirt Follow")

        # Setup Miyabi-style parent and calculation tracking constraints
        root_target_bname = "root" if "root" in rig_obj_ref.pose.bones else ("root.002" if "root.002" in rig_obj_ref.pose.bones else "root.001")
        pb_p02 = rig_obj_ref.pose.bones.get("MCH-Skirt_Parent02")
        if pb_p02 and root_target_bname in rig_obj_ref.pose.bones:
            for c in list(pb_p02.constraints): pb_p02.constraints.remove(c)
            cr = pb_p02.constraints.new('COPY_ROTATION')
            cr.target = rig_obj_ref
            cr.subtarget = root_target_bname

        pb_int_p02 = rig_obj_ref.pose.bones.get("MCH-INT-Skirt_Parent02")
        if pb_int_p02:
            for c in list(pb_int_p02.constraints): pb_int_p02.constraints.remove(c)
            dt = pb_int_p02.constraints.new('DAMPED_TRACK')
            dt.target = rig_obj_ref
            dt.subtarget = "MCH-Skirt_Parent02"
            dt.track_axis = 'TRACK_NEGATIVE_Z'
            dt.head_tail = 1.0
            if plate:
                drv_f = dt.driver_add("influence").driver
                drv_f.type = 'SCRIPTED'
                var_f = drv_f.variables.new()
                var_f.name = "Skirt_Follow"
                var_f.type = 'SINGLE_PROP'
                var_f.targets[0].id = rig_obj_ref
                var_f.targets[0].data_path = 'pose.bones["plate-settings"]["Skirt_Follow"]'
                drv_f.expression = "Skirt_Follow"

        # Setup 4 sensor calculation bones with LOCKED_TRACK targeting thighs
        calc_cfgs = [
            ("MCH-Skirt_Auto_Calc_X.L", "DEF-thigh.L", 'LOCK_X', 'XYZ'),
            ("MCH-Skirt_Auto_Calc_Z.L", "DEF-thigh.L", 'LOCK_Z', 'ZXY'),
            ("MCH-Skirt_Auto_Calc_X.R", "DEF-thigh.R", 'LOCK_X', 'XYZ'),
            ("MCH-Skirt_Auto_Calc_Z.R", "DEF-thigh.R", 'LOCK_Z', 'ZXY'),
        ]

        for cname, th_name, lock_ax, rot_m in calc_cfgs:
            calc_pb = rig_obj_ref.pose.bones.get(cname)
            if calc_pb and th_name in rig_obj_ref.pose.bones:
                calc_pb.rotation_mode = rot_m
                for c in list(calc_pb.constraints): calc_pb.constraints.remove(c)
                lt = calc_pb.constraints.new('LOCKED_TRACK')
                lt.name = f"Track {lock_ax}"
                lt.target = rig_obj_ref
                lt.subtarget = th_name
                lt.track_axis = 'TRACK_Y'
                lt.lock_axis = lock_ax
                lt.head_tail = 0.8

        # Setup STRETCH_TO constraints on all deform bones (volume='VOLUME_XZX')
        for chain_data in skirt_ctrl_chains_data:
            chain = chain_data["deform_chain"]
            c_chain = chain_data["ctrl_chain"]
            tip_name = chain_data["tip_name"]
            for i, bname in enumerate(chain):
                pb = rig_obj_ref.pose.bones.get(bname)
                if pb:
                    for c in list(pb.constraints): pb.constraints.remove(c)
                    st = pb.constraints.new('STRETCH_TO')
                    st.name = "Stretch To"
                    st.target = rig_obj_ref
                    st.volume = 'VOLUME_XZX'
                    st.head_tail = 0.0
                    if i < len(chain) - 1:
                        st.subtarget = c_chain[i+1]
                    else:
                        st.subtarget = tip_name
                    b_ref = rig_obj_ref.data.bones.get(bname)
                    if b_ref:
                        st.rest_length = b_ref.length

        # Assign custom shape widgets to CTRL bones
        skirt_wgt = bpy.data.objects.get("eye circle") or bpy.data.objects.get("Circle.001") or bpy.data.objects.get("Circle")
        for cname in all_skirt_ctrl_bones:
            ctrl_pb = rig_obj_ref.pose.bones.get(cname)
            if ctrl_pb and skirt_wgt:
                ctrl_pb.custom_shape = skirt_wgt
                ctrl_pb.custom_shape_scale_xyz = (0.5, 0.5, 0.5)

        # Helper to add TRANSFORM collision deflection constraint driven by Skirt_Auto
        def add_skirt_deflect(ctrl_bone_name, const_name, calc_bone_name, map_from_ax, map_to_ax, from_range, to_range):
            pb = rig_obj_ref.pose.bones.get(ctrl_bone_name)
            if not pb or calc_bone_name not in rig_obj_ref.pose.bones:
                return
            co = pb.constraints.new('TRANSFORM')
            co.name = const_name
            co.target = rig_obj_ref
            co.subtarget = calc_bone_name
            co.target_space = 'LOCAL'
            co.owner_space = 'LOCAL'
            co.map_from = 'ROTATION'
            co.map_to = 'ROTATION'
            co.use_motion_extrapolate = False

            f1, f2 = from_range
            t1, t2 = to_range

            if f1 <= f2:
                from_min, from_max = f1, f2
                to_min, to_max = t1, t2
            else:
                from_min, from_max = f2, f1
                to_min, to_max = t2, t1

            if map_from_ax == 'X':
                co.from_min_x_rot = math.radians(from_min)
                co.from_max_x_rot = math.radians(from_max)
            elif map_from_ax == 'Z':
                co.from_min_z_rot = math.radians(from_min)
                co.from_max_z_rot = math.radians(from_max)

            if map_to_ax == 'X':
                co.map_to_x_from = map_from_ax
                co.to_min_x_rot = math.radians(to_min)
                co.to_max_x_rot = math.radians(to_max)
            elif map_to_ax == 'Z':
                co.map_to_z_from = map_from_ax
                co.to_min_z_rot = math.radians(to_min)
                co.to_max_z_rot = math.radians(to_max)

            # Driver on influence
            if plate:
                drv = co.driver_add("influence").driver
                drv.type = 'SCRIPTED'
                var = drv.variables.new()
                var.name = "Skirt_Auto"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = rig_obj_ref
                var.targets[0].data_path = 'pose.bones["plate-settings"]["Skirt_Auto"]'
                drv.expression = "Skirt_Auto"

        # Compute cumulative-to-local chain factors matching Miyabi's natural drape
        def compute_skirt_chain_factors(n):
            if n <= 1:
                return [1.0]
            if n == 2:
                return [0.60, 0.40]
            if n == 3:
                return [0.50, 0.30, 0.20]
            if n == 4:
                # Matches Miyabi reference rig:
                # Bone 0: ~50% of total world deflection (~21°-25°)
                # Bone 1: ~75% of total world deflection (~32°-38°)
                # Bone 2: ~90% of total world deflection (~38°-44°)
                # Bone 3: 100% of total world deflection (~42°-49°)
                return [0.50, 0.25, 0.15, 0.10]
            # General N
            cumul = [0.45 + 0.55 * (i / (n - 1)) ** 0.8 for i in range(n)]
            cumul[0] = 0.45
            factors = [cumul[0]]
            for i in range(1, n):
                factors.append(cumul[i] - cumul[i - 1])
            return factors

        # Apply deflection constraints per radial quadrant across full chain
        for chain_data in skirt_ctrl_chains_data:
            cat = chain_data["cat"]
            c_chain = chain_data["ctrl_chain"]
            n = len(c_chain)
            factors = compute_skirt_chain_factors(n)

            for i, cname in enumerate(c_chain):
                f = factors[i]
                if cat == "FRONT_C":
                    # Both legs forward -> pitch forward (-X) matching Miyabi ~45°
                    add_skirt_deflect(cname, "Deflect L Leg", "MCH-Skirt_Auto_Calc_X.L", 'X', 'X', (0, -22), (0, -45 * f))
                    add_skirt_deflect(cname, "Deflect R Leg", "MCH-Skirt_Auto_Calc_X.R", 'X', 'X', (0, -22), (0, -45 * f))

                elif "FRONT_L" in cat:
                    # Primary: Left leg forward -> pitch forward (-X) up to -52°
                    add_skirt_deflect(cname, "Pitch L Leg", "MCH-Skirt_Auto_Calc_X.L", 'X', 'X', (0, -22), (0, -52 * f))
                    # Primary: Left leg forward -> flare outward (-Z) up to -20°
                    add_skirt_deflect(cname, "Flare L Leg Forward", "MCH-Skirt_Auto_Calc_X.L", 'X', 'Z', (0, -22), (0, -20 * f))
                    # Secondary: Right leg forward -> cross-coupling pitch (-X) up to -14°
                    add_skirt_deflect(cname, "Pitch R Leg Cross", "MCH-Skirt_Auto_Calc_X.R", 'X', 'X', (0, -22), (0, -14 * f))
                    # Left leg abduct (-Z) -> flare outward (-Z) up to -28°
                    add_skirt_deflect(cname, "Abduct L Leg", "MCH-Skirt_Auto_Calc_Z.L", 'Z', 'Z', (0, -22), (0, -28 * f))
                    add_skirt_deflect(cname, "Pitch L Leg Abduct", "MCH-Skirt_Auto_Calc_Z.L", 'Z', 'X', (0, -22), (0, -22 * f))

                elif "FRONT_R" in cat:
                    # Primary: Right leg forward -> pitch forward (-X) up to -52°
                    add_skirt_deflect(cname, "Pitch R Leg", "MCH-Skirt_Auto_Calc_X.R", 'X', 'X', (0, -22), (0, -52 * f))
                    # Primary: Right leg forward -> flare outward (+Z) up to +20°
                    add_skirt_deflect(cname, "Flare R Leg Forward", "MCH-Skirt_Auto_Calc_X.R", 'X', 'Z', (0, -22), (0, 20 * f))
                    # Secondary: Left leg forward -> cross-coupling pitch (-X) up to -14°
                    add_skirt_deflect(cname, "Pitch L Leg Cross", "MCH-Skirt_Auto_Calc_X.L", 'X', 'X', (0, -22), (0, -14 * f))
                    # Right leg abduct (+Z) -> flare outward (+Z) up to +28°
                    add_skirt_deflect(cname, "Abduct R Leg", "MCH-Skirt_Auto_Calc_Z.R", 'Z', 'Z', (0, 22), (0, 28 * f))
                    add_skirt_deflect(cname, "Pitch R Leg Abduct", "MCH-Skirt_Auto_Calc_Z.R", 'Z', 'X', (0, 22), (0, -22 * f))

                elif "SIDE_L" in cat:
                    # Left leg abduct (-Z) -> flare outward (-Z) up to -45°
                    add_skirt_deflect(cname, "Abduct L Leg", "MCH-Skirt_Auto_Calc_Z.L", 'Z', 'Z', (0, -22), (0, -45 * f))
                    # Left leg forward (-X) -> flare outward (-Z) up to -30°
                    add_skirt_deflect(cname, "Flare L Leg Forward", "MCH-Skirt_Auto_Calc_X.L", 'X', 'Z', (0, -22), (0, -30 * f))
                    # Left leg forward (-X) -> slight pitch forward (-X) up to -16°
                    add_skirt_deflect(cname, "Pitch L Leg Forward", "MCH-Skirt_Auto_Calc_X.L", 'X', 'X', (0, -22), (0, -16 * f))

                elif "SIDE_R" in cat:
                    # Right leg abduct (+Z) -> flare outward (+Z) up to +45°
                    add_skirt_deflect(cname, "Abduct R Leg", "MCH-Skirt_Auto_Calc_Z.R", 'Z', 'Z', (0, 22), (0, 45 * f))
                    # Right leg forward (-X) -> flare outward (+Z) up to +30°
                    add_skirt_deflect(cname, "Flare R Leg Forward", "MCH-Skirt_Auto_Calc_X.R", 'X', 'Z', (0, -22), (0, 30 * f))
                    # Right leg forward (-X) -> slight pitch forward (-X) up to -16°
                    add_skirt_deflect(cname, "Pitch R Leg Forward", "MCH-Skirt_Auto_Calc_X.R", 'X', 'X', (0, -22), (0, -16 * f))

                elif "BACK_L" in cat:
                    # Left leg back (+X) -> pitch backward (+X) up to +35°
                    add_skirt_deflect(cname, "Back L Leg", "MCH-Skirt_Auto_Calc_X.L", 'X', 'X', (0, 20), (0, 35 * f))
                    # Left leg abduct (-Z) -> flare outward (-Z) up to -24°
                    add_skirt_deflect(cname, "Abduct L Leg", "MCH-Skirt_Auto_Calc_Z.L", 'Z', 'Z', (0, -22), (0, -24 * f))
                    add_skirt_deflect(cname, "Pitch L Leg Abduct", "MCH-Skirt_Auto_Calc_Z.L", 'Z', 'X', (0, -22), (0, 16 * f))

                elif "BACK_R" in cat:
                    # Right leg back (+X) -> pitch backward (+X) up to +35°
                    add_skirt_deflect(cname, "Back R Leg", "MCH-Skirt_Auto_Calc_X.R", 'X', 'X', (0, 20), (0, 35 * f))
                    # Right leg abduct (+Z) -> flare outward (+Z) up to +24°
                    add_skirt_deflect(cname, "Abduct R Leg", "MCH-Skirt_Auto_Calc_Z.R", 'Z', 'Z', (0, 22), (0, 24 * f))
                    add_skirt_deflect(cname, "Pitch R Leg Abduct", "MCH-Skirt_Auto_Calc_Z.R", 'Z', 'X', (0, 22), (0, 16 * f))

                elif cat == "BACK_C":
                    # Kick back (+X) -> flare backward (+X) up to +28°
                    add_skirt_deflect(cname, "Back L Leg", "MCH-Skirt_Auto_Calc_X.L", 'X', 'X', (0, 20), (0, 28 * f))
                    add_skirt_deflect(cname, "Back R Leg", "MCH-Skirt_Auto_Calc_X.R", 'X', 'X', (0, 20), (0, 28 * f))

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
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.data.objects["Empty"].name = "Head_Pole"
    bpy.data.objects["Head_Pole"].empty_display_size = 0.01
    bpy.data.objects["Head_Pole"].parent = bpy.data.objects[char_name+"Rig"]
    bpy.data.objects["Head_Pole"].parent_type = "BONE"
    bpy.data.objects["Head_Pole"].parent_bone = "neck"


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
        
    # Let's now add the pupil resizer drivers
    try:
        variablesScale = [
            {"var_name": "var", "var_type":"TRANSFORMS", "target": "Eye-Pupil-Control", "trans_space": "LOCAL_SPACE", "trans_type": "LOC_Y"},
            {"var_name": "var2", "var_type":"SINGLE_PROP", "data_path": 'pose.bones["plate-settings"]["EyeCorrection"]'}
        ]

        add_driver_to_bone_transform("+EyeBoneA02.R", "scale", 0, variablesScale, "1.5556 * var + 1")
        add_driver_to_bone_transform("+EyeBoneA02.R", "scale", 1, variablesScale, "1.5556 * var + 1")
        add_driver_to_bone_transform("+EyeBoneA02.R", "scale", 2, variablesScale, "1.5556 * var + 1")
        
        # push back driver
        add_driver_to_bone_transform("+EyeBoneA02.R", "location", 1, [
            {"var_name": "var", "var_type":"TRANSFORMS", "target": "Wink-Control-R", "trans_space": "LOCAL_SPACE", "trans_type": "LOC_Y"},
            {"var_name": "var2", "var_type":"SINGLE_PROP", "data_path": 'pose.bones["plate-settings"]["EyeCorrection"]'}
        ],"(0.00273934 * var) * var2")
        _rig_log.append("OK: Pupil driver RIGHT eye created successfully")
    except Exception as e:
        _rig_log.append(f"FAIL: Pupil driver RIGHT eye: {e}")

    # Both eyes separately to handle eyeless/eye patch chars
    try:
        add_driver_to_bone_transform("+EyeBoneA02.L", "scale", 0, variablesScale, "1.5556 * var + 1")
        add_driver_to_bone_transform("+EyeBoneA02.L", "scale", 1, variablesScale, "1.5556 * var + 1")
        add_driver_to_bone_transform("+EyeBoneA02.L", "scale", 2, variablesScale, "1.5556 * var + 1")
        
        # push back driver
        add_driver_to_bone_transform("+EyeBoneA02.L", "location", 1, [
            {"var_name": "var", "var_type":"TRANSFORMS", "target": "Wink-Control-L", "trans_space": "LOCAL_SPACE", "trans_type": "LOC_Y"},
            {"var_name": "var2", "var_type":"SINGLE_PROP", "data_path": 'pose.bones["plate-settings"]["EyeCorrection"]'}
        ],"(0.00273934 * var) * var2")
        _rig_log.append("OK: Pupil driver LEFT eye created successfully")
    except Exception as e:
        _rig_log.append(f"FAIL: Pupil driver LEFT eye: {e}")
    

    # Default limbs to IK mode (0.0) with zero stretch; controls stay native on limb gears (Genshin convention)
    rig_obj = bpy.data.objects.get(char_name + "Rig") or bpy.data.objects.get("rigify") or bpy.context.object
    if rig_obj and hasattr(rig_obj, "pose") and rig_obj.pose:
        for b_name in ["thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"]:
            pb = rig_obj.pose.bones.get(b_name)
            if pb:
                pb["IK_FK"] = 0.0
                pb["IK_Stretch"] = 0.0
        
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

    if "torso" in bpy.data.objects[char_name+"Rig"].pose.bones:
        if "head_follow" in bpy.data.objects[char_name+"Rig"].pose.bones["torso"]:
            bpy.data.objects[char_name+"Rig"].pose.bones["torso"]["head_follow"] = 0.0
        if "neck_follow" in bpy.data.objects[char_name+"Rig"].pose.bones["torso"]:
            bpy.data.objects[char_name+"Rig"].pose.bones["torso"]["neck_follow"] = 0.5
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
    
    def add_eye_bone_const(bone_name, to_bone):
        this_bone = bpy.context.scene.objects[char_name+"Rig"].pose.bones[bone_name]
        co = this_bone.constraints.new('COPY_ROTATION')
        co.target = our_char
        co.subtarget = to_bone
        co.target_space = "LOCAL_OWNER_ORIENT"
        co.owner_space = "LOCAL"

    try:
        final_eye_L_name = left_eye_bone_name if left_eye_bone_name else "+EyeBone L A01"
        final_eye_R_name = right_eye_bone_name if right_eye_bone_name else "+EyeBone R A01"
        add_eye_bone_const(final_eye_R_name, "+EyeBone R A01.001")
        add_eye_bone_const(final_eye_L_name, "+EyeBone L A01.001")

        # Clean leftover constraints targeting deleted eyetrack bones
        for eye_b in ["+EyeBone R A01.001", "+EyeBone L A01.001"]:
            eb_pb = bpy.context.scene.objects[ourRig].pose.bones.get(eye_b)
            if eb_pb:
                for c in list(eb_pb.constraints):
                    if getattr(c, "subtarget", None) in ["eyetrack", "eyetrack_L", "eyetrack_R"]:
                        eb_pb.constraints.remove(c)
    except:
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
            pb_h.custom_shape_scale_xyz = (0.05, 0.05, 0.05)

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

    # Face BG (only eye tracking bones remain; Brow/Eye/Mouth controls belong to the separate face rig)
    assign_bone_to_group("plate-settings", "Root")
    assign_bone_to_group("eyetrack", "Face")
    assign_bone_to_group("eyetrack_L", "Face")
    assign_bone_to_group("eyetrack_R", "Face")
    
    try:
        is_zzz = False
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.data.shape_keys and "Fac_Mth_Aa1" in o.data.shape_keys.key_blocks:
                is_zzz = True
                break

        if is_zzz:
            this_obj.pose.bones["eyetrack_L"].custom_shape_scale_xyz = (2,2,2)
            this_obj.pose.bones["eyetrack_R"].custom_shape_scale_xyz = (2,2,2)
            this_obj.pose.bones["eyetrack"].custom_shape_scale_xyz = (6.5,5,1)
        else:
            this_obj.pose.bones["eyetrack_L"].custom_shape_scale_xyz = (2,2,2)
            this_obj.pose.bones["eyetrack_R"].custom_shape_scale_xyz = (2,2,2)
            this_obj.pose.bones["eyetrack"].custom_shape_scale_xyz = (6.5,5,1)
    except:
        pass

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

    if "head-controller" in this_obj.pose.bones:
        this_obj.pose.bones["head-controller"]["parent_switch"] = 3
        try:
            this_obj.pose.bones["head-controller"].id_properties_ui("parent_switch").update(
                items=switch_parent_dropdown_items, default=3, description="Head Controller Parent"
            )
        except Exception:
            pass

    if "MCH-head-controller-parent" in this_obj.pose.bones:
        generate_switch_parent_constraints("MCH-head-controller-parent","head-controller")
    
    # REENABLE THE CONSTRAINT BELOW.
    for p_bone in ["forearm_tweak-pin.L", "forearm_tweak-pin.R", "shin_tweak-pin.L", "shin_tweak-pin.R"]:
        if p_bone in this_obj.pose.bones:
            this_obj.pose.bones[p_bone]["parent_switch"] = 3
            try:
                this_obj.pose.bones[p_bone].id_properties_ui("parent_switch").update(
                    items=switch_parent_dropdown_items, default=3, description=f"{p_bone} Parent"
                )
            except Exception:
                pass

    generate_switch_parent_constraints("MCH-forearm_tweak-pin.parent.L","forearm_tweak-pin.L")
    generate_switch_parent_constraints("MCH-forearm_tweak-pin.parent.R","forearm_tweak-pin.R")
    generate_switch_parent_constraints("MCH-shin_tweak-pin.parent.L","shin_tweak-pin.L")
    generate_switch_parent_constraints("MCH-shin_tweak-pin.parent.R","shin_tweak-pin.R")
            
    # For each tweak bone, we make the custom property, the constraint and driver.
    def prepare_tweak_bone(tweak_bone, pin_bone):
        # Make Custom Property
        cust_bone = this_obj.pose.bones[tweak_bone]
        cust_bone["tweak_pin"] = 0.00
        # Setting the min/max ranges: https://blender.stackexchange.com/a/258099
        id_prop = cust_bone.id_properties_ui("tweak_pin")
        id_prop.update(min=0.0,max=1.0)    
        cust_bone.property_overridable_library_set('["tweak_pin"]', True)    

        # Make Constraint
        con = this_obj.pose.bones[tweak_bone].constraints.new('COPY_LOCATION')
        con.target = our_char
        con.subtarget = pin_bone
        
        path_str = "pose.bones[\"" + tweak_bone+"\"][\"tweak_pin\"]"
        
        driver = con.driver_add("influence").driver
        driver.type = 'SUM'
        var = driver.variables.new()
        var.name = "bone"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = bpy.context.scene.objects[ourRig]
        var.targets[0].data_path = path_str
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
    
    prepare_tweak_bone("forearm_tweak.L", "forearm_tweak-pin.L")
    prepare_tweak_bone("forearm_tweak.R", "forearm_tweak-pin.R")
    prepare_tweak_bone("shin_tweak.L", "shin_tweak-pin.L")
    prepare_tweak_bone("shin_tweak.R", "shin_tweak-pin.R")
    
    # To repair the now missing custom property, let's remake it as a dropdown.
    def make_torso_custom():
        cust_bone = this_obj.pose.bones.get("torso-outer") or this_obj.pose.bones.get("torso")
        if not cust_bone:
            return
        cust_bone["torso_parent"] = 1
        try:
            id_prop = cust_bone.id_properties_ui("torso_parent")
            id_prop.update(items=[("P0", "None", ""), ("P1", "Root", "")], default=1)
        except Exception:
            pass
        try:
            cust_bone.property_overridable_library_set('["torso_parent"]', True) # allow library override of this bone
        except Exception:
            pass
    
    make_torso_custom()
    
    # rig_id also needs to be library overridable.
    bpy.data.armatures[original_name].property_overridable_library_set('["rig_id"]', True)
        
    # Adjustments to positioning
    this_obj.pose.bones["foot_ik.L"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-ik-pivot-L"]
    this_obj.pose.bones["foot_ik.R"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-ik-pivot-R"]
    this_obj.pose.bones["hand-ik-L"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-hand-ik-pivot-L"]
    this_obj.pose.bones["hand-ik-R"].custom_shape_transform = bpy.data.objects[char_name+"Rig"].pose.bones["mch-hand-ik-pivot-R"]
    
    # Align custom shape of hand IK controller bones (wrist) straight to center
    for b_name in ["hand-ik-L", "hand-ik-R", "hand_ik.L", "hand_ik.R", "hand_ik_wrist.L", "hand_ik_wrist.R"]:
        pb = this_obj.pose.bones.get(b_name)
        if pb and hasattr(pb, "custom_shape_rotation_euler"):
            pb.custom_shape_rotation_euler[0] = 0.0
            pb.custom_shape_rotation_euler[1] = 0.0
            pb.custom_shape_rotation_euler[2] = 0.0
    
    this_obj.pose.bones["ik-sub-pivot-L"].custom_shape_translation = (foot_L_x_diff*-1.0, 0.0, foot_L_z_diff*-1.0)
    this_obj.pose.bones["ik-sub-pivot-R"].custom_shape_translation = (foot_R_x_diff*-1.0, 0.0, foot_R_z_diff*-1.0)
   
    # thanks enthralpy for the code to delete the palm constraints that i fuckin forgot to do
    blist = ['ORG-palm.04.R', 'ORG-palm.03.R', 'ORG-palm.02.R', 'ORG-palm.04.L', 'ORG-palm.03.L', 'ORG-palm.02.L']

    for name in blist:
        try:
            bone = this_obj.pose.bones[name]
            # Create a list of all the constraints to be deleted on this bone
            get = [ c for c in bone.constraints if c.type == 'COPY_TRANSFORMS' ]
            fucked = [ c for c in bone.constraints if c.type == 'COPY_ROTATION' ]

            # Iterate over and delete them all
            for c in get:
                bone.constraints.remove( c ) 
            for c in fucked:
                bone.constraints.remove( c )
        except:
            pass
           
        
    # Penultimate: Rename bones as needed
    for oldname, newname in rename_bones_list:
        bone = this_obj.pose.bones.get(oldname)
        if bone is None:
            print(f"[RIG WARNING] Rename skipped: bone '{oldname}' not found")
            continue
        bone.name = newname
        print(f"[RIG OK] Renamed bone '{oldname}' -> '{newname}'")

    # Ensure prop.L, prop.R, and weapon bones are parented to root.002 so moving root.002 moves all weapons
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
                    eb_p = this_obj.data.edit_bones.get("prop.L" if ".l" in wb_name.lower() else "prop.R")
                    w_eb.parent = eb_p if eb_p else eb_r002
        bpy.ops.object.mode_set(mode='POSE')
    except Exception as e_parent_props:
        print(f"[ZZZ Rig Warning] Failed to ensure prop parenting to root.002: {e_parent_props}")
        try:
            bpy.ops.object.mode_set(mode='POSE')
        except Exception:
            pass 
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

    pb_torso = this_obj.pose.bones.get("torso")
    if pb_torso:
        try:
            d_hf = pb_torso.driver_add('["head_follow"]').driver
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
            d_nf = pb_torso.driver_add('["neck_follow"]').driver
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
        return '\n        if is_selected({"plate-settings"}):\n            layout.prop(pose_bones["plate-settings"], \'["Use Head Controller"]\', text="Use Head Tracker Controller", slider=True)\n            layout.prop(pose_bones["plate-settings"], \'["Head Follow"]\', text="Head Follow", slider=True)\n            layout.prop(pose_bones["plate-settings"], \'["Neck Follow"]\', text="Neck Follow", slider=True)\n            if "Skirt_Auto" in pose_bones["plate-settings"]:\n                layout.prop(pose_bones["plate-settings"], \'["Skirt_Auto"]\', text="Skirt Auto", slider=True)\n            if "Skirt_Follow" in pose_bones["plate-settings"]:\n                layout.prop(pose_bones["plate-settings"], \'["Skirt_Follow"]\', text="Skirt Follow", slider=True)\n            layout.prop(pose_bones["plate-settings"], \'["EyeCorrection"]\', text="Adjust Pupil Wink Distance", slider=True)'

    def generate_string_for_head_controller_slider():
        return '\n        if is_selected({"head-controller"}):\n            layout.prop(pose_bones["plate-settings"], \'["Use Head Controller"]\', text="Use Head Tracker Controller", slider=True)\n        if is_selected({"head"}):\n            layout.prop(pose_bones["plate-settings"], \'["Use Head Controller"]\', text="Use Head Tracker Controller", slider=True)'

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
            print(f"[ZZZ] drive_visibility_with_prop notice for {obj_name}: {ex}")
        
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
        bpy.context.object.data.layers[21] = True
        bpy.context.object.data.layers[22] = False
        bpy.context.object.data.layers[28] = True
        bpy.context.object.data.layers[26] = False
        bpy.context.object.data.collections["Tweaks"].is_visible = False
        if "Props" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Props"].is_visible = False
        if "Weapon" in bpy.context.object.data.collections:
            bpy.context.object.data.collections["Weapon"].is_visible = True
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
    
    # MOVING FACE (head-controller, eye tracking in Face collection, plate-settings in Root)
    bone_to_layer("plate-settings", 28, "Root")
    bone_to_layer("head-controller", 0, "Face")
    bone_to_layer("eyetrack", 0, "Face")
    bone_to_layer("eyetrack_L", 0, "Face")        
    bone_to_layer("eyetrack_R", 0, "Face")  
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
        
    try:
        bone_to_layer("+EyeBone L A01.001", 25, "Other")
        bone_to_layer("+EyeBone R A01.001", 25, "Other")
    except:
        pass
               
    if no_eyes:
        bone_to_layer("eyetrack",25,"Other")
        bone_to_layer("eyetrack_L",25,"Other")
        bone_to_layer("eyetrack_R",25,"Other")
           
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

    # Catch any remaining weapon bones (excluding back/spine weaponbox)
    for b in loop_arm.bones:
        b_low = b.name.lower()
        if "box" in b_low or "weaponbox" in b_low:
            continue
        if any(k in b_low for k in ["prop1", "prop2", "weapon", "equip"]):
            bone_to_layer(b.name, 21, "Weapon")

    # Ensure all face bones (slider-, frame-, eyetrack, plate-, Face-, Wink, etc.) are in Face (excluding plate-settings which is Root)
    for b in loop_arm.bones:
        b_low = b.name.lower()
        if "plate-settings" in b_low:
            continue
        if any(k in b_low for k in ["slider-", "frame-", "eyetrack", "brow-", "eye-", "mouth-", "plate-", "face-", "wgt-eye", "wink"]):
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
            colls["Weapon"].is_visible = True

    # MOVING OF BONES END -------------------------------    

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
    
def setup_neck_and_head_follow(neck_follow_value=0.0, head_follow_value=0.0):
    if bpy.context.object and hasattr(bpy.context.object, "pose") and bpy.context.object.pose and "torso" in bpy.context.object.pose.bones:
        torso_pb = bpy.context.object.pose.bones["torso"]
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
