# Shared helper: per-character WGTS isolation (Append-safe).
# Each character gets WGTS_<CharName> nested INSIDE its own collection,
# so File > Append > Collection > <Char> only brings its own widgets.

import bpy


def get_char_collection(rig_obj, char_name=None):
    if rig_obj is not None:
        try:
            for c in list(rig_obj.users_collection):
                if c.name not in ("Collection", "Master Collection", "Scene Collection"):
                    return c
        except Exception:
            pass
    if char_name:
        coll = bpy.data.collections.get(str(char_name))
        if coll is not None:
            return coll
    try:
        return bpy.context.scene.collection
    except Exception:
        return None


def get_or_create_char_wgts(char_coll, char_name):
    wgts_name = f"WGTS_{char_name}"
    wgts_coll = bpy.data.collections.get(wgts_name)
    if wgts_coll is None:
        wgts_coll = bpy.data.collections.new(wgts_name)
    try:
        if wgts_coll.name not in char_coll.children:
            char_coll.children.link(wgts_coll)
    except Exception:
        pass
    # Never leave per-character WGTS at scene root
    try:
        if wgts_coll.name in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.unlink(wgts_coll)
    except Exception:
        pass
    # Keep it only under char_coll
    try:
        for parent_c in list(bpy.data.collections):
            if parent_c != char_coll and parent_c != wgts_coll and wgts_coll.name in parent_c.children:
                try:
                    parent_c.children.unlink(wgts_coll)
                except Exception:
                    pass
    except Exception:
        pass
    for flag in ("hide_viewport", "hide_select", "hide_render"):
        try:
            setattr(wgts_coll, flag, True)
        except Exception:
            pass
    try:
        def _exclude(lc, target):
            if lc.collection == target:
                try:
                    lc.exclude = True
                except Exception:
                    pass
                return True
            for child in lc.children:
                if _exclude(child, target):
                    return True
            return False
        _exclude(bpy.context.view_layer.layer_collection, wgts_coll)
    except Exception:
        pass
    return wgts_coll


