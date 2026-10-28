/** Sidebar plus content in one wrapping row; the sidebar stacks above the content on phones (Design 8.2). */
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet } from "react-router-dom";
import { api, demoClock, unwrap } from "../api/client";
import { useAuth, useMe } from "../lib/auth";
import { formatDateTime, nameOf } from "../lib/format";
import { useOnline } from "../lib/online";

export interface MenuItem {
  to: string;
  key: string;
  end?: boolean;
}

/** Each role's menu (FR-AUT-01); the Company Admin also gets the team page. */
export function menuFor(role: string, isCompanyAdmin: boolean, verified: boolean): MenuItem[] {
  const own = verified ? [] : [{ to: "/verification", key: "verification" }];
  switch (role) {
    case "student":
      return [{ to: "/student", key: "home", end: true }, { to: "/student/profile", key: "profile" },
        { to: "/student/vacancies", key: "vacancies" }, { to: "/student/applications", key: "applications" },
        { to: "/student/reports", key: "reports" }, ...own];
    case "company_supervisor":
      return [{ to: "/company", key: "home", end: true }, { to: "/company/vacancies", key: "company_vacancies" },
        { to: "/company/trainees", key: "trainees" },
        ...(isCompanyAdmin ? [{ to: "/company/team", key: "team" }] : []), ...own];
    case "academic_supervisor":
      return [{ to: "/academic", key: "home", end: true }, { to: "/academic/students", key: "my_students" },
        { to: "/academic/similarity", key: "similarity" }, { to: "/academic/grades", key: "grades" }];
    case "coordinator":
      return [{ to: "/coordinator", key: "home", end: true }, { to: "/coordinator/students", key: "students" },
        { to: "/coordinator/supervisors", key: "supervisors" }, { to: "/coordinator/cycles", key: "cycles" },
        { to: "/coordinator/placements", key: "placements" }, { to: "/coordinator/grades", key: "grades" },
        { to: "/coordinator/escalations", key: "escalations" }, { to: "/coordinator/exports", key: "exports" },
        { to: "/coordinator/audit", key: "audit" }, ...own];
    case "platform_admin":
      return [{ to: "/platform", key: "home", end: true }, { to: "/platform/verifications", key: "verifications" },
        { to: "/platform/organizations", key: "organizations" }, { to: "/platform/catalog", key: "catalog" },
        { to: "/platform/audit", key: "audit" }];
    default:
      return [];
  }
}

export function LanguageSwitch({ className = "" }: { className?: string }) {
  const { t, i18n } = useTranslation();
  const { setLanguage } = useAuth();
  const next = i18n.language === "ar" ? "en" : "ar";
  return (
    <button type="button" onClick={() => void setLanguage(next)} lang={next}
      className={`min-h-[44px] rounded-ctl border border-line bg-white px-4 text-sm font-semibold text-primary hover:bg-ground ${className}`}>
      {t("common.switch_language")}
    </button>
  );
}

function DemoClock() {
  const { t } = useTranslation();
  const [state, setState] = useState<{ now: string; offset_hours: number } | null>(null);
  useEffect(() => {
    void demoClock().then(setState);
  }, []);
  if (!state) return null;
  const move = async (hours: number) => setState(await demoClock(hours));
  return (
    <div className="mt-4 rounded-ctl bg-white/10 p-3 text-xs text-white/80">
      <p className="font-semibold">{t("dev.clock")}</p>
      <p dir="ltr" className="text-start">{formatDateTime(state.now)} (+{state.offset_hours}h)</p>
      <div className="mt-2 flex gap-2">
        <button type="button" className="rounded bg-white/20 px-2 py-1" onClick={() => void move(24)}>{t("dev.plus_day")}</button>
        <button type="button" className="rounded bg-white/20 px-2 py-1" onClick={() => void move(24 * 7)}>{t("dev.plus_week")}</button>
      </div>
    </div>
  );
}

/** The bell with the unread count (FR-NOT-01), refreshed every minute. */
function Bell() {
  const { t } = useTranslation();
  const unread = useQuery({ queryKey: ["notifications", "unread"], refetchInterval: 60_000, queryFn: () =>
    unwrap(api.GET("/api/v1/notifications", { params: { query: { unread_only: true, page_size: 1 } } })) });
  const count = unread.data?.unread_count ?? 0;
  return (
    <Link to="/notifications" aria-label={t("notifications.title_n", { n: count })}
      className="relative inline-flex h-11 w-11 items-center justify-center rounded-ctl border border-line bg-white text-primary hover:bg-ground">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" />
      </svg>
      {count > 0 && (
        <span className="absolute -top-1 -end-1 min-w-[20px] rounded-full bg-[#A61B1B] px-1 text-center text-xs font-bold leading-5 text-white" dir="ltr">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </Link>
  );
}

/** Shown while the browser is offline (FR-PWA-03); action buttons are disabled at the same time. */
function OfflineBanner() {
  const { t } = useTranslation();
  if (useOnline()) return null;
  return (
    <div role="status" className="border-b border-[#F2D9A6] bg-[#FFF1D6] px-6 py-2 text-sm font-semibold text-[#8A4B00]">
      {t("offline.banner")}
    </div>
  );
}

export function AppLayout() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const { logout } = useAuth();
  const verified = !["pending", "rejected"].includes(me.verification_status);
  const items = menuFor(me.role, me.is_company_admin, verified);
  const org = me.organization;
  const orgName = org.company ?? (i18n.language === "en" ? org.college_en : org.college_ar) ?? "";
  return (
    <div className="flex min-h-screen flex-col bg-ground md:flex-row">
      <aside className="flex flex-col bg-primary px-4 py-6 text-white md:min-h-screen md:w-64 md:shrink-0">
        <div className="mb-6 px-2">
          <p className="text-2xl font-bold">InternSync</p>
          <p className="mt-1 text-sm text-white/70">{t(`portal.${me.role}`)}</p>
        </div>
        <nav className="flex flex-row flex-wrap gap-1 md:flex-col" aria-label={t("common.menu")}>
          {items.map((it) => (
            <NavLink key={it.to} to={it.to} end={it.end}
              className={({ isActive }) => `flex min-h-[44px] items-center rounded-ctl px-3 text-sm font-medium ${isActive ? "bg-primary-active text-white" : "text-white/85 hover:bg-white/10"}`}>
              {t(`menu.${it.key}`)}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto pt-6">
          {import.meta.env.DEV && <DemoClock />}
          <button type="button" onClick={() => void logout()}
            className="mt-3 flex min-h-[44px] w-full items-center rounded-ctl px-3 text-sm text-white/85 hover:bg-white/10">
            {t("common.logout")}
          </button>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-6 py-3">
          <div>
            <p className="text-sm font-semibold text-ink">{nameOf(me, i18n.language)}</p>
            <p className="text-xs text-ink-muted">{orgName}</p>
          </div>
          <div className="flex items-center gap-2">
            <Bell />
            <LanguageSwitch />
          </div>
        </header>
        <OfflineBanner />
        <main className="mx-auto max-w-6xl p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

/** The frame of the public pages (login, registration, links from emails). */
export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col items-center bg-ground px-4 py-10">
      <div className="mb-6 flex w-full max-w-xl items-center justify-between">
        <p className="text-2xl font-bold text-primary">InternSync</p>
        <LanguageSwitch />
      </div>
      <div className="w-full max-w-xl">
        <Outlet />
      </div>
    </div>
  );
}
