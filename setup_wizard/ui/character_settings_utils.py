# Central helper: per-armature game tag for Character Settings panels.
# Stores GameType.name on the rig object so Append keeps the info and
# each panel only shows for its own game + selected character.

GACHA_GAME_KEY = "gacha_game"
GACHA_CHAR_KEY = "gacha_character"


def stamp_rig_game(rig_obj, game_name, char_name=None):
    """Tags a rig armature so its Character Settings panel can be resolved after Append."""
    if rig_obj is None:
        return
    try:
        rig_obj[GACHA_GAME_KEY] = str(game_name)
    except Exception:
        pass
    if char_name:
        try:
            rig_obj[GACHA_CHAR_KEY] = str(char_name)
        except Exception:
            pass
    # Also tag armature data (survives some Append/Link paths)
    try:
        data = getattr(rig_obj, "data", None)
        if data is not None:
            data[GACHA_GAME_KEY] = str(game_name)
    except Exception:
        pass


def resolve_settings_armature(context):
    """Returns the armature targeted by selection (None if none). Never falls back to scene."""
    if context is None:
        return None
    try:
        obj = getattr(context, "active_object", None) or getattr(context, "object", None)
    except Exception:
        obj = None
    candidates = []
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
        try:
            arm = cand.find_armature()
            if arm is not None:
                return arm
        except Exception:
            pass
        for mod in getattr(cand, "modifiers", []) or []:
            try:
                if mod.type == 'ARMATURE' and getattr(mod, "object", None) is not None:
                    return mod.object
            except Exception:
                continue
        parent = getattr(cand, "parent", None)
        if parent is not None and getattr(parent, "type", None) == 'ARMATURE':
            return parent
    return None


def _iter_rig_meshes(arm):
    seen = set()
    try:
        for child in getattr(arm, "children_recursive", []) or []:
            if getattr(child, "type", None) == 'MESH' and child.name not in seen:
                seen.add(child.name)
                yield child
    except Exception:
        pass
    try:
        import bpy
        for obj in bpy.data.objects:
            if getattr(obj, "type", None) != 'MESH' or obj.name in seen:
                continue
            try:
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE' and getattr(mod, "object", None) == arm:
                        yield obj
                        break
            except Exception:
                continue
    except Exception:
        pass


def detect_armature_game(arm):
    """Detects GameType.name for an armature: stamped tag first, then per-rig heuristics."""
    if arm is None:
        return None
    # 1. Stamped tag (set at rig time, survives Append)
    try:
        g = arm.get(GACHA_GAME_KEY)
        if g:
            return str(g)
    except Exception:
        pass
    try:
        g = getattr(arm, "data", {}).get(GACHA_GAME_KEY) if hasattr(getattr(arm, "data", None), "get") else None
        if g:
            return str(g)
    except Exception:
        pass
    # 2. Bone signatures (WuWa / AKE empties are parented, not bones, so check objects too)
    try:
        bones = getattr(getattr(arm, "data", None), "bones", []) or []
        bone_names = set(bones.keys()) if hasattr(bones, "keys") else {b.name for b in bones}
        if "EyeTracker" in bone_names or arm.get("ww_model_prefix") is not None:
            return "WUTHERING_WAVES"
    except Exception:
        pass
    # 3. Per-rig materials (scoped to this rig, never global bpy.data.materials)
    try:
        mat_names = []
        for mesh in _iter_rig_meshes(arm):
            for slot in getattr(mesh, "material_slots", []) or []:
                mat = getattr(slot, "material", None)
                if mat is not None:
                    mat_names.append(mat.name.lower())
        blob = " ".join(mat_names)
        if not blob:
            return None
        if "stellartoon" in blob or "hsr" in blob:
            return "HONKAI_STAR_RAIL"
        if "hoyoverse - genshin" in blob or "hoyoverse - gi" in blob or "genshin" in blob:
            return "GENSHIN_IMPACT"
        if "kythera" in blob or blob.strip().startswith("zzz ") or " zzz " in f" {blob} ":
            return "ZENLESS_ZONE_ZERO"
        if "pbrtoon" in blob or "endfield" in blob or "arknights" in blob:
            return "ARKNIGHTS_ENDFIELD"
        if "wuwa" in blob or "wuthering" in blob or "gustling" in blob:
            return "WUTHERING_WAVES"
    except Exception:
        pass
    return None


def resolve_character_name(arm, fallback=None):
    """Single canonical character name for WGTS_<Char> (Append-safe).

    Prefers the stamped gacha_character tag, else the shared
    extract_clean_character_name() so rig scripts and face rigs always
    produce the SAME collection name (no WGTS_Skeleton + WGTS_SkeletonRig dupes).
    """
    if arm is not None:
        try:
            tag = arm.get(GACHA_CHAR_KEY)
            if tag:
                return str(tag)
        except Exception:
            pass
        try:
            from setup_wizard.character_rig_setup.rig_ui_utils import extract_clean_character_name
            clean = extract_clean_character_name(getattr(arm, "name", "") or "")
            if clean and clean.lower() not in ("character", "armature", "rig", "root"):
                return clean
        except Exception:
            pass
        try:
            return str(arm.name).replace("Rig", "")
        except Exception:
            pass
    return fallback


def is_game_armature(context, game_name):
    """True only if the selected armature belongs to game_name. False otherwise (incl. no selection)."""
    arm = resolve_settings_armature(context)
    if arm is None:
        return False
    detected = detect_armature_game(arm)
    if detected is not None:
        return detected == str(game_name)
    return False
