import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/locales');
const locales = ['en', 'it'];
const files = (locale) =>
  fs
    .readdirSync(path.join(root, locale))
    .filter((file) => file.endsWith('.json'))
    .sort();

const errors = [];
const [canonicalFiles, translatedFiles] = locales.map(files);
if (JSON.stringify(canonicalFiles) !== JSON.stringify(translatedFiles)) {
  errors.push(`Namespace mismatch: en=[${canonicalFiles}] it=[${translatedFiles}]`);
}

const variables = (value) =>
  [...value.matchAll(/{{\s*([^},\s]+)[^}]*}}/g)].map((match) => match[1]).sort();

function compare(left, right, location) {
  if (typeof left !== typeof right || Array.isArray(left) !== Array.isArray(right)) {
    errors.push(`${location}: incompatible value shape`);
    return;
  }
  if (left && typeof left === 'object') {
    const leftKeys = Object.keys(left).sort();
    const rightKeys = Object.keys(right).sort();
    if (JSON.stringify(leftKeys) !== JSON.stringify(rightKeys)) {
      errors.push(`${location}: key mismatch en=[${leftKeys}] it=[${rightKeys}]`);
      return;
    }
    for (const key of leftKeys) compare(left[key], right[key], `${location}.${key}`);
    return;
  }
  if (
    typeof left === 'string' &&
    JSON.stringify(variables(left)) !== JSON.stringify(variables(right))
  ) {
    errors.push(`${location}: interpolation variable mismatch`);
  }
}

for (const file of canonicalFiles) {
  if (!translatedFiles.includes(file)) continue;
  compare(
    JSON.parse(fs.readFileSync(path.join(root, 'en', file), 'utf8')),
    JSON.parse(fs.readFileSync(path.join(root, 'it', file), 'utf8')),
    file.replace(/\.json$/, '')
  );
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`Locale catalogs are consistent (${canonicalFiles.length} namespaces).`);
