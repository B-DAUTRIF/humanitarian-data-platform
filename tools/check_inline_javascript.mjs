import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const paths = process.argv.slice(2);
if (!paths.length) throw new Error('Utilisation: node check_inline_javascript.mjs fichier.html [...]');
let total = 0;
for (const path of paths) {
  const html = await readFile(path, 'utf8');
  const matches = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)];
  if (!matches.length) throw new Error(`Aucun script inline trouvé dans ${path}`);
  for (const [index, match] of matches.entries()) {
    new vm.Script(match[1], { filename: `${path}:inline-${index + 1}` });
    total++;
  }
}
console.log(`${total} script(s) inline valide(s) dans ${paths.length} fichier(s)`);
