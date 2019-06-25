import logging
import re
from typing import List, Optional

from server.protocol import (
    CodeAction, Command, CompletionList, Diagnostic, Example, Hover, Location,
    Position, Range, SyntaxHighlight
)

logger = logging.getLogger(__name__)


class TeaspnHandler(object):
    """
    This is the abstract base class for handling requests (method calls) from ``TeaspnServer``.
    Writing assistance technology developers are expected to inherit this class and create their own
    implementation of this class. See ``handler_impl_sample.py`` for the sample implementation.

    This class also provides some low-level utility methods for keeping the document in sync with
    the client side.
    """
    def __init__(self):
        self._line_offsets = [0]
        self._uri = None
        self._text = ""

    def _position_to_offset(self, position: Position) -> int:
        """
        Given a Position in the document, converts it to the offset in `self._text`.

        Parameters:
            position (Position): position in the document

        Returns:
            offset (int): offset in `self._text`
        """
        return self._line_offsets[position.line] + position.character

    def _offset_to_position(self, offset: int) -> Position:
        """
        Given an offset in `self._text`, returns a Position in the document.

        Parameters:
            offset (int): offset in `self._text`

        Returns:
            position (Position): position in the document

        """
        line = 0
        for i, n in enumerate(self._line_offsets):
            if n > offset:
                line = i - 1
                break

        character = offset - line
        return Position(line=line, character=character)

    def _recompute_line_offsets(self):
        """
        After document updates, recomputes `self._line_offsets`.
        """
        # TODO: Consider \r\n?
        self._line_offsets = [0] + [m.start() + 1 for m in re.finditer('\n', self._text)]

    def _get_text(self, range: Range) -> str:
        """
        Given a Range, get text in the range.

        Parameters:
            range (Range): range in the document

        Returns:
            text (str): text in the range
        """
        start_offset = self._position_to_offset(range.start)
        end_offset = self._position_to_offset(range.end)
        return self._text[start_offset:end_offset]

    def _get_line(self, line: int) -> str:
        """
        Given a line number, returns the text on the specified line.

        Parameters:
            line (int): line number (0-base)

        Returns:
            line_text (str): text of the line
        """
        line_offsets_with_sentinel = self._line_offsets + [len(self._text)]
        return self._text[line_offsets_with_sentinel[line]:line_offsets_with_sentinel[line+1]]

    def _get_word_at(self, position: Position) -> Optional[str]:
        """Returns the word at position.

        This method gets the text for the cursor line, and then
        finds the word that encompasses the cursor. This is a bit inefficient, but simple.
        (otherwise you'd need to scan the string in both directions and find punctuations etc.,
        which is a lot more complicated, and language dependent).

        Parameters:
            position (Position): position in the document

        Returns:
            word (Optional[str]): word at the position.
                If there's no word at the position, returns None.
        """
        line = self._get_line(position.line)

        for match in re.finditer(r'\w+', line):
            if match.start() <= position.character <= match.end():
                return match.group(0)

        return None

    def initialize_document(self, uri: str, text: str):
        """
        Initializes document.

        Parameters:
            uri (str): URI of the document
            text (str): text of the document
        """
        logger.debug('Initialized document: uri=%s, text=%s', uri, text)
        self._uri = uri
        self._text = text
        self._recompute_line_offsets()

    def update_document(self, range: Range, text: str):
        """
        Updates document.

        Parameters:
            range (Range): range in the document where the update occurs
            text (str): text after the update
        """
        start_offset = self._position_to_offset(range.start)
        end_offset = self._position_to_offset(range.end)
        self._text = self._text[:start_offset] + text + self._text[end_offset:]
        self._recompute_line_offsets()
        logger.debug('Updated document: text=%s', self._text)

    def highlight_syntax(self) -> List[SyntaxHighlight]:
        """
        Handles syntax highlighting. Based on the current document, computes highlights.

        Returns:
            highlights (List[Highlights]): list of computed `Highlight`s
        """
        raise NotImplementedError

    def get_diagnostics(self) -> List[Diagnostic]:
        """
        Handles diagnostics. Based on the current documents, computes diagnostics (e.g., GED).

        Returns:
            diagnostics (List[Diagnostic]): list of computed `Diagnostic`s
        """
        raise NotImplementedError

    def run_quick_fix(self, range: Range, diagnostics: List[Diagnostic]) -> List[CodeAction]:
        """
        Handles quick fixes. This is called when user responds to diagnostics.

        Parameters:
            range (Range): range of the fix
            diagnostics (List[Diagnostic]): list of Diagnostics that user reacted upon

        Returns:
            actions (List[CodeAction]): list of `CodeAction`s that are shown to users
        """
        raise NotImplementedError

    def run_code_action(self, range: Range) -> List[Command]:
        """
        Handles code actions. This is called when user chooses to invoke text rewriting in a range.

        Parameters:
            range (Range): range of the document where code action is invoked

        Returns:
            commands (List[Command]): list of `Command`s that get executed as a result of the action
        """
        raise NotImplementedError

    def search_example(self, query: str) -> List[Example]:
        """
        Handles example search. This is called when user issues the example search command.

        Parameters:
            query (str): query string

        Returns:
            examples (List[Examples]): list of `Examples` (search result)
        """
        raise NotImplementedError

    def search_definition(self, position: Position, uri: str) -> List[Location]:
        """
        Handles "jump to definition". This is called when user issues the "go to definition" command

        Parameters:
            position (Position): position of the token whose definition to look up
            url (str): URI of document

        Returns:
            locations (List[Location]): list of `Location`s of the definition
        """
        raise NotImplementedError

    def get_completion_list(self, position: Position) -> CompletionList:
        """
        Handles autocomplete. This is called in response to user input.

        Parameters:
            position (Position): position of the cursor

        Returns:
            completion_list (CompletionList): a `CompletionList` instance with completions
        """
        raise NotImplementedError

    def hover(self, position: Position) -> Optional[Hover]:
        """
        Handles hover. This is called when user hovers the cursor over a position

        Parameters:
            position (Position): position of the hover

        Returns:
            hover (Optional[Hover]): information to show. None if there's no information to show.
        """
        raise NotImplementedError
