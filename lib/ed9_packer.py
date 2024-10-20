import json
import zlib

import lib.packer as packer

MASK = 0xFFFFFFFF


def get_hash(text: str):
    crc = zlib.crc32(text.encode("utf8"))
    return crc ^ MASK


def pack_table(tbl_data: list, game: str):
    header_data = b"#TBL"
    entry_data = b""
    pointer_data = b""

    header_count = len(tbl_data)
    header_data += header_count.to_bytes(4, "little")
    start_offset = 8 + 80 * header_count
    pointer_start = start_offset
    for header_info in tbl_data:
        pointer_start += int(header_info["entry_length"]) * len(header_info["entries"])

    for header_info in tbl_data:
        header_name = str(header_info["header_name"])
        entry_length = int(header_info["entry_length"])
        entries = list(header_info["entries"])
        entry_count = len(entries)
        schema_version = int(header_info["version"])
        print(header_name)
        encoded_name = header_name.encode("utf8")
        while len(encoded_name) < 64:
            encoded_name += b"\0"
        header_data += encoded_name
        header_data += get_hash(header_name).to_bytes(4, "little")
        header_data += start_offset.to_bytes(4, "little")
        header_data += entry_length.to_bytes(4, "little")
        header_data += entry_count.to_bytes(4, "little")
        start_offset += entry_count * entry_length

        if schema_version == 0:
            schema = {}
        else:
            with open(f"schemas/{game}/{header_name}.json") as schema_file:
                schema_data = json.load(schema_file)
                version = int(schema_data["version"])
                assert version == schema_version
                schema = dict(schema_data["schema"])

        for entry in entries:
            new_entry_data, pointer_data = pack_entry(entry, schema, pointer_start, pointer_data, entry_length)
            entry_data += new_entry_data

    return header_data + entry_data + pointer_data


def pack_entry(entry: dict, schema: dict, pointer_start: int, pointer_data: bytearray, expected_length: int):
    result = b""
    for schema_key, schema_type in schema.items():
        data = entry[schema_key]
        result_data, pointer_data = packer.pack(data, schema_type, pointer_start, pointer_data)
        result += result_data

    if "extra" in entry:
        result += bytes.fromhex(entry["extra"])
    assert len(result) == expected_length
    return result, pointer_data
