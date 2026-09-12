# Author: michael-gh1

# Kudos to M4urlcl0 for bringing up adding the UV map (UV1) and
# the armature bone settings when importing the FBX model

import os
import math
import pathlib

import bpy
from mathutils import Vector
from bpy.props import StringProperty
from bpy.types import Operator

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper

from setup_wizard.domain.game_types import GameType
from setup_wizard.import_order import (
    CHARACTER_MODEL_FOLDER_FILE_PATH,
    NEVERNESS_TO_EVERNESS_ROOT_FOLDER_FILE_PATH,
    NEVERNESS_TO_EVERNESS_SHADER_FILE_PATH,
    WUTHERING_WAVES_ROOT_FOLDER_FILE_PATH,
    WUTHERING_WAVES_SHADER_FILE_PATH,
    NextStepInvoker,
    cache_using_cache_key,
    get_cache,
    set_active_character_directory,
)
from setup_wizard.setup_wizard_operator_base_classes import (
    BasicSetupUIOperator,
    CustomOperatorProperties,
)
from setup_wizard.utils import material_utils

SHADER_COLOR_ATTRIBUTE_NAME = "Col"

# Session variable to track if character was imported via the automatic wizard flow in this session
IMPORTED_VIA_WIZARD = False


def is_rigging_disabled(context=None):
    """
    Checks if 'Disable Rigging' is enabled in the setup wizard settings.
    When True, the original FBX/armature structure (rolls, tails, rest pose)
    is preserved intact for animation compatibility.
    """
    if context is None:
        context = bpy.context
    scene = getattr(context, "scene", None)
    if not scene:
        return False
    props = getattr(scene, "character_rigger_props", None)
    return getattr(props, "disable_rigging", getattr(scene, "disable_rigging", False))


def _execute_fbx_import(filepath):
    """
    Executes FBX import using the modern Blender C++ importer (bpy.ops.wm.fbx_import) with default options
    as requested by the user, with fallback to legacy import_scene.fbx if wm.fbx_import is not available.
    """
    if hasattr(bpy.ops.wm, "fbx_import"):
        try:
            bpy.ops.wm.fbx_import(
                filepath=filepath,
                global_scale=1.0,
                mtl_name_collision_mode='MAKE_UNIQUE',
                import_colors='SRGB',
                use_custom_normals=True,
                use_custom_props=True,
                use_custom_props_enum_as_string=True,
                import_subdivision=False,
                ignore_leaf_bones=False,
                validate_meshes=True,
                use_anim=True,
                anim_offset=1.0,
            )
            return
        except Exception as e:
            print(f"bpy.ops.wm.fbx_import failed ({e}), falling back to import_scene.fbx")

    # Fallback for older Blender versions / legacy FBX importer
    bpy.ops.import_scene.fbx(
        filepath=filepath,
        force_connect_children=True,
        automatic_bone_orientation=True,
    )


def apply_spine_rest_pose(armature):
    """
    Selects Bip001 Spine and Bip001 Spine1 (and common variants) in pose mode,
    and applies them as rest pose to fix torso offset / separation issues.
    """
    if not armature or armature.type != 'ARMATURE':
        return

    orig_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'

    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        armature.hide_viewport = False
        armature.hide_set(False)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        target_names = {
            "bip001 spine", "bip001 spine1", "bip001 spine 1",
            "bip001-spine", "bip001-spine1", "bip001_spine", "bip001_spine1",
            "bip001 spine.001", "bip001 spine 01",
            "spine", "spine1", "spine 1", "spine.001"
        }

        selected_any = False
        if armature.pose:
            for pbone in armature.pose.bones:
                low = pbone.name.lower().strip()
                low_clean = low.replace("-", " ").replace("_", " ")
                if low in target_names or low_clean in target_names or ("spine" in low and ("1" in low or low.endswith("spine"))):
                    pbone.select = True
                    if hasattr(pbone.bone, "select"):
                        pbone.bone.select = True
                    selected_any = True

        if selected_any:
            bpy.ops.pose.armature_apply(selected=True)
    except Exception as e:
        print(f"[APPLY SPINE REST POSE] Notice: {e}")
    finally:
        try:
            bpy.ops.object.mode_set(mode=orig_mode if orig_mode in ('OBJECT', 'EDIT', 'POSE') else 'OBJECT')
        except Exception:
            pass


def clear_armature_pose(armature):
    """
    Clears all pose transformations (location, rotation, scale) for all bones in the armature.
    Also unlinks active animation actions so keyframes do not override the rest pose during rigging.
    Switches to POSE mode, selects all bones, and clears transforms to reset the pose.
    """
    if not armature or armature.type != 'ARMATURE':
        return

    # If armature has an active animation action driving the pose, unlink it (preserving it via fake user)
    # so the bones return to neutral rest pose before rigging.
    if armature.animation_data and armature.animation_data.action:
        try:
            armature.animation_data.action.use_fake_user = True
            armature.animation_data.action = None
        except Exception as e:
            print(f"[CLEAR POSE] Action notice: {e}")

    orig_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'

    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        armature.hide_viewport = False
        armature.hide_set(False)
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)

        bpy.ops.object.mode_set(mode='POSE')
        try:
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.pose.transforms_clear()
        except Exception:
            pass

        # Also reset directly on all pose bones to guarantee every bone is reset
        if armature.pose:
            for pbone in armature.pose.bones:
                pbone.location = (0.0, 0.0, 0.0)
                pbone.rotation_euler = (0.0, 0.0, 0.0)
                if hasattr(pbone, 'rotation_quaternion'):
                    pbone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
                if hasattr(pbone, 'rotation_axis_angle'):
                    pbone.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
                pbone.scale = (1.0, 1.0, 1.0)
    except Exception as e:
        print(f"[CLEAR POSE] Notice: {e}")
    finally:
        try:
            bpy.ops.object.mode_set(mode=orig_mode if orig_mode in ('OBJECT', 'EDIT', 'POSE') else 'OBJECT')
        except Exception:
            pass


