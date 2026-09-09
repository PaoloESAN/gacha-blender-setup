# Author: michael-gh1

import bpy
import os
import re


from abc import ABC, abstractmethod
from bpy.types import Context, Operator
from setup_wizard.domain.shader_node_names import ShaderNodeNames, StellarToonShaderNodeNames, V2_GenshinShaderNodeNames, V3_GenshinShaderNodeNames, V4_PrimoToonShaderNodeNames
from setup_wizard.domain.star_cloak_types import StarCloakTypes
from setup_wizard.domain.material_identifier_service import PunishingGrayRavenMaterialIdentifierService

from setup_wizard.import_order import CHARACTER_MODEL_FOLDER_FILE_PATH, NextStepInvoker, get_actual_material_name_for_dress, get_cache, get_active_character_directory


from setup_wizard.domain.game_types import GameType
from setup_wizard.domain.shader_identifier_service import GenshinImpactShaders, HonkaiStarRailShaders, ShaderIdentifierService, \
    ShaderIdentifierServiceFactory
from setup_wizard.domain.shader_material_names import StellarToonShaderMaterialNames, V3_BonnyFestivityGenshinImpactMaterialNames, V2_FestivityGenshinImpactMaterialNames, \
    ShaderMaterialNames, Nya222HonkaiStarRailShaderMaterialNames, JaredNytsPunishingGrayRavenShaderMaterialNames, V4_PrimoToonGenshinImpactMaterialNames, \
    ZenlessZoneZeroShaderMaterialNames
from setup_wizard.texture_import_setup.texture_importer_types import TextureImporterType, find_all_image_nodes_by_category
from setup_wizard.domain.shader_material_name_keywords import ShaderMaterialNameKeywords
from setup_wizard.utils.genshin_body_part_deducer import get_monster_body_part_name, \
    get_npc_mesh_body_part_name

class GameDefaultMaterialReplacer(ABC):
    @abstractmethod
    def replace_default_materials(self):
        raise NotImplementedError()


class GameDefaultMaterialReplacerFactory:
    def create(game_type: GameType, blender_operator: Operator, context: Context):
        shader_identifier_service: ShaderIdentifierService = ShaderIdentifierServiceFactory.create(game_type)
        shader = shader_identifier_service.identify_shader(bpy.data.materials, bpy.data.node_groups)

        # Because we inject the GameType via StringProperty, we need to compare using the Enum's name (a string)
        if game_type == GameType.GENSHIN_IMPACT.name:
            if shader is GenshinImpactShaders.V1_GENSHIN_IMPACT_SHADER or shader is GenshinImpactShaders.V2_GENSHIN_IMPACT_SHADER:
                material_names = V2_FestivityGenshinImpactMaterialNames
                shader_node_names = V2_GenshinShaderNodeNames
            elif shader is GenshinImpactShaders.V3_GENSHIN_IMPACT_SHADER:
                material_names = V3_BonnyFestivityGenshinImpactMaterialNames
                shader_node_names = V3_GenshinShaderNodeNames
            elif shader is GenshinImpactShaders.V1_HOYOTOON_GENSHIN_IMPACT_SHADER:
                from setup_wizard.domain.shader_material_names import V1_HoYoToonGenshinImpactMaterialNames
                from setup_wizard.domain.shader_node_names import V1_HoYoToonShaderNodeNames
                material_names = V1_HoYoToonGenshinImpactMaterialNames
                shader_node_names = V1_HoYoToonShaderNodeNames
            else:
                material_names = V4_PrimoToonGenshinImpactMaterialNames 
                shader_node_names = V4_PrimoToonShaderNodeNames
            return GenshinImpactDefaultMaterialReplacer(blender_operator, context, material_names, shader_node_names)
        elif game_type == GameType.HONKAI_STAR_RAIL.name:
            if shader is HonkaiStarRailShaders.NYA222_HONKAI_STAR_RAIL_SHADER:
                return HonkaiStarRailDefaultMaterialReplacer(blender_operator, context, Nya222HonkaiStarRailShaderMaterialNames)
            else:  # shader is HonkaiStarRailShaders.STELLARTOON_HONKAI_STAR_RAIL_SHADER
                return StellarToonDefaultMaterialReplacer(blender_operator, context, StellarToonShaderMaterialNames)
        elif game_type == GameType.PUNISHING_GRAY_RAVEN.name:
            return PunishingGrayRavenDefaultMaterialReplacer(blender_operator, context)
        elif game_type == GameType.ZENLESS_ZONE_ZERO.name:
            return ZenlessZoneZeroDefaultMaterialReplacer(blender_operator, context)
        elif game_type == GameType.NEVERNESS_TO_EVERNESS.name:
            return NevernessToEvernessDefaultMaterialReplacer(blender_operator, context)
        elif game_type == GameType.WUTHERING_WAVES.name:
            return WutheringWavesDefaultMaterialReplacer(blender_operator, context)
        elif game_type == GameType.ARKNIGHTS_ENDFIELD.name:
            return ArknightsEndfieldDefaultMaterialReplacer(blender_operator, context)
        else:
            raise Exception(f'Unknown {GameType}: {game_type}')



class GenshinImpactDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    def __init__(self, blender_operator, context, material_names: ShaderMaterialNames, shader_node_names: ShaderNodeNames):
        self.blender_operator: Operator = blender_operator
        self.context: Context = context
        self.material_names = material_names
        self.shader_node_names = shader_node_names

    def replace_default_materials(self):
        mesh_ignore_list = []
        meshes = [mesh for mesh in bpy.context.scene.objects if mesh.type == 'MESH' and mesh.name not in mesh_ignore_list]

        for mesh in meshes:
            for material_slot in mesh.material_slots:
                material_name = material_slot.name
                
                # If it already has our shader prefix, it was processed previously (e.g. earlier character).
                if material_name.startswith(self.material_names.MATERIAL_PREFIX):
                    continue

                mesh_body_part_name = None
                character_type = None

                if material_name.startswith('NPC'):
                    mesh_body_part_name = get_npc_mesh_body_part_name(material_name)
                    character_type = TextureImporterType.NPC
                elif material_name.startswith('Monster'):
                    mesh_body_part_name = get_monster_body_part_name(material_name)
                    character_type = TextureImporterType.MONSTER
                elif material_name.startswith(('Equip_', 'EquipSkin_')) or (mesh and mesh.name.startswith(('Equip_', 'EquipSkin_'))):
                    mesh_body_part_name = 'Body'
                    character_type = TextureImporterType.AVATAR
                else:
                    mesh_body_part_name = material_name.split('_')[-1]
                    character_type = TextureImporterType.AVATAR

                if material_name.startswith(ShaderMaterialNameKeywords.SKILLOBJ) and material_name.endswith('Glass_Mat'):
                    mesh_body_part_name = 'Glass'
                elif material_name.startswith(ShaderMaterialNameKeywords.SKILLOBJ) and material_name.endswith('Glass_Eff_Mat'):
                    mesh_body_part_name = 'Glass_Eff'
                elif material_name.startswith(ShaderMaterialNameKeywords.SKILLOBJ):
                    skillobj_identifier = material_name.split('_')[2]
                    mesh_body_part_name = f'{ShaderMaterialNameKeywords.SKILLOBJ} {skillobj_identifier}'
                elif material_name.endswith('Hand_Eff_Mat'):  # Asmoday
                    mesh_body_part_name = 'StarCloak'

                is_numbered_pupil = any(
                    f'pupil{k}' in s.lower() or f'pupil_{k}' in s.lower() or f'pupil 0{k}' in s.lower() or f'pupila{k}' in s.lower() or f'pupila_{k}' in s.lower()
                    for s in [material_name, mesh.name]
                    for k in ['01', '1', '02', '2', '03', '3', '04', '4']
                ) or any(
                    'sandrone' in s.lower() or 'marionettenew' in s.lower() or 'marionette_new' in s.lower() or 'newmarionette' in s.lower() or 'vodyanitsa' in s.lower() or 'ronova' in s.lower()
                    for s in [material_name, mesh.name] + ([mesh.parent.name] if mesh.parent else [])
                )
                if not is_numbered_pupil and material_slot.material and material_slot.material.use_nodes:
                    for n in material_slot.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE' and n.image:
                            img_lower = n.image.name.lower()
                            if any(f'pupil{k}' in img_lower or f'pupil_{k}' in img_lower or f'pupil 0{k}' in img_lower or f'pupila{k}' in img_lower for k in ['01', '1', '02', '2', '03', '3', '04', '4']):
                                is_numbered_pupil = True
                                break

                is_pupil_part = ('pupil' in material_name.lower() or 'pupila' in material_name.lower()) or (mesh_body_part_name and ('pupil' in mesh_body_part_name.lower() or 'pupila' in mesh_body_part_name.lower()))

                if mesh_body_part_name in ['Eye', 'EyeStar', 'Eyes', 'EyeShadow']:
                    mesh_body_part_name = 'Face'
                elif is_pupil_part:
                    if is_numbered_pupil:
                        mesh_body_part_name = 'New Pupil'
                    else:
                        mesh_body_part_name = 'Pupil'

                # If material_name is ever 'Dress', 'Arm' or 'Cloak', there could be issues with get_actual_material_name_for_dress()
                material_name = self.create_shader_material_if_unique_mesh(mesh, mesh_body_part_name, material_name)
                genshin_material = bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}') or \
                                   bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX_AFTER_RENAME}{mesh_body_part_name}') or \
                                   bpy.data.materials.get(f'HoYoverse - Genshin {mesh_body_part_name}')
                if not genshin_material and mesh_body_part_name in ['Eye', 'EyeStar', 'Eyes', 'EyeShadow', 'Brow', 'Pupil', 'Pupila', 'New Pupil']:
                    genshin_material = bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}Face') or \
                                       bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}Brow')

                if genshin_material:
                    self.__transfer_diffuse_texture(material_slot.material, genshin_material)
                    material_slot.material = genshin_material
                    is_equip_mat = material_name.startswith(('Equip_', 'EquipSkin_')) or (mesh and mesh.name.startswith(('Equip_', 'EquipSkin_'))) or ('equip' in material_name.lower())
                    if is_equip_mat and genshin_material.use_nodes:
                        for n in genshin_material.node_tree.nodes:
                            if 'Use Alpha' in n.inputs:
                                n.inputs['Use Alpha'].default_value = 1.0
                            if n.type == 'GROUP' and n.node_tree:
                                for sub_node in n.node_tree.nodes:
                                    if 'Use Alpha' in sub_node.inputs:
                                        sub_node.inputs['Use Alpha'].default_value = 1.0
                elif mesh_body_part_name and ('Dress' in mesh_body_part_name or 'Arm' in mesh_body_part_name or 'Cloak' in mesh_body_part_name):
                    # Xiao is the only character with an Arm material
                    # Dainsleif and Paimon are the only characters with Cloak materials
                    self.blender_operator.report({'INFO'}, 'Dress detected on character model!')

                    actual_material_for_dress = get_actual_material_name_for_dress(material_name, character_type.name)
                    if actual_material_for_dress == 'Cloak' or mesh_body_part_name == 'Cloak':
                        if bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}VFX'):
                            actual_material_for_dress = 'VFX'
                            mesh_body_part_name = 'StarCloak'
                        elif mesh_body_part_name == 'Cloak' and character_type == TextureImporterType.AVATAR:
                            pass  # Give Dainslief basic body shader (backwards compatibility)
                        else:
                            # short-circuit, no shader available for 'Cloak' so do nothing (Paimon)
                            continue
                    elif actual_material_for_dress == 'Effect':  # Dress2 material w/ Effect texture filename (Skirk support)
                        # (dangerous) assumption that all Dress w/ Effect texture filename are Hair-type
                        actual_material_for_dress = 'Hair'  # backwards compatible before VFX shader existed, pre-v4.0

                        if bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}VFX'):
                            actual_material_for_dress = 'VFX'
                            mesh_body_part_name = 'StarCloak'
                    elif actual_material_for_dress == 'Eff':  # Asmoday support
                        # (dangerous) assumption that all Eff texture filename are Body-type
                        actual_material_for_dress = 'Body'  # backwards compatible before VFX shader existed, pre-v4.0

                        if bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}VFX'):
                            actual_material_for_dress = 'VFX'
                            mesh_body_part_name = 'StarCloak'

                    genshin_material = self.__clone_material_and_rename(
                        material_slot, 
                        f'{self.material_names.MATERIAL_PREFIX}{actual_material_for_dress}', 
                        mesh_body_part_name
                    )
                    if not genshin_material:
                        self.blender_operator.report({'WARNING'}, f'Could not find template material for "{actual_material_for_dress}", skipping material: {material_name}')
                        continue
                    if genshin_material.name == f'{self.material_names.STAR_CLOAK}':
                        self.__set_glass_star_cloak_toggle(genshin_material, True)
                        self.__set_star_cloak_type(genshin_material, material_name)  # original material name, which contains character name
                    self.blender_operator.report({'INFO'}, f'Replaced material: "{material_name}" with "{actual_material_for_dress}"')
                elif material_name == 'miHoYoDiffuse':
                    material_slot.material = bpy.data.materials.get(self.material_names.BODY)
                    continue
                else:
                    self.blender_operator.report({'WARNING'}, f'Ignoring unknown mesh body part in character model: {mesh_body_part_name} / Material: {material_name}')
                    continue

                # Deprecated: I don't think cloning and renaming groups is necessary? (original commit: 6a4772e)
                # Don't need to duplicate multiple Face shader nodes
                # if genshin_material.name != f'miHoYo - Genshin Face':
                #     genshin_main_shader_node = genshin_material.node_tree.nodes.get('Group.001')
                #     genshin_main_shader_node.node_tree = self.__clone_shader_node_and_rename(genshin_material, mesh_body_part_name)
        try:
            from setup_wizard.ui.gi_ui_setup_wizard_menu import sync_genshin_shader_properties
            sync_genshin_shader_properties()
        except Exception as e_sync:
            print(f"[GI MATERIALS] Notice syncing shader properties: {e_sync}")

        self.blender_operator.report({'INFO'}, 'Replaced default materials with Genshin shader materials...')

    def create_shader_material_if_unique_mesh(self, mesh, mesh_body_part_name, material_name):
        if not mesh_body_part_name:
            return material_name
        m_low = mesh_body_part_name.lower()
        if m_low in ['body1', 'body01', 'body_01']:
            body_material = self.create_body_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            material_name = body_material.name
        elif m_low in ['body2', 'body02', 'body_02']:
            body_material = self.create_body_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
        elif m_low in ['dress1', 'dress01', 'dress_01', 'dress2', 'dress02', 'dress_02']:
            dress_template = bpy.data.materials.get(self.material_names.DRESS) or bpy.data.materials.get(self.material_names.BODY)
            new_material = bpy.data.materials.get(f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            if not new_material and dress_template:
                new_material = dress_template.copy()
                new_material.name = f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}'
                new_material.use_fake_user = True
                self.__clear_material_images(new_material)
            material_name = new_material.name if new_material else material_name
        elif mesh_body_part_name == 'EffectHair':  # Furina
            hair_material = self.create_hair_material(self.material_names, self.material_names.EFFECT_HAIR)
            material_name = hair_material.name
        elif mesh_body_part_name == 'Effect':  # Furina (Default)
            hair_material = self.create_hair_material(self.material_names, self.material_names.EFFECT)
            material_name = hair_material.name
        elif mesh_body_part_name == 'Helmet':  # Frem
            helmet_material = self.create_hair_material(self.material_names, self.material_names.HELMET)
            material_name = helmet_material.name
        elif mesh_body_part_name == 'HelmetEmo':  # Frem
            helmet_material = self.create_hair_material(self.material_names, self.material_names.HELMET_EMO)
            material_name = helmet_material.name
        elif mesh_body_part_name == 'Gauntlet':  # Wrioth
            gauntlet_material = self.create_body_material(self.material_names, self.material_names.GAUNTLET)
            material_name = gauntlet_material.name
        elif mesh_body_part_name == 'Leather':
            leather_material = self.create_body_material(self.material_names, self.material_names.LEATHER)
            material_name = leather_material.name
        elif mesh_body_part_name == 'Glass':
            glass_material = self.create_body_material(self.material_names, self.material_names.GLASS)
            material_name = glass_material.name
        elif mesh_body_part_name == 'Glass_Eff':
            glass_material = self.create_glass_material(self.material_names, self.material_names.GLASS_EFF)
            if glass_material:
                self.__set_glass_star_cloak_toggle(glass_material, False)
                glass_method_set = True
                glass_material.blend_method = 'BLEND'
                glass_material.shadow_method = 'NONE'
                glass_material.show_transparent_back = False
                material_name = glass_material.name
        elif mesh_body_part_name and mesh_body_part_name.startswith(ShaderMaterialNameKeywords.SKILLOBJ):
            skillobj_material = self.create_body_material(self.material_names, self.material_names.SKILLOBJ)
            skillobj_material.name = skillobj_material.name.replace(ShaderMaterialNameKeywords.SKILLOBJ, mesh_body_part_name)
            material_name = skillobj_material.name
        elif mesh_body_part_name == 'Skirt':
            skirt_material = self.create_body_material(self.material_names, self.material_names.SKIRT)
            material_name = skirt_material.name
        elif mesh_body_part_name == 'Pupil':
            pupil_material = self.create_body_material(self.material_names, self.material_names.PUPIL)
            if pupil_material:
                material_name = pupil_material.name
        elif mesh_body_part_name == 'New Pupil':
            new_pupil_name = getattr(self.material_names, 'NEW_PUPIL', f'{self.material_names.MATERIAL_PREFIX}New Pupil')
            pupil_material = self.create_body_material(self.material_names, new_pupil_name)
            if pupil_material:
                material_name = pupil_material.name
        elif mesh_body_part_name and 'Item' in mesh_body_part_name:  # NPCs
            item_material = self.create_body_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            material_name = item_material.name
        elif mesh_body_part_name and ('Screw' in mesh_body_part_name or 'Hat' in mesh_body_part_name):  # Aranaras
            new_material = self.create_body_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            material_name = new_material.name
        elif mesh_body_part_name and 'Others' in mesh_body_part_name:  # NPCs, Frem Penguins
            new_material = self.create_body_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            material_name = new_material.name
        elif mesh_body_part_name and 'crystal' in mesh_body_part_name.lower():
            crystal_material = self.create_crystal_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            material_name = crystal_material.name
        elif mesh_body_part_name and mesh_body_part_name not in ['Face', 'Body', 'Hair', 'Eye', 'Dress', 'Arm', 'Cloak', 'VFX', 'StarCloak', 'Pupil', 'Pupila', 'New Pupil']:
            # Fallback for completely unknown materials (like 'Stockings', 'Wings', etc)
            new_material = self.create_body_material(self.material_names, f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
            material_name = new_material.name
        return material_name

    def __clone_material_and_rename(self, material_slot, mesh_body_part_name_template, mesh_body_part_name):
        template_material = bpy.data.materials.get(mesh_body_part_name_template)
        if not template_material:
            print(f'WARNING: Template material "{mesh_body_part_name_template}" not found, cannot clone for "{mesh_body_part_name}"')
            return None
        new_material = template_material.copy()
        new_material.name = f'{self.material_names.MATERIAL_PREFIX}{mesh_body_part_name}'
        new_material.use_fake_user = True

        self.__transfer_diffuse_texture(material_slot.material, new_material)
        material_slot.material = new_material
        return new_material

    def __transfer_diffuse_texture(self, old_material, new_material):
        if not old_material or not old_material.use_nodes or not new_material or not new_material.use_nodes:
            return
            
        old_image = None
        for node in old_material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                old_image = node.image
                break
                
        if not old_image:
            return
            
        diffuse_nodes = find_all_image_nodes_by_category(new_material.node_tree, 'diffuse')
        for node in diffuse_nodes:
            node.image = old_image

    def __set_glass_star_cloak_toggle(self, material, value):
        vfx_shader_node = material.node_tree.nodes.get(self.shader_node_names.VFX_SHADER)
        vfx_shader_node.inputs.get(self.shader_node_names.TOGGLE_GLASS_STAR_CLOAK).default_value = value

    def __set_star_cloak_type(self, material, original_material_name):
        for star_cloak_type in StarCloakTypes._member_names_:
            if star_cloak_type.lower() in original_material_name.lower():
                vfx_shader_node = material.node_tree.nodes.get(self.shader_node_names.VFX_SHADER)
                vfx_shader_node.inputs.get(self.shader_node_names.STAR_CLOAK_TYPE).default_value = getattr(StarCloakTypes, star_cloak_type).value

    def create_face_material(self, shader_material_names: ShaderMaterialNames, material_name):
        face_material = bpy.data.materials.get(material_name)
        if not face_material:
            face_template = bpy.data.materials.get(shader_material_names.FACE)
            if face_template:
                face_material = face_template.copy()
                face_material.name = material_name
                face_material.use_fake_user = True
        return face_material

    def __clear_material_images(self, material):
        if not material or not material.use_nodes or not material.node_tree:
            return
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                node.image = None

    def create_body_material(self, shader_material_names: ShaderMaterialNames, material_name):
        body_material = bpy.data.materials.get(material_name)
        if not body_material:
            body_template = bpy.data.materials.get(shader_material_names.BODY)
            if body_template:
                body_material = body_template.copy()
                body_material.name = material_name
                body_material.use_fake_user = True
                self.__clear_material_images(body_material)
        return body_material

    def create_hair_material(self, shader_material_names: ShaderMaterialNames, material_name):
        hair_material = bpy.data.materials.get(material_name)
        if not hair_material:
            hair_template = bpy.data.materials.get(shader_material_names.HAIR)
            if hair_template:
                hair_material = hair_template.copy()
                hair_material.name = material_name
                hair_material.use_fake_user = True
                self.__clear_material_images(hair_material)
        return hair_material

    def create_glass_material(self, shader_material_names: ShaderMaterialNames, material_name):
        glass_material = bpy.data.materials.get(material_name)
        vfx_template_material = bpy.data.materials.get(shader_material_names.VFX)
        if vfx_template_material and not glass_material:
            glass_material = vfx_template_material.copy()
            glass_material.name = material_name
            glass_material.use_fake_user = True
            self.__clear_material_images(glass_material)
        return glass_material

    def setup_crystal_material_nodes(self, crystal_material):
        """
        Applies the Crystal transparency shader setup:
        (Lightmap Color if present, else Diffuse Color) -> Separate Color (Red) -> Greater Than (0.5) -> Mix Shader (Factor)
        with Transparent BSDF (Shader 1) and Body Shader BSDF (Shader 2) -> Material Output (Surface).
        """
        if not crystal_material or not crystal_material.use_nodes or not crystal_material.node_tree:
            return

        tree = crystal_material.node_tree

        output_node = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not output_node:
            return

        body_shader = tree.nodes.get('Body Shader') or \
                      tree.nodes.get('PrimoToon') or \
                      tree.nodes.get('HoYoToon') or \
                      tree.nodes.get('Group.001') or \
                      next((n for n in tree.nodes if n.type == 'GROUP' and 'BSDF' in n.outputs), None)

        lightmap_img_nodes = [n for n in tree.nodes if n.type == 'TEX_IMAGE' and 'lightmap' in (n.name + " " + (n.label or "")).lower()]
        has_lightmap_image = any(n.image is not None for n in lightmap_img_nodes)

        color_source_socket = None
        # 1. Try Lightmap if an image is loaded
        if has_lightmap_image:
            if body_shader and 'Lightmap Color' in body_shader.inputs and body_shader.inputs['Lightmap Color'].links:
                color_source_socket = body_shader.inputs['Lightmap Color'].links[0].from_socket
            elif tree.nodes.get('Lightmap Lerp') and 'Color' in tree.nodes['Lightmap Lerp'].outputs:
                color_source_socket = tree.nodes['Lightmap Lerp'].outputs['Color']
            elif lightmap_img_nodes:
                for n in lightmap_img_nodes:
                    if n.image and 'Color' in n.outputs:
                        color_source_socket = n.outputs['Color']
                        break

        # 2. Fallback to Diffuse Lerp / Diffuse Color
        if not color_source_socket:
            if body_shader and 'Diffuse Color' in body_shader.inputs and body_shader.inputs['Diffuse Color'].links:
                color_source_socket = body_shader.inputs['Diffuse Color'].links[0].from_socket
            elif tree.nodes.get('Diffuse Lerp') and 'Color' in tree.nodes['Diffuse Lerp'].outputs:
                color_source_socket = tree.nodes['Diffuse Lerp'].outputs['Color']
            else:
                diffuse_nodes = [n for n in tree.nodes if n.type == 'TEX_IMAGE' and 'diffuse' in (n.name + " " + (n.label or "")).lower()]
                if diffuse_nodes and 'Color' in diffuse_nodes[0].outputs:
                    color_source_socket = diffuse_nodes[0].outputs['Color']

        bsdf_loc_x = body_shader.location.x if body_shader else 0
        bsdf_loc_y = body_shader.location.y if body_shader else 0

        mix_node = next((n for n in tree.nodes if n.type == 'MIX_SHADER'), None)
        trans_node = next((n for n in tree.nodes if n.type == 'BSDF_TRANSPARENT'), None)
        math_node = next((n for n in tree.nodes if n.type == 'MATH' and getattr(n, 'operation', '') == 'GREATER_THAN'), None)
        sep_node = next((n for n in tree.nodes if n.type in ('SEPARATE_COLOR', 'SEPARATE_RGB')), None)

        if not mix_node:
            mix_node = tree.nodes.new('ShaderNodeMixShader')
            mix_node.location = (bsdf_loc_x + 300, bsdf_loc_y)

        if not trans_node:
            trans_node = tree.nodes.new('ShaderNodeBsdfTransparent')
            trans_node.location = (bsdf_loc_x + 300, bsdf_loc_y - 150)
            if 'Color' in trans_node.inputs:
                trans_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)

        if not math_node:
            math_node = tree.nodes.new('ShaderNodeMath')
            math_node.location = (bsdf_loc_x + 100, bsdf_loc_y - 300)
            math_node.operation = 'GREATER_THAN'
            math_node.inputs[1].default_value = 0.5
            math_node.use_clamp = False

        if not sep_node:
            if hasattr(bpy.types, "ShaderNodeSeparateColor"):
                sep_node = tree.nodes.new('ShaderNodeSeparateColor')
                if hasattr(sep_node, "mode"):
                    sep_node.mode = 'RGB'
            else:
                sep_node = tree.nodes.new('ShaderNodeSeparateRGB')
            sep_node.location = (bsdf_loc_x - 100, bsdf_loc_y - 300)

        if color_source_socket:
            if sep_node.inputs[0].links:
                for l in list(sep_node.inputs[0].links):
                    tree.links.remove(l)
            tree.links.new(color_source_socket, sep_node.inputs[0])

        red_socket = sep_node.outputs.get('Red') or sep_node.outputs.get('R') or sep_node.outputs[0]
        if not math_node.inputs[0].links:
            tree.links.new(red_socket, math_node.inputs[0])

        if not mix_node.inputs[0].links:
            tree.links.new(math_node.outputs[0], mix_node.inputs[0])

        if not mix_node.inputs[1].links:
            tree.links.new(trans_node.outputs[0], mix_node.inputs[1])

        if body_shader and 'BSDF' in body_shader.outputs and not mix_node.inputs[2].links:
            tree.links.new(body_shader.outputs['BSDF'], mix_node.inputs[2])

        if not output_node.inputs['Surface'].links or output_node.inputs['Surface'].links[0].from_node != mix_node:
            tree.links.new(mix_node.outputs[0], output_node.inputs['Surface'])

        try:
            crystal_material.blend_method = 'BLEND'
        except Exception:
            pass

        try:
            crystal_material.shadow_method = 'NONE'
        except Exception:
            pass

        try:
            crystal_material.show_transparent_back = False
        except Exception:
            pass

    def create_crystal_material(self, shader_material_names: ShaderMaterialNames, material_name):
        crystal_material = bpy.data.materials.get(material_name)
        if not crystal_material:
            body_template = bpy.data.materials.get(shader_material_names.BODY)
            if body_template:
                crystal_material = body_template.copy()
                crystal_material.name = material_name
                crystal_material.use_fake_user = True
                self.__clear_material_images(crystal_material)
                self.setup_crystal_material_nodes(crystal_material)
        else:
            self.setup_crystal_material_nodes(crystal_material)
        return crystal_material

    '''
    This method was used for V1 shader and should NOT be used for V2 shader because the group name is different.
    The intent was purely to have separate shader nodes and matching the name to the material.
    This does not seem necessary. Haven't checked if there's a performance impact
    '''
    def __clone_shader_node_and_rename(self, material, mesh_body_part_name):
        new_shader_node_tree = material.node_tree.nodes.get('Group.001').node_tree.copy()
        new_shader_node_tree.name = f'miHoYo - Genshin {mesh_body_part_name}'
        return new_shader_node_tree


class HonkaiStarRailDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    MESH_IGNORE_LIST = [
        'Face_Mask'
    ]

    def __init__(self, blender_operator, context, material_names: ShaderMaterialNames):
        self.blender_operator: Operator = blender_operator
        self.context: Context = context
        self.shader_material_names = material_names

    def __transfer_diffuse_texture(self, old_material, new_material):
        if not old_material or not old_material.use_nodes or not new_material or not new_material.use_nodes:
            return
            
        old_image = None
        for node in old_material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                old_image = node.image
                break
                
        if not old_image:
            return
            
        diffuse_nodes = find_all_image_nodes_by_category(new_material.node_tree, 'diffuse')
        if not diffuse_nodes:
            for node in new_material.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    n_low = (node.name + " " + (node.label or "")).lower()
                    if any(k in n_low for k in ['diffuse', 'color', 'srgb', '画像テクスチャ']) and not any(k in n_low for k in ['lightmap', 'ramp', 'normal', 'mask']):
                        diffuse_nodes.append(node)
        for node in diffuse_nodes:
            node.image = old_image

    def replace_default_materials(self):
        meshes = [mesh for mesh in bpy.context.scene.objects if mesh.type == 'MESH' and mesh.name not in self.MESH_IGNORE_LIST]

        for mesh in meshes:
            for material_slot in mesh.material_slots:
                material_name = material_slot.name
                
                if material_name.startswith(self.shader_material_names.MATERIAL_PREFIX):
                    continue

                mesh_body_part_name = self.find_body_part_name(material_name)

                # Another hacky-solution, some characters only have a "Body" material, but the shader materials
                # only have Body1, Body2 and Body_A. Should request Shader to have a "Body" material
                # Some characters have a mismatch between Texture and Material Data too... (Body_Color_A and Body)
                # Checklist:
                # 1. Materials
                # 2. Textures
                # 3. Material Data
                # The best fix would be to create a "Body" material via code in case the shader is updated to have the same
                if mesh_body_part_name == 'Body':
                    body_material = self.create_body_material(mesh, self.shader_material_names.BODY)
                    material_name = body_material.name
                elif mesh_body_part_name == 'Body1':  # for StellarToon
                    body_material = self.create_body_material(mesh, self.shader_material_names.BODY1)
                    material_name = body_material.name
                elif mesh_body_part_name == 'Body2':  # for StellarToon
                    body_material = self.create_body_material(mesh, self.shader_material_names.BODY2)
                    material_name = body_material.name
                elif mesh_body_part_name == 'Body3':
                    body_material = self.create_body_material(mesh, self.shader_material_names.BODY3)
                    material_name = body_material.name
                elif mesh_body_part_name ==  'Body_Trans' or mesh_body_part_name == 'Mat_Trans':
                    body_material = self.create_body_trans_material(mesh, self.shader_material_names.BODY_TRANS) 
                    mesh_body_part_name = 'Body_Trans'
                    material_name = body_material.name
                elif mesh_body_part_name ==  'Body2_Trans':
                    body_material = self.create_body_trans_material(mesh, self.shader_material_names.BODY2_TRANS) 
                    material_name = body_material.name
                elif mesh_body_part_name in ['EyeShadow', 'EyeSpecular', 'Eye_Specular', 'EyeStar']:
                    eyeshadow_material = self.create_body_material(mesh, f'{self.shader_material_names.MATERIAL_PREFIX}{mesh_body_part_name}')
                    material_name = eyeshadow_material.name
                elif mesh_body_part_name == 'Face':
                    face_material = self.create_body_material(mesh, self.shader_material_names.FACE)
                    material_name = face_material.name
                elif 'Coat' in mesh_body_part_name:
                    body_material = self.create_body_material(mesh, self.shader_material_names.COAT)
                    material_name = body_material.name
                elif 'Weapon' in mesh_body_part_name:
                    weapon_material = self.create_weapon_materials(mesh_body_part_name)
                    material_name = weapon_material.name
                elif 'Handbag' in mesh_body_part_name:
                    handbag_material = self.create_weapon_materials(mesh_body_part_name)
                    material_name = handbag_material.name
                elif 'Kendama' in mesh_body_part_name:
                    handbag_material = self.create_weapon_materials(mesh_body_part_name)
                    material_name = handbag_material.name
                else:  # Fallback, best guess attempt by creating a Body-type material for the unknown material body part
                    material_name = f'{self.shader_material_names.MATERIAL_PREFIX}{mesh_body_part_name}'
                    self.create_body_material(mesh, material_name)

                honkai_star_rail_material = bpy.data.materials.get(material_name)

                if honkai_star_rail_material:
                    if material_slot.material:
                        honkai_star_rail_material["_original_material_name"] = material_slot.material.name
                        if material_slot.material.use_nodes and material_slot.material.node_tree:
                            for node in material_slot.material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE' and node.image and node.image.name:
                                    honkai_star_rail_material["_original_fbx_texture"] = node.image.name
                                    break
                    self.__transfer_diffuse_texture(material_slot.material, honkai_star_rail_material)
                    material_slot.material = honkai_star_rail_material
                else:
                    self.blender_operator.report({'WARNING'}, f'Ignoring unknown mesh body part in character model: {mesh_body_part_name} / Material: {material_name}')
                    continue
        self.blender_operator.report({'INFO'}, 'Replaced default materials with Genshin shader materials...')

    def find_body_part_name(self, material_name):
        if material_name.startswith('Eff_') or 'Eff_' in material_name or material_name.startswith('Effect_'):
            return material_name

        if '_Mat_' in material_name:
            suffix = material_name.split('_Mat_')[1]
            return suffix

        expected_format_body_part_name = self.__expected_format_body_part_name_search(material_name)
        naive_search_body_part_name = self.__naive_body_part_name_search(material_name)
        body_part_name = ''

        # If the two are equal, then we're confident that the body part name is correct (pick either)
        # Elif the naive search found none of the expected body part names, return expected format search body part name
        # Else expected format and naive searches do not equal, use the naive search (pulls from list of expected body part names)
        if expected_format_body_part_name == naive_search_body_part_name:
            body_part_name = expected_format_body_part_name
        elif expected_format_body_part_name and not naive_search_body_part_name:
            body_part_name = expected_format_body_part_name
        else:
            return naive_search_body_part_name
        return body_part_name

    '''
    Expected Format Search: Search for body part name at expected location, at the end of the material name (ex. 'Body')
    '''
    def __expected_format_body_part_name_search(self, material_name):
        if material_name.endswith('_S') or material_name.endswith('_D'):
            return material_name.split('_')[-2]
        return material_name.split('_')[-1]

    '''
    Naive Search: Search for body part name in material name
    '''
    def __naive_body_part_name_search(self, material_name):
        EXPECTED_BODY_PART_NAMES = [
            'Hair',
            'Body1',
            'Body2_Trans',
            'Body2',
            'Body3',
            'Body_Trans',
            'Mat_Trans',
            'EyeShadow',
            'EyeSpecular',
            'Eye_Specular',
            'EyeStar',
            'Face',
            'Weapon_Trans',
            'Body',  # Important this is last in the list because it could interfere with Body1 and Body2
        ]

        for expected_body_part_name in EXPECTED_BODY_PART_NAMES:
            if expected_body_part_name in material_name:
                return expected_body_part_name

    def create_body_material(self, mesh, material_name):
        body_material = bpy.data.materials.get(material_name)
        if not body_material:
            body_material = bpy.data.materials.get(self.shader_material_names.BODY1).copy()
            body_material.name = material_name
            body_material.use_fake_user = True
        return body_material

    def create_body_trans_material(self, mesh, material_name):
        body_material = bpy.data.materials.get(material_name)
        if not body_material:
            body_material = bpy.data.materials.get(self.shader_material_names.BODY_TRANS).copy()
            body_material.name = material_name
            body_material.use_fake_user = True
        return body_material

    def create_weapon_materials(self, mesh_body_part_name):
        weapon_material_name = \
            f'{self.shader_material_names.MATERIAL_PREFIX}{mesh_body_part_name}' if \
            mesh_body_part_name == 'Weapon01' or \
            mesh_body_part_name == 'Weapon02' or \
            mesh_body_part_name == 'Weapon1' or \
            mesh_body_part_name == 'Weapon_Trans' or \
            mesh_body_part_name == 'Handbag' or \
            mesh_body_part_name == 'Kendama' else \
            f'{self.shader_material_names.WEAPON}'
        weapon_material = bpy.data.materials.get(weapon_material_name)

        if not weapon_material:
            weapon_material = bpy.data.materials.get(f'{self.shader_material_names.WEAPON}').copy()
            weapon_material.name = weapon_material_name
            weapon_material.use_fake_user = True
        return weapon_material


class StellarToonDefaultMaterialReplacer(HonkaiStarRailDefaultMaterialReplacer):
    MESH_IGNORE_LIST = [
        'Face_Mask'
    ]

    ENABLE_TRANSPARENCY = 'Enable Transparency'

    def __init__(self, blender_operator, context, material_names: ShaderMaterialNames):
        self.blender_operator: Operator = blender_operator
        self.context: Context = context
        self.shader_material_names = material_names

    def replace_default_materials(self):
        super().replace_default_materials()

    def _is_trans_material(self, name: str) -> bool:
        n_low = name.lower()
        return ('_trans' in n_low or 
                'transparent' in n_low or 
                'eyespecular' in n_low or 
                'eye_specular' in n_low or 
                'eyeshadow' in n_low or
                'eyestar' in n_low or
                'body_d1' in n_low or
                '_d1' in n_low or
                'body1_d1' in n_low or
                ('robin' in n_low and 'd1' in n_low))

    def _set_transparency(self, material, enabled: bool):
        if not material or not material.node_tree:
            return
        val = 1.0 if enabled else 0.0
        for node in material.node_tree.nodes:
            inp = node.inputs.get(self.ENABLE_TRANSPARENCY)
            if inp:
                inp.default_value = val
            if node.type == 'GROUP' and node.node_tree:
                for sub_node in node.node_tree.nodes:
                    sub_inp = sub_node.inputs.get(self.ENABLE_TRANSPARENCY)
                    if sub_inp:
                        sub_inp.default_value = val

    def create_body_material(self, mesh, material_name):
        body_material = bpy.data.materials.get(material_name)
        if not body_material:
            body_material = bpy.data.materials.get(self.shader_material_names.BASE).copy()
            body_material.name = material_name
            body_material.use_fake_user = True
        is_trans = self._is_trans_material(material_name)
        self._set_transparency(body_material, is_trans)
        return body_material

    def create_body_trans_material(self, mesh, material_name):
        body_material = bpy.data.materials.get(material_name)
        if not body_material:
            body_material = bpy.data.materials.get(self.shader_material_names.BASE).copy()
            body_material.name = material_name
            body_material.use_fake_user = True
        self._set_transparency(body_material, True)
        return body_material

    def create_weapon_materials(self, mesh_body_part_name):
        weapon_material = super().create_weapon_materials(mesh_body_part_name)
        is_trans = self.shader_material_names.WEAPON_TRANS in weapon_material.name or '_Trans' in weapon_material.name or '_trans' in weapon_material.name
        self._set_transparency(weapon_material, is_trans)
        return weapon_material


class PunishingGrayRavenDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    MESH_IGNORE_LIST = []

    def __init__(self, blender_operator, context):
        self.blender_operator: Operator = blender_operator
        self.context: Context = context

    def replace_default_materials(self):
        meshes = [mesh for mesh in bpy.context.scene.objects if mesh.type == 'MESH' and mesh.name not in self.MESH_IGNORE_LIST]

        for mesh in meshes:
            for material_slot in mesh.material_slots:
                material_name = material_slot.name
                
                if material_name.startswith(JaredNytsPunishingGrayRavenShaderMaterialNames.MATERIAL_PREFIX):
                    continue

                material_identifier_service = PunishingGrayRavenMaterialIdentifierService()
                mesh_body_part_name = material_identifier_service.get_body_part_name(material_name) or \
                    self.find_body_part_name(material_name)  # If in different naming schema, fallback to best guess mode
                mesh_body_part_name = \
                    material_identifier_service.get_body_part_name_of_shared_material(material_name) or \
                    mesh_body_part_name
                if 'Face' in mesh_body_part_name:  # 6.Karenina_Ember (material w/ Face in it, but no called just Face)
                    mesh_body_part_name = 'Face'
                if 'OL' in mesh_body_part_name:  # 9S (Generic), Bianca_Veritas (Ink-lit Hermit)
                    mesh_body_part_name = mesh_body_part_name.replace('OL', '')

                if mesh_body_part_name and 'Alpha' not in mesh_body_part_name:
                    material_type = JaredNytsPunishingGrayRavenShaderMaterialNames.HAIR if 'Hair' in mesh_body_part_name else \
                        JaredNytsPunishingGrayRavenShaderMaterialNames.MAIN
                    material_name = f'{JaredNytsPunishingGrayRavenShaderMaterialNames.MATERIAL_PREFIX}{mesh_body_part_name}'
                    self.create_main_material(mesh, material_type, material_name)
                elif mesh_body_part_name and 'Alpha' in mesh_body_part_name:
                    material_name = JaredNytsPunishingGrayRavenShaderMaterialNames.ALPHA
                    mesh_body_part_name = 'Alpha'
                else:
                    self.blender_operator.report({'WARNING'}, f'Ignoring unknown mesh body part in character model: {mesh_body_part_name} / Material: {material_name}')
                    continue

                punishing_gray_raven_material = bpy.data.materials.get(
                    f'{JaredNytsPunishingGrayRavenShaderMaterialNames.MATERIAL_PREFIX}{mesh_body_part_name}'
                )

                if punishing_gray_raven_material:
                    material_slot.material = punishing_gray_raven_material
                else:
                    self.blender_operator.report({'WARNING'}, f'Ignoring unknown mesh body part in character model: {mesh_body_part_name} / Material: {material_name}')
                    continue
        self.blender_operator.report({'INFO'}, 'Replaced default materials with Genshin shader materials...')

    def find_body_part_name(self, material_name):
        expected_format_body_part_name = self.__expected_format_body_part_name_search(material_name)
        naive_search_body_part_name = self.__naive_body_part_name_search(material_name)
        body_part_name = ''

        # If the two are equal, then we're confident that the body part name is correct (pick either)
        # Elif the naive search found none of the expected body part names, return expected format search body part name
        # Else expected format and naive searches do not equal, use the naive search (pulls from list of expected body part names)
        if expected_format_body_part_name == naive_search_body_part_name:
            body_part_name = expected_format_body_part_name
        elif expected_format_body_part_name and not naive_search_body_part_name:
            body_part_name = expected_format_body_part_name
        else:
            return naive_search_body_part_name
        return body_part_name

    '''
    Expected Format Search: Search for body part name at expected location, at the end of the material name (ex. 'Body')
    '''
    def __expected_format_body_part_name_search(self, material_name):
        armature =  [object for object in bpy.data.objects if object.type == 'ARMATURE'][0]
        return material_name.split(armature.name)[-1]

    '''
    Naive Search: Search for body part name in material name
    '''
    def __naive_body_part_name_search(self, material_name):
        EXPECTED_BODY_PART_NAMES = [
            'Alpha',
            'Alpha01',
            'Alpha02',
            'Upper',
            'Down',
            'Eye',
            'Face',
            'Cloth01',
            'Cloth02',
            'Hair01',
            'Hair02',
            'Mantilla',
            'Pipe',
            'Weapon',
            'Cloth',
            'Hair',
            'Body',  # Default to Body last
        ]

        for expected_body_part_name in EXPECTED_BODY_PART_NAMES:
            if expected_body_part_name in material_name:
                return expected_body_part_name

    def create_main_material(self, mesh, material_type: ShaderMaterialNames, material_name):
        body_material = bpy.data.materials.get(material_name)
        if not body_material:
            body_material = bpy.data.materials.get(material_type).copy()
            body_material.name = material_name
            body_material.use_fake_user = True
        return body_material


class ZenlessZoneZeroDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context

    def replace_default_materials(self):
        selected_shader = getattr(bpy.context.scene, 'zzz_shader_type', 'KYTHERA') if hasattr(bpy, 'context') and hasattr(bpy.context, 'scene') else 'KYTHERA'
        meshes = [mesh for mesh in bpy.context.scene.objects if mesh.type == 'MESH']

        # Locate Materials folder to check JSON definitions
        char_folder = self.blender_operator.file_directory if hasattr(self.blender_operator, "file_directory") and self.blender_operator.file_directory else ""
        if not char_folder and hasattr(self.blender_operator, "filepath") and self.blender_operator.filepath:
            char_folder = os.path.dirname(self.blender_operator.filepath)
        if not char_folder:
            char_folder = bpy.path.abspath("//")

        materials_dirs = [
            char_folder,
            os.path.join(char_folder, "Materials"),
            os.path.join(os.path.dirname(char_folder), "Materials") if char_folder else ""
        ]
        mat_dir = None
        for d in materials_dirs:
            if d and os.path.isdir(d) and any(f.lower().endswith(".json") for f in os.listdir(d)):
                mat_dir = d
                break

        def is_untextured_material_json(name):
            if not mat_dir or not name:
                return False
            import re, json
            m_raw = re.sub(r'\.\d+$', '', name.strip())
            clean_key = lambda k: re.sub(r'\.\d+$', '', k.lower().replace("mat_", "").replace("_ui", "")).strip(" _-")
            target_clean = clean_key(m_raw)
            for jf in os.listdir(mat_dir):
                if not jf.lower().endswith(".json"):
                    continue
                j_stem = os.path.splitext(jf)[0]
                if j_stem.lower() == m_raw.lower() or clean_key(j_stem) == target_clean:
                    try:
                        with open(os.path.join(mat_dir, jf), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        tex_envs = data.get("m_SavedProperties", {}).get("m_TexEnvs", {})
                        for slot, val in tex_envs.items():
                            if isinstance(val, dict):
                                tex_info = val.get("m_Texture", {})
                                if isinstance(tex_info, dict) and not tex_info.get("IsNull", True):
                                    return False  # has at least one valid texture
                        return True  # JSON exists and all textures are null
                    except Exception:
                        pass
            return False

        if selected_shader == 'LEGACY':
            # --- LEGACY ZZZ SHADER REPLACEMENT ---
            for mesh in meshes:
                if len(mesh.material_slots) == 0:
                    mesh.data.materials.append(None)

                for slot in mesh.material_slots:
                    mat = slot.material
                    matname = mat.name.lower() if mat else mesh.name.lower()

                    if mat and is_untextured_material_json(mat.name):
                        continue

                    if mat and mat.name.startswith("ZZZ Shader"):
                        continue

                    target_mat_name = None
                    if "hair" in matname:
                        target_mat_name = "ZZZ Shader Hair"
                    elif "eyebrow" in matname or "brow" in matname or "眉" in matname:
                        target_mat_name = "ZZZ Shader Face"
                    elif "eyehighlight" in matname or "highlight" in matname:
                        target_mat_name = "ZZZ Shader EyeHighlights" if bpy.data.materials.get("ZZZ Shader EyeHighlights") else "ZZZ Shader Face"
                    elif "eye" in matname and matname != "eye transparent":
                        target_mat_name = "ZZZ Shader Eye" if bpy.data.materials.get("ZZZ Shader Eye") else "ZZZ Shader Face"
                    elif "face" in matname:
                        target_mat_name = "ZZZ Shader Face"
                    elif any(k in matname for k in ["body 2", "body2", "body_2", "wing", "ala", "feather", "dress", "cape", "coat", "jacket"]):
                        target_mat_name = "ZZZ Shader Body 2"
                    elif any(k in matname for k in ["body 3", "body3", "body_3", "leg", "tail", "shoe", "boot", "foot"]):
                        target_mat_name = "ZZZ Shader Body3/Leg"
                    elif any(k in matname for k in ["weapon", "wpn", "equip", "sword", "blade", "spear", "lance", "gun", "prop"]):
                        if any(k in matname for k in ["weapon 2", "weapon2", "weapon_2", "map2"]):
                            target_mat_name = "ZZZ Shader Weapon 2" if bpy.data.materials.get("ZZZ Shader Weapon 2") else "ZZZ Shader Weapon"
                        else:
                            target_mat_name = "ZZZ Shader Weapon"
                    elif "body" in matname:
                        target_mat_name = "ZZZ Shader Body"
                    else:
                        mesh_lower = mesh.name.lower()
                        if "hair" in mesh_lower:
                            target_mat_name = "ZZZ Shader Hair"
                        elif "face" in mesh_lower:
                            target_mat_name = "ZZZ Shader Face"
                        elif any(k in mesh_lower for k in ["wing", "ala", "body2", "body 2", "dress", "cape"]):
                            target_mat_name = "ZZZ Shader Body 2"
                        elif any(k in mesh_lower for k in ["leg", "tail", "body3", "body 3"]):
                            target_mat_name = "ZZZ Shader Body3/Leg"
                        elif any(k in mesh_lower for k in ["weapon", "wpn", "sword"]):
                            target_mat_name = "ZZZ Shader Weapon"
                        else:
                            target_mat_name = "ZZZ Shader Body"

                    if target_mat_name:
                        template_mat = bpy.data.materials.get(target_mat_name)
                        if template_mat:
                            orig_tex_name = None
                            if mat and mat.node_tree:
                                for n in mat.node_tree.nodes:
                                    if n.type == 'TEX_IMAGE' and n.image and n.image.name:
                                        orig_tex_name = n.image.name
                                        break
                            new_mat = template_mat.copy()
                            if orig_tex_name:
                                new_mat["_original_fbx_texture"] = orig_tex_name
                            if mat and mat.name:
                                new_mat["_original_material_name"] = mat.name
                            name_base = mat.name if mat else mesh.name
                            new_mat.name = f"ZZZ Shader {name_base}"
                            new_mat.use_fake_user = True
                            slot.material = new_mat

            weapon_mats = [m for m in bpy.data.materials if m.name.startswith("ZZZ Shader") and "weapon" in m.name.lower()]
            main_weapon_mat = weapon_mats[0] if weapon_mats else bpy.data.materials.get("ZZZ Shader Weapon")
            for mesh in meshes:
                m_lower = mesh.name.lower()
                if any(k in m_lower for k in ["weapon", "wpn", "equip", "sword", "blade", "spear", "lance", "gun", "prop"]):
                    for slot in mesh.material_slots:
                        if not slot.material and main_weapon_mat:
                            new_mat = main_weapon_mat.copy()
                            new_mat.name = f"ZZZ Shader {mesh.name}"
                            new_mat.use_fake_user = True
                            slot.material = new_mat

            self.blender_operator.report({'INFO'}, "Replaced default materials with ZZZ Shader materials...")

        else:
            # --- KYTHERA SHADER REPLACEMENT ---
            # Find Kythera face and main shader template materials dynamically
            face_template = None
            for mat in bpy.data.materials:
                if not mat.node_tree:
                    continue
                m_low = mat.name.lower()
                if ("face" in m_low or "cara" in m_low or "head" in m_low) and \
                   ("kythera" in m_low or "kyteraz" in m_low or "zzz" in m_low) and \
                   not mat.name.startswith("ZZZ MAT_") and not mat.name.startswith("ZZZ Shader") and not mat.name.endswith("Outlines"):
                    face_template = mat
                    break

            if not face_template:
                for mat in bpy.data.materials:
                    if not mat.node_tree or mat.name.startswith("ZZZ MAT_") or mat.name.endswith("Outlines"):
                        continue
                    if any(n.type == 'GROUP' and n.node_tree and "face" in n.node_tree.name.lower() and ("kythera" in n.node_tree.name.lower() or "kyteraz" in n.node_tree.name.lower() or "zzz" in n.node_tree.name.lower()) for n in mat.node_tree.nodes):
                        face_template = mat
                        break

            shader_template = None
            for mat in bpy.data.materials:
                if not mat.node_tree:
                    continue
                m_low = mat.name.lower()
                if ("kythera" in m_low or "kyteraz" in m_low) and \
                   ("face" not in m_low and "cara" not in m_low and "head" not in m_low) and \
                   not mat.name.startswith("ZZZ MAT_") and not mat.name.startswith("ZZZ Shader") and not mat.name.endswith("Outlines"):
                    shader_template = mat
                    break

            if not shader_template:
                for mat in bpy.data.materials:
                    if not mat.node_tree or mat.name.startswith("ZZZ MAT_") or mat.name.endswith("Outlines"):
                        continue
                    if any(n.type == 'GROUP' and n.node_tree and "face" not in n.node_tree.name.lower() and ("kythera" in n.node_tree.name.lower() or "kyteraz" in n.node_tree.name.lower() or "zzz" in n.node_tree.name.lower()) for n in mat.node_tree.nodes):
                        shader_template = mat
                        break

            for mesh in meshes:
                if len(mesh.material_slots) == 0:
                    mesh.data.materials.append(None)

                for slot in mesh.material_slots:
                    mat = slot.material
                    matname = mat.name.lower() if mat else mesh.name.lower()

                    # Handle hair shadow mesh / material
                    if "hairshadow" in matname or "hairshadow" in mesh.name.lower():
                        transp_mat = bpy.data.materials.get("Transp OL")
                        if transp_mat:
                            slot.material = transp_mat
                        continue

                    # If the JSON explicitly defines that this material has no textures, keep the base FBX material intact
                    if mat and is_untextured_material_json(mat.name):
                        continue

                    # If already replaced with a cloned Kythera ZZZ material, skip
                    if mat and (mat.name.startswith("ZZZ ") or mat.name.startswith("Kythera")):
                        continue

                    is_face = any(k in matname for k in ["face", "eyebrow", "brow", "眉", "eye", "eyelash", "pupil", "iris", "highlight"])
                    template_mat = face_template if is_face else shader_template

                    if template_mat:
                        orig_tex_name = None
                        if mat and mat.node_tree:
                            for n in mat.node_tree.nodes:
                                if n.type == 'TEX_IMAGE' and n.image and n.image.name:
                                    orig_tex_name = n.image.name
                                    break

                        new_mat = template_mat.copy()
                        if orig_tex_name:
                            new_mat["_original_fbx_texture"] = orig_tex_name
                        if mat and mat.name:
                            new_mat["_original_material_name"] = mat.name
                        
                        # Ensure meaningful name preserving mesh context (e.g. Wing, Dress, Leg, Hair, Body)
                        if mat and mat.name and not mat.name.lower().startswith(("material", "default", "node", "untitled")):
                            if any(k in mesh.name.lower() for k in ["wing", "ala", "feather", "dress", "cape", "coat", "jacket", "tail", "leg", "shoe", "boot", "weapon", "wpn", "sticker"]) and mesh.name.lower() not in mat.name.lower():
                                name_base = f"{mesh.name}_{mat.name}"
                            else:
                                name_base = mat.name
                        else:
                            name_base = mesh.name

                        new_mat.name = f"ZZZ {name_base}"
                        new_mat.use_fake_user = True
                        slot.material = new_mat

            # Fallback for any meshes with empty material slots
            for mesh in meshes:
                m_lower = mesh.name.lower()
                is_face_mesh = any(k in m_lower for k in ["face", "eyebrow", "brow", "eye"])
                fallback_template = face_template if is_face_mesh else shader_template
                for slot in mesh.material_slots:
                    if not slot.material and fallback_template:
                        new_mat = fallback_template.copy()
                        new_mat.name = f"ZZZ {mesh.name}"
                        new_mat.use_fake_user = True
                        slot.material = new_mat

            self.blender_operator.report({'INFO'}, "Replaced default materials with Kythera's ZZZ Shader materials...")


def find_nte_texture_for_material(mat_name, tex_type, image_files):
    name_lower = mat_name.lower()

    def matches_type(f):
        flow = f.lower()
        if tex_type == 'd':
            return any(k in flow for k in ['_d.', '_d_', '_d1', '_d2', '_diff', '_color', '_base', '_albedo'])
        elif tex_type == 'n':
            return any(k in flow for k in ['_n.', '_n_', '_n1', '_n2', '_norm', '_normal'])
        elif tex_type == 'm':
            return any(k in flow for k in ['_m.', '_m_', '_m1', '_m2', '_mask', '_lightmap'])
        elif tex_type == 'id':
            return any(k in flow for k in ['_id.', '_id_', '_id1', '_id2', '_idmap'])
        elif tex_type == 'r':
            return any(k in flow for k in ['_r.', '_r_', '_r1', '_r2', '_rim'])
        return True

    is_eye_mat = any(k in name_lower for k in ['eye', '目', 'iris', 'pupil', 'eyelash', 'eyebrow', '眉毛', '睫毛'])

    def is_eye_texture(f):
        flow = f.lower()
        return any(k in flow for k in ['eye', 'eyes', 'bantou', '目', '睫毛', '眉毛', 'eyelash', 'eyebrow'])

    if 'hair' in name_lower or 'pelo' in name_lower or '发' in name_lower:
        hair_num = None
        for p in re.split(r'[-_.\s]+', name_lower):
            if p.isdigit():
                hair_num = p
                break
        if not hair_num and ('02' in name_lower or '2' in name_lower or '后发' in name_lower):
            hair_num = '02'
        elif not hair_num:
            hair_num = '01'

        padded_num = hair_num.zfill(2)
        candidates = [f for f in image_files if 'hair' in f.lower() and matches_type(f) and (f'_{padded_num}_' in f.lower() or f'_{padded_num}.' in f.lower() or f'_{int(padded_num)}_' in f.lower() or f'_{int(padded_num)}.' in f.lower() or padded_num in f.lower())]
        if not candidates:
            candidates = [f for f in image_files if 'hair' in f.lower() and matches_type(f)]
        if candidates:
            return candidates[0]

    if 'face' in name_lower or 'cara' in name_lower or '面' in name_lower or 'head' in name_lower:
        candidates = [f for f in image_files if 'face' in f.lower() and matches_type(f)]
        specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent'])]
        if specific_candidates:
            return specific_candidates[0]
        if candidates:
            return candidates[0]

    if any(k in name_lower for k in ['gaoguang', 'hi', 'high', 'bantou']):
        candidates = [f for f in image_files if 'face' in f.lower() and matches_type(f)]
        specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
        if specific_candidates:
            return specific_candidates[0]
        if candidates:
            return candidates[0]

    if is_eye_mat:
        candidates = [f for f in image_files if ('eyes' in f.lower() or 'eye_' in f.lower() or 'eye.' in f.lower() or 'eye' in f.lower()) and matches_type(f)]
        specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['touming', 'common', 'default', 'dummy', 'transparent'])]
        if specific_candidates:
            return specific_candidates[0]
        if not candidates:
            candidates = [f for f in image_files if 'eye' in f.lower()]
            specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['touming', 'common', 'default', 'dummy', 'transparent'])]
            if specific_candidates:
                return specific_candidates[0]
        if candidates:
            return candidates[0]

    material_noise_tokens = {'player', 'oneiroi', 'oneir', 'mint', 'skin', 'lod0', 'skeleton', 'nte', 'shader', 'mi', 'mat', 'chastener'}

    clean_mat = name_lower.split('.')[0] if '.' in name_lower and name_lower.split('.')[-1].isdigit() else name_lower
    raw_tokens = [p for p in re.split(r'[-_.\s]+', clean_mat) if p]
    tokens = [p for p in raw_tokens if p not in material_noise_tokens]

    def score_file(f):
        if not matches_type(f) or (not is_eye_mat and is_eye_texture(f)):
            return -1000
        
        f_lower = f.lower()
        f_clean = f_lower.rsplit('.', 1)[0]
        f_tokens = set(re.split(r'[-_.\s]+', f_clean))

        score = 0
        for t in tokens:
            if t.isdigit():
                t_num = str(int(t))
                t_pad = t.zfill(2)
                if t in f_tokens or t_num in f_tokens or t_pad in f_tokens or f'_{t}_' in f_lower or f'_{t_pad}_' in f_lower or f'_{t_num}_' in f_lower or f'_{t_pad}.' in f_lower or f'_{t}.' in f_lower:
                    score += 50
                elif any(f'_{num.zfill(2)}_' in f_lower or f'_{int(num)}_' in f_lower for num in ['01', '02', '03', '04', '05', '1', '2', '3', '4', '5'] if int(num) != int(t)):
                    score -= 30
            else:
                if len(t) >= 2:
                    if t in f_tokens:
                        score += 20
                    elif t in f_lower:
                        score += 10

        return score

    best_file = None
    best_score = 0
    for f in image_files:
        sc = score_file(f)
        if sc > best_score:
            best_score = sc
            best_file = f

    if best_file and best_score > 0:
        return best_file

    if any(k in name_lower for k in ['down', '02', '_2', 'bottom', 'skirt', 'leg']):
        candidates = [f for f in image_files if ('_02_' in f.lower() or '_2_' in f.lower() or 'down' in f.lower() or 'body2' in f.lower() or 'cloth' in f.lower() or 'clothing' in f.lower() or '衣服' in f.lower()) and matches_type(f)]
        if not candidates:
            candidates = [f for f in image_files if '_02_' in f.lower() or '_2_' in f.lower()]
        if candidates:
            return candidates[0]

    if any(k in name_lower for k in ['up', '01', '_1', 'top', 'upper', 'body', 'skin', 'chastener_1']):
        candidates = [f for f in image_files if ('_01_' in f.lower() or '_1_' in f.lower() or 'up' in f.lower() or 'cloth' in f.lower() or 'clothing' in f.lower() or '衣服' in f.lower()) and matches_type(f)]
        if not candidates:
            candidates = [f for f in image_files if '_01_' in f.lower() or '_1_' in f.lower()]
        if candidates:
            return candidates[0]

    candidates = [f for f in image_files if matches_type(f) and (is_eye_mat or not is_eye_texture(f))]
    return candidates[0] if candidates else (image_files[0] if image_files else None)


