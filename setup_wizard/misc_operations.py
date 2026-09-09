# Author: michael-gh1
# With modified scripts for PGR Operators from JaredNyts and SilentNightSound

import os
import re
import bpy
from bpy.types import Material, Operator

from setup_wizard.domain.game_types import GameType
from setup_wizard.domain.shader_identifier_service import HonkaiStarRailShaders, ShaderIdentifierService, ShaderIdentifierServiceFactory
from setup_wizard.domain.shader_material_names import JaredNytsPunishingGrayRavenShaderMaterialNames, Nya222HonkaiStarRailShaderMaterialNames, ShaderMaterialNames, StellarToonShaderMaterialNames
from setup_wizard.import_order import NextStepInvoker
from setup_wizard.setup_wizard_operator_base_classes import CustomOperatorProperties
from setup_wizard.texture_import_setup.texture_node_names import TextureNodeNames


class GI_OT_SetColorManagementToStandard(Operator, CustomOperatorProperties):
    '''Sets Color Management to Standard'''
    bl_idname = 'genshin.set_color_management_to_standard'
    bl_label = 'Genshin: Set Color Management to Standard'

    def execute(self, context):
        bpy.context.scene.view_settings.view_transform = 'Standard'

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


class HYV_OT_SetUpScreenSpaceReflections(Operator, CustomOperatorProperties):
    '''Sets Up Screen Space Reflections'''
    bl_idname = 'hoyoverse.set_up_screen_space_reflections'
    bl_label = 'HoYoverse: Set Up Screen Space Reflections'

    def execute(self, context):
        eevee = context.scene.eevee
        # Blender 4.2+ / Blender 5.x EEVEE Next Raytracing
        if hasattr(eevee, "use_raytracing"):
            try:
                eevee.use_raytracing = True
            except Exception as e:
                print(f"Notice: Setting use_raytracing: {e}")
        if hasattr(eevee, "raytracing_method"):
            try:
                eevee.raytracing_method = 'SCREEN_SPACE'
            except Exception as e:
                print(f"Notice: Setting raytracing_method: {e}")

        # Blender 4.1 and earlier EEVEE SSR
        if hasattr(eevee, "use_ssr"):
            try:
                eevee.use_ssr = True
                eevee.use_ssr_refraction = True
            except Exception as e:
                print(f"Notice: Setting use_ssr: {e}")

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


