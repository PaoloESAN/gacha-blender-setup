# Author: michael-gh1

import os
import bpy

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

from setup_wizard.domain.game_types import GameType
from setup_wizard.import_order import NextStepInvoker
from setup_wizard.character_rig_setup.rigify_character_service import RigifyCharacterService
from setup_wizard.setup_wizard_operator_base_classes import BasicSetupUIOperator, CustomOperatorProperties


class GI_OT_RigCharacter(Operator, BasicSetupUIOperator):
    '''Sets Up Rig for Character'''
    bl_idname = 'hoyoverse.set_up_character_rig'
    bl_label = 'HoYoverse: Set Up Character Rig (UI)'


class HOYOVERSE_OT_rig_character(Operator, ImportHelper, CustomOperatorProperties):
    """Sets Up Rig for Character"""
    bl_idname = "hoyoverse.rig_character"  # important since its how we chain file dialogs
    bl_label = "Rigs Character"

    # ImportHelper mixin class uses this
    filename_ext = "*.*"

    # DEPRECATED, replaced by GI_OT_RootShape_FilePath_Setter_Operator 
    import_path: StringProperty(
        name="Path",
        description="Root_Shape .blend File",
        default="",
        subtype='DIR_PATH'
    )

    filter_glob: StringProperty(
        default="*.*",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    GAME_TYPES_FULL_SETUP_RIGGING_ENABLED = [
        GameType.GENSHIN_IMPACT.name,
        GameType.HONKAI_STAR_RAIL.name,
        GameType.ZENLESS_ZONE_ZERO.name,
        GameType.NEVERNESS_TO_EVERNESS.name,
        GameType.WUTHERING_WAVES.name,
        GameType.ARKNIGHTS_ENDFIELD.name,
    ]

    def execute(self, context):
        props = getattr(context.scene, "character_rigger_props", None)
        disable_rigging = getattr(props, "disable_rigging", getattr(context.scene, "disable_rigging", False))
        if disable_rigging:
            self.report(
                {'INFO'},
                'Rigging skipped. Disable Rigging is enabled in Setup Settings.'
            )
            self.invoke_next_step()
            super().clear_custom_properties()
            return {'FINISHED'}

        # Check if the imported model is a Weapon / Equipment (Equip_ / EquipSkin_ and not Avatar_)
        fbx_path = context.scene.get("setup_wizard_imported_fbx_path", "")
        fbx_name = os.path.basename(fbx_path) if fbx_path else ""
        is_equip = False
        if fbx_name:
            if not fbx_name.startswith("Avatar_") and (fbx_name.startswith("Equip_") or fbx_name.startswith("EquipSkin_") or "equip" in fbx_name.lower()):
                is_equip = True
        
        if not is_equip:
            objects_to_check = context.selected_objects if context.selected_objects else list(context.scene.objects)
            has_avatar = any(obj.name.startswith("Avatar_") for obj in objects_to_check)
            if not has_avatar:
                is_equip = any(
                    obj.name.startswith(("Equip_", "EquipSkin_")) or 
                    any(slot.material.name.startswith(("Equip_", "EquipSkin_")) for slot in getattr(obj, "material_slots", []) if slot.material)
                    for obj in objects_to_check
                )

        if is_equip:
            self.report(
                {'INFO'},
                'Rigging skipped for weapon / equipment (Equip_ / EquipSkin_ detected).'
            )
            self.invoke_next_step()
            super().clear_custom_properties()
            return {'FINISHED'}

        selected_armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE' and not obj.name.startswith('RIG-')]
        if not selected_armatures:
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    for mod in obj.modifiers:
                        if mod.type == 'ARMATURE' and mod.object and not mod.object.name.startswith('RIG-'):
                            selected_armatures.append(mod.object)
                            break
                    if selected_armatures:
                        break
        if not selected_armatures:
            selected_armatures = [obj for obj in context.scene.objects if obj.type == 'ARMATURE' and not obj.name.startswith('RIG-')]
        if not selected_armatures:
            selected_armatures = [obj for obj in context.scene.objects if obj.type == 'ARMATURE']

        if selected_armatures:
            arm_obj = selected_armatures[0]
            context.view_layer.objects.active = arm_obj
            arm_obj.select_set(True)
            if not self.game_type:
                b_names = set(arm_obj.data.bones.keys())
                if 'Bip001-Pelvis' in b_names or 'Bip001-Head' in b_names or 'Bip001-Spine' in b_names:
                    self.game_type = GameType.NEVERNESS_TO_EVERNESS.name
                elif 'Bip001Pelvis' in b_names or 'Bip001Head' in b_names or 'Bip001Neck' in b_names or 'Bip001LUpperArm' in b_names:
                    self.game_type = GameType.WUTHERING_WAVES.name
                elif any(k in b_names for k in ('faceLfIrisJoint', 'faceRtIrisJoint', 'browLf01Joint', 'browLineLf01Joint')) or any('actor_' in o.name.lower() or 'chr_' in o.name.lower() for o in context.scene.objects if o.type == 'MESH'):
                    self.game_type = GameType.ARKNIGHTS_ENDFIELD.name
        
        if not self.game_type:
            if getattr(context.scene, "game_type_dropdown", None):
                self.game_type = context.scene.game_type_dropdown
            else:
                self.game_type = GameType.GENSHIN_IMPACT.name

        is_full_setup = any(
            full_setup_name in (self.high_level_step_name or "").lower()
            for full_setup_name in ["setup_wizard_ui", "setup_wizard"]
        )
        is_advanced_setup = not is_full_setup
        rigging_enabled = is_advanced_setup or \
            (getattr(bpy.context.window_manager, "setup_wizard_full_run_rigging_enabled", True) and self.game_type in self.GAME_TYPES_FULL_SETUP_RIGGING_ENABLED)

        rigify_installed = any('rigify' in k.lower() for k in bpy.context.preferences.addons.keys())
        expy_kit_installed = any('expy' in k.lower() for k in bpy.context.preferences.addons.keys())

        if not rigging_enabled:
            self.report(
                {'WARNING'},
                'Rigging skipped. Rigging not enabled on Run Entire Setup.'
            )
            self.invoke_next_step()
            return {'FINISHED'}

        if self.game_type in (GameType.WUTHERING_WAVES.name, GameType.NEVERNESS_TO_EVERNESS.name):
            if not rigify_installed:
                self.report(
                    {'WARNING'},
                    'Rigging skipped. Rigify add-on is required.'
                )
                self.invoke_next_step()
                return {'FINISHED'}
        else:
            if not expy_kit_installed or not rigify_installed:
                self.report(
                    {'WARNING'},
                    'Rigging skipped. ExpyKit and Rigify are required.\n'
                    f'ExpyKit: {"Installed" if expy_kit_installed else "Missing"}\n'
                    f'Rigify: {"Installed" if rigify_installed else "Missing"}'
                )
                self.invoke_next_step()
                return {'FINISHED'}

        try:
            rigify_character_service = RigifyCharacterService(self.game_type, self, context)
            rigify_character_service.rig_character()
        except Exception as ex:
            if self.game_type == GameType.ZENLESS_ZONE_ZERO.name:
                print(f"[ZZZ Rigging Notice] Rigging skipped or encountered non-fatal issue: {ex}")
                self.report({'WARNING'}, f'ZZZ Rigging notice: {ex}')
            else:
                raise ex
        finally:
            self.invoke_next_step()
            super().clear_custom_properties()
        return {'FINISHED'}

    def invoke_next_step(self):
        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx, 
                self.invoker_type, 
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )

