# Author: michael-gh1 (adapted for ZZZ)

import bpy
from bpy.types import Panel, UILayout

from setup_wizard.domain.game_types import GameType
from setup_wizard.ui.ui_render_checker import ZenlessZoneZeroUIRenderChecker


class ZZZ_PT_Setup_Wizard_UI_Layout(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "Zenless Zone Zero Setup Wizard"
    bl_idname = "ZZZ_PT_Setup_Wizard_UI_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"

    bpy.types.Scene.zzz_shader_type = bpy.props.EnumProperty(
        items=[
            ("KYTHERA", "Kythera's Shader", "Use Kythera's ZZZ Shader (Face Shader + General Shader)"),
            ("LEGACY", "Legacy Shader", "Use Legacy ZZZ Setup File V2.0 Shader"),
        ],
        name="Shader",
        description="Select shader setup for Zenless Zone Zero",
        default="KYTHERA",
    )

    def draw(self, context):
        layout = self.layout
        window_manager = context.window_manager

        sub_layout = layout.box()
        run_entire_setup_column = sub_layout.column()
        OperatorFactory.create(
            run_entire_setup_column,
            "zenless_zone_zero.setup_wizard_ui",
            "Run Entire Setup",
            "PLAY",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )

        settings_box = layout.box()
        settings_header = settings_box.row()
        settings_header.label(text="Setup Settings", icon="PREFERENCES")

        settings_col = settings_box.column()
        settings_col.prop(context.scene, "zzz_shader_type", text="Shader")
        props = context.scene.character_rigger_props
        enable_physics = getattr(props, "enable_hair_clothes_physics", getattr(props, "enable_hair_dress_physics", False))
        settings_col.prop(props, "enable_hair_clothes_physics", text="Hair & Clothes Physics")
        sliders_col = settings_col.column()
        sliders_col.active = enable_physics
        sliders_col.prop(props, "hair_physics_influence", text="Hair", slider=True)
        sliders_col.prop(props, "clothes_physics_influence", text="Clothes", slider=True)
        settings_col.prop(props, "disable_rigging", text="Disable Rigging")


class ZZZ_PT_Basic_Setup_Wizard_UI_Layout(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "Basic Setup"
    bl_idname = "ZZZ_PT_UI_Basic_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.box()

        set_up_character_column = sub_layout.column()
        OperatorFactory.create(
            set_up_character_column,
            "zenless_zone_zero.set_up_character",
            "Set Up Character",
            icon="OUTLINER_OB_ARMATURE",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )

        OperatorFactory.create(
            sub_layout,
            "zenless_zone_zero.set_up_materials",
            "Set Up Materials",
            icon="MATERIAL",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        if bpy.app.version >= (3, 3, 0):
            OperatorFactory.create(
                sub_layout,
                "zenless_zone_zero.set_up_outlines",
                "Set Up Outlines",
                icon="GEOMETRY_NODES",
                game_type=GameType.ZENLESS_ZONE_ZERO.name,
            )
        else:
            layout.label(text="(Outlines Disabled < v3.3.0)")

        OperatorFactory.create(
            sub_layout,
            "genshin.fix_transformations",
            "Fix Transformations",
            "OBJECT_DATA",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )

        OperatorFactory.create_rig_character_ui(sub_layout)

        OperatorFactory.create(
            sub_layout,
            "zenless_zone_zero.finish_setup",
            "Finish Setup",
            icon="CHECKMARK",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )


class ZZZ_PT_Advanced_Setup_Wizard_UI_Layout(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "Advanced Setup"
    bl_idname = "ZZZ_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout


class ZZZ_PT_UI_Character_Model_Menu(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "1. Character Model"
    bl_parent_id = "ZZZ_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "genshin.import_model",
            "Import Character Model",
            "IMPORT",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
            setup_mode="ADVANCED",
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.delete_empties",
            "Delete Empties",
            "TRASH",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.reorient_bones",
            "Fix Orientation",
            "BONE_DATA",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )


class ZZZ_PT_UI_Materials_Menu(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "2. Materials"
    bl_parent_id = "ZZZ_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "genshin.import_materials",
            "Import Materials",
            "IMPORT",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
            setup_mode="ADVANCED",
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.replace_default_materials",
            "Replace Default Materials",
            "MATERIAL",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.import_textures",
            "Import Character Textures",
            "TEXTURE",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )


class ZZZ_PT_UI_Outlines_Menu(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "3. Outlines"
    bl_parent_id = "ZZZ_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        if bpy.app.version >= (3, 3, 0):
            OperatorFactory.create(
                sub_layout,
                "genshin.import_outlines",
                "Import Outlines Node Group",
                "IMPORT",
                game_type=GameType.ZENLESS_ZONE_ZERO.name,
                setup_mode="ADVANCED",
            )
            OperatorFactory.create(
                sub_layout,
                "genshin.setup_geometry_nodes",
                "Set Up Geometry Nodes",
                "GEOMETRY_NODES",
                game_type=GameType.ZENLESS_ZONE_ZERO.name,
            )
            OperatorFactory.create(
                sub_layout,
                "genshin.import_outline_lightmaps",
                "Import Outline Lightmaps",
                "IMAGE_DATA",
                game_type=GameType.ZENLESS_ZONE_ZERO.name,
                setup_mode="ADVANCED",
            )
            OperatorFactory.create(
                sub_layout,
                "genshin.import_material_data",
                "Import Outline Material Data",
                "ASSET_MANAGER",
                game_type=GameType.ZENLESS_ZONE_ZERO.name,
                setup_mode="ADVANCED",
            )
        else:
            layout.label(text="Outlines Disabled (< v3.3.0)")


class ZZZ_PT_UI_Finish_Setup_Menu(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "5. Finish Setup"
    bl_parent_id = "ZZZ_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "zenless_zone_zero.setup_head_driver",
            "Set Up Head Driver",
            "CONSTRAINT",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.set_color_management_to_standard",
            "Set Color Management",
            "COLOR",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        OperatorFactory.create(
            sub_layout,
            "hoyoverse.rename_shader_materials",
            "Rename Shader Materials",
            "FONT_DATA",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        OperatorFactory.create(
            sub_layout,
            "zenless_zone_zero.rename_collection_and_rig",
            "Rename Collection & Rig",
            "OUTLINER_COLLECTION",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        if getattr(context.scene, "zzz_shader_type", "KYTHERA") == "LEGACY":
            OperatorFactory.create(
                sub_layout,
                "zenless_zone_zero.move_lighting_panel_to_char_collection",
                "Move Lighting Panel to Collection",
                "LIGHT",
                game_type=GameType.ZENLESS_ZONE_ZERO.name,
            )


class ZZZ_PT_UI_Character_Rig_Setup_Menu(Panel, ZenlessZoneZeroUIRenderChecker):
    bl_label = "4. Rigging"
    bl_parent_id = "ZZZ_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)
        OperatorFactory.create(
            sub_layout,
            "genshin.fix_transformations",
            "Fix Transformations",
            "OBJECT_DATA",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        OperatorFactory.create_rig_character_ui(sub_layout)
        OperatorFactory.create(
            sub_layout,
            "hoyoverse.apply_hair_clothes_physics",
            "Apply Hair & Clothes Physics",
            "PHYSICS",
        )


class OperatorFactory:
    @staticmethod
    def create(
        ui_object: UILayout,
        operator: str,
        text: str,
        icon: str,
        operator_context="EXEC_DEFAULT",
        **kwargs,
    ):
        ui_object.operator_context = operator_context
        btn = ui_object.operator(
            operator=operator,
            text=text,
            icon=icon,
        )

        if btn:
            for key, value in kwargs.items():
                setattr(btn, key, value)

    @staticmethod
    def create_rig_character_ui(
        ui_object: UILayout,
    ):
        expy_kit_installed = any('expy' in k.lower() for k in bpy.context.preferences.addons.keys())
        rigify_installed = any('rigify' in k.lower() for k in bpy.context.preferences.addons.keys())

        column = ui_object.column()
        column.enabled = True if expy_kit_installed and rigify_installed else False
        OperatorFactory.create(
            column,
            "hoyoverse.set_up_character_rig",
            "Rig Character",
            "OUTLINER_OB_ARMATURE",
            game_type=GameType.ZENLESS_ZONE_ZERO.name,
        )
        if not column.enabled:
            column = ui_object.column()
            if not expy_kit_installed:
                column.label(text="ExpyKit required", icon="ERROR")
            if not rigify_installed:
                column.label(text="Rigify required", icon="ERROR")


ZZZ_LIGHT_PRESETS = {
    "0": { # Default
        "ambient": (1.0, 1.0, 1.0),
        "lit_tint": (1.0, 1.0, 1.0),
        "lit_brightness": 0.0,
        "shadow_tint": (0.65, 0.65, 0.85),
        "shadow_intensity": 1.0,
        "fake_sss_intensity": 1.0,
        "enable_rim": True,
        "rim_color": (1.0, 1.0, 1.0),
        "coverage": 1.0,
        "brightness": 1.0,
        "left_right": 0.5,
        "up_down": 0.1,
    },
    "1": { # Sunrise
        "ambient": (0.95, 0.85, 0.8),
        "lit_tint": (1.0, 0.88, 0.75),
        "lit_brightness": 0.1,
        "shadow_tint": (0.65, 0.65, 0.85),
        "shadow_intensity": 1.0,
        "fake_sss_intensity": 1.0,
        "enable_rim": True,
        "rim_color": (1.0, 0.85, 0.6),
        "coverage": 1.0,
        "brightness": 1.0,
        "left_right": 0.6,
        "up_down": 0.05,
    },
    "2": { # Day
        "ambient": (1.0, 1.0, 1.0),
        "lit_tint": (1.0, 1.0, 1.0),
        "lit_brightness": 0.2,
        "shadow_tint": (0.75, 0.75, 0.85),
        "shadow_intensity": 1.0,
        "fake_sss_intensity": 1.0,
        "enable_rim": True,
        "rim_color": (1.0, 1.0, 1.0),
        "coverage": 1.0,
        "brightness": 1.0,
        "left_right": 0.5,
        "up_down": 0.3,
    },
    "3": { # Sunset
        "ambient": (0.9, 0.75, 0.7),
        "lit_tint": (1.0, 0.65, 0.45),
        "lit_brightness": 0.1,
        "shadow_tint": (0.5, 0.45, 0.7),
        "shadow_intensity": 1.0,
        "fake_sss_intensity": 1.0,
        "enable_rim": True,
        "rim_color": (1.0, 0.6, 0.3),
        "coverage": 1.0,
        "brightness": 1.0,
        "left_right": 0.7,
        "up_down": 0.0,
    },
    "4": { # Night
        "ambient": (0.4, 0.45, 0.6),
        "lit_tint": (0.6, 0.7, 0.9),
        "lit_brightness": 0.0,
        "shadow_tint": (0.25, 0.3, 0.5),
        "shadow_intensity": 1.0,
        "fake_sss_intensity": 0.5,
        "enable_rim": True,
        "rim_color": (0.5, 0.7, 1.0),
        "coverage": 1.0,
        "brightness": 0.8,
        "left_right": 0.4,
        "up_down": 0.1,
    },
    "5": { # Rainy
        "ambient": (0.6, 0.65, 0.7),
        "lit_tint": (0.75, 0.8, 0.85),
        "lit_brightness": 0.0,
        "shadow_tint": (0.45, 0.5, 0.6),
        "shadow_intensity": 0.8,
        "fake_sss_intensity": 0.5,
        "enable_rim": True,
        "rim_color": (0.7, 0.8, 0.9),
        "coverage": 1.0,
        "brightness": 0.7,
        "left_right": 0.5,
        "up_down": 0.4,
    },
}

_is_updating_zzz_props = False

def update_zzz_light_mode(self, context=None):
    global _is_updating_zzz_props
    if _is_updating_zzz_props:
        return
    mode = getattr(self, "zzz_light_mode", "0")
    if mode in ZZZ_LIGHT_PRESETS:
        preset = ZZZ_LIGHT_PRESETS[mode]
        _is_updating_zzz_props = True
        try:
            self.zzz_ambient_tint = preset["ambient"]
            self.zzz_lit_tint = preset["lit_tint"]
            self.zzz_lit_brightness = preset["lit_brightness"]
            self.zzz_shadow_tint = preset["shadow_tint"]
            self.zzz_shadow_intensity = preset.get("shadow_intensity", 1.0)
            self.zzz_fake_sss_intensity = preset.get("fake_sss_intensity", 1.0)
            self.zzz_enable_rim_light = preset["enable_rim"]
            self.zzz_rim_light_color = preset["rim_color"]
            self.zzz_rim_coverage = preset["coverage"]
            self.zzz_rim_brightness = preset["brightness"]
            self.zzz_rim_left_right = preset["left_right"]
            self.zzz_rim_up_down = preset["up_down"]
        finally:
            _is_updating_zzz_props = False
    update_zzz_kythera_props(self, context)


def update_zzz_kythera_props(self, context=None):
    global _is_updating_zzz_props
    if _is_updating_zzz_props:
        return
    scene = bpy.context.scene if context is None else getattr(context, "scene", bpy.context.scene)
    if not scene:
        return

    _is_updating_zzz_props = True
    try:
        # Snap float sliders to 1 decimal place (steps of 0.1) and clamp near-zero
        raw_lb = getattr(scene, "zzz_lit_brightness", 0.0)
        raw_si = getattr(scene, "zzz_shadow_intensity", 1.0)
        raw_sss = getattr(scene, "zzz_fake_sss_intensity", 1.0)
        raw_rc = getattr(scene, "zzz_rim_coverage", 1.0)
        raw_rb = getattr(scene, "zzz_rim_brightness", 1.0)
        raw_lr = getattr(scene, "zzz_rim_left_right", 0.5)
        raw_ud = getattr(scene, "zzz_rim_up_down", 0.1)

        lit_brightness = 0.0 if raw_lb < 0.05 else round(raw_lb, 1)
        shadow_intensity = 0.0 if raw_si < 0.05 else round(raw_si, 1)
        fake_sss_intensity = 0.0 if raw_sss < 0.05 else round(raw_sss, 1)
        rim_coverage = 0.0 if raw_rc < 0.05 else round(raw_rc, 1)
        rim_brightness = 0.0 if raw_rb < 0.05 else round(raw_rb, 1)
        rim_left_right = 0.0 if raw_lr < 0.05 else round(raw_lr, 1)
        rim_up_down = 0.0 if raw_ud < 0.05 else round(raw_ud, 1)

        if scene.zzz_lit_brightness != lit_brightness:
            scene.zzz_lit_brightness = lit_brightness
        if scene.zzz_shadow_intensity != shadow_intensity:
            scene.zzz_shadow_intensity = shadow_intensity
        if scene.zzz_fake_sss_intensity != fake_sss_intensity:
            scene.zzz_fake_sss_intensity = fake_sss_intensity
        if scene.zzz_rim_coverage != rim_coverage:
            scene.zzz_rim_coverage = rim_coverage
        if scene.zzz_rim_brightness != rim_brightness:
            scene.zzz_rim_brightness = rim_brightness
        if scene.zzz_rim_left_right != rim_left_right:
            scene.zzz_rim_left_right = rim_left_right
        if scene.zzz_rim_up_down != rim_up_down:
            scene.zzz_rim_up_down = rim_up_down
    finally:
        _is_updating_zzz_props = False

    ambient_tint = list(getattr(scene, "zzz_ambient_tint", (1.0, 1.0, 1.0)))
    if len(ambient_tint) == 3: ambient_tint.append(1.0)
    
    lit_tint = list(getattr(scene, "zzz_lit_tint", (1.0, 1.0, 1.0)))
    if len(lit_tint) == 3: lit_tint.append(1.0)
    
    shadow_tint = list(getattr(scene, "zzz_shadow_tint", (1.0, 1.0, 1.0)))
    if len(shadow_tint) == 3: shadow_tint.append(1.0)
    
    enable_rim = getattr(scene, "zzz_enable_rim_light", True)
    
    rim_color = list(getattr(scene, "zzz_rim_light_color", (1.0, 1.0, 1.0)))
    if len(rim_color) == 3: rim_color.append(1.0)

    prop_map = {
        "Ambient Tint": ambient_tint,
        "Overall Tint": ambient_tint,
        "Lit Tint": lit_tint,
        "Lit Brightness": lit_brightness,
        "Shadow Tint": shadow_tint,
        "Shadow Intensity": shadow_intensity,
        "Fake SSS Intensity": fake_sss_intensity,
        "Enable Rim Light": enable_rim,
        "Rim Light Color": rim_color,
        "Coverage": rim_coverage,
        "Brightness": rim_brightness,
        "Left/Right": rim_left_right,
        "Up/Down": rim_up_down,
    }

    # 1. Update in node groups definitions
    for ng in bpy.data.node_groups:
        ng_low = ng.name.lower()
        if "kythera" in ng_low or "rim light" in ng_low or "lit/shadow" in ng_low or "face shader" in ng_low:
            if hasattr(ng, "interface"):
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name in prop_map:
                        try:
                            item.default_value = prop_map[item.name]
                        except Exception:
                            pass
            elif hasattr(ng, "inputs"):
                for inp in ng.inputs:
                    if inp.name in prop_map:
                        try:
                            inp.default_value = prop_map[inp.name]
                        except Exception:
                            pass

    # 2. Update in all material nodes
    for m in bpy.data.materials:
        if m.node_tree:
            for node in m.node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree:
                    nt_low = node.node_tree.name.lower()
                    if "kythera" in nt_low or "rim light" in nt_low or "lit/shadow" in nt_low or "face shader" in nt_low:
                        for inp_name, val in prop_map.items():
                            if inp_name in node.inputs:
                                try:
                                    node.inputs[inp_name].default_value = val
                                except Exception:
                                    pass


class ZZZ_PT_Rig_Character_Settings(Panel):
    bl_label = "Character Settings"
    bl_idname = "ZZZ_PT_Rig_Character_Settings_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        # Only show when using Kythera's shader
        if getattr(context.scene, "zzz_shader_type", "KYTHERA") != "KYTHERA":
            return False
        try:
            from setup_wizard.ui.character_settings_utils import is_game_armature
            return is_game_armature(context, "ZENLESS_ZONE_ZERO")
        except Exception:
            pass
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object or context.object

        # 1. Lighting Mode / Presets
        col_light = layout.column(align=True)
        col_light.label(text="Lighting Mode:")
        col_light.prop(scene, "zzz_light_mode", text="")

        # Only show Shading & Tints when in Custom mode ("6")
        if getattr(scene, "zzz_light_mode", "0") == "6":
            # 2. Shading & Tints
            box_shading = layout.box()
            box_shading.label(text="Shading & Tints", icon="COLOR")
            col_shading = box_shading.column(align=True)
            col_shading.prop(scene, "zzz_ambient_tint", text="Ambient")
            col_shading.prop(scene, "zzz_lit_tint", text="Lit Tint")
            col_shading.prop(scene, "zzz_lit_brightness", text="Lit Brightness", slider=True)
            col_shading.prop(scene, "zzz_shadow_tint", text="Shadow Tint")
            col_shading.prop(scene, "zzz_shadow_intensity", text="Shadow Intensity", slider=True)
            col_shading.prop(scene, "zzz_fake_sss_intensity", text="Fake SSS Intensity", slider=True)

        # 3. Rim Light Settings (Separate option below lighting)
        box_rim = layout.box()
        box_rim.label(text="Rim Light", icon="LIGHT_SUN")
        box_rim.prop(scene, "zzz_enable_rim_light", text="Enable Rim Light")

        col_rim = box_rim.column(align=True)
        col_rim.active = scene.zzz_enable_rim_light
        col_rim.prop(scene, "zzz_rim_brightness", text="Brightness", slider=True)
        col_rim.prop(scene, "zzz_rim_left_right", text="Left / Right", slider=True)
        col_rim.prop(scene, "zzz_rim_up_down", text="Up / Down", slider=True)
        if getattr(scene, "zzz_light_mode", "0") == "6":
            col_rim.prop(scene, "zzz_rim_light_color", text="Color")

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




def register_zzz_properties():
    from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty

    bpy.types.Scene.zzz_light_mode = EnumProperty(
        name="Light Mode",
        description="Lighting preset mode for Kythera ZZZ shader",
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
        update=update_zzz_light_mode,
    )

    bpy.types.Scene.zzz_ambient_tint = FloatVectorProperty(
        name="Ambient Tint",
        description="Ambient color tint for Kythera ZZZ shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_lit_tint = FloatVectorProperty(
        name="Lit Tint",
        description="Lit color tint for Kythera ZZZ shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_lit_brightness = FloatProperty(
        name="Lit Brightness",
        description="Lit brightness offset for Kythera ZZZ shader",
        min=0.0,
        max=1.0,
        default=0.0,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_shadow_tint = FloatVectorProperty(
        name="Shadow Tint",
        description="Shadow color tint for Kythera ZZZ shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.65, 0.65, 0.85),
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_shadow_intensity = FloatProperty(
        name="Shadow Intensity",
        description="Shadow intensity for Kythera ZZZ shader",
        min=0.0,
        max=1.0,
        default=1.0,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_fake_sss_intensity = FloatProperty(
        name="Fake SSS Intensity",
        description="Fake SSS intensity for Kythera ZZZ shader",
        min=0.0,
        max=1.0,
        default=1.0,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_enable_rim_light = BoolProperty(
        name="Enable Rim Light",
        description="Enable or disable rim light on Kythera ZZZ shader",
        default=True,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_rim_light_color = FloatVectorProperty(
        name="Rim Light Color",
        description="Rim light color tint for Kythera ZZZ shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_rim_coverage = FloatProperty(
        name="Coverage",
        description="Rim light coverage for Kythera ZZZ shader",
        min=0.0,
        max=1.0,
        default=1.0,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_rim_brightness = FloatProperty(
        name="Brightness",
        description="Rim light brightness for Kythera ZZZ shader",
        min=0.0,
        max=1.0,
        default=1.0,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_rim_left_right = FloatProperty(
        name="Left / Right",
        description="Rim light horizontal direction offset",
        min=0.0,
        max=1.0,
        default=0.5,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )

    bpy.types.Scene.zzz_rim_up_down = FloatProperty(
        name="Up / Down",
        description="Rim light vertical direction offset",
        min=0.0,
        max=1.0,
        default=0.1,
        step=10,
        precision=1,
        update=update_zzz_kythera_props,
    )


def unregister_zzz_properties():
    props = [
        "zzz_light_mode",
        "zzz_ambient_tint",
        "zzz_lit_tint",
        "zzz_lit_brightness",
        "zzz_shadow_tint",
        "zzz_shadow_intensity",
        "zzz_fake_sss_intensity",
        "zzz_enable_rim_light",
        "zzz_rim_light_color",
        "zzz_rim_coverage",
        "zzz_rim_brightness",
        "zzz_rim_left_right",
        "zzz_rim_up_down",
    ]
    for p in props:
        if hasattr(bpy.types.Scene, p):
            delattr(bpy.types.Scene, p)

