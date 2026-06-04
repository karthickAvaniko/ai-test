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
    await keysAPI.revoke(keyId);
    toast.success("Key revoked");
    load();
  };

  const copy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied!");
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-2">API Keys</h1>
      <p className="text-gray-400 mb-8">Manage your API keys. Keys are shown only once at creation.</p>

      {/* New key display */}
      {newKey && (
        <div className="bg-green-900/30 border border-green-700 rounded-xl p-5 mb-6">
          <p className="text-green-400 text-sm font-medium mb-2">
            New API Key — copy it now, it won't be shown again
          </p>
          <div className="flex items-center gap-3">
            <code className="bg-gray-900 px-4 py-2 rounded-lg text-green-300 font-mono text-sm flex-1 truncate">
              {newKey}
            </code>
            <button onClick={() => copy(newKey)}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2">
              <Copy size={14} />Copy
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <h2 className="font-semibold text-gray-300 mb-4">Create New Key</h2>
        <div className="flex gap-3">
          <input
            value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Key name (e.g. My App, Production)"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-indigo-500 focus:outline-none"
          />
          <button onClick={createKey} disabled={creating}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50">
            <Plus size={16} />{creating ? "Creating..." : "Create"}
          </button>
        </div>
      </div>

      {/* Keys list */}
      <div className="space-y-3">
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : keys.length === 0 ? (
          <p className="text-gray-500">No API keys yet. Create one above.</p>
        ) : keys.map((k) => (
          <div key={k.key_id} className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-center justify-between">
            <div>
              <p className="font-medium text-white">{k.name}</p>
              <p className="text-sm text-gray-500 font-mono">{k.key_prefix}...</p>
              <div className="flex gap-4 mt-2 text-xs text-gray-600">
                <span>Today: {k.requests_today} / {k.daily_limit}</span>
                <span>Total: {k.total_requests}</span>
                <span>Tokens: {k.total_tokens?.toLocaleString()}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-1 rounded-full ${k.is_active ? "bg-green-900/50 text-green-400" : "bg-red-900/50 text-red-400"}`}>
                {k.is_active ? "Active" : "Revoked"}
              </span>
              {k.is_active && (
                <button onClick={() => revoke(k.key_id)}
                  className="text-gray-600 hover:text-red-400 p-2 rounded-lg hover:bg-gray-800 transition">
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
