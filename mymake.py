#!/home/yogo/env/bin/python3
from Make_API.makeapi import *
import click

BASEDIR = "./NPB-CPP/NPB-OMP"
BINDIR = f"{BASEDIR}/bin"

rules = []
# src_file is never a dependency since it is modified (and will cause incorrect reconstruction)
src_file = StaticFileNode(f"{BASEDIR}/BT/bt.cpp")

scopes_script = StaticFileNode("scrape.py")
targets_script = StaticFileNode("prune.py")
modify_script = StaticFileNode("modify.py")
collect_script = StaticFileNode("collect.py")

timer_cpp_lib = StaticFileNode("timer.hpp")

src_file_copy = DynamicFileNode(f"{BASEDIR}/BT/orig_bt.cpp")

rules.append(ShellRule(src_file_copy, [], f"cp {src_file.path} {src_file_copy.path}"))

scopes = DynamicFileNode("main.scopes.json")
rules.append(ShellRule(scopes, [scopes_script],
    f"python3 {scopes_script.path} --input {src_file.path} -o {scopes.path}"
))

targets = DynamicFileNode("main.targets.json")
rules.append(ShellRule(targets, [scopes, targets_script],
    f"python3 {targets_script.path} --input {scopes.path} -o {targets.path}"
))

times_log = DynamicFileNode("main.times")

modified = DynamicFileNode("modified.label")
rules.append(ShellRule(modified, [targets, modify_script],
    ' && '.join([
        f"python3 {modify_script.path} --read_file {src_file.path} --write_file {src_file.path} --logs_filename {times_log.path} --targets {targets.path}",
        f"touch {modified.path}"
    ])
))

copied_timer = DynamicFileNode(f"{BASEDIR}/common/timer.hpp")
rules.append(ShellRule(copied_timer, [timer_cpp_lib],
    f"cp {timer_cpp_lib.path} {copied_timer.path}"
))

timed_executable = DynamicFileNode(f"{BINDIR}/bt.S")
rules.append(ShellRule(timed_executable, [modified, copied_timer],
    f"make -C {BASEDIR} bt"
))

rules.append(ShellRule(times_log, [timed_executable], timed_executable.path))

samples = DynamicFileNode("main.samples.json")
rules.append(ShellRule(samples, [times_log, targets, collect_script, src_file_copy],
    f"python3 {collect_script.path} -o {samples.path} --runtimes_file {times_log.path} --source_file {src_file_copy.path} --loops_file {targets.path}"
))



tgt = samples
bs = BuildSystem(rules)

@click.group()
def cli():
    pass

@cli.command("build")
def build():
    print(f"Building target...")
    bs.build(tgt)

@cli.command("clean")
def clean():
    print(f"Cleaning target...")
    bs.clean(tgt)

@cli.command("dag")
def dag():
    print(f"Printing DAG...")
    bs.dag(tgt)

if __name__ == "__main__":
    cli()