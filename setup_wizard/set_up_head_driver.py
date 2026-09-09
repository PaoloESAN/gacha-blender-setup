# Author: michael-gh1

import math
import os
import bpy
from bpy.types import Operator

from setup_wizard.import_order import NextStepInvoker
from setup_wizard.setup_wizard_operator_base_classes import CustomOperatorProperties

HEAD_DRIVER_OBJECT_NAME = "Head Driver"
HEAD_ORIGIN_OBJECT_NAME = "Head Origin"


class GI_OT_SetUpHeadDriver(Operator, CustomOperatorProperties):
    """Sets up Head Driver"""

    bl_idname = "genshin.setup_head_driver"
    bl_label = "Genshin: Setup Head Driver"

    def execute(self, context):
        # Check if weapon / equipment
        fbx_path = context.scene.get("setup_wizard_imported_fbx_path", "")
        fbx_name = os.path.basename(fbx_path) if fbx_path else ""
        is_equip = False
        if fbx_name and not fbx_name.startswith("Avatar_") and (fbx_name.startswith(("Equip_", "EquipSkin_")) or "equip" in fbx_name.lower()):
            is_equip = True
        elif not any(obj.name.startswith("Avatar_") for obj in (context.selected_objects or context.scene.objects)):
            if any(obj.name.startswith(("Equip_", "EquipSkin_")) for obj in (context.selected_objects or context.scene.objects)):
                is_equip = True

        # Try to find the correct armature
        armatures = [
            obj for obj in bpy.context.selected_objects if obj.type == "ARMATURE"
        ]
        if not armatures:
            armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]

        if is_equip or not armatures:
            self.report({"INFO"}, "Head driver skipped for weapon / equipment.")
            if self.next_step_idx:
                NextStepInvoker().invoke(
                    self.next_step_idx,
                    self.invoker_type,
                    high_level_step_name=self.high_level_step_name,
                    game_type=self.game_type,
                )
            super().clear_custom_properties()
            return {"FINISHED"}

        # Prioritize Rigify character rig (named 'rig' or containing 'rig') if present
        rigify_armatures = [a for a in armatures if a.name == "rig" or "rig" in a.name.lower()]
        armature = rigify_armatures[0] if rigify_armatures else armatures[0]
        char_name = (
            armature.name.replace("Rig", "")
            if "Rig" in armature.name
            else armature.name
        )

        head_driver_candidates = [
            f"{HEAD_DRIVER_OBJECT_NAME}_{char_name}",
            f"{HEAD_ORIGIN_OBJECT_NAME}_{char_name}",
            f"Head Direction_{char_name}",
            f"{char_name}Head Direction",
            f"{char_name} Head Direction",
            HEAD_DRIVER_OBJECT_NAME,
            HEAD_ORIGIN_OBJECT_NAME,
            "Head Direction",
            "Head Origin",
            "Head Driver",
            "head origin",
            "head driver",
        ]
        head_driver_object = None
        for cand in head_driver_candidates:
            obj = bpy.data.objects.get(cand)
            if obj:
                head_driver_object = obj
                break

        if not head_driver_object:
            # Fallback search by prefix
            for obj in bpy.data.objects:
                if obj.type == "EMPTY" and (
                    obj.name.startswith("Head Origin")
                    or obj.name.startswith("Head Driver")
                    or obj.name.startswith("Head Direction")
                ):
                    head_driver_object = obj
                    break

        if not head_driver_object:
            self.report({"ERROR"}, "Head Driver / Head Origin not found")
            return {"CANCELLED"}

        child_of_constraint = self._get_child_of_constraint(head_driver_object)
        if not child_of_constraint:
            child_of_constraint = head_driver_object.constraints.new("CHILD_OF")

        armature_bones = armature.data.bones
        head_bone_names = [
            b for b in [
                "head", "Head", "DEF-head", "DEF-spine.006", "spine.006", "Head_M", "head_M",
                "Bip001-Head", "Bip001 Head", "Bip001_Head", "Bip001Head", "Bip001 头", "頭", "头"
            ]
            if b in armature_bones
        ] or [
            bone_name
            for bone_name in armature_bones.keys()
            if "Head" in bone_name or "head" in bone_name or bone_name == "DEF-spine.006" or bone_name == "spine.006"
        ]

        if head_bone_names:
            head_bone_name = head_bone_names[0]  # expecting 1 Head bone
            saved_matrix = head_driver_object.matrix_world.copy()
            self.set_contraint_target_and_bone(
                child_of_constraint, armature, head_bone_name
            )
            self.set_inverse(head_driver_object, child_of_constraint.name)
            head_driver_object.matrix_world = saved_matrix
        else:
            self.report({"WARNING"}, "No head bone found for head-driver setup.")

        # Mover Head Direction, Lighting Panel y widgets a 'lights' solo si es ZZZ, si no a 'wgt' / 'WGTS'
        if self.game_type == "ZENLESS_ZONE_ZERO":
            self._move_head_driver_system_to_lights(head_driver_object)
        else:
            self._move_head_driver_system_to_wgt(head_driver_object)

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        else:
            try:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
            except Exception:
                pass
        return {"FINISHED"}

    def _get_child_of_constraint(self, obj):
        for constraint in obj.constraints:
            if constraint.type == "CHILD_OF":
                return constraint
        return None

    def set_contraint_target_and_bone(self, constraint, armature, bone_name):
        constraint.target = armature
        constraint.subtarget = bone_name

    def _move_head_driver_system_to_wgt(self, main_obj):
        # Prefer per-character WGTS_<Char> nested in the rig's collection (Append-safe).
        wgt_coll = None
        try:
            rig = None
            for con in getattr(main_obj, "constraints", []) or []:
                if con.type == 'CHILD_OF' and getattr(con, "target", None) is not None:
                    if getattr(con.target, "type", None) == 'ARMATURE':
                        rig = con.target
                        break
            if rig is None:
                try:
                    from setup_wizard.ui.character_settings_utils import resolve_settings_armature
                    rig = resolve_settings_armature(bpy.context)
                except Exception:
                    rig = None
            if rig is not None:
                try:
                    char_tag = rig.get("gacha_character")
                except Exception:
                    char_tag = None
                char_name = char_tag or rig.name.replace("Rig", "")
                char_coll = rig.users_collection[0] if rig.users_collection else bpy.context.scene.collection
                from setup_wizard.character_rig_setup.wgts_isolation import get_or_create_char_wgts
                wgt_coll = get_or_create_char_wgts(char_coll, char_name)
        except Exception:
            wgt_coll = None
        if wgt_coll is None:
            for c in bpy.data.collections:
                if c.name.startswith("WGTS") or c.name.lower() == "wgt":
                    wgt_coll = c
                    break
        if not wgt_coll:
            wgt_coll = bpy.data.collections.get("wgt") or bpy.data.collections.get("WGTS")
        if not wgt_coll:
            wgt_coll = bpy.data.collections.new("WGTS")
            bpy.context.scene.collection.children.link(wgt_coll)

        def get_all_children(obj):
            children = []
            for child in obj.children:
                children.append(child)
                children.extend(get_all_children(child))
            return children

        all_objects = [main_obj] + get_all_children(main_obj)
        for obj in all_objects:
            if obj.name not in wgt_coll.objects:
                wgt_coll.objects.link(obj)
            for coll in list(obj.users_collection):
                if coll != wgt_coll:
                    try:
                        coll.objects.unlink(obj)
                    except Exception:
                        pass
            try:
                obj.hide_viewport = True
                obj.hide_render = True
            except Exception:
                pass

        try:
            wgt_coll.hide_viewport = True
            wgt_coll.hide_render = True
        except Exception:
            pass

    def _move_head_driver_system_to_lights(self, main_obj=None):
        move_lighting_and_head_driver_to_lights(main_obj)

    def set_inverse(self, obj, constraint_name):
        previous_hide_viewport = getattr(obj, "hide_viewport", False)
        obj.hide_viewport = False

        changed_lcs = []
        def enable_layer_colls(lc, target_name):
            if lc.exclude:
                lc.exclude = False
                changed_lcs.append(lc)
            for child in lc.children:
                c_low = child.name.lower()
                if target_name in child.collection.objects or c_low == "wgt" or c_low.startswith(("wgts", "wgt")):
                    if child.exclude:
                        child.exclude = False
                        changed_lcs.append(child)
                    enable_layer_colls(child, target_name)

        try:
            enable_layer_colls(bpy.context.view_layer.layer_collection, obj.name)
        except Exception:
            pass

        previous_active = bpy.context.view_layer.objects.active
        previous_selected = list(bpy.context.selected_objects)

        try:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.constraint.childof_set_inverse(
                constraint=constraint_name, owner="OBJECT"
            )
        except Exception as err:
            self.report(
                {"WARNING"}, f"Could not set Child Of inverse on '{obj.name}': {err}"
            )
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for selected in previous_selected:
                    if selected and selected.name in bpy.context.view_layer.objects:
                        selected.select_set(True)
                if (
                    previous_active
                    and previous_active.name in bpy.context.view_layer.objects
                ):
                    bpy.context.view_layer.objects.active = previous_active
            except Exception:
                pass
            
            try:
                obj.hide_viewport = previous_hide_viewport
            except Exception:
                pass
            for lc in changed_lcs:
                try:
                    lc.exclude = True
                except Exception:
                    pass


