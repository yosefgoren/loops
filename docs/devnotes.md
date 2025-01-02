## Transformer Classification
A few articles with some relevant background related to transformer classification:
* https://medium.com/@anthony.demeusy/machine-learning-tips-adjusting-decision-threshold-for-binary-classification-c937d7046a43
* https://machinelearningmastery.com/threshold-moving-for-imbalanced-classification/
* https://cookbook.openai.com/examples/using_logprobs


## Prompt Ideas
Here is a base Idea for what the system prompt for performance estimation should be:
```json
{
  "system": "You are a specialized chatbot trained to estimate the parallel execution time of given OpenMP parallelized code snippets. Your task is to classify the code's execution time into one of five categories based on complexity and potential runtime:\n1 - None: Minimal or no execution time.\n2 - Low: Slight time consumption.\n3 - Medium: Moderate time consumption.\n4 - Much: High time consumption.\n5 - Lots: Very high time consumption.\n",
  "prompt": "#include <omp.h>\n#include <stdio.h>\n\nint main() {\n    int n = 1000000;\n    double sum = 0.0;\n    double start_time = omp_get_wtime();\n\n    #pragma omp parallel for reduction(+:sum)\n    for (int i = 0; i < n; i++) {\n        sum += i * 0.5;\n    }\n\n    double end_time = omp_get_wtime();\n    printf(\"Execution Time: %f seconds\\n\", end_time - start_time);\n\n    return 0;\n",
  "completion": "3"
}
```

## Future Directions
Some areas worth exploring in regard to improving the model's results:
* Task Description: should we describe the task to the model before each question (regardless of fine-tuning), for example by specifying the actual time intervals of each timing class.
* Code Context: how much code context should we provide with each prompt to enhance the ability of the model to comprehend the code to be profiled.