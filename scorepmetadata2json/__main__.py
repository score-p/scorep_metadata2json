import logging
import json
from pathlib import Path
import argparse

from scorepmetadata2json.basemodel import Metadata
from scorepmetadata2json.parser import parse_metadata


def main() -> None:
    """
    Main entry point.

    :return: None
    """
    args = parse_args()
    if args.schema:
        print(json.dumps(Metadata.model_json_schema(), indent=2))
        return

    file_content = Path(args.file).read_text(encoding="utf-8")
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    metadata = parse_metadata(file_content)
    print(json.dumps(metadata.model_dump(), indent=2))


def parse_args() -> argparse.Namespace:
    """
    Parse the command line arguments.

    :return: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Parse a Score-P Metadata File (scorep.fair) into a JSON format."
    )

    # Creating a mutually exclusive group
    group = parser.add_mutually_exclusive_group(required=True)

    # Adding arguments to the mutually exclusive group
    group.add_argument("file", type=str, nargs="?", help="The file to parse.")
    group.add_argument(
        "--schema", action="store_true", help="Print the schema to stdout."
    )

    # Regular argument (not in the mutually exclusive group)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    return parser.parse_args()


if __name__ == "__main__":
    main()
