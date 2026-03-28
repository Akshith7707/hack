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

export async function getWeightsWithHistory() {
  const res = await fetch(`${API_BASE}/weights/history`);
  if (!res.ok) throw new Error('Failed to fetch weights history');
  return res.json();
}

// Workflow CRUD
export async function getWorkflows() {
  const res = await fetch(`${API_BASE}/workflows`);
  if (!res.ok) throw new Error('Failed to fetch workflows');
  return res.json();
}

export async function getWorkflow(workflowId) {
  const res = await fetch(`${API_BASE}/workflows/${workflowId}`);
  if (!res.ok) throw new Error('Failed to fetch workflow');
  return res.json();
}

export async function createWorkflow(workflow) {
  const res = await fetch(`${API_BASE}/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow)
  });
  if (!res.ok) throw new Error('Failed to create workflow');
  return res.json();
}

export async function updateWorkflow(workflowId, workflow) {
  const res = await fetch(`${API_BASE}/workflows/${workflowId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow)
  });
  if (!res.ok) throw new Error('Failed to update workflow');
  return res.json();
}

export async function deleteWorkflow(workflowId) {
  const res = await fetch(`${API_BASE}/workflows/${workflowId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete workflow');
  return res.json();
}

export async function runWorkflowById(workflowId, triggerData = {}) {
  const res = await fetch(`${API_BASE}/workflows/${workflowId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trigger_data: triggerData })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to run workflow');
  }
  return res.json();
}

// Executions
export async function getExecutions(limit = 20) {
  const res = await fetch(`${API_BASE}/executions?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch executions');
  return res.json();
}

export async function getExecution(executionId) {
  const res = await fetch(`${API_BASE}/executions/${executionId}`);
  if (!res.ok) throw new Error('Failed to fetch execution');
  return res.json();
}

export async function submitExecutionFeedback(executionId, action) {
  const res = await fetch(`${API_BASE}/executions/${executionId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action })
  });
  if (!res.ok) throw new Error('Failed to submit feedback');
  return res.json();
}

// Drift management
export async function resetAgentDrift(agentId) {
  const res = await fetch(`${API_BASE}/agents/${agentId}/reset-drift`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to reset drift');
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

// ============== TEMPLATES ==============

export async function getTemplates(category = null) {
  const url = category
    ? `${API_BASE}/templates?category=${category}`
    : `${API_BASE}/templates`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch templates');
  return res.json();
}

export async function getTemplateCategories() {
  const res = await fetch(`${API_BASE}/templates/categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

export async function getTemplate(templateId) {
  const res = await fetch(`${API_BASE}/templates/${templateId}`);
  if (!res.ok) throw new Error('Failed to fetch template');
  return res.json();
}

export async function cloneTemplate(templateId, name = null) {
  const res = await fetch(`${API_BASE}/templates/${templateId}/clone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  });
  if (!res.ok) throw new Error('Failed to clone template');
  return res.json();
}

export async function createTemplate(template) {
  const res = await fetch(`${API_BASE}/templates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(template)
  });
  if (!res.ok) throw new Error('Failed to create template');
  return res.json();
}

// ============== INTEGRATIONS ==============

export async function getIntegrations() {
  const res = await fetch(`${API_BASE}/integrations`);
  if (!res.ok) throw new Error('Failed to fetch integrations');
  return res.json();
}

// ============== PROMPT OPTIMIZATION ==============

export async function getAgentPerformance(agentId) {
  const res = await fetch(`${API_BASE}/agents/${agentId}/performance`);
  if (!res.ok) throw new Error('Failed to fetch performance');
  return res.json();
}

export async function getPendingSuggestions(agentId = null) {
  const url = agentId
    ? `${API_BASE}/prompt-suggestions?agent_id=${agentId}`
    : `${API_BASE}/prompt-suggestions`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch suggestions');
  return res.json();
}

export async function applySuggestion(suggestionId) {
  const res = await fetch(`${API_BASE}/prompt-suggestions/${suggestionId}/apply`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to apply suggestion');
  return res.json();
}

export async function rejectSuggestion(suggestionId) {
  const res = await fetch(`${API_BASE}/prompt-suggestions/${suggestionId}/reject`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to reject suggestion');
  return res.json();
}

export async function getPromptHistory(agentId) {
  const res = await fetch(`${API_BASE}/agents/${agentId}/prompt-history`);
  if (!res.ok) throw new Error('Failed to fetch prompt history');
  return res.json();
}

export async function updateAgentPrompt(agentId, prompt) {
  const res = await fetch(`${API_BASE}/agents/${agentId}/prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  if (!res.ok) throw new Error('Failed to update prompt');
  return res.json();
}


