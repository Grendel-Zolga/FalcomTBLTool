import json
import os
import zlib
from io import BufferedReader

import lib.parser as parser

MASK = 0xFFFFFFFF


def get_hash(text: str):
    crc = zlib.crc32(text.encode("utf8"))
    return crc ^ MASK


def parse_table(tbl_data: BufferedReader, game: str):
    result = list()
    start_offsets = list()
    entry_counts = list()

    magic = tbl_data.read(4)
    assert magic == b"#TBL"
    header_count = int.from_bytes(tbl_data.read(4), "little")
    for _ in range(header_count):
        start_offset, entry_count, header = parse_header(tbl_data)
        start_offsets.append(start_offset)
        entry_counts.append(entry_count)
        result.append(header)

    for i, header in enumerate(result):
        print(header)
        header_name = header["header_name"]
        # print(f"{start_offsets[i]=}, {header['entry_count']=}, {header['entry_length']=}")
        tbl_data.seek(start_offsets[i])
        if os.path.exists(f"schemas/{game}/{header_name}.json"):
            print(f"Schema for {header_name} found")
            with open(f"schemas/{game}/{header_name}.json") as schema_file:
                data = json.load(schema_file)
                version = data["version"]
                schema = data["schema"]
        else:
            version = 0
            schema = {}
        print(schema)
        header["version"] = version
        header["entries"] = list()
        for _ in range(entry_counts[i]):
            entry = parse_entry(tbl_data, schema, header["entry_length"])
            header["entries"].append(entry)

    return result


def parse_header(input_stream: BufferedReader):
    header_name = input_stream.read(64).replace(b"\0", b"").decode("utf8")
    input_stream.read(4)  # Skip over the hash
    start_offset = int.from_bytes(input_stream.read(4), "little")
    entry_length = int.from_bytes(input_stream.read(4), "little")
    entry_count = int.from_bytes(input_stream.read(4), "little")

    result = {"header_name": header_name, "entry_length": entry_length}
    return start_offset, entry_count, result


def parse_entry(input_stream: BufferedReader, schema: dict, expected: int):
    entry = dict()
    actual = 0
    for k, v in schema.items():
        length, result = parser.parse(input_stream, v)
        actual += length
        entry[k] = result
    assert actual <= expected
    if actual < expected:
        entry["extra"] = parser.parse_data(input_stream, expected - actual)[1]
    return entry
