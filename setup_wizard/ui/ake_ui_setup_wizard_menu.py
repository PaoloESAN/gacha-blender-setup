# Arknights: Endfield UI Setup Wizard Menu
# Adapted for Gacha Setup Wizard

import bpy
from bpy.types import Panel

from setup_wizard.domain.game_types import GameType
from setup_wizard.ui.ui_render_checker import ArknightsEndfieldUIRenderChecker
from setup_wizard.ui.gi_ui_setup_wizard_menu import OperatorFactory


class AKE_PT_Setup_Wizard_UI_Layout(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "Arknights: Endfield Setup Wizard"
    bl_idname = "AKE_PT_Setup_Wizard_UI_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"

    def draw(self, context):
        layout = self.layout

        sub_layout = layout.box()
        run_entire_setup_column = sub_layout.column()
        OperatorFactory.create(
            run_entire_setup_column,
            "arknights_endfield.setup_wizard_ui",
            "Run Entire Setup",
            "PLAY",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
            operator_context="INVOKE_DEFAULT",
        )

        settings_box = layout.box()
        settings_header = settings_box.row()
        settings_header.label(text="Setup Settings", icon="PREFERENCES")

        settings_col = settings_box.column()
        props = context.scene.character_rigger_props
        enable_physics = getattr(props, "enable_hair_clothes_physics", getattr(props, "enable_hair_dress_physics", False))
        settings_col.prop(props, "enable_hair_clothes_physics", text="Hair & Clothes Physics")
        sliders_col = settings_col.column()
        sliders_col.active = enable_physics
        sliders_col.prop(props, "hair_physics_influence", text="Hair", slider=True)
        sliders_col.prop(props, "clothes_physics_influence", text="Clothes", slider=True)
        settings_col.prop(props, "disable_rigging", text="Disable Rigging")


class AKE_PT_Basic_Setup_Wizard_UI_Layout(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "Basic Setup"
    bl_idname = "AKE_PT_UI_Basic_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.box()

        # Step 1: Set Up Character
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.set_up_character",
            "Set Up Character",
            icon="OUTLINER_OB_ARMATURE",
            operator_context="INVOKE_DEFAULT",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )

        # Step 2: Set Up Materials
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.set_up_materials",
            "Set Up Materials",
            icon="MATERIAL",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
            operator_context="INVOKE_DEFAULT",
        )

        # Step 3: Setup Outlines
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.set_up_outlines",
            "Setup Outlines",
            icon="GEOMETRY_NODES",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )

        # Step 4: Rig Character
        OperatorFactory.create_rig_character_ui(sub_layout, game_type=GameType.ARKNIGHTS_ENDFIELD.name)

        # Step 5: Setup Compositor Nodes
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.setup_compositor_nodes",
            "Setup Compositor Nodes",
            icon="NODE_COMPOSITING",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )

        # Step 6: Finish Setup
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.finish_setup",
            "Finish Setup",
            icon="CHECKMARK",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )


class AKE_PT_Advanced_Setup_Wizard_UI_Layout(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "Advanced Setup"
    bl_idname = "AKE_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass


class AKE_PT_UI_Character_Model_Menu(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "1. Character Model"
    bl_parent_id = "AKE_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)
        sub_layout.label(text="Import FBX model & Smooth Normals", icon="INFO")
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.set_up_character",
            "Import Character Model",
            "IMPORT",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
            operator_context="INVOKE_DEFAULT",
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.fix_transformations",
            "Fix Transformations",
            "OBJECT_ORIGIN",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.delete_empties",
            "Delete Empties",
            "TRASH",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.reorient_bones",
            "Fix Orientation",
            "BONE_DATA",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )


class AKE_PT_UI_Materials_Menu(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "2. Materials"
    bl_parent_id = "AKE_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "genshin.import_materials",
            "Import Shader Materials",
            "IMPORT",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )

        OperatorFactory.create(
            sub_layout,
            "genshin.replace_default_materials",
            "Replace Default Materials",
            "MATERIAL",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )

        OperatorFactory.create(
            sub_layout,
            "genshin.import_textures",
            "Import Character Textures",
            "TEXTURE",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
            operator_context="INVOKE_DEFAULT",
        )


class AKE_PT_UI_Outlines_Menu(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "3. Outlines"
    bl_parent_id = "AKE_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.set_up_outlines",
            "Setup Outlines",
            "GEOMETRY_NODES",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )


class AKE_PT_UI_Rig_Character_Menu(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "4. Rig Character"
    bl_parent_id = "AKE_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)
        OperatorFactory.create_rig_character_ui(sub_layout, game_type=GameType.ARKNIGHTS_ENDFIELD.name)
        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.setup_face_rig",
            "Set Up Isaac Face Rig",
            "ARMATURE_DATA",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )


class AKE_PT_UI_Finish_Setup_Menu(Panel, ArknightsEndfieldUIRenderChecker):
    bl_label = "5. Finish Setup"
    bl_parent_id = "AKE_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.setup_compositor_nodes",
            "Setup Compositor Nodes",
            "NODE_COMPOSITING",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )

        OperatorFactory.create(
            sub_layout,
            "arknights_endfield.finish_setup",
            "Finish Setup",
            "CHECKMARK",
            game_type=GameType.ARKNIGHTS_ENDFIELD.name,
        )