def reorient_armature_bones(armature):
    """
    Reorients edit bone tails towards their children's average position
    and recalculates bone roll along the global +Y axis.
    Applied exclusively for Genshin Impact, Honkai: Star Rail, and Zenless Zone Zero.
    """
    if not armature or armature.type != 'ARMATURE':
        return

    # First apply spine rest pose to fix torso offset on models with altered rest pose
    apply_spine_rest_pose(armature)

    orig_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'

    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        armature.hide_viewport = False
        armature.hide_set(False)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = armature.data.edit_bones

        for bone in edit_bones:
            if bone.children:
                avg_child_pos = sum((child.head for child in bone.children), bone.children[0].head * 0) / len(bone.children)
                if (avg_child_pos - bone.head).length > 0.001:
                    bone.tail = avg_child_pos

        for bone in edit_bones:
            if not bone.children and bone.parent:
                p_dir = bone.head - bone.parent.head
                if p_dir.length > 0.001:
                    length = bone.length if bone.length > 0.001 else 0.05
                    bone.tail = bone.head + p_dir.normalized() * length

        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Y')
    except Exception as e:
        print(f"[REORIENT BONES] Notice: {e}")
    finally:
        try:
            bpy.ops.object.mode_set(mode=orig_mode if orig_mode in ('OBJECT', 'EDIT', 'POSE') else 'OBJECT')
        except Exception:
            pass


class GI_OT_SetUpCharacter(Operator, BasicSetupUIOperator):
    """Sets Up Character"""

    bl_idname = "genshin.set_up_character"
    bl_label = "Genshin: Set Up Character (UI)"


class HSR_OT_SetUpCharacter(Operator, BasicSetupUIOperator):
    """Sets Up Character"""

    bl_idname = "honkai_star_rail.set_up_character"
    bl_label = "Honkai Star Rail: Set Up Character (UI)"


class ZZZ_OT_SetUpCharacter(Operator, BasicSetupUIOperator):
    """Sets Up Character"""

    bl_idname = "zenless_zone_zero.set_up_character"
    bl_label = "Zenless Zone Zero: Set Up Character (UI)"


def find_largest_uemodel_file(directory_or_file):
    """
    Finds the largest .uemodel file in the given directory or file path.
    Selecting the largest file ensures we import the full detailed character model (e.g. LOD0)
    rather than a low-poly LOD, accessory, or sub-mesh.
    """
    if not directory_or_file:
        return None

    if os.path.isfile(directory_or_file):
        if directory_or_file.lower().endswith(".uemodel"):
            return directory_or_file
        directory_or_file = os.path.dirname(directory_or_file)

    if not os.path.isdir(directory_or_file):
        return None

    uemodel_files = []
    for root, _, files in os.walk(directory_or_file):
        for file_name in files:
            if file_name.lower().endswith(".uemodel"):
                full_path = os.path.join(root, file_name)
                try:
                    size = os.path.getsize(full_path)
                    uemodel_files.append((size, full_path))
                except Exception:
                    uemodel_files.append((0, full_path))

    if not uemodel_files:
        return None

    # Sort descending by file size
    uemodel_files.sort(key=lambda item: item[0], reverse=True)
    largest_file = uemodel_files[0][1]
    print(f"[NTE IMPORT] Scanned {len(uemodel_files)} .uemodel files. Selected largest ({uemodel_files[0][0]} bytes): {largest_file}")
    return largest_file


