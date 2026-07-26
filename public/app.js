const graphSvg = document.querySelector('#graph');
const graphScroll = document.querySelector('#graph-scroll');
const promptEditor = document.querySelector('#prompt-editor');
const forkButton = document.querySelector('#fork-button');
const resetButton = document.querySelector('#reset-button');
const actionMessage = document.querySelector('#action-message');

let graphData = null;
let selectedId = null;

const statusNames = new Map([
  [0, 'checkpoint'], [1, 'running'], [2, 'success'], [3, 'error'], [4, 'fork'],
]);

function el(name, attributes = {}, text = '') {
  const node = document.createElementNS('http://www.w3.org/2000/svg', name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text) node.textContent = text;
  return node;
}

function descendantsLayout(nodes) {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const children = new Map(nodes.map((node) => [node.id, []]));
  const roots = [];
  for (const node of nodes) {
    if (node.parentId && children.has(node.parentId)) children.get(node.parentId).push(node.id);
    else roots.push(node.id);
  }
  let leaf = 0;
  const positions = new Map();
  function place(id, depth) {
    const kids = children.get(id) || [];
    const childYs = kids.map((child) => place(child, depth + 1));
    const y = childYs.length ? childYs.reduce((sum, value) => sum + value, 0) / childYs.length : leaf++ * 112 + 70;
    positions.set(id, { x: depth * 176 + 40, y });
    return y;
  }
  roots.forEach((id) => place(id, 0));
  return { positions, width: Math.max(720, ...[...positions.values()].map((p) => p.x + 180)), height: Math.max(420, leaf * 112 + 40), byId };
}

function renderGraph() {
  graphSvg.replaceChildren();
  const { positions, width, height, byId } = descendantsLayout(graphData.nodes);
  graphSvg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  graphSvg.setAttribute('width', width);
  graphSvg.setAttribute('height', height);

  for (const node of graphData.nodes) {
    if (!node.parentId) continue;
    const from = positions.get(node.parentId);
    const to = positions.get(node.id);
    const startX = from.x + 136;
    const endX = to.x;
    const middle = (startX + endX) / 2;
    const parent = byId.get(node.parentId);
    graphSvg.append(el('path', {
      d: `M ${startX} ${from.y} C ${middle} ${from.y}, ${middle} ${to.y}, ${endX} ${to.y}`,
      class: `edge ${node.status === 4 || parent?.status === 4 ? 'fork-edge' : ''}`,
    }));
  }

  for (const node of graphData.nodes) {
    const position = positions.get(node.id);
    const status = statusNames.get(node.status) || 'checkpoint';
    const group = el('g', {
      class: `node ${status}${node.id === selectedId ? ' selected' : ''}`,
      transform: `translate(${position.x} ${position.y - 34})`,
      tabindex: '0', role: 'button', 'aria-label': `Node ${node.id}, ${node.label}, ${status}`,
    });
    group.append(el('rect', { width: 136, height: 68 }));
    group.append(el('rect', { class: 'node-accent', width: 4, height: 68, rx: 2 }));
    group.append(el('text', { x: 13, y: 18, class: 'node-id' }, `#${node.id}  ${status.toUpperCase()}`));
    group.append(el('text', { x: 13, y: 38 }, node.label.length > 18 ? `${node.label.slice(0, 17)}…` : node.label));
    group.append(el('text', { x: 13, y: 55, class: 'node-pages' }, `${node.changedPages}/${node.pages} pages changed`));
    group.addEventListener('click', () => selectNode(node.id));
    group.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') selectNode(node.id);
    });
    graphSvg.append(group);
  }
}

function selectNode(id) {
  selectedId = id;
  const node = graphData.nodes.find((candidate) => candidate.id === id);
  const status = statusNames.get(node.status) || 'checkpoint';
  document.querySelector('#node-title').textContent = `#${node.id} ${node.label}`;
  const badge = document.querySelector('#node-status');
  badge.textContent = status;
  badge.className = `status-badge ${status}`;
  document.querySelector('#node-hash').textContent = node.stateHash;
  document.querySelector('#node-pages').textContent = `${node.changedPages} of ${node.pages}`;
  document.querySelector('#node-tokens').textContent = node.memory.tokensProcessed.toLocaleString();
  document.querySelector('#node-prefix').textContent = `${node.memory.prefixStepsReused} steps`;
  promptEditor.value = node.memory.prompt;
  promptEditor.disabled = false;
  forkButton.disabled = false;
  document.querySelector('#node-memory').textContent = JSON.stringify({
    schema: node.memory.schema || null,
    dialect: node.memory.dialect || null,
    response: node.memory.response || null,
    error: node.memory.error || null,
  }, null, 2);
  actionMessage.textContent = node.status === 3
    ? 'Change the prompt, then fork. Dependency invalidation resumes at dialect selection.'
    : node.note;
  actionMessage.className = 'action-message';
  renderGraph();
}

function updateSummary() {
  document.querySelector('#metric-nodes').textContent = graphData.stats.nodes;
  document.querySelector('#metric-pages').textContent = graphData.stats.physicalPages;
  document.querySelector('#metric-saved').textContent = `${(graphData.stats.savedRatio * 100).toFixed(1)}%`;
  document.querySelector('#metric-shared').textContent = graphData.stats.sharedReferences;
  document.querySelector('#head-id').textContent = `#${graphData.head}`;
  document.querySelector('#graph-caption').textContent = `${graphData.stats.logicalPages} logical page references mapped locally`;
}

async function request(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed with ${response.status}`);
  return body;
}

async function loadGraph(preferredNode) {
  graphData = await request('/api/graph');
  updateSummary();
  selectedId = preferredNode || selectedId || graphData.nodes.find((node) => node.status === 3)?.id || graphData.head;
  renderGraph();
  selectNode(graphData.nodes.some((node) => node.id === selectedId) ? selectedId : graphData.head);
  requestAnimationFrame(() => {
    const selected = graphSvg.querySelector('.selected');
    if (!selected) return;
    const box = selected.getBBox();
    graphScroll.scrollTo({
      left: Math.max(0, box.x - graphScroll.clientWidth / 2 + box.width / 2),
      top: Math.max(0, box.y - graphScroll.clientHeight / 2 + box.height / 2),
      behavior: 'smooth',
    });
  });
}

forkButton.addEventListener('click', async () => {
  forkButton.disabled = true;
  actionMessage.textContent = 'Mapping branch pages and resuming the local agent...';
  try {
    const next = await request('/api/fork', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nodeId: selectedId, prompt: promptEditor.value }),
    });
    graphData = next;
    selectedId = next.head;
    updateSummary();
    renderGraph();
    selectNode(selectedId);
    actionMessage.textContent = 'Branch completed. Unchanged prefix pages were retained.';
  } catch (error) {
    actionMessage.textContent = error.message;
    actionMessage.className = 'action-message error';
  } finally {
    forkButton.disabled = false;
  }
});

resetButton.addEventListener('click', async () => {
  resetButton.disabled = true;
  try {
    graphData = await request('/api/demo', { method: 'POST' });
    selectedId = graphData.nodes.find((node) => node.status === 3)?.id || graphData.head;
    updateSummary();
    renderGraph();
    selectNode(selectedId);
  } catch (error) {
    actionMessage.textContent = error.message;
    actionMessage.className = 'action-message error';
  } finally {
    resetButton.disabled = false;
  }
});

loadGraph().catch((error) => {
  actionMessage.textContent = error.message;
  actionMessage.className = 'action-message error';
});