class HYV_OT_VertexPaintFaceSeeThroughEffect(Operator, CustomOperatorProperties):
    '''Vertex Paint Face'''
    bl_idname = 'hoyoverse.vertex_paint_face_see_through_effect'
    bl_label = 'HoYoverse: Vertex Paint Face for See Through Effect'

    def execute(self, context):
        shader_identifier_service = ShaderIdentifierServiceFactory.create(self.game_type)
        shader = shader_identifier_service.identify_shader(bpy.data.materials, bpy.data.node_groups)
        self.shader_material_names = Nya222HonkaiStarRailShaderMaterialNames if \
            shader is HonkaiStarRailShaders.NYA222_HONKAI_STAR_RAIL_SHADER else \
            StellarToonShaderMaterialNames

        face_object = bpy.data.objects.get('Face')
        face_mesh: bpy.types.Mesh = bpy.data.meshes.get('Face')

        if shader is HonkaiStarRailShaders.STELLARTOON_HONKAI_STAR_RAIL_SHADER and face_mesh and face_object:
            color_color_attribute = face_mesh.color_attributes.get('Color')
            orig_active_obj = bpy.context.active_object
            orig_mode = orig_active_obj.mode if orig_active_obj else 'OBJECT'

            if not color_color_attribute:
                color_color_attribute = face_mesh.color_attributes.new(
                    name='Color',
                    type='FLOAT_COLOR',
                    domain='POINT'
                )
                for v_index in range(len(face_object.data.vertices)):
                    color_color_attribute.data[v_index].color = [0, 0, 0, 1]
            face_mesh.attributes.active_color = color_color_attribute

            col_color_attribute = face_mesh.vertex_colors.get('Col')
            if col_color_attribute:
                col_color_attribute.active_render = True

            try:
                bpy.context.view_layer.objects.active = face_object
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')

                # Try first slot as a best guess (Screwllum has Body1 material in Face mesh)
                face_material_slot = face_object.material_slots.get(self.shader_material_names.FACE) or (
                    face_object.material_slots[0] if face_object.material_slots else None
                )
                if face_material_slot:
                    face_object.active_material_index = face_material_slot.slot_index

                bpy.ops.mesh.select_all(action='DESELECT')
                if face_material_slot:
                    bpy.ops.object.material_slot_select()

                bpy.ops.paint.vertex_paint_toggle()
                face_mesh.use_paint_mask = True
                if "Draw" in bpy.data.brushes:
                    bpy.data.brushes["Draw"].color = (1, 1, 1)
                bpy.ops.paint.vertex_color_set()
            except Exception as e:
                print(f"[HSR] Vertex paint face see through error: {e}")
            finally:
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except Exception:
                    pass

            if orig_active_obj and orig_active_obj.name in bpy.data.objects:
                try:
                    bpy.context.view_layer.objects.active = orig_active_obj
                    if orig_mode in ('POSE', 'EDIT', 'OBJECT'):
                        bpy.ops.object.mode_set(mode=orig_mode)
                except Exception:
                    pass

            self.__replace_eyeshadow_material()

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}

    def __replace_eyeshadow_material(self):
        face_meshes = [
            obj for obj in bpy.data.objects 
            if obj.type == 'MESH' and ('face' in obj.name.lower() or 'head' in obj.name.lower())
        ]
        if not face_meshes:
            face_mesh = bpy.data.objects.get('Face')
            if face_mesh:
                face_meshes = [face_mesh]

        eyeshadow_mat = None
        if hasattr(self.shader_material_names, 'EYESHADOW'):
            eyeshadow_mat = bpy.data.materials.get(self.shader_material_names.EYESHADOW)
        
        if not eyeshadow_mat:
            # Look for shader EyeShadow material (excluding default FBX raw materials like Mat_EyeShadow_00)
            for mat in bpy.data.materials:
                if 'EyeShadow' in mat.name and not mat.name.startswith('Mat_') and mat.name != 'EyeShadow':
                    eyeshadow_mat = mat
                    break
            if not eyeshadow_mat:
                for mat in bpy.data.materials:
                    if 'EyeShadow' in mat.name and mat.name != 'Mat_EyeShadow_00':
                        eyeshadow_mat = mat
                        break

        for face_mesh in face_meshes:
            for material_slot in face_mesh.material_slots:
                if material_slot.material and ('EyeShadow' in material_slot.material.name or 'eyeshadow' in material_slot.material.name.lower()):
                    if eyeshadow_mat:
                        material_slot.material = eyeshadow_mat
                    elif hasattr(self.shader_material_names, 'FACE'):
                        face_mat = bpy.data.materials.get(self.shader_material_names.FACE)
                        if face_mat:
                            material_slot.material = face_mat


class GI_OT_DeleteSpecificObjects(Operator, CustomOperatorProperties):
    '''Cleans up extra meshes'''
    bl_idname = 'genshin.delete_specific_objects'
    bl_label = 'Genshin: Clean up extra meshes'

    def execute(self, context):
        scene = bpy.context.scene
        objects_to_delete = [
            'HairVat',  # Mavuika
            'HairEffect_Vat',  # Mavuika
            'EffectMesh',  # Also, Mavuika: HairEffectMesh
        ]  # be extremely careful, we will be deleting anything that contains these object names
        delete_objects_that_start_with = [
            'AO_',  # Furina (Default)
        ]

        for object in scene.objects:
            for object_to_delete in objects_to_delete:
                if object_to_delete in object.name and object.type == 'MESH':
                    bpy.data.objects.remove(object)
                    break

        # lazy separate for-loop because object may already be deleted when reaching second for-loop
        for object in scene.objects:
            for object_start_with in delete_objects_that_start_with:
                if object.name.startswith(object_start_with) and object.type == 'MESH':
                    bpy.data.objects.remove(object)

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