# ---------------------------------------------------------------------------
# AKE Character Settings (light presets + shader props, Item tab)
# Only these shader inputs are exposed:
# Base Color, dirLight_lightColor, ambientlightcolortint, specularcolor,
# NormalStrength, fresnelInsideColor, fresnelOutsideColor, ToonfresnelPow
# ---------------------------------------------------------------------------

AKE_LIGHT_PRESETS = {
    "0": {  # Default
        "ambient": (1.0, 1.0, 1.0),
        "ambient_tint": (1.0, 1.0, 1.0),
        "dir_light": (1.0, 1.0, 1.0),
        "specular": (1.0, 1.0, 1.0),
        "base_color": (1.0, 1.0, 1.0),
        "fresnel_inside": (1.0, 1.0, 1.0),
        "fresnel_outside": (1.0, 1.0, 1.0),
    },
    "1": {  # Sunrise
        "ambient": (0.95, 0.85, 0.8),
        "ambient_tint": (0.95, 0.85, 0.8),
        "dir_light": (1.0, 0.88, 0.75),
        "specular": (1.0, 0.9, 0.8),
        "base_color": (0.95, 0.85, 0.8),
        "fresnel_inside": (1.0, 0.85, 0.7),
        "fresnel_outside": (0.85, 0.7, 0.55),
    },
    "2": {  # Day
        "ambient": (0.95, 0.98, 1.0),
        "ambient_tint": (0.95, 0.98, 1.0),
        "dir_light": (1.0, 1.0, 0.98),
        "specular": (1.0, 1.0, 1.0),
        "base_color": (0.95, 0.98, 1.0),
        "fresnel_inside": (1.0, 1.0, 1.0),
        "fresnel_outside": (0.9, 0.95, 1.0),
    },
    "3": {  # Sunset
        "ambient": (0.9, 0.7, 0.6),
        "ambient_tint": (0.9, 0.7, 0.6),
        "dir_light": (1.0, 0.65, 0.45),
        "specular": (1.0, 0.75, 0.5),
        "base_color": (0.9, 0.7, 0.6),
        "fresnel_inside": (1.0, 0.7, 0.5),
        "fresnel_outside": (0.95, 0.55, 0.35),
    },
    "4": {  # Night
        "ambient": (0.35, 0.4, 0.55),
        "ambient_tint": (0.35, 0.4, 0.55),
        "dir_light": (0.6, 0.7, 0.95),
        "specular": (0.5, 0.65, 0.9),
        "base_color": (0.35, 0.4, 0.55),
        "fresnel_inside": (0.4, 0.6, 0.95),
        "fresnel_outside": (0.3, 0.5, 0.85),
    },
    "5": {  # Rainy
        "ambient": (0.55, 0.6, 0.65),
        "ambient_tint": (0.55, 0.6, 0.65),
        "dir_light": (0.75, 0.8, 0.85),
        "specular": (0.7, 0.75, 0.8),
        "base_color": (0.55, 0.6, 0.65),
        "fresnel_inside": (0.65, 0.75, 0.85),
        "fresnel_outside": (0.5, 0.6, 0.7),
    },
}

_is_updating_ake_props = False

# Last color values actually applied to materials (per shader input name).
# Custom mode only pushes colors that changed since this snapshot, so
# per-material authored values are preserved until the user edits a color.
_ake_applied_colors = {}

