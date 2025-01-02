from utils.openai_common import *
import random
from sys import argv
from augmentation.augmentation_common import *

VERSION = str(argv[1])

def shuffle_list(input_list):
    """
    Shuffles the order of elements in a given list.
    
    Args:
        input_list (list): The list to be shuffled.
    
    Returns:
        list: A new list with the elements shuffled.
    """
    shuffled_list = input_list[:]
    random.shuffle(shuffled_list)
    return shuffled_list

orig = parse_jsonl_ds('ompcpp.train.jsonl')
augmented = parse_jsonl_ds(f'{AUGMENTATION_OUTPUT_BASEDIR}/ompcpp.train.augment_{VERSION}.jsonl')

with open(f'ompcpp.train+augmented-shuffle_{VERSION}.jsonl', 'x') as outf:
    for snippet, label in shuffle_list(orig+augmented):
        write_jsonl_line(snippet, label, outf)

with open(f'ompcpp.train+augmented-blocks_{VERSION}.jsonl', 'x') as outf:
    for (snippet1, label1), (snippet2, label2) in zip(orig, augmented):
        write_jsonl_line(snippet1, label1, outf)
        write_jsonl_line(snippet2, label2, outf)