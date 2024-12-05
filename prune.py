import json
from serial import *

def list_from_serial(data: list[dict[str, object]], parser) -> list[object]:
    return [parser(elem) for elem in data]

data = json.load(open('scopes.json', 'r'))
loops: list[FilePosition] = [FilePosition.from_serial(elem) for elem in data["loops"]]
scopes: list[CodeScope] = [CodeScope.from_serial(elem) for elem in data["scopes"]]

class FlowError(RuntimeError):
    def __init__(self):
        super("Unexpected Control Flow")
class SyntaxError(RuntimeError):
    def __init__(self, note: str | None = None):
        super("Flow indicates syntax error in input" + "" if note is None else note)

pos_by_offset: dict[int, FilePosition | CodeScope] = dict()
dicts: list[dict[int, FilePosition | CodeScope]] = [
    {f.offset: f for f in loops},
    {s.start_pos.offset: s for s in scopes},
    {s.end_pos.offset: s for s in scopes},
]

for d in dicts:
    for offset, v in d.items():
        if offset in pos_by_offset.keys():
            raise ValueError(f"Got repeating offset: {offset}.\n\tFirst: {pos_by_offset[offset]}.\n\tSecond: {v}.")
        pos_by_offset[offset] = v

offsets = list(pos_by_offset.keys())
offsets.sort()
ordered_positions: list[tuple[int, FilePosition | CodeScope]] =  [(off, pos_by_offset[off]) for off in offsets]

def find_qualified_scope_ending(pos_idx: int) -> None | CodeScope:
    """Find code scope of for loop (specified as index in array of positions), or return None if loop is disqualified"""
    
    rest_of_pos = ordered_positions[pos_idx+1:]
    if len(rest_of_pos) < 4:
        # For disqualified since '{' is not present or invalid syntax
        # There must be at-least one '()' pair and '{}' pair after the 'for' token
        return None
    for idx, (offset, value) in enumerate(rest_of_pos):
        if type(value) is CodeScope:
            if value.context_type == ContextType.BRACES:
                if value.start_pos.offset == offset:
                    return value
                elif value.end_pos.offset == offset:
                    raise SyntaxError("Did not expect closing '}' before '{' after 'for'")
                else:
                    raise FlowError()
            else:
                # Other tokens are ignored
                continue
        else:
            # This means there were no braces before the next for - disqualifiying this loop
            return None
    # This means there were no braces after the 'for' token, so disqalifies:
    return None
        
def get_positions_in_scope(scope: CodeScope) -> list[int]:
    """returns indecies of all positions (from global list) which are within the specified scope"""
    start_idx = offsets.index(scope.start_pos.offset)
    end_idx = offsets.index(scope.end_pos.offset)
    assert start_idx < end_idx
    return list(range(start_idx+1, end_idx))

disq_inner_loop_indices: set[int] = set() # Indices of for loops disqualified due to being in an inner scope.
file = scopes[0].start_pos.file
targets: list[ForLoop] = []

for idx in range(len(ordered_positions)):
    offset, value = ordered_positions[idx]
    
    if type(value) is FilePosition:
        # Check if this for loop was already disqualified:
        if idx in disq_inner_loop_indices:
            continue
        scope = find_qualified_scope_ending(idx)
        if scope is None:
            print(f"Got disqualified 'for' at: {value}")
        else:
            # Disqualifiy all loops in inner scope:
            for inner_pos_idx in get_positions_in_scope(scope):
                inner_offset, inner_value = ordered_positions[inner_pos_idx]
                if type(inner_value) is FilePosition: #It's a for loop
                    # print(f"disqualifying: {inner_value}")
                    disq_inner_loop_indices.add(inner_pos_idx)
            print(f"Got 'for': {value}, with scope: {scope}")
            targets.append(ForLoop(value, scope))

json.dump([loop.serialize() for loop in targets], open('targets.json', 'w'), indent=4)