# Shader input name -> scene prop holding its Custom/preset value.
_AKE_COLOR_SCENE_PROPS = {
    'BaseColor': 'ake_base_color',
    'dirLight_lightColor': 'ake_dir_light_color',
    'AmbientLightColorTint': 'ake_amb_color',
    'SpecularColor': 'ake_specular_color',
    'fresnelInsideColor': 'ake_fresnel_inside',
    'fresnelOutsideColor': 'ake_fresnel_outside',
}


def _resolve_ake_target_rig(context):
    """Returns the AKE character armature targeted by the context (or None)."""
    if context is None:
        try:
            context = bpy.context
        except Exception:
            return None
    candidates = []
    try:
        obj = getattr(context, "active_object", None)
    except Exception:
        obj = None
    if obj is not None:
        candidates.append(obj)
    try:
        candidates.extend(list(getattr(context, "selected_objects", []) or []))
    except Exception:
        pass
    for cand in candidates:
        if cand is None:
            continue
        if getattr(cand, "type", None) == 'ARMATURE':
            return cand
        parent = getattr(cand, "parent", None)
        if parent is not None and getattr(parent, "type", None) == 'ARMATURE':
            return parent
    return None


def _is_ake_shader_node(node):
    try:
        if node.type == 'GROUP' and node.node_tree:
            nt_low = node.node_tree.name.lower()
            return 'pbrtoon' in nt_low or 'endfield' in nt_low or 'arknights' in nt_low
    except Exception:
        pass
    return False


def get_ake_character_materials(context=None):
    """AKE shader materials of the selected character.

    Returns (rig, [materials]). If no character can be resolved,
    returns (None, []) so the caller decides (global or do nothing).
    This keeps Shading Settings independent per character.
    """
    rig = _resolve_ake_target_rig(context)
    if rig is None:
        return None, []
    mats = []
    seen = set()

    def _add(mat):
        if mat is not None and mat.name not in seen:
            seen.add(mat.name)
            mats.append(mat)

    try:
        for child in rig.children_recursive:
            if getattr(child, "type", None) == 'MESH':
                for slot in child.material_slots:
                    _add(slot.material)
    except Exception:
        pass
    if not mats:
        # Fallback: meshes with an Armature modifier pointing at the rig
        try:
            for obj in bpy.data.objects:
                if getattr(obj, "type", None) != 'MESH':
                    continue
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE' and getattr(mod, "object", None) == rig:
                        for slot in obj.material_slots:
                            _add(slot.material)
                        break
        except Exception:
            pass
    ake_mats = []
    for mat in mats:
        try:
            if mat.node_tree and any(_is_ake_shader_node(n) for n in mat.node_tree.nodes):
                ake_mats.append(mat)
        except Exception:
            continue
    return rig, ake_mats


def _read_ake_input(mats, input_names):
    """Reads the first value found for a shader input across a material list."""
    for mat in mats:
        try:
            nodes = mat.node_tree.nodes
        except Exception:
            continue
        for node in nodes:
            if not _is_ake_shader_node(node):
                continue
            for iname in input_names:
                try:
                    inp = node.inputs.get(iname)
                except Exception:
                    inp = None
                if inp is not None:
                    try:
                        return float(inp.default_value)
                    except Exception:
                        continue
    return None


def pull_ake_panel_values(scene, context):
    """Copies the selected character's values into the scene props.

    This way sliders show/edit only that character (independent per
    character) instead of overwriting every shader in the scene.
    """
    global _is_updating_ake_props
    if scene is None:
        return
    try:
        _, mats = get_ake_character_materials(context)
    except Exception:
        return
    if not mats:
        return
    base_mats = [m for m in mats if 'hair' not in m.name.lower()]
    hair_mats = [m for m in mats if 'hair' in m.name.lower()]
    _is_updating_ake_props = True
    try:
        v = _read_ake_input(base_mats, ('SmoothnessMax',))
        if v is not None:
            try:
                scene.ake_smoothness_max = v
            except Exception:
                pass
        v = _read_ake_input(base_mats, ('NormalStrength', 'Skin NormalStrength'))
        if v is not None:
            try:
                scene.ake_normal_strength = v
            except Exception:
                pass
        v = _read_ake_input(hair_mats, ('SmoothnessMax',))
        if v is not None:
            try:
                scene.ake_hair_smoothness_max = v
            except Exception:
                pass
        v = _read_ake_input(hair_mats, ('HNormalStrength', 'NormalStrength'))
        if v is not None:
            try:
                scene.ake_hair_normal_strength = v
            except Exception:
                pass
        # Eye multiplier: derived from current / stored base
        eye_mult = None
        for mat in mats:
            try:
                base = float(mat['ake_eye_hl_base'])
            except Exception:
                base = 0.0
            if not base:
                continue
            v = _read_ake_input([mat], ('Eyes HightLight brightness',))
            if v is None:
                continue
            eye_mult = max(1.0, min(20.0, v / base))
            break
        if eye_mult is not None:
            try:
                scene.ake_eyes_brightness = eye_mult
            except Exception:
                pass
        v = _read_ake_input(mats, ('Rain On', 'Skin Rain On'))
        if v is not None:
            try:
                scene.ake_rain_on = bool(v)
            except Exception:
                pass
    finally:
        _is_updating_ake_props = False


