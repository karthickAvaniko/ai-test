import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { authAPI } from "../lib/api";

export const useAuth = create(
  persist(
    (set) => ({
      user:   null,
      token:  null,
      apiKey: null,

      login: async (email, password) => {
        const { data } = await authAPI.login({ email, password });
        // ✅ Zustand persist handles storage — no manual localStorage needed
        set({ user: data.user ?? data, token: data.token });
        return data;
      },

      signup: async (name, email, password) => {
        const { data } = await authAPI.signup({ name, email, password });
        // ✅ Zustand persist handles storage — no manual localStorage needed
        set({ user: data.user ?? data, token: data.token });
        return data;
      },

      setApiKey: (key) => set({ apiKey: key }),

      logout: () => {
        // ✅ Clear Zustand persisted storage completely
        useAuth.persist.clearStorage();
        set({ user: null, token: null, apiKey: null });
      }
    }),
    {
      name: "avaniko-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ user: s.user, token: s.token, apiKey: s.apiKey })
    }
  )
);
