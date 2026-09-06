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
        "base_color": (1.0, 0.92, 0.85),
        "fresnel_inside": (1.0, 0.85, 0.7),
        "fresnel_outside": (0.85, 0.7, 0.55),
    },
    "2": {  # Day
        "ambient": (0.95, 0.98, 1.0),
        "ambient_tint": (0.95, 0.98, 1.0),
        "dir_light": (1.0, 1.0, 0.98),
        "specular": (1.0, 1.0, 1.0),
        "base_color": (1.0, 1.0, 1.0),
        "fresnel_inside": (1.0, 1.0, 1.0),
        "fresnel_outside": (0.9, 0.95, 1.0),
    },
    "3": {  # Sunset
        "ambient": (0.9, 0.7, 0.6),
        "ambient_tint": (0.9, 0.7, 0.6),
        "dir_light": (1.0, 0.65, 0.45),
        "specular": (1.0, 0.75, 0.5),
        "base_color": (0.95, 0.72, 0.58),
        "fresnel_inside": (1.0, 0.7, 0.5),
        "fresnel_outside": (0.95, 0.55, 0.35),
    },
    "4": {  # Night
        "ambient": (0.35, 0.4, 0.55),
        "ambient_tint": (0.35, 0.4, 0.55),
        "dir_light": (0.6, 0.7, 0.95),
        "specular": (0.5, 0.65, 0.9),
        "base_color": (0.45, 0.52, 0.7),
        "fresnel_inside": (0.4, 0.6, 0.95),
        "fresnel_outside": (0.3, 0.5, 0.85),
    },
    "5": {  # Rainy
        "ambient": (0.55, 0.6, 0.65),
        "ambient_tint": (0.55, 0.6, 0.65),
        "dir_light": (0.75, 0.8, 0.85),
        "specular": (0.7, 0.75, 0.8),
        "base_color": (0.7, 0.75, 0.8),
        "fresnel_inside": (0.65, 0.75, 0.85),
        "fresnel_outside": (0.5, 0.6, 0.7),
    },
}

_is_updating_ake_props = False


def sync_ake_shader_properties(scene=None):
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

    color_props = {
        'BaseColor': (*base_col[:3], 1.0),
        'dirLight_lightColor': (*dir_col[:3], 1.0),
        'AmbientLightColorTint': (*amb_col[:3], 1.0),
        'SpecularColor': (*spec_col[:3], 1.0),
        'fresnelInsideColor': (*fres_in[:3], 1.0),
        'fresnelOutsideColor': (*fres_out[:3], 1.0),
    }
    float_props = {
        'SmoothnessMax': smoothness_max,
        'NormalStrength': normal_strength,
        'HNormalStrength': normal_strength,
        'Skin NormalStrength': normal_strength,
    }

    # 1. Update material group nodes (fast O(1) RNA lookups, only if value differs)
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'GROUP' and node.node_tree:
                nt_low = node.node_tree.name.lower()
                if 'pbrtoon' in nt_low or 'endfield' in nt_low or 'arknights' in nt_low:
                    inputs = node.inputs
                    for k, v in color_props.items():
                        inp = inputs.get(k)
                        if inp:
                            try:
                                if tuple(inp.default_value)[:len(v)] != v:
                                    inp.default_value = v
                            except Exception:
                                pass
                    for k, v in float_props.items():
                        inp = inputs.get(k)
                        if inp:
                            try:
                                if abs(float(inp.default_value) - v) > 1e-4:
                                    inp.default_value = v
                            except Exception:
                                pass

    # 2. Update the main AKE node group interface defaults so newly added nodes inherit them
    for ng_name in ("Arknights: Endfield_PBRToonBase", "Arknights: Endfield_PBRToonBaseFace", "Arknights: Endfield_PBRToonBaseHair"):
        ng = bpy.data.node_groups.get(ng_name)
        if ng and hasattr(ng, "interface"):
            for item in ng.interface.items_tree:
                if item.name in color_props:
                    v = color_props[item.name]
                    try:
                        if tuple(item.default_value)[:len(v)] != v:
                            item.default_value = v
                    except Exception:
                        pass
                elif item.name in float_props:
                    v = float_props[item.name]
                    try:
                        if abs(float(item.default_value) - v) > 1e-4:
                            item.default_value = v
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
    sync_ake_shader_properties(getattr(context, "scene", getattr(bpy.context, "scene", None)))


def update_ake_light_mode(self, context=None):
    global _is_updating_ake_props
    if _is_updating_ake_props:
        return
    mode = str(getattr(self, "ake_light_mode", "0"))
    if mode in AKE_LIGHT_PRESETS:
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
    sync_ake_shader_properties(getattr(context, "scene", getattr(bpy.context, "scene", None)))


class AKE_PT_Rig_Character_Settings(Panel):
    bl_label = "Character Settings"
    bl_idname = "AKE_PT_Rig_Character_Settings_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object or context.object
        if not obj:
            return False

        is_rig = (obj.type == 'ARMATURE') or (obj.type == 'MESH' and obj.parent and obj.parent.type == 'ARMATURE')
        if not is_rig:
            is_ake_mesh = obj.type == 'MESH' and any(
                s.material and any(k in s.material.name.lower() for k in ('arknights', 'endfield', 'body_01', 'face_01', 'cloth_01', 'hair_01'))
                for s in obj.material_slots
            )
            if not is_ake_mesh:
                return False

        if getattr(context.scene, "game_type_dropdown", None) == GameType.ARKNIGHTS_ENDFIELD.name:
            return True

        if any(any(k in m.name.lower() for k in ('arknights', 'endfield')) for m in bpy.data.materials):
            return True
        if any(any(k in m.name.lower() for k in ('body_01', 'face_01', 'cloth_01', 'hair_01')) for m in bpy.data.materials):
            if bpy.data.objects.get('HC') or bpy.data.objects.get('HF') or bpy.data.objects.get('HR'):
                return True

        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

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

        # 3. Shading Settings
        box_shading = layout.box()
        box_shading.label(text="Shading Settings", icon="SHADING_RENDERED")
        col_shading = box_shading.column(align=True)
        col_shading.prop(scene, "ake_smoothness_max", text="Smoothness Max", slider=True)
        col_shading.prop(scene, "ake_normal_strength", text="Normal Strength", slider=True)

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
    from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty

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
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_ambient_tint = FloatVectorProperty(
        name="Ambient Tint",
        description="Ambient light color tint",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_dir_light_color = FloatVectorProperty(
        name="Custom Light Color",
        description="Custom directional light color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
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
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_fresnel_inside = FloatVectorProperty(
        name="Custom Fresnel Inside Color",
        description="Custom inside fresnel color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_fresnel_outside = FloatVectorProperty(
        name="Custom Fresnel Outside Color",
        description="Custom outside fresnel color for Arknights: Endfield shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_ake_props,
    )
    bpy.types.Scene.ake_smoothness_max = FloatProperty(
        name="Smoothness Max",
        description="Maximum smoothness / specular glossiness for Arknights: Endfield shader",
        min=0.0,
        max=5.0,
        default=1.0,
        step=10,
        precision=2,
        update=update_ake_props,
    )
    bpy.types.Scene.ake_normal_strength = FloatProperty(
        name="Normal Strength",
        description="Normal map strength for Arknights: Endfield shader",
        min=0.0,
        max=10.0,
        default=1.5,
        step=10,
        precision=2,
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
        sync_ake_shader_properties(scene)
    except Exception:
        pass
