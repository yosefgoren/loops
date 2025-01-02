from openai import *
import json

MODEL_NAME = "gpt-4o-mini"

def get_openapi_client() -> OpenAI:
    return OpenAI(api_key=open("utils/api_key.txt", 'r').read().strip())

def parse_jsonl_ds(fname: str) -> list[tuple[str, int]]:
    valid_raw: str = open(fname, 'r').read()
    valid_raw_samples: list[str] = valid_raw.splitlines()
    valid_full_samples: list[dict[str, list[dict[str, str]]]] = [json.loads(raw_sample) for raw_sample in valid_raw_samples]
    valid_dict_samples: list[tuple[dict[str, str], dict[str, str]]] = [(full_sample["messages"][1], full_sample["messages"][2]) for full_sample in valid_full_samples]
    valid_samples: list[tuple[str, int]] = [
        (dict_sample[0]["content"], int(dict_sample[1]["content"]))
        for dict_sample in valid_dict_samples
    ]
    return valid_samples

CLASSEFIER_SYSTEM_PROMPT = "You are a specialized chatbot trained to estimate the parallel execution time of given OpenMP parallelized code snippets. Your task is to classify the code's execution time into one of five categories based on complexity and potential runtime:\n1 - None: Minimal or no execution time.\n2 - Low: Slight time consumption.\n3 - Medium: Moderate time consumption.\n4 - Much: High time consumption.\n5 - Lots: Very high time consumption.\n"

def write_jsonl_line(code: str, label: int, file):
    file.write(json.dumps({
        "messages": [
            {
                "role": "system",
                "content": CLASSEFIER_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": code
            },
            {
                "role": "assistant",
                "content": str(label)
            }
        ]
    }) + "\n")
    file.flush()