GI_OT_CharacterRiggerOperator = HOYOVERSE_OT_rig_character


class ZZZ_OT_FixBoneChains(Operator):
    '''Fix selected bone chains (tails) parenting and lengths'''
    bl_idname = 'zenless_zone_zero.fix_bone_chains'
    bl_label = 'ZZZ: Fix Selected Bone Chains (Tails)'
    bl_description = "Fix parenting and lengths for selected bone chains (e.g. tails)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object is not an Armature")
            return {'CANCELLED'}

        original_mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')

        selected_bones = [bone.name for bone in context.selected_bones]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            bpy.ops.object.mode_set(mode=original_mode)
            return {'CANCELLED'}

        sb = sorted(selected_bones)
        armature = obj.data
        eb = armature.edit_bones

        def attach(foot, toe):
            eb[foot].tail.x = eb[toe].head.x
            eb[foot].tail.y = eb[toe].head.y
            eb[foot].tail.z = eb[toe].head.z

        groups = {}
        for name in sb:
            key = name[:-2]
            groups.setdefault(key, []).append(name)

        for key, group_bones in groups.items():
            if len(group_bones) < 2:
                continue
            for b in range(1, len(group_bones) + 1):
                if b == len(group_bones):
                    if len(group_bones) >= 2:
                        eb[group_bones[b-1]].length = eb[group_bones[b-2]].length + 0.1
                else:
                    bone_name = group_bones[b]
                    parent_name = group_bones[b-1]
                    eb[bone_name].parent = eb[parent_name]
                    attach(parent_name, bone_name)

        bpy.ops.object.mode_set(mode=original_mode)
        self.report({'INFO'}, "Successfully fixed selected bone chains")
        return {'FINISHED'}


