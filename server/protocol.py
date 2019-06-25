"""Defines constants and types for TEASPN."""

from typing import Dict, List, NamedTuple, Optional, Union


class TextDocumentSyncKind:
    NONE = 0
    Full = 1
    Incremental = 2


class Position(NamedTuple):
    line: int
    character: int

    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        return cls(line=data['line'], character=data['character'])

    def to_dict(self):
        return {'line': self.line, 'character': self.character}


class Range(NamedTuple):
    start: Position
    end: Position

    @classmethod
    def from_dict(cls, data: Dict) -> 'Range':
        start = Position.from_dict(data['start'])
        end = Position.from_dict(data['end'])
        return cls(start=start, end=end)

    def to_dict(self):
        return {'start': self.start.to_dict(), 'end': self.end.to_dict()}


class Location(NamedTuple):
    uri: str
    range: Range

    def to_dict(self):
        return {'uri': self.uri, 'range': self.range.to_dict()}


class SyntaxHighlight(NamedTuple):
    range: Range
    type: str
    hoverMessage: Optional[str] = None

    def to_dict(self):
        result = {
            'range': self.range.to_dict(),
            'type': self.type
        }

        if self.hoverMessage:
            result['hoverMessage'] = self.hoverMessage

        return result


class DiagnosticSeverity:
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


class Diagnostic(NamedTuple):
    range: Range
    message: str
    severity: Optional[int] = None
    code: Optional[Union[int, str]] = None
    source: Optional[str] = None
    relatedInformation: None = None  # TODO: support relatedInformation

    @classmethod
    def from_dict(cls, data: Dict) -> 'Diagnostic':
        rng = Range.from_dict(data['range'])
        return cls(range=rng,
                   message=data['message'],
                   severity=data.get('severity'),
                   code=data.get('code'),
                   source=data.get('source'))

    def to_dict(self):
        result = {
            'range': self.range.to_dict(),
            'message': self.message
        }

        if self.severity is not None:
            result['severity'] = self.severity

        if self.code is not None:
            result['code'] = self.code

        if self.source is not None:
            result['source'] = self.source

        return result


class TextEdit(NamedTuple):
    range: Range
    newText: str

    def to_dict(self):
        return {
            'range': self.range.to_dict(),
            'newText': self.newText
        }


class CompletionItem(NamedTuple):
    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None  # TODO: support MarkupContent
    deprecated: Optional[bool] = None
    preselect: Optional[bool] = None
    sortText: Optional[str] = None
    filterText: Optional[str] = None
    insertText: Optional[str] = None
    insertTextFormat = None  # TODO: support insertTextFormat
    textEdit: TextEdit = None
    additionalTextEdits = None  # TODO: support additionalTextEdits
    commitCharacters: Optional[List[str]] = None
    command = None  # TODO: support command
    data = None  # TODO: support data

    def to_dict(self):
        result = {'label': self.label}

        if self.detail is not None:
            result['detail'] = self.detail

        if self.textEdit is not None:
            result['textEdit'] = self.textEdit.to_dict()

        return result


class CompletionList(NamedTuple):
    isIncomplete: bool
    items: List[CompletionItem]

    def to_dict(self):
        return {
            'isIncomplete': self.isIncomplete,
            'items': [item.to_dict() for item in self.items]
        }


class Example(NamedTuple):
    label: str
    description: str

    def to_dict(self):
        return {
            'label': self.label,
            'description': self.description
        }


class WorkspaceEdit(NamedTuple):
    changes: Dict[str, List[TextEdit]]
    documentChanges = None  # NOTE: not supported

    def to_dict(self):
        return {'changes': {uri: [edit.to_dict() for edit in edits]
                            for uri, edits in self.changes.items()}}


class Command(NamedTuple):
    title: str
    command: str
    arguments: Optional[List] = None

    def to_dict(self):
        result = {
            'title': self.title,
            'command': self.command
        }
        if self.arguments is not None:
            result['arguments'] = [arg.to_dict() for arg in self.arguments]

        return result


class CodeAction(NamedTuple):
    title: str
    kind: Optional[str] = None
    edit: Optional[WorkspaceEdit] = None  # NOTE: current ver. of VSCode doesn't support this
    command: Optional[Command] = None

    def to_dict(self):
        result = {
            'title': self.title
        }

        if self.kind:
            result['kind'] = self.kind

        if self.edit:
            result['edit'] = self.edit.to_dict()

        if self.command:
            result['command'] = self.command.to_dict()

        return result


class Hover(NamedTuple):
    contents: str  # TODO: support MarkedString and list of MarkedString
    range: Optional[Range] = None

    def to_dict(self):
        result = {
            'contents': self.contents
        }

        if self.range is not None:
            result['range'] = self.range.to_dict()

        return result
