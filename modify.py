import json
from serial import *
import click

def insert(text_corpus: str, inserted: str, offset: int) -> str:
    before, after = text_corpus[:offset], text_corpus[offset:]
    return before + inserted + after

def atomic_modify(
    src_file: str,
    out_file: str,
    to_insert_list: list[tuple[str, int]],
    to_replace_list: list[tuple[str, str]]
):
    """
    Atomically inserts a list of values at provided positions, and replaces given sequences.
    All provided positions are specified with respect to the unmodified list.
    """
    # inserts.sort(key=lambda _, off: off) #TODO: verify sorted...
    gain = 0
    content = open(src_file, 'r').read()
    for inserted, off in to_insert_list:
        content = insert(content, inserted, off+gain)
        gain += len(inserted)
    # Replacing AFTER inserting so replacement with different length does not invalidate offsets.
    for old, new in to_replace_list:
        content = content.replace(old, new)
    open(out_file, 'w').write(content)

@click.command()
@click.argument('basename', type=str)
def modify(basename: str):
    data = json.load(open(f'{basename}.targets.json', 'r'))
    targets: list[ForLoop] = [ForLoop.from_serial(raw_loop) for raw_loop in data]

    assert len(targets) > 0
    src_fname = f"{basename}.cpp"
    assert targets[0].for_token.file == src_fname
    assert src_fname.endswith(".cpp")
    out_fname = f"{basename}.timed.cpp"


    inserts: list[tuple[str, FilePosition]] = []
    includes: str = "".join([f"#include \"{name}\"\n" for name in ["timer.hpp", "omp.h"]])
    inserts.append((includes, 0))
    for loop in targets:
        inserts.append(("__timer_capture__(0);", loop.for_token.offset))
        inserts.append(("__timer_capture__(1);", loop.scope.end_pos.offset+1))
    replaces = [
        ("//@#$init\n", f'__timer_init__("{basename}.times");\n'),
        ("//@#$finish\n", f"__timer_finish__();\n")
    ]
    # print("\n".join([str(m) for m in mods]))
    atomic_modify(src_fname, out_fname, inserts, replaces)
    print(f"results written to: {out_fname}")

if __name__ == "__main__":
    modify()