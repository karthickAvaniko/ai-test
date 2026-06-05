import { useState, useEffect } from "react";
import { Routes, Route, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
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
  const { user, logout } = useAuth();
  const navigate         = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="flex h-screen bg-bg text-white overflow-hidden relative">
      {/* Animated Background for the entire dashboard */}
      <div className="bg-mesh"></div>
      <div className="orb orb-1" style={{ top: '-20%', left: '10%' }}></div>
      <div className="orb orb-2" style={{ bottom: '-10%', right: '20%' }}></div>

      {/* Sidebar - Glassmorphic */}
      <aside className="w-64 glass border-r border-gray-800/50 flex flex-col relative z-10 m-4 rounded-2xl mr-0">
        <div className="p-6 border-b border-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Cpu className="text-indigo-400" size={24} />
            </div>
            <span className="font-bold font-display text-lg text-white">Avaniko AI</span>
          </div>
          <p className="text-xs text-gray-400 mt-3 truncate bg-gray-900/50 p-2 rounded-md border border-gray-800">
            {user?.email}
          </p>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive 
                    ? "nav-active" 
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50 hover:pl-5"
                }`
              }
            >
              <Icon size={18} />{label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800/50">
          <button onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-red-500/10 hover:text-red-400 w-full transition-all hover:pl-5">
            <LogOut size={18} />Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto relative z-10 p-4">
        <div className="bg-gray-900/30 backdrop-blur-md rounded-2xl min-h-full border border-gray-800/30 shadow-2xl">
          <Routes>
            <Route index           element={<Overview />} />
            <Route path="api-keys" element={<APIKeys />} />
            <Route path="projects" element={<Projects />} />
            <Route path="chat"     element={<ChatTest />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function Overview() {
  const { apiKey } = useAuth();
  return (
    <div className="p-8 animate-fade-up">
      <h1 className="text-3xl font-bold font-display mb-2 text-white">Overview</h1>
      <p className="text-gray-400 mb-8">Your AI Platform Dashboard</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="API Base URL" value="api.avaniko.com" sub="HTTPS endpoint" delay="delay-1" />
        <StatCard title="Current Key"  value={apiKey ? `${apiKey.slice(0,20)}...` : "No key set"} sub="Set in API Keys tab" delay="delay-2" />
        <StatCard title="Model"        value="qwen3-moe"       sub="Default model" delay="delay-3" />
      </div>

      <div className="mt-8 glass card-3d rounded-2xl p-8 border-gradient delay-4 animate-fade-up">
        <h2 className="font-semibold mb-4 text-gray-200 text-lg flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          Quick Start Integration
        </h2>
        <pre className="text-sm text-green-300 overflow-auto bg-[#050505]/80 backdrop-blur-sm rounded-xl p-5 border border-white/5 font-mono shadow-inner">{`pip install avaniko-ai

from avaniko_ai import Avaniko

client = Avaniko(api_key="ava-sk-your-key")
response = client.chat("Hello!")
print(response)`}</pre>
      </div>
    </div>
  );
}

function StatCard({ title, value, sub, delay }) {
  return (
    <div className={`glass card-3d rounded-2xl p-6 relative overflow-hidden animate-fade-up ${delay}`}>
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <Cpu size={48} />
      </div>
      <p className="text-xs text-indigo-300 uppercase tracking-wider font-semibold mb-2">{title}</p>
      <p className="text-2xl font-bold text-white truncate relative z-10">{value}</p>
      <p className="text-sm text-gray-400 mt-2 relative z-10">{sub}</p>
    </div>
  );
}
