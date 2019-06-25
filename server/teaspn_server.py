import logging
import sys

from pyls_jsonrpc.dispatchers import MethodDispatcher
from pyls_jsonrpc.endpoint import Endpoint
from pyls_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

from server.handler_impl_sample import TeaspnHandlerSample
from server.protocol import Diagnostic, Position, Range, TextDocumentSyncKind
from server.teaspn_handler import TeaspnHandler

MAX_WORKERS = 64

logging.basicConfig(filename='log.txt',
                    filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _binary_stdio():
    """Construct binary stdio streams (not text mode).
    This seems to be different for Window/Unix Python2/3, so going by:
        https://stackoverflow.com/questions/2850893/reading-binary-data-from-stdin

    NOTE: this method is borrowed from python-language-server:
        https://github.com/palantir/python-language-server/blob/develop/pyls/__main__.py
    """
    PY3K = sys.version_info >= (3, 0)

    if PY3K:
        # pylint: disable=no-member
        stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
    else:
        # Python 2 on Windows opens sys.stdin in text mode, and
        # binary data that read from it becomes corrupted on \r\n
        if sys.platform == "win32":
            # set sys.stdin to binary mode
            # pylint: disable=no-member,import-error
            import os
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        stdin, stdout = sys.stdin, sys.stdout

    return stdin, stdout


class TeaspnServer(MethodDispatcher):
    """
    This class handles JSON-RPC requests to/from a TEASPN client, working as a middle layer
    that passes requests to a TeaspnHandler. Also does serialization and deseriaization of
    TEASPN objects.
    """
    def __init__(self, rx, tx, handler: TeaspnHandler, check_parent_process=False):
        self.workspace = None
        self.config = None

        self._jsonrpc_stream_reader = JsonRpcStreamReader(rx)
        self._jsonrpc_stream_writer = JsonRpcStreamWriter(tx)
        self._handler = handler
        self._check_parent_process = check_parent_process
        self._endpoint = Endpoint(self, self._jsonrpc_stream_writer.write, max_workers=MAX_WORKERS)
        self._dispatchers = []
        self._shutdown = False

    def start(self):
        """Entry point for the server."""
        self._jsonrpc_stream_reader.listen(self._endpoint.consume)

    def m_initialize(self, processId=None, rootUri=None, rootPath=None, initializationOptions=None,
                     **_kwargs):
        return {"capabilities": {
            "textDocumentSync": {
                "openClose": True,
                "change": TextDocumentSyncKind.Incremental
            },
            "completionProvider": {
                "resolveProvider": True,
                "triggerCharacters":[' '] + list(__import__('string').ascii_lowercase)
            },
            "codeActionProvider": True,
            "executeCommandProvider": {
                "commands": ['refactor.rewrite']
            },
            "definitionProvider": True,
            "hoverProvider": True
        }}

    def m_shutdown(self, **_kwargs):
        return None

    def m_text_document__did_open(self, textDocument=None, **_kwargs):
        self._handler.initialize_document(textDocument['uri'], textDocument['text'])

        diagnostics = self._handler.get_diagnostics()
        self._endpoint.notify('textDocument/publishDiagnostics', {
            'uri': textDocument['uri'],
            'diagnostics': [diagnostic.to_dict() for diagnostic in diagnostics]
        })

    def m_text_document__did_change(self, textDocument=None, contentChanges=None, **_kwargs):
        for change in contentChanges:
            rng = Range.from_dict(change['range'])
            self._handler.update_document(range=rng, text=change['text'])

        diagnostics = self._handler.get_diagnostics()

        self._endpoint.notify('textDocument/publishDiagnostics', {
            'uri': textDocument['uri'],
            'diagnostics': [diagnostic.to_dict() for diagnostic in diagnostics]
        })

    def m_text_document__syntax_highlight(self, textDocument=None, **_kwargs):
        highlights = self._handler.highlight_syntax()
        return [highlight.to_dict() for highlight in highlights]

    def m_text_document__completion(self, textDocument=None, position=None, **_kwargs):
        position = Position.from_dict(position)

        completion_list = self._handler.get_completion_list(position=position)

        return completion_list.to_dict()

    def m_workspace__search_example(self, query=None, **_kwargs):
        examples = self._handler.search_example(query)
        return [example.to_dict() for example in examples]

    def m_text_document__code_action(self, textDocument=None, range=None, context=None, **_kwargs):
        rng = Range.from_dict(range)
        actions = []
        if context is not None and context.get('diagnostics', []):
            # code action for resolving diagnostics -> invoke quick fix
            diagnostics = [Diagnostic.from_dict(diag) for diag in context['diagnostics']]
            actions = self._handler.run_quick_fix(rng, diagnostics)

        # obtain paraphrases
        commands = self._handler.run_code_action(rng)

        return [action_or_command.to_dict() for action_or_command in actions + commands]

    def m_workspace__execute_command(self, command=None, arguments=None, **_kwargs):
        if command == 'refactor.rewrite':
            self._endpoint.request('workspace/applyEdit', {
                'edit': arguments[0]
            })

    def m_text_document__definition(self, textDocument=None, position=None, **_kwargs):
        position = Position.from_dict(position)
        locations = self._handler.search_definition(position, uri=textDocument['uri'])
        return [location.to_dict() for location in locations]

    def m_text_document__hover(self, textDocument=None, position=None, **_kwargs):
        position = Position.from_dict(position)
        hover = self._handler.hover(position)
        if hover:
            return hover.to_dict()
        else:
            return None


def main():
    stdin, stdout = _binary_stdio()
    handler = TeaspnHandlerSample()
    server = TeaspnServer(stdin, stdout, handler, check_parent_process=False)
    server.start()

if __name__ == '__main__':
    main()
