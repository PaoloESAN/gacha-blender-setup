# Based on Blender-WuWa-Character-Setup by @fnoji and @nytsjared
# Adapted for Gacha Setup by PaoloESAN
# Licensed under GPL-3.0-or-later

import bpy
from bpy.types import Panel, UILayout

from setup_wizard.domain.game_types import GameType
from setup_wizard.ui.ui_render_checker import WutheringWavesUIRenderChecker
from setup_wizard.ui.gi_ui_setup_wizard_menu import OperatorFactory


class WW_PT_Setup_Wizard_UI_Layout(Panel, WutheringWavesUIRenderChecker):
    bl_label = "Wuthering Waves Setup Wizard"
    bl_idname = "WW_PT_Setup_Wizard_UI_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"

    def draw(self, context):
        layout = self.layout

        sub_layout = layout.box()
        run_entire_setup_column = sub_layout.column()
        OperatorFactory.create(
            run_entire_setup_column,
            "wuthering_waves.setup_wizard_ui",
            "Run Entire Setup",
            "PLAY",
            game_type=GameType.WUTHERING_WAVES.name,
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


class WW_PT_Basic_Setup_Wizard_UI_Layout(Panel, WutheringWavesUIRenderChecker):
    bl_label = "Basic Setup"
    bl_idname = "WW_PT_UI_Basic_Setup_Layout"
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
            "wuthering_waves.set_up_character",
            "Set Up Character",
            icon="OUTLINER_OB_ARMATURE",
            operator_context="INVOKE_DEFAULT",
            game_type=GameType.WUTHERING_WAVES.name,
        )

        # Step 2: Set Up Materials
        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.set_up_materials",
            "Set Up Materials",
            icon="MATERIAL",
            game_type=GameType.WUTHERING_WAVES.name,
            operator_context="INVOKE_DEFAULT",
        )

        # Step 3: Setup Outlines
        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.set_up_outlines",
            "Setup Outlines",
            icon="GEOMETRY_NODES",
            game_type=GameType.WUTHERING_WAVES.name,
        )

        # Step 4: Rig Character
        OperatorFactory.create_rig_character_ui(sub_layout, game_type=GameType.WUTHERING_WAVES.name)

        # Step 5: Finish Setup
        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.finish_setup",
            "Finish Setup",
            icon="CHECKMARK",
            game_type=GameType.WUTHERING_WAVES.name,
        )


class WW_PT_Advanced_Setup_Wizard_UI_Layout(Panel, WutheringWavesUIRenderChecker):
    bl_label = "Advanced Setup"
    bl_idname = "WW_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass


class WW_PT_UI_Character_Model_Menu(Panel, WutheringWavesUIRenderChecker):
    bl_label = "1. Character Model"
    bl_parent_id = "WW_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)
        sub_layout.label(text="Import .uemodel (UEFormat) or .fbx", icon="INFO")
        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.set_up_character",
            "Import Character Model",
            "IMPORT",
            game_type=GameType.WUTHERING_WAVES.name,
            operator_context="INVOKE_DEFAULT",
        )


class WW_PT_UI_Materials_Menu(Panel, WutheringWavesUIRenderChecker):
    bl_label = "2. Materials"
    bl_parent_id = "WW_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "genshin.import_materials",
            "Import Gustling Waters Shader",
            "IMPORT",
            game_type=GameType.WUTHERING_WAVES.name,
            setup_mode="ADVANCED",
            operator_context="INVOKE_DEFAULT",
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.replace_default_materials",
            "Replace Default Materials",
            "MATERIAL",
            game_type=GameType.WUTHERING_WAVES.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.import_textures",
            "Import Character Textures",
            "TEXTURE",
            game_type=GameType.WUTHERING_WAVES.name,
            operator_context="INVOKE_DEFAULT",
        )


