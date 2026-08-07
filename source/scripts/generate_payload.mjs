import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(process.argv[2] ?? 'payload');
const output = path.resolve(process.argv[3] ?? 'src/payload_generated.h');

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.name === '__pycache__' || entry.name.endsWith('.pyc')) continue;
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(absolute));
    else if (entry.isFile()) files.push(absolute);
  }
  return files;
}

const files = await walk(root);
const chunks = [
  '#ifndef HDP_PAYLOAD_GENERATED_H',
  '#define HDP_PAYLOAD_GENERATED_H',
  '',
  '#include <stddef.h>',
  'typedef struct { const char *path; const unsigned char *data; size_t size; } HdpPayloadFile;',
  '',
];

const records = [];
for (const [index, absolute] of files.entries()) {
  const relative = path.relative(root, absolute).split(path.sep).join('/');
  const data = await readFile(absolute);
  const identifier = `hdp_payload_${index}`;
  const lines = [];
  for (let offset = 0; offset < data.length; offset += 16) {
    lines.push('  ' + [...data.subarray(offset, offset + 16)].map(byte => `0x${byte.toString(16).padStart(2, '0')}`).join(', ') + ',');
  }
  chunks.push(`static const unsigned char ${identifier}[] = {`);
  chunks.push(...lines);
  chunks.push('};', '');
  records.push(`  { "${relative}", ${identifier}, sizeof(${identifier}) },`);
}

chunks.push('static const HdpPayloadFile g_payload_files[] = {', ...records, '};');
chunks.push('static const size_t g_payload_file_count = sizeof(g_payload_files) / sizeof(g_payload_files[0]);');
chunks.push('', '#endif', '');

await writeFile(output, chunks.join('\n'));
