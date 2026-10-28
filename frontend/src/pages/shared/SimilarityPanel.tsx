/** The similarity check of a submitted report version for the academic supervisor and the coordinator (FR-SIM-02,
 *  FR-SIM-03; wireframe `AS_ReportReview`). Advisory: the decision changes nothing else. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Advisory, Button, Card, ErrorBox, Loading, Select, StatusChip, TextArea } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";
import { slotTitle } from "./PlacementReports";

type Result = S<"SimilarityResult">;

function percent(x: string | number | null | undefined) {
  return x === null || x === undefined ? "—" : `${Math.round(Number(x) * 100)}%`;
}

function Decision({ versionId, result, onDone }: { versionId: string; result: Result; onDone: (r: Result) => void }) {
  const { t } = useTranslation();
  const [decision, setDecision] = useState<"no_issue" | "overlap_confirmed">(
    result.decision === "no_issue" ? "no_issue" : "overlap_confirmed");
  const [comment, setComment] = useState(result.decision_comment ?? "");
  const save = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/report-versions/{version_id}/similarity/decision", {
    params: { path: { version_id: versionId } }, body: { decision, comment } })), onSuccess: onDone });
  return (
    <div className="mt-4 flex flex-col gap-3 rounded-ctl border border-line p-3">
      <Select label={t("similarity.decision")} value={decision}
        onChange={(e) => setDecision(e.target.value as typeof decision)}
        options={[{ value: "overlap_confirmed", label: t("similarity.decision_overlap_confirmed") },
          { value: "no_issue", label: t("similarity.decision_no_issue") }]} />
      <TextArea label={t("similarity.comment")} rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
      <ErrorBox error={save.error} />
      <div><Button busy={save.isPending} disabled={!comment.trim()} onClick={() => save.mutate()}>{t("similarity.record")}</Button></div>
      <p className="text-xs text-ink-muted">{t("similarity.decision_note")}</p>
    </div>
  );
}

export function SimilarityPanel({ versionId }: { versionId: string }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const key = ["similarity", versionId];
  const q = useQuery({ queryKey: key, refetchInterval: (query) => query.state.data?.status === "pending" ? 5000 : false,
    queryFn: () => unwrap(api.GET("/api/v1/report-versions/{version_id}/similarity", { params: { path: { version_id: versionId } } })) });
  if (q.isLoading) return <Card title={t("similarity.title")}><Loading /></Card>;
  const r = q.data;
  if (!r || r.status === "none") return null;
  return (
    <Card title={t("similarity.title")}
      actions={r.status === "done" && <StatusChip status={r.is_flagged ? "flagged" : "clear"}
        label={r.is_flagged ? t("similarity.flagged") : t("similarity.not_flagged")} />}>
      <ErrorBox error={q.error} />
      <Advisory>
        {r.status === "pending" && <p>{t("similarity.pending")}</p>}
        {r.status === "failed" && <p>{t("similarity.unavailable")}</p>}
        {r.status === "done" && (
          <>
            <p>{t("similarity.summary", { score: percent(r.max_score), threshold: percent(r.threshold) })}</p>
            <p className="mt-1 text-xs">{t("similarity.advisory_note")}</p>
          </>
        )}
      </Advisory>
      {r.sources.map((s) => (
        <div key={s.version_id} className="mt-4 rounded-ctl border border-line p-3">
          <p className="text-sm font-semibold">
            {slotTitle(s, t)} · {s.cycle_name} ·{" "}
            <span dir="ltr">{percent(s.score)}</span>
          </p>
          {s.author && <p className="text-xs text-ink-muted">{t("similarity.author")}: {nameOf(s.author, i18n.language)}
            {s.author.student_number && <> · <span dir="ltr">{s.author.student_number}</span></>}</p>}
          <div className="mt-2 flex flex-col gap-2">
            {s.passages.map((p, i) => (
              <div key={i} className="grid gap-2 md:grid-cols-2">
                <blockquote className="rounded-ctl bg-[#FCE8E8] p-2 text-sm" dir="auto">
                  <p className="mb-1 text-xs font-semibold text-ink-muted">{t("similarity.this_report")}</p>{p.report_text}
                </blockquote>
                <blockquote className="rounded-ctl bg-ground p-2 text-sm" dir="auto">
                  <p className="mb-1 text-xs font-semibold text-ink-muted">{t("similarity.source")}</p>{p.source_text}
                </blockquote>
              </div>
            ))}
          </div>
        </div>
      ))}
      {r.decision && (
        <p className="mt-4 text-sm">
          <b>{t(`similarity.decision_${r.decision}`)}</b> · {i18n.language === "ar" ? r.decided_by_ar : r.decided_by_en}
          {r.decided_at && <> · <span dir="ltr">{formatDateTime(r.decided_at)}</span></>}
          {r.decision_comment && <span className="block whitespace-pre-wrap text-ink-muted">{r.decision_comment}</span>}
        </p>
      )}
      {r.can_decide && <Decision versionId={versionId} result={r} onDone={(next) => {
        queryClient.setQueryData(key, next);
        void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }} />}
      {r.model_version && <p className="mt-3 text-xs text-ink-muted" dir="ltr">{r.model_version}</p>}
    </Card>
  );
}
