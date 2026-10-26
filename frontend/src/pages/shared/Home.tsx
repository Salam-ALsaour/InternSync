/** Role home page: the role's menu with short descriptions (Increment 1 design, Section 10). The dashboards with
 *  counts come in Increment 2. */
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { menuFor } from "../../components/Layout";
import { Card, Notice, PageHeader } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { nameOf } from "../../lib/format";

export default function Home() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const verified = !["pending", "rejected"].includes(me.verification_status);
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
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((m) => (
          <Link key={m.to} to={m.to} className="no-underline">
            <Card className="h-full transition-shadow hover:shadow-md">
              <h2 className="mb-2 text-base font-bold text-primary">{t(`menu.${m.key}`)}</h2>
              <p className="text-sm text-ink-muted">{t(`menu_hint.${m.key}`)}</p>
            </Card>
          </Link>
        ))}
      </div>
    </>
  );
}