def sync_ake_shader_properties(scene=None, context=None, strict_character=False):
    scene = scene or getattr(bpy.context, "scene", None)
    if not scene:
        return

    amb_col = tuple(getattr(scene, "ake_amb_color", getattr(scene, "ake_ambient_tint", (1.0, 1.0, 1.0))))
    dir_col = tuple(getattr(scene, "ake_dir_light_color", (1.0, 1.0, 1.0)))
    spec_col = tuple(getattr(scene, "ake_specular_color", (1.0, 1.0, 1.0)))
    base_col = tuple(getattr(scene, "ake_base_color", (1.0, 1.0, 1.0)))
    fres_in = tuple(getattr(scene, "ake_fresnel_inside", (1.0, 1.0, 1.0)))
    fres_out = tuple(getattr(scene, "ake_fresnel_outside", (1.0, 1.0, 1.0)))
    smoothness_max = float(getattr(scene, "ake_smoothness_max", 1.0))
    normal_strength = float(getattr(scene, "ake_normal_strength", 1.5))
    hair_smoothness_max = float(getattr(scene, "ake_hair_smoothness_max", 1.0))
    hair_normal_strength = float(getattr(scene, "ake_hair_normal_strength", 1.5))
    # Default (mode "0") = shader defaults: restored per material
    # (each material has its own defaults, e.g. body_01 SpecularColor
    # differs from face_01), the preset is not applied.
    is_default_mode = str(getattr(scene, "ake_light_mode", "0")) == "0"
    eye_mult = float(getattr(scene, "ake_eyes_brightness", 1.0))
    eye_mult = max(1.0, min(20.0, eye_mult))
    rain_on = bool(getattr(scene, "ake_rain_on", False))

    color_props = {
        'BaseColor': (*base_col[:3], 1.0),
        'dirLight_lightColor': (*dir_col[:3], 1.0),
        'AmbientLightColorTint': (*amb_col[:3], 1.0),
        'SpecularColor': (*spec_col[:3], 1.0),
        'fresnelInsideColor': (*fres_in[:3], 1.0),
        'fresnelOutsideColor': (*fres_out[:3], 1.0),
    }
    # NOTE: Normal Strength / Smoothness Max are split on purpose:
    # global props only affect body/face/cloth, hair has its own props.
    float_props = {
        'SmoothnessMax': smoothness_max,
        'NormalStrength': normal_strength,
        'Skin NormalStrength': normal_strength,
    }
    hair_float_props = {
        'SmoothnessMax': hair_smoothness_max,
        'NormalStrength': hair_normal_strength,
        'HNormalStrength': hair_normal_strength,
    }
    # One checkbox enables both rain inputs of the main shader
    bool_props = {
        'Rain On': rain_on,
        'Skin Rain On': rain_on,
    }
    # Eyes (irisBase): input -> key where its base value is stored for multiplying
    eye_inputs = {
        'Eyes brightness': 'ake_eye_base',
        'Eyes HightLight brightness': 'ake_eye_hl_base',
    }

    def _is_hair(mat, node_tree_name=""):
        return (
            'hair' in (mat.name.lower() if mat else '')
            or 'hair' in (node_tree_name.lower() if node_tree_name else '')
        )

    # 1. Target materials: only the selected character (independent
    # per character). No character in context: global unless strict_character.
    if context is None:
        try:
            context = bpy.context
        except Exception:
            context = None
    try:
        _, scoped_mats = get_ake_character_materials(context)
    except Exception:
        scoped_mats = []
    if scoped_mats:
        target_materials = scoped_mats
    elif strict_character:
        return
    else:
        target_materials = [m for m in bpy.data.materials if m and m.node_tree]

    # 1b. Update material group nodes (fast O(1) RNA lookups, only if value differs)
    applied_colors = set()
    for mat in target_materials:
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'GROUP' and node.node_tree:
                nt_low = node.node_tree.name.lower()
                if 'pbrtoon' in nt_low or 'endfield' in nt_low or 'arknights' in nt_low:
                    inputs = node.inputs
                    for k, v in color_props.items():
                        inp = inputs.get(k)
                        if not inp:
                            continue
                        base_key = 'ake_def_' + k
                        try:
                            cur = tuple(inp.default_value)
                        except Exception:
                            continue
                        try:
                            has_base = base_key in mat.keys()
                        except Exception:
                            has_base = False
                        if not has_base:
                            # First contact: the baseline is the current value
                            # (.blend authored or post-texture-import)
                            try:
                                mat[base_key] = cur
                            except Exception:
                                pass
                            if is_default_mode:
                                continue
                            has_base = True
                        if is_default_mode:
                            # Default = shader defaults, per material
                            try:
                                bv = tuple(mat[base_key])
                            except Exception:
                                continue
                            try:
                                if cur[:len(bv)] != bv:
                                    inp.default_value = bv
                            except Exception:
                                pass
                        else:
                            # Custom/preset: only push colors that changed since
                            # the snapshot, preserving per-material values.
                            sc = tuple(v[:3])
                            try:
                                prev = _ake_applied_colors.get(k)
                            except Exception:
                                prev = None
                            if prev is not None and len(prev) == 3 and all(
                                abs(a - b) < 1e-4 for a, b in zip(sc, prev)
                            ):
                                continue
                            try:
                                if cur[:len(v)] != v:
                                    inp.default_value = v
                            except Exception:
                                pass
                            applied_colors.add(k)
                    is_hair = _is_hair(mat, node.node_tree.name)
                    active_float_props = hair_float_props if is_hair else float_props
                    for k, v in active_float_props.items():
                        inp = inputs.get(k)
                        if inp:
                            try:
                                if abs(float(inp.default_value) - v) > 1e-4:
                                    inp.default_value = v
                            except Exception:
                                pass
                    # Eyes: multiplies the base value (respects ~1.2 and 5 defaults).
                    # The base is captured on first contact; mult 1.0 restores it.
                    for iname, base_key in eye_inputs.items():
                        inp = inputs.get(iname)
                        if not inp:
                            continue
                        try:
                            cur = float(inp.default_value)
                        except Exception:
                            continue
                        try:
                            base = float(mat[base_key])
                        except Exception:
                            base = 0.0
                        if base == 0.0:
                            if cur == 0.0:
                                continue
                            base = cur
                            try:
                                mat[base_key] = base
                            except Exception:
                                pass
                        try:
                            target = base * eye_mult
                            if abs(cur - target) > 1e-4:
                                inp.default_value = target
                        except Exception:
                            pass
                    # Rain: the checkbox enables both inputs at once
                    for k, v in bool_props.items():
                        inp = inputs.get(k)
                        if inp:
                            try:
                                if bool(inp.default_value) != v:
                                    inp.default_value = v
                            except Exception:
                                pass

    # 2. Update the main AKE node group interface defaults so newly added nodes inherit them
    for ng_name in ("Arknights: Endfield_PBRToonBase", "Arknights: Endfield_PBRToonBaseFace", "Arknights: Endfield_PBRToonBaseHair"):
        ng = bpy.data.node_groups.get(ng_name)
        if ng and hasattr(ng, "interface"):
            is_hair_ng = 'hair' in ng_name.lower()
            active_float_props = hair_float_props if is_hair_ng else float_props
            for item in ng.interface.items_tree:
                if item.name in color_props:
                    if is_default_mode:
                        # Default = .blend authored: do not overwrite defaults
                        continue
                    if item.name not in applied_colors:
                        continue
                    v = color_props[item.name]
                    try:
                        if tuple(item.default_value)[:len(v)] != v:
                            item.default_value = v
                    except Exception:
                        pass
                elif item.name in active_float_props:
                    v = active_float_props[item.name]
                    try:
                        if abs(float(item.default_value) - v) > 1e-4:
                            item.default_value = v
                    except Exception:
                        pass
                elif item.name in bool_props:
                    v = bool_props[item.name]
                    try:
                        if bool(item.default_value) != v:
                            item.default_value = v
                    except Exception:
                        pass

    # Snapshot colors applied this run (after the whole loop, so every
    # material gets them before the snapshot updates).
    if not is_default_mode:
        for k in applied_colors:
            try:
                _ake_applied_colors[k] = tuple(color_props[k][:3])
            except Exception:
                pass

    if hasattr(bpy.context, 'window_manager') and bpy.context.window_manager:
        for win in getattr(bpy.context.window_manager, 'windows', []):
            screen = getattr(win, 'screen', None)
            if screen:
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()