class ZZZ_OT_SetUpHeadDriver(Operator, CustomOperatorProperties):
    """Sets up Head Driver specifically for Zenless Zone Zero"""

    bl_idname = "zenless_zone_zero.setup_head_driver"
    bl_label = "ZZZ: Setup Head Driver"

    def execute(self, context):
        ignore_names = ["lighting", "panel", "direction", "metarig", "wgt"]
        armatures = [
            obj for obj in bpy.context.selected_objects
            if obj.type == "ARMATURE" and not any(ign in obj.name.lower() for ign in ignore_names)
        ]
        if not armatures:
            armatures = [
                obj for obj in bpy.data.objects
                if obj.type == "ARMATURE" and not any(ign in obj.name.lower() for ign in ignore_names)
            ]
        if not armatures:
            armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE" and obj.name != "metarig"]

        if not armatures:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        rigify_armatures = [a for a in armatures if a.name == "rig" or "rig" in a.name.lower()]
        armature = rigify_armatures[0] if rigify_armatures else armatures[0]
        char_name = (
            armature.name.replace("Rig", "").replace("_UI", "")
            if "Rig" in armature.name
            else armature.name.replace("_UI", "")
        )

        head_driver_object = (
            bpy.data.objects.get(f"{HEAD_DRIVER_OBJECT_NAME}_{char_name}")
            or bpy.data.objects.get(f"{HEAD_ORIGIN_OBJECT_NAME}_{char_name}")
            or bpy.data.objects.get(f"Head Direction_{char_name}")
            or bpy.data.objects.get(f"{char_name}Head Direction")
            or bpy.data.objects.get(f"{char_name} Head Direction")
            or bpy.data.objects.get(HEAD_DRIVER_OBJECT_NAME)
            or bpy.data.objects.get(HEAD_ORIGIN_OBJECT_NAME)
            or bpy.data.objects.get("Head Direction")
        )

        if head_driver_object:
            child_of_constraint = self._get_child_of_constraint(head_driver_object)
            if child_of_constraint:
                armature_bones = armature.data.bones
                head_bone_names = [
                    b for b in ["head", "Head", "DEF-head", "DEF-spine.006"]
                    if b in armature_bones
                ] or [
                    bone_name
                    for bone_name in armature_bones.keys()
                    if "Head" in bone_name or "head" in bone_name or bone_name == "DEF-spine.006"
                ]
                if head_bone_names:
                    head_bone_name = head_bone_names[0]
                    saved_matrix = head_driver_object.matrix_world.copy()
                    self.set_contraint_target_and_bone(
                        child_of_constraint, armature, head_bone_name
                    )
                    self.set_inverse(head_driver_object, child_of_constraint.name)
                    head_driver_object.matrix_world = saved_matrix

        move_lighting_and_head_driver_to_lights(head_driver_object)

        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {"FINISHED"}

    def _get_child_of_constraint(self, obj):
        for constraint in obj.constraints:
            if constraint.type == "CHILD_OF":
                return constraint
        return None

    def set_contraint_target_and_bone(self, constraint, armature, bone_name):
        constraint.target = armature
        constraint.subtarget = bone_name

    def set_inverse(self, obj, constraint_name):
        previous_hide_viewport = getattr(obj, "hide_viewport", False)
        obj.hide_viewport = False

        # Head objects may live in an excluded WGTS_<Char>: temporarily
        # un-exclude their layer collections so the operator can evaluate
        # (same system as GI_OT_SetUpHeadDriver).
        changed_lcs = []
        def enable_layer_colls(lc, target_name):
            if lc.exclude:
                lc.exclude = False
                changed_lcs.append(lc)
            for child in lc.children:
                c_low = child.name.lower()
                if target_name in child.collection.objects or c_low == "wgt" or c_low.startswith(("wgts", "wgt")):
                    if child.exclude:
                        child.exclude = False
                        changed_lcs.append(child)
                    enable_layer_colls(child, target_name)

        try:
            enable_layer_colls(bpy.context.view_layer.layer_collection, obj.name)
        except Exception:
            pass

        previous_active = bpy.context.view_layer.objects.active
        previous_selected = list(bpy.context.selected_objects)

        try:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.constraint.childof_set_inverse(
                constraint=constraint_name, owner="OBJECT"
            )
        except Exception as err:
            self.report(
                {"WARNING"}, f"Could not set Child Of inverse on '{obj.name}': {err}"
            )
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for selected in previous_selected:
                    if selected and selected.name in bpy.context.view_layer.objects:
                        selected.select_set(True)
                if previous_active and previous_active.name in bpy.context.view_layer.objects:
                    bpy.context.view_layer.objects.active = previous_active
            except Exception:
                pass
            try:
                obj.hide_viewport = previous_hide_viewport
            except Exception:
                pass
            for lc in changed_lcs:
                try:
                    lc.exclude = True
                except Exception:
                    pass