class WW_PT_UI_Outlines_Menu(Panel, WutheringWavesUIRenderChecker):
    bl_label = "3. Outlines"
    bl_parent_id = "WW_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.set_up_outlines",
            "Setup Outlines",
            "GEOMETRY_NODES",
            game_type=GameType.WUTHERING_WAVES.name,
        )


class WW_PT_UI_Rig_Character_Menu(Panel, WutheringWavesUIRenderChecker):
    bl_label = "4. Rig Character"
    bl_parent_id = "WW_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column()
        box = sub_layout.box()

        character_rigger_props = context.scene.character_rigger_props

        OperatorFactory.create_rig_character_ui(box, game_type=GameType.WUTHERING_WAVES.name)
        OperatorFactory.create(
            box,
            'hoyoverse.apply_hair_clothes_physics',
            'Apply Hair & Clothes Physics',
            'PHYSICS',
        )
        box.separator()
        box.operator("wuthering_waves.create_face_panel", text="Create Face Rig Panel", icon="FACE_MAPS")

        box = sub_layout.box()
        box.label(text='Settings')
        col = box.column()
        enable_physics = getattr(character_rigger_props, "enable_hair_clothes_physics", getattr(character_rigger_props, "enable_hair_dress_physics", False))
        col.prop(character_rigger_props, 'enable_hair_clothes_physics', text="Hair & Clothes Physics")
        sliders_col = col.column()
        sliders_col.active = enable_physics
        sliders_col.prop(character_rigger_props, 'hair_physics_influence', text='Hair', slider=True)
        sliders_col.prop(character_rigger_props, 'clothes_physics_influence', text='Clothes', slider=True)


class WW_PT_UI_Finish_Setup_Menu(Panel, WutheringWavesUIRenderChecker):
    bl_label = "5. Finish Setup"
    bl_parent_id = "WW_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column(align=True)

        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.setup_head_driver",
            "Set Up Head Driver & Light Direction",
            "CONSTRAINT",
            game_type=GameType.WUTHERING_WAVES.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.set_color_management_to_standard",
            "Set Color Mgmt to Standard",
            "COLOR",
            game_type=GameType.WUTHERING_WAVES.name,
        )
        OperatorFactory.create(
            sub_layout,
            "hoyoverse.set_up_screen_space_reflections",
            "Enable SSR & Shadows",
            "SCENE",
            game_type=GameType.WUTHERING_WAVES.name,
        )
        OperatorFactory.create(
            sub_layout,
            "wuthering_waves.setup_compositor_nodes",
            "Set Up Compositing Nodes",
            "NODE_COMPOSITING",
            game_type=GameType.WUTHERING_WAVES.name,
        )


