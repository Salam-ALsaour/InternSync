/** Signed-in user, login, logout, and the language preference (FR-AUT-01, FR-AUT-03, FR-LOC-01). Offline, the
 *  session continues with the saved user, and the idle limit is applied by the app as well (CR-10). */
import { useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type S, session, unwrap } from "../api/client";
import { applyLanguage } from "../i18n";
import { clearCopy, clearDrafts, idleFor, saveMe, savedMe, touch } from "./offline";

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
    clearCopy();
  }, [queryClient]);

  const refresh = useCallback(async () => {
    if (!session.token) {
      setMe(null);
      return null;
    }
    try {
      const user = await unwrap(api.GET("/api/v1/me"));
      setMe(user);
      saveMe(user);
      applyLanguage(user.language);
      return user;
    } catch (e) {
      const saved = e instanceof ApiError ? null : savedMe<Me>();
      if (saved) {  // no connection: keep the session with the saved user and the saved copy
        setMe(saved);
        applyLanguage(saved.language);
        return saved;
      }
      clear();
      return null;
    }
  }, [clear]);

  const expire = useCallback(() => {
    clear();
    navigate("/login?expired=1", { replace: true });
  }, [clear, navigate]);

  useEffect(() => {
    session.onUnauthorized(() => {
      if (session.token) expire();
    });
    const limit = (savedMe<Me>()?.idle_timeout_minutes ?? 30) * 60_000;
    if (session.token && idleFor() > limit) clear();  // the window was left idle past the limit
    void refresh().finally(() => setReady(true));
  }, [clear, expire, refresh]);

  // FR-AUT-03 on the device: no key, click, or touch for the idle limit ends the session, online or not. The
  // notification count polls the API, so the server alone would never see the session as idle.
  useEffect(() => {
    if (!me) return;
    let last = 0;
    const active = () => {
      const now = Date.now();
      if (now - last > 10_000) {
        last = now;
        touch();
      }
    };
    active();
    const events = ["keydown", "pointerdown", "wheel", "touchstart"] as const;
    for (const e of events) window.addEventListener(e, active, { passive: true });
    const timer = setInterval(() => {
      if (idleFor() > me.idle_timeout_minutes * 60_000) {
        void api.POST("/api/v1/auth/logout").catch(() => undefined);
        expire();
      }
    }, 30_000);
    return () => {
      for (const e of events) window.removeEventListener(e, active);
      clearInterval(timer);
    };
  }, [me, expire]);

  const login = useCallback(async (email: string, password: string) => {
    const out = await unwrap(api.POST("/api/v1/auth/login", { body: { email, password } }));
    clearCopy();
    session.token = out.access_token;
    queryClient.clear();
    setMe(out.user);
    saveMe(out.user);
    touch();
    applyLanguage(out.user.language);
    return out.user;
  }, [queryClient]);

  const logout = useCallback(async () => {
    try {
      await api.POST("/api/v1/auth/logout");
    } catch {
      /* offline: the session ends on this device; the server ends it at its idle limit */
    } finally {
      clear();
      clearDrafts();
      navigate("/login", { replace: true });
    }
  }, [clear, navigate]);

  const setLanguage = useCallback(async (lang: "ar" | "en") => {
    applyLanguage(lang);
    if (session.token) {
      const user = await unwrap(api.PATCH("/api/v1/me", { body: { language: lang } }));
      setMe(user);
      saveMe(user);
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
