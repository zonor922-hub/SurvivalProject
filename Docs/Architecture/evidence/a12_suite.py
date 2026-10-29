"""A12 black-box assertions over real BPC_Inventory public commands. No graph edits."""
import unreal
from a09_verify import read, write, snapshot, result, items


def suite(gi, bp, scenario, tests, primary=None):
    keep = []
    def check(label, value):
        tests.append({'scenario': scenario, 'test': label, 'passed': bool(value)})
        assert value, label
    def new(count=4, weight=10.):
        o = unreal.new_object(bp.generated_class(), outer=gi)
        keep.append(o)
        o.call_method('InitializeInventory', (gi, count, weight))
        check('initialized fixture', o.call_method('IsInitialized'))
        return o
    def rev(o): return read(snapshot(o), 'Revision')
    def total(o): return sum(read(s, 'Quantity') for s in items(o))
    def guid(o, index=0): return read(items(o)[index], 'StackId')
    def audit(*objects):
        ids = []
        inventories = []
        for o in objects:
            snap = snapshot(o)
            identity = read(snap, 'InventoryId')
            check('valid inventory GUID', unreal.GuidLibrary.is_valid_guid(identity))
            inventories.append(identity.export_text())
            for i, slot in enumerate(read(snap, 'Slots')):
                check('stable slot index', read(slot, 'SlotIndex') == i)
                if read(slot, 'HasItem'):
                    s = read(slot, 'ItemStack')
                    # Directed fixtures use the catalog wood definition (20 / 0.5).
                    check('positive quantity within wood MaxStack', 0 < read(s, 'Quantity') <= 20)
                    check('valid stack GUID', unreal.GuidLibrary.is_valid_guid(read(s, 'StackId')))
                    ids.append(read(s, 'StackId').export_text())
                else:
                    check('empty slot canonical GUID', not unreal.GuidLibrary.is_valid_guid(read(read(slot, 'ItemStack'), 'StackId')))
            check('derived wood weight', o.call_method('GetCurrentWeight') == (total(o) * .5, True))
            check('weight within capacity', o.call_method('GetCurrentWeight')[0] <= read(snap, 'MaxWeight'))
        check('unique live stack GUIDs across inventories', len(ids) == len(set(ids)))
        check('unique inventory GUIDs', len(inventories) == len(set(inventories)))
    def add(o, q):
        s = read(read(snapshot(o), 'Slots')[0], 'ItemStack')
        write(s, 'ItemId', 'item.wood'); write(s, 'Quantity', q)
        return o.call_method('TryAddExact', (s,))
    def success(o, action, q, *others):
        before = rev(o); r = result(action())
        check('success result and one revision increment', r == (True, 1, q, before + 1))
        audit(o, *others)
    def reject(objects, action, code, transfer=False):
        before = [snapshot(o).export_text() for o in objects]
        revisions = [rev(o) for o in objects]
        raw = action(); r = result(raw[0] if transfer else raw)
        check('expected rejection and zero actual quantity', r == (False, code, 0, revisions[0]))
        if transfer: check('destination revision unchanged in result', raw[1] == revisions[1])
        check('failure preserves complete snapshots', before == [snapshot(o).export_text() for o in objects])
        audit(*dict.fromkeys(objects))
    o = primary if primary is not None else new()
    check('fresh primary inventory', rev(o) == 0 and total(o) == 0)
    if scenario == 1:
        success(o, lambda: add(o, 20), 20)
        check('exact upper weight boundary accepted', o.call_method('GetCurrentWeight') == (10., True))
        before = snapshot(o).export_text()
        for _ in range(10): snapshot(o); o.call_method('GetCurrentWeight'); o.call_method('IsInitialized')
        check('reads do not mutate state', snapshot(o).export_text() == before)
        copy = snapshot(o); slots = list(read(copy, 'Slots')); s = read(slots[0], 'ItemStack')
        write(s, 'Quantity', 999); write(slots[0], 'ItemStack', s); write(copy, 'Slots', slots)
        write(copy, 'Revision', 999); write(copy, 'MaxWeight', 999.)
        check('nested snapshot copy detached', snapshot(o).export_text() == before)
        reject([o], lambda: add(o, 1), 8)
        for q in (0, -1): reject([o], lambda q=q: add(o, q), 6)
        success(o, lambda: o.call_method('TryRemoveExact', ('item.wood', 20)), 20)
        check('empty lower weight boundary', o.call_method('GetCurrentWeight') == (0., True))
        reject([o], lambda: o.call_method('TryRemoveExact', ('item.wood', 1)), 10)
        zero = new(weight=0.); reject([zero], lambda: add(zero, 1), 8)
        full = new(count=1, weight=100.); success(full, lambda: add(full, 20), 20)
        reject([full], lambda: add(full, 1), 9)
        multi = new(weight=100.); success(multi, lambda: add(multi, 21), 21)
        check('21 wood distributed over two stacks', [read(s, 'Quantity') for s in items(multi)] == [20, 1])
        success(multi, lambda: multi.call_method('TryRemoveExact', ('item.wood', 21)), 21)
        check('multi-stack removal leaves empty inventory', total(multi) == 0)
    elif scenario == 2:
        success(o, lambda: add(o, 10), 10); original = guid(o)
        success(o, lambda: o.call_method('TrySplit', (original, 4, 1)), 4)
        created = guid(o, 1)
        check('split quantities, GUID and conserved weight', [read(s, 'Quantity') for s in items(o)] == [6, 4] and guid(o).export_text() == original.export_text() and created.export_text() != original.export_text() and total(o) == 10)
        reject([o], lambda: o.call_method('TrySplit', (original, 1, 1)), 9)
        reject([o], lambda: o.call_method('TrySplit', (original, 0, 2)), 6)
        success(o, lambda: o.call_method('TryMerge', (created, original)), 4)
        check('merge preserves receiving GUID and quantity', total(o) == 10 and len(items(o)) == 1 and guid(o).export_text() == original.export_text())
        reject([o], lambda: o.call_method('TryMerge', (created, original)), 11)
        full = new(count=1); success(full, lambda: add(full, 10), 10)
        reject([full], lambda: full.call_method('TrySplit', (guid(full), 1, 0)), 9)
        over = new(weight=100.); success(over, lambda: add(over, 21), 21)
        reject([over], lambda: over.call_method('TryMerge', (guid(over, 1), guid(over))), 14)
    elif scenario == 3:
        dest = new(); success(o, lambda: add(o, 10), 10); original = guid(o)
        before = [rev(o), rev(dest)]
        raw = o.call_method('TryTransferExact', (dest, original, 3, *before))
        check('transfer commits both revisions', result(raw[0]) == (True, 1, 3, 2) and raw[1] == 1 and [rev(o), rev(dest)] == [2, 1])
        check('transfer conserves pair quantities', total(o) == 7 and total(dest) == 3)
        check('partial transfer identity', guid(o).export_text() == original.export_text() and guid(dest).export_text() != original.export_text())
        audit(o, dest)
        for sr, dr in ((1, 1), (2, 0)):
            reject([o, dest], lambda sr=sr,dr=dr: o.call_method('TryTransferExact', (dest, original, 1, sr, dr)), 15, True)
        reject([o, o], lambda: o.call_method('TryTransferExact', (o, original, 1, rev(o), rev(o))), 16, True)
        blocked = new(count=1); success(blocked, lambda: add(blocked, 20), 20)
        reject([o, blocked], lambda: o.call_method('TryTransferExact', (blocked, original, 1, rev(o), rev(blocked))), 8, True)
        slots = new(count=1, weight=100.); success(slots, lambda: add(slots, 20), 20)
        reject([o, slots], lambda: o.call_method('TryTransferExact', (slots, original, 1, rev(o), rev(slots))), 9, True)
        empty = new(); raw = o.call_method('TryTransferExact', (empty, original, 7, rev(o), rev(empty)))
        check('full transfer preserves GUID and both revisions', result(raw[0]) == (True, 1, 7, 3) and raw[1] == 1 and guid(empty).export_text() == original.export_text() and total(o) == 0 and total(empty) + total(dest) == 10)
        audit(o, dest, empty)
    else: raise ValueError('SCENARIO must be 1, 2 or 3')
