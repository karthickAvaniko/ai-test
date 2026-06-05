import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../store/auth";
import toast from "react-hot-toast";

export default function Signup() {
  const [form, setForm]   = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const { signup }        = useAuth();
  const navigate          = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await signup(form.name, form.email, form.password);
      toast.success("Account created!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg relative overflow-hidden flex items-center justify-center px-4">
      {/* Animated Background */}
      <div className="bg-mesh"></div>
      <div className="orb orb-1"></div>
      <div className="orb orb-2"></div>

      <div className="w-full max-w-md relative z-10 animate-fade-up">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold font-display text-white mb-2">
            Join <span className="text-gradient">Avaniko</span>
          </h1>
          <p className="text-gray-400">Create your AI platform account</p>
        </div>

        <div className="glass rounded-2xl p-8 glass-hover">
          <form onSubmit={handleSubmit} className="space-y-6">
            {[
              { label: "Name",     key: "name",     type: "text",     placeholder: "Your name" },
              { label: "Email",    key: "email",    type: "email",    placeholder: "you@example.com" },
              { label: "Password", key: "password", type: "password", placeholder: "••••••••" },
            ].map(({ label, key, type, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">{label}</label>
                <input
                  type={type} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="w-full input-premium rounded-xl px-4 py-3"
                  placeholder={placeholder} required
                />
              </div>
            ))}
            
            <button type="submit" disabled={loading}
              className="w-full btn-glow text-white font-semibold py-3.5 rounded-xl transition disabled:opacity-50 mt-4">
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-gray-800/50 text-center">
            <p className="text-gray-400 text-sm">
              Already have an account?{" "}
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium transition">
                Sign in instead
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
