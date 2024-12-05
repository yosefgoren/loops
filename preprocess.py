from utils.sources import *
from os import system

for path in [f"{PREFIX}/{suffix}" for suffix in SUFFIXES]:
    system(f"gcc -E {path}.cpp -o {path}.i")