def update_ake_props(self, context=None):
    if _is_updating_ake_props:
        return
    if context is None:
        try:
            context = bpy.context
        except Exception:
            context = None
    scene = getattr(context, "scene", None) if context else None
    if scene is None:
        scene = getattr(bpy.context, "scene", None)
    sync_ake_shader_properties(scene, context=context)


def pull_ake_color_values(scene, context):
    """Copies the character's current colors into the scene props.

    So Custom starts exactly from the current look (e.g. after Default,
    which restores the per-material authored defaults).
    """
    global _is_updating_ake_props
    if scene is None:
        return
    try:
        _, mats = get_ake_character_materials(context)
    except Exception:
        return
    if not mats:
        return
    base_mats = [m for m in mats if 'hair' not in m.name.lower()]
    ordered = base_mats + [m for m in mats if m not in base_mats]

    def _read_color_from_mat(mat, iname):
        try:
            nodes = mat.node_tree.nodes
        except Exception:
            return None
        for node in nodes:
            if not _is_ake_shader_node(node):
                continue
            try:
                inp = node.inputs.get(iname)
            except Exception:
                inp = None
            if inp is not None:
                try:
                    return tuple(inp.default_value)[:3]
                except Exception:
                    continue
        return None

    def _read_color(mats_list, iname):
        for mat in mats_list:
            v = _read_color_from_mat(mat, iname)
            if v is not None:
                return v
        return None

    # Representative material: first non-hair mat using the MAIN PBRToonBase
    # group, so all six colors come from a single consistent source instead
    # of mixing values across materials (e.g. face Specular is white while
    # body Specular is ~4.2).
    rep = None
    for mat in ordered:
        try:
            nodes = mat.node_tree.nodes
        except Exception:
            continue
        for node in nodes:
            try:
                gname = node.node_tree.name if node.node_tree else ""
            except Exception:
                continue
            if node.type == 'GROUP' and gname == 'Arknights: Endfield_PBRToonBase':
                rep = mat
                break
        if rep is not None:
            break
    if rep is None and ordered:
        rep = ordered[0]

    mapping = {
        'ake_amb_color': 'AmbientLightColorTint',
        'ake_ambient_tint': 'AmbientLightColorTint',
        'ake_dir_light_color': 'dirLight_lightColor',
        'ake_specular_color': 'SpecularColor',
        'ake_base_color': 'BaseColor',
        'ake_fresnel_inside': 'fresnelInsideColor',
        'ake_fresnel_outside': 'fresnelOutsideColor',
    }
    _is_updating_ake_props = True
    try:
        for prop, iname in mapping.items():
            v = _read_color_from_mat(rep, iname) if rep is not None else None
            if v is None:
                v = _read_color(ordered, iname)
            if v is None:
                continue
            try:
                setattr(scene, prop, v)
            except Exception:
                pass
    finally:
        _is_updating_ake_props = False


