import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authAPI } from "../lib/api";

export const useAuth = create(
  persist(
    (set) => ({
      user:   null,
      token:  null,
      apiKey: null,

      login: async (email, password) => {
        const { data } = await authAPI.login({ email, password });
        localStorage.setItem("token", data.token);
        set({ user: data, token: data.token });
        return data;
      },

      signup: async (name, email, password) => {
        const { data } = await authAPI.signup({ name, email, password });
        localStorage.setItem("token", data.token);
        set({ user: data, token: data.token });
        return data;
      },

      setApiKey: (key) => set({ apiKey: key }),

      logout: () => {
        localStorage.removeItem("token");
        set({ user: null, token: null, apiKey: null });
      }
    }),
    { name: "avaniko-auth", partialize: (s) => ({ user: s.user, token: s.token, apiKey: s.apiKey }) }
  )
);
