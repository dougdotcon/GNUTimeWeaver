import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const isWindows = process.platform === 'win32';
const compiler = process.env.CC || (isWindows ? 'gcc' : 'cc');
const output = path.join(root, 'build', `timeweaver_tests${isWindows ? '.exe' : ''}`);
mkdirSync(path.dirname(output), { recursive: true });

const compile = spawnSync(compiler, [
  '-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic',
  '-Iinclude', '-Isrc/native',
  'src/native/platform.c', 'src/native/store.c', 'test/native_test.c',
  '-o', output,
], { cwd: root, stdio: 'inherit' });
if (compile.status !== 0) process.exit(compile.status ?? 1);
const test = spawnSync(output, [], { cwd: root, stdio: 'inherit' });
if (test.status !== 0) process.exit(test.status ?? 1);

const build = spawnSync(process.execPath, [path.join(root, 'tools', 'build.mjs')], {
  cwd: root, stdio: 'inherit',
});
if (build.status !== 0) process.exit(build.status ?? 1);

const workspace = mkdtempSync(path.join(tmpdir(), 'timeweaver-integration-'));
const binary = path.join(root, 'build', `timeweaver${isWindows ? '.exe' : ''}`);
try {
  const demo = spawnSync(binary, ['demo', workspace], { cwd: root, encoding: 'utf8' });
  if (demo.status !== 0) throw new Error(demo.stderr || 'demo command failed');
  const graph = JSON.parse(demo.stdout);
  const failed = graph.nodes.find((node) => node.status === 3);
  const final = graph.nodes.at(-1);
  if (!failed || final?.status !== 2 || final.memory.prefixStepsReused !== 2) {
    throw new Error('demo did not produce the expected failure and resumed branch');
  }
  if (graph.stats.savedRatio < 0.7) throw new Error('CoW memory saving regressed below 70%');

  const branch = spawnSync(binary, [
    'branch', workspace, String(failed.id), 'Use PostgreSQL syntax only.',
  ], { cwd: root, encoding: 'utf8' });
  if (branch.status !== 0) throw new Error(branch.stderr || 'branch command failed');
  const branchedGraph = JSON.parse(branch.stdout);
  if (branchedGraph.nodes.at(-1)?.status !== 2) throw new Error('interactive branch did not complete');

  const validate = spawnSync(binary, ['validate', workspace], { cwd: root, encoding: 'utf8' });
  if (validate.status !== 0) throw new Error(validate.stderr || 'validation failed');
  console.log('CLI rewind/fork/resume integration: ok');
} finally {
  rmSync(workspace, { recursive: true, force: true });
}