def write_physics_log_datablock(log_lines):
    try:
        tb = bpy.data.texts.get("PHYSICS_LOG") or bpy.data.texts.new("PHYSICS_LOG")
        tb.clear()
        tb.write("\n".join(log_lines))
    except Exception as e:
        print(f"[GACHA SETUP LOG] Could not write text datablock: {e}")


def _apply_hair_clothes_physics_impl(self, context):
    log_lines = []
    def log(msg):
        print(f"[GACHA SETUP LOG] {msg}")
        log_lines.append(str(msg))

    log("=======================================================")
    log(">>> Button 'Apply Hair & Clothes Physics' CLICKED!")
    act = context.active_object
    log(f"Active object in context: {act.name if act else 'None'} ({act.type if act else 'None'})")
    log(f"Selected objects: {[o.name for o in context.selected_objects]}")

    from setup_wizard.character_rig_setup.rig_ui_utils import apply_hair_and_clothes_physics, find_target_armature
    armature = find_target_armature(context)
    log(f"Target armature resolved: {armature.name if armature else 'None'}")

    if not armature:
        log("ERROR: No active or selected character armature found in scene!")
        write_physics_log_datablock(log_lines)
        self.report({'ERROR'}, "No active or selected character armature found")
        return {'CANCELLED'}

    hair_inf = getattr(context.scene, "gi_hair_physics_influence", None)
    if hair_inf is None and hasattr(context.scene, "character_rigger_props"):
        hair_inf = getattr(context.scene.character_rigger_props, "hair_physics_influence", 0.7)
    if hair_inf is None:
        hair_inf = 0.7

    clothes_inf = getattr(context.scene, "gi_clothes_physics_influence", None)
    if clothes_inf is None and hasattr(context.scene, "character_rigger_props"):
        clothes_inf = getattr(context.scene.character_rigger_props, "clothes_physics_influence", getattr(context.scene.character_rigger_props, "dress_physics_influence", 0.4))
    if clothes_inf is None:
        clothes_inf = 0.4

    log(f"Settings to apply -> Hair Influence: {hair_inf:.2f}, Clothes Influence: {clothes_inf:.2f}")
    count = apply_hair_and_clothes_physics(armature, context, hair_influence=hair_inf, clothes_influence=clothes_inf)
    log(f"apply_hair_and_clothes_physics finished -> {count} bones affected.")

    log("\n--- Active Damped Track Constraints on Armature ---")
    found_constraints = 0
    if armature.pose:
        for pb in armature.pose.bones:
            for c in pb.constraints:
                if c.type == 'DAMPED_TRACK':
                    log(f"  • {pb.name:<24} | Constraint: '{c.name}' | Target: {c.subtarget} | Inf: {c.influence:.2f}")
                    found_constraints += 1
    log(f"Total Damped Track constraints active: {found_constraints}")
    log("=======================================================")

    write_physics_log_datablock(log_lines)

    if count > 0:
        self.report({'INFO'}, f"Applied Hair & Clothes Physics ({count} bones affected)")
    else:
        self.report({'WARNING'}, "No qualifying hair or clothes bones found in the armature")
    return {'FINISHED'}


