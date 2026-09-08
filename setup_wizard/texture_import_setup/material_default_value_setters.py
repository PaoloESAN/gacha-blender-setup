# Author: michael-gh1

import bpy

from abc import abstractmethod

from setup_wizard.domain.body_hair_ramp_switch_values import BodyHairRampSwitchValues
from setup_wizard.domain.shader_node_names import V2_GenshinShaderNodeNames, V3_GenshinShaderNodeNames, V4_PrimoToonShaderNodeNames
from setup_wizard.domain.shader_identifier_service import GenshinImpactShaders, ShaderIdentifierService, ShaderIdentifierServiceFactory
from setup_wizard.domain.shader_material_names import ShaderMaterialNames, V2_FestivityGenshinImpactMaterialNames, \
    V3_BonnyFestivityGenshinImpactMaterialNames, V4_PrimoToonGenshinImpactMaterialNames
from setup_wizard.domain.shader_node_names import ShaderNodeNames

from setup_wizard.domain.game_types import GameType
from setup_wizard.texture_import_setup.texture_node_names import V4_GenshinImpactTextureNodeNames


class MaterialDefaultValueSetterFactory:
    def create(game_type: GameType):
        shader_identifier_service: ShaderIdentifierService = ShaderIdentifierServiceFactory.create(game_type)

        if game_type == GameType.GENSHIN_IMPACT.name:
            shader = shader_identifier_service.identify_shader(bpy.data.materials, bpy.data.node_groups)
            if shader is GenshinImpactShaders.V1_GENSHIN_IMPACT_SHADER or shader is GenshinImpactShaders.V2_GENSHIN_IMPACT_SHADER:
                return GenshinImpactMaterialDefaultValueSetter(V2_FestivityGenshinImpactMaterialNames, V2_GenshinShaderNodeNames)
            elif shader is GenshinImpactShaders.V3_GENSHIN_IMPACT_SHADER:
                return GenshinImpactMaterialDefaultValueSetter(V3_BonnyFestivityGenshinImpactMaterialNames, V3_GenshinShaderNodeNames)
            else:
                return GenshinImpactMaterialDefaultValueSetter(V4_PrimoToonGenshinImpactMaterialNames, V4_PrimoToonShaderNodeNames)
        elif game_type == GameType.HONKAI_STAR_RAIL.name:
            return HonkaiStarRailMaterialDefaultValueSetter()
        elif game_type == GameType.PUNISHING_GRAY_RAVEN.name:
            return PunishingGrayRavenMaterialDefaultValueSetter()
        elif game_type == GameType.ZENLESS_ZONE_ZERO.name:
            return ZenlessZoneZeroMaterialDefaultValueSetter()
        elif game_type == GameType.NEVERNESS_TO_EVERNESS.name:
            return NevernessToEvernessMaterialDefaultValueSetter()
        elif game_type == GameType.WUTHERING_WAVES.name:
            return WutheringWavesMaterialDefaultValueSetter()
        elif game_type == GameType.ARKNIGHTS_ENDFIELD.name:
            return ArknightsEndfieldMaterialDefaultValueSetter()
        else:
            raise Exception(f'Unknown {GameType}: {game_type}')



