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
@click.option('-r', '--read_file', required=True, type=str)
@click.option('-w', '--write_file', required=True, type=str)
@click.option('-l', '--logs_filename', required=True, type=str)
@click.option('-t', '--targets', required=True, type=str)
def modify(read_file: str, write_file: str, logs_filename: str, targets: str):
    targets: list[ForLoop] = load_targets_file(targets)

    assert len(targets) > 0
    assert all([tgt.for_token.file == read_file for tgt in targets])
    assert read_file.endswith(".cpp")

    inserts: list[tuple[str, int]] = []
    includes: str = "".join([f"#include \"{name}\"\n" for name in ["timer.hpp", "omp.h"]])
    inserts.append((includes, 0))
    for loop in targets:
        # ident*2 is the loop start ID, ident*2+1 is the loop end ID
        inserts.append((f"__timer_capture__({loop.ident*2});", loop.for_token.offset))
        inserts.append((f"__timer_capture__({loop.ident*2+1});", loop.scope.end_pos.offset+1))
    replaces = [
        ("//@#$init\n", f'__timer_init__("{logs_filename}");\n'),
        ("//@#$finish\n", f"__timer_finish__();\n")
    ]
    # print("\n".join([str(m) for m in mods]))
    atomic_modify(read_file, write_file, inserts, replaces)
    print(f"results written to: {write_file}")

if __name__ == "__main__":
    modify()