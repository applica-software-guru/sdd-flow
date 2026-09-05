import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const checkDist = process.argv.includes('--dist');
const publicDir = path.join(root, 'public');
const distDir = path.join(root, 'dist');
const assetDir = checkDist ? distDir : publicDir;
const manifestPath = path.join(assetDir, 'site.webmanifest');
const indexPath = path.join(checkDist ? distDir : root, 'index.html');

function fail(message) {
  console.error(`PWA validation failed: ${message}`);
  process.exitCode = 1;
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    fail(`cannot read valid JSON at ${path.relative(root, filePath)} (${error.message})`);
    return null;
  }
}

function pngDimensions(filePath) {
  const buffer = fs.readFileSync(filePath);
  const signature = '89504e470d0a1a0a';
  if (buffer.subarray(0, 8).toString('hex') !== signature) {
    throw new Error('not a PNG file');
  }
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
  };
}

function normalizeIconPath(src) {
  return src.replace(/^\.\//, '').replace(/^\//, '');
}

if (!fs.existsSync(manifestPath)) fail(`missing ${path.relative(root, manifestPath)}`);
if (!fs.existsSync(indexPath)) fail(`missing ${path.relative(root, indexPath)}`);

const manifest = fs.existsSync(manifestPath) ? readJson(manifestPath) : null;
const indexHtml = fs.existsSync(indexPath) ? fs.readFileSync(indexPath, 'utf8') : '';

if (manifest) {
  for (const field of [
    'id',
    'name',
    'short_name',
    'description',
    'start_url',
    'scope',
    'display',
    'background_color',
    'theme_color',
  ]) {
    if (!manifest[field]) fail(`manifest is missing required field "${field}"`);
  }

  if (manifest.display !== 'standalone') fail('manifest display must be "standalone"');
  if (!Array.isArray(manifest.icons) || manifest.icons.length < 4) {
    fail('manifest must declare normal and maskable 192/512 icons');
  }

  const requiredIcons = new Map([
    ['192x192:any', false],
    ['512x512:any', false],
    ['192x192:maskable', false],
    ['512x512:maskable', false],
  ]);

  for (const icon of manifest.icons ?? []) {
    if (!icon.src || !icon.sizes || icon.type !== 'image/png') {
      fail(`manifest icon ${JSON.stringify(icon)} must declare src, sizes and type image/png`);
      continue;
    }

    const iconPath = path.join(assetDir, normalizeIconPath(icon.src));
    if (!fs.existsSync(iconPath)) {
      fail(`manifest icon is missing: ${icon.src}`);
      continue;
    }

    try {
      const [expectedWidth, expectedHeight] = String(icon.sizes).split('x').map(Number);
      const { width, height } = pngDimensions(iconPath);
      if (width !== expectedWidth || height !== expectedHeight) {
        fail(`icon ${icon.src} is ${width}x${height}, expected ${icon.sizes}`);
      }
    } catch (error) {
      fail(`cannot validate icon ${icon.src}: ${error.message}`);
    }

    const purpose = String(icon.purpose ?? 'any');
    for (const part of purpose.split(/\s+/)) {
      const key = `${icon.sizes}:${part}`;
      if (requiredIcons.has(key)) requiredIcons.set(key, true);
    }
  }

  for (const [key, found] of requiredIcons) {
    if (!found) fail(`manifest is missing required icon ${key}`);
  }
}

if (!indexHtml.includes('rel="manifest"') || !indexHtml.includes('/site.webmanifest')) {
  fail('index.html must link /site.webmanifest');
}
if (!indexHtml.includes('rel="apple-touch-icon"')) {
  fail('index.html must link an Apple touch icon');
}
if (!indexHtml.includes('name="description"')) {
  fail('index.html must include a description meta tag');
}
if (!indexHtml.includes('name="theme-color"')) {
  fail('index.html must include a theme-color meta tag');
}

if (checkDist) {
  const swPath = path.join(distDir, 'sw.js');
  if (!fs.existsSync(swPath)) fail('production build must emit dist/sw.js');
}

if (!process.exitCode) {
  console.log(`PWA validation passed${checkDist ? ' for dist' : ''}.`);
}