class WW_PT_Rig_Character_Settings(Panel):
    bl_label = "Character Settings"
    bl_idname = "WW_PT_Rig_Character_Settings_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        try:
            from setup_wizard.ui.character_settings_utils import is_game_armature
            return is_game_armature(context, "WUTHERING_WAVES")
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

        # 1. Enable / Disable Animate Mode
        is_anim = scene.get("ww_animate_mode", False)
        layout.operator(
            "wuthering_waves.toggle_animate_mode",
            text="Disable Animate Mode" if is_anim else "Enable Animate Mode",
            icon="SHADING_TEXTURE" if is_anim else "RESTRICT_RENDER_OFF"
        )

        # 2. Lighting Mode (Own row with label on top)
        col_light = layout.column(align=True)
        col_light.label(text="Lighting Mode:")
        col_light.prop(scene, "ww_light_mode", text="")

        # Custom Colors when Lighting Mode is Custom ("6")
        if getattr(scene, "ww_light_mode", "0") == "6":
            box_col = col_light.box()
            box_col.label(text="Custom Colors", icon="COLOR")
            col_colors = box_col.column(align=True)
            col_colors.prop(scene, "ww_amb_color", text="Ambient")
            col_colors.prop(scene, "ww_light_color", text="Light")
            col_colors.prop(scene, "ww_shadow_color", text="Shadow")
            col_colors.prop(scene, "ww_rim_color", text="Rim")

        # 3. Blush
        layout.prop(scene, "ww_blush_value", text="Blush", slider=True)

        # 4. Toggle Resonator Star
        layout.operator("wuthering_waves.toggle_star_motion", text="Toggle Resonator Star", icon="LIGHT_SUN")

        # 5. Use Fresnel
        col_fresnel = layout.column(align=True)
        col_fresnel.prop(scene, "ww_use_fresnel", text="Use Fresnel")
        if getattr(scene, "ww_use_fresnel", False):
            box_fr = col_fresnel.box()
            box_fr.label(text="Fresnel Options", icon="SHADING_RENDERED")
            col_fr_props = box_fr.column(align=True)
            col_fr_props.prop(scene, "ww_fresnel_color", text="Fresnel Color")
            col_fr_props.prop(scene, "ww_fresnel_scale", text="Fresnel Scale")
            col_fr_props.prop(scene, "ww_fresnel_strength", text="Fresnel Strength")

        # 6. Alpha Transparency (Animatable checkbox)
        layout.prop(scene, "ww_alpha_transparency", text="Alpha Transparency")

        # 7. Outlines Mode (Default / Custom)
        col_ol = layout.column(align=True)
        col_ol.label(text="Outlines:")
        col_ol.prop(scene, "ww_outline_mode", text="")

        # Custom Outline Colors when Outlines Mode is Custom
        if getattr(scene, "ww_outline_mode", "DEFAULT") == "CUSTOM":
            box_ol = col_ol.box()
            box_ol.label(text="Custom Outline Colors", icon="COLOR")
            col_ol_colors = box_ol.column(align=True)
            col_ol_colors.prop(scene, "ww_outline_color_1", text="Outline Color 1")
            col_ol_colors.prop(scene, "ww_outline_color_2", text="Outline Color 2")

        # 8. Outline Thickness Slider
        layout.prop(scene, "ww_outline_thickness", text="Outline Thickness", slider=True)

        # 9. Hair & Clothes Physics
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

        # --- Other controls commented out ---
        # layout.prop(scene, "ww_metallic_value", text="Metallics", slider=True)
        # layout.prop(scene, "ww_specular_value", text="Specular", slider=True)
        # layout.prop(scene, "ww_disgust_value", text="Disgust Shadow", slider=True)
        # layout.prop(scene, "ww_catch_shadows", text="Catch Shadows")
        # layout.prop(scene, "ww_shadow_transition_range_value", text="Shadow Range", slider=True)
        # layout.prop(scene, "ww_face_shadow_softness_value", text="Face Softness", slider=True)
        # layout.prop(scene, "ww_tex_mode", text="Texture Mode")
        # layout.operator("wuthering_waves.fix_eye_uv", text="Fix Eye UV (UV2)", icon="UV")
        # layout.operator("wuthering_waves.toggle_outlines", text="Toggle Outlines", icon="MOD_EDGESPLIT")
        # layout.operator("wuthering_waves.toggle_hair_transparency", text="Toggle Hair Transparency", icon="GHOST_ENABLED")
        # layout.operator("wuthering_waves.set_performance_mode", text="Performance", icon="PREVIEW_RANGE")
        # layout.operator("wuthering_waves.set_quality_mode", text="Quality", icon="SCENE")
        # layout.operator("wuthering_waves.separate_mesh", text="Separate Mesh Parts", icon="SELECT_SUBTRACT")


classes = (
    WW_PT_Setup_Wizard_UI_Layout,
    WW_PT_Basic_Setup_Wizard_UI_Layout,
    WW_PT_Advanced_Setup_Wizard_UI_Layout,
    WW_PT_UI_Character_Model_Menu,
    WW_PT_UI_Materials_Menu,
    WW_PT_UI_Outlines_Menu,
    WW_PT_UI_Rig_Character_Menu,
    WW_PT_UI_Finish_Setup_Menu,
    WW_PT_Rig_Character_Settings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
