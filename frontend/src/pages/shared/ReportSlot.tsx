/** A report slot: the student writes and submits (wireframe `ST_Report`), the academic supervisor reviews and
 *  comments (`AS_ReportReview`, without the similarity panel), the company supervisor and coordinator read
 *  (FR-REP-02 – 07, FR-WFL-01). The actions shown are the ones the API allows for this caller. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api, openFile, type S, sendForm, unwrap } from "../../api/client";
import { Button, Card, Dialog, DraftNotice, ErrorBox, Loading, Notice, PageHeader, TextArea } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";
import { draftKey, useLocalDraft } from "../../lib/offline";
import { SlotStatus, slotTitle } from "./PlacementReports";
import { SimilarityPanel } from "./SimilarityPanel";
import { History } from "./History";
import { useMe } from "../../lib/auth";

type Slot = S<"SlotOut">;
type Version = S<"VersionOut">;
const WEEKLY = ["tasks_performed", "learning", "challenges", "next_week_plan"] as const;
type DraftField = (typeof WEEKLY)[number] | "summary";

function Attachments({ version }: { version: Version }) {
  const { t } = useTranslation();
  const [error, setError] = useState<unknown>(null);
  if (version.attachments.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="mb-1 text-xs text-ink-muted">{t("report.attachments")}</p>
      <ul className="flex flex-col gap-1 text-sm">
        {version.attachments.map((a) => (
          <li key={a.id}>
            <button type="button" className="text-primary underline" onClick={() => openFile(a.file_id).catch(setError)}>
              {a.original_name}
            </button>
            {a.role === "main" && <span className="ms-2 text-xs text-ink-muted">({t("report.main_document")})</span>}
          </li>
        ))}
      </ul>
      <ErrorBox error={error} />
    </div>
  );
}

function VersionView({ v, kind }: { v: Version; kind: string }) {
  const { t, i18n } = useTranslation();
  const fields: DraftField[] = kind === "final" ? ["summary"] : [...WEEKLY];
  return (
    <Card title={t("report.version", { n: v.version_no })}
      actions={<span className="text-sm text-ink-muted" dir="ltr">{formatDateTime(v.submitted_at)}{v.is_late ? ` · ${t("status.late")}` : ""}</span>}>
      <div className="flex flex-col gap-3">
        {fields.map((f) => v[f] && (
          <div key={f}>
            <p className="text-xs font-semibold text-ink-muted">{t(`report.${f}`)}</p>
            <p className="whitespace-pre-wrap text-sm">{v[f]}</p>
          </div>
        ))}
      </div>
      <Attachments version={v} />
      {v.review && (
        <div className="mt-4 rounded-ctl bg-ground p-3 text-sm">
          <p className="font-semibold">
            {t(`report.review_${v.review.decision}`)} — {i18n.language === "en" ? v.review.reviewer_en : v.review.reviewer_ar}
          </p>
          {v.review.comment && <p className="mt-1 whitespace-pre-wrap">{v.review.comment}</p>}
        </div>
      )}
    </Card>
  );
}

function DraftEditor({ slot, onChange }: { slot: Slot; onChange: (s: Slot) => void }) {
  const { t } = useTranslation();
  const me = useMe();
  const fields: DraftField[] = slot.kind === "final" ? ["summary"] : [...WEEKLY];
  const server = Object.fromEntries(fields.map((f) => [f, (slot.draft?.[f] as string | null) ?? ""]));
  const params = { params: { path: { slot_id: slot.id } } };
  const put = (body: Record<string, string>) =>
    unwrap(api.PUT("/api/v1/report-slots/{slot_id}/draft", { ...params, body })).then((s) => {
      onChange(s);
      return s;
    });
  // The text is kept on the device until it reaches the server, and saved when the connection returns (CR-10).
  const local = useLocalDraft(draftKey(me.id, "report", slot.id), server, put);
  const values = local.values;
  const setValues = local.setValues;
  const save = useMutation({ mutationFn: () => put(values), onSuccess: local.saved });
  const submit = useMutation({
    mutationFn: async () => {
      await put(values);
      return unwrap(api.POST("/api/v1/report-slots/{slot_id}/submit", params));
    },
    onSuccess: (s) => {
      local.saved();
      onChange(s);
    },
  });
  const upload = useMutation({
    mutationFn: ({ file, role }: { file: File; role: "main" | "attachment" }) => {
      const form = new FormData();
      form.set("file", file);
      form.set("role", role);
      return sendForm<Slot>("POST", `/api/v1/report-slots/${slot.id}/draft/attachments`, form);
    },
    onSuccess: onChange,
  });
  const remove = useMutation({
    mutationFn: (attachmentId: string) => unwrap(api.DELETE("/api/v1/report-slots/{slot_id}/draft/attachments/{attachment_id}",
      { params: { path: { slot_id: slot.id, attachment_id: attachmentId } } })),
    onSuccess: onChange,
  });
  const atts = slot.draft?.attachments ?? [];
  const extra = atts.filter((a) => a.role === "attachment").length;
  const pick = (role: "main" | "attachment") => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate({ file, role });
    e.target.value = "";
  };
  return (
    <Card title={slot.status === "revision_requested" ? t("report.revise") : t("report.write")}>
      <div className="flex flex-col gap-4">
        {slot.status === "revision_requested" && <Notice tone="warning">{t("report.revision_note")}</Notice>}
        {fields.map((f) => (
          <TextArea key={f} label={t(`report.${f}`)} value={values[f] ?? ""} maxLength={8000}
            onChange={(e) => setValues((v) => ({ ...v, [f]: e.target.value }))} rows={f === "summary" ? 6 : 4} />
        ))}
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">{t("report.attachments")}</p>
          <ul className="flex flex-col gap-1 text-sm">
            {atts.map((a) => (
              <li key={a.id} className="flex items-center gap-3">
                <span>{a.original_name}{a.role === "main" ? ` (${t("report.main_document")})` : ""}</span>
                <Button tone="ghost" className="min-h-0 px-0" onClick={() => remove.mutate(a.id)}>{t("common.remove")}</Button>
              </li>
            ))}
          </ul>
          {slot.kind === "final" && (
            <label className="text-sm">
              {t("report.upload_main")}
              <input type="file" accept=".pdf,.docx" className="ms-2" onChange={pick("main")} />
            </label>
          )}
          {extra < slot.max_attachments && (
            <label className="text-sm">
              {t("report.upload_attachment", { max: slot.max_attachments, mb: slot.attachment_max_mb })}
              <input type="file" accept=".pdf,.docx,.png,.jpg,.jpeg" className="ms-2" onChange={pick("attachment")} />
            </label>
          )}
        </div>
        <DraftNotice status={local.status} onKeepMine={local.keepMine} onKeepSaved={local.keepSaved} />
        <ErrorBox error={save.error ?? submit.error ?? upload.error ?? remove.error} />
        {save.isSuccess && !save.isPending && local.status === "server" && <Notice tone="success">{t("report.saved")}</Notice>}
        <div className="flex flex-wrap gap-2">
          <Button tone="secondary" busy={save.isPending} onClick={() => save.mutate()}>{t("report.save_draft")}</Button>
          <Button busy={submit.isPending} onClick={() => submit.mutate()} className="min-h-[48px]">{t("report.submit")}</Button>
        </div>
      </div>
    </Card>
  );
}

function Review({ slot, onChange }: { slot: Slot; onChange: (s: Slot) => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState<"revision" | "missing" | null>(null);
  const [comment, setComment] = useState("");
  const params = { params: { path: { slot_id: slot.id } } };
  const done = (s: Slot) => {
    setOpen(null);
    setComment("");
    onChange(s);
  };
  const accept = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/report-slots/{slot_id}/accept", params)),
    onSuccess: done });
  const revise = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/report-slots/{slot_id}/request-revision",
    { ...params, body: { comment } })), onSuccess: done });
  const close = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/report-slots/{slot_id}/close-missing", params)),
    onSuccess: done });
  const actions = slot.allowed_actions;
  if (!actions.some((a) => ["accept", "request_revision", "close_missing"].includes(a))) return null;
  return (
    <Card title={t("report.review")}>
      <ErrorBox error={accept.error} />
      <div className="flex flex-wrap gap-2">
        {actions.includes("accept") && <Button busy={accept.isPending} onClick={() => accept.mutate()}>{t("report.accept")}</Button>}
        {actions.includes("request_revision") && <Button tone="secondary" onClick={() => setOpen("revision")}>{t("report.request_revision")}</Button>}
        {actions.includes("close_missing") && <Button tone="danger" onClick={() => setOpen("missing")}>{t("report.close_missing")}</Button>}
      </div>
      <Dialog open={open === "revision"} title={t("report.request_revision")} onClose={() => setOpen(null)}>
        <TextArea label={t("report.revision_comment")} value={comment} onChange={(e) => setComment(e.target.value)} />
        <ErrorBox error={revise.error} />
        <div className="mt-4 flex gap-2">
          <Button busy={revise.isPending} disabled={!comment.trim()} onClick={() => revise.mutate()}>{t("common.send")}</Button>
          <Button tone="secondary" onClick={() => setOpen(null)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
      <Dialog open={open === "missing"} title={t("report.close_missing")} onClose={() => setOpen(null)}>
        <p className="text-sm text-ink-muted">{t("report.close_missing_note")}</p>
        <ErrorBox error={close.error} />
        <div className="mt-4 flex gap-2">
          <Button tone="danger" busy={close.isPending} onClick={() => close.mutate()}>{t("report.close_missing")}</Button>
          <Button tone="secondary" onClick={() => setOpen(null)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}

function Comments({ slot }: { slot: Slot }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const key = ["comments", slot.id];
  const params = { params: { path: { slot_id: slot.id } } };
  const comments = useQuery({ queryKey: key, queryFn: () => unwrap(api.GET("/api/v1/report-slots/{slot_id}/comments", params)) });
  const add = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/report-slots/{slot_id}/comments", { ...params, body: { body } })),
    onSuccess: (rows) => {
      queryClient.setQueryData(key, rows);
      setBody("");
    },
  });
  return (
    <Card title={t("report.comments")}>
      <ul className="mb-4 flex flex-col gap-3">
        {(comments.data ?? []).map((c) => (
          <li key={c.id} className="rounded-ctl bg-ground p-3 text-sm">
            <p className="text-xs text-ink-muted">
              {i18n.language === "en" ? c.author_en : c.author_ar} · {t(`role.${c.author_role}`)} · <span dir="ltr">{formatDateTime(c.created_at)}</span>
            </p>
            <p className="mt-1 whitespace-pre-wrap">{c.body}</p>
          </li>
        ))}
        {comments.data?.length === 0 && <li className="text-sm text-ink-muted">{t("report.no_comments")}</li>}
      </ul>
      {slot.can_comment && (
        <div className="flex flex-col gap-2">
          <TextArea label={t("report.add_comment")} value={body} rows={2} maxLength={2000} onChange={(e) => setBody(e.target.value)} />
          <ErrorBox error={add.error} />
          <div><Button busy={add.isPending} disabled={!body.trim()} onClick={() => add.mutate()}>{t("common.send")}</Button></div>
        </div>
      )}
    </Card>
  );
}

export default function ReportSlot() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const { slotId = "" } = useParams();
  const queryClient = useQueryClient();
  const key = ["slot", slotId];
  const slot = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/report-slots/{slot_id}", { params: { path: { slot_id: slotId } } })) });
  if (slot.isLoading) return <Loading />;
  if (slot.error || !slot.data) return <ErrorBox error={slot.error} />;
  const s = slot.data;
  const update = (next: Slot) => {
    queryClient.setQueryData(key, next);
    void queryClient.invalidateQueries({ queryKey: ["slots", next.placement_id] });
  };
  const canWrite = s.allowed_actions.includes("submit");
  return (
    <>
      <PageHeader title={slotTitle(s, t)}
        subtitle={<>{nameOf(s.student, i18n.language)} · {t("report.due")}: <span dir="ltr">{formatDateTime(s.due_at)}</span></>}
        actions={<SlotStatus slot={s} />} />
      <Link to={`/placements/${s.placement_id}`} className="mb-4 inline-block text-sm">{t("report.back")}</Link>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          {canWrite && <DraftEditor slot={s} onChange={update} />}
          <Review slot={s} onChange={update} />
          {s.submitted.slice().reverse().map((v) => <VersionView key={v.id} v={v} kind={s.kind} />)}
          {s.submitted.length === 0 && !canWrite && <Notice>{t("report.nothing_submitted")}</Notice>}
        </div>
        <div className="flex flex-col gap-4">
          {(me.role === "academic_supervisor" || me.role === "coordinator") && s.submitted.length > 0 &&
            <SimilarityPanel versionId={s.submitted[s.submitted.length - 1].id} />}
          <Comments slot={s} />
          <Card><History type="report_slot" id={s.id} /></Card>
        </div>
      </div>
    </>
  );
}