HEAD_EMPTY_PREFIXES_LOWER = ("head origin", "head driver", "head forward", "head up", "head direction")


def _resolve_head_empty_rig(obj):
    """Owning character rig for a head-driver empty (constraint target, _Char suffix, or parent chain)."""
    try:
        seen = set()
        current = obj
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            for con in getattr(current, "constraints", []) or []:
                if con.type == 'CHILD_OF' and getattr(con, "target", None) is not None:
                    if getattr(con.target, "type", None) == 'ARMATURE':
                        return con.target
            try:
                base = current.name
            except Exception:
                base = ""
            for prefix in ("Head Origin_", "Head Driver_", "Head Forward_", "Head Up_", "Head Direction_"):
                if base.startswith(prefix):
                    char = base[len(prefix):]
                    rig = bpy.data.objects.get(f"{char}Rig") or bpy.data.objects.get(char)
                    if rig is not None and getattr(rig, "type", None) == 'ARMATURE':
                        return rig
                    break
            # Children like Head Forward_Bone inherit the rig from their parent
            # (e.g. parented under Head Origin_<Char>).
            try:
                current = getattr(current, "parent", None)
            except Exception:
                current = None
    except Exception:
        pass
    return None


def _move_head_empties_to_char_wgts(objs):
    """Moves per-character head-driver empties into their rig's WGTS_<Char> (Append-safe).

    Same system as HSR/Genshin: Head* travels with the character, only scene-global
    lighting stays in 'lights'. Returns the set of moved objects.
    """
    moved = set()
    try:
        from setup_wizard.character_rig_setup.wgts_isolation import get_or_create_char_wgts
    except Exception:
        return moved
    for obj in list(objs or []):
        try:
            o_low = obj.name.lower()
        except Exception:
            continue
        if not any(o_low.startswith(p) for p in HEAD_EMPTY_PREFIXES_LOWER):
            continue
        rig = _resolve_head_empty_rig(obj)
        if rig is None:
            continue
        try:
            char_tag = rig.get("gacha_character")
        except Exception:
            char_tag = None
        char_name = char_tag or rig.name.replace("Rig", "")
        char_coll = rig.users_collection[0] if rig.users_collection else bpy.context.scene.collection
        try:
            wgts = get_or_create_char_wgts(char_coll, char_name)
        except Exception:
            continue
        try:
            if obj.name not in wgts.objects:
                wgts.objects.link(obj)
            for coll in list(obj.users_collection):
                if coll != wgts:
                    coll.objects.unlink(obj)
            obj.hide_viewport = True
            obj.hide_render = True
            moved.add(obj)
        except Exception:
            continue
    return moved