class NTE_OT_SetUpCharacter(Operator, ImportHelper, CustomOperatorProperties):
    """Sets Up Character for Neverness to Everness"""

    bl_idname = "neverness_to_everness.set_up_character"
    bl_label = "Select NTE Character Folder or .uemodel"

    filename_ext = "*.*"
    filter_glob: StringProperty(
        default="*.*",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        if not self.filepath:
            return {"CANCELLED"}

        uemodel_path = find_largest_uemodel_file(self.filepath)
        if not uemodel_path or not os.path.isfile(uemodel_path):
            self.report({"ERROR"}, f"No .uemodel file found in: {self.filepath}")
            return {"CANCELLED"}

        folder = os.path.dirname(uemodel_path)
        filename = os.path.basename(uemodel_path)
        set_active_character_directory(folder)
        cache_using_cache_key(get_cache(True), CHARACTER_MODEL_FOLDER_FILE_PATH, folder)
        cache_using_cache_key(get_cache(True), NEVERNESS_TO_EVERNESS_ROOT_FOLDER_FILE_PATH, folder)
        cache_using_cache_key(get_cache(True), NEVERNESS_TO_EVERNESS_SHADER_FILE_PATH, folder)
        context.scene["setup_wizard_imported_model_dir"] = folder
        context.scene["setup_wizard_imported_uemodel_path"] = uemodel_path
        print(f"[NTE SETUP] Cached character folder: {folder} (model: {filename})")

        if hasattr(bpy.ops, 'uf') and hasattr(bpy.ops.uf, 'import_uemodel'):
            imported_ok = False

            if hasattr(context.scene, 'uf_settings') and hasattr(context.scene.uf_settings, 'reorient_bones'):
                try:
                    context.scene.uf_settings.reorient_bones = True
                    print(f"[NTE SETUP] Set context.scene.uf_settings.reorient_bones = True")
                except Exception as e_set:
                    print(f"[NTE SETUP] Notice setting reorient_bones: {e_set}")

            # Method 1: Pass directory + files collection + filepath (UEFormat ImportHelper standard)
            try:
                bpy.ops.uf.import_uemodel(
                    filepath=uemodel_path,
                    directory=folder,
                    files=[{"name": filename}]
                )
                imported_ok = True
            except Exception as e1:
                print(f"[NTE SETUP] Method 1 uf.import_uemodel notice: {e1}")

            # Method 2: Pass directory + files collection with EXEC_DEFAULT
            if not imported_ok:
                try:
                    bpy.ops.uf.import_uemodel(
                        'EXEC_DEFAULT',
                        filepath=uemodel_path,
                        directory=folder,
                        files=[{"name": filename}]
                    )
                    imported_ok = True
                except Exception as e2:
                    print(f"[NTE SETUP] Method 2 uf.import_uemodel notice: {e2}")

            # Method 3: Pass filepath only
            if not imported_ok:
                try:
                    bpy.ops.uf.import_uemodel(filepath=uemodel_path)
                    imported_ok = True
                except Exception as e3:
                    print(f"[NTE SETUP] Method 3 uf.import_uemodel notice: {e3}")

            # Method 4: Fallback execute with filepath only
            if not imported_ok:
                try:
                    bpy.ops.uf.import_uemodel('EXEC_DEFAULT', filepath=uemodel_path)
                    imported_ok = True
                except Exception as e4:
                    self.report({"WARNING"}, f"UEFormat import notice: {e4}")

            self.report({"INFO"}, f"Imported NTE character model: {filename}")
        else:
            self.report({"ERROR"}, "UEFormat add-on is not enabled or available.")
            return {"CANCELLED"}

        return {"FINISHED"}


class WW_OT_SetUpCharacter(Operator, ImportHelper, CustomOperatorProperties):
    """Sets Up Character for Wuthering Waves"""

    bl_idname = "wuthering_waves.set_up_character"
    bl_label = "Select WuWa Character Folder, .uemodel, or .fbx"

    filename_ext = "*.*"
    filter_glob: StringProperty(
        default="*.*",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        if not self.filepath:
            return {"CANCELLED"}

        folder = self.filepath if os.path.isdir(self.filepath) else os.path.dirname(self.filepath)
        uemodel_path = find_largest_uemodel_file(self.filepath)

        fbx_path = None
        if not uemodel_path:
            if not os.path.isdir(self.filepath) and self.filepath.lower().endswith(".fbx"):
                fbx_path = self.filepath
            elif os.path.isdir(self.filepath):
                for root, _, files in os.walk(self.filepath):
                    for f in files:
                        if f.lower().endswith(".fbx"):
                            fbx_path = os.path.join(root, f)
                            break
                    if fbx_path:
                        break

        from setup_wizard.import_order import (
            WUTHERING_WAVES_ROOT_FOLDER_FILE_PATH,
            WUTHERING_WAVES_SHADER_FILE_PATH,
        )

        set_active_character_directory(folder)
        cache_using_cache_key(get_cache(True), CHARACTER_MODEL_FOLDER_FILE_PATH, folder)
        cache_using_cache_key(get_cache(True), WUTHERING_WAVES_ROOT_FOLDER_FILE_PATH, folder)
        cache_using_cache_key(get_cache(True), WUTHERING_WAVES_SHADER_FILE_PATH, folder)

        existing_objects = set(context.scene.objects)

        if uemodel_path and hasattr(bpy.ops, 'uf') and hasattr(bpy.ops.uf, 'import_uemodel'):
            filename = os.path.basename(uemodel_path)
            if hasattr(context.scene, 'uf_settings'):
                try:
                    context.scene.uf_settings.import_collision = False
                    context.scene.uf_settings.import_morph_targets = True
                    context.scene.uf_settings.import_sockets = True
                    context.scene.uf_settings.import_virtual_bones = False
                    context.scene.uf_settings.reorient_bones = True
                    context.scene.uf_settings.bone_length = 4.0
                except Exception as e_set:
                    print(f"Notice setting uf_settings: {e_set}")

            try:
                bpy.ops.uf.import_uemodel(
                    filepath=uemodel_path,
                    directory=os.path.dirname(uemodel_path),
                    files=[{"name": filename}]
                )
            except Exception:
                try:
                    bpy.ops.uf.import_uemodel(filepath=uemodel_path)
                except Exception as e_uf:
                    self.report({"ERROR"}, f"Error importing .uemodel: {e_uf}")
                    return {"CANCELLED"}
        elif fbx_path and os.path.isfile(fbx_path):
            _execute_fbx_import(fbx_path)
        else:
            self.report({"ERROR"}, f"No valid .uemodel or .fbx found in {self.filepath}")
            return {"CANCELLED"}

        # Organize imported objects
        new_objects = [obj for obj in context.scene.objects if obj not in existing_objects]
        armatures = [o for o in new_objects if o.type == 'ARMATURE']
        meshes = [o for o in new_objects if o.type == 'MESH']

        from setup_wizard.character_rig_setup.wuwa_rig_script import (
            extract_clean_character_name,
            get_model_prefix,
        )

        char_name = None
        if armatures:
            arm = armatures[0]
            prefix = get_model_prefix(arm.name)
            if prefix:
                arm["ww_model_prefix"] = prefix
            char_name = extract_clean_character_name(arm.name)
            arm.name = f"{char_name}_Skeleton"

        if not char_name and meshes:
            char_name = extract_clean_character_name(meshes[0].name)

        char_name = char_name or "Character"

        for m in meshes:
            if not m.name.startswith(char_name):
                m.name = f"{char_name}_{m.name}"

        # Create character collection
        char_col = bpy.data.collections.get(char_name)
        if not char_col:
            char_col = bpy.data.collections.new(char_name)
            context.scene.collection.children.link(char_col)

        for obj in new_objects:
            if obj.name not in char_col.objects:
                char_col.objects.link(obj)
            for col in list(obj.users_collection):
                if col != char_col:
                    col.objects.unlink(obj)

        self.report({"INFO"}, f"Imported Wuthering Waves character: {char_name}")
        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                file_path_to_cache=folder,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type or GameType.WUTHERING_WAVES.name,
            )
        super().clear_custom_properties()
        return {"FINISHED"}


def compute_ake_smoothnormal_ws(mesh_obj):
    """Calculates corner-domain smoothnormalWS attribute for Arknights: Endfield meshes."""
    if not mesh_obj or mesh_obj.type != 'MESH':
        return
    mesh = mesh_obj.data
    if "smoothnormalWS" in mesh.attributes:
        return
    try:
        if mesh.uv_layers.active:
            mesh.calc_tangents(uvmap=mesh.uv_layers.active.name)
        elif mesh.uv_layers:
            mesh.calc_tangents(uvmap=mesh.uv_layers[0].name)
    except Exception:
        pass

    if not mesh.uv_layers.get("UV0") and mesh.uv_layers.active:
        try:
            mesh.uv_layers.new(name="UV0")
        except Exception:
            pass

    try:
        smooth_attr = mesh.attributes.new(name="smoothnormalWS", type='FLOAT_VECTOR', domain='CORNER')
        vert_normals = [Vector((0.0, 0.0, 0.0)) for _ in mesh.vertices]
        for poly in mesh.polygons:
            p_norm = poly.normal
            p_area = poly.area
            for vert_idx in poly.vertices:
                vert_normals[vert_idx] += p_norm * p_area

        for v_i in range(len(vert_normals)):
            if vert_normals[v_i].length > 1e-6:
                vert_normals[v_i].normalize()
            else:
                vert_normals[v_i] = mesh.vertices[v_i].normal

        for loop in mesh.loops:
            smooth_attr.data[loop.index].vector = vert_normals[loop.vertex_index]
    except Exception as e:
        print(f"[AKE SETUP] smoothnormalWS notice for {mesh_obj.name}: {e}")


def handle_ake_post_import(context):
    """Handles post FBX import operations for Arknights: Endfield: clearing imported pose, rotating -90 deg X to stand upright, normal smoothing, vertex color attributes, face subpart vertex weighting, face mesh joining, and hiding auxiliary parts."""
    # 0. Clear baked import pose and stand model upright (-90 deg on X)
    armatures = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if armatures:
        armature = armatures[0]
        orig_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
        try:
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            armature.hide_viewport = False
            try:
                armature.hide_set(False)
            except Exception:
                pass
            armature.select_set(True)
            context.view_layer.objects.active = armature

            # Select all in pose mode and clear all pose transforms
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.pose.transforms_clear()
            bpy.ops.object.mode_set(mode='OBJECT')

            # Clearing baked pose makes the character lie flat on the floor because FBX imported with rot_x = +90 deg.
            # Rotate -90 degrees on X to stand upright.
            armature.rotation_euler.x -= math.radians(90)
            context.view_layer.update()

            # Apply rotation transforms across armature and all child meshes
            meshes = [o for o in bpy.data.objects if o.type == 'MESH']
            bpy.ops.object.select_all(action='DESELECT')
            armature.select_set(True)
            for m in meshes:
                m.select_set(True)
            context.view_layer.objects.active = armature
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            print("[AKE SETUP] Cleared import pose, rotated -90 deg on X, and applied transforms successfully.")
            if not is_rigging_disabled(context):
                reorient_armature_bones(armature)
        except Exception as e:
            print(f"[AKE SETUP] Pose clear / orientation notice: {e}")
        finally:
            try:
                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode=orig_mode if orig_mode in ('OBJECT', 'EDIT', 'POSE') else 'OBJECT')
            except Exception:
                pass

    # 1. Compute smoothnormalWS and ensure Color vertex attribute exists for all meshes
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            compute_ake_smoothnormal_ws(obj)
            mesh = obj.data
            if 'Color' not in mesh.color_attributes:
                try:
                    col_attr = mesh.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
                    for col in col_attr.data:
                        col.color = (1.0, 1.0, 1.0, 1.0)
                except Exception:
                    pass

    # 2. Fix vertex group weighting for face subparts before joining
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    face_mesh = next((o for o in meshes if 'face_01' in o.name.lower() or 'face' in o.name.lower()), None)
    iris_mesh = next((o for o in meshes if 'iris_01' in o.name.lower() or 'iris' in o.name.lower()), None)
    join_targets = [
        o for o in meshes
        if o != face_mesh and any(k in o.name.lower() for k in ['eyebrow', 'brow', 'iris', 'eyeshadow', 'eyewhite'])
    ]

    # Assign Bip001_Head and eye bone weights to iris so it moves with the head and eye controllers
    if iris_mesh:
        vg_head = iris_mesh.vertex_groups.get('Bip001_Head') or iris_mesh.vertex_groups.new(name='Bip001_Head')
        for v in iris_mesh.data.vertices:
            vg_head.add([v.index], 1.0, 'REPLACE')

        vg_lf = iris_mesh.vertex_groups.get('faceLfIrisJoint') or iris_mesh.vertex_groups.new(name='faceLfIrisJoint')
        vg_rt = iris_mesh.vertex_groups.get('faceRtIrisJoint') or iris_mesh.vertex_groups.new(name='faceRtIrisJoint')
        vg_def_lf = iris_mesh.vertex_groups.get('DEF-eye.L') or iris_mesh.vertex_groups.new(name='DEF-eye.L')
        vg_def_rt = iris_mesh.vertex_groups.get('DEF-eye.R') or iris_mesh.vertex_groups.new(name='DEF-eye.R')
        for v in iris_mesh.data.vertices:
            if v.co.x > 0:
                vg_lf.add([v.index], 1.0, 'REPLACE')
                vg_def_lf.add([v.index], 1.0, 'REPLACE')
            else:
                vg_rt.add([v.index], 1.0, 'REPLACE')
                vg_def_rt.add([v.index], 1.0, 'REPLACE')

    # Ensure eyebrows and eyeshadow have Bip001_Head vertex group
    for obj in join_targets:
        if obj and obj != iris_mesh:
            if 'Bip001_Head' not in obj.vertex_groups:
                vg = obj.vertex_groups.new(name='Bip001_Head')
                for v in obj.data.vertices:
                    vg.add([v.index], 1.0, 'REPLACE')

    # Join face subparts into face_mesh
    if face_mesh and join_targets:
        try:
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            face_mesh.select_set(True)
            context.view_layer.objects.active = face_mesh
            for o in join_targets:
                o.select_set(True)
            bpy.ops.object.join()
        except Exception as e:
            print(f"[AKE SETUP] Face join notice: {e}")


    # 4. Hide auxiliary vfxpart meshes
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('vfxpart' in o.name.lower() or 'eyestar' in o.name.lower()):
            try:
                o.hide_viewport = True
                o.hide_render = True
            except Exception:
                pass


