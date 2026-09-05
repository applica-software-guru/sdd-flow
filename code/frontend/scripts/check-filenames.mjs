import { readdir } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('../src/', import.meta.url);
const pattern = /^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.(?:test|d))?\.(?:ts|tsx)$/;
const invalid = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await walk(path);
    else if (/\.tsx?$/.test(entry.name) && !pattern.test(entry.name)) invalid.push(path);
  }
}

await walk(root.pathname);
if (invalid.length) {
  console.error(`Source filenames must use kebab-case:\n${invalid.join('\n')}`);
  process.exit(1);
}
console.log('All application source filenames use kebab-case.');