class GI_OT_RenameShaderMaterials(Operator, CustomOperatorProperties):
    '''Renames Shader Materials with Character Names'''
    bl_idname = 'hoyoverse.rename_shader_materials'
    bl_label = 'HoYoverse: Rename Shader Materials'

    def execute(self, context):
        shader_identifier_service: ShaderIdentifierService = ShaderIdentifierServiceFactory.create(self.game_type)
        shader_material_names = shader_identifier_service.get_shader_material_names(
            self.game_type, bpy.data.materials, bpy.data.node_groups
        )
        shader = shader_identifier_service.identify_shader(bpy.data.materials, bpy.data.node_groups)
        shader_material_names = shader_identifier_service.get_shader_material_names_using_shader(shader)

        # 1. GI, PGR
        # 2. HSR-Nya222
        # 3. HSR-StellarToon
        body_material: Material = bpy.data.materials.get(shader_material_names.BODY) or \
            bpy.data.materials.get(shader_material_names.BODY1) or bpy.data.materials.get(shader_material_names.BASE)
        texture_node_names: TextureNodeNames = shader_identifier_service.get_shader_texture_node_names(shader)

        body_diffuse_node_name = self.__get_body_diffuse_node_name(body_material, texture_node_names)

        if body_material and body_diffuse_node_name:
            body_diffuse_texture = body_material.node_tree.nodes.get(body_diffuse_node_name).image
            if body_diffuse_texture:
                materials_to_check = [material for material in bpy.data.materials if \
                                    material.name.startswith(shader_material_names.MATERIAL_PREFIX)]
                for material in materials_to_check:
                    self.__set_material_names(self.game_type, material, shader_material_names, body_diffuse_texture.name)

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}

    # TODO: Oof, this should be refactored, but it's a little tricky with Genshin Shader v4.0
    # We could create a shared variable across all TextureNodeNames, but we need to be able to differentiate v3 from v4.0
    def __get_body_diffuse_node_name(self, material, texture_node_names: TextureNodeNames):
        body_diffuse_node_names = [
            texture_node_names.BODY_DIFFUSE_UV0,  # Genshin
            texture_node_names.MAIN_DIFFUSE,  # Genshin >= v4.0
            # StellarToon before common shaders is important!!!
            # We need to check StellarToon before the others otherwise it may attempt to provide the incorrect
            # body_diffuse_uv0_node_name, this is because texture_node_names.DIFFUSE is common across StellarToon AND
            # other common diffuse node names.
            f'Body{texture_node_names.DIFFUSE_UV0_SUFFIX}' if texture_node_names.DIFFUSE_UV0_SUFFIX else '',  # StellarToon
            texture_node_names.DIFFUSE,  # Nya222/PGR -- # Keep on bottom as last check, catch-all common shader diffuse name
        ]

        for node_name in body_diffuse_node_names:
            if material and material.node_tree.nodes.get(node_name):
                return node_name

    def __set_material_names(self, game_type: GameType, material: Material, shader_material_names: ShaderMaterialNames, body_diffuse_filename):
        if game_type == GameType.HONKAI_STAR_RAIL.name:
            character_name = body_diffuse_filename.split('_')[1]
        elif game_type == GameType.GENSHIN_IMPACT.name:
            body_diffuse_filename_lowercased = body_diffuse_filename.lower()
            if 'monster' in body_diffuse_filename_lowercased:
                monster_start_index = body_diffuse_filename_lowercased.index('monster')
                character_name = body_diffuse_filename[monster_start_index:].split('_')[1]
            else:
                character_name = body_diffuse_filename.split('_')[3]
        elif game_type == GameType.PUNISHING_GRAY_RAVEN.name:
            armature =  [object for object in bpy.data.objects if object.type == 'ARMATURE'][0]
            character_name = armature.name
        else:
            return
        second_half_of_material_prefix = shader_material_names.MATERIAL_PREFIX.split('-')[1]
        material.name = material.name.replace(f'-{second_half_of_material_prefix}', f'- {character_name} ')


