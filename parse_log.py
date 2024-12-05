import struct
from dataclasses import dataclass
from typing import List

# Define the Timestamp dataclass
@dataclass
class Timestamp:
    time: float  # Time in seconds
    id: int      # User-provided ID

def parse(filename: str) -> List[Timestamp]:
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

if __name__ == "__main__":
    # Example usage
    log_file = "main.times"
    parsed_timestamps = parse(log_file)

    # Display the parsed timestamps
    for timestamp in parsed_timestamps:
        print(timestamp)
