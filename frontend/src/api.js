const API_BASE = 'http://localhost:8000/api';

export async function getAgents() {
  const res = await fetch(`${API_BASE}/agents`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
}

export async function createAgent(agent) {
  const res = await fetch(`${API_BASE}/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agent)
  });
  if (!res.ok) throw new Error('Failed to create agent');
  return res.json();
}

export async function deleteAgent(agentId) {
  const res = await fetch(`${API_BASE}/agents/${agentId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete agent');
  return res.json();
}

export async function runWorkflow(inputData) {
  const res = await fetch(`${API_BASE}/workflow/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input_data: inputData })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to run workflow');
  }
  return res.json();
}

export async function submitFeedback(runId, action) {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, action })
  });
  if (!res.ok) throw new Error('Failed to submit feedback');
  return res.json();
}

export async function getWeights() {
  const res = await fetch(`${API_BASE}/weights`);
  if (!res.ok) throw new Error('Failed to fetch weights');
  return res.json();
}

export async function getNextMockEmail() {
  const res = await fetch(`${API_BASE}/mock-email/next`);
  if (!res.ok) throw new Error('Failed to fetch mock email');
  return res.json();
}

export async function getGmailEmails() {
  const res = await fetch(`${API_BASE}/emails`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to fetch Gmail emails');
  }
  return res.json();
}

export async function setupDemo() {
  const res = await fetch(`${API_BASE}/demo/setup`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to setup demo');
  return res.json();
}

export async function getRunHistory() {
  const res = await fetch(`${API_BASE}/workflow/runs`);
  if (!res.ok) throw new Error('Failed to fetch run history');
  return res.json();
}

export async function getRunDetails(runId) {
  const res = await fetch(`${API_BASE}/workflow/runs/${runId}`);
  if (!res.ok) throw new Error('Failed to fetch run details');
  return res.json();
}

export function subscribeToLogs(runId, onLog, onComplete) {
  const eventSource = new EventSource(`${API_BASE}/stream/${runId}`);
  
  eventSource.addEventListener('log', (event) => {
    const log = JSON.parse(event.data);
    onLog(log);
  });
  
  eventSource.addEventListener('complete', (event) => {
    onComplete();
    eventSource.close();
  });
  
  eventSource.onerror = () => {
    eventSource.close();
  };
  
  return () => eventSource.close();
}
