import { createContext, useContext, useState, ReactNode } from "react";
import { api } from "./api";

interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  role: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem("pragyaan_user");
    return raw ? JSON.parse(raw) : null;
  });

  function persist(token: string, user: AuthUser) {
    localStorage.setItem("pragyaan_token", token);
    localStorage.setItem("pragyaan_user", JSON.stringify(user));
    setUser(user);
  }

  async function login(email: string, password: string) {
    const { data } = await api.post("/auth/login", { email, password });
    persist(data.access_token, data.user);
  }

  async function register(email: string, password: string, fullName: string) {
    const { data } = await api.post("/auth/register", {
      email, password, full_name: fullName,
    });
    persist(data.access_token, data.user);
  }

  function logout() {
    localStorage.removeItem("pragyaan_token");
    localStorage.removeItem("pragyaan_user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
