/** Public certificate check (wireframe `Verify_Mobile`, FR-CER-02): no login; Valid, Revoked, or Not found, with
 *  the name, university, college, cycle, company, and training dates. Never the grade. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Button, Card, DefList, ErrorBox, Input, Loading } from "../../components/ui";
import { formatDate } from "../../lib/format";

function Result({ code }: { code: string }) {
  const { t, i18n } = useTranslation();
  const ar = i18n.language === "ar";
  const q = useQuery({ queryKey: ["public-certificate", code], queryFn: () =>
    unwrap(api.GET("/api/v1/public/certificates/{code}", { params: { path: { code } } })) });
  if (q.isLoading) return <Loading />;
  if (!q.data) return <ErrorBox error={q.error} />;
  const c = q.data;
  if (c.status === "not_found") {
    return <div role="status" className="rounded-card border border-[#E9B8B8] bg-[#FCE8E8] p-5 text-[#A61B1B]">
      <p className="text-lg font-bold">{t("verify.not_found")}</p></div>;
  }
  const valid = c.status === "valid";
  const pick = (n?: { en: string; ar: string } | null) => (n ? (ar ? n.ar : n.en) : "—");
  return (
    <div className="flex flex-col gap-4">
      <div role="status" className={`rounded-card border p-5 ${valid ? "border-[#BFE0C8] bg-[#E3F3E7] text-[#1E6B34]" : "border-[#E9B8B8] bg-[#FCE8E8] text-[#A61B1B]"}`}>
        <p className="text-xl font-bold">{valid ? `✓ ${t("verify.valid")}` : `✕ ${t("verify.revoked")}`}</p>
      </div>
      <Card>
        <DefList items={[
          [t("verify.student"), c.name_removed ? t("verify.name_removed") : pick(c.student_name)],
          [t("verify.university"), pick(c.university)],
          [t("verify.college"), pick(c.college)],
          [t("verify.cycle"), c.cycle],
          [t("verify.company"), c.company],
          [t("verify.dates"), <span dir="ltr">{formatDate(c.training_start ?? "")} – {formatDate(c.training_end ?? "")}</span>],
        ]} />
        <p className="mt-4 text-xs text-ink-muted">{t("verify.no_grade")}</p>
      </Card>
    </div>
  );
}

export default function Verify() {
  const { t } = useTranslation();
  const { code = "" } = useParams();
  const navigate = useNavigate();
  const [typed, setTyped] = useState(code);
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("verify.title")}</h1>
      <form className="flex flex-wrap items-end gap-2" onSubmit={(e) => {
        e.preventDefault();
        const clean = typed.replace(/[\s-]+/g, "").toUpperCase();
        if (clean) navigate(`/verify/${clean}`);
      }}>
        <div className="min-w-[240px] flex-1">
          <Input label={t("verify.code")} value={typed} dir="ltr" autoCapitalize="characters" spellCheck={false}
            onChange={(e) => setTyped(e.target.value)} />
        </div>
        <Button type="submit" disabled={!typed.trim()}>{t("verify.check")}</Button>
      </form>
      {code && <Result code={code} />}
    </div>
  );
}
