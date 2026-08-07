#!/usr/bin/env node

import {readFile, writeFile} from 'node:fs/promises'
import {pathToFileURL} from 'node:url'

const [modulePath, outputPath] = process.argv.slice(2)

if (!modulePath || !outputPath) {
  throw new Error('Usage: generate_un_m49_snapshot.mjs <un-m49/index.js> <output.json>')
}

const moduleUrl = pathToFileURL(modulePath).href
const {unM49} = await import(moduleUrl)
const packageJson = JSON.parse(
  await readFile(new URL('./package.json', moduleUrl), 'utf8')
)

const snapshot = {
  schema_version: 1,
  generated_at: '2026-08-07',
  source: {
    authority: 'United Nations Statistics Division',
    standard: 'Standard country or area codes for statistical use (M49)',
    url: 'https://unstats.un.org/unsd/methodology/m49/overview/',
    intermediary: `un-m49 npm ${packageJson.version}`,
    intermediary_url: 'https://github.com/wooorm/un-m49',
    intermediary_license: 'MIT'
  },
  entities: unM49
}

await writeFile(outputPath, `${JSON.stringify(snapshot, null, 2)}\n`, 'utf8')
