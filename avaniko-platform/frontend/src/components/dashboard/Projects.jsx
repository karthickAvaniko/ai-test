import { useState, useEffect } from "react";
import { projectsAPI } from "../../lib/api";
import { useAuth } from "../../store/auth";
import { Plus, Trash2, Edit2, Copy } from "lucide-react";
import toast from "react-hot-toast";

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm]         = useState({ name: "", system_prompt: "", model_id: "qwen3-moe", temperature: 0.7 });
  const { apiKey }              = useAuth();

  const load = async () => {
    if (!apiKey) return;
    try {
      const { data } = await projectsAPI.list(apiKey);
      setProjects(data.projects || []);
    } catch {}
  };

  useEffect(() => { load(); }, [apiKey]);

  const create = async () => {
    if (!form.name || !form.system_prompt) return toast.error("Name and system prompt required");
    try {
      await projectsAPI.create(apiKey, form);
      toast.success("Project created!");
      setShowForm(false);
      setForm({ name: "", system_prompt: "", model_id: "qwen3-moe", temperature: 0.7 });
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    }
  };

  const remove = async (id) => {
    if (!confirm("Delete this project?")) return;
    await projectsAPI.delete(apiKey, id);
    toast.success("Deleted");
    load();
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-gray-400 text-sm mt-1">Save system prompts — use project_id in API calls</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm">
          <Plus size={16} />New Project
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6 space-y-4">
          <h2 className="font-semibold text-gray-300">Create Project</h2>
          <input
            value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Project name"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"
          />
          <textarea
            value={form.system_prompt} onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
            placeholder="System prompt — e.g. You are an expert invoice extractor..."
            rows={5}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 resize-none"
          />
          <div className="flex gap-3">
            <select value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none text-sm">
              <option value="qwen3-moe">qwen3-moe</option>
              <option value="llama-3.1-70b">llama-3.1-70b</option>
              <option value="claude-3-5-sonnet-20241022">claude-3.5-sonnet</option>
            </select>
            <input type="number" step="0.1" min="0" max="2"
              value={form.temperature} onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
              className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none text-sm"
              placeholder="Temp"
            />
          </div>
          <div className="flex gap-3">
            <button onClick={create} className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm">Create</button>
            <button onClick={() => setShowForm(false)} className="bg-gray-800 text-gray-400 px-5 py-2 rounded-lg text-sm hover:bg-gray-700">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {projects.map((p) => (
          <div key={p.project_id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="font-semibold text-white">{p.name}</p>
                <p className="text-xs font-mono text-indigo-400 mt-1">{p.project_id}</p>
                <p className="text-sm text-gray-400 mt-2 line-clamp-2">{p.system_prompt?.slice(0, 120)}...</p>
                <div className="flex gap-3 mt-2 text-xs text-gray-600">
                  <span>Model: {p.model_id}</span>
                  <span>Temp: {p.temperature}</span>
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <button onClick={() => { navigator.clipboard.writeText(p.project_id); toast.success("Copied project_id"); }}
                  className="text-gray-500 hover:text-white p-2 hover:bg-gray-800 rounded-lg transition">
                  <Copy size={15} />
                </button>
                <button onClick={() => remove(p.project_id)}
                  className="text-gray-500 hover:text-red-400 p-2 hover:bg-gray-800 rounded-lg transition">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <p className="text-gray-500 text-sm">No projects yet. Create one to save your system prompts.</p>
        )}
      </div>
    </div>
  );
}
