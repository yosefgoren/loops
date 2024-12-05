from math import floor

class IndexedFile:
    def __init__(self, path: str):
        self.path = path
        self.lines = open(self.path, 'r').read().splitlines(keepends=True)
        self.line_start_offsets = [0]
        for line in self.lines:
            self.line_start_offsets.append(self.line_start_offsets[-1] + len(line))
    
    def _bin_search_line_off(self, file_offset: int) -> int:
        """returns the index of the line in which the file offset is contained"""
        if file_offset == 8:
            pass
        first_idx, last_idx = 0, len(self.line_start_offsets)-1
        first_off = self.line_start_offsets[first_idx]
        last_off = self.line_start_offsets[last_idx]
        if not (first_off <= file_offset and file_offset <= last_off):
            raise RuntimeError(f"Requested offset '{file_offset}' is not in file '{self.path}'")
        while last_idx - first_idx > 1:
            mid_idx = floor((first_idx+last_idx+1)/2)
            mid_off = self.line_start_offsets[mid_idx]
            if file_offset <= mid_off:
                # In first half, decrease last:
                last_idx = mid_idx
            else:
                # In second half, increase first:
                first_idx = mid_idx
        return first_idx
    
    def find_line(self, file_offset: int) -> tuple[int, int]:
        lineno = self._bin_search_line_off(file_offset)
        line_start_off = self.line_start_offsets[lineno]
        return lineno, file_offset-line_start_off

indexed_files_cache: dict[str, IndexedFile] = dict()
def index_file(path: str) -> IndexedFile:
    if path not in indexed_files_cache.keys():
        indexed_files_cache[path] = IndexedFile(path)
    return indexed_files_cache[path]

def resolve_lineno(path: str, file_offset: int) -> tuple[int, int]:
    """returns line number of line offset"""
    return index_file(path).find_line(file_offset)