def move_lighting_and_head_driver_to_lights(main_obj=None):
    lights_coll = bpy.data.collections.get("lights")
    if not lights_coll:
        lights_coll = bpy.data.collections.new("lights")
        bpy.context.scene.collection.children.link(lights_coll)

    def get_all_children(obj):
        children = []
        for child in obj.children:
            children.append(child)
            children.extend(get_all_children(child))
        return children

    target_objs = set()
    if main_obj:
        if "colorwheel" not in main_obj.name.lower():
            target_objs.add(main_obj)
        for child in get_all_children(main_obj):
            if "colorwheel" not in child.name.lower():
                target_objs.add(child)

    target_names = [
        "head direction", "head driver", "head origin",
        "lighting panel", "lightpanelselectorwgt", "lightpanelwgtplane"
    ]

    for obj in bpy.data.objects:
        o_lower = obj.name.lower()
        if "light direction" in o_lower or "colorwheel" in o_lower:
            continue
        for t_name in target_names:
            if t_name in o_lower:
                target_objs.add(obj)
                for child in get_all_children(obj):
                    if "light direction" not in child.name.lower() and "colorwheel" not in child.name.lower():
                        target_objs.add(child)
                break

    target_objs = {obj for obj in target_objs if "light direction" not in obj.name.lower() and "colorwheel" not in obj.name.lower()}

    # Per-character head-driver empties travel with the character (WGTS_<Char>),
    # like HSR/Genshin — only scene-global lighting stays in 'lights'.
    try:
        target_objs -= _move_head_empties_to_char_wgts(target_objs)
    except Exception:
        pass

    for obj in target_objs:
        if obj.name not in lights_coll.objects:
            lights_coll.objects.link(obj)
        for coll in list(obj.users_collection):
            if coll != lights_coll:
                try:
                    coll.objects.unlink(obj)
                except Exception:
                    pass

    # Explicitly ensure NO ColorWheel meshes remain linked to lights collection
    if lights_coll:
        for obj in list(lights_coll.objects):
            if "colorwheel" in obj.name.lower():
                try:
                    lights_coll.objects.unlink(obj)
                except Exception:
                    pass


