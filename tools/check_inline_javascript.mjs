import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const path = process.argv[2];
if (!path) throw new Error('Utilisation: node check_inline_javascript.mjs index.html');
const html = await readFile(path, 'utf8');
const matches = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)];
if (!matches.length) throw new Error('Aucun script inline trouvé');
for (const [index, match] of matches.entries()) {
  new vm.Script(match[1], { filename: `${path}:inline-${index + 1}` });
}
console.log(`${matches.length} script(s) inline valide(s)`);

