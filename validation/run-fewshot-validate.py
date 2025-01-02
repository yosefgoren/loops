import json
from sys import argv
from utils.openai_common import *
from validation.validation_common import *

SYSTEM_PROMPT = """\
You are a specialized chatbot trained to estimate the execution time of given code snippets.
Your task is to classify the code's execution time into one of five categories based on potential runtime:
1 - Very small
2 - Small
3 - Moderate
4 - High
5 - Very high
Your responses must always be a single number from 1 to 5 and nothing more.
"""
CONTEXT_MESSAGES = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

client = get_openapi_client()
def categorize_performance(code_txt: str) -> int:
    """
    Return a categorization by the model in 1-5, or -1 if model response is invalid
    """
    completion = client.chat.completions.create(
    model=MODEL_NAME,
    store=True,

    messages=[
        *CONTEXT_MESSAGES,
        {"role": "user", "content": code_txt}
    ]
    )
    msg = completion.choices[0].message
    print(f"Got response: '{msg}'")
    return int(msg.content) if (msg.content.isdigit() and int(msg.content) >= 0 and int(msg.content) <= 5) else -1
    

def collect_validation(valid_set_fname: str, output_fname: str):
    with open(output_fname, 'x') as outf: #Open it here to fail before making OpenAI API requests
        valid_samples: list[tuple[str, int]] = parse_jsonl_ds(valid_set_fname)

        results: list[dict] = [
            {
                "code": sample[0],
                "label": sample[1],
                "output": categorize_performance(sample[0])
            }
            for sample in valid_samples
        ]
        file_content: dict = {
            "model": MODEL_NAME,
            "context": CONTEXT_MESSAGES,
            "results": results
        }

        json.dump(file_content, outf, indent=4)

collect_validation("ompcpp.validate.jsonl", f"{VALIDATION_OUTPUT_BASEDIR}/ompcpp.valid.fewshot-4omini_{int(argv[1])}.json")