def update_ake_light_mode(self, context=None):
    global _is_updating_ake_props
    if _is_updating_ake_props:
        return
    if context is None:
        try:
            context = bpy.context
        except Exception:
            context = None
    mode = str(getattr(self, "ake_light_mode", "0"))
    if mode == "6":
        # Custom starts exactly from the current look (e.g. after Default):
        # pull values and snapshot them so the entry sync applies nothing.
        scene = getattr(context, "scene", None) if context else None
        if scene is None:
            scene = getattr(bpy.context, "scene", None)
        _is_updating_ake_props = True
        try:
            pull_ake_color_values(scene or self, context)
            sc = scene or self
            for _iname, _prop in _AKE_COLOR_SCENE_PROPS.items():
                try:
                    _ake_applied_colors[_iname] = tuple(getattr(sc, _prop))[:3]
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            _is_updating_ake_props = False
    elif mode in AKE_LIGHT_PRESETS:
        preset = AKE_LIGHT_PRESETS[mode]
        _is_updating_ake_props = True
        try:
            self.ake_amb_color = preset["ambient"]
            self.ake_ambient_tint = preset["ambient"]
            self.ake_dir_light_color = preset["dir_light"]
            self.ake_specular_color = preset["specular"]
            self.ake_base_color = preset.get("base_color", (1.0, 1.0, 1.0))
            self.ake_fresnel_inside = preset["fresnel_inside"]
            self.ake_fresnel_outside = preset["fresnel_outside"]
        except Exception:
            pass
        finally:
            _is_updating_ake_props = False
    scene = getattr(context, "scene", None) if context else None
    if scene is None:
        scene = getattr(bpy.context, "scene", None)
    sync_ake_shader_properties(scene, context=context)