def find_nte_body_texture_by_material_name(mat_name_lower, type_keys, image_files):
    material_noise_tokens = {'player', 'oneiroi', 'oneir', 'mint', 'skin', 'lod0', 'skeleton', 'nte', 'shader', 'mi', 'mat', 'chastener'}

    clean_mat = mat_name_lower.split('.')[0] if '.' in mat_name_lower and mat_name_lower.split('.')[-1].isdigit() else mat_name_lower
    raw_tokens = [p for p in re.split(r'[-_.\s]+', clean_mat) if p]
    tokens = [p for p in raw_tokens if p not in material_noise_tokens]
    if not tokens:
        return None

    def score_file(f):
        f_lower = f.lower()
        if not any(tk in f_lower for tk in type_keys):
            return -1000
        if any(k in f.lower() for k in ['hair', 'face', 'eye', 'eyes', 'bantou', 'gaoguang', '睫毛', '眉毛']):
            return -1000

        f_clean = f_lower.rsplit('.', 1)[0]
        f_tokens = set(re.split(r'[-_.\s]+', f_clean))

        score = 0
        for t in tokens:
            if t.isdigit():
                t_num = str(int(t))
                t_pad = t.zfill(2)
                if t in f_tokens or t_num in f_tokens or t_pad in f_tokens or f'_{t}_' in f_lower or f'_{t_pad}_' in f_lower or f'_{t_num}_' in f_lower or f'_{t_pad}.' in f_lower or f'_{t}.' in f_lower:
                    score += 50
                elif any(f'_{num.zfill(2)}_' in f_lower or f'_{int(num)}_' in f_lower for num in ['01', '02', '03', '04', '05', '1', '2', '3', '4', '5'] if int(num) != int(t)):
                    score -= 30
            else:
                if len(t) >= 2:
                    if t in f_tokens:
                        score += 20
                    elif t in f_lower:
                        score += 10

        return score

    best_file = None
    best_score = 0
    for f in image_files:
        sc = score_file(f)
        if sc > best_score:
            best_score = sc
            best_file = f

    return best_file if best_score > 0 else None


