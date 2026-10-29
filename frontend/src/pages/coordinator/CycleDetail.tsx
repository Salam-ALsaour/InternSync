/** Cycle settings: schedule, weekly deadlines, grade weights, rubric, close and reopen (wireframe `CO_CycleSettings`,
 *  FR-CYC-01 – 03, FR-CYC-05). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { ApiError, api, type S, unwrap } from "../../api/client";
import {
  Button, Card, Dialog, ErrorBox, Input, Loading, Notice, PageHeader, Select, StatusChip, Table, Tabs, Td, TextArea,
} from "../../components/ui";
import { formatDate, formatDateTime, fromRiyadhInput, toRiyadhInput } from "../../lib/format";
import CycleStats from "./CycleStats";
import Privacy from "./Privacy";
import { ScheduleFields, type ScheduleForm, scheduleBody } from "./Cycles";

type Cycle = S<"CycleWithWeeks">;
type Component = { name_en: string; name_ar: string; weight: string; source: "company_final_evaluation" | "academic_supervisor" };
type Criterion = { name_en: string; name_ar: string; levels: Record<string, { en: string; ar: string }> };

function toForm(c: Cycle): ScheduleForm {
  return { name: c.name, type: c.type as ScheduleForm["type"], start_date: c.start_date, end_date: c.end_date,
    weeks: String(c.weeks), working_days: c.working_days, report_weekday: String(c.report_weekday),
    report_time: c.report_time.slice(0, 5), periodic_eval_due_at: toRiyadhInput(c.periodic_eval_due_at),
    final_eval_due_at: toRiyadhInput(c.final_eval_due_at), final_report_due_at: toRiyadhInput(c.final_report_due_at) };
}

function Schedule({ cycle, onSaved }: { cycle: Cycle; onSaved: (c: Cycle) => void }) {
  const { t } = useTranslation();
  const [form, setForm] = useState(toForm(cycle));
  useEffect(() => setForm(toForm(cycle)), [cycle]);
  const save = useMutation({
    mutationFn: () => {
      const body = scheduleBody(form) as Record<string, unknown>;
      delete body.type;
      return unwrap(api.PATCH("/api/v1/cycles/{cycle_id}", { params: { path: { cycle_id: cycle.id } }, body: body as never }));
    },
    onSuccess: onSaved,
  });
  return (
    <Card title={t("cycles.schedule")}>
      {cycle.schedule_locked && <div className="mb-4"><Notice tone="warning">{t("cycles.schedule_locked")}</Notice></div>}
      <ScheduleFields form={form} setForm={setForm} lockSchedule={cycle.schedule_locked}
        error={save.error instanceof ApiError ? save.error : undefined} />
      <ErrorBox error={save.error} />
      {save.isSuccess && <div className="mt-3"><Notice tone="success">{t("common.saved")}</Notice></div>}
      <Button className="mt-4" busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button>
    </Card>
  );
}

function Weeks({ cycle, onSaved }: { cycle: Cycle; onSaved: () => void }) {
  const { t } = useTranslation();
  const [editing, setEditing] = useState<S<"WeekOut"> | null>(null);
  const [due, setDue] = useState("");
  const [reason, setReason] = useState("");
  const move = useMutation({
    mutationFn: () => unwrap(api.PATCH("/api/v1/cycles/{cycle_id}/weeks/{week_no}", { params: { path: { cycle_id: cycle.id,
      week_no: editing?.week_no ?? 0 } }, body: { report_due_at: fromRiyadhInput(due), reason } })),
    onSuccess: () => {
      setEditing(null);
      onSaved();
    },
  });
  return (
    <Card title={t("cycles.weekly_deadlines")}>
      <Table head={[t("cycles.week"), t("cycles.from_to"), t("cycles.scheduled_days"), t("report.due"), ""]}>
        {cycle.week_list.map((w) => (
          <tr key={w.week_no}>
            <Td className="font-semibold">{w.week_no}</Td>
            <Td>{formatDate(w.starts_on)} – {formatDate(w.ends_on)}</Td>
            <Td>{w.scheduled_days}</Td>
            <Td><span dir="ltr">{formatDateTime(w.report_due_at)}</span></Td>
            <Td>{cycle.status === "open" && <Button tone="ghost" onClick={() => { setEditing(w); setDue(toRiyadhInput(w.report_due_at)); setReason(""); }}>
              {t("cycles.move_deadline")}</Button>}</Td>
          </tr>
        ))}
      </Table>
      <Dialog open={!!editing} title={t("cycles.move_deadline_of", { n: editing?.week_no })} onClose={() => setEditing(null)}>
        <div className="flex flex-col gap-3">
          <Input label={t("report.due")} type="datetime-local" value={due} onChange={(e) => setDue(e.target.value)} hint={t("common.riyadh_time")} />
          <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
          <ErrorBox error={move.error} />
          <div className="flex gap-2">
            <Button busy={move.isPending} disabled={!reason.trim() || !due} onClick={() => move.mutate()}>{t("common.save")}</Button>
            <Button tone="secondary" onClick={() => setEditing(null)}>{t("common.cancel")}</Button>
          </div>
        </div>
      </Dialog>
    </Card>
  );
}

function Weights({ cycle }: { cycle: Cycle }) {
  const { t } = useTranslation();
  const path = { params: { path: { cycle_id: cycle.id } } };
  const current = useQuery({ queryKey: ["components", cycle.id], queryFn: () => unwrap(api.GET("/api/v1/cycles/{cycle_id}/grade-components", path)) });
  const [rows, setRows] = useState<Component[]>([]);
  useEffect(() => {
    if (current.data) setRows(current.data.map((c) => ({ name_en: c.name_en, name_ar: c.name_ar, weight: String(c.weight),
      source: c.source as Component["source"] })));
  }, [current.data]);
  const save = useMutation({ mutationFn: () => unwrap(api.PUT("/api/v1/cycles/{cycle_id}/grade-components",
    { ...path, body: { components: rows.map((r) => ({ ...r, weight: r.weight })) } as never })) });
  const total = rows.reduce((s, r) => s + (Number(r.weight) || 0), 0);
  const update = (i: number, patch: Partial<Component>) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  return (
    <Card title={t("cycles.weights")} actions={<span className={`text-sm font-semibold ${total === 100 ? "text-[#1E6B34]" : "text-[#A61B1B]"}`}>{t("cycles.total", { n: total })}</span>}>
      <div className="flex flex-col gap-3">
        {rows.map((r, i) => (
          <div key={i} className="grid items-end gap-3 rounded-ctl border border-line p-3 md:grid-cols-[1fr_1fr_110px_1fr_auto]">
            <Input label={t("field.name_ar")} value={r.name_ar} onChange={(e) => update(i, { name_ar: e.target.value })} />
            <Input label={t("field.name_en")} dir="ltr" value={r.name_en} onChange={(e) => update(i, { name_en: e.target.value })} />
            <Input label={t("cycles.weight")} dir="ltr" inputMode="decimal" value={r.weight} onChange={(e) => update(i, { weight: e.target.value })} />
            <Select label={t("cycles.source")} value={r.source} onChange={(e) => update(i, { source: e.target.value as Component["source"] })}
              options={[{ value: "company_final_evaluation", label: t("cycles.source_company") }, { value: "academic_supervisor", label: t("cycles.source_academic") }]} />
            <Button tone="ghost" onClick={() => setRows(rows.filter((_, j) => j !== i))}>{t("common.remove")}</Button>
          </div>
        ))}
        <div><Button tone="secondary" onClick={() => setRows([...rows, { name_en: "", name_ar: "", weight: "", source: "academic_supervisor" }])}>{t("cycles.add_component")}</Button></div>
        <ErrorBox error={save.error} />
        {save.isSuccess && <Notice tone="success">{t("common.saved")}</Notice>}
        <div><Button busy={save.isPending} disabled={cycle.status !== "open"} onClick={() => save.mutate()}>{t("common.save")}</Button></div>
      </div>
    </Card>
  );
}

const LEVELS = ["1", "2", "3", "4", "5"];

function Rubric({ cycle }: { cycle: Cycle }) {
  const { t } = useTranslation();
  const path = { params: { path: { cycle_id: cycle.id } } };
  const current = useQuery({ queryKey: ["rubric", cycle.id], queryFn: () => unwrap(api.GET("/api/v1/cycles/{cycle_id}/rubric", path)) });
  const [rows, setRows] = useState<Criterion[]>([]);
  useEffect(() => {
    if (current.data) setRows(current.data.criteria.map((c) => ({ name_en: c.name_en, name_ar: c.name_ar, levels: c.levels as Criterion["levels"] })));
  }, [current.data]);
  const save = useMutation({ mutationFn: () => unwrap(api.PUT("/api/v1/cycles/{cycle_id}/rubric", { ...path, body: { criteria: rows } as never })) });
  const locked = current.data?.locked ?? false;
  const blank = (): Criterion => ({ name_en: "", name_ar: "", levels: Object.fromEntries(LEVELS.map((l) => [l, { en: "", ar: "" }])) });
  const update = (i: number, patch: Partial<Criterion>) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  return (
    <Card title={t("cycles.rubric")}>
      {locked && <div className="mb-4"><Notice tone="warning">{t("cycles.rubric_locked")}</Notice></div>}
      <fieldset disabled={locked || cycle.status !== "open"} className="flex flex-col gap-4">
        {rows.map((r, i) => (
          <div key={i} className="rounded-ctl border border-line p-3">
            <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
              <Input label={t("cycles.criterion_ar")} value={r.name_ar} onChange={(e) => update(i, { name_ar: e.target.value })} />
              <Input label={t("cycles.criterion_en")} dir="ltr" value={r.name_en} onChange={(e) => update(i, { name_en: e.target.value })} />
              <Button tone="ghost" onClick={() => setRows(rows.filter((_, j) => j !== i))}>{t("common.remove")}</Button>
            </div>
            <div className="mt-3 grid gap-2 md:grid-cols-5">
              {LEVELS.map((l) => (
                <div key={l} className="flex flex-col gap-1">
                  <p className="text-xs font-semibold text-ink-muted">{t("cycles.level", { n: l })}</p>
                  <input aria-label={`${t("cycles.level", { n: l })} AR`} className="min-h-[36px] rounded-ctl border border-line px-2 text-sm"
                    placeholder="عربي" value={r.levels[l]?.ar ?? ""}
                    onChange={(e) => update(i, { levels: { ...r.levels, [l]: { ...r.levels[l], ar: e.target.value } } })} />
                  <input aria-label={`${t("cycles.level", { n: l })} EN`} dir="ltr" className="min-h-[36px] rounded-ctl border border-line px-2 text-sm"
                    placeholder="English" value={r.levels[l]?.en ?? ""}
                    onChange={(e) => update(i, { levels: { ...r.levels, [l]: { ...r.levels[l], en: e.target.value } } })} />
                </div>
              ))}
            </div>
          </div>
        ))}
        <div><Button tone="secondary" onClick={() => setRows([...rows, blank()])}>{t("cycles.add_criterion")}</Button></div>
        <ErrorBox error={save.error} />
        {save.isSuccess && <Notice tone="success">{t("common.saved")}</Notice>}
        <div><Button busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button></div>
      </fieldset>
    </Card>
  );
}

function OpenClose({ cycle, onSaved }: { cycle: Cycle; onSaved: () => void }) {
  const { t } = useTranslation();
  const [reopening, setReopening] = useState(false);
  const [reason, setReason] = useState("");
  const path = { params: { path: { cycle_id: cycle.id } } };
  const close = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/cycles/{cycle_id}/close", path)), onSuccess: onSaved });
  const reopen = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/cycles/{cycle_id}/reopen", { ...path, body: { reason } })),
    onSuccess: () => { setReopening(false); onSaved(); } });
  return (
    <Card title={t("cycles.status")}>
      <p className="mb-3 text-sm text-ink-muted">{t(cycle.status === "open" ? "cycles.close_note" : "cycles.reopen_note")}</p>
      <ErrorBox error={close.error} />
      {cycle.status === "open"
        ? <Button tone="danger" busy={close.isPending} onClick={() => close.mutate()}>{t("cycles.close")}</Button>
        : <Button tone="secondary" onClick={() => setReopening(true)}>{t("cycles.reopen")}</Button>}
      <Dialog open={reopening} title={t("cycles.reopen")} onClose={() => setReopening(false)}>
        <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
        <ErrorBox error={reopen.error} />
        <div className="mt-4 flex gap-2">
          <Button busy={reopen.isPending} disabled={!reason.trim()} onClick={() => reopen.mutate()}>{t("cycles.reopen")}</Button>
          <Button tone="secondary" onClick={() => setReopening(false)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}

export default function CycleDetail() {
  const { t } = useTranslation();
  const { cycleId = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"schedule" | "weeks" | "weights" | "rubric" | "stats">("schedule");
  const key = ["cycle", cycleId];
  const cycle = useQuery({ queryKey: key, queryFn: () => unwrap(api.GET("/api/v1/cycles/{cycle_id}", { params: { path: { cycle_id: cycleId } } })) });
  if (cycle.isLoading) return <Loading />;
  if (cycle.error || !cycle.data) return <ErrorBox error={cycle.error} />;
  const c = cycle.data;
  const reload = () => {
    void queryClient.invalidateQueries({ queryKey: key });
    void queryClient.invalidateQueries({ queryKey: ["cycles"] });
  };
  return (
    <>
      <PageHeader title={c.name} subtitle={`${t(`training.${c.type}`)} · ${formatDate(c.start_date)} – ${formatDate(c.end_date)} · ${t("cycles.students_n", { n: c.enrolled_students })}`}
        actions={<StatusChip status={c.status} />} />
      {c.status === "closed" && <div className="mb-4"><Notice tone="warning">{t("cycles.closed_note")}</Notice></div>}
      <Tabs value={tab} onChange={setTab} items={[{ value: "schedule", label: t("cycles.schedule") }, { value: "weeks", label: t("cycles.weekly_deadlines") },
        { value: "weights", label: t("cycles.weights") }, { value: "rubric", label: t("cycles.rubric") },
        { value: "stats", label: t("stats.tab") }]} />
      <div className="flex flex-col gap-4">
        {tab === "schedule" && <><Schedule cycle={c} onSaved={(n) => queryClient.setQueryData(key, n)} /><OpenClose cycle={c} onSaved={reload} /><Privacy cycleId={c.id} /></>}
        {tab === "weeks" && <Weeks cycle={c} onSaved={reload} />}
        {tab === "weights" && <Weights cycle={c} />}
        {tab === "rubric" && <Rubric cycle={c} />}
        {tab === "stats" && <CycleStats cycleId={c.id} />}
      </div>
    </>
  );
}
