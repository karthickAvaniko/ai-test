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

  if (!usage) return <div className="p-8 text-gray-500">Loading usage data...</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Usage (Last 30 days)</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card label="Total Requests" value={usage.total_requests?.toLocaleString()} />
        <Card label="Total Tokens"   value={usage.total_tokens?.toLocaleString()} />
        <Card label="Avg Response"   value={`${usage.avg_response_ms}ms`} />
        <Card label="Est. Cost"      value={`$${usage.total_cost?.toFixed(4)}`} />
      </div>

      {usage.by_model?.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="font-semibold text-gray-300 mb-4">Requests by Model</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={usage.by_model}>
              <XAxis dataKey="model" stroke="#666" fontSize={12} />
              <YAxis stroke="#666" fontSize={12} />
              <Tooltip contentStyle={{ background: "#111", border: "1px solid #333" }} />
              <Bar dataKey="requests" fill="#6366f1" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function Card({ label, value }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
  );
}