class GI_OT_SetUpArmTwistBoneConstraints(Operator, CustomOperatorProperties):
    '''Sets Up ArmTwist Bone Constraints'''
    bl_idname = 'genshin.set_up_armtwist_bone_constraints'
    bl_label = 'Genshin: Set Up ArmTwist Bone Constraints'

    ARMTWIST_A01_INFLUENCE = 0.35
    ARMTWIST_A02_INFLUENCE = 0.65

    # Genshin Impact / Honkai Star Rail
    LEFT_ARMTWIST_A01 = '+UpperArmTwist L A01'
    LEFT_ARMTWIST_A02 = '+UpperArmTwist L A02'
    RIGHT_ARMTWIST_A01 = '+UpperArmTwist R A01'
    RIGHT_ARMTWIST_A02 = '+UpperArmTwist R A02'

    LEFT_FOREARM = 'Bip001 L Forearm'
    RIGHT_FOREARM = 'Bip001 R Forearm'

    # Punishing Gray Raven
    LEFT_UPPERARM_TWIST = 'BoneLUpperArmTwist'
    LEFT_FOREARM_TWIST = 'BoneLForeArmTwist'
    RIGHT_UPPERARM_TWIST = 'BoneRUpperArmTwist'
    RIGHT_FOREARM_TWIST = 'BoneRForeArmTwist'

    LEFT_FOREARM = 'Bip001LForearm'
    RIGHT_FOREARM = 'Bip001RForearm'

    def execute(self, context):
        armature =  [object for object in bpy.data.objects if object.type == 'ARMATURE'][0]
        left_armtwist_bone_names, right_armtwist_bone_names = self.get_armtwist_bones()

        self.reorient_armtwist_bones(armature, left_armtwist_bone_names, self.LEFT_FOREARM)
        self.reorient_armtwist_bones(armature, right_armtwist_bone_names, self.RIGHT_FOREARM)
        self.set_up_armtwist_bone_constraints(armature)

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}

    def get_armtwist_bones(self):
        if self.game_type == GameType.PUNISHING_GRAY_RAVEN.name:
            left_armtwist_bone_names = [
                self.LEFT_UPPERARM_TWIST,
                self.LEFT_FOREARM_TWIST,
            ]
            right_armtwist_bone_names = [
                self.RIGHT_UPPERARM_TWIST,
                self.RIGHT_FOREARM_TWIST,
            ]
        else:
            left_armtwist_bone_names = [
                self.LEFT_ARMTWIST_A01,
                self.LEFT_ARMTWIST_A02,
            ]
            right_armtwist_bone_names = [
                self.RIGHT_ARMTWIST_A01,
                self.RIGHT_ARMTWIST_A02,
            ]
        return (left_armtwist_bone_names, right_armtwist_bone_names)

    def set_up_armtwist_bone_constraints(self, armature):
        if self.game_type == GameType.PUNISHING_GRAY_RAVEN.name:
            self.set_up_armtwist_bone_constraint(armature, self.LEFT_UPPERARM_TWIST, self.LEFT_FOREARM, self.ARMTWIST_A01_INFLUENCE)
            # self.set_up_armtwist_bone_constraint(armature, self.LEFT_FOREARM_TWIST, self.LEFT_FOREARM, self.ARMTWIST_A02_INFLUENCE)
            self.set_up_armtwist_bone_constraint(armature, self.RIGHT_UPPERARM_TWIST, self.RIGHT_FOREARM, self.ARMTWIST_A01_INFLUENCE)
            # self.set_up_armtwist_bone_constraint(armature, self.RIGHT_FOREARM_TWIST, self.RIGHT_FOREARM, self.ARMTWIST_A02_INFLUENCE)
        else:
            self.set_up_armtwist_bone_constraint(armature, self.LEFT_ARMTWIST_A01, self.LEFT_FOREARM, self.ARMTWIST_A01_INFLUENCE)
            self.set_up_armtwist_bone_constraint(armature, self.LEFT_ARMTWIST_A02, self.LEFT_FOREARM, self.ARMTWIST_A02_INFLUENCE)
            self.set_up_armtwist_bone_constraint(armature, self.RIGHT_ARMTWIST_A01, self.RIGHT_FOREARM, self.ARMTWIST_A01_INFLUENCE)
            self.set_up_armtwist_bone_constraint(armature, self.RIGHT_ARMTWIST_A02, self.RIGHT_FOREARM, self.ARMTWIST_A02_INFLUENCE)

    def reorient_armtwist_bones(self, armature, bone_names, target_bone_name):
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        for bone_name in bone_names:
            bone = armature.data.edit_bones.get(bone_name)
            target_bone = armature.data.edit_bones.get(target_bone_name)

            if bone and target_bone:
                original_bone_length = bone.length
                bone.tail = target_bone.head
                bone.length = original_bone_length

        bpy.ops.object.mode_set(mode='OBJECT')

    def set_up_armtwist_bone_constraint(self, armature, bone_name, subtarget_bone_name, influence):
        armature_bones = armature.pose.bones
        twist_bone = armature_bones.get(bone_name)

        if twist_bone and subtarget_bone_name:
            copy_rotation_constraint = twist_bone.constraints.new('COPY_ROTATION')
            copy_rotation_constraint.target = armature
            copy_rotation_constraint.subtarget = subtarget_bone_name
            copy_rotation_constraint.use_x = False
            copy_rotation_constraint.use_z = False
            copy_rotation_constraint.target_space = 'LOCAL'
            copy_rotation_constraint.owner_space = 'LOCAL'
            copy_rotation_constraint.influence = influence
            return copy_rotation_constraint


