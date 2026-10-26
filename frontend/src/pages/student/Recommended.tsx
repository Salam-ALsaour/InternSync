/** Recommended vacancies ranked by fit (wireframe `ST_Vacancies`, "Recommended" tab; FR-MAT-01 – 07). Every score
 *  is advisory and shows its reason; the student decides. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ApiError, api, type S, unwrap } from "../../api/client";
import { Advisory, Button, Card, Chip, ErrorBox, Loading, Notice } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";

type Item = S<"MatchItem">;

function Plan({ vacancyId }: { vacancyId: string }) {
  const { t, i18n } = useTranslation();
  const plan = useQuery({ queryKey: ["plan", vacancyId], queryFn: () =>
    unwrap(api.GET("/api/v1/students/me/matches/{vacancy_id}/plan", { params: { path: { vacancy_id: vacancyId } } })) });
  if (plan.isLoading) return <Loading />;
  if (!plan.data) return <ErrorBox error={plan.error} />;
  if (plan.data.missing_skills.length === 0) return <p className="text-sm">{t("match.nothing_missing")}</p>;
  return (
    <ul className="flex flex-col gap-2 text-sm">
      {plan.data.missing_skills.map((m) => (
        <li key={m.skill.id}>
          <b>{nameOf(m.skill, i18n.language)}</b>
          {m.resources.length === 0 ? <span className="ms-2 text-ink-muted">— {t("match.no_resource")}</span> : (
            <ul className="ms-4 mt-1 list-disc">
              {m.resources.map((r) => (
                <li key={r.url}><a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a>
                  {r.estimated_effort && <span className="text-ink-muted"> · {r.estimated_effort}</span>}</li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}

function MatchCard({ item, rank }: { item: Item; rank: number }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [showPlan, setShowPlan] = useState(false);
  const v = item.vacancy;
  const apply = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/vacancies/{vacancy_id}/applications", { params: { path: { vacancy_id: v.id } } })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["matches"] });
      void queryClient.invalidateQueries({ queryKey: ["applications"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const pct = Math.round(item.fit_score);
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#E6EEFB] font-bold text-primary">{rank}</span>
          <div>
            <h3 className="text-lg font-bold">{v.title}</h3>
            <p className="text-sm text-ink-muted">{v.company} · {v.city} · {t("vacancy.deadline")} <span dir="ltr">{formatDateTime(v.application_deadline)}</span></p>
          </div>
        </div>
        <div className="w-40">
          <p className="text-xs text-ink-muted">{t("match.fit")}</p>
          <p className="text-2xl font-bold text-primary" dir="ltr">{pct}%</p>
          <div className="mt-1 h-2 rounded-full bg-line"><div className="h-2 rounded-full bg-primary" style={{ width: `${pct}%` }} /></div>
          {item.mode === "basic" && <p className="mt-1 text-xs text-advisory-fg">{t("match.basic")}</p>}
        </div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-xs text-ink-muted">{t("match.matched")}</p>
          <div className="flex flex-wrap gap-1">
            {item.matched_skills.map((s) => <Chip key={s.id} tone="success">{nameOf(s, i18n.language)}</Chip>)}
            {item.matched_skills.length === 0 && <span className="text-sm text-ink-muted">—</span>}
          </div>
        </div>
        <div>
          <p className="mb-1 text-xs text-ink-muted">{t("match.missing")}</p>
          <div className="flex flex-wrap gap-1">
            {item.missing_skills.map((s) => <Chip key={s.id} tone="warning">{nameOf(s, i18n.language)}</Chip>)}
            {item.missing_skills.length === 0 && <span className="text-sm text-[#1E6B34]">{t("match.nothing_missing")}</span>}
          </div>
        </div>
      </div>
      <p className="mt-3 text-xs text-ink-muted">
        {t("match.parts")}: {item.parts.semantic !== null && item.parts.semantic !== undefined && <>{t("match.part_semantic")} <span dir="ltr">{Math.round(item.parts.semantic * 100)}%</span> · </>}
        {t("match.part_required")} <span dir="ltr">{Math.round(item.parts.required * 100)}%</span>
        {item.parts.preferred !== null && item.parts.preferred !== undefined && <> · {t("match.part_preferred")} <span dir="ltr">{Math.round(item.parts.preferred * 100)}%</span></>}
      </p>
      {showPlan && <div className="mt-4"><Advisory><p className="mb-2 font-semibold">{t("match.plan")}</p><Plan vacancyId={v.id} /></Advisory></div>}
      <ErrorBox error={apply.error} />
      <div className="mt-4 flex flex-wrap gap-2">
        {item.already_applied ? <Chip tone="success">{t("vacancy.applied")}</Chip>
          : <Button busy={apply.isPending} onClick={() => apply.mutate()}>{t("vacancy.apply")}</Button>}
        <Button tone="secondary" onClick={() => setShowPlan(!showPlan)}>{t("match.plan")}</Button>
      </div>
    </Card>
  );
}

export default function Recommended() {
  const { t } = useTranslation();
  const matches = useQuery({ queryKey: ["matches"], retry: false, queryFn: () =>
    unwrap(api.GET("/api/v1/students/me/matches", { params: { query: { limit: 20 } } })) });
  if (matches.isLoading) return <Loading />;
  if (matches.error instanceof ApiError && matches.error.code === "SKILLS_NOT_CONFIRMED") {
    return <Notice tone="warning">{matches.error.detail} <Link to="/student/profile" className="font-semibold">{t("menu.profile")}</Link></Notice>;
  }
  if (!matches.data) return <ErrorBox error={matches.error} />;
  const m = matches.data;
  return (
    <div className="flex flex-col gap-4">
      <Advisory><p className="text-sm">{t("match.advisory_text")}</p>
        {m.mode !== "semantic" && <p className="mt-1 text-sm font-semibold">{t(m.mode === "basic" ? "match.basic_all" : "match.basic_some")}</p>}
      </Advisory>
      {m.items.map((item, i) => <MatchCard key={item.vacancy.id} item={item} rank={i + 1} />)}
      {m.items.length === 0 && <Notice>{t("match.none")}</Notice>}
      {m.total > m.items.length && <p className="text-sm text-ink-muted">{t("match.more", { n: m.total - m.items.length })}</p>}
    </div>
  );
}
