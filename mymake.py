#!/home/yogo/env/bin/python3
from Make_API.makeapi import *
import click

BASEDIR = "./NPB-CPP/NPB-OMP"
BINDIR = f"{BASEDIR}/bin"
BASE_DATASET_DIR = "base_dataset"

scopes_script = StaticFileNode(f"{BASE_DATASET_DIR}/scrape.py")
targets_script = StaticFileNode(f"{BASE_DATASET_DIR}/prune.py")
modify_script = StaticFileNode(f"{BASE_DATASET_DIR}/modify.py")
collect_script = StaticFileNode(f"{BASE_DATASET_DIR}/collect.py")
finalize_script = StaticFileNode(f"{BASE_DATASET_DIR}/finalize.py")

def pymodule_script_prefix(script_path: str) -> str:
    if not script_path.endswith('.py'):
        raise ValueError(f"expected to receive a python script (ending with .py) but got: '{script_path}'")
    no_suffix_path = script_path[:-3]
    return f"python3 -m {no_suffix_path.replace('/', '.')}"

def nas_collection_rules(bench_name: str) -> tuple[list[Rule], DynamicFileNode]:
    """
    Returns a generated samples node and a list of rules required for creating it.
    """
    rules: list[Rule] = []
    
    # src_file is never a dependency since it is modified (and will cause incorrect reconstruction)
    src_file = StaticFileNode(f"{BASEDIR}/{bench_name.upper()}/{bench_name}.cpp")


    src_file_copy = DynamicFileNode(f"{BASEDIR}/{bench_name.upper()}/orig_{bench_name}.cpp")

    rules.append(ShellRule(src_file_copy, [], f"cp {src_file.path} {src_file_copy.path}"))

    scopes = DynamicFileNode(f"./samples/{bench_name}.scopes.json")
    rules.append(ShellRule(scopes, [scopes_script],
        f"{pymodule_script_prefix(scopes_script.path)} --input {src_file.path} -o {scopes.path}"
    ))

    targets = DynamicFileNode(f"./samples/{bench_name}.targets.json")
    rules.append(ShellRule(targets, [scopes, targets_script],
        f"{pymodule_script_prefix(targets_script.path)} --input {scopes.path} -o {targets.path}"
    ))

    times_log = DynamicFileNode(f"./samples/{bench_name}.times")

    modified = DynamicFileNode(f"./labels/{bench_name}-modified.label")
    rules.append(ShellRule(modified, [targets, modify_script],
        ' && '.join([
            f"{pymodule_script_prefix(modify_script.path)} --read_file {src_file.path} --write_file {src_file.path} --logs_filename {times_log.path} --tgt_file {targets.path}",
            f"touch {modified.path}"
        ])
    ))

    timed_executable = DynamicFileNode(f"{BINDIR}/{bench_name}.S")
    rules.append(ShellRule(timed_executable, [modified, copied_timer],
        f"make -C {BASEDIR} {bench_name}"
    ))

    rules.append(ShellRule(times_log, [timed_executable], timed_executable.path))

    samples = DynamicFileNode(f"./samples/{bench_name}.samples.json")
    rules.append(ShellRule(samples, [times_log, targets, collect_script, src_file_copy],
        f"{pymodule_script_prefix(collect_script.path)} -o {samples.path} --runtimes_file {times_log.path} --source_file {src_file_copy.path} --loops_file {targets.path}"
    ))
    
    return rules, samples


all_rules: list[Rule] = []
sample_nodes: list[DynamicFileNode] = []

# Add rules shared across all benchmarks:
timer_cpp_lib = StaticFileNode("timer.hpp")
copied_timer = DynamicFileNode(f"{BASEDIR}/common/timer.hpp")
all_rules.append(ShellRule(copied_timer, [timer_cpp_lib],
    f"cp {timer_cpp_lib.path} {copied_timer.path}"
))


# Add rules for each benchmark:
for bench in [
    "bt",
    "cg",
    "ep",
    "ft",
    "is",
    "lu",
    "mg",
    "sp",
]:
    new_rules, node = nas_collection_rules(bench)
    sample_nodes.append(node)
    all_rules += new_rules

dataset_name = "ompcpp"
dataset_files = DynamicFileNode(f"{dataset_name}.train.jsonl") # TODO: add MAKE-API feature for target with multiple files, and use it here to make ompcpp.validate.jsonl another declared target.
gen_dataset_cmdline = f"{pymodule_script_prefix(finalize_script.path)} {dataset_name} {' '.join([node.path for node in sample_nodes])}"
all_rules.append(ShellRule(dataset_files, sample_nodes, gen_dataset_cmdline))

dataset_zip = DynamicFileNode(f"{dataset_name}.zip")
all_rules.append(ShellRule(dataset_zip, [dataset_files], f"zip {dataset_zip.path} {dataset_name}.train.jsonl {dataset_name}.validate.jsonl"))


# Generic Make-API CLI
# TODO: add script to avoid writing this every time
bs = BuildSystem(all_rules)

@click.group()
def cli():
    pass

@cli.command("build")
def build():
    print(f"Building target...")
    bs.build()

@cli.command("clean")
def clean():
    print(f"Cleaning target...")
    bs.clean()

@cli.command("dag")
def dag():
    print(f"Printing DAG...")
    bs.dag()

if __name__ == "__main__":
    cli()