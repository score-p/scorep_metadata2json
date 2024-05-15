from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Dict
import logging
from .basemodel import LinkedType, Object, Instrumenter, Runtime, Metadata


class ParsingContext:
    """
    Holds the context for parsing operations.
    The context consists of an array of lines and the current index of that array.
    The index is used to keep track of the current line. It defaults to 0.
    """

    def __init__(self, lines: List[str], current_index: int = 0):
        self.lines = lines
        self.current_index = current_index

    def get_current_line(self) -> str:
        """
        Returns the current line.

        :return: The current line.
        :rtype: str
        """
        return (
            self.lines[self.current_index].strip()
            if self.current_index < len(self.lines)
            else ""
        )

    def advance(self, steps: int = 1) -> "ParsingContext":
        """
        Advances the current index by the given number of steps.
        It returns itself to allow chaining.

        :param steps: The number of steps to advance. The default is 1.
        :type steps: int
        :return: self
        :rtype: ParsingContext
        """
        self.current_index = min(self.current_index + steps, len(self.lines))
        return self

    def has_more_lines(self) -> bool:
        """
        Checks if there are more lines to parse.

        :returns: True if there are more lines to parse, False otherwise.
        :rtype: bool
        """
        return self.current_index < len(self.lines)

    def copy(self) -> "ParsingContext":
        """
        Creates a copy of the current ParsingContext with the same lines and current index.

        :returns: A copy of the current ParsingContext.
        :rtype: ParsingContext
        """
        return ParsingContext(self.lines, self.current_index)


@dataclass(frozen=True)
class CommonAttributes:
    """
    Holds the common attributes of an object, executable, or runtime.
    """

    env: Dict[str, Optional[str]]
    compiler: str
    define_flags: List[str]
    compiler_flags: List[str]
    library_files: List[str]


class PathLikeParseType(Enum):
    """
    Enum for the different path-like types that can be parsed.
    """
    SINGLE_LINE_MULTIPLE_ELEMENTS = auto()
    MULTIPLE_LINES_SINGLE_ELEMENT = auto()


class TopLevelSectionNames(str, Enum):
    RUNTIME = "runtime"
    INSTRUMENTER = "instrumenter"
    EXECUTABLE = "executable "
    SHARED_LIBRARY = "shared-library "
    OBJECT = "object "
    SOURCE = "source "


def parse_env_variables(context: ParsingContext) -> Dict[str, Optional[str]]:
    """
    Parses environment variables from the lines of the file.
    """
    env: Dict[str, Optional[str]] = {}

    while context.has_more_lines():
        line = context.get_current_line()
        if is_new_section(line):
            # We reached the end of the environment variables section for this section.
            break

        if line.startswith("unset "):
            # We found an unset environment variable.
            key = line.split()[1]
            env[key] = None

        elif line.startswith("set "):
            # We found a set environment variable (but might be empty).
            line_split = line.split(maxsplit=3)
            key = line_split[-2]
            value = line_split[-1]
            env[key] = value

        context.advance()

    return env


def parse_path_like(context: ParsingContext, keyword: str,
                    kind: PathLikeParseType = PathLikeParseType.SINGLE_LINE_MULTIPLE_ELEMENTS,
                    with_bytesize: bool = True) -> List[str]:
    """
    Parses a pathlike string.

    :param context: ParsingContext to search in.
    :type context: ParsingContext
    :return: The value searched for.
    :rtype: str
    """
    return_value = []
    while context.has_more_lines():
        line = context.get_current_line()
        if is_new_section(line):
            break

        if line.startswith(keyword):
            line_split = line.strip().split(maxsplit=2)

            if with_bytesize:  # Sanity Check for Bytesize

                if (len(line_split) == 2) and (int(line_split[1]) != 0):
                    raise ValueError(f"Expected 0, got {line_split[1]}")

                if (len(line_split) == 3) and (int(line_split[1]) == 0):
                    raise ValueError(f"Expected not '0' , got {line_split[1]}")

            if ((len(line_split) == 3)
                    or (len(line_split) == 2 and with_bytesize is False)):
                if kind == PathLikeParseType.SINGLE_LINE_MULTIPLE_ELEMENTS:
                    value = line_split[-1].split()
                    return_value = [val.strip() for val in value]
                    # We found the keyword, so we can stop searching.
                    break

                elif kind == PathLikeParseType.MULTIPLE_LINES_SINGLE_ELEMENT:
                    value = line_split[-1]
                    return_value.append(value.strip())

                else:
                    raise ValueError(f"Unknown kind: {kind}")
        context.advance()

    return return_value if return_value != [] else [""]


