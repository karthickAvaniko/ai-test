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
    try {
      await projectsAPI.delete(apiKey, id);
      toast.success("Project deleted");
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete project");
    }
  };

  return (
    <div className="p-8 animate-fade-up">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold font-display text-white">Projects</h1>
          <p className="text-gray-400 text-sm mt-2">Manage your project contexts and system prompts.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="btn-glow text-white px-5 py-3 rounded-xl flex items-center gap-2 text-sm font-semibold whitespace-nowrap">
          <Plus size={18} />{showForm ? "Cancel" : "New Project"}
        </button>
      </div>

      {showForm && (
        <div className="glass rounded-2xl p-6 mb-8 border-gradient animate-fade-up">
          <h2 className="font-semibold text-gray-200 mb-5 flex items-center gap-2">
            <Plus size={18} className="text-primary" /> Create Project
          </h2>
          <div className="space-y-4">
            <input
              value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Project name"
              className="w-full input-premium rounded-xl px-4 py-3"
            />
            <textarea
              value={form.system_prompt} onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              placeholder="System prompt — e.g. You are an expert invoice extractor..."
              rows={4}
              className="w-full input-premium rounded-xl px-4 py-3 resize-none"
            />
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wide">Model</label>
                <select value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })}
                  className="w-full input-premium rounded-xl px-4 py-3 text-sm appearance-none">
                  <option value="qwen3-moe">Qwen3 Mixture of Experts</option>
                  <option value="llama-3.1-70b">Llama 3.1 70B</option>
                  <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                </select>
              </div>
              <div className="w-32">
                <label className="block text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wide">Temperature</label>
                <input type="number" step="0.1" min="0" max="2"
                  value={form.temperature} onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                  className="w-full input-premium rounded-xl px-4 py-3 text-sm"
                  placeholder="Temp"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => setShowForm(false)} className="px-6 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-gray-800/50 hover:text-white transition-all">Cancel</button>
              <button onClick={create} className="btn-glow text-white px-6 py-3 rounded-xl text-sm font-semibold">Create Project</button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {projects.map((p, idx) => (
          <div key={p.project_id} className={`glass card-3d rounded-2xl p-6 flex flex-col justify-between animate-fade-up delay-${(idx % 4) + 1}`}>
            <div>
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-bold text-white text-lg">{p.name}</h3>
                <div className="flex items-center gap-1">
                  <button onClick={() => { navigator.clipboard.writeText(p.project_id); toast.success("Copied project_id"); }}
                    className="p-2 text-indigo-400 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 rounded-lg transition-colors border border-indigo-500/20" title="Copy Project ID">
                    <Copy size={16} />
                  </button>
                  <button onClick={() => remove(p.project_id)}
                    className="p-2 text-red-400 hover:text-white bg-red-500/10 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20" title="Delete Project">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <p className="text-xs font-mono text-gray-500 bg-black/40 inline-block px-3 py-1 rounded-full border border-white/5 mb-4">
                ID: {p.project_id}
              </p>
              
              <div className="bg-[#050505]/50 border border-white/5 rounded-xl p-4 mb-4 relative">
                <span className="absolute -top-2.5 left-4 bg-[#0a0f1e] px-2 text-[10px] font-bold uppercase tracking-wider text-gray-500">System Prompt</span>
                <p className="text-sm text-gray-300 line-clamp-3 leading-relaxed">
                  {p.system_prompt || "No system prompt configured."}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 pt-3 border-t border-gray-800/50 mt-auto">
              <div className="flex flex-col">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Model</span>
                <span className="text-sm text-indigo-300 font-medium">{p.model_id}</span>
              </div>
              <div className="w-px h-8 bg-gray-800/50"></div>
              <div className="flex flex-col">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Temp</span>
                <span className="text-sm text-white font-medium">{p.temperature}</span>
              </div>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="col-span-full py-12 flex flex-col items-center justify-center border-2 border-dashed border-gray-800 rounded-2xl">
            <p className="text-gray-500 font-medium mb-4">No projects yet. Create one to organize your system prompts and API calls.</p>
            <button onClick={() => setShowForm(true)} className="btn-glow text-white px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
              <Plus size={16}/> Create Project
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
