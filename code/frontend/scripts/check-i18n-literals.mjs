import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import ts from 'typescript';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src');
const textAttributes = new Set([
  'alt',
  'aria-description',
  'aria-label',
  'cancelLabel',
  'confirmLabel',
  'description',
  'emptyMessage',
  'emptyTitle',
  'errorMessage',
  'eyebrow',
  'label',
  'pendingLabel',
  'placeholder',
  'title',
]);
const allowedText = new Set(['S', 'SDD Flow', 'BUG-011', 'GitHub', '/NNN-', 'CR']);
const textProperties = new Set([
  'detail',
  'description',
  'emptyMessage',
  'job',
  'label',
  'message',
  'placeholder',
  'text',
  'title',
]);
const findings = [];

function humanText(value) {
  const normalized = value.replace(/\s+/g, ' ').trim();
  return /[A-Za-z]{2}/.test(normalized) && !allowedText.has(normalized);
}

function likelyCss(value) {
  const tokens = value.trim().split(/\s+/);
  return (
    tokens.length > 0 &&
    tokens.every((token) =>
      /^(?:-?(?:bg|text|border|dark|hover|focus|ring|rounded|p[trblxy]?|m[trblxy]?|h|w|min|max|flex|grid|gap|items|justify|font|leading|tracking|shadow|opacity|translate|cursor|overflow|relative|absolute|fixed|z|data)-|(?:sm|md|lg|xl|dark|hover|focus):)/.test(
        token
      )
    )
  );
}

function inspect(file) {
  const source = fs.readFileSync(file, 'utf8');
  const sourceFile = ts.createSourceFile(
    file,
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX
  );
  function report(node, value) {
    const position = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
    findings.push(
      `${path.relative(root, file)}:${position.line + 1}: ${value.replace(/\s+/g, ' ').trim()}`
    );
  }
  function visit(node) {
    if (ts.isJsxText(node) && humanText(node.text)) report(node, node.text);
    if (ts.isJsxAttribute(node) && textAttributes.has(node.name.text) && node.initializer) {
      if (ts.isStringLiteral(node.initializer) && humanText(node.initializer.text)) {
        report(node, node.initializer.text);
      }
      if (
        ts.isJsxExpression(node.initializer) &&
        node.initializer.expression &&
        ts.isTemplateExpression(node.initializer.expression) &&
        !node.initializer.expression.getText(sourceFile).includes('translate(') &&
        !node.initializer.expression.getText(sourceFile).includes('t(')
      ) {
        report(node, node.initializer.expression.getText(sourceFile));
      }
    }
    if (
      ts.isPropertyAssignment(node) &&
      textProperties.has(node.name.getText(sourceFile)) &&
      ts.isStringLiteral(node.initializer) &&
      humanText(node.initializer.text)
    ) {
      report(node, node.initializer.text);
    }
    if (
      ts.isStringLiteral(node) &&
      ts.isBinaryExpression(node.parent) &&
      ['BarBarToken', 'QuestionQuestionToken'].includes(
        ts.SyntaxKind[node.parent.operatorToken.kind]
      ) &&
      humanText(node.text) &&
      (/[A-Z]/.test(node.text[0] ?? '') || node.text.includes(' ')) &&
      !likelyCss(node.text)
    ) {
      report(node, node.text);
    }
    ts.forEachChild(node, visit);
  }
  visit(sourceFile);
}

function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.name === '__tests__' || entry.name === 'locales') continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(target);
    else if (entry.name.endsWith('.tsx')) inspect(target);
  }
}

walk(root);
if (findings.length) {
  console.error(`Untranslated user-facing literals:\n${findings.join('\n')}`);
  process.exit(1);
}
console.log('No unexplained user-facing JSX literals found.');