def isolate_wgts_for_character(rig_obj, char_name, char_coll=None, extra_keywords=None):
    """Moves this rig's custom-shape widgets into WGTS_<Char> nested in char collection."""
    if not char_name:
        return None
    char_name = str(char_name)
    # Canonical name (stamp > extract_clean): rig scripts and face rigs must agree,
    # otherwise WGTS_Skeleton + WGTS_SkeletonRig dupes appear.
    if rig_obj is not None:
        try:
            from setup_wizard.ui.character_settings_utils import resolve_character_name
            char_name = resolve_character_name(rig_obj, char_name) or char_name
        except Exception:
            pass
    if char_coll is None:
        char_coll = get_char_collection(rig_obj, char_name)
    if char_coll is None:
        return None
    wgts_coll = get_or_create_char_wgts(char_coll, char_name)

    referenced = set()
    try:
        if rig_obj is not None:
            for pb in rig_obj.pose.bones:
                cs = getattr(pb, "custom_shape", None)
                if cs is not None:
                    referenced.add(cs.name)
    except Exception:
        pass

    keywords = ["WGT-", "root plate", "head-control-shape", "eye circle", "eye controller"]
    if extra_keywords:
        keywords.extend(list(extra_keywords))
    # Head-driver empties (NOT Light Direction: that stays with the character).
    # startswith match covers per-character renames like "Head Origin_Char".
    head_empty_prefixes = ("Head Origin", "Head Driver", "Head Forward", "Head Up", "Face Light Direction")

    def _move(c_obj):
        if c_obj is None or wgts_coll is None:
            return
        try:
            if c_obj.name not in wgts_coll.objects:
                wgts_coll.objects.link(c_obj)
        except Exception:
            return
        for ucoll in list(c_obj.users_collection):
            if ucoll != wgts_coll:
                try:
                    ucoll.objects.unlink(c_obj)
                except Exception:
                    pass

    # Shapes used by ANY other rig: never steal those (multi-char safe).
    # Anything else matching widget keywords (incl. orphan .001 duplicates
    # left by wm.append / Rigify) belongs in THIS character's WGTS.
    other_used_ids = set()
    try:
        for o in bpy.data.objects:
            if o.type != 'ARMATURE' or o == rig_obj:
                continue
            try:
                for pb in o.pose.bones:
                    cs = getattr(pb, "custom_shape", None)
                    if cs is not None:
                        other_used_ids.add(id(cs))
            except Exception:
                continue
    except Exception:
        pass

    for w_obj in list(bpy.data.objects):
        try:
            w_type = getattr(w_obj, "type", None)
            is_head_empty = (
                w_type == 'EMPTY'
                and any(w_obj.name.startswith(p) for p in head_empty_prefixes)
            )
            if w_type == 'EMPTY' and not is_head_empty:
                continue
            if w_type not in ('MESH', 'EMPTY'):
                continue
            if w_type == 'MESH':
                if any(mod.type == "ARMATURE" for mod in getattr(w_obj, "modifiers", []) or []):
                    continue
                if w_obj.name.startswith("S_actor_"):
                    continue
            # isaacfacerig widget planes (Plane.001, ...) only when they belong to a
            # FaceRig: parented to it or already sitting in a widget collection.
            # Never grab a generic user plane from the scene root.
            is_facerig_plane = False
            if w_type == 'MESH' and (w_obj.name.startswith("Plane.") or w_obj.name.startswith("Plane ")):
                try:
                    parent = getattr(w_obj, "parent", None)
                    if parent is not None and parent.type == 'ARMATURE' and any(
                        k in parent.name.lower() for k in ('facerig', 'isaac')
                    ):
                        is_facerig_plane = True
                    else:
                        for uc in list(w_obj.users_collection):
                            un = uc.name
                            if un == "wgt" or un.startswith("wgt.") or un == "WGTS" or un.startswith("WGTS") or un == "WG":
                                is_facerig_plane = True
                                break
                except Exception:
                    pass
            is_wgt = (
                w_obj.name in referenced
                or is_head_empty
                or is_facerig_plane
                or (w_type == 'MESH' and any(k in w_obj.name for k in keywords))
            )
            if is_wgt:
                # WGT-* and generic widget meshes (head-control-shape, root plate,
                # eye circle...) move into THIS char's WGTS unless another rig uses them.
                # This also catches orphan .001 duplicates from wm.append / Rigify.
                used_by_other = False
                try:
                    used_by_other = id(w_obj) in other_used_ids
                except Exception:
                    pass
                if not used_by_other:
                    _move(w_obj)
                    for flag in ("hide_viewport", "hide_render"):
                        try:
                            setattr(w_obj, flag, True)
                        except Exception:
                            pass
        except Exception:
            continue

    # Migrate leftovers from global wgt / Rigify WGTS_* that belong to this rig
    for coll in list(bpy.data.collections):
        if coll == wgts_coll or coll == char_coll:
            continue
        try:
            cname = coll.name
            is_global = (
                cname == "wgt" or cname.startswith("wgt.")
                or cname == "WGTS" or cname.startswith("WGTS_") or cname == "WG"
            )
        except Exception:
            continue
        if not is_global:
            continue
        # Don't touch another character's WGTS_<Other>
        if coll.name.startswith("WGTS_") and coll.name != wgts_coll.name:
            # Still migrate objects used by THIS rig, leave the rest
            for c_obj in list(coll.objects):
                try:
                    used = c_obj.name in referenced
                    if not used and rig_obj is not None:
                        for pb in rig_obj.pose.bones:
                            if getattr(pb, "custom_shape", None) == c_obj:
                                used = True
                                break
                    if used:
                        _move(c_obj)
                except Exception:
                    continue
            # Merge dupe: if nothing (else) remains, remove it so only 1 WGTS survives
            try:
                if len(coll.objects) == 0 and len(coll.children) == 0:
                    bpy.data.collections.remove(coll, do_unlink=True)
            except Exception:
                pass
            continue
        for c_obj in list(coll.objects):
            try:
                if id(c_obj) in other_used_ids:
                    continue
                _move(c_obj)
            except Exception:
                continue
        try:
            if len(coll.objects) == 0 and len(coll.children) == 0:
                bpy.data.collections.remove(coll, do_unlink=True)
        except Exception:
            pass

    return wgts_coll
