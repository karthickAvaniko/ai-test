import { useState, useEffect } from "react";
import { keysAPI } from "../../lib/api";
import { useAuth } from "../../store/auth";
import { Copy, Trash2, Plus, Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";

export default function APIKeys() {
  const [keys, setKeys]         = useState([]);
  const [newKey, setNewKey]     = useState(null);
  const [name, setName]         = useState("");
  const [loading, setLoading]   = useState(false);
  const [creating, setCreating] = useState(false);
  const { setApiKey }           = useAuth();

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await keysAPI.list();
      setKeys(data.keys || []);
    } catch (err) {
      console.error("Failed to load API keys", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createKey = async () => {
    if (!name.trim()) return toast.error("Enter a key name");
    setCreating(true);
    try {
      const { data } = await keysAPI.create({ name, daily_limit: 1000 });
      setNewKey(data.api_key);
      setApiKey(data.api_key);
      toast.success("API key created!");
      setName("");
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create key");
    } finally {
      setCreating(false);
    }
  };

  const revoke = async (keyId) => {
    if (!confirm("Revoke this API key?")) return;
    try {
      await keysAPI.revoke(keyId);
      toast.success("Key revoked");
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to revoke key");
    }
  };

  const copy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied!");
  };

  return (
    <div className="p-8 animate-fade-up">
      <h1 className="text-3xl font-bold font-display mb-2 text-white">API Keys</h1>
      <p className="text-gray-400 mb-8">Manage your API keys. Keys are shown only once at creation.</p>

      {/* New key display */}
      {newKey && (
        <div className="glass border-green-500/30 rounded-2xl p-6 mb-8 animate-fade-up border-gradient">
          <p className="text-green-400 text-sm font-semibold mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
            New API Key — copy it now, it won't be shown again
          </p>
          <div className="flex items-center gap-3 bg-black/40 p-2 rounded-xl border border-white/5">
            <code className="px-4 py-2 text-green-300 font-mono text-sm flex-1 truncate">
              {newKey}
            </code>
            <button onClick={() => copy(newKey)}
              className="bg-green-600/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all">
              <Copy size={16} />Copy
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      {/* Create form */}
      <div className="glass rounded-2xl p-6 mb-8 border-gradient">
        <h2 className="font-semibold text-gray-200 mb-4 flex items-center gap-2">
          <Plus size={18} className="text-primary" /> Create New Key
        </h2>
        <div className="flex gap-4">
          <input
            value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Key name (e.g. Production App)"
            className="flex-1 input-premium rounded-xl px-4 py-3"
          />
          <button onClick={createKey} disabled={creating}
            className="btn-glow text-white px-6 py-3 rounded-xl flex items-center gap-2 font-semibold disabled:opacity-50">
            {creating ? "Creating..." : "Create Key"}
          </button>
        </div>
      </div>

      {/* Keys list */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {loading ? (
          <p className="text-gray-500 col-span-full">Loading keys...</p>
        ) : keys.length === 0 ? (
          <p className="text-gray-500 col-span-full">No API keys yet. Create one above.</p>
        ) : keys.map((k, idx) => (
          <div key={k.key_id} className={`glass card-3d rounded-2xl p-6 flex items-center justify-between animate-fade-up delay-${(idx % 4) + 1}`}>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <p className="font-bold text-white text-lg">{k.name}</p>
                <span className={`text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-full ${k.is_active ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
                  {k.is_active ? "Active" : "Revoked"}
                </span>
              </div>
              <p className="text-sm text-indigo-300/70 font-mono mb-4">{k.key_prefix}••••••••••••••••••••••••••••</p>
              
              <div className="flex gap-6 text-sm text-gray-400">
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Today</span>
                  <span className="text-white font-medium">{k.requests_today} <span className="text-gray-600">/ {k.daily_limit}</span></span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Total</span>
                  <span className="text-white font-medium">{k.total_requests}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 h-full">
              {k.is_active && (
                <button onClick={() => revoke(k.key_id)}
                  className="text-gray-500 hover:text-red-400 p-3 rounded-xl hover:bg-red-500/10 transition-colors border border-transparent hover:border-red-500/20"
                  title="Revoke Key">
                  <Trash2 size={18} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
