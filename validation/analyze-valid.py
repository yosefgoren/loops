import json
from sys import argv
from validation.validation_common import *

data: dict = json.load(open(f'{VALIDATION_OUTPUT_BASEDIR}/ompcpp.valid.fewshot-4omini_{int(argv[1])}.json', 'r'))
results: list[dict] = data["results"]
biases: list[int] = []
for res in results:
    label = res['label']
    output = res['output']
    biases.append(label-output)

print(f"success rate: {len(list(filter(lambda x: x == 0, biases)))/len(biases)}")
print(f"1dist rate: {len(list(filter(lambda x: abs(x) < 2, biases)))/len(biases)}")
print(f"average bias: {sum(biases)/len(biases)}")
print(f"average dist: {sum(map(abs, biases))/len(biases)}")
