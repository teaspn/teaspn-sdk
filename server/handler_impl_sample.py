import re
from typing import Dict, List, Optional

from overrides import overrides

from server.protocol import (
    CodeAction, Command, CompletionItem, CompletionList, Diagnostic, DiagnosticSeverity, Example,
    Hover, Location, Position, Range, SyntaxHighlight, TextEdit, WorkspaceEdit
)
from server.teaspn_handler import TeaspnHandler


class TeaspnHandlerSample(TeaspnHandler):
    """
    A sample TeaspnHandler implementation with simple writing assistance features.
    """
    def __init__(self):
        # Manages a mapping from Diagnostic to replacements
        self._diag_to_replacements: Dict[Diagnostic, List[str]] = {}

        super().__init__()

    @overrides
    def highlight_syntax(self) -> List[SyntaxHighlight]:
        """
        Implements sample syntax highlighting where all occurrences of CAPS WORDS and numbers
        are highlighted in different colors with hover messages.
        """
        highlights = []
        for line_id, line_text in enumerate(self._text.splitlines()):
            for match in re.finditer(r'\b[A-Z]+\b', line_text):
                rng = Range(start=Position(line=line_id, character=match.start()),
                            end=Position(line=line_id, character=match.end()))
                highlights.append(SyntaxHighlight(range=rng,
                                                  type='blue',
                                                  hoverMessage=f'ALL CAPS: {match.group(0)}'))

            for match in re.finditer(r'\b[0-9]+\b', line_text):
                rng = Range(start=Position(line=line_id, character=match.start()),
                            end=Position(line=line_id, character=match.end()))
                highlights.append(SyntaxHighlight(range=rng,
                                                  type='red',
                                                  hoverMessage=f'numbers: {match.group(0)}'))

        return highlights

    @overrides
    def get_diagnostics(self) -> List[Diagnostic]:
        """
        Implements sample grammatical error detection (GED) and correction (GEC).
        This checks English subject-verb agreement in statement sentences using hand-crafted rules.
        """
        PRONOUNS = ['i', 'you', 'we', 'she', 'he', 'they', 'it']
        BE_VERBS = ['am', 'are', 'is', 'were', 'was']
        VALID_COMBINATIONS = {
            'i': {'am', 'was'},
            'you': {'are', 'were'},
            'we': {'are', 'were'},
            'she': {'is', 'was'},
            'he': {'is', 'was'},
            'they': {'are', 'were'},
            'it': {'is', 'was'}
        }

        diagnostics = []
        for line_id, line_text in enumerate(self._text.splitlines()):
            matches = list(re.finditer(r'\w+', line_text))
            for m1, m2 in zip(matches, matches[1:]):
                w1, w2 = m1.group(0), m2.group(0)
                if not (w1.lower() in PRONOUNS and w2.lower() in BE_VERBS):
                    continue
                if w2.lower() in VALID_COMBINATIONS[w1.lower()]:
                    continue

                rng = Range(start=Position(line=line_id, character=m1.start(0)),
                            end=Position(line=line_id, character=m2.end(0)))
                diagnostic = Diagnostic(range=rng,
                                        severity=DiagnosticSeverity.Error,
                                        message='Wrong agreement: {} {}'.format(w1, w2))

                diagnostics.append(diagnostic)

                # Register the diagnostic for later use in GEC
                replacements = [f'{w1} {verb}' for verb in VALID_COMBINATIONS[w1.lower()]]
                self._diag_to_replacements[diagnostic] = replacements

        return diagnostics

    @overrides
    def run_quick_fix(self, range: Range, diagnostics: List[Diagnostic]) -> List[CodeAction]:
        """
        Implements GEC for fixing subject-verb agreement errors detected above.
        """
        actions = []
        for diag in diagnostics:
            for repl in self._diag_to_replacements[diag]:
                edit = WorkspaceEdit({self._uri: [TextEdit(range=diag.range, newText=repl)]})
                command = Command(title='Quick fix: {}'.format(repl),
                                  command='refactor.rewrite',
                                  arguments=[edit])
                actions.append(CodeAction(title='Quick fix: {}'.format(repl),
                                          kind='quickfix',
                                          command=command))
        return actions

    @overrides
    def run_code_action(self, range: Range) -> List[Command]:
        """
        Implements sample text rewriting where uppercase and lowercase rewriting is provided.
        """
        target_text = self._get_text(range)
        if not target_text:
            return []

        text_upper = target_text.upper()
        edit_upper = WorkspaceEdit({self._uri: [TextEdit(range=range, newText=text_upper)]})
        command_upper = Command(title=f'UPPER: {text_upper}',
                                command='refactor.rewrite',
                                arguments=[edit_upper])

        text_lower = target_text.lower()
        edit_lower = WorkspaceEdit({self._uri: [TextEdit(range=range, newText=text_lower)]})
        command_lower = Command(title=f'lower: {text_lower}',
                                command='refactor.rewrite',
                                arguments=[edit_lower])

        return [command_upper, command_lower]

    @overrides
    def search_example(self, query: str) -> List[Example]:
        """
        Sample search feature which returns a list of tea varieties and their descriptions,
        regardless of the query.
        """
        return [
            Example(label="Assam",
                    description="a black tea named after the region of its production, "
                                "Assam, India."),
            Example(label="Chai",
                    description="a flavoured tea beverage made by brewing black tea "
                                "with a mixture of aromatic spices and herbs."),
            Example(label="Darjeeling",
                    description="a tea grown in the Darjeeling district, Kalimpong District "
                                "in West Bengal, India, and widely exported and known."),
            Example(label="Earl Grey",
                    description="a tea blend which has been flavoured "
                                "with the addition of oil of bergamot."),
            Example(label="Jasmine",
                    description="tea scented with the aroma of jasmine blossoms."),
            Example(label="Matcha",
                    description="finely ground powder of specially grown "
                                "and processed green tea leaves."),
            Example(label="Oolong",
                    description="a traditional semi-oxidized Chinese tea"),
            Example(label="Puerh",
                    description="a variety of fermented tea produced "
                                "in the Yunnan province of China.")
        ]

    @overrides
    def search_definition(self, position: Position, uri: str) -> List[Location]:
        """
        Implements a "go to definition" feature where all occurrence of the target word are returned
        """
        word = self._get_word_at(position)

        locations = []
        offset = 0
        while True:
            offset = self._text.find(word, offset)
            if offset == -1:
                break
            rng = Range(start=self._offset_to_position(offset),
                        end=self._offset_to_position(offset + len(word)))
            locations.append(Location(uri=uri, range=rng))

            offset += 1

        return locations

    @overrides
    def get_completion_list(self, position: Position) -> CompletionList:
        """
        Implements simple word completion with tea variety names
        """
        COMPLETION_WORDS = [
            "Assam",
            "Chai",
            "Darjeeling",
            "Earl Grey",
            "Jasmine",
            "Matcha",
            "Oolong",
            "Puerh"
        ]
        offset = self._position_to_offset(position)
        context = self._text[:offset]
        query = context.split()[-1]

        items = []
        for word in COMPLETION_WORDS:
            if word.startswith(query):
                items.append(CompletionItem(label=word))

        return CompletionList(isIncomplete=True, items=items)

    @overrides
    def hover(self, position: Position) -> Optional[Hover]:
        """
        Implements a sample hover feature where a massage "word: {identity of word}" is shown
        when the cursor hovers over a word.
        """
        word = self._get_word_at(position)
        if not word:
            return None

        return Hover(contents=f'word: {word}')
