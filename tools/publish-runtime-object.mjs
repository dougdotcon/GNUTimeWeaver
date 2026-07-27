// SPDX-License-Identifier: AGPL-3.0-or-later
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const [source, workspace, fault = 'none'] = process.argv.slice(2);
if (!source || !workspace) throw new Error('usage: publish-runtime-object STATE WORKSPACE [fault]');
const data = fs.readFileSync(source);
const sha = crypto.createHash('sha256').update(data).digest('hex');
const root = path.resolve(workspace, 'runtime');
const objects = path.join(root, 'objects');
const manifests = path.join(root, 'manifests');
const tmp = path.join(root, 'tmp');
fs.mkdirSync(objects, { recursive: true, mode: 0o700 });
fs.mkdirSync(manifests, { recursive: true, mode: 0o700 });
fs.mkdirSync(tmp, { recursive: true, mode: 0o700 });
const temporary = path.join(tmp, `${process.pid}-${sha}.tmp`);
const object = path.join(objects, `${sha}.bin`);

if (fault === 'before_state_write') process.exit(70);
const fd = fs.openSync(temporary, 'wx', 0o600);
const bytes = fault === 'mid_state_write' ? Math.floor(data.length / 2) : data.length;
fs.writeSync(fd, data, 0, bytes);
fs.fsyncSync(fd);
fs.closeSync(fd);
if (fault === 'mid_state_write' || fault === 'before_object_rename') process.exit(71);
if (bytes !== data.length) process.exit(72);
const check = crypto.createHash('sha256').update(fs.readFileSync(temporary)).digest('hex');
if (check !== sha) process.exit(73);
if (!fs.existsSync(object)) fs.renameSync(temporary, object); else fs.unlinkSync(temporary);
if (fault === 'after_object_rename' || fault === 'before_manifest_publish') process.exit(74);

const manifest = { version: 1, kind: 'opaque_runtime_state', sha256: sha, bytes: data.length,
  object: `runtime/objects/${sha}.bin`, published_at: new Date().toISOString() };
const manifestPath = path.join(manifests, `${sha}.json`);
const manifestTmp = `${manifestPath}.${process.pid}.tmp`;
fs.writeFileSync(manifestTmp, JSON.stringify(manifest, null, 2), { mode: 0o600 });
const mf = fs.openSync(manifestTmp, 'r+'); fs.fsyncSync(mf); fs.closeSync(mf);
fs.renameSync(manifestTmp, manifestPath);
if (fault === 'before_node_publish') process.exit(75);

const nodePath = path.join(root, 'smoke-node.json');
fs.writeFileSync(nodePath, JSON.stringify({ node_id: 1, parent_node: null, state: sha }, null, 2), { mode: 0o600 });
const referenced = new Set(fs.readdirSync(manifests).filter(x => x.endsWith('.json')).map(x => x.slice(0, -5)));
const orphans = fs.readdirSync(objects).filter(x => x.endsWith('.bin') && !referenced.has(x.slice(0, -4)));
console.log(JSON.stringify({ sha256: sha, bytes: data.length, object, manifest: manifestPath, node: nodePath, orphans }));
