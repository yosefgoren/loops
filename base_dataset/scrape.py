import re
import abc
import random
from typing import Any
from utils.serialize import *
import click

FOR_PAT = r'\bfor\b'

DELIMITERS: list[ScopeDelimiter] = [
    ScopeDelimiter("\"", "\"", True, False, ContextType.QUOTES),
    ScopeDelimiter("/*", "*/", True, False, ContextType.MULTICOMMENT),
    ScopeDelimiter("//", "\n", True, False, ContextType.UNICOMMENT),
    ScopeDelimiter("#pragma", "\n", True, True, ContextType.PRAGMA),
    ScopeDelimiter("(", ")", False, True, ContextType.COLONS),
    ScopeDelimiter("{", "}", False, True, ContextType.BRACES),
]

class Disq(abc.ABC):
    """Disqulifier"""
    @abc.abstractmethod
    def check(self, pos: FilePosition) -> bool:
        pass

@dataclass
class PrefixDisq(Disq):
    prefix: str
    
    def check(self, pos: FilePosition) -> bool:
        lineno, lineoff = resolve_lineno(pos.file, pos.offset)
        line = open(pos.file, 'r').readlines()[lineno]
        return self.prefix in line[:lineoff]

disqs: list[Disq] = [
    PrefixDisq("#pragma omp "),
    PrefixDisq(" * "),
    PrefixDisq("printf(\""),
    PrefixDisq("/*")
]
found_loops: list[FilePosition] = []
found_scopes: list[CodeScope] = []

def find_next_token_offset(text: str, tokens: list[str]) -> tuple[int, list[int]]:
    """returns (offset, matching_token_indices)"""
    i = 0
    while i < len(text):
        matching_token_indices = [idx for idx, token in enumerate(tokens) if token == text[i]]
        if len(matching_token_indices) > 0:
            return i, matching_token_indices
        i += 1
    return -1, []

def process_chunk(chunk: str, path: str, file_off: int) -> None:
    """
    This function goes over the provided chunck of code and searches for any 'for' loops within.
    This is done by first finding all instances of the string 'for', then disqualifying all instances
        of the 'for' string which are not actually a syntactic 'for' loop.
    For example. `#pragma omp for` is not a syntactic 'for' loop,
        thus any instance of the 'for' string which is prefixed by `#pragma omp `
        is disqualified (note there is no newline in the prefix).
    """
    for match in re.finditer(FOR_PAT, chunk):
        pos = FilePosition(path, file_off + match.span()[0])
        if not any([dis.check(pos) for dis in disqs]):    
            found_loops.append(pos)

def printpos(path: str, file_offset: int) -> None:
    print(FilePosition(path, file_offset))

class FileSeek:
    def __init__(self, path) -> None:
        self.file_offset: int = 0
        self.remain_txt: str = open(path, 'r').read()
        self.path: str = path
    
    def advance(self, n: int) -> None:
        self.remain_txt = self.remain_txt[n:]
        self.file_offset += n
        # print(f"Advanced to: {FilePosition(self.path, self.file_offset)}")
    
@click.command()
@click.option('-i', '--input', required=True, type=str, help="A code file to be parsed")
@click.option('-o', '--output', required=True, type=str, help="A json file with information about all scopes found in code")
def scrape(input: str, output: str):
    print(f"parsing {input}")
    seek = FileSeek(input)
    context_stack: list[ScopeContext] = []
    
    start_tokens: list[str] = [delim.start[0] for delim in DELIMITERS] + [delim.end[0] for delim in DELIMITERS if not delim.bully]
    start_delims: list[ScopeDelimiter] = DELIMITERS + [delim for delim in DELIMITERS if not delim.bully]
    while True:
        token_offset, token_indices = find_next_token_offset(seek.remain_txt, start_tokens)
        
        if token_offset == -1:
            process_chunk(seek.remain_txt, input, seek.file_offset)
            break

        chunk = seek.remain_txt[:token_offset]
        process_chunk(chunk, input, seek.file_offset)
        seek.advance(token_offset)
        delim_found = False
        for delim in [start_delims[idx] for idx in token_indices]:
            if seek.remain_txt.startswith(delim.start):
                if delim.bully:
                    scope_start_pos = FilePosition(input, seek.file_offset)
                    seek.advance(len(delim.start))
                    end_offset = seek.remain_txt.find(delim.end)
                    seek.advance(end_offset+len(delim.end))
                    scope_end_pos = FilePosition(input, seek.file_offset)
                    if delim.do_save:
                        found_scopes.append(CodeScope(delim.context_type, scope_start_pos, scope_end_pos))
                else:
                    if delim.do_save:
                        context_stack.append(ScopeContext(delim.context_type, FilePosition(input, seek.file_offset)))
                    seek.advance(len(delim.start))
                delim_found = True
            elif seek.remain_txt.startswith(delim.end) and not delim.bully:
                if len(context_stack) == 0:
                    raise RuntimeError(f"a {delim.context_type} scoped ended but scope stack is empty")
                if delim.do_save:
                    top_scope = context_stack.pop()
                    if top_scope.context_type != delim.context_type:
                        printpos(input, seek.file_offset)
                        raise RuntimeError(f"Top scope is {top_scope.context_type}, but a {delim.context_type} scope just ended.")
                    found_scopes.append(CodeScope(top_scope.context_type, top_scope.pos, FilePosition(input, seek.file_offset)))
                seek.advance(len(delim.end))
                delim_found = True
        
        if not delim_found:
            seek.advance(1) # Token was no associated with any scope, skip it
        
    founds: list[list[Any]] = [found_loops, found_scopes]
    for found in founds:
        print("\n".join([f"{found[random.randint(0, len(found)-1)]}" for _ in range(min(20, len(found)))]))

    dump_scopes_file(output, (found_loops, found_scopes))
    
if __name__ == "__main__":
    scrape()