/** Role home page: the dashboard of pending actions with live counts and links (FR-DSH-01; wireframes
 *  `ST_Dashboard`, `CS_Dashboard`, `AS_Dashboard`, `CO_Dashboard`, `PA_Dashboard`), the platform figures for the
 *  Platform Admin (FR-DSH-05), then the role's menu. */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { menuFor } from "../../components/Layout";
import { Card, ErrorBox, Loading, Notice, PageHeader } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { nameOf } from "../../lib/format";

function PlatformFigures() {
  const { t } = useTranslation();
  const stats = useQuery({ queryKey: ["platform-stats"], queryFn: () => unwrap(api.GET("/api/v1/platform/stats")) });
  if (stats.isLoading) return <Loading />;
  if (!stats.data) return <ErrorBox error={stats.error} />;
  const s = stats.data;
  const figures: [string, number | string][] = [
    [t("platform.universities"), s.universities], [t("platform.colleges"), s.colleges],
    [t("platform.colleges_with"), s.colleges_with_coordinator], [t("platform.colleges_without"), s.colleges_without_coordinator],
    [t("platform.companies"), s.verified_companies], [t("platform.vacancies"), s.published_vacancies],
    [t("platform.pending"), s.pending_verifications],
    [t("platform.oldest"), s.oldest_pending_days === null || s.oldest_pending_days === undefined ? "—" : t("platform.days", { n: s.oldest_pending_days })],
  ];
  return (
    <Card title={t("platform.figures")} className="mb-6">
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {figures.map(([k, v]) => (
          <div key={k}><dt className="text-xs text-ink-muted">{k}</dt><dd className="text-2xl font-bold text-primary" dir="ltr">{v}</dd></div>
        ))}
      </dl>
      <p className="mb-2 mt-4 text-sm font-semibold">{t("platform.users")}</p>
      <div className="flex flex-wrap gap-2">
        {Object.entries(s.users_by_role).map(([role, n]) => (
          <span key={role} className="rounded-full bg-ground px-3 py-1 text-sm">{t(`role.${role}`)}: <b dir="ltr">{n}</b></span>
        ))}
      </div>
    </Card>
  );
}

export default function Home() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const verified = !["pending", "rejected"].includes(me.verification_status);
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: () => unwrap(api.GET("/api/v1/dashboard")),
    refetchOnWindowFocus: true });
  const items = menuFor(me.role, me.is_company_admin, verified).filter((m) => m.key !== "home");
  return (
    <>
      <PageHeader title={t("home.welcome", { name: nameOf(me, i18n.language) })} subtitle={t(`portal.${me.role}`)} />
      {me.role === "student" && !verified && (
        <div className="mb-6">
          <Notice tone="warning">
            {t(me.verification_status === "rejected" ? "home.student_rejected" : "home.student_pending")}{" "}
            <Link to="/verification" className="font-semibold">{t("menu.verification")}</Link>
          </Notice>
        </div>
      )}
      <h2 className="mb-3 text-lg font-bold">{t("dashboard.pending")}</h2>
      {dashboard.isLoading && <Loading />}
      <ErrorBox error={dashboard.error} />
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(dashboard.data?.items ?? []).filter((i) => i.type !== "verification").map((i) => (
          <Link key={i.type} to={i.link} className="no-underline">
            <Card className={`h-full transition-shadow hover:shadow-md ${i.count > 0 ? "border-primary/40" : ""}`}>
              <p className="text-sm text-ink-muted">{t(`dashboard.${i.type}`)}</p>
              <p className={`mt-2 text-4xl font-bold ${i.count > 0 ? "text-primary" : "text-ink-muted"}`} dir="ltr">{i.count}</p>
              {i.oldest_days !== null && i.oldest_days !== undefined && (
                <p className="mt-1 text-xs text-ink-muted">{t("platform.oldest")}: {t("platform.days", { n: i.oldest_days })}</p>
              )}
            </Card>
          </Link>
        ))}
      </div>
      {me.role === "platform_admin" && <PlatformFigures />}
      <h2 className="mb-3 text-lg font-bold">{t("common.menu")}</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((m) => (
          <Link key={m.to} to={m.to} className="no-underline">
            <Card className="h-full transition-shadow hover:shadow-md">
              <h3 className="mb-2 text-base font-bold text-primary">{t(`menu.${m.key}`)}</h3>
              <p className="text-sm text-ink-muted">{t(`menu_hint.${m.key}`)}</p>
            </Card>
          </Link>
        ))}
      </div>
    </>
  );
}
