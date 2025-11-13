const vscode = require('vscode');

async function swapRows() {
  // Wir nehmen jeweils den aktiven Tab der 4 Gruppen und tauschen oben <-> unten.
  const groups = vscode.window.tabGroups.all;
  if (groups.length < 4) {
    vscode.window.showErrorMessage('Erwarte ein 2x2-Layout (4 Editorgruppen).');
    return;
  }

  // Helpers: aktiven Tab je Gruppe holen (nur wenn vorhanden)
  const g1 = groups[0]?.activeTab;
  const g2 = groups[1]?.activeTab;
  const g3 = groups[2]?.activeTab;
  const g4 = groups[3]?.activeTab;

  // Funktion: Tab in Zielgruppe öffnen (falls Text-Editor); für Webviews/Previews ggf. keine Garantie
  async function openTab(tab, targetViewColumn) {
    if (!tab) return;
    // Nur Textdokumente sicher unterstützen:
    if (tab.input && tab.input.uri) {
      const doc = await vscode.workspace.openTextDocument(tab.input.uri);
      await vscode.window.showTextDocument(doc, { viewColumn: targetViewColumn, preview: false, preserveFocus: true });
    } else {
      // Fallback: versuche einfach den Tab zu aktivieren (nicht immer möglich)
      await vscode.window.tabGroups.open(tab, { preserveFocus: true });
    }
  }

  // Reihen tauschen: (1,2) <-> (3,4)
  // Zielspalten sind ViewColumn.One/Two/Three/Four
  await openTab(g3, vscode.ViewColumn.One);
  await openTab(g4, vscode.ViewColumn.Two);
  await openTab(g1, vscode.ViewColumn.Three);
  await openTab(g2, vscode.ViewColumn.Four);
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand('rowSash.swapRows', swapRows)
  );
}

function deactivate() {}
module.exports = { activate, deactivate };
