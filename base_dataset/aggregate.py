"""
This program takes all samples with different thread counts of the same benchmark, and aggregates them to find all scalability coefficients of the different targeted snippets of code of the given benchmark.
"""

import click
import json
from utils.serialize import *
import random
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import numpy as np

class TargetFunc:
    def __init__(self, points, formula):
        self.points = points
        self.formula = formula

    def __call__(self, alpha):
        total_error = 0
        for x, y in self.points:
            predicted_y = self.formula(x, alpha) 
            error = (y - predicted_y) ** 2
            total_error += error
        return total_error

def fit_curve(points: list[tuple[float, float]], make_photo: str | None = None) -> float:
    """runtime_alpha(t) = alpha / x + (1 - alpha)"""
    
    # Initial guess for 'a'
    initial_guess = 1.0

    if points[0][0] != 1:
        print(f"Error: points list must start with '1' for normalization!")
        exit(1)

    basetime = points[0][1]
    normalized_points = [(nt, runtime/basetime) for nt, runtime in points]

    curve = TargetFunc(normalized_points, lambda x, alpha: alpha / x + (1 - alpha))

    # Perform optimization to minimize the objective function
    result = minimize(curve, initial_guess)

    # Extract the optimized value of 'a'
    # optimized_a = result.x[0]
    optimized_a = result.x[0]


    if isinstance(make_photo, str):
        x_values = np.linspace(0.2, 18, 100)  # Generate x values for plotting
        y_values = optimized_a / x_values + (1 - optimized_a)  # Calculate y values for the curve

        plt.figure(figsize=(8, 6))
        plt.scatter(*zip(*normalized_points), label='Data Points')
        plt.plot(x_values, y_values, color='red', label='Fitted Curve')
        plt.xlabel('Num Threads')
        plt.ylabel('Runtime')
        plt.title(f'Alpha = {optimized_a:.3f}, Loss = {curve(optimized_a):.3f}')
        plt.legend()
        plt.grid(True)
        plt.savefig(make_photo)

    return optimized_a


def get_sample_id(sample: LoopSample) -> str:
    """
    Return a unique identifier representing the given sample
    """
    return str(sample.loop.for_token)

def group_by_snippet(snippet_samples_per_tc: dict[int, list[LoopSample]]) -> list[dict[int, LoopSample]]:
    """
    Transform from:
        - a dictionary mapping a thread count to all samples of different
            snippets sampled with that thread count.
    Into:
        - a list of dictionaries where each nested dict represents the samples
            with all different thread counts of a certain snippet.
    """
    
    
    # First find which samples are even present by acquiring a unique identifier to each:
    snippet_identifiers: set[str] = set()
    for snippet_samples in snippet_samples_per_tc.values():
        for sample in snippet_samples:
            snippet_identifiers.add(get_sample_id(sample))
    
    # This is the same as the result, only instead of a list of snippet dicts,
    #   we have a dict of dicts to be able to esaly find to which nested dict a given sample corresponds.
    dict_of_snippet_dicts: dict[str, dict[int, LoopSample]] = {ident: dict() for ident in snippet_identifiers}
    
    for tc, snippet_samples in snippet_samples_per_tc.items():
        for sample in snippet_samples:
            dict_of_snippet_dicts[get_sample_id(sample)][tc] = sample
    
    # Turn the outer dict into a list:
    return list(dict_of_snippet_dicts.values())


@click.command()
@click.option('-b', '--bench_name', required=True, type=str, help="The name of the benchmark which's results will be aggregated")
@click.option('-t', '--thread_counts', required=True, type=str, help="A string of all thread counts for which the benchmark was sampled, decimal, space seperated, as a single string")
def aggregate(bench_name: str, thread_counts: str) -> None:
    thread_counts_parsed: list[int] = [int(tok) for tok in thread_counts.split(' ')]

    tc_to_samples: dict[int, list[LoopSample]] = dict()
    for tc in thread_counts_parsed:
        path = f"./samples/{bench_name}_{tc}.samples.json"
        tc_to_samples[tc] = load_samples_file(path)

    by_snippet: list[dict[int, LoopSample]] = group_by_snippet(tc_to_samples)
    all_coefficients: list[LoopCoefficent] = []
    for snippet_samples_by_tc in by_snippet:
        snippet_samples_by_tc.items()
        unchecked_coordinates = [(tc, sample.duration) for tc, sample in snippet_samples_by_tc.items()]
        
        if any([duration is None for tc, duration in unchecked_coordinates]):
            continue
        
        coordinates: list[tuple[int, float]] = unchecked_coordinates # type: ignore

        first_sample: LoopSample = list(snippet_samples_by_tc.values())[0]
        code_start_offset: int = first_sample.loop.for_token.offset
        coefficient_value = fit_curve(coordinates, f'./images/{bench_name}_{code_start_offset}.png')

        all_coefficients.append(
            LoopCoefficent(first_sample.loop, first_sample.raw_code, first_sample.duration, thread_counts_parsed, coefficient_value)
        )

    output_path: str = f"./samples/{bench_name}.coefficients.json"
    dump_coefficients_file(output_path, all_coefficients)

if __name__ == "__main__":
    aggregate()