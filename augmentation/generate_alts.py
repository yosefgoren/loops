from openai import *
from utils.openai_common import *
from sys import argv
import os
from augmentation.augmentation_common import *

client = get_openapi_client()

AUGMENT_SYSTEM_PROMPT = """\
You are a specialized chatbot trained to augment snippets of C++ code.
Your taks is to augment the snippet of code provided to you by generating an alternative code snippet.
Your alternative code snippets are equivalent to the ones provided to you in terms of their runtime performance and the code's functionality.
Your responses must not include anything other than the alternative snippet, in particular, they do not include the code's context or explenations.
"""

def augment_code(snippet: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        store=True,
        messages=[
            {"role": "system", "content": AUGMENT_SYSTEM_PROMPT},
            {"role": "user", "content": "for(m=0; m<5; m++){\n\terrnm[m]=sqrt(errnm[m]/((nx0-2)*(ny0-2)*(nz0-2)));\n}"},
            {"role": "assistant", "content": "auto base = ((nx0-2)*(ny0-2)*(nz0-2));\nerrnm[0]=sqrt(errnm[0]/base);\nerrnm[1]=sqrt(errnm[1]/base);\nerrnm[2]=sqrt(errnm[2]/base);\nerrnm[3]=sqrt(errnm[3]/base);\nerrnm[4]=sqrt(errnm[4]/base);"},
            {"role": "user", "content": "for(j = 1; j < nrows; j++){\n\tnzloc[j] = nzloc[j] + nzloc[j-1];\n}"},
            {"role": "assistant", "content": "for(int j = 1; j < nrows; ++j) {\n\tnzloc[j] += nzloc[j - 1];\n}"},
            {"role": "user", "content": snippet},
        ]
    )

    msg = completion.choices[0].message
    print(f"Got response: '{msg}'")
    return msg.content


def generate_augmented():
    all_samples: list[tuple[str, int]] = parse_jsonl_ds('ompcpp.train.jsonl')
    for snippet, label in all_samples:
        augmented = augment_code(snippet)
        yield (augmented, label)
    
with open(f'{AUGMENTATION_OUTPUT_BASEDIR}/ompcpp.train.augment_{argv[1]}.jsonl', 'x') as outf:
    for snippet, label in generate_augmented():
        write_jsonl_line(snippet, label, outf)