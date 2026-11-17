'use strict';
const { execFileSync } = require('child_process');

function detect(cwd, env = process.env) {
  const remote = execFileSync('git', ['remote', 'get-url', 'origin'], { cwd, encoding: 'utf8' }).trim();
  const url = remote.includes('://') ? new URL(remote) : new URL(`ssh://${remote.replace(':', '/')}`);
  const host = url.hostname.toLowerCase();
  const repo = url.pathname.replace(/^\//, '').replace(/\.git$/, '');
  const provider = host === 'github.com' ? 'github' : host === 'gitee.com' ? 'gitee'
    : /^gitlab\./.test(host) || (env.ATHENA_GITLAB_HOSTS || '').split(',').includes(host) ? 'gitlab' : '';
  if (!provider) throw new Error(`unsupported tracker host ${host}; configure self-hosted GitLab with ATHENA_GITLAB_HOSTS`);
  return { cwd, env, host, repo, provider };
}

async function request(t, method, endpoint, data) {
  if (t.provider === 'gitee') {
    if (!t.env.GITEE_TOKEN) throw new Error('GITEE_TOKEN is required');
    const response = await fetch(`${t.env.ATHENA_GITEE_API_URL || 'https://gitee.com/api/v5'}/${endpoint}`, {
      method, headers: { Authorization: `Bearer ${t.env.GITEE_TOKEN}`, 'Content-Type': 'application/json' },
      ...(data ? { body: JSON.stringify(data) } : {}),
    });
    if (!response.ok) throw new Error(`gitee ${method} failed (${response.status})`);
    const text = await response.text();
    return text ? JSON.parse(text) : null;
  }
  const cli = t.provider === 'github' ? 'gh' : 'glab';
  const args = ['api', '--hostname', t.host, '--method', method, endpoint];
  if (data) args.push('--input', '-');
  try {
    const text = execFileSync(cli, args, { cwd: t.cwd, env: t.env, encoding: 'utf8', input: data ? JSON.stringify(data) : undefined, stdio: ['pipe', 'pipe', 'pipe'] });
    return text.trim() ? JSON.parse(text) : null;
  } catch (_) { throw new Error(`${cli} ${method} ${endpoint} failed; check tracker authentication and permissions`); }
}

function base(t) { return t.provider === 'gitlab' ? `projects/${encodeURIComponent(t.repo)}/issues` : `repos/${t.repo}/issues`; }
function update(t, n) { return t.provider === 'gitee' ? `repos/${t.repo.split('/')[0]}/issues/${n}` : `${base(t)}/${n}`; }
function normalize(t, issue) {
  return { number: String(issue.iid || issue.number), title: issue.title, body: issue.description || issue.body || '',
    url: issue.web_url || issue.html_url, labels: (issue.labels || []).map(l => typeof l === 'string' ? l : l.name),
    assignees: (issue.assignees || (issue.assignee ? [issue.assignee] : [])).map(a => a.login || a.username),
    state: issue.state, pr: !!issue.pull_request };
}
// Gitee 的「进行中」是独立状态 progressing，仍算开放
const OPEN = ['open', 'opened', 'progressing'];
async function me(t) {
  const user = await request(t, 'GET', 'user');
  const email = execFileSync('git', ['config', 'user.email'], { cwd: t.cwd, encoding: 'utf8' }).trim();
  let emails = user.email ? [user.email] : [];
  if (!emails.some(value => value.toLowerCase() === email.toLowerCase())) {
    const extra = await request(t, 'GET', t.provider === 'gitee' ? 'emails' : 'user/emails').catch((error) => {
      throw t.provider === 'github' ? new Error(`${error.message}; reading account emails needs the user scope: gh auth refresh -s user`) : error;
    });
    emails = emails.concat(extra.map(value => typeof value === 'string' ? value : value.email));
  }
  if (!emails.some(value => value.toLowerCase() === email.toLowerCase())) throw new Error('tracker account does not match git user.email; authenticate as the human DRI');
  return { login: user.login || user.username, id: user.id };
}
async function list(t) {
  const user = await me(t);
  const found = [];
  for (let page = 1; ; page += 1) {
    const rows = await request(t, 'GET', `${base(t)}?state=${t.provider === 'gitlab' ? 'opened' : 'open'}&per_page=100&page=${page}${t.provider === 'gitlab' ? '&scope=all' : ''}`);
    found.push(...rows.map(i => normalize(t, i)).filter(i => !i.pr && OPEN.includes(i.state) &&
      (i.assignees.includes(user.login) || (!i.assignees.length && i.labels.includes('agent-ok')))));
    if (rows.length < 100) return found;
  }
}
async function claim(t, n) {
  const user = await me(t);
  const issue = normalize(t, await request(t, 'GET', `${base(t)}/${n}`));
  if (!OPEN.includes(issue.state) || issue.pr) throw new Error(`issue ${n} is not an open issue`);
  const others = issue.assignees.filter(a => a !== user.login);
  if (others.length) throw new Error(`issue ${n} already claimed by ${others.join(', ')}; ask them to unassign first`);
  const labels = [...new Set([...issue.labels, 'in-progress'])];
  const data = t.provider === 'github' ? { assignees: [user.login], labels }
    : t.provider === 'gitlab' ? { assignee_ids: [user.id], add_labels: 'in-progress' }
      : { repo: t.repo.split('/')[1], assignee: user.login, labels: labels.join(',') };
  const claimed = normalize(t, await request(t, t.provider === 'gitlab' ? 'PUT' : 'PATCH', update(t, n), data));
  if (!claimed.assignees.includes(user.login) || !claimed.labels.includes('in-progress')) throw new Error(`issue ${n} claim was not applied; check tracker permissions`);
  return issue;
}
async function comment(t, n, body) {
  return request(t, 'POST', `${base(t)}/${n}/${t.provider === 'gitlab' ? 'notes' : 'comments'}`, { body });
}
async function close(t, n) {
  return request(t, t.provider === 'gitlab' ? 'PUT' : 'PATCH', update(t, n), t.provider === 'gitlab'
    ? { state_event: 'close' } : { state: 'closed', ...(t.provider === 'gitee' ? { repo: t.repo.split('/')[1] } : {}) });
}
async function create(t, title, body) {
  const endpoint = t.provider === 'gitee' ? `repos/${t.repo.split('/')[0]}/issues` : base(t);
  return normalize(t, await request(t, 'POST', endpoint, { title, [t.provider === 'gitlab' ? 'description' : 'body']: body,
    ...(t.provider === 'gitee' ? { repo: t.repo.split('/')[1] } : {}) }));
}
module.exports = { detect, list, claim, comment, close, create };
