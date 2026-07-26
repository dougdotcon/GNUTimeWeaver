import { mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const isWindows = process.platform === 'win32';
const compiler = process.env.CC || (isWindows ? 'gcc' : 'cc');
const output = path.join(root, 'build', `timeweaver${isWindows ? '.exe' : ''}`);
const args = [
  '-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic',
  '-Iinclude', '-Isrc/native',
  'src/native/platform.c', 'src/native/store.c', 'src/native/demo_agent.c',
  'src/native/cli.c', '-o', output,
];

mkdirSync(path.dirname(output), { recursive: true });
const result = spawnSync(compiler, args, { cwd: root, stdio: 'inherit' });
if (result.error) {
  console.error(`Unable to start ${compiler}: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