class MaterialDefaultValueSetter:
    def __init__(self, material_names: ShaderMaterialNames, shader_node_names: ShaderNodeNames):
        self.material_names = material_names
        self.shader_node_names = shader_node_names

    @abstractmethod
    def set_default_values(self):
        raise NotImplementedError()

    def set_up_shadow_ramp_default_value(self, body_part, material, default_missing=0, default_exists=1):
        possible_shadow_ramp_node_group_names = [
            f'{body_part} Shadow Ramp',
            'Shadow Ramp',
        ]
        for shadow_ramp_node_name in possible_shadow_ramp_node_group_names:
            shadow_ramp_node_group = bpy.data.node_groups.get(shadow_ramp_node_name)
            if shadow_ramp_node_group:
                shadow_ramp_node = shadow_ramp_node_group.nodes.get(f'{body_part}_Shadow_Ramp')

        if not shadow_ramp_node_group or not shadow_ramp_node:
            return

        default_value = default_missing if not shadow_ramp_node.image else default_exists

        body_shader_node = material.node_tree.nodes.get(self.shader_node_names.BODY_SHADER)
        if body_shader_node:
            shader_use_shadow_ramp_input = body_shader_node.inputs.get(self.shader_node_names.USE_SHADOW_RAMP)
            if shader_use_shadow_ramp_input:
                shader_use_shadow_ramp_input.default_value = default_value

    def set_up_lightmap_ao_default_value(self, body_part, material, default_missing=0, default_exists=1):
        lightmap_uv0 = material.node_tree.nodes.get(f'{body_part}_Lightmap_UV0')
        lightmap_uv1 = material.node_tree.nodes.get(f'{body_part}_Lightmap_UV1')
        lightmap_all = material.node_tree.nodes.get(V4_GenshinImpactTextureNodeNames.LIGHTMAP)  # >= v4.0 Body/Hair use same node name

        if (not lightmap_uv0 or not lightmap_uv1) and not lightmap_all:
            return

        if lightmap_uv0 and lightmap_uv1:
            default_value = default_missing if not lightmap_uv0.image or not lightmap_uv1.image else default_exists
        else:
            default_value = default_missing if not lightmap_all.image else default_exists

        body_shader_node = material.node_tree.nodes.get(self.shader_node_names.BODY_SHADER)
        if body_shader_node:
            shader_use_lightmap_ao_input = body_shader_node.inputs.get(self.shader_node_names.USE_LIGHTMAP_AO)
            if shader_use_lightmap_ao_input:
                shader_use_lightmap_ao_input.default_value = default_value

    def set_up_normal_map_default_value(self, material, default_missing=0, default_exists=1):
        if not material or not material.use_nodes or not material.node_tree:
            return

        from setup_wizard.texture_import_setup.texture_importer_types import find_all_image_nodes_by_category
        normal_nodes = find_all_image_nodes_by_category(material.node_tree, 'normal')
        has_normal_image = any(n.image is not None for n in normal_nodes)
        default_value = default_exists if has_normal_image else default_missing

        socket_name = getattr(self.shader_node_names, 'USE_NORMAL_MAP', 'Use Normal Map') or 'Use Normal Map'

        body_shader_node = material.node_tree.nodes.get(self.shader_node_names.BODY_SHADER)
        if not body_shader_node:
            for node in material.node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree:
                    if socket_name in node.inputs:
                        body_shader_node = node
                        break

        if body_shader_node:
            shader_use_normal_map_input = body_shader_node.inputs.get(socket_name)
            if shader_use_normal_map_input:
                shader_use_normal_map_input.default_value = default_value

    def set_up_veil_material_default_value(self, material, default_value=1.0):
        if not material or not material.use_nodes or not material.node_tree:
            return

        if 'Veil' in material.name or 'veil' in material.name.lower():
            body_shader_node = material.node_tree.nodes.get(self.shader_node_names.BODY_SHADER)
            if not body_shader_node:
                for node in material.node_tree.nodes:
                    if node.type == 'GROUP' and node.node_tree:
                        if 'Use Material 2' in node.inputs:
                            body_shader_node = node
                            break

            if body_shader_node:
                use_mat2_input = body_shader_node.inputs.get('Use Material 2')
                if use_mat2_input:
                    use_mat2_input.default_value = default_value

    def set_up_hair_material(self, material):
        raise NotImplementedError("This method should be implemented in subclasses that require hair material setup.")


class GenshinImpactMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self, material_names: ShaderMaterialNames, shader_node_names: ShaderNodeNames) -> None:
        super().__init__(material_names, shader_node_names)

    def set_default_values(self):
        materials_to_check = [
            material for material in bpy.data.materials if material.use_nodes and material.node_tree and (
                (self.material_names.MATERIAL_PREFIX and material.name.startswith(self.material_names.MATERIAL_PREFIX)) or
                (self.material_names.MATERIAL_PREFIX_AFTER_RENAME and material.name.startswith(self.material_names.MATERIAL_PREFIX_AFTER_RENAME))
            )
        ]

        for material in materials_to_check:
            # The reason we try both is so that we don't need to explicitly list out materials
            # Basically it's to futureproof Setup Wizard when future characters have different material names
            self.set_up_shadow_ramp_default_value('Body', material)
            self.set_up_shadow_ramp_default_value('Hair', material)

            self.set_up_lightmap_ao_default_value('Body', material)
            self.set_up_lightmap_ao_default_value('Hair', material)

            self.set_up_normal_map_default_value(material)
            self.set_up_veil_material_default_value(material)
        
        body2_material = bpy.data.materials.get(self.material_names.BODY2)
        if body2_material:
            self.set_up_body2_material(body2_material)

    def set_up_body2_material(self, material):
        material.name = self.material_names.BODY2

        body_shader = material.node_tree.nodes.get(self.shader_node_names.BODY_SHADER)
        body_hair_ramp_switch = body_shader.inputs.get(self.shader_node_names.BODY_HAIR_RAMP_SWITCH)
        if body_hair_ramp_switch:
            body_hair_ramp_switch_values: BodyHairRampSwitchValues = BodyHairRampSwitchValues(self.shader_node_names)
            body_hair_ramp_switch.default_value = body_hair_ramp_switch_values.BODY2

    def set_up_hair_material(self, material):
        material.name = self.material_names.HAIR
        material.use_fake_user = True

        body_shader = material.node_tree.nodes.get(self.shader_node_names.BODY_SHADER)
        body_hair_ramp_switch = body_shader.inputs.get(self.shader_node_names.BODY_HAIR_RAMP_SWITCH)
        if body_hair_ramp_switch:
            body_hair_ramp_switch_values: BodyHairRampSwitchValues = BodyHairRampSwitchValues(self.shader_node_names)
            body_hair_ramp_switch.default_value = body_hair_ramp_switch_values.HAIR


class HonkaiStarRailMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self) -> None:
        return

    def set_default_values(self):
        for material in bpy.data.materials:
            if not material or not material.node_tree:
                continue
            mat_name = material.name.lower()
            is_trans = ('_trans' in mat_name or 
                        'transparent' in mat_name or 
                        'eyespecular' in mat_name or 
                        'eye_specular' in mat_name or 
                        'eyeshadow' in mat_name or 
                        'eyestar' in mat_name or
                        'body_d1' in mat_name or
                        '_d1' in mat_name or
                        'body1_d1' in mat_name or
                        ('robin' in mat_name and 'd1' in mat_name))
            val = 1.0 if is_trans else 0.0
            for node in material.node_tree.nodes:
                inp = node.inputs.get('Enable Transparency')
                if inp:
                    inp.default_value = val
                if node.type == 'GROUP' and node.node_tree:
                    for sub_node in node.node_tree.nodes:
                        sub_inp = sub_node.inputs.get('Enable Transparency')
                        if sub_inp:
                            sub_inp.default_value = val


class PunishingGrayRavenMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self) -> None:
        return

    def set_default_values(self):
        return


class ZenlessZoneZeroMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self) -> None:
        return

    def set_default_values(self):
        return


class NevernessToEvernessMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self) -> None:
        return

    def set_default_values(self):
        return


class WutheringWavesMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self) -> None:
        return

    def set_default_values(self):
        return


