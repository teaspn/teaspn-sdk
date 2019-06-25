/* --------------------------------------------------------------------------------------------
 * TEASPN license:
 * Copyright (c) TEASPN developers. All rights reserved.
 * Licensed under the MIT License.

 * Original license:
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See LICENSE.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
'use strict';

import * as net from 'net';
import * as vscode from 'vscode';
import { workspace, window } from 'vscode';

import { join } from 'path';

import { LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	Trace,
	RequestType,
	TextDocumentIdentifier,
	Range
} from 'vscode-languageclient';
import { PassThrough } from 'stream';

interface SyntaxHighlightParams {
	textDocument: TextDocumentIdentifier
}

interface SyntaxHighlight {
	range: Range
	type: string
	hoverMessage?: string
}

namespace SyntaxHighlightRequest {
	export const type = new RequestType<SyntaxHighlightParams, SyntaxHighlight[] | null, void, void>('textDocument/syntaxHighlight');
}

const decorationTypes = {
	'blue': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'blue',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkblue' },
		dark: {	color: 'lightblue' }
	}),
	'red': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'red',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkred' },
		dark: {	color: 'lightpink' }
	}),
	'coral': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'coral',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkcoral' },
		dark: {	color: 'lightcoral' }
	}),
	'cyan': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'cyan',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkcyan' },
		dark: {	color: 'lightcyan' }
	}),
	'green': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'green',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkgreen' },
		dark: {	color: 'lightgreen' }
	}),
	'salmon': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'salmon',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darksalmon' },
		dark: {	color: 'lightsalmon' }
	}),
	'seagreen': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'seagreen',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkseagreen' },
		dark: {	color: 'lightseagreen' }
	}),
	'yellow': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'yellow',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkyellow' },
		dark: {	color: 'lightyellow' }
	}),
	'orange': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'orange',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'darkorange' },
		dark: {	color: 'orange' }
	}),
	'gold': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'gold',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'goldenrod' },
		dark: {	color: 'gold' }
	}),
	'lime': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'lime',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'limegreen' },
		dark: {	color: 'mediumspringgreen' }
	}),
	'skyblue': vscode.window.createTextEditorDecorationType({
		overviewRulerColor: 'skyblue',
		overviewRulerLane: vscode.OverviewRulerLane.Right,
		light: { color: 'deepskyblue' },
		dark: {	color: 'lightskyblue' }
	})
	// TODO: Add more decoration types
};

interface WorkspaceSearchExampleParams {
	query: string;
}

interface ExampleInformation {
	label: string;
	description: string;
}

namespace WorkspaceSearchExampleRequest {
	export const type = new RequestType<WorkspaceSearchExampleParams, ExampleInformation[] | null, void, void>('workspace/searchExample');
}

function startLangServer(command: string, args: string[], documentSelector: string[]): vscode.Disposable {
	const serverOptions: ServerOptions = {
        command,
		args,
	};
	const clientOptions: LanguageClientOptions = {
		documentSelector: documentSelector,
        synchronize: {
            configurationSection: "teaspn"
        }
	}
	const client = new LanguageClient('teaspn', 'TEASPN client', serverOptions, clientOptions, true);
	client.trace = Trace.Verbose;

	// Add syntax highlighting
	const callback = (event: vscode.TextDocumentChangeEvent): void => {
		const document = event.document;
		if (document.uri.scheme == "output")
			return;

		const params = { textDocument: { uri: document.uri.toString() }};
		client.sendRequest(SyntaxHighlightRequest.type, params).then(
			(response) => {
				const typeToOptions: { [type: string]: any[] } = {};

				for (let highlight of response) {
					if (typeToOptions[highlight.type] == undefined)
						typeToOptions[highlight.type] = [];
					typeToOptions[highlight.type].push({range: highlight.range, hoverMessage: highlight.hoverMessage});
				}

				for (let type in typeToOptions) {
					window.activeTextEditor.setDecorations(decorationTypes[type], typeToOptions[type]);
				}
			}
		);
	};

	workspace.onDidChangeTextDocument(callback);

	// Add example search command
	vscode.commands.registerCommand('teaspn.searchExample', () => {
		window.showInputBox().then((query) => {
			if (query == undefined) return;

			client.sendRequest(WorkspaceSearchExampleRequest.type, { query }).then(
				(response) => {
					window.showQuickPick(response, 
						{ matchOnDescription: true, 
							placeHolder: 'further filter results by typing in English or the language used for desription.',
						canPickMany: true }).then(
						(values) => { 
							console.log(values);
							for (var value of values) {
								vscode.window.showInformationMessage(value.label + ' ' + value.description);
							}
						});
				});
			});
		});

	return client.start();
}

function startLangServerTCP(port: number, documentSelector: string[]): vscode.Disposable {
	const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
			var client = new net.Socket();
			client.connect(port, "127.0.0.1", function() {
				resolve({
					reader: client,
					writer: client
				});
			});
		});
	}

	const clientOptions: LanguageClientOptions = {
		documentSelector: documentSelector,
	}
	const client = new LanguageClient('teaspn', serverOptions, clientOptions);
	client.trace = Trace.Verbose;
	return client.start();
}

export function activate(context: vscode.ExtensionContext) {
	const executable = workspace.getConfiguration("teaspn").get<string>("executable");
    context.subscriptions.push(startLangServer(join(context.extensionPath, executable), [], ["plaintext"]));
    // For TCP server needs to be started seperately
    // context.subscriptions.push(startLangServerTCP(3000, ["plaintext"]));
}
