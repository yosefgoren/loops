from dataclasses import dataclass
from enum import Enum
from utils.indexed_file import resolve_lineno
import json

class ContextType(Enum):
    QUOTES = "quotes"
    MULTICOMMENT = "multicomment"
    UNICOMMENT = "unicomment"
    COLONS = "colons"
    BRACES = "braces"

@dataclass
class FilePosition:
    """
    Line number and offset are counted from 0
    """
    
    file: str
    offset: int
    
    def __str__(self) -> str:
        lineno, lineoff = resolve_lineno(self.file, self.offset)
        return f"{self.file}:{lineno+1}:{lineoff+1} ({self.offset})"

    
    # Comparison operator to check if one FilePosition is before another
    def __lt__(self, other: "FilePosition") -> bool:
        if self.file == other.file:
            return self.offset < other.offset
        return self.file < other.file  # Compare filenames lexicographically

    def serialize(self) -> dict[str, object]:
        return {
            "file": self.file,
            "offset": self.offset
        }
    
    @staticmethod
    def from_serial(data: dict[str, object]):
        return FilePosition(data["file"], data["offset"]) # type: ignore[arg-type]


@dataclass
class ScopeDelimiter:
    """Information for parsing a scoped context such as (*), '*' e.t.c."""
    start: str
    end: str
    bully: bool
    context_type: ContextType

@dataclass
class ScopeContext:
    context_type: ContextType
    pos: FilePosition    

@dataclass
class CodeScope:
    context_type: ContextType
    start_pos: FilePosition
    end_pos: FilePosition
    
    def __str__(self) -> str:
        return f"{self.context_type}: {self.start_pos} - {self.end_pos}"

    def serialize(self) -> dict[str, object]:
        return {
            "context_type": self.context_type.value,
            "start_pos": self.start_pos.serialize(),
            "end_pos": self.end_pos.serialize(),
        }

    @staticmethod
    def from_serial(data: dict[str, object]):
        return CodeScope(
            ContextType(data["context_type"]), # type: ignore[arg-type]
            FilePosition.from_serial(data["start_pos"]), # type: ignore[arg-type]
            FilePosition.from_serial(data["end_pos"]), # type: ignore[arg-type]
        )

def dump_scopes_file(path: str, values: tuple[list[FilePosition], list[CodeScope]]) -> None:
    result = {
        "loops": [res.serialize() for res in values[0]],
        "scopes": [res.serialize() for res in values[1]]
    }
    json.dump(result, open(path, 'w'), indent=4)


def load_scopes_file(path: str) -> tuple[list[FilePosition], list[CodeScope]]:
    assert path.endswith('.json')
    data = json.load(open(path, 'r'))
    loops: list[FilePosition] = [FilePosition.from_serial(elem) for elem in data["loops"]]
    scopes: list[CodeScope] = [CodeScope.from_serial(elem) for elem in data["scopes"]]
    return loops, scopes

@dataclass
class ForLoop:
    for_token: FilePosition
    scope: CodeScope
    ident: int

    def __str__(self) -> str:
        return f"For loop {self.ident} at {self.for_token}, Scope {self.scope}"
    
    def serialize(self) -> dict[str, object]:
        return {
            "for_token": self.for_token.serialize(),
            "scope": self.scope.serialize(),
            "ident": self.ident
        }
    
    @staticmethod
    def from_serial(data: dict[str, object]):
        return ForLoop(
            FilePosition.from_serial(data["for_token"]), # type: ignore[arg-type]
            CodeScope.from_serial(data["scope"]), # type: ignore[arg-type]
            data["ident"], # type: ignore[arg-type]
        )
    
def dump_targets_file(path: str, targets: list[ForLoop]) -> None:
    json.dump([loop.serialize() for loop in targets], open(path, 'w'), indent=4)

def load_targets_file(path: str) -> list[ForLoop]:
    assert path.endswith('.json')
    data = json.load(open(path, 'r'))
    return [ForLoop.from_serial(raw_loop) for raw_loop in data]

@dataclass
class LoopSample:
    loop: ForLoop
    raw_code: str
    duration: float | None

    def __str__(self) -> str:
        return f"Sample: '{self.loop}' took {self.duration:.4} seconds"

    def serialize(self) -> dict[str, object]:
        return {
            "loop": self.loop.serialize(),
            "raw_code": self.raw_code,
            "duration": self.duration,
        }
    
    @staticmethod
    def from_serial(data: dict[str, object]):
        return LoopSample(
            ForLoop.from_serial(data["loop"]), # type: ignore[arg-type]
            data["raw_code"], # type: ignore[arg-type]
            data["duration"], # type: ignore[arg-type]
        )

def dump_samples_file(path: str, samples: list[LoopSample]) -> None:
    json.dump([s.serialize() for s in samples], open(path, 'w'), indent=4)

def load_samples_file(path: str) -> list[LoopSample]:
    assert path.endswith('.json')
    data = json.load(open(path, 'r'))
    return [LoopSample.from_serial(s) for s in data]