class ArknightsEndfieldMaterialDefaultValueSetter(MaterialDefaultValueSetter):
    def __init__(self, character_folder: str = None) -> None:
        self.character_folder = character_folder

    def set_default_values(self):
        import os, json
        from setup_wizard.import_order import get_active_character_directory

        folder = self.character_folder or get_active_character_directory() or bpy.context.scene.get("setup_wizard_imported_model_dir")
        if not folder or not os.path.isdir(folder):
            return

        json_data = {}
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith('.json'):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as jf:
                            d = json.load(jf)
                            stem = os.path.splitext(f)[0].lower()
                            json_data[stem] = d
                    except Exception:
                        pass

        for mat in bpy.data.materials:
            if not mat.use_nodes or not mat.node_tree:
                continue
            mat_name = mat.name.lower()

            matched_json = None
            for j_stem, j_content in json_data.items():
                if j_stem in mat_name or mat_name in j_stem:
                    matched_json = j_content
                    break
                parts = mat_name.split('_')
                if len(parts) >= 2 and '_'.join(parts[-2:]) in j_stem:
                    matched_json = j_content
                    break

            if not matched_json:
                continue

            saved_props = matched_json.get('m_SavedProperties', {})
            floats = saved_props.get('m_Floats', {})
            colors = saved_props.get('m_Colors', {})

            # Blend mode / transparency
            surface_type = float(floats.get('_SurfaceType', 0.0) or 0.0)
            blend_mode = float(floats.get('_BlendMode', 0.0) or 0.0)
            alpha_clip = float(floats.get('_AlphaClip', 0.0) or 0.0)
            
            if 'body' in mat_name and not any(k in mat_name for k in ['eyeshadow', 'eyewhite', 'whiteshadow', 'eye_shadow']):
                is_transp = False
            else:
                is_transp = (surface_type > 0.0 or blend_mode > 0.0 or alpha_clip > 0.0 or any(k in mat_name for k in ['cloth_03', 'cloth_04', 'cloth_07', 'cloth_08', 'vfxpart', 'eyeshadow', 'eyewhite', 'whiteshadow', 'eye_shadow']))

            if is_transp:
                try:
                    mat.surface_render_method = 'BLENDED'
                    mat.use_backface_culling = False
                    mat.show_transparent_back = False
                except Exception:
                    pass
                if hasattr(mat, "blend_method"):
                    try:
                        mat.blend_method = 'BLEND'
                    except Exception:
                        pass
            else:
                try:
                    mat.surface_render_method = 'DITHERED'
                    mat.use_backface_culling = False
                except Exception:
                    pass

            # Update shader node group inputs
            for node in mat.node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree:
                    inputs = node.inputs
                    if 'BaseColor' in inputs and '_BaseColor' in colors:
                        c = colors['_BaseColor']
                        try:
                            inputs['BaseColor'].default_value = (c.get('r', 1.0), c.get('g', 1.0), c.get('b', 1.0), c.get('a', 1.0))
                        except Exception:
                            pass
                        # The Default baseline is re-captured on the next sync
                        try:
                            if 'ake_def_BaseColor' in mat.keys():
                                del mat['ake_def_BaseColor']
                        except Exception:
                            pass

                    if 'Emission Color' in inputs and '_EmissionColor' in colors:
                        c = colors['_EmissionColor']
                        br = float(floats.get('_EmissionBrightness', 1.0) or 1.0)
                        try:
                            inputs['Emission Color'].default_value = (c.get('r', 0.0) * br, c.get('g', 0.0) * br, c.get('b', 0.0) * br, 1.0)
                        except Exception:
                            pass

                    # AKE shader defaults: SmoothnessMax 2.0 (1.0 on hair, max), NormalStrength 1.5, ToonFresnelPow 7.0 on hair, Front R Smo 1.7 on face
                    is_hair = 'hair' in mat_name
                    is_face = 'face' in mat_name
                    if 'SmoothnessMax' in inputs:
                        try:
                            inputs['SmoothnessMax'].default_value = 1.0 if is_hair else 2.0
                        except Exception:
                            pass

                    if 'NormalStrength' in inputs:
                        try:
                            inputs['NormalStrength'].default_value = 1.5
                        except Exception:
                            pass

                    if 'HNormalStrength' in inputs:
                        try:
                            inputs['HNormalStrength'].default_value = 1.5
                        except Exception:
                            pass

                    if 'Skin NormalStrength' in inputs:
                        try:
                            inputs['Skin NormalStrength'].default_value = 1.5
                        except Exception:
                            pass

                    if is_hair:
                        for fresnel_pow_key in ('ToonFresnelPow', 'Toon Fresnel Pow', 'ToonFresnel Pow', 'Toon FresnelPow'):
                            if fresnel_pow_key in inputs:
                                try:
                                    inputs[fresnel_pow_key].default_value = 7.0
                                except Exception:
                                    pass
                        for inp in inputs:
                            try:
                                k_low = inp.name.lower().replace(' ', '').replace('_', '')
                                if 'fresnel' in k_low and 'pow' in k_low and 'toon' in k_low:
                                    inp.default_value = 7.0
                            except Exception:
                                pass

                    if is_face:
                        for smo_key in ('Front R Smo', 'Front R Smooth', 'Front R Smoothness', 'Front RSmo', 'FrontR Smo'):
                            if smo_key in inputs:
                                try:
                                    inputs[smo_key].default_value = 1.7
                                except Exception:
                                    pass
                        for inp in inputs:
                            try:
                                k_low = inp.name.lower().replace(' ', '').replace('_', '')
                                if 'front' in k_low and 'smo' in k_low:
                                    inp.default_value = 1.7
                            except Exception:
                                pass

                    if 'Use NormalTex?' in inputs:
                        try:
                            inputs['Use NormalTex?'].default_value = True
                        except Exception:
                            pass

                    if 'MetallicMax' in inputs:
                        try:
                            if is_hair:
                                inputs['MetallicMax'].default_value = 0.4
                            elif '_Metallic' in floats:
                                inputs['MetallicMax'].default_value = float(floats['_Metallic'])
                        except Exception:
                            pass

                    if 'SpecularColor' in inputs and '_Specular' in floats:
                        sp = float(floats['_Specular'])
                        try:
                            inputs['SpecularColor'].default_value = (sp, sp, sp, 1.0)
                        except Exception:
                            pass
                        # The Default baseline is re-captured on the next sync
                        try:
                            if 'ake_def_SpecularColor' in mat.keys():
                                del mat['ake_def_SpecularColor']
                        except Exception:
                            pass

                    if 'Highlight length' in inputs and '_AnisotropyIntensity' in floats:
                        try:
                            inputs['Highlight length'].default_value = float(floats['_AnisotropyIntensity'])
                        except Exception:
                            pass

                    if 'Front R Color' in inputs and '_SDFRimColor' in colors:
                        c = colors['_SDFRimColor']
                        try:
                            inputs['Front R Color'].default_value = (c.get('r', 1.0), c.get('g', 1.0), c.get('b', 1.0), 1.0)
                        except Exception:
                            pass

                    if 'Rim_Color' in inputs and '_SDFRimColor' in colors:
                        c = colors['_SDFRimColor']
                        try:
                            inputs['Rim_Color'].default_value = (c.get('r', 1.0), c.get('g', 1.0), c.get('b', 1.0), 1.0)
                        except Exception:
                            pass

                    if 'nose_shadow_Color' in inputs and '_NoseShadowColor' in colors:
                        c = colors['_NoseShadowColor']
                        try:
                            inputs['nose_shadow_Color'].default_value = (c.get('r', 1.0), c.get('g', 1.0), c.get('b', 1.0), 1.0)
                        except Exception:
                            pass

                    if 'Eyes HightLight brightness' in inputs:
                        if '_EyeHighLightColor' in colors:
                            c = colors['_EyeHighLightColor']
                            mag = max(c.get('r', 1.0), c.get('g', 1.0), c.get('b', 1.0))
                            try:
                                inputs['Eyes HightLight brightness'].default_value = max(mag * 2.0, 5.0)
                            except Exception:
                                pass
                        elif '_EmissionBrightness' in floats:
                            try:
                                inputs['Eyes HightLight brightness'].default_value = float(floats['_EmissionBrightness']) * 5.0
                            except Exception:
                                pass
                        # The Character Settings multiplier base is re-captured
                        for _k in ("ake_eye_base", "ake_eye_hl_base"):
                            try:
                                if _k in mat.keys():
                                    del mat[_k]
                            except Exception:
                                pass

                    if 'Eyes brightness' in inputs and '_EmissionBrightness' in floats:
                        try:
                            inputs['Eyes brightness'].default_value = max(float(floats['_EmissionBrightness']), 1.2)
                        except Exception:
                            pass
                        # The Character Settings multiplier base is re-captured
                        for _k in ("ake_eye_base", "ake_eye_hl_base"):
                            try:
                                if _k in mat.keys():
                                    del mat[_k]
                            except Exception:
                                pass