class WW_OT_SetUpHeadDriver(Operator, CustomOperatorProperties):
    """Sets up Head Driver for Wuthering Waves (following GI/ZZZ pattern)"""

    bl_idname = "wuthering_waves.setup_head_driver"
    bl_label = "Wuthering Waves: Setup Head Driver"

    def execute(self, context):
        armatures = [obj for obj in context.selected_objects if obj.type == "ARMATURE"]
        if not armatures:
            armatures = [obj for obj in context.scene.objects if obj.type == "ARMATURE"]

        if not armatures:
            self.report({"INFO"}, "No armature found to attach Head Driver.")
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
            return {"FINISHED"}

        rigify_armatures = [a for a in armatures if a.name.startswith("RIG-") or "rig" in a.name.lower()]
        armature = rigify_armatures[0] if rigify_armatures else armatures[0]

        # 1. Ensure Highlight Top / Bottom are children of Eye Highlight, not Head Origin
        eye_highlight = bpy.data.objects.get("Eye Highlight")
        if eye_highlight:
            for hl_name in ["Highlight Top", "Highlight Bottom"]:
                hl_obj = bpy.data.objects.get(hl_name)
                if hl_obj and hl_obj.parent != eye_highlight:
                    orig_mat = hl_obj.matrix_world.copy()
                    hl_obj.parent = eye_highlight
                    hl_obj.matrix_parent_inverse = eye_highlight.matrix_world.inverted()
                    hl_obj.matrix_world = orig_mat

        # 2. Setup Head Origin
        head_origin = bpy.data.objects.get("Head Origin") or bpy.data.objects.get("Head Driver") or bpy.data.objects.get("Head Controller")
        if head_origin:
            child_of_con = None
            for con in head_origin.constraints:
                if con.type == "CHILD_OF":
                    child_of_con = con
                    break
            if not child_of_con:
                child_of_con = head_origin.constraints.new("CHILD_OF")
                child_of_con.name = "Child Of"

            head_bones = ["head", "Bip001Head", "ORG-head", "DEF-head", "c_head.x", "Head"]
            matched_bone = None
            for b in head_bones:
                if b in armature.data.bones:
                    matched_bone = b
                    break
            if not matched_bone:
                for b_name in armature.data.bones.keys():
                    if "head" in b_name.lower():
                        matched_bone = b_name
                        break

            if matched_bone:
                saved_matrix = head_origin.matrix_world.copy()
                child_of_con.target = armature
                child_of_con.subtarget = matched_bone
                self.set_inverse(head_origin, child_of_con.name)
                head_origin.matrix_world = saved_matrix

        # 3. Ensure Light Direction has no constraints (pure world sun direction)
        light_dir = bpy.data.objects.get("Light Direction")
        if light_dir:
            for con in list(light_dir.constraints):
                if con.type == "CHILD_OF":
                    light_dir.constraints.remove(con)

        # 4. Move Head Origin system (Head Origin, Head Forward, Head Up) to WGTS collection and deactivate/hide
        if head_origin:
            self._move_head_driver_system_to_wgt(head_origin)

        self.report({"INFO"}, "Configured Wuthering Waves Head Driver.")
        NextStepInvoker().invoke(
            self.next_step_idx,
            self.invoker_type,
            high_level_step_name=self.high_level_step_name,
            game_type=self.game_type,
        )
        return {"FINISHED"}

    def _move_head_driver_system_to_wgt(self, main_obj):
        wgt_coll = None
        for c in bpy.data.collections:
            if c.name.startswith("WGTS") or c.name.lower() == "wgt":
                wgt_coll = c
                break
        if not wgt_coll:
            wgt_coll = bpy.data.collections.get("wgt") or bpy.data.collections.get("WGTS")
        if not wgt_coll:
            wgt_coll = bpy.data.collections.new("WGTS")
            bpy.context.scene.collection.children.link(wgt_coll)

        def get_all_children(obj):
            children = []
            for child in obj.children:
                children.append(child)
                children.extend(get_all_children(child))
            return children

        all_objects = [main_obj] + get_all_children(main_obj)
        for obj in all_objects:
            if obj.name not in wgt_coll.objects:
                wgt_coll.objects.link(obj)
            for coll in list(obj.users_collection):
                if coll != wgt_coll:
                    try:
                        coll.objects.unlink(obj)
                    except Exception:
                        pass
            try:
                obj.hide_viewport = True
                obj.hide_render = True
            except Exception:
                pass

        try:
            wgt_coll.hide_viewport = True
            wgt_coll.hide_render = True
        except Exception:
            pass

    def set_inverse(self, obj, constraint_name):
        previous_hide_viewport = getattr(obj, "hide_viewport", False)
        obj.hide_viewport = False

        previous_active = bpy.context.view_layer.objects.active
        previous_selected = list(bpy.context.selected_objects)

        try:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.constraint.childof_set_inverse(
                constraint=constraint_name, owner="OBJECT"
            )
        except Exception as err:
            self.report(
                {"WARNING"}, f"Could not set Child Of inverse on '{obj.name}': {err}"
            )
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for selected in previous_selected:
                    if selected and selected.name in bpy.context.view_layer.objects:
                        selected.select_set(True)
                if previous_active and previous_active.name in bpy.context.view_layer.objects:
                    bpy.context.view_layer.objects.active = previous_active
            except Exception:
                pass
            try:
                obj.hide_viewport = previous_hide_viewport
            except Exception:
                pass


