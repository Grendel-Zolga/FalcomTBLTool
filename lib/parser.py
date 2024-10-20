import json
import os
import struct
from io import BufferedReader


def parse_int(input_stream: BufferedReader, length: int, signed: bool):
    return length, int.from_bytes(input_stream.read(length), "little", signed=signed)


def parse_float(input_stream: BufferedReader, length: int):
    if length == 4:
        return length, struct.unpack("<f", input_stream.read(4))[0]
    return length, struct.unpack("<d", input_stream.read(8))[0]


def parse_data(input_stream: BufferedReader, length: int):
    return length, input_stream.read(length).hex(bytes_per_sep=1, sep=" ").upper()


def parse_str(input_stream: BufferedReader, encoding: str):
    length = 1
    output = input_stream.read(1)
    while not output.endswith(b"\0"):
        length += 1
        output += input_stream.read(1)
    return length, output.replace(b"\0", b"").decode(encoding)


def parse_pointer(input_stream: BufferedReader, schema_type: str):
    new_pos = int.from_bytes(input_stream.read(8), "little")
    current_pos = input_stream.tell()
    input_stream.seek(new_pos, 0)
    _, result = parse(input_stream, schema_type)
    input_stream.seek(current_pos, 0)
    return 8, result


def parse_array(input_stream: BufferedReader, schema_type: str):
    new_pos = int.from_bytes(input_stream.read(8), "little")
    rep = int.from_bytes(input_stream.read(4), "little")
    current_pos = input_stream.tell()
    input_stream.seek(new_pos, 0)
    results = list()
    for _ in range(rep):
        result = parse(input_stream, schema_type)[1]
        results.append(result)
    input_stream.seek(current_pos, 0)
    return 12, results


def parse_dict(input_stream: BufferedReader, schema: dict):
    result = dict()
    length = 0
    for k, v in schema.items():
        dict_length, dict_result = parse(input_stream, v)
        length += dict_length
        result[k] = dict_result
    return length, result


def parse_ref(input_stream: BufferedReader, reference_type: str):
    result = dict()
    assert os.path.exists(f"schemas/common/{reference_type}.json")
    with open(f"schemas/common/{reference_type}.json") as schema_file:
        data = json.load(schema_file)
        version = data["version"]
        schema = data["schema"]
    result["version"] = version
    length, result_data = parse_dict(input_stream, schema)
    result["data"] = result_data
    return length, result


def parse(input_stream: BufferedReader, schema_type: str | dict):
    if isinstance(schema_type, dict):
        total_size = 0
        if "repeat" in schema_type:
            results = list()
            for _ in range(schema_type["repeat"]):
                if isinstance(schema_type["type"], dict):
                    length, result = parse_dict(input_stream, schema_type["type"])
                else:
                    length, result = parse(input_stream, schema_type["type"])
                total_size += length
                results.append(result)
            return total_size, results
        else:
            if isinstance(schema_type["type"], dict):
                length, result = parse_dict(input_stream, schema_type["type"])
            else:
                length, result = parse(input_stream, schema_type["type"])
            total_size += length
            return length, result
    if schema_type.startswith("str"):
        _, encoding = schema_type.rsplit("_", maxsplit=1)
        return parse_str(input_stream, encoding)
    if schema_type.startswith("u"):
        length = int(schema_type[1:]) // 8
        return parse_int(input_stream, length, False)
    if schema_type.startswith("s"):
        length = int(schema_type[1:]) // 8
        return parse_int(input_stream, length, True)
    if schema_type.startswith("f"):
        length = int(schema_type[1:]) // 8
        return parse_float(input_stream, length)
    if schema_type.startswith("d"):
        return parse_data(input_stream, int(schema_type[1:]))
    if schema_type.startswith("ptr"):
        return parse_pointer(input_stream, schema_type[4:])
    if schema_type.startswith("arr"):
        return parse_array(input_stream, schema_type[4:])
    if schema_type.startswith("ref"):
        return parse_ref(input_stream, schema_type[4:])
    raise Exception(f"Unknown Data Type {schema_type}")