class AKE_PT_Rig_Character_Settings(Panel):
    bl_label = "Character Settings"
    bl_idname = "AKE_PT_Rig_Character_Settings_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        try:
            from setup_wizard.ui.character_settings_utils import is_game_armature
            return is_game_armature(context, "ARKNIGHTS_ENDFIELD")
        except Exception:
            pass
        obj = context.active_object or context.object
        if not obj:
            return False
        is_rig = (obj.type == 'ARMATURE') or (obj.type == 'MESH' and obj.parent and obj.parent.type == 'ARMATURE')
        if not is_rig:
            return False
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Sliders follow the selected character: they show its actual values
        # and only edit its materials (independent per character).
        try:
            pull_ake_panel_values(scene, context)
        except Exception:
            pass

        # 1. Lighting Mode / Presets
        col_light = layout.column(align=True)
        col_light.label(text="Lighting Mode:")
        col_light.prop(scene, "ake_light_mode", text="")

        # 2. Custom Colors (Shown ONLY when in Custom mode "6")
        if getattr(scene, "ake_light_mode", "0") == "6":
            box_col = col_light.box()
            box_col.label(text="Custom Colors", icon="COLOR")
            col_colors = box_col.column(align=True)
            col_colors.prop(scene, "ake_amb_color", text="Ambient")
            col_colors.prop(scene, "ake_dir_light_color", text="Light")
            col_colors.prop(scene, "ake_specular_color", text="Specular")
            col_colors.prop(scene, "ake_base_color", text="Base Color")
            col_colors.prop(scene, "ake_fresnel_inside", text="Fresnel Inside")
            col_colors.prop(scene, "ake_fresnel_outside", text="Fresnel Outside")

        # 3. General Shading (does not affect hair: hair has its own sliders)
        box_shading = layout.box()
        box_shading.label(text="General Shading", icon="SHADING_RENDERED")
        col_shading = box_shading.column(align=True)
        col_shading.prop(scene, "ake_smoothness_max", text="Smoothness Max", slider=True)
        col_shading.prop(scene, "ake_normal_strength", text="Normal Strength", slider=True)

        # 3b. Hair Shading Settings (hair only)
        box_hair = layout.box()
        box_hair.label(text="Hair Shading", icon="SHADING_RENDERED")
        col_hair = box_hair.column(align=True)
        col_hair.prop(scene, "ake_hair_smoothness_max", text="Hair Smoothness Max", slider=True)
        col_hair.prop(scene, "ake_hair_normal_strength", text="Hair Normal Strength", slider=True)

        # 3c. Eyes Brightness (multiplies the ~1.2 and 5 base brightness values)
        box_eyes = layout.box()
        box_eyes.label(text="Eyes", icon="SHADING_RENDERED")
        col_eyes = box_eyes.column(align=True)
        col_eyes.prop(scene, "ake_eyes_brightness", text="Eyes Brightness", slider=True)

        # 3d. Rain (enables 'Rain On' and 'Skin Rain On' of the main shader)
        box_rain = layout.box()
        box_rain.label(text="Weather", icon="WORLD")
        col_rain = box_rain.column(align=True)
        col_rain.prop(scene, "ake_rain_on", text="Enable Rain")

        # 4. Hair & Clothes Physics
        box_physics = layout.box()
        box_physics.label(text="Hair & Clothes Physics", icon="PHYSICS")
        col_physics = box_physics.column(align=True)
        try:
            from setup_wizard.character_rig_setup.rig_ui_utils import has_hair_clothes_physics
            physics_present = has_hair_clothes_physics(context)
        except Exception:
            physics_present = False

        if physics_present:
            col_physics.prop(scene, "gi_hair_physics_influence", text="Hair Physics", slider=True)
            col_physics.prop(scene, "gi_clothes_physics_influence", text="Clothes Physics", slider=True)
        else:
            col_physics.operator("hoyoverse.apply_hair_clothes_physics", text="Apply Physics", icon="FILE_REFRESH")


