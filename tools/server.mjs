import { createServer } from 'node:http';
import { existsSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const isWindows = process.platform === 'win32';
const binary = path.join(root, 'build', `timeweaver${isWindows ? '.exe' : ''}`);
const workspace = path.join(root, '.timeweaver', 'demo');
const publicDir = path.join(root, 'public');
const host = process.env.HOST || '127.0.0.1';
const port = Number.parseInt(process.env.PORT || '7331', 10);

const mimeTypes = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
]);

function buildNative() {
  const result = spawnSync(process.execPath, [path.join(root, 'tools', 'build.mjs')], {
    cwd: root,
    stdio: 'inherit',
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function runCli(args) {
  const result = spawnSync(binary, args, {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 4 * 1024 * 1024,
  });
  if (result.status !== 0) {
    throw new Error(result.stderr.trim() || `Native command failed with ${result.status}`);
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    throw new Error('Native engine returned malformed JSON');
  }
}

function resetDemo() {
  const resolved = path.resolve(workspace);
  const allowed = path.resolve(root, '.timeweaver');
  if (!resolved.startsWith(`${allowed}${path.sep}`)) {
    throw new Error('Refusing to reset a workspace outside .timeweaver');
  }
  rmSync(resolved, { recursive: true, force: true });
  mkdirSync(resolved, { recursive: true });
  return runCli(['demo', resolved]);
}

function readGraph() {
  if (!existsSync(path.join(workspace, 'graph.twm'))) return resetDemo();
  return runCli(['export', workspace]);
}

function sendJson(response, status, value) {
  const body = JSON.stringify(value);
  response.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store',
  });
  response.end(body);
}

function readJson(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    request.on('data', (chunk) => {
      size += chunk.length;
      if (size > 64 * 1024) {
        reject(new Error('Request body exceeds 64 KiB'));
        request.destroy();
        return;
      }
      chunks.push(chunk);
    });
    request.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'));
      } catch {
        reject(new Error('Body must be valid JSON'));
      }
    });
    request.on('error', reject);
  });
}

function serveStatic(request, response) {
  const url = new URL(request.url, `http://${request.headers.host || host}`);
  const relative = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
  const target = path.resolve(publicDir, relative);
  if (!target.startsWith(`${path.resolve(publicDir)}${path.sep}`) || !existsSync(target)) {
    response.writeHead(404).end('Not found');
    return;
  }
  const body = readFileSync(target);
  response.writeHead(200, {
    'Content-Type': mimeTypes.get(path.extname(target)) || 'application/octet-stream',
    'Content-Length': body.length,
    'Cache-Control': 'no-cache',
  });
  response.end(request.method === 'HEAD' ? undefined : body);
}

if (!existsSync(binary)) buildNative();
mkdirSync(workspace, { recursive: true });
readGraph();

const server = createServer(async (request, response) => {
  response.setHeader('Content-Security-Policy',
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'");
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('Referrer-Policy', 'no-referrer');
  try {
    const url = new URL(request.url, `http://${request.headers.host || host}`);
    if (request.method === 'GET' && url.pathname === '/api/graph') {
      sendJson(response, 200, readGraph());
      return;
    }
    if (request.method === 'GET' && url.pathname === '/api/health') {
      sendJson(response, 200, { status: 'ok', engine: 'native-mmap' });
      return;
    }
    if (request.method === 'POST' && url.pathname === '/api/demo') {
      sendJson(response, 201, resetDemo());
      return;
    }
    if (request.method === 'POST' && url.pathname === '/api/fork') {
      const body = await readJson(request);
      const nodeId = Number(body.nodeId);
      const prompt = typeof body.prompt === 'string' ? body.prompt.trim() : '';
      if (!Number.isSafeInteger(nodeId) || nodeId < 1 || !prompt || prompt.length > 2048) {
        sendJson(response, 400, { error: 'nodeId and a prompt of at most 2048 characters are required' });
        return;
      }
      sendJson(response, 201, runCli(['branch', workspace, String(nodeId), prompt]));
      return;
    }
    if (request.method === 'GET' || request.method === 'HEAD') {
      serveStatic(request, response);
      return;
    }
    response.writeHead(405, { Allow: 'GET, HEAD, POST' }).end('Method not allowed');
  } catch (error) {
    sendJson(response, 500, { error: error instanceof Error ? error.message : 'Internal error' });
  }
});

server.listen(port, host, () => {
  console.log(`GNU TimeWeaver is running at http://${host}:${port}`);
  console.log(`Workspace: ${workspace}`);
});