def is_new_section(line: str) -> bool:
    """
    Checks if the given line marks the start of a new section.

    :param line: The line to check.
    :type line: str
    :return: True if the line marks the start of a new section, False otherwise.
    :rtype: bool
    """
    return any(
        line.startswith(keyword)
        for keyword in [
            e.value for e in TopLevelSectionNames
        ]
    )


def parse_common_attributes(context: ParsingContext) -> CommonAttributes:
    """
    Parses the common attributes of an object, executable, or runtime.

    :param context: ParsingContext to search in.
    :type context: ParsingContext
    :return: The common attributes.
    :rtype: CommonAttributes
    """

    env = parse_env_variables(context.copy())
    compiler = parse_path_like(context.copy(), "compiler ")
    define_flags = parse_path_like(context.copy(), "define-flags ")
    compiler_flags = parse_path_like(context.copy(), "compiler-flags ")
    library_files = parse_path_like(context.copy(), "library-files ")

    return CommonAttributes(
        env=env,
        compiler=compiler[0],  # compiler is a list of one element
        define_flags=define_flags,
        compiler_flags=compiler_flags,
        library_files=library_files,
    )


def parse_metadata(file_content: str) -> Metadata:
    """
    Parses the metadata from the given file content.

    :param file_content: The content of the file to parse.
    :type file_content: str
    :return: The parsed metadata.
    :rtype: Metadata
    """
    lines = file_content.strip().split("\n")

    context = ParsingContext(lines)
    type_of_linked_type = None
    objects = []
    runtime = None
    linked_type = None

    while context.has_more_lines():
        line = context.get_current_line()

        logging.debug(f"Parsing line: {line}")

        if line.startswith(TopLevelSectionNames.RUNTIME):
            context.advance()
            logging.debug("Parsing runtime")
            common_attributes = parse_common_attributes(context.copy())
            run_id: str = parse_path_like(context.copy(), "run-id",
                                          with_bytesize=False)[0]  # Get first element (there should be only 1)
            runtime = Runtime(
                id=run_id,
                date=run_id.split("_")[2],
                env=common_attributes.env
            )

        elif line.startswith(TopLevelSectionNames.EXECUTABLE) or \
                line.startswith(TopLevelSectionNames.SHARED_LIBRARY):
            logging.debug(f"Parsing '{line}'")

            type_of_linked_type = TopLevelSectionNames.EXECUTABLE if line.startswith(
                TopLevelSectionNames.EXECUTABLE) else TopLevelSectionNames.SHARED_LIBRARY

            context.advance()
            common_attributes = parse_common_attributes(context.copy())

            object_files = parse_path_like(context.copy(), "object-file ",
                                           PathLikeParseType.MULTIPLE_LINES_SINGLE_ELEMENT)
            link_id: str = parse_path_like(context.copy(), "compile-id",
                                              with_bytesize=False)[0]  # Get first element (there should be only 1)
            linked_type = LinkedType(
                id=link_id,
                date=link_id.split("_")[2],
                compiler=common_attributes.compiler,
                define_flags=common_attributes.define_flags,
                compiler_flags=common_attributes.compiler_flags,
                library_files=common_attributes.library_files,
                object_files=object_files,
                env=common_attributes.env,
            )

        elif line.startswith(TopLevelSectionNames.OBJECT):
            logging.debug(f"Parsing object: {line.split()[-1]}")
            context.advance()

            common_attributes = parse_common_attributes(context.copy())

            source_files = parse_path_like(context.copy(), "source-file")
            source_language = parse_path_like(context.copy(), "source-language",
                                              with_bytesize=False)[0]  # Get first element (there should be only 1)
            compile_id: str = parse_path_like(context.copy(), "compile-id",
                                              with_bytesize=False)[0]  # Get first element (there should be only 1)
            objects.append(
                Object(
                    id=compile_id,
                    date=compile_id.split("_")[2],
                    compiler=common_attributes.compiler,
                    define_flags=common_attributes.define_flags,
                    compiler_flags=common_attributes.compiler_flags,
                    library_files=common_attributes.library_files,
                    source_files=source_files,
                    source_language=source_language,
                    env=common_attributes.env,
                )
            )

        else:
            # We don't know what to do with this line, so we skip it.
            context.advance()
    if type_of_linked_type == TopLevelSectionNames.EXECUTABLE:
        instrumenter = Instrumenter(executable=linked_type, object=objects)
    elif type_of_linked_type == TopLevelSectionNames.SHARED_LIBRARY:
        instrumenter = Instrumenter(shared_library=linked_type, object=objects)
    else:
        instrumenter = None

    return Metadata(runtime=runtime, instrumenter=instrumenter)
