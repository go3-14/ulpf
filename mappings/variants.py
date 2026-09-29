from copy import deepcopy
from mappings.matcher import condition_matches

def select_variant(mapping: dict, parsed: dict) -> dict:
    variants = mapping.get("variants") or []
    chosen = next((item for item in variants if condition_matches(item.get("when", {}), parsed)), None)
    if chosen is None:
        return mapping
    result = deepcopy(mapping)
    for key in ("field_map", "transforms", "defaults", "constants"):
        if key in chosen:
            merged = dict(result.get(key) or {})
            merged.update(chosen[key] or {})
            result[key] = merged
    if "class_uid" in chosen:
        result.setdefault("ocsf", {})["class_uid"] = chosen["class_uid"]
    for key in ("category_uid", "version"):
        if key in chosen: result.setdefault("ocsf", {})[key] = chosen[key]
    return result