class HOYOVERSE_OT_apply_hair_clothes_physics(Operator):
    """Apply Damped Track physics to Hair (0.7) and Clothes (0.4) bone chains"""
    bl_idname = "hoyoverse.apply_hair_clothes_physics"
    bl_label = "Apply Hair & Clothes Physics"
    bl_description = "Applies Damped Track constraints to hair (influence 0.7) and clothes (influence 0.4) bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return _apply_hair_clothes_physics_impl(self, context)


class HOYOVERSE_OT_apply_hair_dress_physics(Operator):
    """Compatibility alias for apply_hair_dress_physics"""
    bl_idname = "hoyoverse.apply_hair_dress_physics"
    bl_label = "Apply Hair & Clothes Physics"
    bl_description = "Applies Damped Track constraints to hair (influence 0.7) and clothes (influence 0.4) bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return _apply_hair_clothes_physics_impl(self, context)


class HOYOVERSE_OT_toggle_weapon_hand(Operator):
    """Toggle weapon attached to hand or free in world"""
    bl_idname = "hoyoverse.toggle_weapon_hand"
    bl_label = "Poner en mano"
    bl_description = "Alterna el arma entre sujeta a la mano (1.0) o libre en el espacio (0.0)"
    bl_options = {'REGISTER', 'UNDO'}

    side: StringProperty(name="Side", default="L")
    prop_bone: StringProperty(name="Prop Bone", default="")

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            for o in getattr(context, "selected_objects", []):
                if o.type == 'ARMATURE':
                    obj = o
                    break
        if not obj or not hasattr(obj, "pose") or not obj.pose:
            self.report({'WARNING'}, "Selecciona la armadura del personaje.")
            return {'CANCELLED'}

        if self.prop_bone:
            prop_name = self.prop_bone
            side_str = "R" if ".r" in self.prop_bone.lower() else "L"
        else:
            side_str = self.side.upper()
            prop_name = f"prop.{side_str}"

        pb = obj.pose.bones.get(prop_name)
        if not pb:
            self.report({'WARNING'}, f"Hueso {prop_name} no encontrado en el rig.")
            return {'CANCELLED'}

        curr_val = pb.get("Poner en mano", 1.0)
        new_val = 0.0 if curr_val >= 0.5 else 1.0
        pb["Poner en mano"] = new_val

        # Update matching hand properties if present
        for h_name in [f"hand_ik.{side_str}", f"hand_fk.{side_str}"]:
            hpb = obj.pose.bones.get(h_name)
            if hpb and "Poner en mano" in hpb:
                hpb["Poner en mano"] = new_val

        # Update constraint influence directly and set inverse_matrix to Identity so it snaps exactly to the hand
        from mathutils import Matrix
        for c in pb.constraints:
            if c.type == 'CHILD_OF' and (c.name == "Poner en mano" or "hand" in (c.subtarget or "").lower()):
                c.inverse_matrix = Matrix.Identity(4)
                c.influence = new_val

        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)

        try:
            pb.id_properties_ui("Poner en mano").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
        except Exception:
            pass

        context.view_layer.update()
        state = "en la mano" if new_val >= 0.5 else "libre"
        self.report({'INFO'}, f"Arma {prop_name} {state} ({new_val:.1f}).")
        return {'FINISHED'}


# Compatibility aliases
GI_OT_ApplyHairClothesPhysicsOperator = HOYOVERSE_OT_apply_hair_clothes_physics
GI_OT_ApplyHairDressPhysicsOperator = HOYOVERSE_OT_apply_hair_dress_physics
GI_OT_ToggleWeaponHand = HOYOVERSE_OT_toggle_weapon_hand

