import { useState, useEffect } from "react";
import { Routes, Route, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { keysAPI } from "../lib/api";
import APIKeys    from "../components/dashboard/APIKeys";
import Usage      from "../components/dashboard/Usage";
import Projects   from "../components/dashboard/Projects";
import ChatTest   from "../components/dashboard/ChatTest";
import { KeyRound, BarChart2, FolderOpen, MessageSquare, LogOut, Cpu } from "lucide-react";
import toast from "react-hot-toast";

const navItems = [
  { to: "/dashboard",          icon: BarChart2,     label: "Overview"  },
  { to: "/dashboard/api-keys", icon: KeyRound,      label: "API Keys"  },
  { to: "/dashboard/projects", icon: FolderOpen,    label: "Projects"  },
  { to: "/dashboard/chat",     icon: MessageSquare, label: "Chat Test" },
];

export default function Dashboard() {
  const { user, apiKey, logout } = useAuth();
  const navigate                 = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Cpu className="text-indigo-400" size={20} />
            <span className="font-bold text-white">Avaniko AI</span>
          </div>
          <p className="text-xs text-gray-500 mt-1 truncate">{user?.email}</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive ? "bg-indigo-600 text-white" : "text-gray-400 hover:bg-gray-800 hover:text-white"
                }`
              }
            >
              <Icon size={16} />{label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-800">
          <button onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white w-full transition">
            <LogOut size={16} />Logout
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route index           element={<Overview />} />
          <Route path="api-keys" element={<APIKeys />} />
          <Route path="projects" element={<Projects />} />
          <Route path="chat"     element={<ChatTest />} />
        </Routes>
      </main>
    </div>
  );
}

function Overview() {
  const { apiKey } = useAuth();
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-2">Overview</h1>
      <p className="text-gray-400 mb-8">Your AI Platform Dashboard</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="API Base URL" value="api.avaniko.com" sub="HTTPS endpoint" />
        <StatCard title="Current Key"  value={apiKey ? `${apiKey.slice(0,20)}...` : "No key set"} sub="Set in API Keys tab" />
        <StatCard title="Model"        value="qwen3-moe"       sub="Default model" />
      </div>
      <div className="mt-8 bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="font-semibold mb-4 text-gray-300">Quick Start</h2>
        <pre className="text-sm text-green-400 overflow-auto bg-gray-950 rounded-lg p-4">{`pip install avaniko-ai

from avaniko_ai import Avaniko

client = Avaniko(api_key="ava-sk-your-key")
response = client.chat("Hello!")
print(response)`}</pre>
      </div>
    </div>
  );
}

function StatCard({ title, value, sub }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{title}</p>
      <p className="text-lg font-semibold mt-1 text-white truncate">{value}</p>
      <p className="text-xs text-gray-600 mt-1">{sub}</p>
    </div>
  );
}
