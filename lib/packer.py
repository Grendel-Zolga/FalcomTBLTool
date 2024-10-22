import json
import os
import struct


def pack_int(input_data: int, length: int, signed: bool, pointer_data: bytes):
    return input_data.to_bytes(length, "little", signed=signed), pointer_data


def pack_float(input_data: float, length: int, pointer_data: bytes):
    if length == 4:
        return struct.pack("<f", input_data), pointer_data
    return struct.pack("<d", input_data), pointer_data


def pack_data(input_data: str, pointer_data: bytes):
    return bytes.fromhex(input_data), pointer_data


def pack_str(input_data: str, encoding: str, pointer_data: bytes):
    return input_data.encode(encoding) + b"\0", pointer_data


def pack_pointer(input_data, schema_type: str, pointer_start: int, pointer_data: bytes):
    pointer = pointer_start + len(pointer_data)
    result = pointer.to_bytes(8, "little")
    new_pointer_data, pointer_data = pack(input_data, schema_type, pointer_start, pointer_data)
    pointer_data += new_pointer_data
    return result, pointer_data


def pack_array(input_data: list, schema_type: str, pointer_start: int, pointer_data: bytes):
    pointer = pointer_start + len(pointer_data)

    if schema_type.startswith(("u", "s", "f")):
        length = int(schema_type[1:]) // 8
        while pointer % length != 0:
            pointer += 1
            pointer_data += b"\0"

    result = pointer.to_bytes(8, "little")
    result += len(input_data).to_bytes(4, "little")

    for data in input_data:
        new_pointer_data, pointer_data = pack(data, schema_type, pointer_start, pointer_data)
        pointer_data += new_pointer_data
    return result, pointer_data


def pack_dict(input_data: dict, schema: dict, pointer_start: int, pointer_data: bytes):
    result = b""
    for schema_key, schema_type in schema.items():
        data = input_data[schema_key]
        result_data, pointer_data = pack(data, schema_type, pointer_start, pointer_data)
        result += result_data
    return result, pointer_data


def pack_ref(input_data: dict, reference_type: str, pointer_start: int, pointer_data: bytes):
    assert os.path.exists(f"schemas/common/{reference_type}.json")
    with open(f"schemas/common/{reference_type}.json") as schema_file:
        data = json.load(schema_file)
        version = data["version"]
        assert version == input_data["version"]
        schema = data["schema"]
    return pack_dict(input_data["data"], schema, pointer_start, pointer_data)


def pack(input_data, schema_type: str | dict, pointer_start: int, pointer_data: bytes):
    if isinstance(schema_type, dict):
        if "repeat" in schema_type:
            print(f"Repeat input data: {input_data}")
            results = b""
            for data in input_data:
                if isinstance(schema_type["type"], dict):
                    result, pointer_data = pack_dict(data, schema_type["type"], pointer_start, pointer_data)
                else:
                    result, pointer_data = pack(data, schema_type["type"], pointer_start, pointer_data)
                results += result
            return results, pointer_data
        else:
            if isinstance(schema_type["type"], dict):
                result, pointer_data = pack_dict(input_data, schema_type["type"], pointer_start, pointer_data)
            else:
                result, pointer_data = pack(input_data, schema_type["type"], pointer_start, pointer_data)
            return result, pointer_data
    if schema_type.startswith("str"):
        _, encoding = schema_type.rsplit("_", maxsplit=1)
        return pack_str(input_data, encoding, pointer_data)
    if schema_type.startswith("u"):
        length = int(schema_type[1:]) // 8
        return pack_int(input_data, length, False, pointer_data)
    if schema_type.startswith("s"):
        length = int(schema_type[1:]) // 8
        return pack_int(input_data, length, True, pointer_data)
    if schema_type.startswith("f"):
        length = int(schema_type[1:]) // 8
        return pack_float(input_data, length, pointer_data)
    if schema_type.startswith("d"):
        return pack_data(input_data, pointer_data)
    if schema_type.startswith("ptr"):
        return pack_pointer(input_data, schema_type[4:], pointer_start, pointer_data)
    if schema_type.startswith("arr"):
        return pack_array(input_data, schema_type[4:], pointer_start, pointer_data)
    if schema_type.startswith("ref"):
        return pack_ref(input_data, schema_type[4:], pointer_start, pointer_data)
    raise Exception(f"Unknown Data Type {schema_type}")
