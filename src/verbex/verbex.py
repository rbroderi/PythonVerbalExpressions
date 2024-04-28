"""Generate regular expressions from an easier fluent verbal form."""

from __future__ import annotations

import re
from collections.abc import Callable
from collections.abc import Iterator
from enum import Enum
from functools import wraps
from typing import Annotated
from typing import Any
from typing import TypeAlias
from typing import Union
from typing import cast
from typing import runtime_checkable

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from re import Pattern
from typing import ParamSpec
from typing import Protocol
from typing import TypeVar

from beartype import beartype
from beartype.vale import Is


def _string_len_is_1(text: object) -> bool:
    return isinstance(text, str) and len(text) == 1


Char = Annotated[str, Is[_string_len_is_1]]


P = ParamSpec("P")
R = TypeVar("R")


# work around for bug https://github.com/python/mypy/issues/12660
# fixed in next version of mypy.
@runtime_checkable
class HasIter(Protocol):
    """Workaround for mypy P.args."""

    def __iter__(self) -> Iterator[Any]:
        """Object can be iterated.

        Yields
        ------
            Next object.

        """
        ...


# work around for bug https://github.com/python/mypy/issues/12660
# fixed in next version of mypy
@runtime_checkable
class HasItems(Protocol):
    """Workaround for mypy P.kwargs."""

    def items(self) -> tuple[str, Any]:
        """Object has items method.

        :returns: The dict of items.
        :rtype: dict
        """
        ...


class EscapedText(str):
    """Text that has been escaped for regex.

    :param str value: the string to escape
    :return: escaped regex string
    :rtype: str

    """

    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        """Return an escaped regex string.

        :param str value: the string to escape
        :return: escaped regex string
        :rtype: str

        """
        return str.__new__(cls, re.escape(value))


def re_escape(func: Callable[P, R]) -> Callable[P, R]:
    """Automatically escape any string parameters as EscapedText.

    :param func: The function to decorate.
    :type func: Callable[P, R]
    :return: The decorated function.
    :rtype: Callable[P, R]

    """

    @wraps(func)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        escaped_args: list[Any] = []
        escaped_kwargs: dict[str, Any] = {}
        for arg in cast(HasIter, args):
            if not isinstance(arg, EscapedText) and isinstance(arg, str):
                escaped_args.append(EscapedText(arg))
            else:
                escaped_args.append(arg)
        arg_k: str
        arg_v: Any
        for arg_k, arg_v in cast(HasItems, kwargs).items():
            if not isinstance(arg_v, EscapedText) and isinstance(arg_v, str):
                escaped_kwargs[arg_k] = EscapedText(str(arg_v))
            else:
                escaped_kwargs[arg_k] = arg_v
        return func(*escaped_args, **escaped_kwargs)  # pyright: ignore[reportCallIssue]

    return inner


class CharClass(Enum):
    """Enum of character classes in regex.

    :param Enum: Extends the Enum class.
    :type Enum: class

    """

    DIGIT = "\\d"
    LETTER = "\\w"
    UPPERCASE_LETTER = "\\u"
    LOWERCASE_LETTER = "\\l"
    WHITESPACE = "\\s"
    TAB = "\\t"

    def __str__(self) -> str:
        """To string method based on Enum value.

        :return: value of Enum
        :rtype: str

        """
        return self.value


class SpecialChar(Enum):
    """Enum of special characters, shorthand.

    :param Enum: Extends the Enum class.
    :type Enum: class

    """

    # does not work  / should not be used in [ ]
    LINEBREAK = "(\\n|(\\r\\n))"
    START_OF_LINE = "^"
    END_OF_LINE = "$"
    TAB = "\t"

    def __str__(self) -> str:
        """To string for special chars enum.

        :return: Return value of enum as string.
        :rtype: str

        """
        return self.value


CharClassOrChars: TypeAlias = str | CharClass
EscapedCharClassOrSpecial: TypeAlias = str | CharClass | SpecialChar
VerbexEscapedCharClassOrSpecial: TypeAlias = Union["Verbex", EscapedCharClassOrSpecial]


