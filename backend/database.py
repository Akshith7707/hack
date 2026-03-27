import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "flowforge.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            goal TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('classifier','worker','supervisor','decision')),
            style TEXT DEFAULT NULL,
            model TEXT DEFAULT 'Qwen/Qwen2.5-7B-Instruct',
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_weights (
            agent_id TEXT PRIMARY KEY,
            style TEXT,
            weight REAL DEFAULT 0.33,
            times_selected INTEGER DEFAULT 0,
            times_accepted INTEGER DEFAULT 0,
            times_rejected INTEGER DEFAULT 0,
            FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
        )
    """)
    
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
            run_id TEXT NOT NULL,
            selected_agent TEXT,
            action TEXT NOT NULL CHECK(action IN ('accept','reject')),
            context TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
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
def save_feedback(run_id: str, selected_agent: str, action: str, context: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO feedback_log (run_id, selected_agent, action, context, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (run_id, selected_agent, action, context, datetime.utcnow().isoformat()))
    
    cursor.execute("""
        UPDATE workflow_runs SET feedback = ? WHERE id = ?
    """, (action, run_id))
    
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
