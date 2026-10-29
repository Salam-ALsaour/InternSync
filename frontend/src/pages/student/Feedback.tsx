/** UC-14: the student evaluates the training company and answers the job-offer survey (FR-EVL-05, FR-DSH-03).
 *  Only the coordinator sees the answers, never the company. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Loading, Notice, PageHeader, TextArea } from "../../components/ui";
import { formatDate, formatDateTime } from "../../lib/format";

type Feedback = S<"Feedback">;
const RATINGS = ["learning_opportunities", "supervision_quality", "work_environment", "relevance_to_major"] as const;
type Rating = (typeof RATINGS)[number];

function Scale({ name, value, onChange }: { name: string; value: number | undefined; onChange: (n: number) => void }) {
  return (
    <div className="flex flex-wrap gap-2" role="radiogroup">
      {[1, 2, 3, 4, 5].map((n) => (
        <label key={n} className={`flex min-h-[44px] min-w-[44px] cursor-pointer items-center focus-within:ring-2 focus-within:ring-primary/40 justify-center rounded-ctl border px-3 text-sm font-semibold ${value === n ? "border-primary bg-[#E6EEFB] text-primary" : "border-line"}`}>
          <input type="radio" name={name} className="sr-only" checked={value === n} onChange={() => onChange(n)} />
          {n}
        </label>
      ))}
    </div>
  );
}

function EvaluationCard({ f, onSaved }: { f: Feedback; onSaved: (f: Feedback) => void }) {
  const { t } = useTranslation();
  const [ratings, setRatings] = useState<Partial<Record<Rating, number>>>({});
  const [recommend, setRecommend] = useState<boolean | null>(null);
  const [comment, setComment] = useState("");
  const send = useMutation({
    mutationFn: () => unwrap(api.PUT("/api/v1/placements/{placement_id}/company-evaluation", {
      params: { path: { placement_id: f.placement_id } },
      body: { ...(ratings as Record<Rating, number>), would_recommend: !!recommend, comment: comment || null } })),
    onSuccess: onSaved,
  });
  const e = f.evaluation;
  if (e) {
    return (
      <Card title={t("feedback.evaluation")} actions={<span className="text-sm text-ink-muted" dir="ltr">{formatDateTime(e.submitted_at)}</span>}>
        <ul className="flex flex-col gap-2 text-sm">
          {RATINGS.map((r) => <li key={r} className="flex justify-between border-b border-line pb-2"><span>{t(`feedback.${r}`)}</span><b>{t("feedback.of_five", { n: e[r] })}</b></li>)}
          <li className="flex justify-between"><span>{t("feedback.would_recommend")}</span><b>{t(e.would_recommend ? "feedback.yes" : "feedback.no")}</b></li>
        </ul>
        {e.comment && <p className="mt-3 whitespace-pre-wrap text-sm">{e.comment}</p>}
        <p className="mt-3 text-xs text-ink-muted">{t("feedback.submitted")}</p>
      </Card>
    );
  }
  if (!f.can_evaluate) return null;
  const complete = RATINGS.every((r) => ratings[r]) && recommend !== null;
  return (
    <Card title={t("feedback.evaluation")}>
      <div className="flex flex-col gap-4">
        {RATINGS.map((r) => (
          <fieldset key={r}>
            <legend className="mb-2 text-sm font-medium">{t(`feedback.${r}`)}</legend>
            <Scale name={r} value={ratings[r]} onChange={(n) => setRatings({ ...ratings, [r]: n })} />
          </fieldset>
        ))}
        <fieldset>
          <legend className="mb-2 text-sm font-medium">{t("feedback.would_recommend")}</legend>
          <div className="flex gap-2">
            {[true, false].map((v) => (
              <label key={String(v)} className={`flex min-h-[44px] cursor-pointer items-center focus-within:ring-2 focus-within:ring-primary/40 rounded-ctl border px-4 text-sm font-semibold ${recommend === v ? "border-primary bg-[#E6EEFB] text-primary" : "border-line"}`}>
                <input type="radio" name="recommend" className="sr-only" checked={recommend === v} onChange={() => setRecommend(v)} />
                {t(v ? "feedback.yes" : "feedback.no")}
              </label>
            ))}
          </div>
        </fieldset>
        <TextArea label={t("feedback.comment")} value={comment} maxLength={2000} rows={3} onChange={(e) => setComment(e.target.value)} />
        <ErrorBox error={send.error} />
        <div className="flex flex-wrap items-center gap-3">
          <Button busy={send.isPending} disabled={!complete} onClick={() => send.mutate()}>{t("feedback.submit")}</Button>
          <span className="text-xs text-ink-muted">{t("feedback.once")}</span>
        </div>
      </div>
    </Card>
  );
}

function SurveyCard({ f, onSaved }: { f: Feedback; onSaved: (f: Feedback) => void }) {
  const { t } = useTranslation();
  const [answer, setAnswer] = useState(f.survey?.job_offer ?? "");
  const send = useMutation({
    mutationFn: () => unwrap(api.PUT("/api/v1/placements/{placement_id}/outcome-survey", {
      params: { path: { placement_id: f.placement_id } }, body: { job_offer: answer as "yes" | "no" | "pending" } })),
    onSuccess: onSaved,
  });
  if (!f.can_answer) return null;
  return (
    <Card title={t("feedback.survey")}>
      <fieldset className="flex flex-col gap-3">
        <legend className="mb-2 text-sm font-medium">{t("feedback.survey_question")}</legend>
        <div className="flex flex-wrap gap-2">
          {(["yes", "no", "pending"] as const).map((v) => (
            <label key={v} className={`flex min-h-[44px] cursor-pointer items-center focus-within:ring-2 focus-within:ring-primary/40 rounded-ctl border px-4 text-sm font-semibold ${answer === v ? "border-primary bg-[#E6EEFB] text-primary" : "border-line"}`}>
              <input type="radio" name="job_offer" className="sr-only" checked={answer === v} onChange={() => setAnswer(v)} />
              {t(`feedback.offer_${v}`)}
            </label>
          ))}
        </div>
        <ErrorBox error={send.error} />
        {send.isSuccess && <Notice tone="success">{t("feedback.answer_saved")}</Notice>}
        <div><Button busy={send.isPending} disabled={!answer || answer === f.survey?.job_offer} onClick={() => send.mutate()}>{t("feedback.save_answer")}</Button></div>
      </fieldset>
    </Card>
  );
}

function PlacementFeedback({ placementId }: { placementId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const key = ["feedback", placementId];
  const q = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}/feedback", { params: { path: { placement_id: placementId } } })) });
  if (q.isLoading) return <Loading />;
  if (!q.data) return <ErrorBox error={q.error} />;
  const f = q.data;
  const saved = (next: Feedback) => {
    queryClient.setQueryData(key, next);
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };
  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-bold">{f.company} · <span className="font-normal">{f.vacancy}</span></h2>
      {!f.is_open
        ? <Notice>{t("feedback.opens", { date: formatDate(f.open_from) })}</Notice>
        : <><EvaluationCard f={f} onSaved={saved} /><SurveyCard f={f} onSaved={saved} /></>}
    </section>
  );
}

export default function Feedback() {
  const { t } = useTranslation();
  const placements = useQuery({ queryKey: ["placements", "mine"], queryFn: () =>
    unwrap(api.GET("/api/v1/placements", { params: { query: { page_size: 20 } } })) });
  if (placements.isLoading) return <Loading />;
  const rows = (placements.data?.items ?? []).filter((p) => p.status !== "cancelled");
  return (
    <>
      <PageHeader title={t("feedback.title")} subtitle={t("feedback.subtitle")} />
      <ErrorBox error={placements.error} />
      {rows.length === 0 ? <Empty>{t("feedback.none")}</Empty>
        : <div className="flex flex-col gap-8">{rows.map((p) => <PlacementFeedback key={p.id} placementId={p.id} />)}</div>}
    </>
  );
}