class Verbex:  # pylint: disable=too-many-public-methods
    """VerbalExpressions class.

    The following methods do not try to match the original js lib!

    .. note::
        This class is a modified version of the VerbalExpressions library.

    """

    EMPTY_REGEX_FLAG = re.RegexFlag(0)

    @re_escape
    @beartype
    def __init__(self, modifiers: re.RegexFlag = EMPTY_REGEX_FLAG) -> None:
        """Create a Verbex object; setting any needed flags.

        :param modifiers: Regex modifying flags (default: ``re.RegexFlag(0)``)
        :type modifiers: re.RegexFlag

        :returns: The created Verbex object.
        :rtype: Verbex

        """
        # self._parts: List[str] = [text]
        self._parts: list[str] = []
        self._modifiers = modifiers

    @property
    def modifiers(self) -> re.RegexFlag:
        """Return the modifiers for this Verbex object.

        :return: The modifiers applied to this object.
        :rtype: re.RegexFlag

        """
        return self._modifiers

    def __str__(self) -> str:
        """Return regex string representation.

        :return: The regex string representation.
        :rtype: str

        """
        return "".join(self._parts)

    @beartype
    def _add(self, value: str | list[str]) -> Verbex:
        """Append a transformed value to internal expression to be compiled.

        As possible, this method should be "private".

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        if isinstance(value, list):
            self._parts.extend(value)
        else:
            self._parts.append(value)
        return self

    def regex(self) -> Pattern[str]:
        """Get a regular expression object.

        :return: A regular expression object.
        :rtype: Pattern[str]

        """
        return re.compile(
            str(self),
            self._modifiers,
        )

    # allow VerbexEscapedCharClassOrSpecial

    @re_escape
    @beartype
    def _capture_group_with_name(
        self,
        name: str,
        text: VerbexEscapedCharClassOrSpecial,
    ) -> Verbex:
        return self._add(f"(?<{name}>{text!s})")

    @re_escape
    @beartype
    def _capture_group_without_name(
        self,
        text: VerbexEscapedCharClassOrSpecial,
    ) -> Verbex:
        return self._add(f"({text!s})")

    @re_escape
    @beartype
    def capture_group(
        self,
        name_or_text: str | None | VerbexEscapedCharClassOrSpecial = None,
        text: VerbexEscapedCharClassOrSpecial | None = None,
    ) -> Verbex:
        """Create a capture group.

        Name is optional. If not specified, then the first argument is the text.

        :param name_or_text: The name of the group / text to search for (default: None)
        :type name_or_text: str or None
        :param text: The text to search for (default: None)
        :type text: str or None

        :raises ValueError: If name is specified, then text must be as well.

        :returns: Verbex with added capture group.
        :rtype: Verbex

        """
        if name_or_text is not None:
            if text is None:
                _text = name_or_text
                return self._capture_group_without_name(_text)
            if isinstance(name_or_text, str):
                return self._capture_group_with_name(name_or_text, text)
        msg = "text must be specified with optional name"
        raise ValueError(msg)

    @re_escape
    @beartype
    def OR(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:  # noqa: N802
        """`or` is a python keyword so we use `OR` instead.

        :param text: Text to find or a Verbex object.
        :type text: VerbexEscapedCharClassOrSpecial

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add("|").find(text)

    @re_escape
    @beartype
    def zero_or_more(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Find the text or Verbex object zero or more times.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:{text!s})*")

    @re_escape
    @beartype
    def one_or_more(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Find the text or Verbex object one or more times.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:{text!s})+")

    @re_escape
    @beartype
    def n_times(
        self,
        text: VerbexEscapedCharClassOrSpecial,
        n: int,
    ) -> Verbex:
        """Find the text or Verbex object n or more times.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial
        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:{text!s}){{{n}}}")

    @re_escape
    @beartype
    def n_times_or_more(
        self,
        text: VerbexEscapedCharClassOrSpecial,
        n: int,
    ) -> Verbex:
        """Find the text or Verbex object at least n times.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial
        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:{text!s}){{{n},}}")

    @re_escape
    @beartype
    def n_to_m_times(
        self,
        text: VerbexEscapedCharClassOrSpecial,
        n: int,
        m: int,
    ) -> Verbex:
        """Find the text or Verbex object between n and m times.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial
        :param n: The minimum number of times to find the text.
        :type n: int
        :param m: The maximum number of times to find the text.
        :type m: int
        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:{text!s}){{{n},{m}}}")

    @re_escape
    @beartype
    def maybe(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Possibly find the text / Verbex object.

        :param text: The text / Verbex object to possibly find.
        :type text: VerbexEscapedCharClassOrSpecial

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:{text!s})?")

    @re_escape
    @beartype
    def find(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Find the text or Verbex object.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(str(text))

    @re_escape
    @beartype
    def then(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Synonym for find.

        :param text: The text / Verbex object to look for.
        :type text: VerbexEscapedCharClassOrSpecial

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self.find(text)

    @re_escape
    @beartype
    def followed_by(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Match if string is followed by text.

        Positive lookahead

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?={text})")

    @re_escape
    @beartype
    def not_followed_by(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Match if string is not followed by text.

        Negative lookahead

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?!{text})")

    @re_escape
    @beartype
    def preceded_by(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Match if string is not preceded by text.

        Positive lookbehind

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?<={text})")

    @re_escape
    @beartype
    def not_preceded_by(self, text: VerbexEscapedCharClassOrSpecial) -> Verbex:
        """Match if string is not preceded by text.

        Negative Lookbehind

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?<!{text})")

    @re_escape
    @beartype
    def any_of(self, chargroup: CharClassOrChars) -> Verbex:
        """Find anything in this group of chars or char class.

        :param text: The characters to look for.
        :type text: str

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:[{chargroup}])")

    @re_escape
    @beartype
    def not_any_of(self, text: CharClassOrChars) -> Verbex:
        """Find anything but this group of chars or char class.

        :param text: The characters to not look for.
        :type text: str

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"(?:[^{text}])")

    @re_escape
    def anything_but(self, chargroup: EscapedCharClassOrSpecial) -> Verbex:
        """Find anything one or more times but this group of chars or char class.

        :param text: The characters to not look for.
        :type text: str

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"[^{chargroup}]+")

    # no text input

    def start_of_line(self) -> Verbex:
        """Find the start of the line.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self.find(SpecialChar.START_OF_LINE)

    def end_of_line(self) -> Verbex:
        """Find the end of the line.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self.find(SpecialChar.END_OF_LINE)

    def line_break(self) -> Verbex:
        """Find a line break.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self.find(SpecialChar.LINEBREAK)

    def tab(self) -> Verbex:
        """Find a tab.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self.find(SpecialChar.TAB)

    def anything(self) -> Verbex:
        """Find anything one or more times.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(".+")

    def as_few(self) -> Verbex:
        """Modify previous search to not be greedy.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add("?")

    @beartype
    def number_range(self, start: int, end: int) -> Verbex:
        """Generate a range of numbers.

        :param start: Start of the range
        :type start: int
        :param end: End of the range
        :type end: int
        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add("(?:" + "|".join(str(i) for i in range(start, end + 1)) + ")")

    @beartype
    def letter_range(self, start: Char, end: Char) -> Verbex:
        """Generate a range of letters.

        :param start: Start of the range
        :type start: Char
        :param end: End of the range
        :type end: Char
        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add(f"[{start}-{end}]")

    def word(self) -> Verbex:
        """Find a word on word boundary.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        return self._add("(\\b\\w+\\b)")

    # # --------------- modifiers ------------------------

    def with_any_case(self) -> Verbex:
        """Modify Verbex object to be case insensitive.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        self._modifiers |= re.IGNORECASE
        return self

    def search_by_line(self) -> Verbex:
        """Search each line, ^ and $ match beginning and end of line respectively.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        self._modifiers |= re.MULTILINE
        return self

    def with_ascii(self) -> Verbex:
        """Match ascii instead of unicode.

        :return: Modified Verbex object.
        :rtype: Verbex

        """
        self._modifiers |= re.ASCII
        return self


# left over notes from original version
# def __getattr__(self, attr):
#     """ any other function will be sent to the regex object """
#     regex = self.regex()
#     return getattr(regex, attr)

# def replace(self, string, repl):
#     return self.sub(repl, string)


if __name__ == "__main__":
    pass
