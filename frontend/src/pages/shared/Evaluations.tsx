/** Periodic and final evaluations on the cycle rubric (wireframe `CS_Evaluation`, FR-EVL-01 – 04). The company
 *  supervisor rates every criterion 1–5 against its level descriptions; others read what is visible to them. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Dialog, ErrorBox, Loading, Notice, StatusChip, TextArea } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";
import { History } from "./History";

type Overview = S<"EvaluationOverview">;
type Item = S<"EvaluationItem">;
type Criterion = S<"Criterion">;

function levelText(c: Criterion, score: number, lang: string): string {
  const level = (c.levels as Record<string, { en: string; ar: string }>)[String(score)];
  return level ? (lang === "en" ? level.en : level.ar) : "";
}

function EvaluationForm({ placementId, item, rubric, onSaved }: { placementId: string; item: Item; rubric: Criterion[];
  onSaved: (o: Overview) => void }) {
  const { t, i18n } = useTranslation();
  const [scores, setScores] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");
  useEffect(() => {
    const e = item.evaluation;
    setScores(Object.fromEntries((e?.scores ?? []).map((s) => [s.criterion_id, s.score])));
    setComment(e?.overall_comment ?? "");
  }, [item.evaluation]);
  const params = { params: { path: { placement_id: placementId, type: item.type as "periodic" | "final" } } };
  const body = () => ({ scores: Object.entries(scores).map(([criterion_id, score]) => ({ criterion_id, score })),
    overall_comment: comment });
  const save = useMutation({ mutationFn: () => unwrap(api.PUT("/api/v1/placements/{placement_id}/evaluations/{type}",
    { ...params, body: body() })), onSuccess: onSaved });
  const submit = useMutation({
    mutationFn: async () => {
      await unwrap(api.PUT("/api/v1/placements/{placement_id}/evaluations/{type}", { ...params, body: body() }));
      return unwrap(api.POST("/api/v1/placements/{placement_id}/evaluations/{type}/submit", params));
    },
    onSuccess: onSaved,
  });
  return (
    <div className="flex flex-col gap-4">
      <Notice>{t("evaluation.rubric_note")}</Notice>
      {rubric.map((c) => (
        <fieldset key={c.id} className="rounded-card border border-line p-4">
          <legend className="px-1 font-bold">{nameOf(c, i18n.language)}</legend>
          <div className="grid gap-2 sm:grid-cols-5">
            {[1, 2, 3, 4, 5].map((n) => (
              <label key={n} className={`flex min-h-[44px] cursor-pointer items-center gap-2 rounded-ctl border px-3 text-sm ${scores[c.id] === n ? "border-primary bg-[#E6EEFB]" : "border-line"}`}>
                <input type="radio" name={`c-${item.type}-${c.id}`} checked={scores[c.id] === n} className="accent-[#1F3864]"
                  onChange={() => setScores({ ...scores, [c.id]: n })} />
                <b>{n}</b> <span className="text-ink-muted">{levelText(c, n, i18n.language)}</span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <TextArea label={t("evaluation.comment")} value={comment} rows={4} onChange={(e) => setComment(e.target.value)} />
      <ErrorBox error={save.error ?? submit.error} />
      {save.isSuccess && <Notice tone="success">{t("common.saved")}</Notice>}
      <div className="flex flex-wrap items-center gap-2">
        <Button tone="secondary" busy={save.isPending} onClick={() => save.mutate()}>{t("evaluation.save_draft")}</Button>
        <Button busy={submit.isPending} onClick={() => submit.mutate()}>{t("evaluation.submit")}</Button>
        <span className="text-xs text-ink-muted">{t("evaluation.submit_note")}</span>
      </div>
    </div>
  );
}

function EvaluationView({ item, rubric }: { item: Item; rubric: Criterion[] }) {
  const { t, i18n } = useTranslation();
  const e = item.evaluation;
  if (!e) return <p className="text-sm text-ink-muted">{t(item.type === "final" ? "evaluation.final_hidden" : "evaluation.not_yet")}</p>;
  const byId = Object.fromEntries(rubric.map((c) => [c.id, c]));
  return (
    <div className="flex flex-col gap-3 text-sm">
      <ul className="flex flex-col gap-2">
        {e.scores.map((s) => (
          <li key={s.criterion_id} className="flex flex-wrap justify-between gap-2 border-b border-line pb-2">
            <span className="font-semibold">{nameOf(s, i18n.language)}</span>
            <span><b dir="ltr">{s.score} / 5</b> <span className="text-ink-muted">{byId[s.criterion_id] ? levelText(byId[s.criterion_id], s.score, i18n.language) : ""}</span></span>
          </li>
        ))}
      </ul>
      {e.mean_score && <p><b>{t("evaluation.mean")}:</b> <span dir="ltr">{e.mean_score}</span></p>}
      {e.overall_comment && <p className="whitespace-pre-wrap"><b>{t("evaluation.comment")}:</b> {e.overall_comment}</p>}
      {e.submitted_at && (
        <p className="text-xs text-ink-muted">{i18n.language === "en" ? e.submitted_by_en : e.submitted_by_ar} · <span dir="ltr">{formatDateTime(e.submitted_at)}</span></p>
      )}
      {e.reopen_reason && <p className="text-xs text-ink-muted">{t("evaluation.reopened")}: {e.reopen_reason}</p>}
    </div>
  );
}

export default function Evaluations({ placementId }: { placementId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const key = ["evaluations", placementId];
  const data = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}/evaluations", { params: { path: { placement_id: placementId } } })) });
  const [reopening, setReopening] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const saved = (o: Overview) => {
    queryClient.setQueryData(key, o);
    void queryClient.invalidateQueries({ queryKey: ["grade", placementId] });
    setReopening(null);
  };
  const reopen = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/evaluations/{evaluation_id}/reopen",
    { params: { path: { evaluation_id: reopening ?? "" } }, body: { reason } })), onSuccess: saved });
  if (data.isLoading) return <Loading />;
  if (data.error || !data.data) return <ErrorBox error={data.error} />;
  const o = data.data;
  return (
    <div className="flex flex-col gap-4">
      {o.items.map((item) => (
        <Card key={item.type} title={t(`evaluation.${item.type}`)}
          actions={<>
            <span className="text-xs text-ink-muted">{t("evaluation.due")}: <span dir="ltr">{formatDateTime(item.due_at)}</span></span>
            <StatusChip status={item.evaluation?.status ?? "draft"}
              label={item.evaluation ? t(`evaluation.status_${item.evaluation.status}`) : t("evaluation.not_started")} />
          </>}>
          {item.can_edit ? <EvaluationForm placementId={placementId} item={item} rubric={o.rubric} onSaved={saved} />
            : <EvaluationView item={item} rubric={o.rubric} />}
          {item.can_reopen && item.evaluation && (
            <Button tone="secondary" className="mt-4" onClick={() => { setReopening(item.evaluation?.id ?? null); setReason(""); }}>
              {t("evaluation.reopen")}</Button>
          )}
          {item.evaluation && <History type="evaluation" id={item.evaluation.id} />}
        </Card>
      ))}
      {o.rubric.length === 0 && <Notice tone="warning">{t("evaluation.no_rubric")}</Notice>}
      <Dialog open={!!reopening} title={t("evaluation.reopen")} onClose={() => setReopening(null)}>
        <p className="mb-3 text-sm text-ink-muted">{t("evaluation.reopen_note")}</p>
        <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
        <ErrorBox error={reopen.error} />
        <div className="mt-4 flex gap-2">
          <Button busy={reopen.isPending} disabled={!reason.trim()} onClick={() => reopen.mutate()}>{t("evaluation.reopen")}</Button>
          <Button tone="secondary" onClick={() => setReopening(null)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </div>
  );
}