def register_ake_properties():
    from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty

    bpy.types.Scene.ake_light_mode = EnumProperty(
        name="Light Mode",
        description="Lighting preset mode for Arknights: Endfield shader",
        items=[
            ("0", "Default", "Default Game Lighting"),
            ("1", "Sunrise", "Sunrise Tone"),
            ("2", "Day", "Bright Daylight"),
            ("3", "Sunset", "Warm Sunset"),
            ("4", "Night", "Cool Night"),
            ("5", "Rainy", "Overcast / Rainy"),
            ("6", "Custom", "Custom User Colors"),
        ],
        default="0",
        update=update_ake_light_mode,
    )
    bpy.types.Scene.ake_amb_color = FloatVectorProperty(
        name="Custom Ambient Color",
        description="Custom ambient color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_ambient_tint = FloatVectorProperty(
        name="Ambient Tint",
        description="Ambient light color tint",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_dir_light_color = FloatVectorProperty(
        name="Custom Light Color",
        description="Custom directional light color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_specular_color = FloatVectorProperty(
        name="Custom Specular Color",
        description="Custom specular color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_base_color = FloatVectorProperty(
        name="Custom Base Color",
        description="Custom base color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_fresnel_inside = FloatVectorProperty(
        name="Custom Fresnel Inside Color",
        description="Custom inside fresnel color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_fresnel_outside = FloatVectorProperty(
        name="Custom Fresnel Outside Color",
        description="Custom outside fresnel color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=10.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_smoothness_max = FloatProperty(
        name="Smoothness Max",
        description="Maximum smoothness / specular glossiness for Arknights: Endfield shader (body/face/cloth, does not affect hair)",
        min=0.0,
        max=2.0,
        default=2.0,
        step=10,
        precision=2,
        update=update_ake_props,
    )
    bpy.types.Scene.ake_normal_strength = FloatProperty(
        name="Normal Strength",
        description="Normal map strength for Arknights: Endfield shader (body/face/cloth, does not affect hair)",
        min=0.0,
        max=5.0,
        default=1.5,
        step=10,
        precision=2,
        update=update_ake_props,
    )
    bpy.types.Scene.ake_hair_smoothness_max = FloatProperty(
        name="Hair Smoothness Max",
        description="Maximum smoothness / specular glossiness, hair only",
        min=0.0,
        max=1.0,
        default=1.0,
        step=10,
        precision=2,
        update=update_ake_props,
    )
    bpy.types.Scene.ake_hair_normal_strength = FloatProperty(
        name="Hair Normal Strength",
        description="Normal map strength, hair only",
        min=0.0,
        max=5.0,
        default=1.5,
        step=10,
        precision=2,
        update=update_ake_props,
    )
    bpy.types.Scene.ake_eyes_brightness = FloatProperty(
        name="Eyes Brightness",
        description="Multiplies the base eye brightness values (Eyes brightness ~1.2 and Eyes HightLight ~5)",
        min=1.0,
        max=20.0,
        default=1.0,
        step=10,
        precision=2,
        update=update_ake_props,
    )
    bpy.types.Scene.ake_rain_on = BoolProperty(
        name="Enable Rain",
        description="Enables 'Rain On' and 'Skin Rain On' of the main shader",
        default=False,
        update=update_ake_props,
    )


def unregister_ake_properties():
    for prop in [
        "ake_light_mode",
        "ake_amb_color",
        "ake_ambient_tint",
        "ake_dir_light_color",
        "ake_specular_color",
        "ake_base_color",
        "ake_fresnel_inside",
        "ake_fresnel_outside",
        "ake_smoothness_max",
        "ake_normal_strength",
        "ake_hair_smoothness_max",
        "ake_hair_normal_strength",
        "ake_eyes_brightness",
        "ake_rain_on",
        "ake_toon_fresnel_pow",
    ]:
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
            except Exception:
                pass


@bpy.app.handlers.persistent
def ake_frame_change_handler(scene, depsgraph=None):
    try:
        ctx = bpy.context
    except Exception:
        ctx = None
    try:
        # strict: at render time never overwrite all materials, only the
        # in-context character (or nothing if there is none).
        sync_ake_shader_properties(scene, context=ctx, strict_character=True)
    except Exception:
        pass