class PGR_OT_PaintVertexColors(Operator, CustomOperatorProperties):
    '''Paint Vertex Colors'''
    bl_idname = 'punishing_gray_raven.paint_vertex_colors'
    bl_label = 'Punishing Gray Raven: Paint Vertex Colors'

    def execute(self, context):
        meshes = bpy.data.meshes.values()
        for mesh in meshes:
            if not mesh.vertex_colors:
                mesh.vertex_colors.new()
            color_layer = mesh.vertex_colors.get('Col')

            if not color_layer:
                continue

            color_layer_index = 0
            for poly in mesh.polygons:
                for indice in poly.loop_indices:  # Yes, indice is intentionally unused
                    color_layer.data[color_layer_index].color = (1, 0.502, 0.502,0.5)  # RGBA (original author wrote AGBR ??)
                    color_layer_index += 1

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


class PGR_OT_PaintFaceShadowTexture(Operator, CustomOperatorProperties):
    '''Paint Vertex Colors'''
    bl_idname = 'punishing_gray_raven.paint_face_shadow_texture'
    bl_label = 'Punishing Gray Raven: Paint Face Shadow Texture'

    def execute(self, context):
        face_material = [material for material in bpy.data.materials.values() if \
                         material.name.startswith(JaredNytsPunishingGrayRavenShaderMaterialNames.MATERIAL_PREFIX) and material.name.endswith('Face')][0]
        face_material.node_tree.nodes.get('Image Texture').select = True

        # The outlines must be disabled on viewport for texture painting to work! (not sure why)
        meshes = [obj for obj in bpy.data.objects.values() if obj.type == 'MESH']
        for mesh in meshes:
            modifiers = [modifier for modifier in mesh.modifiers.values() if 'Outlines' in modifier.name]
            for modifier in modifiers:
                modifier.show_viewport = False

        # 1. Select the face mesh
        # 2. Go to Edit Mode
        # 3. Select all the faces of Face and Ears (do not touch eyes, eyelashes etc.)
        bpy.ops.paint.texture_paint_toggle()
        bpy.context.object.data.use_paint_mask = True
        bpy.ops.paint.face_select_all(action='INVERT')
        bpy.data.brushes["TexDraw"].color = (0.744, 0.744, 0.744)
        bpy.context.scene.tool_settings.unified_paint_settings.size = 500

        # Press LMB on the face to texture paint onto the Face Shadow texture
        # This paints the 'Face Shadow' texture and preps for usage when we erase the outlines in the next step
        # Then run PGR_OT_VertexPaintEraseFaceAlpha (Erase Face Alpha)

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


