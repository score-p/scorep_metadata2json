from dataclasses import dataclass
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
            key = line.split()[-1]  # last word in line
            context.advance()
            value = context.get_current_line() if context.has_more_lines() else ""
            env[key] = value

        context.advance()

    return env


def parse_compiler(context: ParsingContext) -> str:
    """
    Parses the compiler from the lines of the file.

    :param context: ParsingContext to search in.
    :type context: ParsingContext
    :return: The compiler name.
    :rtype: str
    """
    compiler = ""
    while context.has_more_lines():
        line = context.get_current_line()
        if is_new_section(line):
            break

        if line.startswith("compiler "):
            compiler = line.split()[1]
            # We found the compiler, so we can stop searching.
            break

        context.advance()

    return compiler


def parse_flags(context: ParsingContext, keyword: str) -> List[str]:
    """
    Parses flags from the lines of the file.

    The flags are expected to be in the following format::

        <keyword> <length of flags in bytes>
        if length of flags > 0:
            <flag1> <flag2> ... <flagN>
        endif

    :param context: ParsingContext to search in.
    :type context: ParsingContext
    :param keyword: Keyword to search for.
    :type keyword: str
    :return: The flags.
    :rtype: List[str]
    """
    found = False
    flags = [""]
    while context.has_more_lines() and not found:
        line = context.get_current_line()
        if is_new_section(line):
            break

        if line.startswith(keyword):
            nbyte = int(line.split()[1])
            if nbyte > 0:
                flags = context.advance().get_current_line().split()
            break

        context.advance()

    return flags


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
            "source ",
            "object ",
            "shared-library ",
            "static-library ",
            "executable ",
            "runtime",
            "instrumenter",
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
    compiler = parse_compiler(context.copy())
    define_flags = parse_flags(context.copy(), "define-flags ")
    compiler_flags = parse_flags(context.copy(), "compiler-flags ")
    library_files = parse_flags(context.copy(), "library-files ")

    return CommonAttributes(
        env=env,
        compiler=compiler,
        define_flags=define_flags,
        compiler_flags=compiler_flags,
        library_files=library_files,
    )


def parse_keyword(context: ParsingContext, keyword: str) -> List[str]:
    """
    Parses a keyword from the lines of the file.
    The keyword is expected to be in the following format::

        <keyword> <value1>
        <keyword> <value2>
         ...
        <keyword> <valueN>

    :param context: The ParsingContext to search in.
    :type context: ParsingContext
    :param keyword: The keyword to search for.
    :type keyword: str
    :return: The values of the keyword.
    :rtype: List[str]
    """
    result = []
    while context.has_more_lines():
        line = context.get_current_line()
        if is_new_section(line):
            break

        if line.startswith(keyword):
            result.append(line.split()[1])
        context.advance()

    return result


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

    objects = []
    runtime = None
    linked_type = None

    while context.has_more_lines():
        line = context.get_current_line()

        logging.debug(f"Parsing line: {line}")

        if line.startswith("runtime"):
            context.advance()
            logging.debug("Parsing runtime")
            common_attributes = parse_common_attributes(context.copy())
            runtime = Runtime(env=common_attributes.env)

        elif line.startswith("executable "):
            logging.debug(f"Parsing executable: {line.split()[-1]}")
            context.advance()
            common_attributes = parse_common_attributes(context.copy())

            object_files = parse_keyword(context.copy(), "object-file ")

            linked_type = LinkedType(
                compiler=common_attributes.compiler,
                define_flags=common_attributes.define_flags,
                compiler_flags=common_attributes.compiler_flags,
                library_files=common_attributes.library_files,
                object_files=object_files,
                env=common_attributes.env,
            )

        elif line.startswith("object "):
            logging.debug(f"Parsing object: {line.split()[-1]}")
            context.advance()

            common_attributes = parse_common_attributes(context.copy())

            source_files = parse_keyword(context.copy(), "source-file")
            source_language = parse_keyword(context.copy(), "source-language")[0]

            objects.append(
                Object(
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

    instrumenter = Instrumenter(executable=executable, object=objects)

    return Metadata(runtime=runtime, instrumenter=instrumenter)
