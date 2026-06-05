import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../store/auth";
import toast from "react-hot-toast";
import { Cpu, ArrowRight, Sparkles } from "lucide-react";

export default function Login() {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const { login }               = useAuth();
  const navigate                = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden">
      {/* Animated background */}
      <div className="bg-mesh" />
      <div className="stars" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />

      {/* Animated grid */}
      <div className="grid-bg absolute inset-0 opacity-60" />

      {/* Rotating ring behind card */}
      <div className="absolute w-[520px] h-[520px] rounded-full border border-indigo-500/10 spin-ring" />
      <div className="absolute w-[620px] h-[620px] rounded-full border border-purple-500/5" style={{ animation: 'spin-ring 14s linear infinite reverse' }} />

      {/* Card */}
      <div className="relative z-10 w-full max-w-md animate-scale-in">

        {/* Logo */}
        <div className="text-center mb-10 animate-fade-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 relative"
            style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(139,92,246,0.2))', border: '1px solid rgba(99,102,241,0.4)', boxShadow: '0 0 30px rgba(99,102,241,0.3)' }}>
            <Cpu size={28} className="text-indigo-400" />
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-indigo-500 rounded-full flex items-center justify-center">
              <Sparkles size={9} className="text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-display text-gradient mb-2">Avaniko AI</h1>
          <p className="text-slate-400 text-sm">Sign in to your platform</p>
        </div>

        {/* Form Card */}
        <div className="glass rounded-2xl p-8 animate-fade-up delay-1 card-3d shimmer"
          style={{ border: '1px solid rgba(99,102,241,0.2)' }}>

          {/* Inner glow top */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-px"
            style={{ background: 'linear-gradient(90deg, transparent, rgba(99,102,241,0.6), transparent)' }} />

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-widest">Email</label>
              <input
                type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                className="input-premium w-full rounded-xl px-4 py-3 text-sm"
                placeholder="you@example.com" required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-widest">Password</label>
              <input
                type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                className="input-premium w-full rounded-xl px-4 py-3 text-sm"
                placeholder="••••••••" required
              />
            </div>

            <button type="submit" disabled={loading}
              className="btn-glow w-full rounded-xl py-3 text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2">
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>Sign In <ArrowRight size={16} /></>
              )}
            </button>
          </form>

          <div className="divider-glow mt-6 mb-5" />

          <p className="text-center text-slate-500 text-sm">
            No account?{" "}
            <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
              Create one →
            </Link>
          </p>
        </div>

        {/* Bottom tags */}
        <div className="flex justify-center gap-3 mt-6 animate-fade-up delay-2">
          {["Secure", "Fast", "OpenAI Compatible"].map(tag => (
            <span key={tag} className="text-xs px-3 py-1 rounded-full text-slate-500"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