class PGR_OT_PaintVertexEraseFaceAlpha(Operator, CustomOperatorProperties):
    '''Paint Vertex Colors'''
    bl_idname = 'punishing_gray_raven.paint_vertex_erase_face_alpha'
    bl_label = 'Punishing Gray Raven: Paint Vertex Colors'

    def execute(self, context):
        # The outlines must be enabled on viewport for erasing to work! (not sure why)
        meshes = [obj for obj in bpy.data.objects.values() if obj.type == 'MESH']
        for mesh in meshes:
            for modifier in mesh.modifiers.values():
                modifier.show_viewport = True

        # 'Col' color attribute/vertex color must be selected as active!
        face_mesh = [mesh for mesh in bpy.data.meshes.values() if 'Face' in mesh.name][0]  # expecting Face mesh
        face_mesh.vertex_colors['Col'].active = True

        bpy.ops.paint.vertex_paint_toggle()
        bpy.context.object.data.use_paint_mask = True
        bpy.data.brushes["Draw"].blend = 'ERASE_ALPHA'
        bpy.context.scene.tool_settings.unified_paint_settings.size = 500
        bpy.data.brushes["Draw"].strength = 1
        bpy.data.brushes["Draw"].use_frontface = False
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'

        # Tap on the face once to erase the outlines on the eyes and lips

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


class ZZZ_OT_RenameCollectionAndRig(Operator, CustomOperatorProperties):
    """Renames character collection and rig to character name"""
    bl_idname = 'zenless_zone_zero.rename_collection_and_rig'
    bl_label = 'ZZZ: Rename Collection & Rig'

    def _get_character_name(self):
        return get_clean_character_name()

    def _find_character_collection(self):
        return find_zzz_character_collection()

    def _find_character_armature(self):
        return find_zzz_character_armature()

    def execute(self, context):
        char_name = self._get_character_name()
        if char_name and char_name.lower() not in ["character", "eye", "eyes", "wgt", "lights"]:
            target_coll = self._find_character_collection()
            if target_coll:
                target_coll.name = char_name

            arm_obj = self._find_character_armature()
            if arm_obj:
                arm_obj.name = f"{char_name}Rig"
                if arm_obj.data:
                    arm_obj.data.name = f"{char_name}Rig"

        # Unlink wgt and lights collections from scene
        unlink_all_wgt_and_lights_from_scene()

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}


