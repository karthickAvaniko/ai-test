import { useState, useEffect } from "react";
import { usageAPI } from "../../lib/api";
import { useAuth } from "../../store/auth";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function Usage() {
  const [usage, setUsage] = useState(null);
  const { apiKey }        = useAuth();

  useEffect(() => {
    if (!apiKey) return;
    usageAPI.get(apiKey, 30).then(({ data }) => setUsage(data)).catch(() => {});
  }, [apiKey]);

  if (!apiKey) return (
    <div className="p-8 text-center mt-20">
      <p className="text-gray-400 text-lg">No API Key Set</p>
      <p className="text-gray-600 text-sm mt-2">Go to the <span className="text-indigo-400">API Keys</span> tab and create a key first.</p>
    </div>
  );
  if (!usage) return <div className="p-8 text-gray-500">Loading usage data...</div>;

  return (
    <div className="p-8 animate-fade-up">
      <h1 className="text-3xl font-bold font-display mb-6 text-white">Usage (Last 30 days)</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card label="Total Requests" value={usage.total_requests?.toLocaleString()} />
        <Card label="Total Tokens"   value={usage.total_tokens?.toLocaleString()} />
        <Card label="Avg Response"   value={`${usage.avg_response_ms}ms`} />
        <Card label="Est. Cost"      value={`$${usage.total_cost?.toFixed(4)}`} />
      </div>

      {usage.by_model?.length > 0 && (
        <div className="glass rounded-2xl p-6 border-gradient animate-fade-up delay-4">
          <h2 className="font-semibold text-gray-200 mb-6 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            Requests by Model
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={usage.by_model} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="model" stroke="#4f46e5" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#4f46e5" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'rgba(99,102,241,0.1)' }}
                contentStyle={{ background: "rgba(10,15,30,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", backdropFilter: "blur(10px)", color: "#fff" }} 
              />
              <Bar dataKey="requests" fill="url(#colorPrimary)" radius={[6,6,0,0]} />
              <defs>
                <linearGradient id="colorPrimary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={1}/>
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function Card({ label, value }) {
  return (
    <div className="glass card-3d rounded-2xl p-6 relative overflow-hidden">
      <div className="absolute -top-4 -right-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl"></div>
      <p className="text-[10px] text-indigo-300 uppercase tracking-widest font-bold mb-2">{label}</p>
      <p className="text-3xl font-display font-bold text-white mt-1 relative z-10">{value}</p>
    </div>
  );
}
