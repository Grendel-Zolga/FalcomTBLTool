import argparse
import json
import os
import sys

from lib.schema_util import update_schema
from lib.ed9_parser import parse_table
from lib.ed9_packer import pack_table

GAME_TABLE = {"kuro": "ed9_Daybreak1", "kuro1": "ed9_Daybreak1", "daybreak": "ed9_Daybreak1", "daybreak1": "ed9_Daybreak1", "ed9_1": "ed9_Daybreak1", "ysx": "ys_X", "ys_x": "ys_X"}


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        self.exit(2, "%s: error: %s\n" % (self.prog, message))


def init_args():
    parser = ArgumentParser(prog="FalcomTBLTool", description="Tools for working with Falcom tbl format", add_help=True)
    subparsers = parser.add_subparsers(dest="command")

    parser_tbl2json = subparsers.add_parser("tbl2json", help="Convert TBL to JSON")
    parser_tbl2json.add_argument("game", help="Game schema to use")
    parser_tbl2json.add_argument("tblfile", help="Name of tbl file")
    parser_tbl2json.add_argument("outputfile", nargs="?", default=None, help="Optional. Name of output file")

    parser_json2tbl = subparsers.add_parser("json2tbl", help="Convert JSON to TBL")
    parser_json2tbl.add_argument("game", help="Game schema to use")
    parser_json2tbl.add_argument("jsonfile", help="Name of json file")
    parser_json2tbl.add_argument("outputfile", nargs="?", default=None, help="Optional. Name of output file")

    parser_schema = subparsers.add_parser("update", help="Fetch and update schema")
    parser_schema.add_argument("game", help="Game to update schema")

    return parser


if __name__ == "__main__":
    parser = init_args()
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    print(args)

    command: str = args.command
    game: str = args.game.lower().strip()
    print(f"{game=}")
    if game not in GAME_TABLE and game != "custom":
        print(f"Invalid game name. Possible values are: {list(GAME_TABLE.keys()) + ['custom']}")
        sys.exit(1)

    game = GAME_TABLE[game]

    if not os.path.exists(f"schemas/{game}"):
        if game.lower() == "custom":
            print("Custom schema currently unsupported")
            sys.exit(1)
        else:
            print(f"Schema not downloaded for {game}. Downloading...")
            update_schema(game)

    print(f"Starting command {command}")
    if command == "update":
        update_schema(game)

    if command == "tbl2json":
        tbl_file: str = args.tblfile
        output_file: str = args.outputfile

        if output_file is None:
            output_file = f"{tbl_file.rsplit('.', maxsplit=1)[0]}.json"

        with open(tbl_file, "rb") as input_data, open(output_file, "w", encoding="utf8") as output:
            json.dump(parse_table(input_data, game), output, ensure_ascii=False, indent=4)

    if command == "json2tbl":
        json_file: str = args.jsonfile
        output_file: str = args.outputfile

        if output_file is None:
            output_file = f"{json_file.rsplit('.', maxsplit=1)[0]}.tbl"

        with open(json_file, encoding="utf-8") as input_data, open(output_file, "wb") as output:
            output.write(pack_table(json.load(input_data), game))

    print("DONE")
