/** Signed-in user, login, logout, and the language preference (FR-AUT-01, FR-AUT-03, FR-LOC-01). */
import { useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type S, session, unwrap } from "../api/client";
import { applyLanguage } from "../i18n";

export type Me = S<"MeOut">;

interface AuthState {
  me: Me | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<Me>;
  logout: () => Promise<void>;
  refresh: () => Promise<Me | null>;
  setLanguage: (lang: "ar" | "en") => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export const HOME: Record<string, string> = {
  student: "/student",
  company_supervisor: "/company",
  academic_supervisor: "/academic",
  coordinator: "/coordinator",
  platform_admin: "/platform",
};

/** Where a user lands: the privacy notice first, then the verification status while pending, else home. */
export function landing(me: Me): string {
  if (me.consent_required) return "/consent";
  if (["pending", "rejected"].includes(me.verification_status) && me.role !== "student") return "/verification";
  return HOME[me.role] ?? "/";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const clear = useCallback(() => {
    session.token = null;
    setMe(null);
    queryClient.clear();
  }, [queryClient]);

  const refresh = useCallback(async () => {
    if (!session.token) {
      setMe(null);
      return null;
    }
    try {
      const user = await unwrap(api.GET("/api/v1/me"));
      setMe(user);
      applyLanguage(user.language);
      return user;
    } catch {
      clear();
      return null;
    }
  }, [clear]);

  useEffect(() => {
    session.onUnauthorized(() => {
      if (!session.token) return;
      clear();
      navigate("/login?expired=1", { replace: true });
    });
    void refresh().finally(() => setReady(true));
  }, [clear, navigate, refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const out = await unwrap(api.POST("/api/v1/auth/login", { body: { email, password } }));
    session.token = out.access_token;
    queryClient.clear();
    setMe(out.user);
    applyLanguage(out.user.language);
    return out.user;
  }, [queryClient]);

  const logout = useCallback(async () => {
    try {
      await api.POST("/api/v1/auth/logout");
    } finally {
      clear();
      navigate("/login", { replace: true });
    }
  }, [clear, navigate]);

  const setLanguage = useCallback(async (lang: "ar" | "en") => {
    applyLanguage(lang);
    if (session.token) {
      const user = await unwrap(api.PATCH("/api/v1/me", { body: { language: lang } }));
      setMe(user);
    }
  }, []);

  const value = useMemo(() => ({ me, ready, login, logout, refresh, setLanguage }),
    [me, ready, login, logout, refresh, setLanguage]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}

/** The signed-in user inside protected pages. */
export function useMe(): Me {
  const { me } = useAuth();
  if (!me) throw new Error("useMe without a user");
  return me;
}