class AKE_OT_SetUpCharacter(Operator, ImportHelper, CustomOperatorProperties):
    """Sets Up Character for Arknights: Endfield"""

    bl_idname = "arknights_endfield.set_up_character"
    bl_label = "Select Arknights Endfield Character Folder or .fbx"

    filename_ext = "*.*"
    filter_glob: StringProperty(
        default="*.*",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        if not self.filepath:
            return {"CANCELLED"}

        folder = self.filepath if os.path.isdir(self.filepath) else os.path.dirname(self.filepath)
        fbx_path = None
        if not os.path.isdir(self.filepath) and self.filepath.lower().endswith(".fbx"):
            fbx_path = self.filepath
        elif os.path.isdir(self.filepath):
            for root, _, files in os.walk(self.filepath):
                for f in files:
                    if f.lower().endswith(".fbx"):
                        fbx_path = os.path.join(root, f)
                        break
                if fbx_path:
                    break

        from setup_wizard.import_order import (
            ARKNIGHTS_ENDFIELD_ROOT_FOLDER_FILE_PATH,
            ARKNIGHTS_ENDFIELD_SHADER_FILE_PATH,
        )

        set_active_character_directory(folder)
        cache_using_cache_key(get_cache(True), CHARACTER_MODEL_FOLDER_FILE_PATH, folder)
        cache_using_cache_key(get_cache(True), ARKNIGHTS_ENDFIELD_ROOT_FOLDER_FILE_PATH, folder)
        cache_using_cache_key(get_cache(True), ARKNIGHTS_ENDFIELD_SHADER_FILE_PATH, folder)
        try:
            bpy.context.scene["setup_wizard_imported_model_dir"] = folder
            if fbx_path:
                bpy.context.scene["setup_wizard_imported_fbx_path"] = fbx_path
        except Exception:
            pass

        if fbx_path:
            _execute_fbx_import(fbx_path)

        handle_ake_post_import(context)

        self.report({"INFO"}, f"Imported Arknights: Endfield character model")
        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                file_path_to_cache=folder,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type or GameType.ARKNIGHTS_ENDFIELD.name,
            )
        super().clear_custom_properties()
        return {"FINISHED"}


