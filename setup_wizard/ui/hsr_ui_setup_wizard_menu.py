# Author: michael-gh1

import bpy
from bpy.types import Panel, UILayout

from setup_wizard.domain.game_types import GameType
from setup_wizard.ui.ui_render_checker import HonkaiStarRailUIRenderChecker


class HSR_PT_Setup_Wizard_UI_Layout(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Honkai Star Rail Setup Wizard"
    bl_idname = "HSR_PT_Setup_Wizard_UI_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"

    def draw(self, context):
        layout = self.layout
        window_manager = context.window_manager

        sub_layout = layout.box()
        run_entire_setup_column = sub_layout.column()
        OperatorFactory.create(
            run_entire_setup_column,
            "honkai_star_rail.setup_wizard_ui",
            "Run Entire Setup",
            "PLAY",
            game_type=GameType.HONKAI_STAR_RAIL.name,
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


class HSR_PT_Basic_Setup_Wizard_UI_Layout(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Basic Setup"
    bl_idname = "HSR_PT_UI_Basic_Setup_Layout"
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
            "honkai_star_rail.set_up_character",
            "Set Up Character",
            icon="OUTLINER_OB_ARMATURE",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )

        OperatorFactory.create(
            sub_layout,
            "honkai_star_rail.set_up_materials",
            "Set Up Materials",
            icon="MATERIAL",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        if bpy.app.version >= (3, 3, 0):
            OperatorFactory.create(
                sub_layout,
                "honkai_star_rail.set_up_outlines",
                "Set Up Outlines",
                icon="GEOMETRY_NODES",
                game_type=GameType.HONKAI_STAR_RAIL.name,
            )
        else:
            layout.label(text="(Outlines Disabled < v3.3.0)")
        OperatorFactory.create(
            sub_layout,
            "genshin.fix_transformations",
            "Fix Transformations",
            "OBJECT_DATA",
        )

        OperatorFactory.create_rig_character_ui(sub_layout)

        OperatorFactory.create(
            sub_layout,
            "honkai_star_rail.finish_setup",
            "Finish Setup",
            icon="CHECKMARK",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )


class HSR_PT_Advanced_Setup_Wizard_UI_Layout(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Advanced Setup"
    bl_idname = "HSR_PT_UI_Advanced_Setup_Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Character Setup Wizard"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout


class HSR_PT_UI_Character_Model_Menu(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Set Up Character Menu"
    bl_idname = "HSR_PT_UI_Character_Model_Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "HSR_PT_UI_Advanced_Setup_Layout"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.box()

        import_character_model_column = sub_layout.column()
        OperatorFactory.create(
            import_character_model_column,
            "genshin.import_model",
            "Import Character Model",
            "OUTLINER_OB_ARMATURE",
        )

        OperatorFactory.create(
            sub_layout, "genshin.delete_empties", "Delete Empties", "TRASH"
        )
        OperatorFactory.create(
            sub_layout, "genshin.reorient_bones", "Fix Orientation", "BONE_DATA"
        )


class HSR_PT_UI_Materials_Menu(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Set Up Materials Menu"
    bl_idname = "HSR_PT_UI_Materials_Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "HSR_PT_UI_Advanced_Setup_Layout"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column()

        OperatorFactory.create(
            sub_layout,
            "genshin.import_materials",
            "Import HSR Materials",
            "MATERIAL",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.replace_default_materials",
            "Replace Default Materials",
            "ARROW_LEFTRIGHT",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.import_textures",
            "Import Character Textures",
            "TEXTURE",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )


class HSR_PT_UI_Outlines_Menu(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Set Up Outlines Menu"
    bl_idname = "HSR_PT_UI_Outlines_Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "HSR_PT_UI_Advanced_Setup_Layout"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column()
        scene = context.scene

        if bpy.app.version >= (3, 3, 0):
            OperatorFactory.create(
                sub_layout,
                "genshin.import_outlines",
                "Import Outlines",
                "FILE_FOLDER",
                game_type=GameType.HONKAI_STAR_RAIL.name,
            )
            OperatorFactory.create(
                sub_layout,
                "genshin.setup_geometry_nodes",
                "Set Up Geometry Nodes",
                "GEOMETRY_NODES",
                game_type=GameType.HONKAI_STAR_RAIL.name,
            )
            OperatorFactory.create(
                sub_layout,
                "genshin.import_outline_lightmaps",
                "Import Outline Lightmaps",
                "FILE_FOLDER",
                game_type=GameType.HONKAI_STAR_RAIL.name,
            )

            sub_layout = layout.box()
            sub_layout.prop_search(
                scene,
                "setup_wizard_material_for_material_data_import",
                bpy.data,
                "materials",
            )
            sub_layout.prop_search(
                scene,
                "setup_wizard_outlines_material_for_material_data_import",
                bpy.data,
                "materials",
            )
            OperatorFactory.create(
                sub_layout,
                "genshin.import_material_data",
                "Import Material Data",
                "FILE",
                game_type=GameType.HONKAI_STAR_RAIL.name,
                setup_mode="ADVANCED",
            )
        else:
            layout.label(text="(Outlines Disabled < v3.3.0)")


class HSR_PT_UI_Finish_Setup_Menu(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Finish Setup Menu"
    bl_idname = "HSR_PT_UI_Misc_Setup_Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "HSR_PT_UI_Advanced_Setup_Layout"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column()

        OperatorFactory.create(
            sub_layout, "genshin.setup_head_driver", "Set Up Head Driver", "CONSTRAINT"
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.set_color_management_to_standard",
            "Set Color Mgmt to Standard",
            "SCENE",
        )
        OperatorFactory.create(
            sub_layout,
            "hoyoverse.set_up_screen_space_reflections",
            "Enable SSR",
            "SCENE",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        OperatorFactory.create(
            sub_layout,
            "hoyoverse.vertex_paint_face_see_through_effect",
            "Vertex Paint Face",
            "VPAINT_HLT",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.delete_specific_objects",
            "Clean Up Extra Meshes",
            "TRASH",
        )
        OperatorFactory.create(
            sub_layout,
            "hoyoverse.rename_shader_materials",
            "Rename Shader Materials",
            "GREASEPENCIL",
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        OperatorFactory.create(
            sub_layout,
            "genshin.set_up_armtwist_bone_constraints",
            "Set Up ArmTwist Bone Constraints",
            "CONSTRAINT_BONE",
        )


class HSR_PT_UI_Character_Rig_Setup_Menu(Panel, HonkaiStarRailUIRenderChecker):
    bl_label = "Character Rig Menu"
    bl_idname = "HSR_PT_Rigify_Setup_Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "HSR_PT_UI_Advanced_Setup_Layout"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sub_layout = layout.column()
        box = sub_layout.box()

        character_rigger_props = context.scene.character_rigger_props

        OperatorFactory.create_rig_character_ui(box)
        OperatorFactory.create(
            box,
            "hoyoverse.apply_hair_clothes_physics",
            "Apply Hair & Clothes Physics",
            "PHYSICS",
        )

        box = sub_layout.box()
        box.label(text="Settings")

        col = box.column()
        OperatorFactory.create(
            col,
            "hoyoverse.rootshape_filepath_setter",
            "Override RootShape Filepath",
            "FILE_FOLDER",
            game_type=GameType.HONKAI_STAR_RAIL.name,
            operator_context="INVOKE_DEFAULT",
        )
        col = box.column()
        col.prop(character_rigger_props, "allow_arm_ik_stretch")
        col.prop(character_rigger_props, "allow_leg_ik_stretch")
        col.prop(character_rigger_props, "use_arm_ik_poles")
        col.prop(character_rigger_props, "use_leg_ik_poles")
        col.prop(character_rigger_props, "add_children_of_constraints")
        col.prop(character_rigger_props, "use_head_tracker")
        enable_physics = getattr(character_rigger_props, "enable_hair_clothes_physics", getattr(character_rigger_props, "enable_hair_dress_physics", False))
        col.prop(character_rigger_props, "enable_hair_clothes_physics", text="Hair & Clothes Physics")
        sliders_col = col.column()
        sliders_col.active = enable_physics
        sliders_col.prop(character_rigger_props, "hair_physics_influence", text="Hair", slider=True)
        sliders_col.prop(character_rigger_props, "clothes_physics_influence", text="Clothes", slider=True)


# class HSR_PT_UI_Compositing_Panel_Post_Processing_UI_Layout(Panel, HonkaiStarRailUIRenderChecker):
#     bl_label = "Compositing Setup Wizard"
#     bl_idname = "HSR_PT_Custom_Compositing_Node_UI_Layout"
#     bl_space_type = "NODE_EDITOR"
#     bl_region_type = "UI"
#     bl_category = "HSR - Setup Wizard"

#     def draw(self, context):
#         layout = self.layout
#         row = layout.row()
#         sub_layout = layout.box()
#         window_manager = context.window_manager

#         row.prop(window_manager, 'cache_enabled')
#         OperatorFactory.create(
#             row,
#             'genshin.clear_cache_operator',
#             'Clear Cache',
#             'TRASH',
#             game_type=GameType.HONKAI_STAR_RAIL.name,
#         )
#         OperatorFactory.create(
#             sub_layout,
#             'genshin.change_bpy_context',
#             'Enable Use Nodes',
#             'CHECKMARK',
#             bpy_context_attr='scene.use_nodes',
#             bpy_context_value_bool=True
#         )
#         OperatorFactory.create(
#             sub_layout,
#             'hoyoverse.custom_composite_node_setup',
#             'Set Up Compositing Node',
#             'PLAY'
#         )


"""
    This factory is intended to help create a UI element's operator (or the action it takes) when pressed.
    While it currently doesn't do anything too grand, it may provide future flexibility.
"""


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
        ui_object = ui_object.operator(
            operator=operator,
            text=text,
            icon=icon,
        )

        for key, value in kwargs.items():
            setattr(ui_object, key, value)

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
            game_type=GameType.HONKAI_STAR_RAIL.name,
        )
        if not column.enabled:
            column = ui_object.column()
            if not expy_kit_installed:
                column.label(text="ExpyKit required", icon="ERROR")
            if not rigify_installed:
                column.label(text="Rigify required", icon="ERROR")


HSR_LIGHT_PRESETS = {
    "0": { # Default
        "ambient": (1.0, 1.0, 1.0),
        "lit": (1.0, 1.0, 1.0),
        "shadow": (1.0, 1.0, 1.0),
        "sharp_lit": (1.0, 1.0, 1.0),
        "sharp_shadow": (1.0, 1.0, 1.0),
    },
    "1": { # Sunrise
        "ambient": (0.95, 0.85, 0.8),
        "lit": (1.0, 0.88, 0.75),
        "shadow": (0.65, 0.65, 0.85),
        "sharp_lit": (1.0, 0.9, 0.8),
        "sharp_shadow": (0.6, 0.6, 0.8),
    },
    "2": { # Day
        "ambient": (1.0, 1.0, 1.0),
        "lit": (1.0, 1.0, 1.0),
        "shadow": (1.0, 1.0, 1.0),
        "sharp_lit": (1.0, 1.0, 1.0),
        "sharp_shadow": (1.0, 1.0, 1.0),
    },
    "3": { # Sunset
        "ambient": (0.9, 0.75, 0.7),
        "lit": (1.0, 0.65, 0.45),
        "shadow": (0.5, 0.45, 0.7),
        "sharp_lit": (1.0, 0.7, 0.5),
        "sharp_shadow": (0.45, 0.4, 0.65),
    },
    "4": { # Night
        "ambient": (0.4, 0.45, 0.6),
        "lit": (0.6, 0.7, 0.9),
        "shadow": (0.25, 0.3, 0.5),
        "sharp_lit": (0.65, 0.75, 0.95),
        "sharp_shadow": (0.2, 0.25, 0.45),
    },
    "5": { # Rainy
        "ambient": (0.6, 0.65, 0.7),
        "lit": (0.75, 0.8, 0.85),
        "shadow": (0.45, 0.5, 0.6),
        "sharp_lit": (0.8, 0.85, 0.9),
        "sharp_shadow": (0.4, 0.45, 0.55),
    },
}

_is_updating_hsr_props = False

def update_hsr_light_mode(self, context=None):
    global _is_updating_hsr_props
    if _is_updating_hsr_props:
        return
    mode = getattr(self, "hsr_light_mode", "0")
    if mode in HSR_LIGHT_PRESETS:
        preset = HSR_LIGHT_PRESETS[mode]
        _is_updating_hsr_props = True
        try:
            self.hsr_amb_color = preset["ambient"]
            self.hsr_lit_color = preset["lit"]
            self.hsr_shadow_color = preset["shadow"]
            self.hsr_sharp_lit_color = preset["sharp_lit"]
            self.hsr_sharp_shadow_color = preset["sharp_shadow"]
        finally:
            _is_updating_hsr_props = False
    update_hsr_stellartoon_props(self, context)


def update_hsr_stellartoon_props(self, context=None):
    global _is_updating_hsr_props
    if _is_updating_hsr_props:
        return
    scene = bpy.context.scene if context is None else getattr(context, "scene", bpy.context.scene)
    if not scene:
        return

    _is_updating_hsr_props = True
    try:
        # Snap float sliders to 1 decimal place (steps of 0.1) and clamp near-zero
        raw_cheek = getattr(scene, "hsr_exp_cheek", 0.0)
        raw_shy = getattr(scene, "hsr_exp_shy", 0.0)
        raw_shadow = getattr(scene, "hsr_exp_shadow", 0.0)

        exp_cheek = 0.0 if raw_cheek < 0.05 else round(raw_cheek, 1)
        exp_shy = 0.0 if raw_shy < 0.05 else round(raw_shy, 1)
        exp_shadow = 0.0 if raw_shadow < 0.05 else round(raw_shadow, 1)
        
        if scene.hsr_exp_cheek != exp_cheek:
            scene.hsr_exp_cheek = exp_cheek
        if scene.hsr_exp_shy != exp_shy:
            scene.hsr_exp_shy = exp_shy
        if scene.hsr_exp_shadow != exp_shadow:
            scene.hsr_exp_shadow = exp_shadow
    finally:
        _is_updating_hsr_props = False

    eye_cant_tint = 1.0 if getattr(scene, "hsr_eye_cant_be_tinted", False) else 0.0

    amb_color = list(getattr(scene, "hsr_amb_color", (1.0, 1.0, 1.0)))
    if len(amb_color) == 3: amb_color.append(1.0)
    
    lit_color = list(getattr(scene, "hsr_lit_color", (1.0, 1.0, 1.0)))
    if len(lit_color) == 3: lit_color.append(1.0)
    
    shadow_color = list(getattr(scene, "hsr_shadow_color", (1.0, 1.0, 1.0)))
    if len(shadow_color) == 3: shadow_color.append(1.0)
    
    sharp_lit = list(getattr(scene, "hsr_sharp_lit_color", (1.0, 1.0, 1.0)))
    if len(sharp_lit) == 3: sharp_lit.append(1.0)
    
    sharp_shadow = list(getattr(scene, "hsr_sharp_shadow_color", (1.0, 1.0, 1.0)))
    if len(sharp_shadow) == 3: sharp_shadow.append(1.0)

    prop_map = {
        "Expression Cheek Intensity": exp_cheek,
        "Expression Shy Intensity": exp_shy,
        "Expression Shadow Intensity": exp_shadow,
        "Eye Can't Be Tinted?": eye_cant_tint,
        "Custom Ambient Color": amb_color,
        "Custom Lit Color": lit_color,
        "Custom Shadow Color": shadow_color,
        "Custom Sharp Lit Color": sharp_lit,
        "Custom Sharp Shadow Color": sharp_shadow,
    }

    # 1. Update inside GlobalProperties node group (both its internal nodes and interface)
    gp_group = bpy.data.node_groups.get("GlobalProperties")
    if gp_group:
        if hasattr(gp_group, "nodes"):
            for node in gp_group.nodes:
                for name, val in prop_map.items():
                    if name in node.inputs:
                        try:
                            node.inputs[name].default_value = val
                        except Exception:
                            pass
        if hasattr(gp_group, "interface"):
            for item in gp_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.name in prop_map:
                    try:
                        item.default_value = prop_map[item.name]
                    except Exception:
                        pass

    # 2. Update in all node groups and materials
    def apply_props_to_container(container):
        if not container or not hasattr(container, "nodes"):
            return
        for node in container.nodes:
            if node.type == 'GROUP' and node.node_tree:
                nt_name = node.node_tree.name
                if "GlobalProperties" in nt_name or "StellarToon" in nt_name:
                    for name, val in prop_map.items():
                        if name in node.inputs:
                            try:
                                node.inputs[name].default_value = val
                            except Exception:
                                pass

    for ng in bpy.data.node_groups:
        apply_props_to_container(ng)

    for mat in bpy.data.materials:
        if mat.node_tree:
            apply_props_to_container(mat.node_tree)


class HSR_PT_Rig_Character_Settings(Panel):
    bl_label = "Character Settings"
    bl_idname = "HSR_PT_Rig_Character_Settings_Main"
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
            is_hsr_mesh = obj.type == 'MESH' and any(s.material and ("stellartoon" in s.material.name.lower() or "hsr" in s.material.name.lower()) for s in obj.material_slots)
            if not is_hsr_mesh:
                return False

        if getattr(context.scene, "game_type_dropdown", None) == GameType.HONKAI_STAR_RAIL.name:
            return True

        if any("stellartoon" in m.name.lower() or "hsr" in m.name.lower() for m in bpy.data.materials):
            return True

        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 1. Lighting Mode / Presets
        col_light = layout.column(align=True)
        col_light.label(text="Lighting Mode:")
        col_light.prop(scene, "hsr_light_mode", text="")

        # 2. Custom Colors (Shown ONLY when in Custom mode "6")
        if getattr(scene, "hsr_light_mode", "0") == "6":
            box_col = col_light.box()
            box_col.label(text="Custom Colors", icon="COLOR")
            col_colors = box_col.column(align=True)
            col_colors.prop(scene, "hsr_amb_color", text="Ambient")
            col_colors.prop(scene, "hsr_lit_color", text="Lit")
            col_colors.prop(scene, "hsr_shadow_color", text="Shadow")
            col_colors.prop(scene, "hsr_sharp_lit_color", text="Sharp Lit")
            col_colors.prop(scene, "hsr_sharp_shadow_color", text="Sharp Shadow")

        # 3. Expressions (3 sliders)
        box_exp = layout.box()
        box_exp.label(text="Expressions", icon="COMMUNITY")
        col_exp = box_exp.column(align=True)
        col_exp.prop(scene, "hsr_exp_cheek", text="Cheek", slider=True)
        col_exp.prop(scene, "hsr_exp_shy", text="Shy", slider=True)
        col_exp.prop(scene, "hsr_exp_shadow", text="Shadow", slider=True)

        # 4. Eye Can't Be Tinted?
        layout.prop(scene, "hsr_eye_cant_be_tinted", text="Eye Can't Be Tinted?")

        # 5. Hair & Clothes Physics
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


def register_hsr_properties():
    from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty

    bpy.types.Scene.hsr_light_mode = EnumProperty(
        name="Light Mode",
        description="Lighting preset mode for Honkai Star Rail StellarToon shader",
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
        update=update_hsr_light_mode,
    )

    bpy.types.Scene.hsr_exp_cheek = FloatProperty(
        name="Expression Cheek Intensity",
        description="Expression cheek intensity",
        min=0.0,
        max=1.0,
        default=0.0,
        step=10,
        precision=1,
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_exp_shy = FloatProperty(
        name="Expression Shy Intensity",
        description="Expression shy intensity",
        min=0.0,
        max=1.0,
        default=0.0,
        step=10,
        precision=1,
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_exp_shadow = FloatProperty(
        name="Expression Shadow Intensity",
        description="Expression shadow intensity",
        min=0.0,
        max=1.0,
        default=0.0,
        step=10,
        precision=1,
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_eye_cant_be_tinted = BoolProperty(
        name="Eye Can't Be Tinted?",
        description="Prevent eyes from being affected by lighting tints",
        default=False,
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_amb_color = FloatVectorProperty(
        name="Custom Ambient Color",
        description="Custom ambient color for StellarToon shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_lit_color = FloatVectorProperty(
        name="Custom Lit Color",
        description="Custom lit color for StellarToon shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_shadow_color = FloatVectorProperty(
        name="Custom Shadow Color",
        description="Custom shadow color for StellarToon shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_sharp_lit_color = FloatVectorProperty(
        name="Custom Sharp Lit Color",
        description="Custom sharp lit color for StellarToon shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_hsr_stellartoon_props,
    )

    bpy.types.Scene.hsr_sharp_shadow_color = FloatVectorProperty(
        name="Custom Sharp Shadow Color",
        description="Custom sharp shadow color for StellarToon shader",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0),
        update=update_hsr_stellartoon_props,
    )


def unregister_hsr_properties():
    props = [
        "hsr_light_mode",
        "hsr_exp_cheek",
        "hsr_exp_shy",
        "hsr_exp_shadow",
        "hsr_eye_cant_be_tinted",
        "hsr_amb_color",
        "hsr_lit_color",
        "hsr_shadow_color",
        "hsr_sharp_lit_color",
        "hsr_sharp_shadow_color",
    ]
    for p in props:
        if hasattr(bpy.types.Scene, p):
            delattr(bpy.types.Scene, p)

