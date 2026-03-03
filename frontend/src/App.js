import { useState, useEffect } from 'react';
import './App.css';

const API = 'http://127.0.0.1:5000';

function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    const res = await fetch(`${API}/tasks`);
    const data = await res.json();
    setTasks(data);
  };

  const addTask = async () => {
    if (!title.trim()) return;
    await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, status: 'pending' })
    });
    setTitle('');
    fetchTasks();
  };

  const deleteTask = async (id) => {
    await fetch(`${API}/tasks/${id}`, { method: 'DELETE' });
    fetchTasks();
  };

  const toggleStatus = async (task) => {
    const newStatus = task.status === 'pending' ? 'done' : 'pending';
    await fetch(`${API}/tasks/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    fetchTasks();
  };

  return (
    <div style={{ maxWidth: '600px', margin: '50px auto', fontFamily: 'Arial' }}>
      <h1 style={{ color: '#0078d4' }}>☁️ Azure Task Manager</h1>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Enter a task..."
          style={{ flex: 1, padding: '10px', fontSize: '16px', borderRadius: '5px', border: '1px solid #ccc' }}
          onKeyPress={e => e.key === 'Enter' && addTask()}
        />
        <button
          onClick={addTask}
          style={{ padding: '10px 20px', background: '#0078d4', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px' }}
        >
          Add
        </button>
      </div>
      {tasks.map(task => (
        <div key={task.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', marginBottom: '10px', background: '#f5f5f5', borderRadius: '5px' }}>
          <span
            onClick={() => toggleStatus(task)}
            style={{ flex: 1, cursor: 'pointer', textDecoration: task.status === 'done' ? 'line-through' : 'none', color: task.status === 'done' ? '#888' : '#000' }}
          >
            {task.title}
          </span>
          <span style={{ padding: '3px 8px', borderRadius: '10px', fontSize: '12px', background: task.status === 'done' ? '#d4edda' : '#fff3cd' }}>
            {task.status}
          </span>
          <button
            onClick={() => deleteTask(task.id)}
            style={{ padding: '5px 10px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
          >
            Delete
          </button>
        </div>
      ))}
      {tasks.length === 0 && <p style={{ color: '#888' }}>No tasks yet. Add one above!</p>}
    </div>
  );
}

export default App;