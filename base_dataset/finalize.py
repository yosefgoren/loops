import click
import json
from utils.serialize import *
import random

SYSTEM_PROMPT = "You are a specialized chatbot trained to estimate the parallel execution time of given OpenMP parallelized code snippets. Your task is to classify the code's execution time into one of five categories based on complexity and potential runtime:\n1 - None: Minimal or no execution time.\n2 - Low: Slight time consumption.\n3 - Medium: Moderate time consumption.\n4 - Much: High time consumption.\n5 - Lots: Very high time consumption.\n"
NUMBER_OF_CLASSES = 5
TRAIN_VALID_RATIO = 0.8

def classify_results_uniform(times: list[float], nb_classes: int) -> list[int]:
    """
    This function decides how different performance times should be classified to different performance categories.
    It takes in a list of runtimes (likely associated with actual code samples),
        and outputs a the list of corresponding classes.
    
    The categorization is relative to the list of inputs itself, and is defind by percentiles
        where the classes of percenties are all of uniform proportion to the entier dataset (list of times).

    For example, if the number of classes is 5:    
    The top 20% longest durations are categorized as '5' (highest time consumption),
        the next 20% as '4' e.t.c.
    """
    assert nb_classes >= 2 # Does not make sense to classify any less...

    nb_samples = len(times)
    class_size = (nb_samples+nb_classes-1)//nb_classes # Celing Divide
    
    # Find the order of the different indices:
    indexed_times: list[tuple[int, float]] = list(zip(list(range(nb_samples)), times))
    indexed_times.sort(key=lambda entry: entry[1]) # Sort by the duration
    ordered_indices: list[int] = [idx for idx, _ in indexed_times] # Discard the duration

    # The i'th position of 'classification' will have the class of the i'th sample.
    classification: list[int | None] = [None]*nb_samples
    all_classes: list[int] = list(range(1, nb_classes+1))
    for c in all_classes:
        # With this solution, the last class is smaller than the rest when `nb_samples%nb_classes != 0`
        #   But since we can assume `nb_classses << nb_samples` this should be a minor difference.
        for sample_idx in ordered_indices[(c-1)*class_size:c*class_size]:
            classification[sample_idx] = c
    
    # Except the last class, all clasess should be of the same size.
    assert all([classification.count(1) == classification.count(c) for c in all_classes[1:-1]])

    assert all([c is not None for c in classification])
    return classification # type: ignore

def split_list_randomly(ls: list[dict], first_set_size: int) -> tuple[list[dict], list[dict]]:
    if first_set_size > len(ls):
        raise ValueError("first_set_size cannot be greater than the size of the list")
    
    # Randomly select 'first_set_size' elements for the first group
    group1: list[dict] = random.sample(ls, first_set_size)
    # Derive the second group by excluding the elements in group1
    group2: list[dict] = [item for item in ls if item not in group1]
    
    return group1, group2


def dump_jsonl(content: list[dict], out_path: str) -> None:
    with open(out_path, 'w') as outf:
        for entry in content:
            outf.write(json.dumps(entry) + "\n")

@click.command()
@click.argument('output_prefix', type=str)
@click.argument('input_files', nargs=-1, type=str)
def finalize(output_prefix: str, input_files: list[str]) -> None:
    # Collect all raw samples:
    raw_samples: list[LoopSample] = []
    for fname in input_files:
        raw_samples += load_samples_file(fname)

    # Filter the samples for ones with 'None' duration:
    filtered_samples = [sample for sample in raw_samples if sample.duration is not None]
    durations: list[float] = [sample.duration for sample in filtered_samples] # type: ignore
    # TODO: check how is it possible that samples are None...
    
    # Classify all of the samples with respect to eachother:
    classification: list[int] = classify_results_uniform(durations, NUMBER_OF_CLASSES)
    
    # Compile the final dataset entries, prompts and classifications (completions):
    dataset: list[dict] = []
    for sample, c in zip(filtered_samples, classification):
        dataset.append({
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": sample.raw_code
                },
                {
                    "role": "assistant",
                    "content": str(c)
                }
            ]
        })

    train_set_size = int((len(dataset)*TRAIN_VALID_RATIO)//1)
    train, validate = split_list_randomly(dataset, train_set_size)

    # Write the generated dataset to the output file:
    dump_jsonl(train, f"{output_prefix}.train.jsonl")
    dump_jsonl(validate, f"{output_prefix}.validate.jsonl")

if __name__ == "__main__":
    finalize()