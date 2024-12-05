import struct
from dataclasses import dataclass
import click
from serial import *

# Define the Timestamp dataclass
@dataclass
class Timestamp:
    time: float  # Time in seconds
    id: int      # User-provided ID

def parse_times(filename: str) -> list[Timestamp]:
    """
    Parse the binary log file and return a list of Timestamp objects.

    :param filename: Path to the binary log file.
    :return: List of Timestamp objects.
    """
    timestamps = []

    # Structure format: 'di' corresponds to double (time) and int (ID)
    struct_format = "dQ"
    entry_size = struct.calcsize(struct_format)

    try:
        with open(filename, "rb") as f:
            while True:
                # Read a single log entry
                entry_data = f.read(entry_size)
                if not entry_data:
                    break  # EOF

                # Unpack the binary data into a tuple
                time, id = struct.unpack(struct_format, entry_data)

                # Create a Timestamp object and append to the list
                timestamps.append(Timestamp(time=time, id=id))

    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
    except Exception as e:
        print(f"Error reading file {filename}: {e}")

    return timestamps

@click.command()
@click.argument("basename", type=str)
def collect(basename: str):
    # Example usage
    times_file = f"{basename}.times"
    src_code_file = f"{basename}.cpp"

    parsed_timestamps: list[Timestamp] = parse_times(times_file)
    times_dict = {stamp.id: stamp.time for stamp in parsed_timestamps}
    
    targets: list[ForLoop] = load_targets_file(basename)
    assert len(targets) > 0
    assert src_code_file == targets[0].for_token.file
    full_src_code: str = open(src_code_file, 'r').read()
    samples: list[LoopSample] = []
    
    for tgt in targets:
        start_time: float = times_dict[tgt.ident*2]
        end_time: float = times_dict[tgt.ident*2 + 1]
        duration: float = end_time - start_time
        samples.append(LoopSample(
            tgt,
            full_src_code[tgt.for_token.offset:tgt.scope.end_pos.offset],
            duration,
        ))
    
    dump_samples_file(basename, samples)

if __name__ == "__main__":
    collect()