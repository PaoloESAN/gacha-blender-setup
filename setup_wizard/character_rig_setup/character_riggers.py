# Author: michael-gh1

import re
import bpy
import os

from setup_wizard.domain.shader_material_names import ShaderMaterialNames, V2_FestivityGenshinImpactMaterialNames, V3_BonnyFestivityGenshinImpactMaterialNames, V4_PrimoToonGenshinImpactMaterialNames
from setup_wizard.domain.shader_identifier_service import GenshinImpactShaders, ShaderIdentifierService, ShaderIdentifierServiceFactory
from setup_wizard.character_rig_setup.lighting_panel_setup import LightingPanel, LightingPanelFileNames, LightingPanelFileNamesFactory
from setup_wizard.character_rig_setup.rig_script import rig_character
from setup_wizard.character_rig_setup.npc_rig_script import rig_character as rig_npc
from setup_wizard.character_rig_setup.hsr_rig_script import rig_character as hsr_rig_character
from setup_wizard.character_rig_setup.zzz_rig_script import rig_character as zzz_rig_character
from setup_wizard.character_rig_setup.nte_rig_script import rig_character as nte_rig_character
from setup_wizard.character_rig_setup.wuwa_rig_script import rig_wuthering_waves_character
from setup_wizard.character_rig_setup.ake_rig_script import rig_character as ake_rig_character
from setup_wizard.character_rig_setup.zzz_face_rig import zzz_face_rig_main


from abc import ABC, abstractmethod
from bpy.types import Armature, Operator, Context

from setup_wizard.domain.game_types import GameType
from setup_wizard.import_order import GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH, NextStepInvoker, cache_using_cache_key, \
    get_cache

from setup_wizard.character_rig_setup.character_rigger_props import CharacterRiggerPropertyGroup
from setup_wizard.texture_import_setup.texture_node_names import TextureNodeNames, V1_GenshinImpactTextureNodeNames, V2_GenshinImpactTextureNodeNames, V3_GenshinImpactTextureNodeNames, V4_GenshinImpactTextureNodeNames
from setup_wizard.utils.modifier_utils import get_modifier_property, set_modifier_property

class CharacterRiggerFactory:
    def create(game_type: GameType, blender_operator: Operator, context: Context):
        shader_identifier_service: ShaderIdentifierService = ShaderIdentifierServiceFactory.create(game_type)
        shader = shader_identifier_service.identify_shader(bpy.data.materials, bpy.data.node_groups)
        if game_type == GameType.GENSHIN_IMPACT.name:
            if shader is GenshinImpactShaders.V1_GENSHIN_IMPACT_SHADER:
                material_names = V2_FestivityGenshinImpactMaterialNames
                texture_node_names = V1_GenshinImpactTextureNodeNames
            elif shader is GenshinImpactShaders.V2_GENSHIN_IMPACT_SHADER:
                material_names = V2_FestivityGenshinImpactMaterialNames
                texture_node_names = V2_GenshinImpactTextureNodeNames
            elif shader is GenshinImpactShaders.V3_GENSHIN_IMPACT_SHADER:
                material_names = V3_BonnyFestivityGenshinImpactMaterialNames
                texture_node_names = V3_GenshinImpactTextureNodeNames
            else:
                material_names = V4_PrimoToonGenshinImpactMaterialNames
                texture_node_names = V4_GenshinImpactTextureNodeNames
            return GenshinImpactCharacterRigger(blender_operator, context, material_names, texture_node_names, shader)
        elif game_type == GameType.HONKAI_STAR_RAIL.name:
            return HonkaiStarRailCharacterRigger(blender_operator, context)
        elif game_type == GameType.PUNISHING_GRAY_RAVEN.name:
            return PunishingGrayRavenCharacterRigger(blender_operator, context)
        elif game_type == GameType.ZENLESS_ZONE_ZERO.name:
            return ZenlessZoneZeroCharacterRigger(blender_operator, context)
        elif game_type == GameType.NEVERNESS_TO_EVERNESS.name:
            return NevernessToEvernessCharacterRigger(blender_operator, context)
        elif game_type == GameType.WUTHERING_WAVES.name:
            return WutheringWavesCharacterRigger(blender_operator, context)
        elif game_type == GameType.ARKNIGHTS_ENDFIELD.name:
            return ArknightsEndfieldCharacterRigger(blender_operator, context)
        else:
            raise Exception(f'Unexpected input GameType "{game_type}" for CharacterRiggerFactory')