class GI_OT_GenshinImportModel(Operator, ImportHelper, CustomOperatorProperties):
    """Select the folder with the desired model to import"""

    bl_idname = "genshin.import_model"  # important since its how we chain file dialogs
    bl_label = "Select Character Folder"

    # ImportHelper mixin class uses this
    filename_ext = "*.*"

    import_path: StringProperty(
        name="Path",
        description="Path to the folder of the Model",
        default="",
        subtype="DIR_PATH",
    )

    filter_glob: StringProperty(
        default="*.*",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def clean_up_scene(self):
        OBJECTS_TO_CLEAN_UP = [
            'Cube',
            'Light',
        ]
        for obj in bpy.data.objects:
            if obj.name in OBJECTS_TO_CLEAN_UP:
                bpy.data.objects.remove(obj)

    def execute(self, context):
        self.clean_up_scene()
        is_character_model_file = not os.path.isdir(self.filepath) and self.filepath
        character_model_directory = (
            os.path.dirname(self.filepath) or self.file_directory
        )
        character_model_file_path_or_directory = (
            self.filepath
            if is_character_model_file
            else (self.file_directory or character_model_directory)
        )

        if not character_model_file_path_or_directory:
            bpy.ops.genshin.import_model(
                "INVOKE_DEFAULT",
                next_step_idx=self.next_step_idx,
                file_directory=self.file_directory,
                invoker_type=self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
            return {"FINISHED"}

        existing_materials = (
            bpy.data.materials.values()
        )  # used to track materials before and after importing character model
        try:
            self.import_character_model(
                character_model_file_path_or_directory, is_character_model_file
            )
            # If rigging is disabled, keep the imported armature untouched (preserve rest pose,
            # bone orientations, tails, and rolls for animation compatibility).
            if not is_rigging_disabled(context):
                armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
                for arm in armatures:
                    clear_armature_pose(arm)

                if self.game_type in (
                    GameType.GENSHIN_IMPACT.name,
                    GameType.HONKAI_STAR_RAIL.name,
                    GameType.ZENLESS_ZONE_ZERO.name,
                    GameType.ARKNIGHTS_ENDFIELD.name,
                ):
                    if armatures:
                        reorient_armature_bones(armatures[0])

            self.rename_mesh_color_attribute_name(
                SHADER_COLOR_ATTRIBUTE_NAME
            )  # Blender 3.4 changed default name to 'Attribute', revert it

            if character_model_directory:
                set_active_character_directory(character_model_directory)

            global IMPORTED_VIA_WIZARD
            IMPORTED_VIA_WIZARD = True

            # Add fake user to all materials that were added when importing character model (to prevent unused materials from being cleaned up)
            materials_imported_from_character_model = [
                material
                for material in bpy.data.materials.values()
                if material not in existing_materials
            ]
            material_utils.add_fake_user_to_materials(
                materials_imported_from_character_model
            )

            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                file_path_to_cache=character_model_directory,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        finally:
            super().clear_custom_properties()
        return {"FINISHED"}

    def import_character_model(
        self, character_model_file_path_or_directory, is_character_model_file
    ):
        if self.game_type == GameType.NEVERNESS_TO_EVERNESS.name:
            uemodel_path = find_largest_uemodel_file(character_model_file_path_or_directory)
            if not uemodel_path or not os.path.isfile(uemodel_path):
                self.report({"ERROR"}, f"No .uemodel file found in: {character_model_file_path_or_directory}")
                raise RuntimeError(f"No .uemodel file found in: {character_model_file_path_or_directory}")

            folder = os.path.dirname(uemodel_path)
            filename = os.path.basename(uemodel_path)
            set_active_character_directory(folder)
            cache_using_cache_key(get_cache(True), CHARACTER_MODEL_FOLDER_FILE_PATH, folder)
            cache_using_cache_key(get_cache(True), NEVERNESS_TO_EVERNESS_ROOT_FOLDER_FILE_PATH, folder)
            cache_using_cache_key(get_cache(True), NEVERNESS_TO_EVERNESS_SHADER_FILE_PATH, folder)
            try:
                bpy.context.scene["setup_wizard_imported_model_dir"] = folder
                bpy.context.scene["setup_wizard_imported_uemodel_path"] = uemodel_path
            except Exception:
                pass

            if hasattr(bpy.context.scene, 'uf_settings') and hasattr(bpy.context.scene.uf_settings, 'reorient_bones'):
                try:
                    bpy.context.scene.uf_settings.reorient_bones = True
                except Exception:
                    pass

            if hasattr(bpy.ops, 'uf') and hasattr(bpy.ops.uf, 'import_uemodel'):
                imported_ok = False
                try:
                    bpy.ops.uf.import_uemodel(
                        filepath=uemodel_path,
                        directory=folder,
                        files=[{"name": filename}]
                    )
                    imported_ok = True
                except Exception as e1:
                    print(f"[NTE SETUP] Method 1 uf.import_uemodel notice: {e1}")

                if not imported_ok:
                    try:
                        bpy.ops.uf.import_uemodel(
                            'EXEC_DEFAULT',
                            filepath=uemodel_path,
                            directory=folder,
                            files=[{"name": filename}]
                        )
                        imported_ok = True
                    except Exception as e2:
                        print(f"[NTE SETUP] Method 2 uf.import_uemodel notice: {e2}")

                if not imported_ok:
                    try:
                        bpy.ops.uf.import_uemodel(filepath=uemodel_path)
                        imported_ok = True
                    except Exception as e3:
                        print(f"[NTE SETUP] Method 3 uf.import_uemodel notice: {e3}")

                if not imported_ok:
                    try:
                        bpy.ops.uf.import_uemodel('EXEC_DEFAULT', filepath=uemodel_path)
                        imported_ok = True
                    except Exception as e4:
                        self.report({"WARNING"}, f"UEFormat import notice: {e4}")

                self.report({"INFO"}, f"Imported NTE character model (largest .uemodel): {filename}")
                return
            else:
                self.report({"ERROR"}, "UEFormat add-on is not enabled or available.")
                raise RuntimeError("UEFormat add-on is not enabled or available.")

        if self.game_type == GameType.WUTHERING_WAVES.name:
            uemodel_path = find_largest_uemodel_file(character_model_file_path_or_directory)
            fbx_path = None
            if not uemodel_path:
                if is_character_model_file and character_model_file_path_or_directory.lower().endswith(".fbx"):
                    fbx_path = character_model_file_path_or_directory
                else:
                    fbx_path = self.__find_fbx_file(character_model_file_path_or_directory)

            if not uemodel_path and not fbx_path:
                self.report({"ERROR"}, f"No .uemodel or .fbx file found in: {character_model_file_path_or_directory}")
                raise RuntimeError(f"No .uemodel or .fbx file found in: {character_model_file_path_or_directory}")

            folder = os.path.dirname(uemodel_path or fbx_path)
            set_active_character_directory(folder)
            cache_using_cache_key(get_cache(True), CHARACTER_MODEL_FOLDER_FILE_PATH, folder)
            cache_using_cache_key(get_cache(True), WUTHERING_WAVES_ROOT_FOLDER_FILE_PATH, folder)
            cache_using_cache_key(get_cache(True), WUTHERING_WAVES_SHADER_FILE_PATH, folder)
            try:
                bpy.context.scene["setup_wizard_imported_model_dir"] = folder
                if uemodel_path:
                    bpy.context.scene["setup_wizard_imported_uemodel_path"] = uemodel_path
                if fbx_path:
                    bpy.context.scene["setup_wizard_imported_fbx_path"] = fbx_path
            except Exception:
                pass

            existing_objects = set(bpy.context.scene.objects)

            if uemodel_path:
                if hasattr(bpy.context.scene, 'uf_settings'):
                    try:
                        bpy.context.scene.uf_settings.import_collision = False
                        bpy.context.scene.uf_settings.import_morph_targets = True
                        bpy.context.scene.uf_settings.import_sockets = True
                        bpy.context.scene.uf_settings.import_virtual_bones = False
                        bpy.context.scene.uf_settings.reorient_bones = True
                        bpy.context.scene.uf_settings.bone_length = 4.0
                    except Exception:
                        pass

                if hasattr(bpy.ops, 'uf') and hasattr(bpy.ops.uf, 'import_uemodel'):
                    filename = os.path.basename(uemodel_path)
                    imported_ok = False
                    try:
                        bpy.ops.uf.import_uemodel(
                            filepath=uemodel_path,
                            directory=folder,
                            files=[{"name": filename}]
                        )
                        imported_ok = True
                    except Exception:
                        pass

                    if not imported_ok:
                        try:
                            bpy.ops.uf.import_uemodel('EXEC_DEFAULT', filepath=uemodel_path, directory=folder, files=[{"name": filename}])
                            imported_ok = True
                        except Exception:
                            pass

                    if not imported_ok:
                        try:
                            bpy.ops.uf.import_uemodel(filepath=uemodel_path)
                            imported_ok = True
                        except Exception:
                            pass

                    if not imported_ok:
                        try:
                            bpy.ops.uf.import_uemodel('EXEC_DEFAULT', filepath=uemodel_path)
                            imported_ok = True
                        except Exception as e:
                            self.report({"ERROR"}, f"UEFormat import error: {e}")
                            raise RuntimeError(f"UEFormat import error: {e}")
                else:
                    self.report({"ERROR"}, "UEFormat add-on is not enabled or available.")
                    raise RuntimeError("UEFormat add-on is not enabled or available.")
            elif fbx_path:
                _execute_fbx_import(fbx_path)

            # Organize imported objects
            new_objects = [obj for obj in bpy.context.scene.objects if obj not in existing_objects]
            armatures = [o for o in new_objects if o.type == 'ARMATURE']
            meshes = [o for o in new_objects if o.type == 'MESH']

            from setup_wizard.character_rig_setup.wuwa_rig_script import (
                extract_clean_character_name,
                get_model_prefix,
            )

            char_name = None
            if armatures:
                arm = armatures[0]
                prefix = get_model_prefix(arm.name)
                if prefix:
                    arm["ww_model_prefix"] = prefix
                char_name = extract_clean_character_name(arm.name)
                arm.name = f"{char_name}_Skeleton"

            if not char_name and meshes:
                char_name = extract_clean_character_name(meshes[0].name)

            char_name = char_name or "Character"

            for m in meshes:
                if not m.name.startswith(char_name):
                    m.name = f"{char_name}_{m.name}"

            # Create character collection
            char_col = bpy.data.collections.get(char_name)
            if not char_col:
                char_col = bpy.data.collections.new(char_name)
                bpy.context.scene.collection.children.link(char_col)

            for obj in new_objects:
                if obj.name not in char_col.objects:
                    char_col.objects.link(obj)
                for col in list(obj.users_collection):
                    if col != char_col:
                        col.objects.unlink(obj)

            self.report({"INFO"}, f"Imported Wuthering Waves character: {char_name}")
            return

        character_model_file_path = (
            character_model_file_path_or_directory
            if is_character_model_file
            else self.__find_fbx_file(character_model_file_path_or_directory)
        )

        if not character_model_file_path:
            self.report(
                {"ERROR"},
                f"No FBX file found in: {character_model_file_path_or_directory}",
            )
            raise RuntimeError(
                f"No FBX file found in: {character_model_file_path_or_directory}"
            )

        # Persist the real FBX path for later steps (e.g. Finish Setup renaming)
        try:
            bpy.context.scene["setup_wizard_imported_fbx_path"] = (
                character_model_file_path
            )
            bpy.context.scene["setup_wizard_imported_model_dir"] = os.path.dirname(
                character_model_file_path
            )
        except Exception:
            pass

        # Ensure clean context for import (no active/selected objects to interfere)
        try:
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = None
        except Exception as e:
            self.report({"WARNING"}, f"Failed to clear selection context: {e}")

        # Keep track of existing objects to see if anything gets imported even if an exception is raised
        existing_objects = set(bpy.data.objects.keys())

        if self.game_type == GameType.ZENLESS_ZONE_ZERO.name:
            try:
                _execute_fbx_import(character_model_file_path)
            except Exception as e:
                # Clean up newly created objects
                new_objects = [
                    bpy.data.objects[name]
                    for name in bpy.data.objects.keys()
                    if name not in existing_objects
                ]
                for ob in new_objects:
                    try:
                        bpy.data.objects.remove(ob)
                    except Exception:
                        pass

                error_message = "Please reopen Blender and import the FBX manually."
                self.report({"ERROR"}, error_message)
                raise RuntimeError(error_message)

            obj = None
            new_objects = [
                bpy.data.objects[name]
                for name in (set(bpy.data.objects.keys()) - existing_objects)
                if name in bpy.data.objects
            ]
            new_armatures = [o for o in new_objects if o.type == "ARMATURE"]
            if new_armatures:
                obj = new_armatures[0]

            if not obj:
                for ob in bpy.data.objects:
                    if ob.type == "ARMATURE" and (
                        "avatar" in ob.name.lower() or "npc" in ob.name.lower()
                    ):
                        obj = ob
                        break
            if not obj:
                armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
                if armatures:
                    obj = armatures[0]
            if not obj:
                obj = bpy.data.objects.get("Armature")

            if obj:
                if obj.name in bpy.context.view_layer.objects:
                    obj.hide_set(False)
                    obj.hide_viewport = False
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")

                # Find top-most parent object (e.g. root empty like Avatar_Female_Size02_ZhenzhenDawnlight_UI)
                top_root = obj
                while top_root.parent is not None:
                    top_root = top_root.parent

                import math

                def get_world_bone_extents(arm):
                    mw = arm.matrix_world
                    max_wy = max(abs((mw @ b.head_local).y) for b in arm.data.bones) if arm.data.bones else 0
                    max_wz = max(abs((mw @ b.head_local).z) for b in arm.data.bones) if arm.data.bones else 0
                    return max_wy, max_wz

                bpy.context.view_layer.update()
                wy, wz = get_world_bone_extents(obj)

                if wy > wz:
                    orig_rot = top_root.rotation_euler.copy()
                    best_rot = None
                    for test_deg in [90, -90, 180, -180]:
                        top_root.rotation_euler = orig_rot.copy()
                        top_root.rotation_euler[0] += math.radians(test_deg)
                        bpy.context.view_layer.update()
                        test_y, test_z = get_world_bone_extents(obj)
                        if test_z > test_y and test_z > 0.5:
                            best_rot = test_deg
                            break

                    if best_rot is None:
                        top_root.rotation_euler = orig_rot

                    # Select top_root and all children to apply transform
                    def select_hierarchy(o):
                        o.select_set(True)
                        for c in o.children:
                            select_hierarchy(c)

                    bpy.ops.object.select_all(action="DESELECT")
                    select_hierarchy(top_root)
                    bpy.context.view_layer.objects.active = top_root

                    try:
                        bpy.ops.object.transform_apply(
                            location=False, rotation=True, scale=True
                        )
                    except Exception as e:
                        print("Failed to apply rotation/scale transforms:", e)

                    # If top_root is an empty, unparent armature so it's clean
                    if top_root.type == "EMPTY" and obj.parent == top_root:
                        mw = obj.matrix_world.copy()
                        obj.parent = None
                        obj.matrix_world = mw



                if (
                    obj.parent
                    and obj.parent.type == "EMPTY"
                    and obj.parent.name == obj.name
                ):
                    empty_parent = obj.parent
                    matrix_world = obj.matrix_world.copy()
                    obj.parent = None
                    obj.matrix_world = matrix_world
                    bpy.data.objects.remove(empty_parent)

                for mesh_obj in bpy.data.objects:
                    if mesh_obj.type == "MESH" and (
                        "hairshadow" in mesh_obj.name.lower()
                        or "fx" in mesh_obj.name.lower()
                    ):
                        mesh_obj.hide_viewport = True
                        mesh_obj.hide_render = True

                self.fix_zzz_eye_shadow()

                if obj and not is_rigging_disabled(bpy.context) and self.game_type in (
                    GameType.GENSHIN_IMPACT.name,
                    GameType.HONKAI_STAR_RAIL.name,
                    GameType.ZENLESS_ZONE_ZERO.name,
                    GameType.ARKNIGHTS_ENDFIELD.name,
                ):
                    reorient_armature_bones(obj)

            for object in bpy.data.objects:
                if object.type == "MESH" and not object.data.uv_layers.get("UV1"):
                    object.data.uv_layers.new(name="UV1")

            for object in bpy.data.objects:
                if "EffectMesh" in object.name or "EyeStar" in object.name:
                    try:
                        bpy.data.objects[object.name].hide_set(True)
                    except RuntimeError:
                        bpy.data.objects[object.name].hide_viewport = True
                    bpy.data.objects[object.name].hide_render = True

            return

        # Import using recommended settings
        try:
            _execute_fbx_import(character_model_file_path)
        except Exception as e:
            # Clean up newly created objects
            new_objects = [
                bpy.data.objects[name]
                for name in bpy.data.objects.keys()
                if name not in existing_objects
            ]
            for ob in new_objects:
                try:
                    bpy.data.objects.remove(ob)
                except Exception:
                    pass

            error_message = "Please reopen Blender and import the FBX manually."
            self.report({"ERROR"}, error_message)
            raise RuntimeError(error_message)

        for object in bpy.data.objects:
            if object.type == "MESH" and not object.data.uv_layers.get("UV1"):
                object.data.uv_layers.new(name="UV1")
        # Quick-fix, just want to shove this in here for now...
        # Hide EffectMesh (gets deleted later on) and EyeStar
        for object in bpy.data.objects:
            if "EffectMesh" in object.name or "EyeStar" in object.name:
                try:
                    bpy.data.objects[object.name].hide_set(True)
                except RuntimeError:
                    # Object is not in the active View Layer, use hide_viewport instead
                    bpy.data.objects[object.name].hide_viewport = True
                bpy.data.objects[object.name].hide_render = True

        if self.game_type == GameType.ARKNIGHTS_ENDFIELD.name:
            handle_ake_post_import(bpy.context)

    def fix_zzz_eye_shadow(self):
        faceobj = None
        for obj in bpy.data.objects:
            if obj.type == "MESH" and "face" in obj.name.lower():
                faceobj = obj
                break
        if faceobj:
            try:
                if faceobj.name in bpy.context.view_layer.objects:
                    faceobj.hide_set(False)
                    faceobj.hide_viewport = False
                bpy.context.view_layer.objects.active = faceobj
                faceobj.select_set(True)
                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")
                faceobj.select_set(True)
                bpy.context.view_layer.objects.active = faceobj

                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.select_all(action="DESELECT")
                if "Eye Transparent" in faceobj.vertex_groups:
                    faceobj.vertex_groups.active = faceobj.vertex_groups[
                        "Eye Transparent"
                    ]
                    bpy.ops.object.vertex_group_select()
                    for group in faceobj.vertex_groups:
                        if "highlight" in group.name.lower():
                            faceobj.vertex_groups.active = group
                            bpy.ops.object.vertex_group_deselect()
                    bpy.ops.mesh.separate(type="SELECTED")
                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode="OBJECT")

                eye_obj = None
                for ob in bpy.context.selected_objects:
                    if ob != faceobj and ob.type == "MESH":
                        eye_obj = ob
                        break
                if eye_obj:
                    eye_obj.name = "EyeTransparent"
            except Exception as e:
                print("fixeyeshadow error:", e)
                try:
                    if bpy.ops.object.mode_set.poll():
                        bpy.ops.object.mode_set(mode="OBJECT")
                except Exception:
                    pass

    def reset_pose_location_and_rotation(self):
        armatures = [
            object for object in bpy.data.objects if object.type == "ARMATURE"
        ]
        if not armatures:
            return  # No armature found (e.g. for static meshes, weapons, etc.), skip gracefully
        armature = armatures[0]
        try:
            bpy.context.view_layer.objects.active = armature
            if armature.mode != "OBJECT" and bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.mode_set(mode="POSE")
            bpy.ops.pose.loc_clear()
            bpy.ops.pose.rot_clear()
            bpy.ops.object.mode_set(mode="OBJECT")
        except Exception as e:
            print(f"Notice: reset_pose_location_and_rotation skipped ({e})")

    """
        NOTE: This will rename the Color Attributes for ALL meshes
        Currently expecting character setup to be performed in a fresh (new) file
    """

    def rename_mesh_color_attribute_name(self, name):
        meshes = [mesh for mesh_name, mesh in bpy.data.meshes.items()]

        for mesh in meshes:
            if len(mesh.color_attributes) == 1:
                mesh.color_attributes[
                    0
                ].name = (
                    name  # PGR: Named "VertexColors" and may not be the active color
                )
            else:
                if mesh.color_attributes.active_color:
                    mesh.color_attributes.active_color.name = name

    def __find_fbx_file(self, directory):
        for root, folder, files in os.walk(directory):
            for file_name in files:
                if ".fbx" in pathlib.Path(file_name).suffix:
                    return os.path.join(root, file_name)


"""
    This Operator should be executed AFTER importing the character model and
    BEFORE importing Genshin materials.
    That way there is no chance of deleting empties used by Festivity's shaders.
"""


class GI_OT_DeleteEmpties(Operator, CustomOperatorProperties):
    """Deletes Empties (except Head Driver's empties)"""

    bl_idname = "genshin.delete_empties"
    bl_label = "Genshin: Delete empties (except Head Driver's empties)"

    def execute(self, context):
        if self.game_type == GameType.ZENLESS_ZONE_ZERO.name:
            global IMPORTED_VIA_WIZARD
            if not IMPORTED_VIA_WIZARD:
                # Clear character model folder file path from cache to force manual folder selection for textures/outlines
                cache = get_cache()
                if CHARACTER_MODEL_FOLDER_FILE_PATH in cache:
                    cache.pop(CHARACTER_MODEL_FOLDER_FILE_PATH, None)
                    from setup_wizard.import_order import write_to_blender_cache

                    write_to_blender_cache(cache)
            else:
                # Reset the session variable
                IMPORTED_VIA_WIZARD = False

            obj = None
            for ob in bpy.data.objects:
                if ob.type == "ARMATURE" and (
                    "avatar" in ob.name.lower() or "npc" in ob.name.lower()
                ):
                    obj = ob
                    break
            if not obj:
                armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
                if armatures:
                    obj = armatures[0]
            if not obj:
                obj = bpy.data.objects.get("Armature")

            if obj:


                for object in bpy.data.objects:
                    if object.type == "MESH" and not object.data.uv_layers.get("UV1"):
                        object.data.uv_layers.new(name="UV1")

                for object in bpy.data.objects:
                    if object.type == "MESH" and (
                        "EffectMesh" in object.name
                        or "EyeStar" in object.name
                        or "hairshadow" in object.name.lower()
                        or "fx" in object.name.lower()
                    ):
                        try:
                            bpy.data.objects[object.name].hide_set(True)
                        except:
                            bpy.data.objects[object.name].hide_viewport = True
                        bpy.data.objects[object.name].hide_render = True

        scene = bpy.context.scene
        empties_to_not_delete = [
            "Head Forward",
            "Head Up",
            "Light Direction",
            "Main Light Direction",
            "Face Light Direction",
            "Head Driver",
            "Head Origin",
        ]
        for object in scene.objects:
            if object.type == "EMPTY":
                should_delete = True
                for name_to_keep in empties_to_not_delete:
                    if object.name.startswith(name_to_keep):
                        should_delete = False
                        break
                if should_delete:
                    # Unparent any children of this empty, keeping their world transforms
                    for child in object.children:
                        matrix_world = child.matrix_world.copy()
                        child.parent = None
                        child.matrix_world = matrix_world
                    bpy.data.objects.remove(object)

        self.report({"INFO"}, "Deleted Empties")
        if self.next_step_idx:
            NextStepInvoker().invoke(
                self.next_step_idx,
                self.invoker_type,
                high_level_step_name=self.high_level_step_name,
                game_type=self.game_type,
            )
        return {"FINISHED"}


class GI_OT_ClearPose(Operator, CustomOperatorProperties):
    """Clears pose transforms (location, rotation, scale) for all bones in the armature"""

    bl_idname = "genshin.clear_pose"
    bl_label = "Clear Pose"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            armatures = [o for o in context.selected_objects if o.type == "ARMATURE"]
            if not armatures:
                armatures = [
                    o for o in context.scene.objects
                    if o.type == "ARMATURE" and not any(ign in o.name.lower() for ign in ["eyerig", "facerig", "lighting", "metarig"])
                ]
            if armatures:
                armature = armatures[0]

        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Please select a character armature first.")
            return {"CANCELLED"}

        clear_armature_pose(armature)
        self.report({"INFO"}, f"Successfully cleared pose for '{armature.name}'.")
        return {"FINISHED"}


class GI_OT_ReorientBones(Operator, CustomOperatorProperties):
    """Reorients armature bones toward children and recalculates roll along global +Y axis"""

    bl_idname = "genshin.reorient_bones"
    bl_label = "Fix Orientation"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            armatures = [o for o in context.selected_objects if o.type == "ARMATURE"]
            if not armatures:
                armatures = [
                    o for o in context.scene.objects
                    if o.type == "ARMATURE" and not any(ign in o.name.lower() for ign in ["eyerig", "facerig", "lighting", "metarig"])
                ]
            if armatures:
                armature = armatures[0]

        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Please select a character armature first.")
            return {"CANCELLED"}

        game_type = self.game_type
        if not game_type and hasattr(context.scene, "game_type_dropdown"):
            game_type = context.scene.game_type_dropdown
        if not game_type:
            game_type = GameType.GENSHIN_IMPACT.name

        if game_type == GameType.GENSHIN_IMPACT.name:
            clear_armature_pose(armature)

        reorient_armature_bones(armature)
        self.report({"INFO"}, f"Successfully fixed bone orientation for '{armature.name}'.")
        return {"FINISHED"}


register, unregister = bpy.utils.register_classes_factory(
    [
        GI_OT_GenshinImportModel,
        GI_OT_DeleteEmpties,
        GI_OT_ClearPose,
        GI_OT_ReorientBones,
        GI_OT_SetUpCharacter,
        HSR_OT_SetUpCharacter,
        ZZZ_OT_SetUpCharacter,
        NTE_OT_SetUpCharacter,
        WW_OT_SetUpCharacter,
        AKE_OT_SetUpCharacter,
    ]
)