def get_clean_character_name():
    from setup_wizard.character_rig_setup.rig_ui_utils import extract_clean_character_name
    from setup_wizard.import_order import CHARACTER_MODEL_FOLDER_FILE_PATH, get_cache

    # 1. From FBX file path stored in scene or cache
    fbx_path = (
        bpy.context.scene.get("setup_wizard_imported_fbx_path")
        or bpy.context.scene.get("setup_wizard_imported_model_dir")
        or get_cache(True).get(CHARACTER_MODEL_FOLDER_FILE_PATH)
        or ""
    )
    if fbx_path:
        base_name = os.path.splitext(os.path.basename(fbx_path))[0]
        extracted = extract_clean_character_name(base_name)
        if extracted and extracted.lower() not in ["character", "eye", "eyes", "lighting", "panel", "wgt", "lights"]:
            return extracted

    # 2. From Mesh objects (e.g. Avatar_Female_Size02_Alice_UI)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            o_name = obj.name
            if any(k in o_name for k in ["Avatar_", "Size0", "Bdy_", "Skn_", "Face_", "Hair_"]):
                extracted = extract_clean_character_name(o_name)
                if extracted and extracted.lower() not in ["character", "eye", "eyes", "lighting", "panel", "wgt", "lights"]:
                    return extracted

    # 3. From Materials (e.g. "ZZZ Shader Alice_Body_2" -> "Alice")
    for mat in bpy.data.materials:
        if "Shader" in mat.name and not mat.name.startswith("Shader"):
            clean = mat.name.split("Shader")[-1].strip()
            extracted = extract_clean_character_name(clean)
            if extracted and extracted.lower() not in ["character", "eye", "eyes", "lighting", "panel", "wgt", "lights"]:
                return extracted

    # 4. From Armature objects (excluding Eye, Lighting Panel, metarig, rig)
    ignore_arm = {"lighting panel", "light panel", "panel", "light direction", "head direction", "metarig", "wgt", "eyerig", "facerig", "eye", "eyes", "lights"}
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            o_lower = obj.name.lower()
            if any(ign in o_lower for ign in ignore_arm):
                continue
            extracted = extract_clean_character_name(obj.name)
            if extracted and extracted.lower() not in ["character", "eye", "eyes", "lighting", "panel", "wgt", "lights"]:
                return extracted

    # 5. From Collections
    for coll in bpy.data.collections:
        c_low = coll.name.lower()
        if c_low.startswith("wgt") or (c_low.startswith("wgts_") and c_low != "wgts_facerig"):
            continue
        if coll.name.lower() not in ["lights", "wgt", "wgts", "collection", "master collection", "eye", "eyes"]:
            extracted = extract_clean_character_name(coll.name)
            if extracted and extracted.lower() not in ["character", "eye", "eyes", "lighting", "panel", "wgt", "lights"]:
                return extracted

    return "Character"


def unlink_all_wgt_and_lights_from_scene():
    target_names = {"wgt", "wgts", "lights", "lighting panel wgt"}
    for coll in list(bpy.data.collections):
        c_low = coll.name.lower()
        # Preserve per-character WGTS_<Char> nested in the character collection
        # (Append-safe widget isolation). Only legacy globals get unlinked.
        if c_low.startswith("wgts_") and c_low != "wgts_facerig":
            continue
        if c_low in target_names or c_low.startswith("wgt") or c_low.endswith("wgt"):
            # Unlink from scene root collection
            if coll.name in bpy.context.scene.collection.children:
                try:
                    bpy.context.scene.collection.children.unlink(coll)
                except Exception:
                    pass
            # Unlink from all parent collections in the scene
            for parent in list(bpy.data.collections):
                if parent != coll and coll.name in parent.children:
                    try:
                        parent.children.unlink(coll)
                    except Exception:
                        pass


def find_zzz_character_armature():
    ignore_names = {"lighting panel", "light panel", "panel", "light direction", "head direction", "metarig", "wgt", "eyerig", "facerig", "eye", "eyes", "lights"}
    # 1. Look for rig ending with 'Rig' or named with character name
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            o_lower = obj.name.lower()
            if any(ign in o_lower for ign in ignore_names):
                continue
            if obj.name.endswith("Rig") or "rig" in o_lower:
                return obj

    # 2. Look for armature containing main body bones
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            o_lower = obj.name.lower()
            if any(ign in o_lower for ign in ignore_names):
                continue
            if obj.data and any(b in obj.data.bones for b in ["head", "spine", "hips", "root", "DEF-spine.006"]):
                return obj

    # 3. Fallback
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            o_lower = obj.name.lower()
            if any(ign in o_lower for ign in ignore_names):
                continue
            return obj
    return None


def _is_wgt_or_lights_collection(name):
    n_low = name.lower()
    return (
        n_low in ["lights", "wgt", "wgts", "collection", "master collection", "eye", "eyes"]
        or n_low.startswith("wgt")
        or n_low.startswith("wgts_")
    )


def find_zzz_character_collection():
    for coll in bpy.data.collections:
        if coll.name.lower() not in ["lights", "wgt", "wgts", "collection", "master collection", "eye", "eyes"] and ("Avatar_" in coll.name or "Size" in coll.name):
            return coll
    for coll in bpy.data.collections:
        if _is_wgt_or_lights_collection(coll.name):
            continue
        return coll
    for coll in bpy.data.collections:
        c_low = coll.name.lower()
        if c_low.startswith("wgt") or (c_low.startswith("wgts_") and c_low != "wgts_facerig"):
            continue
        if coll.name.lower() not in ["lights", "wgt", "wgts", "eye", "eyes"]:
            return coll
    return None