class AKE_OT_SetUpHeadDriver(Operator, CustomOperatorProperties):
    """Sets up Head Driver (HC, HF, HR) for Arknights: Endfield"""

    bl_idname = "arknights_endfield.setup_head_driver"
    bl_label = "Arknights Endfield: Setup Head Driver"

    def execute(self, context):
        setup_ake_head_driver_system(context)
        self.report({"INFO"}, "Configured Arknights Endfield Head Driver (HC, HF, HR).")
        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        super().clear_custom_properties()
        return {"FINISHED"}


def setup_ake_head_driver_system(context=None):
    if context is None:
        context = bpy.context

    arm = next((o for o in context.selected_objects if o.type == 'ARMATURE'), None)
    if not arm:
        arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)

    if not arm:
        return

    head_bone_name = next((b.name for b in arm.data.bones if any(k in b.name.lower() for k in ['bip001_head', 'bip001 head', 'head', 'head_m'])), None)
    if not head_bone_name:
        return

    head_pose_bone = arm.pose.bones.get(head_bone_name)
    if not head_pose_bone:
        return

    head_world_pos = arm.matrix_world @ head_pose_bone.head

    hc = bpy.data.objects.get('HC')
    hf = bpy.data.objects.get('HF')
    hr = bpy.data.objects.get('HR')

    if not hc:
        return

    # The .blend already carries the correct HC/HF/HR rotation/scale/offsets:
    # do not touch anything, only move the system to the head preserving transforms.
    context.view_layer.update()
    hc_world_before = hc.matrix_world.copy()
    children_world = {}
    for obj in [hf, hr]:
        if obj:
            children_world[obj.name] = obj.matrix_world.copy()

    hc.parent = None
    for c in list(hc.constraints):
        hc.constraints.remove(c)

    # 2. Move HC to the head center and apply rotation (90, -90, -180) deg.
    # HF/HR inherit it as children: their local transforms are left untouched.
    hc.matrix_world = hc_world_before
    hc.matrix_world.translation = head_world_pos
    hc.rotation_mode = 'XYZ'
    hc.rotation_euler = (
        math.radians(90.0),
        math.radians(-90.0),
        math.radians(-180.0),
    )
    context.view_layer.update()

    # 3. Ensure parenting to HC without altering .blend transforms
    for obj in [hf, hr]:
        if not obj:
            continue
        if obj.parent != hc:
            obj.parent = hc
            obj.matrix_world = children_world[obj.name]
    context.view_layer.update()

    # 4. Add Child Of constraint to HC and call childof_set_inverse
    con = hc.constraints.new('CHILD_OF')
    con.target = arm
    con.subtarget = head_bone_name

    prev_active = context.view_layer.objects.active
    prev_selected = list(context.selected_objects)

    try:
        bpy.ops.object.select_all(action='DESELECT')
        hc.select_set(True)
        context.view_layer.objects.active = hc
        bpy.ops.constraint.childof_set_inverse(constraint=con.name, owner='OBJECT')
    except Exception as e:
        print(f"[AKE SETUP] Notice setting HC Child Of inverse: {e}")
    finally:
        try:
            bpy.ops.object.select_all(action='DESELECT')
            for sel in prev_selected:
                if sel and sel.name in context.view_layer.objects:
                    sel.select_set(True)
            if prev_active and prev_active.name in context.view_layer.objects:
                context.view_layer.objects.active = prev_active
        except Exception:
            pass

    # 5. Organization: Nest Lighting collection into WGTS_Armature / WGTS and place Light with character rig
    try:
        organize_ake_lighting_collections(context, arm)
    except Exception as e_org:
        print(f"[AKE SETUP] Notice organizing Lighting and WGTS collections: {e_org}")


