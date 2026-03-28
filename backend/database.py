import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "FlexCode.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Agents table with drift detection columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            goal TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('classifier','worker','supervisor','decision')),
            style TEXT DEFAULT NULL,
            model TEXT DEFAULT 'Qwen/Qwen2.5-7B-Instruct',
            drift_flag INTEGER DEFAULT 0,
            drift_suggestion TEXT DEFAULT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Migration: add drift columns if missing
    cursor.execute("PRAGMA table_info(agents)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'drift_flag' not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN drift_flag INTEGER DEFAULT 0")
    if 'drift_suggestion' not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN drift_suggestion TEXT DEFAULT NULL")
    
    # Agent weights with total_runs tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_weights (
            agent_id TEXT PRIMARY KEY,
            style TEXT,
            weight REAL DEFAULT 0.33,
            times_selected INTEGER DEFAULT 0,
            times_accepted INTEGER DEFAULT 0,
            times_rejected INTEGER DEFAULT 0,
            total_runs INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0.0,
            FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
        )
    """)
    
    # Migration: add total_runs if missing
    cursor.execute("PRAGMA table_info(agent_weights)")
    weight_cols = [col[1] for col in cursor.fetchall()]
    if 'total_runs' not in weight_cols:
        cursor.execute("ALTER TABLE agent_weights ADD COLUMN total_runs INTEGER DEFAULT 0")
    if 'avg_score' not in weight_cols:
        cursor.execute("ALTER TABLE agent_weights ADD COLUMN avg_score REAL DEFAULT 0.0")
    
    # Workflows table (like Zapier Zaps)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            trigger_type TEXT DEFAULT 'manual',
            nodes TEXT,
            edges TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    
    # Executions table (workflow run instances)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            trigger_data TEXT,
            status TEXT DEFAULT 'running',
            results TEXT,
            selected_agent_id TEXT,
            selected_agent_name TEXT,
            final_output TEXT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        )
    """)
    
    # Execution logs (per-node logs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            node_id TEXT,
            agent_id TEXT,
            agent_name TEXT,
            agent_type TEXT,
            input_text TEXT,
            output_text TEXT,
            score REAL,
            duration_ms INTEGER,
            step_order INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (execution_id) REFERENCES executions(id)
        )
    """)
    
    # Legacy workflow_runs table (keep for backwards compatibility)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            input_data TEXT,
            classification TEXT,
            worker_outputs TEXT,
            supervisor_review TEXT,
            decision_output TEXT,
            selected_agent TEXT,
            final_output TEXT,
            context_signals TEXT,
            feedback TEXT DEFAULT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            agent_id TEXT,
            agent_name TEXT,
            agent_type TEXT,
            input_text TEXT,
            output_text TEXT,
            step_order INTEGER,
            timestamp TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            execution_id TEXT,
            agent_id TEXT,
            selected_agent TEXT,
            action TEXT NOT NULL CHECK(action IN ('accept','reject')),
            score REAL,
            context TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Migration: add agent_id to feedback_log if missing
    cursor.execute("PRAGMA table_info(feedback_log)")
    feedback_cols = [col[1] for col in cursor.fetchall()]
    if 'agent_id' not in feedback_cols:
        cursor.execute("ALTER TABLE feedback_log ADD COLUMN agent_id TEXT")
    if 'execution_id' not in feedback_cols:
        cursor.execute("ALTER TABLE feedback_log ADD COLUMN execution_id TEXT")
    if 'score' not in feedback_cols:
        cursor.execute("ALTER TABLE feedback_log ADD COLUMN score REAL")
    
    # Weight history for charting
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            weight REAL NOT NULL,
            run_number INTEGER,
            timestamp TEXT NOT NULL
        )
    """)

    # Workflow templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            icon TEXT DEFAULT '...',
            nodes TEXT NOT NULL,
            edges TEXT NOT NULL,
            use_count INTEGER DEFAULT 0,
            is_featured INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_templates_category
        ON workflow_templates(category)
    """)

    # Prompt versions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            performance_score REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    """)

    # Prompt suggestions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_suggestions (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            current_prompt TEXT NOT NULL,
            suggested_prompt TEXT NOT NULL,
            reasoning TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    """)

    # Migration: add custom_prompt column to agents if missing
    cursor.execute("PRAGMA table_info(agents)")
    agent_cols = [col[1] for col in cursor.fetchall()]
    if 'custom_prompt' not in agent_cols:
        cursor.execute("ALTER TABLE agents ADD COLUMN custom_prompt TEXT DEFAULT NULL")

    conn.commit()
    conn.close()


# Agent CRUD
def create_agent(agent_id: str, name: str, role: str, goal: str, agent_type: str, style: Optional[str] = None) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO agents (id, name, role, goal, type, style, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (agent_id, name, role, goal, agent_type, style, created_at))
    
    if agent_type == 'worker' and style:
        cursor.execute("""
            INSERT INTO agent_weights (agent_id, style, weight, times_selected, times_accepted, times_rejected)
            VALUES (?, ?, 0.33, 0, 0, 0)
        """, (agent_id, style))
    
    conn.commit()
    conn.close()
    
    return {
        "id": agent_id,
        "name": name,
        "role": role,
        "goal": goal,
        "type": agent_type,
        "style": style,
        "created_at": created_at
    }


def get_all_agents() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, w.weight, w.times_selected, w.times_accepted, w.times_rejected
        FROM agents a
        LEFT JOIN agent_weights w ON a.id = w.agent_id
        ORDER BY a.created_at
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_agents_by_type(agent_type: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, w.weight, w.times_selected, w.times_accepted, w.times_rejected
        FROM agents a
        LEFT JOIN agent_weights w ON a.id = w.agent_id
        WHERE a.type = ?
        ORDER BY a.created_at
    """, (agent_type,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_agent_by_id(agent_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, w.weight, w.times_selected, w.times_accepted, w.times_rejected
        FROM agents a
        LEFT JOIN agent_weights w ON a.id = w.agent_id
        WHERE a.id = ?
    """, (agent_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_agent(agent_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM agent_weights WHERE agent_id = ?", (agent_id,))
    cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0


# Weight operations
def get_weights() -> Dict[str, float]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.id, a.name, a.style, w.weight, w.times_selected, w.times_accepted, w.times_rejected
        FROM agents a
        JOIN agent_weights w ON a.id = w.agent_id
        WHERE a.type = 'worker'
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return {row['id']: dict(row) for row in rows}


def update_weight(agent_id: str, new_weight: float):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agent_weights SET weight = ? WHERE agent_id = ?
    """, (new_weight, agent_id))
    
    conn.commit()
    conn.close()


def increment_selected(agent_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agent_weights SET times_selected = times_selected + 1 WHERE agent_id = ?
    """, (agent_id,))
    
    conn.commit()
    conn.close()


def increment_accepted(agent_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agent_weights SET times_accepted = times_accepted + 1 WHERE agent_id = ?
    """, (agent_id,))
    
    conn.commit()
    conn.close()


def increment_rejected(agent_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agent_weights SET times_rejected = times_rejected + 1 WHERE agent_id = ?
    """, (agent_id,))
    
    conn.commit()
    conn.close()


# Workflow runs
def save_run(run_data: Dict) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO workflow_runs (id, input_data, classification, worker_outputs, supervisor_review,
                                   decision_output, selected_agent, final_output, context_signals, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_data['id'],
        run_data['input_data'],
        run_data.get('classification'),
        json.dumps(run_data.get('worker_outputs', [])),
        run_data.get('supervisor_review'),
        run_data.get('decision_output'),
        run_data.get('selected_agent'),
        run_data.get('final_output'),
        json.dumps(run_data.get('context_signals', {})),
        run_data['created_at']
    ))
    
    conn.commit()
    conn.close()
    
    return run_data['id']


def save_log_entry(run_id: str, agent_id: str, agent_name: str, agent_type: str, 
                   input_text: str, output_text: str, step_order: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO run_logs (run_id, agent_id, agent_name, agent_type, input_text, output_text, step_order, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, agent_id, agent_name, agent_type, input_text, output_text, step_order, datetime.utcnow().isoformat()))
    
    conn.commit()
    conn.close()


def get_run(run_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM workflow_runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data = dict(row)
        data['worker_outputs'] = json.loads(data['worker_outputs']) if data['worker_outputs'] else []
        data['context_signals'] = json.loads(data['context_signals']) if data['context_signals'] else {}
        return data
    return None


def get_run_logs(run_id: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM run_logs WHERE run_id = ? ORDER BY step_order", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_runs(limit: int = 50) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        data = dict(row)
        data['worker_outputs'] = json.loads(data['worker_outputs']) if data['worker_outputs'] else []
        data['context_signals'] = json.loads(data['context_signals']) if data['context_signals'] else {}
        results.append(data)
    
    return results


# Feedback
def save_feedback(run_id: str, selected_agent: str, action: str, context: Optional[str] = None, 
                  agent_id: Optional[str] = None, execution_id: Optional[str] = None, score: Optional[float] = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO feedback_log (run_id, execution_id, agent_id, selected_agent, action, score, context, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, execution_id, agent_id, selected_agent, action, score, context, datetime.utcnow().isoformat()))
    
    # Update legacy workflow_runs if run_id exists
    if run_id:
        cursor.execute("UPDATE workflow_runs SET feedback = ? WHERE id = ?", (action, run_id))
    
    # Update executions if execution_id exists
    if execution_id:
        cursor.execute("UPDATE executions SET status = 'completed' WHERE id = ?", (execution_id,))
    
    conn.commit()
    conn.close()


def get_recent_rejection_count(limit: int = 5) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM feedback_log 
        WHERE action = 'reject' 
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    
    row = cursor.fetchone()
    conn.close()
    
    return row['count'] if row else 0


# ============== WORKFLOW CRUD ==============

def create_workflow(workflow_id: str, name: str, description: str = None, 
                    trigger_type: str = 'manual', nodes: List = None, edges: List = None) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO workflows (id, name, description, trigger_type, nodes, edges, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (workflow_id, name, description, trigger_type, 
          json.dumps(nodes or []), json.dumps(edges or []), now, now))
    
    conn.commit()
    conn.close()
    
    return {
        "id": workflow_id,
        "name": name,
        "description": description,
        "trigger_type": trigger_type,
        "nodes": nodes or [],
        "edges": edges or [],
        "is_active": True,
        "created_at": now
    }


def get_all_workflows() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM workflows ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        data = dict(row)
        data['nodes'] = json.loads(data['nodes']) if data['nodes'] else []
        data['edges'] = json.loads(data['edges']) if data['edges'] else []
        data['is_active'] = bool(data['is_active'])
        results.append(data)
    
    return results


def get_workflow(workflow_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data = dict(row)
        data['nodes'] = json.loads(data['nodes']) if data['nodes'] else []
        data['edges'] = json.loads(data['edges']) if data['edges'] else []
        data['is_active'] = bool(data['is_active'])
        return data
    return None


def update_workflow(workflow_id: str, **kwargs) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    for key, value in kwargs.items():
        if key in ['name', 'description', 'trigger_type', 'is_active']:
            updates.append(f"{key} = ?")
            values.append(value)
        elif key in ['nodes', 'edges']:
            updates.append(f"{key} = ?")
            values.append(json.dumps(value))
    
    if updates:
        updates.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(workflow_id)
        
        cursor.execute(f"UPDATE workflows SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return True


def delete_workflow(workflow_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected > 0


# ============== EXECUTION CRUD ==============

def create_execution(execution_id: str, workflow_id: str = None, trigger_data: str = None) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO executions (id, workflow_id, trigger_data, status, started_at)
        VALUES (?, ?, ?, 'running', ?)
    """, (execution_id, workflow_id, trigger_data, now))
    
    conn.commit()
    conn.close()
    
    return {
        "id": execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "started_at": now
    }


def update_execution(execution_id: str, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    for key, value in kwargs.items():
        if key == 'results':
            updates.append(f"{key} = ?")
            values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
        elif key in ['status', 'selected_agent_id', 'selected_agent_name', 'final_output', 'completed_at']:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if updates:
        values.append(execution_id)
        cursor.execute(f"UPDATE executions SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()


def get_execution(execution_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM executions WHERE id = ?", (execution_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data = dict(row)
        data['results'] = json.loads(data['results']) if data['results'] else None
        return data
    return None


def get_execution_logs(execution_id: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM execution_logs WHERE execution_id = ? ORDER BY step_order, timestamp
    """, (execution_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def save_execution_log(execution_id: str, node_id: str, agent_id: str, agent_name: str,
                       agent_type: str, input_text: str, output_text: str, 
                       score: float = None, duration_ms: int = None, step_order: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO execution_logs (execution_id, node_id, agent_id, agent_name, agent_type,
                                    input_text, output_text, score, duration_ms, step_order, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (execution_id, node_id, agent_id, agent_name, agent_type, 
          input_text, output_text, score, duration_ms, step_order, datetime.utcnow().isoformat()))
    
    conn.commit()
    conn.close()


def get_recent_executions(limit: int = 20) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, w.name as workflow_name 
        FROM executions e
        LEFT JOIN workflows w ON e.workflow_id = w.id
        ORDER BY e.started_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        data = dict(row)
        data['results'] = json.loads(data['results']) if data['results'] else None
        results.append(data)
    
    return results


# ============== DRIFT DETECTION ==============

def set_agent_drift(agent_id: str, drift_flag: bool, suggestion: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agents SET drift_flag = ?, drift_suggestion = ? WHERE id = ?
    """, (1 if drift_flag else 0, suggestion, agent_id))
    
    conn.commit()
    conn.close()


def reset_agent_drift(agent_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agents SET drift_flag = 0, drift_suggestion = NULL WHERE id = ?
    """, (agent_id,))
    
    conn.commit()
    conn.close()


def get_agent_feedback_history(agent_id: str, limit: int = 10) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM feedback_log WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?
    """, (agent_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def save_weight_history(agent_id: str, weight: float, run_number: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO weight_history (agent_id, weight, run_number, timestamp)
        VALUES (?, ?, ?, ?)
    """, (agent_id, weight, run_number, datetime.utcnow().isoformat()))
    
    conn.commit()
    conn.close()


def get_weight_history(agent_id: str = None, limit: int = 100) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if agent_id:
        cursor.execute("""
            SELECT * FROM weight_history WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?
        """, (agent_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM weight_history ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def increment_total_runs(agent_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agent_weights SET total_runs = total_runs + 1 WHERE agent_id = ?
    """, (agent_id,))

    conn.commit()
    conn.close()


# ============== WORKFLOW TEMPLATES ==============

def create_template(template_id: str, name: str, description: str, category: str,
                    icon: str, nodes: List, edges: List, is_featured: bool = False) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO workflow_templates
        (id, name, description, category, icon, nodes, edges, is_featured, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (template_id, name, description, category, icon,
          json.dumps(nodes), json.dumps(edges), 1 if is_featured else 0, now, now))

    conn.commit()
    conn.close()

    return {
        "id": template_id,
        "name": name,
        "description": description,
        "category": category,
        "icon": icon,
        "nodes": nodes,
        "edges": edges,
        "is_featured": is_featured,
        "use_count": 0,
        "created_at": now
    }


def get_all_templates(category: str = None) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT * FROM workflow_templates WHERE category = ?
            ORDER BY is_featured DESC, use_count DESC
        """, (category,))
    else:
        cursor.execute("""
            SELECT * FROM workflow_templates
            ORDER BY is_featured DESC, use_count DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        data = dict(row)
        data['nodes'] = json.loads(data['nodes'])
        data['edges'] = json.loads(data['edges'])
        data['is_featured'] = bool(data['is_featured'])
        results.append(data)

    return results


def get_template(template_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM workflow_templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        data = dict(row)
        data['nodes'] = json.loads(data['nodes'])
        data['edges'] = json.loads(data['edges'])
        data['is_featured'] = bool(data['is_featured'])
        return data
    return None


def increment_template_usage(template_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE workflow_templates SET use_count = use_count + 1 WHERE id = ?
    """, (template_id,))

    conn.commit()
    conn.close()


def clone_template_to_workflow(template_id: str, user_name: str = None) -> Dict:
    """Clone a template into a new workflow"""
    import uuid
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")

    workflow_id = str(uuid.uuid4())
    name = f"{template['name']}" + (f" ({user_name})" if user_name else " (Copy)")

    workflow = create_workflow(
        workflow_id=workflow_id,
        name=name,
        description=template['description'],
        trigger_type='manual',
        nodes=template['nodes'],
        edges=template['edges']
    )

    increment_template_usage(template_id)

    return workflow


# ============== PROMPT OPTIMIZATION ==============

def save_prompt_suggestion(suggestion_id: str, agent_id: str, current_prompt: str,
                           suggested_prompt: str, reasoning: str = None) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO prompt_suggestions
        (id, agent_id, current_prompt, suggested_prompt, reasoning, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
    """, (suggestion_id, agent_id, current_prompt, suggested_prompt, reasoning, now))

    conn.commit()
    conn.close()

    return {
        "id": suggestion_id,
        "agent_id": agent_id,
        "current_prompt": current_prompt,
        "suggested_prompt": suggested_prompt,
        "reasoning": reasoning,
        "status": "pending",
        "created_at": now
    }


def get_pending_suggestions(agent_id: str = None) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    if agent_id:
        cursor.execute("""
            SELECT ps.*, a.name as agent_name, a.style
            FROM prompt_suggestions ps
            JOIN agents a ON ps.agent_id = a.id
            WHERE ps.agent_id = ? AND ps.status = 'pending'
            ORDER BY ps.created_at DESC
        """, (agent_id,))
    else:
        cursor.execute("""
            SELECT ps.*, a.name as agent_name, a.style
            FROM prompt_suggestions ps
            JOIN agents a ON ps.agent_id = a.id
            WHERE ps.status = 'pending'
            ORDER BY ps.created_at DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_suggestion_status(suggestion_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE prompt_suggestions SET status = ? WHERE id = ?
    """, (status, suggestion_id))

    conn.commit()
    conn.close()


def get_suggestion(suggestion_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM prompt_suggestions WHERE id = ?", (suggestion_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def update_agent_custom_prompt(agent_id: str, custom_prompt: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agents SET custom_prompt = ? WHERE id = ?
    """, (custom_prompt, agent_id))

    conn.commit()
    conn.close()


def save_prompt_version(version_id: str, agent_id: str, prompt_text: str) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Get next version number
    cursor.execute("""
        SELECT COALESCE(MAX(version), 0) + 1 as next_version
        FROM prompt_versions WHERE agent_id = ?
    """, (agent_id,))
    row = cursor.fetchone()
    next_version = row['next_version'] if row else 1

    # Deactivate previous versions
    cursor.execute("""
        UPDATE prompt_versions SET is_active = 0 WHERE agent_id = ?
    """, (agent_id,))

    # Insert new version
    cursor.execute("""
        INSERT INTO prompt_versions
        (id, agent_id, prompt_text, version, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (version_id, agent_id, prompt_text, next_version, now))

    conn.commit()
    conn.close()

    return {
        "id": version_id,
        "agent_id": agent_id,
        "prompt_text": prompt_text,
        "version": next_version,
        "is_active": True,
        "created_at": now
    }


def get_prompt_history(agent_id: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM prompt_versions
        WHERE agent_id = ?
        ORDER BY version DESC
    """, (agent_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