def ensure_hair_white_texture(folder=None, image_files=None):
    if not folder and not image_files:
        return

    if not image_files and folder and os.path.isdir(folder):
        image_files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp'))]

    white_file = None
    if image_files:
        white_file = next((f for f in image_files if 'linear_white' in f.lower() or 't_linear_white' in f.lower()), None) \
            or next((f for f in image_files if 'srgb_white' in f.lower() or 't_srgb_white' in f.lower()), None) \
            or next((f for f in image_files if 'white' in f.lower() and f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp'))), None)

    if not white_file or not folder:
        return

    img_path = os.path.join(folder, white_file)
    if not os.path.isfile(img_path):
        return

    img = bpy.data.images.load(img_path, check_existing=True)

    # 1. Process all node groups matching 异环-头发
    for ng in bpy.data.node_groups:
        ng_name_low = ng.name.lower()
        if '异环-头发' in ng.name or 'hair' in ng_name_low or '前发' in ng.name or '后发' in ng.name:
            for node in ng.nodes:
                if node.type == 'TEX_IMAGE':
                    is_vector_input_connected = any(
                        link.from_node.type == 'COMBINE_XYZ' or 'Combine' in getattr(link.from_node, 'name', '') 
                        for link in ng.links if link.to_node == node and getattr(link.to_socket, 'name', '') == 'Vector'
                    )
                    is_white_node = node.image is None or any(wk in (node.image.name.lower() if node.image else '') for wk in ['white', 'linear', 'srgb', 'anisotropic'])
                    is_not_main_diff_mask = not (node.image and any(k in node.image.name.lower() for k in ['_d.', '_d_', '_diff', '_m.', '_m_', '_mask']))

                    if is_vector_input_connected or is_white_node or is_not_main_diff_mask:
                        node.image = img

    # 2. Process all hair materials in bpy.data.materials
    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        mat_name_low = mat.name.lower()
        if any(k in mat_name_low for k in ['hair', 'pelo', '前发', '后发', 'toufa']):
            for node in mat.node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree:
                    sub_tree = node.node_tree
                    if '异环-头发' in sub_tree.name or 'hair' in sub_tree.name.lower() or '前发' in sub_tree.name or '后发' in sub_tree.name:
                        for sub_node in sub_tree.nodes:
                            if sub_node.type == 'TEX_IMAGE':
                                is_vector_input_connected = any(
                                    link.from_node.type == 'COMBINE_XYZ' or 'Combine' in getattr(link.from_node, 'name', '') 
                                    for link in sub_tree.links if link.to_node == sub_node and getattr(link.to_socket, 'name', '') == 'Vector'
                                )
                                is_white_node = sub_node.image is None or any(wk in (sub_node.image.name.lower() if sub_node.image else '') for wk in ['white', 'linear', 'srgb', 'anisotropic'])
                                is_not_main_diff_mask = not (sub_node.image and any(k in sub_node.image.name.lower() for k in ['_d.', '_d_', '_diff', '_m.', '_m_', '_mask']))

                                if is_vector_input_connected or is_white_node or is_not_main_diff_mask:
                                    sub_node.image = img


def replace_template_image_node(tex_node, image_files, folder, slot_mat_name="", json_database=None):
    if not tex_node.image:
        is_inside_hair = any(k in slot_mat_name.lower() for k in ['异环-头发', 'hair', '前发', '后发', 'toufa'])
        is_combine_xyz = any(
            link.from_node.type == 'COMBINE_XYZ' or 'Combine' in getattr(link.from_node, 'name', '')
            for link in getattr(getattr(tex_node, 'id_data', None), 'links', [])
            if link.to_node == tex_node and getattr(link.to_socket, 'name', '') == 'Vector'
        )
        if is_inside_hair or is_combine_xyz:
            white_file = next((f for f in image_files if 'linear_white' in f.lower() or 't_linear_white' in f.lower()), None) \
                or next((f for f in image_files if 'srgb_white' in f.lower() or 't_srgb_white' in f.lower()), None) \
                or next((f for f in image_files if 'white' in f.lower() and f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp'))), None)
            if white_file and folder:
                img_path = os.path.join(folder, white_file)
                if os.path.isfile(img_path):
                    img = bpy.data.images.load(img_path, check_existing=True)
                    tex_node.image = img
        return

    old_img_name = tex_node.image.name.lower()
    mat_name_lower = slot_mat_name.lower()
    replacement_file = None

    # Material 'gaoguang' always gets face_d texture assigned
    if 'gaoguang' in mat_name_lower:
        candidates = [f for f in image_files if 'face' in f.lower() and any(dk in f.lower() for dk in ['_d.', '_d_', '_diff', 'face_d', 'd_01', 'd_02'])]
        specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
        face_d_file = specific_candidates[0] if specific_candidates else (candidates[0] if candidates else None)
        if not face_d_file:
            candidates = [f for f in image_files if 'face' in f.lower()]
            specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
            face_d_file = specific_candidates[0] if specific_candidates else (candidates[0] if candidates else None)
        if face_d_file and folder:
            img_path = os.path.join(folder, face_d_file)
            if os.path.isfile(img_path):
                img = bpy.data.images.load(img_path, check_existing=True)
                try:
                    img.alpha_mode = 'CHANNEL_PACKED'
                except Exception:
                    pass
                tex_node.image = img
                return

    # 1. First priority: Check exact JSON texture mapping for this material
    if json_database:
        from setup_wizard.utils.nte_json_parser import get_nte_material_data
        mat_info = get_nte_material_data(slot_mat_name, json_database)
        if mat_info:
            textures = mat_info.get("textures", {})
            handled_slot = False

            if any(dk in old_img_name for dk in ['_d.', '_d_', '_diff', 'd_0', 'd_1', 'd_2', 'mint_01_d', 'mint_02_d', 'hair_01_d', 'hair_02_d', 'hair_d']) or 'diffuse' in old_img_name or 'basecolor' in old_img_name or '基础色' in old_img_name:
                handled_slot = True
                replacement_file = textures.get("diffuse")

            elif any(mk in old_img_name for mk in ['_m.', '_m_', '_mask', 'm_0', 'm_1', 'm_2', 'mint_01_m', 'mint_02_m', 'hair_01_m', 'hair_02_m', 'hair_m']) or 'lightmap' in old_img_name or 'mask' in old_img_name:
                handled_slot = True
                replacement_file = textures.get("lightmap")

            elif any(nk in old_img_name for nk in ['_n.', '_n_', '_norm', 'n_0', 'n_1', 'n_2', 'mint_01_n', 'mint_02_n', 'defaultnormal']) or 'normal' in old_img_name:
                handled_slot = True
                replacement_file = textures.get("normal")

            elif any(ik in old_img_name for ik in ['_id.', '_id_', 'id_0', 'id_1', 'id_2', 'mint_01_id', 'mint_02_id']) or 'id' in old_img_name:
                handled_slot = True
                replacement_file = textures.get("id")

            elif any(rk in old_img_name for rk in ['_r.', '_r_', 'face_r', 'blush', 'facelightmask', 'facemask']):
                handled_slot = True
                replacement_file = textures.get("face_mask")

            elif any(rk in old_img_name for rk in ['ramp', 'night_dusk', 'curve', 'rampaltas', 'rampatlas']):
                handled_slot = True
                replacement_file = textures.get("ramp") or (json_database.get("ramp_atlas_file") if json_database else None)

            elif any(ek in old_img_name for ek in ['emissive', 'noise']):
                handled_slot = True
                replacement_file = textures.get("emissive")

            elif any(wk in old_img_name for wk in ['white', 'linear_white', 'srgb_white', 'anisotropic', 't_srgb_white', 't_linear_white']):
                handled_slot = True
                replacement_file = textures.get("anisotropic")
                if not replacement_file and image_files:
                    replacement_file = next((f for f in image_files if 'linear_white' in f.lower() or 't_linear_white' in f.lower()), None) \
                        or next((f for f in image_files if 'srgb_white' in f.lower() or 't_srgb_white' in f.lower()), None) \
                        or next((f for f in image_files if 'white' in f.lower() and f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp'))), None)

            if handled_slot:
                if replacement_file:
                    img_path = os.path.join(folder, replacement_file)
                    if os.path.isfile(img_path):
                        img = bpy.data.images.load(img_path, check_existing=True)
                        try:
                            img.alpha_mode = 'CHANNEL_PACKED'
                        except Exception:
                            pass
                        tex_node.image = img
                        return
                else:
                    # JSON explicitly does NOT have this texture (e.g. No ID mask on Nitsa 03) -> clear template texture
                    tex_node.image = None
                    return

    hair_sub_idx = '01'
    if any(k in mat_name_lower for k in ['hair_2', 'hair_02', 'hair2', '后发', 'back']):
        hair_sub_idx = '02'
    elif any(k in mat_name_lower for k in ['hair_3', 'hair_03', 'hair3']):
        hair_sub_idx = '03'
    elif '02' in old_img_name or '2' in old_img_name:
        hair_sub_idx = '02'

    if any(fk in mat_name_lower for fk in ['面部因子', 'face factor', 'face_factor']):
        is_r_node = any(rk in old_img_name for rk in ['_r.', '_r_', 'r_1', 'r_2', 'face_r', 'ramp', 'blush'])
        is_m_node = any(mk in old_img_name for mk in ['_m.', '_m_', 'm_1', 'm_2', 'face_m', '_mask'])

        if not is_r_node and not is_m_node:
            if getattr(tex_node, 'location', None) and tex_node.location.y < -50:
                is_r_node = True
            else:
                is_m_node = True

        if is_r_node and not is_m_node:
            candidates = [f for f in image_files if 'face' in f.lower() and any(rk in f.lower() for rk in ['_r.', '_r_', '_r1', '_r_1', '_ramp', 'face_r', 'blush'])]
            specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
            if specific_candidates:
                replacement_file = specific_candidates[0]
            elif candidates:
                replacement_file = candidates[0]
        else:
            candidates = [f for f in image_files if 'face' in f.lower() and ('_m' in f.lower() or 'm_' in f.lower() or '_mask' in f.lower() or 'm.' in f.lower())]
            specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
            if specific_candidates:
                replacement_file = specific_candidates[0]
            elif candidates:
                replacement_file = candidates[0]

    elif any(k in old_img_name for k in ['ramp', 'night_dusk']):
        clean_old_base = old_img_name.split('.')[0].replace('.001', '').replace('.002', '').strip()
        exact_match = next((f for f in image_files if clean_old_base in f.lower() or f.lower().split('.')[0] == clean_old_base), None)
        if exact_match:
            replacement_file = exact_match
        else:
            ramp_candidates = [f for f in image_files if 't_srgb' in f.lower() or 'srgb' in f.lower() or 'ramp' in f.lower()]
            if ramp_candidates:
                replacement_file = ramp_candidates[0]

    elif any(k in old_img_name for k in ['white', 'linear_white', 'srgb_white', 'anisotropic', 't_srgb_white', 't_linear_white']):
        white_candidate = next((f for f in image_files if 'linear_white' in f.lower() or 't_linear_white' in f.lower()), None) \
            or next((f for f in image_files if 'srgb_white' in f.lower() or 't_srgb_white' in f.lower()), None) \
            or next((f for f in image_files if 'white' in f.lower() and f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp'))), None)
        if white_candidate:
            replacement_file = white_candidate

    elif any(k in old_img_name for k in ['matcap', 'silk']):
        clean_old_base = old_img_name.split('.')[0].replace('.001', '').replace('.002', '').strip()
        exact_match = next((f for f in image_files if clean_old_base in f.lower() or f.lower().split('.')[0] == clean_old_base), None)
        if exact_match:
            replacement_file = exact_match
        else:
            matcap_candidates = [f for f in image_files if 'matcap' in f.lower() or 'silk' in f.lower()]
            if matcap_candidates:
                replacement_file = matcap_candidates[0]

    elif 'hair' in old_img_name and any(dk in old_img_name for dk in ['_d.', '_d_', '_d1', '_d2', '_diff', 'd_0', 'd_1', 'd_2']):
        candidates = [f for f in image_files if 'hair' in f.lower() and ('_d' in f.lower() or 'd_' in f.lower()) and hair_sub_idx in f.lower()]
        if not candidates:
            candidates = [f for f in image_files if 'hair' in f.lower() and ('_d' in f.lower() or 'd_' in f.lower())]
        if candidates:
            replacement_file = candidates[0]

    elif 'hair' in old_img_name and any(mk in old_img_name for mk in ['_m.', '_m_', '_m1', '_m2', '_mask', 'm_0', 'm_1', 'm_2']):
        candidates = [f for f in image_files if 'hair' in f.lower() and ('_m' in f.lower() or 'm_' in f.lower()) and hair_sub_idx in f.lower()]
        if not candidates:
            candidates = [f for f in image_files if 'hair' in f.lower() and ('_m' in f.lower() or 'm_' in f.lower())]
        if candidates:
            replacement_file = candidates[0]

    elif 'hair' in old_img_name and any(nk in old_img_name for nk in ['_n.', '_n_', '_n1', '_n2', '_norm', 'n_0', 'n_1', 'n_2']):
        candidates = [f for f in image_files if 'hair' in f.lower() and ('_n' in f.lower() or 'n_' in f.lower()) and hair_sub_idx in f.lower()]
        if not candidates:
            candidates = [f for f in image_files if 'hair' in f.lower() and ('_n' in f.lower() or 'n_' in f.lower())]
        if candidates:
            replacement_file = candidates[0]

    elif 'face' in old_img_name and any(rk in old_img_name for rk in ['_r.', '_r_', '_r1', '_r_1', '_ramp', 'face_r', 'blush']):
        candidates = [f for f in image_files if 'face' in f.lower() and ('_r' in f.lower() or 'r_' in f.lower() or 'ramp' in f.lower())]
        specific_candidates = [f for f in candidates if 'common' not in f.lower()]
        if specific_candidates:
            replacement_file = specific_candidates[0]
        elif candidates:
            replacement_file = candidates[0]

    elif 'face' in old_img_name and any(mk in old_img_name for mk in ['_m.', '_m_', '_mask']):
        candidates = [f for f in image_files if 'face' in f.lower() and ('_m' in f.lower() or 'm_' in f.lower())]
        specific_candidates = [f for f in candidates if 'common' not in f.lower()]
        if specific_candidates:
            replacement_file = specific_candidates[0]
        elif candidates:
            replacement_file = candidates[0]

    elif 'face' in old_img_name and any(dk in old_img_name for dk in ['_d.', '_d_', '_d1', '_diff', 'd_0']):
        candidates = [f for f in image_files if 'face' in f.lower() and ('_d' in f.lower() or 'd_' in f.lower() or 'd1' in f.lower())]
        specific_candidates = [f for f in candidates if 'common' not in f.lower()]
        if specific_candidates:
            replacement_file = specific_candidates[0]
        elif candidates:
            replacement_file = candidates[0]

    elif any(gk in mat_name_lower for gk in ['gaoguang', '目hi']):
        candidates = [f for f in image_files if 'face' in f.lower() and any(dk in f.lower() for dk in ['_d.', '_d_', '_d1', '_diff', 'd_0'])]
        specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
        if specific_candidates:
            replacement_file = specific_candidates[0]
        elif candidates:
            replacement_file = candidates[0]
        else:
            candidates = [f for f in image_files if 'face' in f.lower()]
            specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
            if specific_candidates:
                replacement_file = specific_candidates[0]
            elif candidates:
                replacement_file = candidates[0]


    elif ('eyes' in old_img_name or 'eye' in old_img_name or 'eye' in mat_name_lower) and not any(ek in mat_name_lower for ek in ['eyelash', 'eyebrow', 'shadow', 'white', '二重', '眉', '睫', 'gaoguang', 'bantou', '目hi']):
        candidates = [
            f for f in image_files
            if ('eyes' in f.lower() or 'eye' in f.lower())
            and not any(bg in f.lower() for bg in ['bantou', 'gaoguang', 'eyelash', 'eyebrow', 'shadow', 'white'])
            and any(dk in f.lower() for dk in ['_d.', '_d_', '_d1', '_diff', 'd_0'])
        ]
        specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['touming', 'common', 'default', 'dummy', 'transparent'])]
        if specific_candidates:
            replacement_file = specific_candidates[0]
        elif candidates:
            replacement_file = candidates[0]
        if not replacement_file:
            candidates = [
                f for f in image_files
                if ('eyes' in f.lower() or 'eye' in f.lower())
                and not any(bg in f.lower() for bg in ['bantou', 'gaoguang', 'eyelash', 'eyebrow'])
            ]
            specific_candidates = [f for f in candidates if not any(k in f.lower() for k in ['touming', 'common', 'default', 'dummy', 'transparent'])]
            if specific_candidates:
                replacement_file = specific_candidates[0]
            elif candidates:
                replacement_file = candidates[0]



    elif ('mint_01_d' in old_img_name or 'mint_02_d' in old_img_name or any(dk in old_img_name for dk in ['_d.', '_d_', '_d1', '_diff'])) and 'hair' not in old_img_name and 'face' not in old_img_name:
        name_match = find_nte_body_texture_by_material_name(mat_name_lower, ['_d.', '_d_', '_d1', '_diff', 'd_0', 'd_1', 'd_2'], image_files)
        if name_match:
            replacement_file = name_match
        else:
            body_sub_idx = '01'
            if any(k in mat_name_lower for k in ['_2', '_02', 'chastener_2', 'down', 'bottom', 'leg', 'skirt', 'body_2', 'body2']):
                body_sub_idx = '02'
            candidates = [
                f for f in image_files
                if (f'_{body_sub_idx}_' in f.lower() or f'_{int(body_sub_idx)}_' in f.lower() or (body_sub_idx == '02' and 'down' in f.lower()) or (body_sub_idx == '01' and 'up' in f.lower()) or 'cloth' in f.lower() or 'clothing' in f.lower() or '衣服' in f.lower())
                and any(dk in f.lower() for dk in ['_d.', '_d_', '_d1', '_diff', 'd_0', 'd_1', 'd_2'])
                and 'hair' not in f.lower() and 'face' not in f.lower()
            ]
            if not candidates:
                candidates = [
                    f for f in image_files
                    if any(dk in f.lower() for dk in ['_d.', '_d_', '_d1', '_diff'])
                    and 'hair' not in f.lower() and 'face' not in f.lower()
                    and not any(k in f.lower() for k in ['eye', 'eyes', 'bantou', '目', '睫毛', '眉毛', 'eyelash', 'eyebrow'])
                ]
            if candidates:
                replacement_file = candidates[0]

    elif ('mint_01_m' in old_img_name or 'mint_02_m' in old_img_name or any(mk in old_img_name for mk in ['_m.', '_m_', '_mask'])) and 'hair' not in old_img_name and 'face' not in old_img_name:
        name_match = find_nte_body_texture_by_material_name(mat_name_lower, ['_m.', '_m_', '_mask'], image_files)
        if name_match:
            replacement_file = name_match
        else:
            body_sub_idx = '01'
            if any(k in mat_name_lower for k in ['_2', '_02', 'chastener_2', 'down', 'bottom', 'leg', 'skirt', 'body_2', 'body2']):
                body_sub_idx = '02'
            candidates = [
                f for f in image_files
                if (f'_{body_sub_idx}_' in f.lower() or f'_{int(body_sub_idx)}_' in f.lower() or (body_sub_idx == '02' and 'down' in f.lower()) or (body_sub_idx == '01' and 'up' in f.lower()) or 'cloth' in f.lower() or 'clothing' in f.lower() or '衣服' in f.lower())
                and any(mk in f.lower() for mk in ['_m.', '_m_', '_mask'])
                and 'hair' not in f.lower() and 'face' not in f.lower()
                and not any(k in f.lower() for k in ['eye', 'eyes', 'bantou', '目', '睫毛', '眉毛', 'eyelash', 'eyebrow'])
            ]
            if candidates:
                replacement_file = candidates[0]

    elif ('mint_01_n' in old_img_name or 'mint_02_n' in old_img_name or any(nk in old_img_name for nk in ['_n.', '_n_', '_norm'])) and 'hair' not in old_img_name and 'face' not in old_img_name:
        name_match = find_nte_body_texture_by_material_name(mat_name_lower, ['_n.', '_n_', '_norm'], image_files)
        if name_match:
            replacement_file = name_match
        else:
            body_sub_idx = '01'
            if any(k in mat_name_lower for k in ['_2', '_02', 'chastener_2', 'down', 'bottom', 'leg', 'skirt', 'body_2', 'body2']):
                body_sub_idx = '02'
            candidates = [
                f for f in image_files
                if (f'_{body_sub_idx}_' in f.lower() or f'_{int(body_sub_idx)}_' in f.lower() or (body_sub_idx == '02' and 'down' in f.lower()) or (body_sub_idx == '01' and 'up' in f.lower()) or 'cloth' in f.lower() or 'clothing' in f.lower() or '衣服' in f.lower())
                and any(nk in f.lower() for nk in ['_n.', '_n_', '_norm'])
                and 'hair' not in f.lower() and 'face' not in f.lower()
                and not any(k in f.lower() for k in ['eye', 'eyes', 'bantou', '目', '睫毛', '眉毛', 'eyelash', 'eyebrow'])
            ]
            if candidates:
                replacement_file = candidates[0]

    elif ('mint_01_id' in old_img_name or 'mint_02_id' in old_img_name or any(ik in old_img_name for ik in ['_id.', '_id_'])) and 'hair' not in old_img_name and 'face' not in old_img_name:
        name_match = find_nte_body_texture_by_material_name(mat_name_lower, ['_id.', '_id_'], image_files)
        if name_match:
            replacement_file = name_match
        else:
            body_sub_idx = '01'
            if any(k in mat_name_lower for k in ['_2', '_02', 'chastener_2', 'down', 'bottom', 'leg', 'skirt', 'body_2', 'body2']):
                body_sub_idx = '02'
            candidates = [
                f for f in image_files
                if (f'_{body_sub_idx}_' in f.lower() or f'_{int(body_sub_idx)}_' in f.lower() or (body_sub_idx == '02' and 'down' in f.lower()) or (body_sub_idx == '01' and 'up' in f.lower()) or 'cloth' in f.lower() or 'clothing' in f.lower() or '衣服' in f.lower())
                and any(ik in f.lower() for ik in ['_id.', '_id_'])
                and 'hair' not in f.lower() and 'face' not in f.lower()
                and not any(k in f.lower() for k in ['eye', 'eyes', 'bantou', '目', '睫毛', '眉毛', 'eyelash', 'eyebrow'])
            ]
            if candidates:
                replacement_file = candidates[0]

    if replacement_file:
        img_path = os.path.join(folder, replacement_file)
        img = bpy.data.images.load(img_path, check_existing=True)
        try:
            img.alpha_mode = 'CHANNEL_PACKED'
        except Exception:
            pass
        tex_node.image = img


def process_node_tree(node_tree, image_files, folder, slot_mat_name="", visited=None, json_database=None):
    if visited is None:
        visited = set()
    if not node_tree or node_tree in visited:
        return
    visited.add(node_tree)

    for node in node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            replace_template_image_node(node, image_files, folder, slot_mat_name, json_database=json_database)
        elif node.type == 'GROUP' and node.node_tree:
            sub_mat_name = f"{slot_mat_name} / {node.node_tree.name}" if slot_mat_name else node.node_tree.name
            process_node_tree(node.node_tree, image_files, folder, sub_mat_name, visited, json_database=json_database)



def setup_common_face_material(mat, folder=None, image_files=None):
    if not mat:
        return
    mat.use_nodes = True
    nt = mat.node_tree
    if not nt:
        return
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (350, 0)

    mix_node = nodes.new('ShaderNodeMixShader')
    mix_node.location = (100, 50)

    trans_node = nodes.new('ShaderNodeBsdfTransparent')
    trans_node.location = (-120, 180)
    try:
        trans_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    except Exception:
        pass

    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.location = (-400, -50)

    img = None
    for im in bpy.data.images:
        if 'common_face' in im.name.lower():
            img = im
            break

    if not img and folder:
        cands = []
        if image_files:
            cands = [f for f in image_files if 'common_face' in f.lower()]
        elif os.path.isdir(folder):
            cands = [f for f in os.listdir(folder) if 'common_face' in f.lower() and f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp'))]
        if cands:
            diff_cands = [f for f in cands if '_d.' in f.lower() or '_d_' in f.lower() or 'face_d' in f.lower()]
            picked = diff_cands[0] if diff_cands else cands[0]
            try:
                img_path = os.path.join(folder, picked)
                img = bpy.data.images.load(img_path, check_existing=True)
            except Exception as ex:
                print(f"Notice: Loading common_face texture: {ex}")

    if img:
        tex_node.image = img

    links.new(tex_node.outputs['Alpha'], mix_node.inputs[0])
    links.new(trans_node.outputs['BSDF'], mix_node.inputs[1])
    links.new(tex_node.outputs['Color'], mix_node.inputs[2])
    links.new(mix_node.outputs['Shader'], out_node.inputs['Surface'])

    try:
        mat.blend_method = 'BLEND'
    except Exception:
        pass
    try:
        mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    try:
        mat.shadow_method = 'NONE'
    except Exception:
        pass
    try:
        mat.show_transparent_back = False
    except Exception:
        pass


class NevernessToEvernessDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context

    def replace_default_materials(self):
        cache_enabled = self.context.window_manager.cache_enabled
        folder = self.blender_operator.file_directory or get_cache(cache_enabled).get(CHARACTER_MODEL_FOLDER_FILE_PATH) or get_active_character_directory()
        image_files = []
        json_database = None

        if folder and os.path.isdir(folder):
            from setup_wizard.utils.nte_json_parser import load_nte_character_data, get_nte_material_data
            try:
                json_database = load_nte_character_data(folder)
                image_files = json_database.get("image_files_list", [])
            except Exception as ex:
                print(f"[NTE Replace Default Materials] Notice loading JSON database: {ex}")

            if not image_files:
                try:
                    for root, dirs, files in os.walk(folder):
                        for f in files:
                            if f.lower().endswith(('.png', '.tga', '.dds', '.jpg', '.jpeg', '.webp', '.hdr', '.png.001', '.tga.001', '.dds.001')):
                                image_files.append(f)
                except Exception:
                    image_files = []

        meshes = [mesh for mesh in bpy.context.scene.objects if mesh.type == 'MESH']

        template_names = [
            'YH-Main-UP', 'YH-Main-DOWN', '前发', '后发', '面', '肌', '目', '目Hi',
            '目影', '目白', '眉毛', '睫毛', '二重', '口', '齿舌', '表情', 'edge_clothes2', 'Dots Stroke'
        ]

        for mesh in meshes:
            if len(mesh.material_slots) == 0:
                new_mat = bpy.data.materials.new(name=mesh.name)
                mesh.data.materials.append(new_mat)

            for slot in mesh.material_slots:
                mat = slot.material
                if not mat:
                    continue

                matname = mat.name.lower()

                if "touming" in matname:
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    nodes.clear()
                    out_node = nodes.new('ShaderNodeOutputMaterial')
                    out_node.location = (300, 0)
                    trans_node = nodes.new('ShaderNodeBsdfTransparent')
                    trans_node.location = (0, 0)
                    links.new(trans_node.outputs['BSDF'], out_node.inputs['Surface'])
                    try:
                        mat.blend_method = 'BLEND'
                    except Exception:
                        pass
                    continue

                if any(k in matname for k in ["common_face", "common_face_mask", "face_mask", "facemask"]):
                    setup_common_face_material(mat, folder=folder, image_files=image_files)
                    continue

                if mat.name in template_names or mat.name == '材质球':
                    continue

                template_to_use = None
                is_skin = 0.0

                if any(k in matname for k in ["后发", "back_hair", "hair_2", "hair_02", "hair2", "hair_3", "hair_03", "hair3"]):
                    template_to_use = "后发"
                    is_skin = 1.0
                elif any(k in matname for k in ["前发", "hair", "pelo", "toufa"]):
                    template_to_use = "前发"
                    is_skin = 1.0
                elif any(k in matname for k in ["面", "face", "cara", "head", "mian", "facio", "kao"]):
                    template_to_use = "面"
                    is_skin = 1.0
                elif any(k in matname for k in ["肌", "skin", "piel", "body_skin"]):
                    template_to_use = "肌"
                    is_skin = 1.0
                elif any(k in matname for k in ["目hi", "eye_hi", "gaoguang"]):
                    template_to_use = "目Hi"
                elif any(k in matname for k in ["睫毛", "eyelash"]):
                    template_to_use = "睫毛"
                elif any(k in matname for k in ["眉毛", "eyebrow"]):
                    template_to_use = "眉毛"
                elif any(k in matname for k in ["目影", "eye_shadow", "bantou"]):
                    template_to_use = "目影"

                elif any(k in matname for k in ["目白", "eye_white"]):
                    template_to_use = "目白"
                elif any(k in matname for k in ["二重", "double_eyelid"]):
                    template_to_use = "二重"
                elif any(k in matname for k in ["目", "eye", "iris", "pupil"]):
                    template_to_use = "目"

                elif any(k in matname for k in ["口", "mouth"]):
                    template_to_use = "口"
                elif any(k in matname for k in ["齿舌", "teeth", "tongue"]):
                    template_to_use = "齿舌"
                elif any(k in matname for k in ["down", "bottom", "skirt", "leg", "02"]):
                    template_to_use = "YH-Main-DOWN"
                elif any(k in matname for k in ["edge"]):
                    template_to_use = "edge_clothes2"
                else:
                    template_to_use = "YH-Main-UP"

                template_mat = bpy.data.materials.get(template_to_use)
                if template_mat:
                    new_mat = template_mat.copy()
                    new_mat.name = slot.material.name
                    slot.material = new_mat
                    mat = new_mat

                if mat and mat.use_nodes and mat.node_tree:
                    nodes = mat.node_tree.nodes
                    for node in nodes:
                        if node.type == 'GROUP' and node.node_tree:
                            for inp in node.inputs:
                                if '是否为' in inp.name or '皮肤' in inp.name or inp.name == '是否为皮肤':
                                    inp.default_value = is_skin

                    if folder and image_files:
                        process_node_tree(mat.node_tree, image_files, folder, slot.material.name, json_database=json_database)

                    if json_database:
                        from setup_wizard.utils.nte_json_parser import get_nte_material_data
                        mat_info = get_nte_material_data(slot.material.name, json_database)
                        if mat_info:
                            scalars = mat_info.get("scalars", {})
                            for n in mat.node_tree.nodes:
                                if n.type == 'GROUP' and n.node_tree:
                                    for s_name, s_val in scalars.items():
                                        if s_name in n.inputs and isinstance(s_val, (int, float)):
                                            try:
                                                n.inputs[s_name].default_value = float(s_val)
                                            except Exception:
                                                pass

        if folder and image_files:
            for ng_name in ['异环-头发', '异环-身体', '异环-面部', 'Matcap采样']:
                ng = bpy.data.node_groups.get(ng_name)
                if ng:
                    process_node_tree(ng, image_files, folder, "NodeGroup_" + ng_name, json_database=json_database)

            ensure_hair_white_texture(folder, image_files)

            face_cands = [f for f in image_files if 'face' in f.lower() and any(dk in f.lower() for dk in ['_d.', '_d_', '_diff', 'face_d', 'd_01', 'd_02'])]
            face_spec = [f for f in face_cands if not any(k in f.lower() for k in ['common', 'touming', 'default', 'dummy', 'transparent', 'bantou'])]
            face_d_img_file = face_spec[0] if face_spec else (face_cands[0] if face_cands else None)
            if face_d_img_file:
                face_d_path = os.path.join(folder, face_d_img_file)
                if os.path.isfile(face_d_path):
                    face_d_img = bpy.data.images.load(face_d_path, check_existing=True)
                    for mat in bpy.data.materials:
                        if mat.use_nodes and mat.node_tree and 'gaoguang' in mat.name.lower():
                            for node in mat.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    node.image = face_d_img

        try:
            bpy.ops.neverness_to_everness.set_up_hair_specular()
        except Exception as ex:
            print(f"Notice: Handled setting up hair specular: {ex}")


        # Clean up any duplicate empties (.001, .002) safely without ReferenceError
        orig_head = bpy.data.objects.get('Head Origin')
        orig_light = bpy.data.objects.get('Light Direction')

        head_dupes = []
        light_dupes = []

        for obj in list(bpy.data.objects):
            try:
                name_low = obj.name.lower()
                has_suffix = '.00' in obj.name or '.01' in obj.name
                if has_suffix:
                    if any(k in name_low for k in ['head origin', 'head forward', 'head up']):
                        if orig_head and obj != orig_head:
                            head_dupes.append(obj)
                    elif any(k in name_low for k in ['light direction', 'sun']):
                        if orig_light and obj != orig_light:
                            light_dupes.append(obj)
            except Exception:
                pass

        for obj in head_dupes:
            try:
                if orig_head:
                    for other in list(bpy.data.objects):
                        try:
                            if getattr(other, 'parent', None) == obj:
                                other.parent = orig_head
                            for con in getattr(other, 'constraints', []):
                                if getattr(con, 'target', None) == obj:
                                    con.target = orig_head
                        except Exception:
                            pass
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

        for obj in light_dupes:
            try:
                if orig_light:
                    for other in list(bpy.data.objects):
                        try:
                            if getattr(other, 'parent', None) == obj:
                                other.parent = orig_light
                            for con in getattr(other, 'constraints', []):
                                if getattr(con, 'target', None) == obj:
                                    con.target = orig_light
                        except Exception:
                            pass
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

        def fix_nte_face_sdf_node():
            trees_to_check = set()
            for ng in list(bpy.data.node_groups):
                if ng and hasattr(ng, 'nodes'):
                    trees_to_check.add(ng)
            for mat in list(bpy.data.materials):
                if mat and mat.use_nodes and mat.node_tree:
                    trees_to_check.add(mat.node_tree)

            for tree in trees_to_check:
                ff_nodes = [
                    n for n in tree.nodes
                    if (n.type == 'GROUP' and n.node_tree and 'face factor' in n.node_tree.name.lower())
                    or '面部因子' in getattr(n, 'label', '')
                    or 'face factor' in n.name.lower()
                ]
                for ff in ff_nodes:
                    for link in list(tree.links):
                        if link.from_node == ff:
                            target_node = link.to_node
                            tree.links.remove(link)
                            if target_node.type in ['MIX', 'MIX_RGB']:
                                try:
                                    if 'Factor' in target_node.inputs:
                                        target_node.inputs['Factor'].default_value = 1.0
                                    elif 'Fac' in target_node.inputs:
                                        target_node.inputs['Fac'].default_value = 1.0
                                    else:
                                        target_node.inputs[0].default_value = 1.0
                                except Exception:
                                    pass

        try:
            fix_nte_face_sdf_node()
        except Exception as e_sdf:
            print(f"[NTE Face SDF Fix Notice] {e_sdf}")

        self.blender_operator.report({'INFO'}, 'Replaced default materials with NTE template materials from nteTodo.md...')
        NextStepInvoker().invoke(
            self.blender_operator.next_step_idx, 
            self.blender_operator.invoker_type, 
            high_level_step_name=self.blender_operator.high_level_step_name,
            game_type=self.blender_operator.game_type,
        )


def _is_hair_slot(name_lower):
    return 'hair' in name_lower or '头' in name_lower or 'pelo' in name_lower


def _is_face_slot(name_lower):
    return any(k in name_lower for k in ('face', '面', 'cara', 'head', 'eye', 'eyebrow', 'brow', '眉'))


def _fuse_mesh_slots_to_first(obj):
    """Point every polygon to slot 0 and drop the remaining slots."""
    mesh = obj.data
    for p in mesh.polygons:
        if p.material_index >= 1:
            p.material_index = 0
    while len(mesh.materials) > 1:
        mesh.materials.pop(index=1)
    try:
        mesh.update()
    except Exception:
        pass


def clean_hair_mesh_slots():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.data and hasattr(obj.data, "polygons"):
            obj_name_lower = obj.name.lower()
            slot_names = [slot.material.name.lower() for slot in obj.material_slots if slot.material]
            is_hair_mesh = 'hair' in obj_name_lower or any(_is_hair_slot(s) for s in slot_names)
            # Only fuse meshes whose slots are ALL hair (e.g. Hair + Hair_T).
            # Mixed meshes (e.g. Body carrying Body/Weapon/Hair slots) are left untouched.
            if is_hair_mesh and len(obj.material_slots) >= 2 and slot_names and all(_is_hair_slot(s) for s in slot_names):
                _fuse_mesh_slots_to_first(obj)


def clean_face_mesh_slots():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.data and hasattr(obj.data, "polygons"):
            obj_name_lower = obj.name.lower()
            slot_names = [slot.material.name.lower() for slot in obj.material_slots if slot.material]
            is_face_mesh = 'face' in obj_name_lower or any(_is_face_slot(s) for s in slot_names)
            # Only fuse meshes whose slots are ALL face-related (Face/Eye/Eyebrow).
            # Mixed meshes are left untouched.
            if is_face_mesh and len(obj.material_slots) >= 2 and slot_names and all(_is_face_slot(s) for s in slot_names):
                _fuse_mesh_slots_to_first(obj)


class WutheringWavesDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    def __init__(self, blender_operator, context):
        self.blender_operator = blender_operator
        self.context = context

    def replace_default_materials(self):
        from setup_wizard.utils.wuwa_texture_utils import split_material_name, extract_character_name

        meshes = [obj for obj in self.context.scene.objects if obj.type == 'MESH']

        for mesh in meshes:
            if "_seethru" in mesh.name.lower():
                continue

            char_name = extract_character_name(mesh.name)

            for slot in mesh.material_slots:
                if not slot.material:
                    continue
                orig_mat_name = slot.material.name
                if orig_mat_name.startswith("WW - "):
                    continue

                base_part, version = split_material_name(orig_mat_name)
                if not base_part:
                    base_part = "Main"

                # Determine template in Gustling Waters
                template_name = "WW - Main"
                mat_low = orig_mat_name.lower()

                if "face" in mat_low or base_part.lower() == "face":
                    template_name = "WW - Face"
                    base_part = "Face"
                elif ("eye" in mat_low or base_part.lower() in ["eye", "eyes"]) and not any(k in mat_low for k in ["eyebrow", "eyelash"]):
                    template_name = "WW - Eye"
                    base_part = "Eye"
                elif "bang" in mat_low or base_part.lower() in ["bang", "bangs"]:
                    template_name = "WW - Bangs" if bpy.data.materials.get("WW - Bangs") else "WW - Hair"
                    base_part = "Bangs"
                elif "hair" in mat_low or base_part.lower() in ["hair", "toufa"]:
                    template_name = "WW - Hair"
                    base_part = "Hair"
                elif any(k in mat_low for k in ["star", "xingstar", "resonatorstar"]) or base_part.lower() == "resonatorstar":
                    template_name = "WW - ResonatorStar"
                    base_part = "ResonatorStar"
                elif bpy.data.materials.get(f"WW - {base_part}"):
                    template_name = f"WW - {base_part}"
                else:
                    template_name = "WW - Main"

                unique_mat_name = f"WW - {base_part}{version} {char_name}"
                target_mat = bpy.data.materials.get(unique_mat_name)
                if not target_mat:
                    tmpl = bpy.data.materials.get(template_name) or bpy.data.materials.get("WW - Main")
                    if tmpl:
                        target_mat = tmpl.copy()
                        target_mat.name = unique_mat_name
                        target_mat.use_fake_user = True
                        if target_mat.use_nodes and target_mat.node_tree:
                            for n in target_mat.node_tree.nodes:
                                if n.type == 'TEX_IMAGE':
                                    n.image = None
                    else:
                        target_mat = slot.material

                if target_mat:
                    target_mat["ww_original_name"] = orig_mat_name
                    target_mat["ww_base_part"] = base_part
                    slot.material = target_mat

                    # If material name or original name contains / ends with 'Alpha' or is Fur, unmute Alpha Transparency node
                    is_alpha = any(
                        k in orig_mat_name.lower() or k in base_part.lower() or k in target_mat.name.lower()
                        for k in ["alpha", "touming", "transparency", "fur", "flur"]
                    )
                    if is_alpha and target_mat.node_tree:
                        target_mat["ww_is_alpha_material"] = True
                        for n in target_mat.node_tree.nodes:
                            if (n.type == 'GROUP' and n.node_tree and "alpha transparency" in n.node_tree.name.lower()) or "alpha transparency" in n.name.lower():
                                n.mute = False
                        if hasattr(target_mat, "surface_render_method"):
                            try:
                                target_mat.surface_render_method = 'BLENDED'
                            except Exception:
                                pass
                        if hasattr(target_mat, "blend_method"):
                            try:
                                target_mat.blend_method = 'BLEND'
                            except Exception:
                                pass
                        if hasattr(target_mat, "shadow_method"):
                            try:
                                target_mat.shadow_method = 'HASHED'
                            except Exception:
                                pass

            # Darken Eye vertex colors if mesh has eye polygons
            self.darken_eye_colors(mesh)

        try:
            from setup_wizard.wuwa_operations import sync_wuwa_shader_properties
            sync_wuwa_shader_properties(self.context.scene)
        except Exception as e:
            print(f"[WUWA] Notice syncing shader properties: {e}")

        self.blender_operator.report({'INFO'}, 'Replaced default materials with Wuthering Waves (Gustling Waters) materials.')
        NextStepInvoker().invoke(
            self.blender_operator.next_step_idx, 
            self.blender_operator.invoker_type, 
            high_level_step_name=self.blender_operator.high_level_step_name,
            game_type=self.blender_operator.game_type,
        )

    def darken_eye_colors(self, mesh):
        if not mesh.data or not hasattr(mesh.data, "polygons"):
            return

        # Find eye material slots
        eye_slot_indices = set()
        for idx, slot in enumerate(mesh.material_slots):
            if slot.material and "eye" in slot.material.name.lower():
                eye_slot_indices.add(idx)

        if not eye_slot_indices:
            return

        color_layer = None
        if hasattr(mesh.data, "color_attributes") and mesh.data.color_attributes:
            color_layer = mesh.data.color_attributes.get("COL0") or mesh.data.color_attributes.active_color
        elif hasattr(mesh.data, "vertex_colors") and mesh.data.vertex_colors:
            color_layer = mesh.data.vertex_colors.get("COL0") or mesh.data.vertex_colors.active

        if color_layer:
            try:
                for poly in mesh.data.polygons:
                    if poly.material_index in eye_slot_indices:
                        for loop_idx in poly.loop_indices:
                            color_layer.data[loop_idx].color = (0.0, 0.0, 0.0, 1.0)
            except Exception as ex:
                print(f"Notice darkening eye vertex colors: {ex}")


def clean_mesh_slots():
    clean_hair_mesh_slots()
    clean_face_mesh_slots()


class ArknightsEndfieldDefaultMaterialReplacer(GameDefaultMaterialReplacer):
    def __init__(self, blender_operator: Operator, context: Context):
        self.blender_operator = blender_operator
        self.context = context

    def replace_default_materials(self):
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']

        # Cache standard template materials from AKE.blend
        mat_map = {
            'body': bpy.data.materials.get('body_01'),
            'cloth_01': bpy.data.materials.get('cloth_01'),
            'cloth_02': bpy.data.materials.get('cloth_02'),
            'cloth_03': bpy.data.materials.get('cloth_03'),
            'cloth_04': bpy.data.materials.get('cloth_04'),
            'face_01': bpy.data.materials.get('face_01'),
            'hair_01': bpy.data.materials.get('hair_01'),
            'hairshadow_01': bpy.data.materials.get('hairshadow_01'),
            'iris': bpy.data.materials.get('iris_01'),
            'eyebrow': bpy.data.materials.get('eyebrow_01'),
            'eyeshadow': bpy.data.materials.get('eyeshadow_01'),
            'head': bpy.data.materials.get('head'),
            'weapon': bpy.data.materials.get('weapon'),
            'wing': bpy.data.materials.get('wing'),
        }

        def get_template_for_slot(raw_slot_name, mesh_name):
            slot_low = raw_slot_name.lower()
            mesh_low = mesh_name.lower()
            
            # 1. First match slot name tokens
            if any(k in slot_low for k in ['iris', 'eye_01']):
                return mat_map['iris']
            elif any(k in slot_low for k in ['eyebrow', 'brow']):
                return mat_map['eyebrow']
            elif any(k in slot_low for k in ['eyeshadow', 'eyewhite', 'whiteshadow']):
                return mat_map['eyeshadow']
            elif 'hairshadow' in slot_low:
                return mat_map['hairshadow_01']
            elif 'hair' in slot_low:
                return mat_map['hair_01']
            elif 'face' in slot_low:
                return mat_map['face_01']
            elif 'body' in slot_low:
                return mat_map['body']
            elif 'cloth_01' in slot_low or 'cloth_05' in slot_low:
                return mat_map['cloth_01']
            elif 'cloth_02' in slot_low or 'cloth_06' in slot_low:
                return mat_map['cloth_02']
            elif 'cloth_03' in slot_low:
                return mat_map['cloth_03'] or mat_map['cloth_01']
            elif 'cloth_04' in slot_low:
                return mat_map['cloth_04'] or mat_map['cloth_02']
            elif 'cloth_07' in slot_low or 'cloth_08' in slot_low:
                return mat_map['cloth_01']
            elif 'vfx' in slot_low or 'toppotential' in slot_low:
                return bpy.data.materials.get('Arknights: Endfield_Alpha') or mat_map['cloth_01']
            elif 'cloth' in slot_low:
                return mat_map['cloth_01']
            elif any(k in slot_low for k in ['wpn', 'weapon']):
                return mat_map['weapon']
            elif 'wing' in slot_low:
                return mat_map['wing']
            elif 'head' in slot_low:
                return mat_map['head']

            # 2. Fallback to mesh name tokens
            if any(k in mesh_low for k in ['iris', 'eye_01']):
                return mat_map['iris']
            elif any(k in mesh_low for k in ['eyebrow', 'brow']):
                return mat_map['eyebrow']
            elif any(k in mesh_low for k in ['eyeshadow', 'eyewhite']):
                return mat_map['eyeshadow']
            elif 'hairshadow' in mesh_low:
                return mat_map['hairshadow_01']
            elif 'hair' in mesh_low:
                return mat_map['hair_01']
            elif 'face' in mesh_low:
                return mat_map['face_01']
            elif 'body' in mesh_low:
                return mat_map['body']
            elif 'cloth_01' in mesh_low or 'cloth_05' in mesh_low:
                return mat_map['cloth_01']
            elif 'cloth_02' in mesh_low or 'cloth_06' in mesh_low:
                return mat_map['cloth_02']
            elif 'cloth_03' in mesh_low:
                return mat_map['cloth_03'] or mat_map['cloth_01']
            elif 'cloth_04' in mesh_low:
                return mat_map['cloth_04'] or mat_map['cloth_02']
            elif any(k in mesh_low for k in ['cloth_07', 'cloth_08', 'vfxpart', 'toppotential']):
                return bpy.data.materials.get('Arknights: Endfield_Alpha') or mat_map['cloth_01']
            elif 'cloth' in mesh_low:
                return mat_map['cloth_01']

            return mat_map['cloth_01']

        cloned_mats = {}

        # 1. Assign AKE materials to all mesh slots
        for mesh in meshes:
            mesh_name = mesh.name.lower()
            for slot in mesh.material_slots:
                raw_mat = slot.material
                raw_name = raw_mat.name if raw_mat else slot.name
                clean_name = raw_name.replace('__raw_fbx_', '')

                if clean_name not in cloned_mats:
                    chosen_template = get_template_for_slot(clean_name, mesh.name)
                    if not chosen_template:
                        chosen_template = mat_map['cloth_01']

                    new_mat = chosen_template.copy()
                    new_mat.name = clean_name
                    new_mat.use_fake_user = True
                    cloned_mats[clean_name] = new_mat

                slot.material = cloned_mats[clean_name]

                # Transparency settings: body must strictly be DITHERED, eyeshadow must strictly be BLENDED
                if slot.material:
                    m = slot.material
                    m_low = m.name.lower()
                    if any(k in m_low or k in mesh_name for k in ['eyeshadow', 'eyewhite', 'whiteshadow', 'eye_shadow']):
                        if hasattr(m, "surface_render_method"):
                            try:
                                m.surface_render_method = 'BLENDED'
                            except Exception:
                                pass
                        if hasattr(m, "blend_method"):
                            try:
                                m.blend_method = 'BLEND'
                            except Exception:
                                pass
                        if hasattr(m, "use_backface_culling"):
                            m.use_backface_culling = False
                        if hasattr(m, "show_transparent_back"):
                            m.show_transparent_back = False
                    elif 'body' in m_low or 'body' in mesh_name:
                        if hasattr(m, "surface_render_method"):
                            try:
                                m.surface_render_method = 'DITHERED'
                            except Exception:
                                pass
                        if hasattr(m, "use_backface_culling"):
                            m.use_backface_culling = False
                    elif any(k in m.name.lower() or k in mesh_name for k in ['cloth_03', 'cloth_04', 'cloth_05', 'cloth_06', 'cloth_07', 'cloth_08', 'vfxpart']):
                        if hasattr(m, "surface_render_method"):
                            try:
                                m.surface_render_method = 'BLENDED'
                            except Exception:
                                pass
                        if hasattr(m, "blend_method"):
                            try:
                                m.blend_method = 'BLEND'
                            except Exception:
                                pass
                        if hasattr(m, "use_backface_culling"):
                            m.use_backface_culling = False
                        if hasattr(m, "show_transparent_back"):
                            m.show_transparent_back = False

        # 2. Geometry Node Modifiers: Light, Facemat, Head Controller, Face_ALPHA
        light_ng = bpy.data.node_groups.get('Light')
        facemat_ng = bpy.data.node_groups.get('Facemat')
        head_ctrl_ng = bpy.data.node_groups.get('Head Controller')
        face_alpha_ng = bpy.data.node_groups.get('Face_ALPHA')

        hc = bpy.data.objects.get('HC')
        hf = bpy.data.objects.get('HF')
        hr = bpy.data.objects.get('HR')

        face_mat = bpy.data.materials.get('face_01')
        iris_mat = bpy.data.materials.get('iris_01')
        brow_mat = bpy.data.materials.get('eyebrow_01')
        iris_alpha_mat = bpy.data.materials.get('iris_01_ALPHA')
        brow_alpha_mat = bpy.data.materials.get('eyebrow_01_ALPHA')

        def _set_mod_socket(target_mod, ident_or_name, val):
            if hasattr(target_mod, 'properties') and target_mod.properties and hasattr(target_mod.properties, 'inputs'):
                sock = getattr(target_mod.properties.inputs, ident_or_name, None)
                if not sock and target_mod.node_group and hasattr(target_mod.node_group, 'interface'):
                    for item in target_mod.node_group.interface.items_tree:
                        if getattr(item, 'item_type', '') == 'SOCKET' and item.name == ident_or_name:
                            sock = getattr(target_mod.properties.inputs, item.identifier, None)
                            break
                if sock and hasattr(sock, 'value'):
                    try:
                        sock.value = val
                        return True
                    except Exception:
                        pass
            try:
                target_mod[ident_or_name] = val
                return True
            except Exception:
                pass
            return False

        for mesh in meshes:
            mesh_name = mesh.name.lower()
            is_hair = 'hair_01' in mesh_name or ('hair' in mesh_name and 'shadow' not in mesh_name)
            is_face = 'face_01' in mesh_name or 'face' in mesh_name

            # Light modifier on non-hair meshes
            if light_ng and not is_hair:
                mod_light = mesh.modifiers.get('Light')
                if not mod_light:
                    mod_light = mesh.modifiers.new('Light', 'NODES')
                mod_light.node_group = light_ng
            elif is_hair:
                mod_light = mesh.modifiers.get('Light')
                if mod_light:
                    mesh.modifiers.remove(mod_light)

            # Face modifiers on face mesh
            if is_face:
                if facemat_ng:
                    mod_facemat = mesh.modifiers.get('Facemat')
                    if not mod_facemat:
                        mod_facemat = mesh.modifiers.new('Facemat', 'NODES')
                    mod_facemat.node_group = facemat_ng
                    if face_mat:
                        _set_mod_socket(mod_facemat, "Socket_2", face_mat)
                        _set_mod_socket(mod_facemat, "FaceMat", face_mat)

                if head_ctrl_ng:
                    mod_hc = mesh.modifiers.get('Head Controller')
                    if not mod_hc:
                        mod_hc = mesh.modifiers.new('Head Controller', 'NODES')
                    mod_hc.node_group = head_ctrl_ng
                    if hc:
                        _set_mod_socket(mod_hc, "Socket_0", hc)
                        _set_mod_socket(mod_hc, "HC", hc)
                    if hf:
                        _set_mod_socket(mod_hc, "Socket_2", hf)
                        _set_mod_socket(mod_hc, "HF", hf)
                    if hr:
                        _set_mod_socket(mod_hc, "Socket_3", hr)
                        _set_mod_socket(mod_hc, "HR", hr)

                if face_alpha_ng:
                    mod_fa = mesh.modifiers.get('Face_ALPHA')
                    if not mod_fa:
                        mod_fa = mesh.modifiers.new('Face_ALPHA', 'NODES')
                    mod_fa.node_group = face_alpha_ng
                    if iris_mat:
                        _set_mod_socket(mod_fa, "Socket_4", iris_mat)
                        _set_mod_socket(mod_fa, "irisMat", iris_mat)
                    if brow_mat:
                        _set_mod_socket(mod_fa, "Socket_5", brow_mat)
                        _set_mod_socket(mod_fa, "browMat", brow_mat)
                    if iris_alpha_mat:
                        _set_mod_socket(mod_fa, "Socket_6", iris_alpha_mat)
                        _set_mod_socket(mod_fa, "irisAlphaMat", iris_alpha_mat)
                    if brow_alpha_mat:
                        _set_mod_socket(mod_fa, "Socket_7", brow_alpha_mat)
                        _set_mod_socket(mod_fa, "browAlphaMat", brow_alpha_mat)

        self.blender_operator.report({'INFO'}, 'Replaced default materials with Arknights: Endfield materials and configured modifiers.')









