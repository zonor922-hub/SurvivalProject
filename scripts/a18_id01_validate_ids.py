"""A18-ID01: read-only ID audit of one loaded Unreal world. No assignment/save.
Run in the Unreal Python environment; passing world never combines editor and PIE.
"""
import json
import unreal

INTERFACE_PATH = '/Game/Survival/Interaction/BPI_Interactable.BPI_Interactable_C'
PERMANENT_CLASSES = ('BP_WorldPickup_C', 'BP_StorageContainer_C')

def audit_level(world=None):
    if world is None:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not unreal.SystemLibrary.is_valid(world):
        return {'status': 'FAIL', 'errors': ['IdentityCheckUnavailable: invalid world']}
    interface = unreal.load_class(None, INTERFACE_PATH)
    if interface is None:
        return {'status': 'FAIL', 'errors': ['IdentityCheckUnavailable: missing interface']}
    groups, records, errors = {}, [], []
    for actor in unreal.GameplayStatics.get_all_actors_with_interface(world, interface):
        if not unreal.SystemLibrary.is_valid(actor):
            continue
        path = actor.get_path_name()
        permanent = any(unreal.MathLibrary.class_is_child_of(actor.get_class(), unreal.load_class(None, '/Game/Survival/Interaction/' + n[:-2] + '.' + n)) for n in PERMANENT_CLASSES)
        try:
            target_id, stable = actor.call_method('GetInteractionTargetId')
            valid = unreal.GuidLibrary.is_valid_guid(target_id)
            key = unreal.GuidLibrary.conv_guid_to_string(target_id).upper()
            record = {'actor': path, 'class': actor.get_class().get_path_name(), 'target_id': key, 'has_stable_id': bool(stable), 'valid_guid': bool(valid), 'permanent': permanent}
            records.append(record)
            if valid:
                groups.setdefault(key, []).append(path)
            if stable and not valid:
                errors.append({'actor': path, 'reason': 'ContradictoryStableId'})
            if permanent and not (stable and valid):
                errors.append({'actor': path, 'reason': 'MissingStableId'})
        except Exception as exc:
            errors.append({'actor': path, 'reason': 'IdentityCheckUnavailable', 'detail': str(exc)})
    duplicates = {key: paths for key, paths in groups.items() if len(paths) > 1}
    return {'status': 'FAIL' if errors or duplicates else 'PASS', 'scope': 'loaded actors in one world only; unloaded levels/cells and other maps NOT VERIFIED', 'world': world.get_path_name(), 'records': records, 'duplicate_ids': duplicates, 'errors': errors}

def write_report(output_path, world=None):
    report = audit_level(world)
    with open(output_path, 'w', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    return report