class CharacterRigger(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def rig_character(self):
        raise NotImplementedError


def _get_character_armature(context):
    selected_armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
    if selected_armatures:
        return selected_armatures[0]

    view_layer_objs = getattr(context.view_layer, 'objects', context.scene.objects)
    view_armatures = [obj for obj in view_layer_objs if obj.type == 'ARMATURE']

    for obj in view_armatures:
        if 'Rig' in obj.name and not any(ign in obj.name.lower() for ign in ['eyerig', 'facerig', 'lighting', 'metarig']):
            return obj

    for obj in view_armatures:
        if not any(ign in obj.name.lower() for ign in ['eyerig', 'facerig', 'lighting', 'metarig']):
            return obj

    return view_armatures[0] if view_armatures else None


class GenshinImpactCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context, material_names, texture_node_names, shader):
        self.blender_operator: Operator = blender_operator
        self.context: Context = context
        self.rigify_bone_shapes_file_path = GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH
        self.material_names: ShaderMaterialNames = material_names
        self.texture_node_names: TextureNodeNames = texture_node_names
        self.lighting_panel_file_names: LightingPanelFileNames = LightingPanelFileNamesFactory.create(shader)

    def rig_character(self):
        fbx_path = self.context.scene.get("setup_wizard_imported_fbx_path", "")
        fbx_name = os.path.basename(fbx_path) if fbx_path else ""
        if fbx_name and not fbx_name.startswith("Avatar_") and (fbx_name.startswith(("Equip_", "EquipSkin_")) or "equip" in fbx_name.lower()):
            self.blender_operator.report({'INFO'}, 'Rigging skipped for weapon / equipment (Equip_ / EquipSkin_ detected).')
            return

        cache_enabled = self.context.window_manager.cache_enabled
        filepath = get_cache(cache_enabled).get(self.rigify_bone_shapes_file_path) or self.blender_operator.filepath

        if not filepath:
            filepath = self.lighting_panel_file_names.ROOT_SHAPE_FILEPATH

        light_vectors_modifiers = [modifier for obj in bpy.data.objects.values() if 
                                   obj.type == 'MESH' for modifier in obj.modifiers if 
                                   'Light Vectors' in modifier.name]

        armature: Armature = _get_character_armature(self.context)
        if not armature:
            self.blender_operator.report({'ERROR'}, 'No armature found. Please import or select a character.')
            return

        hand_bones = [bone for bone in armature.pose.bones.values() if 'Hand' in bone.name]
        number_of_hand_bone_children = max([len(hand_bone.children) for hand_bone in hand_bones]) if hand_bones else 0
        is_player_hand = number_of_hand_bone_children >= 5
        avatar_in_texture_name = self.__get_body_diffuse_texture_name().startswith('Avatar')
        is_playable_character = avatar_in_texture_name or is_player_hand

        character_rigger_props: CharacterRiggerPropertyGroup = self.context.scene.character_rigger_props

        # Lighting Panel is an Armature, so it's important this goes after the armature variable initialization above
        # Genshin Shader >= v3.4
        if character_rigger_props.set_up_lighting_panel:
            for modifier in light_vectors_modifiers:
                LightingPanel(self.lighting_panel_file_names.LIGHTING_PANEL_FILEPATH).set_up_lighting_panel(modifier)

        # Important that the Armature is selected before performing rigging operations
        # Ensure we are in OBJECT mode before manipulating selection (Blender 5.0 compatibility)
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        try:
            armature.hide_set(False)
        except:
            pass
        self.context.view_layer.objects.active = armature
        armature.select_set(True)

        meshes_joined = not (bpy.data.objects.get('Body') and bpy.data.objects.get('Face'))
        if [material for material in bpy.data.materials.values() if 'Paimon' in material.name]:
            rig_npc(
                filepath,
                not character_rigger_props.allow_arm_ik_stretch,
                not character_rigger_props.allow_leg_ik_stretch,
                character_rigger_props.use_arm_ik_poles,
                character_rigger_props.use_leg_ik_poles,
                character_rigger_props.add_children_of_constraints,
                character_rigger_props.use_head_tracker,
            )
        elif not is_playable_character:
            rig_npc(
                filepath,
                not character_rigger_props.allow_arm_ik_stretch,
                not character_rigger_props.allow_leg_ik_stretch,
                character_rigger_props.use_arm_ik_poles,
                character_rigger_props.use_leg_ik_poles,
                character_rigger_props.add_children_of_constraints,
                character_rigger_props.use_head_tracker,
            )                                 
        else:
            rig_character(
                filepath,
                self.lighting_panel_file_names.VERSION,
                not character_rigger_props.allow_arm_ik_stretch,
                not character_rigger_props.allow_leg_ik_stretch,
                character_rigger_props.use_arm_ik_poles,
                character_rigger_props.use_leg_ik_poles,
                character_rigger_props.add_children_of_constraints,
                character_rigger_props.use_head_tracker,
                meshes_joined=meshes_joined
            )

        # Refresh Light Vectors modifiers since empties are renamed/appended during rigging
        def refresh_light_vectors_modifiers():
            char_name = armature.name.replace("Rig", "")
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    o_lower = obj.name.lower()
                    if "lightpanelwgt" in o_lower or "lightpanelselector" in o_lower or "wgtplane" in o_lower or "selectorwgt" in o_lower:
                        continue
                    for modifier in obj.modifiers:
                        if modifier.type == 'NODES' and modifier.node_group and 'Light Vectors' in modifier.node_group.name:
                            def assign_empty(socket, empty_name):
                                empty_obj = bpy.data.objects.get(f"{empty_name}_{char_name}") or bpy.data.objects.get(empty_name)
                                if empty_obj:
                                    set_modifier_property(modifier, socket, empty_obj)

                            assign_empty('Input_3', 'Light Direction')
                            if not get_modifier_property(modifier, 'Input_3'):
                                assign_empty('Input_3', 'Main Light Direction')
                            assign_empty('Input_4', 'Head Origin')
                            assign_empty('Input_5', 'Head Forward')
                            assign_empty('Input_6', 'Head Up')

        refresh_light_vectors_modifiers()

        if getattr(character_rigger_props, "enable_hair_clothes_physics", False) or getattr(character_rigger_props, "enable_hair_dress_physics", False) or getattr(self.context.scene, "enable_hair_clothes_physics", False) or getattr(self.context.scene, "enable_hair_dress_physics", False):
            from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics, find_target_armature
            target_rig = find_target_armature(self.context, armature)
            apply_hair_and_clothes_physics(target_rig, self.context)

        cache_enabled = self.context.window_manager.cache_enabled
        if cache_enabled and filepath:
            cache_using_cache_key(get_cache(cache_enabled), self.rigify_bone_shapes_file_path, filepath)

        self.blender_operator.report({'INFO'}, 'Successfully rigged character')

    def __get_body_diffuse_texture_name(self):
        body_material = self.__get_body_material()
        if not body_material:
            return ''

        body_diffuse_node = self.__get_body_diffuse_node(body_material, self.texture_node_names)
        body_diffuse_texture = self.__get_body_diffuse_texture(body_material, body_diffuse_node)
        return body_diffuse_texture.name if body_diffuse_texture else ''

    def __get_body_material(self):
        pattern = fr"^{self.material_names.MATERIAL_PREFIX_AFTER_RENAME}.*Body$"
        for material in bpy.data.materials.values():
            if re.match(pattern, material.name):
                return material

    def __get_body_diffuse_node(self, material, texture_node_names):
        body_diffuse_node_names = [
            texture_node_names.BODY_DIFFUSE_UV0,  # Genshin
            texture_node_names.MAIN_DIFFUSE,  # Genshin >= v4.0
        ]

        for node_name in body_diffuse_node_names:
            if material and material.node_tree.nodes.get(node_name):
                return material.node_tree.nodes.get(node_name)

    def __get_body_diffuse_texture(self, body_material, body_diffuse_node):
        return body_material.node_tree.nodes.get(body_diffuse_node.name).image


class HonkaiStarRailCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context
        self.rigify_bone_shapes_file_path = GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH

    def rig_character(self):
        cache_enabled = self.context.window_manager.cache_enabled
        filepath = get_cache(cache_enabled).get(self.rigify_bone_shapes_file_path) or self.blender_operator.filepath

        if not filepath:
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RootShape.blend')

        armature = _get_character_armature(self.context)
        if not armature:
            self.blender_operator.report({'ERROR'}, 'No armature found. Please import or select a character.')
            return

        character_rigger_props: CharacterRiggerPropertyGroup = self.context.scene.character_rigger_props
        meshes_joined = not (bpy.data.objects.get('Body') and bpy.data.objects.get('Face'))

        bpy.ops.object.select_all(action='DESELECT')
        try:
            armature.hide_set(False)
        except:
            pass
        self.context.view_layer.objects.active = armature
        armature.select_set(True)

        hsr_rig_character(
            filepath,
            not character_rigger_props.allow_arm_ik_stretch,
            not character_rigger_props.allow_leg_ik_stretch,
            character_rigger_props.use_arm_ik_poles,
            character_rigger_props.use_leg_ik_poles,
            character_rigger_props.add_children_of_constraints,
            character_rigger_props.use_head_tracker,
            meshes_joined=meshes_joined
        )

        def setup_isaac_face_rig(body_rig):
            import os
            blend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'isaacfacerig.blend')
            if not os.path.exists(blend_path):
                print(f"[FACE RIG] File not found: {blend_path}")
                return

            objects_before = set(bpy.data.objects)
            facerig_obj = None
            appended_coll = None

            # Detect the first collection inside isaacfacerig.blend dynamically using libraries.load
            try:
                with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                    if data_from.collections:
                        first_coll_name = data_from.collections[0]
                        data_to.collections = [first_coll_name]
                        print(f"[FACE RIG] Detected first collection in blend: '{first_coll_name}'")

                for collection in data_to.collections:
                    if collection:
                        appended_coll = collection
                        if collection.name not in bpy.context.scene.collection.children:
                            bpy.context.scene.collection.children.link(collection)
            except Exception as err:
                print(f"[FACE RIG] Library load error: {err}")

            new_objects = set(bpy.data.objects) - objects_before
            for obj in new_objects:
                if obj.type == 'ARMATURE':
                    facerig_obj = obj
                    break

            if not facerig_obj:
                facerig_obj = bpy.data.objects.get("isaac FaceRig")
                if not facerig_obj:
                    for obj in bpy.data.objects:
                        if obj.type == 'ARMATURE' and any(k in obj.name.lower() for k in ['facerig', 'isaac']):
                            facerig_obj = obj
                            break

            if not facerig_obj:
                print("[FACE RIG] Could not find 'isaac FaceRig' object.")
                return

            print(f"[FACE RIG] Successfully imported/found FaceRig armature: '{facerig_obj.name}'")

            # Move isaac FaceRig armature to Armature collection, planes to WGTS, and remove empty collection
            target_armature_coll = body_rig.users_collection[0] if body_rig.users_collection else bpy.context.scene.collection
            wgt_coll = bpy.data.collections.get("WGTS") or bpy.data.collections.get("WGTS_FaceRig") or bpy.data.collections.get("wgt") or bpy.data.collections.new("WGTS")

            if facerig_obj and target_armature_coll:
                if facerig_obj.name not in target_armature_coll.objects:
                    target_armature_coll.objects.link(facerig_obj)
                for coll in list(facerig_obj.users_collection):
                    if coll != target_armature_coll:
                        coll.objects.unlink(facerig_obj)

            plane_objs = [obj for obj in new_objects if obj != facerig_obj]
            if appended_coll:
                plane_objs.extend([obj for obj in appended_coll.objects if obj != facerig_obj and obj not in plane_objs])

            for p_obj in plane_objs:
                if p_obj.name not in wgt_coll.objects:
                    wgt_coll.objects.link(p_obj)
                for coll in list(p_obj.users_collection):
                    if coll != wgt_coll:
                        coll.objects.unlink(p_obj)

            # Unlink wgt_coll from Scene Collection so it is unlinked from the Outliner
            for parent_coll in list(bpy.data.collections):
                if wgt_coll.name in parent_coll.children:
                    try:
                        parent_coll.children.unlink(wgt_coll)
                    except Exception:
                        pass
            if wgt_coll.name in bpy.context.scene.collection.children:
                try:
                    bpy.context.scene.collection.children.unlink(wgt_coll)
                except Exception:
                    pass

            if appended_coll:
                try:
                    for parent_coll in bpy.data.collections:
                        if appended_coll.name in parent_coll.children:
                            parent_coll.children.unlink(appended_coll)
                    if appended_coll.name in bpy.context.scene.collection.children:
                        bpy.context.scene.collection.children.unlink(appended_coll)
                    bpy.data.collections.remove(appended_coll, do_unlink=True)
                    print(f"[FACE RIG] Cleaned up temporary collection '{appended_coll.name}'")
                except Exception as c_err:
                    print(f"[FACE RIG] Collection cleanup notice: {c_err}")

            body_head_bone_name = None
            for candidate in ["DEF-spine.006", "head", "Head", "Head_M"]:
                if candidate in body_rig.data.bones:
                    body_head_bone_name = candidate
                    break
            if not body_head_bone_name:
                for b in body_rig.data.bones.keys():
                    if "head" in b.lower() or "spine.006" in b.lower():
                        body_head_bone_name = b
                        break

            if not body_head_bone_name:
                print("[FACE RIG] Could not find head bone on body rig.")
                return

            facerig_head_bone_name = "DEF-spine.006" if "DEF-spine.006" in facerig_obj.data.bones else facerig_obj.data.bones[0].name

            try:
                body_head_matrix_world = body_rig.matrix_world @ body_rig.pose.bones[body_head_bone_name].matrix
                facerig_head_matrix_local = facerig_obj.pose.bones[facerig_head_bone_name].matrix
                facerig_obj.matrix_world = body_head_matrix_world @ facerig_head_matrix_local.inverted()
            except Exception as e:
                print(f"[FACE RIG] Matrix alignment warning: {e}")

            pbone = facerig_obj.pose.bones.get(facerig_head_bone_name)
            if pbone:
                constraint = None
                for c in pbone.constraints:
                    if c.type in ['COPY_TRANSFORMS', 'CHILD_OF', 'COPY_LOCATION']:
                        constraint = c
                        break
                if not constraint:
                    constraint = pbone.constraints.new('COPY_TRANSFORMS')
                    constraint.name = "Copy Head Transforms"

                constraint.target = body_rig
                constraint.subtarget = body_head_bone_name

            face_obj = bpy.data.objects.get("Face")
            if not face_obj:
                char_name = body_rig.name.replace("Rig", "")
                face_obj = bpy.data.objects.get(f"Face_{char_name}")
            if not face_obj:
                for obj in bpy.data.objects:
                    if obj.type == 'MESH' and ('face' in obj.name.lower() or obj.parent == body_rig):
                        for mod in obj.modifiers:
                            if mod.type == 'ARMATURE':
                                face_obj = obj
                                break

            if face_obj:
                for mod in face_obj.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = facerig_obj
                        print(f"[FACE RIG] Re-targeted '{face_obj.name}' armature modifier to '{facerig_obj.name}'")
        try:
            from setup_wizard.character_rig_setup.hsr_face_rig import hsr_face_rig_main
            hsr_face_rig_main()
        except Exception as e:
            print(f"HSR face rig skipped: {e}")

        try:
            setup_isaac_face_rig(armature)
        except Exception as e:
            print(f"Isaac face rig skipped: {e}")

        def refresh_light_vectors_modifiers():
            char_name = armature.name.replace("Rig", "")
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    o_lower = obj.name.lower()
                    if "lightpanelwgt" in o_lower or "lightpanelselector" in o_lower or "wgtplane" in o_lower or "selectorwgt" in o_lower:
                        continue
                    for modifier in obj.modifiers:
                        if modifier.type == 'NODES' and modifier.node_group and 'Light Vectors' in modifier.node_group.name:
                            def assign_empty(socket, empty_name):
                                empty_obj = bpy.data.objects.get(f"{empty_name}_{char_name}") or bpy.data.objects.get(empty_name)
                                if empty_obj:
                                    set_modifier_property(modifier, socket, empty_obj)

                            assign_empty('Input_3', 'Light Direction')
                            if not get_modifier_property(modifier, 'Input_3'):
                                assign_empty('Input_3', 'Main Light Direction')
                            assign_empty('Input_4', 'Head Origin')
                            assign_empty('Input_5', 'Head Forward')
                            assign_empty('Input_6', 'Head Up')

        refresh_light_vectors_modifiers()

        if getattr(character_rigger_props, "enable_hair_clothes_physics", False) or getattr(character_rigger_props, "enable_hair_dress_physics", False) or getattr(self.context.scene, "enable_hair_clothes_physics", False) or getattr(self.context.scene, "enable_hair_dress_physics", False):
            from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics, find_target_armature
            target_rig = find_target_armature(self.context, armature)
            apply_hair_and_clothes_physics(target_rig, self.context)

        cache_enabled = self.context.window_manager.cache_enabled
        if cache_enabled and filepath:
            cache_using_cache_key(get_cache(cache_enabled), self.rigify_bone_shapes_file_path, filepath)

        self.blender_operator.report({'INFO'}, 'Successfully rigged HSR character')


class PunishingGrayRavenCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context
        self.rigify_bone_shapes_file_path = 'PLACEHOLDER'

    def rig_character(self):
        return


class ZenlessZoneZeroCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context
        self.rigify_bone_shapes_file_path = GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH

    def rig_character(self):
        cache_enabled = self.context.window_manager.cache_enabled
        cached = get_cache(cache_enabled).get(self.rigify_bone_shapes_file_path)
        filepath = cached if (cached and os.path.isfile(cached)) else (self.blender_operator.filepath if (self.blender_operator.filepath and os.path.isfile(self.blender_operator.filepath)) else None)

        if not filepath or not os.path.isfile(filepath):
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RootShape.blend')

        armature = _get_character_armature(self.context)
        if not armature:
            self.blender_operator.report({'ERROR'}, 'No armature found. Please import or select a character.')
            return

        character_rigger_props: CharacterRiggerPropertyGroup = self.context.scene.character_rigger_props
        meshes_joined = not (bpy.data.objects.get('Body') and bpy.data.objects.get('Face'))

        light_vectors_modifiers = [modifier for obj in bpy.data.objects.values() if 
                                   obj.type == 'MESH' for modifier in obj.modifiers if 
                                   'Light Vectors' in modifier.name]

        selected_shader = getattr(self.context.scene, 'zzz_shader_type', 'KYTHERA')
        use_lighting_panel = character_rigger_props.set_up_lighting_panel and (selected_shader != 'KYTHERA')

        if use_lighting_panel:
            for modifier in light_vectors_modifiers:
                lp_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LightingPanel.blend')
                LightingPanel(lp_filepath).set_up_lighting_panel(modifier)

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass

        bpy.ops.object.select_all(action='DESELECT')
        try:
            armature.hide_set(False)
        except:
            pass
        self.context.view_layer.objects.active = armature
        armature.select_set(True)

        try:
            zzz_rig_character(
                filepath,
                4 if use_lighting_panel else 0, # lighting_panel_version
                not character_rigger_props.allow_arm_ik_stretch,
                not character_rigger_props.allow_leg_ik_stretch,
                character_rigger_props.use_arm_ik_poles,
                character_rigger_props.use_leg_ik_poles,
                character_rigger_props.add_children_of_constraints,
                character_rigger_props.use_head_tracker,
                meshes_joined=meshes_joined
            )
        except Exception as e:
            print(f"[ZZZ Rig Warning] zzz_rig_character skipped/error: {e}")
        finally:
            try:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        try:
            zzz_face_rig_main()
        except Exception as e:
            print(f"[ZZZ Rig Warning] Face rig skipped: {e}")
            try:
                setup_isaac_face_rig(armature)
            except Exception as e_isaac:
                print(f"[ZZZ Rig Warning] Isaac face rig fallback skipped: {e_isaac}")
        finally:
            try:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        def join_extra_armatures(body_rig):
            # Check for any unmerged armatures (Lighting Panel, FaceRig, etc.)
            for obj in list(bpy.data.objects):
                if obj.type == 'ARMATURE' and obj != body_rig and obj.name != body_rig.name:
                    o_low = obj.name.lower()
                    if any(k in o_low for k in ['lighting', 'panel', 'facerig', 'isaac']):
                        try:
                            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                                bpy.ops.object.mode_set(mode='OBJECT')
                        except Exception:
                            pass
                        try:
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)
                            body_rig.select_set(True)
                            bpy.context.view_layer.objects.active = body_rig
                            bpy.ops.object.join()
                            print(f"[ZZZ RIG] Joined '{obj.name}' into '{body_rig.name}' with bpy.ops.object.join()")
                        except Exception as join_err:
                            print(f"[ZZZ RIG Warning] Failed to join '{obj.name}' into '{body_rig.name}': {join_err}")

        join_extra_armatures(armature)

        def cleanup_facerig_and_props_collections(body_rig):
            if hasattr(body_rig.data, "collections"):
                colls = body_rig.data.collections
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
                for b in body_rig.data.bones:
                    if "hook" in b.name.lower():
                        other_coll.assign(b)
                        if face_coll:
                            face_coll.unassign(b)

                # Ensure all 3 root bones (root, root.001, root.002) are in Root collection
                for r_name in ["root", "root.001", "root.002"]:
                    rb = body_rig.data.bones.get(r_name)
                    if rb:
                        root_coll.assign(rb)
                        if "Offsets" in colls:
                            colls["Offsets"].unassign(rb)
                        if other_coll:
                            other_coll.unassign(rb)

                face_coll.is_visible = True
                root_coll.is_visible = True
                if "Weapon" in colls:
                    actual_w_bones = [b for b in colls["Weapon"].bones if b.name not in ["prop.L", "prop.R"]]
                    colls["Weapon"].is_visible = len(actual_w_bones) > 0

        cleanup_facerig_and_props_collections(armature)

        # Ensure all tail bones have the tweak custom shape (exclude IK bones)
        tweak_shape = (
            next((o for o in bpy.data.objects if o.type == 'MESH' and "tweak_spine" in o.name), None)
            or next((o for o in bpy.data.objects if o.type == 'MESH' and "_tweak" in o.name), None)
        )
        if tweak_shape and hasattr(armature, "pose") and armature.pose:
            for pb in armature.pose.bones:
                if ("_tail_" in pb.name.lower() or "_tail" in pb.name.lower() or pb.name.lower().startswith("tail")) and "ik" not in pb.name.lower():
                    pb.custom_shape = tweak_shape
                    pb.use_custom_shape_bone_size = False
                    pb.custom_shape_scale_xyz = (0.08, 0.08, 0.08)
                    pb.rotation_mode = 'XYZ'

        # Ensure tail_ik retains prop-wgt cube shape
        prop_wgt = bpy.data.objects.get("prop-wgt")
        if prop_wgt and hasattr(armature, "pose") and armature.pose:
            for pb in armature.pose.bones:
                if "tail_ik" in pb.name.lower():
                    pb.custom_shape = prop_wgt
                    pb.use_custom_shape_bone_size = False
                    pb.custom_shape_scale_xyz = (0.35, 0.35, 0.35)
                    pb.rotation_mode = 'XYZ'
                    if hasattr(armature.data, "collections"):
                        torso_c = armature.data.collections.get("Torso (IK)")
                        b_ref = armature.data.bones.get(pb.name)
                        if torso_c and b_ref:
                            torso_c.assign(b_ref)

        def refresh_light_vectors_modifiers():
            char_name = armature.name.replace("Rig", "")
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    o_lower = obj.name.lower()
                    if "lightpanelwgt" in o_lower or "lightpanelselector" in o_lower or "wgtplane" in o_lower or "selectorwgt" in o_lower:
                        continue
                    for modifier in obj.modifiers:
                        if modifier.type == 'NODES' and modifier.node_group and 'Light Vectors' in modifier.node_group.name:
                            def assign_empty(socket, empty_name):
                                empty_obj = bpy.data.objects.get(f"{empty_name}_{char_name}") or bpy.data.objects.get(empty_name)
                                if empty_obj:
                                    set_modifier_property(modifier, socket, empty_obj)

                            assign_empty('Input_3', 'Light Direction')
                            if not get_modifier_property(modifier, 'Input_3'):
                                assign_empty('Input_3', 'Main Light Direction')
                            assign_empty('Input_4', 'Head Origin')
                            assign_empty('Input_5', 'Head Forward')
                            assign_empty('Input_6', 'Head Up')

        try:
            refresh_light_vectors_modifiers()
        except Exception as e_light:
            print(f"[ZZZ Rig Warning] refresh_light_vectors_modifiers error: {e_light}")

        if getattr(character_rigger_props, "enable_hair_clothes_physics", False) or getattr(character_rigger_props, "enable_hair_dress_physics", False) or getattr(self.context.scene, "enable_hair_clothes_physics", False) or getattr(self.context.scene, "enable_hair_dress_physics", False):
            try:
                from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics, find_target_armature
                target_rig = find_target_armature(self.context, armature)
                apply_hair_and_clothes_physics(target_rig, self.context)
            except Exception as e_phys:
                print(f"[ZZZ Rig Warning] apply_hair_and_clothes_physics error: {e_phys}")

        cache_enabled = self.context.window_manager.cache_enabled
        if cache_enabled and filepath:
            cache_using_cache_key(get_cache(cache_enabled), self.rigify_bone_shapes_file_path, filepath)

        try:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass

        self.blender_operator.report({'INFO'}, 'Successfully rigged ZZZ character')


class NevernessToEvernessCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context

    def rig_character(self):
        armature = _get_character_armature(self.context)
        if armature:
            self.context.view_layer.objects.active = armature
            armature.select_set(True)

        cache_enabled = self.context.window_manager.cache_enabled
        filepath = self.blender_operator.filepath or get_cache(cache_enabled).get(GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH)

        if armature:
            try:
                nte_rig_character(
                    filepath,
                    disallow_arm_ik_stretch=True,
                    disallow_leg_ik_stretch=True,
                    use_arm_ik_poles=True,
                    use_leg_ik_poles=True,
                    add_child_of_constraints=True,
                    use_head_tracker=True
                )
            except Exception as ex:
                self.blender_operator.report({'ERROR'}, f"Failed to rig NTE character: {ex}")

        try:
            from setup_wizard.character_rig_setup.nte_face_rig import nte_face_rig_main
            nte_face_rig_main()
        except Exception as e:
            print(f"NTE face rig skipped/notice: {e}")

        character_rigger_props: CharacterRiggerPropertyGroup = self.context.scene.character_rigger_props
        if getattr(character_rigger_props, "enable_hair_clothes_physics", False) or getattr(character_rigger_props, "enable_hair_dress_physics", False) or getattr(self.context.scene, "enable_hair_clothes_physics", False) or getattr(self.context.scene, "enable_hair_dress_physics", False):
            from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics, find_target_armature
            target_rig = find_target_armature(self.context, armature)
            apply_hair_and_clothes_physics(target_rig, self.context)

        cache_enabled = self.context.window_manager.cache_enabled
        if cache_enabled and filepath:
            cache_using_cache_key(get_cache(cache_enabled), GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH, filepath)

        self.blender_operator.report({'INFO'}, 'Successfully rigged NTE character')


class WutheringWavesCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context

    def rig_character(self):
        try:
            success = rig_wuthering_waves_character(self.context)
            if success:
                character_rigger_props = self.context.scene.character_rigger_props
                if getattr(character_rigger_props, "enable_hair_clothes_physics", False) or getattr(character_rigger_props, "enable_hair_dress_physics", False) or getattr(self.context.scene, "enable_hair_clothes_physics", False) or getattr(self.context.scene, "enable_hair_dress_physics", False):
                    from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics
                    armature = self.context.active_object
                    if armature:
                        apply_hair_and_clothes_physics(armature, self.context)
                self.blender_operator.report({'INFO'}, 'Successfully rigged Wuthering Waves character!')
            else:
                self.blender_operator.report({'WARNING'}, 'Rigify generation for Wuthering Waves completed with warnings.')
        except Exception as ex:
            self.blender_operator.report({'ERROR'}, f"Failed to rig Wuthering Waves character: {ex}")
            raise ex


class ArknightsEndfieldCharacterRigger(CharacterRigger):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context
        self.rigify_bone_shapes_file_path = GENSHIN_RIGIFY_BONE_SHAPES_FILE_PATH

    def rig_character(self):
        cache_enabled = self.context.window_manager.cache_enabled
        filepath = get_cache(cache_enabled).get(self.rigify_bone_shapes_file_path) or self.blender_operator.filepath

        if not filepath:
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RootShape.blend')

        armature = _get_character_armature(self.context)
        if not armature:
            self.blender_operator.report({'ERROR'}, 'No armature found. Please import or select a character.')
            return

        character_rigger_props: CharacterRiggerPropertyGroup = self.context.scene.character_rigger_props
        meshes_joined = not (bpy.data.objects.get('Body') and bpy.data.objects.get('Face'))

        try:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        bpy.ops.object.select_all(action='DESELECT')
        try:
            armature.hide_set(False)
        except Exception:
            pass
        self.context.view_layer.objects.active = armature
        armature.select_set(True)

        ake_rig_character(
            filepath,
            not character_rigger_props.allow_arm_ik_stretch,
            not character_rigger_props.allow_leg_ik_stretch,
            character_rigger_props.use_arm_ik_poles,
            character_rigger_props.use_leg_ik_poles,
            character_rigger_props.add_children_of_constraints,
            character_rigger_props.use_head_tracker,
            meshes_joined=meshes_joined,
        )

        if getattr(character_rigger_props, "enable_hair_clothes_physics", False) or getattr(character_rigger_props, "enable_hair_dress_physics", False) or getattr(self.context.scene, "enable_hair_clothes_physics", False) or getattr(self.context.scene, "enable_hair_dress_physics", False):
            try:
                from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics, find_target_armature
                target_rig = find_target_armature(self.context, armature)
                apply_hair_and_clothes_physics(target_rig, self.context)
            except Exception as e_phys:
                print(f"[AKE Rig Warning] apply_hair_and_clothes_physics error: {e_phys}")

        try:
            from setup_wizard.character_rig_setup.ake_face_rig import setup_endfield_isaac_face_rig
            from setup_wizard.character_rig_setup.rig_ui_utils import find_target_armature
            target_rig = find_target_armature(self.context, armature)
            setup_endfield_isaac_face_rig(target_rig, self.context)
        except Exception as e_face:
            print(f"[AKE Rig Warning] Isaac face rig setup error: {e_face}")

        try:
            from setup_wizard.set_up_head_driver import setup_ake_head_driver_system
            setup_ake_head_driver_system(self.context)
        except Exception as e_hd:
            print(f"[AKE Rig Warning] Head driver setup notice: {e_hd}")

        cache_enabled = self.context.window_manager.cache_enabled
        if cache_enabled and filepath:
            cache_using_cache_key(get_cache(cache_enabled), self.rigify_bone_shapes_file_path, filepath)

        try:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass

        self.blender_operator.report({'INFO'}, 'Successfully rigged Arknights: Endfield character')