class ZZZ_OT_MoveLightingPanelToCharacterCollection(Operator, CustomOperatorProperties):
    """Moves ONLY Lighting Panel armature into character collection while leaving WGTs in lights"""
    bl_idname = 'zenless_zone_zero.move_lighting_panel_to_char_collection'
    bl_label = 'ZZZ: Move Lighting Panel to Character Collection'

    def _find_character_armature(self):
        return find_zzz_character_armature()

    def _find_character_collection(self):
        return find_zzz_character_collection()

    def execute(self, context):
        # 1. Merge secondary armatures (Eye / FaceRig, Lighting Panel) into main character rig
        main_rig = find_zzz_character_armature()
        if main_rig:
            try:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

            # Merge Eye / Face rig and Lighting Panel rig
            for obj in list(bpy.data.objects):
                if obj.type == 'ARMATURE' and obj != main_rig and obj.name != main_rig.name:
                    o_l = obj.name.lower()
                    if any(k in o_l for k in ["lighting", "panel", "facerig", "isaac", "eye", "face"]):
                        try:
                            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                                bpy.ops.object.mode_set(mode='OBJECT')
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)
                            main_rig.select_set(True)
                            bpy.context.view_layer.objects.active = main_rig
                            bpy.ops.object.join()
                            print(f"[ZZZ] Joined '{obj.name}' into '{main_rig.name}'")
                        except Exception as ex:
                            print(f"[ZZZ] Armature merge warning: {ex}")

        # 2. Ensure all ColorWheel meshes are ONLY in character collection and not in lights/wgt
        target_coll = self._find_character_collection() or self._find_target_collection()
        if target_coll:
            for obj in bpy.data.objects:
                if "colorwheel" in obj.name.lower():
                    if obj.name not in target_coll.objects:
                        target_coll.objects.link(obj)
                    for coll in list(obj.users_collection):
                        if coll != target_coll:
                            try:
                                coll.objects.unlink(obj)
                            except Exception:
                                pass
                    obj.hide_viewport = False
                    obj.hide_render = False

            for coll in bpy.data.collections:
                if coll != target_coll:
                    for obj in list(coll.objects):
                        if "colorwheel" in obj.name.lower():
                            try:
                                coll.objects.unlink(obj)
                            except Exception:
                                pass

        # Desvincular / excluir la colección 'lights' de la escena activa (view layer)
        def exclude_layer_collection(layer_coll, name):
            if layer_coll.name == name or layer_coll.collection.name == name:
                layer_coll.exclude = True
                return True
            for child in layer_coll.children:
                if exclude_layer_collection(child, name):
                    return True
            return False

        try:
            exclude_layer_collection(context.view_layer.layer_collection, "lights")
        except Exception:
            pass

        self.report({"INFO"}, "Zenless Zone Zero: Finish Setup Completed Successfully!")

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {'FINISHED'}

    def _find_target_collection(self):
        for coll in bpy.data.collections:
            if coll.name not in ["lights", "wgt", "WGTS", "Collection", "Master Collection"]:
                return coll
        return None


register, unregister = bpy.utils.register_classes_factory([
    GI_OT_SetColorManagementToStandard,
    HYV_OT_SetUpScreenSpaceReflections,
    HYV_OT_VertexPaintFaceSeeThroughEffect,
    GI_OT_DeleteSpecificObjects,
    GI_OT_RenameShaderMaterials,
    GI_OT_SetUpArmTwistBoneConstraints,
    PGR_OT_PaintVertexColors,
    PGR_OT_PaintFaceShadowTexture,
    PGR_OT_PaintVertexEraseFaceAlpha,
    ZZZ_OT_RenameCollectionAndRig,
    ZZZ_OT_MoveLightingPanelToCharacterCollection,
])
