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
aggregate_script = StaticFileNode(f"{BASE_DATASET_DIR}/aggregate.py")
finalize_script = StaticFileNode(f"{BASE_DATASET_DIR}/finalize.py")

def pymodule_script_prefix(script_path: str) -> str:
    if not script_path.endswith('.py'):
        raise ValueError(f"expected to receive a python script (ending with .py) but got: '{script_path}'")
    no_suffix_path = script_path[:-3]
    return f"python3 -m {no_suffix_path.replace('/', '.')}"



all_rules: list[Rule] = []
coefficients_nodes: list[CreatedFileNode] = []

# Add rules shared across all benchmarks:
timer_cpp_lib = StaticFileNode("timer.hpp")
copied_timer = CreatedFileNode(f"{BASEDIR}/common/timer.hpp")
all_rules.append(ShellRule(copied_timer, [timer_cpp_lib],
    f"cp {timer_cpp_lib.path} {copied_timer.path}"
))


# Add rules for each benchmark:
for bench_name in [
    "bt",
    "cg",
    "ep",
    "ft",
    "is",
    "lu",
    "mg",
    "sp",
]:
    # src_file is never a dependency since it is modified (and will cause incorrect reconstruction)
    src_file = StaticFileNode(f"{BASEDIR}/{bench_name.upper()}/{bench_name}.cpp")

    src_file_copy = CreatedFileNode(f"{BASEDIR}/{bench_name.upper()}/orig_{bench_name}.cpp")
    all_rules.append(ShellRule(src_file_copy, [], f"cp {src_file.path} {src_file_copy.path}"))

    scopes = CreatedFileNode(f"./samples/{bench_name}.scopes.json")
    all_rules.append(ShellRule(scopes, [scopes_script],
        f"{pymodule_script_prefix(scopes_script.path)} --input {src_file.path} -o {scopes.path}"
    ))

    targets = CreatedFileNode(f"./samples/{bench_name}.targets.json")
    all_rules.append(ShellRule(targets, [scopes, targets_script],
        f"{pymodule_script_prefix(targets_script.path)} --input {scopes.path} -o {targets.path}"
    ))
    
    benchmark_sample_nodes: list[CreatedFileNode] = []
    THREAD_COUNTS = [1, 2, 4, 8, 16]
    for num_threads in THREAD_COUNTS:
        do_parallel: bool = num_threads > 1

        basename = f"{bench_name}_{num_threads}"
        times_log = CreatedFileNode(f"./samples/{basename}.times")

        mod = FileModificationNode(src_file, f"{num_threads}")
        all_rules.append(ShellFileModifyRule(mod, [targets, modify_script],
            f"{pymodule_script_prefix(modify_script.path)} --read_file {src_file.path} --write_file {src_file.path} --logs_filename {times_log.path} --tgt_file {targets.path} --parallel {'True' if do_parallel else 'False'}"
        ))

        executable_path: str = f"{BINDIR}/{bench_name}.S" # For example './NPB-CPP/NPB-OMP/bin/bt.S'
        all_rules.append(ShellRule(times_log, [mod, copied_timer],
            f"make -C {BASEDIR} {bench_name} && OMP_NUM_THREADS={num_threads} {executable_path}" # Compile and run the benchmark
        ))

        samples = CreatedFileNode(f"./samples/{basename}.samples.json")
        all_rules.append(ShellRule(samples, [times_log, targets, collect_script, src_file_copy],
            f"{pymodule_script_prefix(collect_script.path)} -o {samples.path} --runtimes_file {times_log.path} --source_file {src_file_copy.path} --loops_file {targets.path}"
        ))
        
        benchmark_sample_nodes.append(samples)

    coefs = CreatedFileNode(f"./samples/{bench_name}.coefficients.json")
    thread_counts_arg: str = ' '.join([str(i) for i in THREAD_COUNTS])
    all_rules.append(ShellRule(coefs, [aggregate_script] + benchmark_sample_nodes,
        f"{pymodule_script_prefix(aggregate_script.path)} -b {bench_name} -t '{thread_counts_arg}'"
    )) # Example command line: `python3 -m base_dataset.aggregate -b bt -t "1 2 4 8 16"`
    coefficients_nodes.append(coefs)

dataset_name = "ompcpp"
dataset_files = CreatedFileNode(f"{dataset_name}.train.jsonl") # TODO: add MAKE-API feature for target with multiple files, and use it here to make ompcpp.validate.jsonl another declared target.
gen_dataset_cmdline = f"{pymodule_script_prefix(finalize_script.path)} {dataset_name} {' '.join([node.path for node in coefficients_nodes])}"
all_rules.append(ShellRule(dataset_files, coefficients_nodes, gen_dataset_cmdline))

dataset_zip = CreatedFileNode(f"{dataset_name}.zip")
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