def organize_ake_lighting_collections(context=None, arm=None):
    if context is None:
        context = bpy.context

    light_col = bpy.data.collections.get('Lighting')
    light_obj = bpy.data.objects.get('Light')

    # 1. Resolve character armature if not provided
    if not arm:
        # Prefer Rigify rig (e.g. PelicaRig) or active armature
        armatures = [o for o in context.selected_objects if o.type == 'ARMATURE' and not any(k in o.name.lower() for k in ['facerig', 'lighting', 'metarig'])]
        if armatures:
            arm = armatures[0]
        else:
            arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.endswith('Rig') and not any(k in o.name.lower() for k in ['facerig', 'lighting', 'metarig'])), None)
        if not arm:
            arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE' and not any(k in o.name.lower() for k in ['facerig', 'lighting', 'metarig'])), None)

    # 2. Resolve character collection (e.g. Pelica)
    char_coll = None
    if arm and arm.users_collection:
        for c in arm.users_collection:
            if not c.name.startswith("WGTS") and c.name.lower() != "wgt":
                char_coll = c
                break
    if not char_coll:
        for c in bpy.data.collections:
            if c.name not in ("Collection", "Master Collection", "Scene Collection", "Lighting") and not c.name.startswith("WGTS") and c.name.lower() != "wgt":
                char_coll = c
                break
    if not char_coll:
        char_coll = context.scene.collection

    # 3. Resolve per-character WGTS collection (e.g. WGTS_Pelica) nested in char_coll.
    # Never use a global WGTS/wgt: that pulls every character's widgets on Append.
    wgts_coll = None
    if char_coll is not None and char_coll.name not in ("Collection", "Master Collection", "Scene Collection"):
        wgts_name = f"WGTS_{char_coll.name}"
        wgts_coll = bpy.data.collections.get(wgts_name)
        if not wgts_coll:
            wgts_coll = bpy.data.collections.new(wgts_name)
        if wgts_coll.name not in char_coll.children:
            try:
                char_coll.children.link(wgts_coll)
            except Exception:
                pass
        if wgts_coll.name in context.scene.collection.children:
            try:
                context.scene.collection.children.unlink(wgts_coll)
            except Exception:
                pass
        try:
            wgts_coll.hide_viewport = True
            wgts_coll.hide_select = True
            wgts_coll.hide_render = True
        except Exception:
            pass
    if wgts_coll is None:
        for c in bpy.data.collections:
            if c.name.startswith("WGTS_") or c.name.startswith("WGTS") or c.name.lower() == "wgt":
                wgts_coll = c
                break

    # 4. Move Light object directly into char_coll (alongside Rig, FaceRig, Meshes)
    if light_obj and char_coll:
        if light_obj.name not in char_coll.objects:
            char_coll.objects.link(light_obj)
        for c in list(bpy.data.collections):
            if c != char_coll and light_obj.name in c.objects:
                try:
                    c.objects.unlink(light_obj)
                except Exception:
                    pass
        if light_obj.name in context.scene.collection.objects and context.scene.collection != char_coll:
            try:
                context.scene.collection.objects.unlink(light_obj)
            except Exception:
                pass

    # 5. Nest Lighting collection inside wgts_coll
    if light_col and wgts_coll:
        if light_col.name not in wgts_coll.children:
            wgts_coll.children.link(light_col)
        for parent_c in list(bpy.data.collections):
            if parent_c != wgts_coll and light_col.name in parent_c.children:
                try:
                    parent_c.children.unlink(light_col)
                except Exception:
                    pass
        if light_col.name in context.scene.collection.children:
            try:
                context.scene.collection.children.unlink(light_col)
            except Exception:
                pass


register, unregister = bpy.utils.register_classes_factory([
    GI_OT_SetUpHeadDriver,
    ZZZ_OT_SetUpHeadDriver,
    WW_OT_SetUpHeadDriver,
    AKE_OT_SetUpHeadDriver,
])
