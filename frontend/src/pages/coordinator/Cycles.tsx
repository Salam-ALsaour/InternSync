/** Training cycles of the college: list and create (wireframe `CO_CycleSettings`, FR-CYC-01). */
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api, unwrap } from "../../api/client";
import { Button, Card, Checkbox, Empty, ErrorBox, Input, Loading, PageHeader, Select, StatusChip, Table, Td } from "../../components/ui";
import { formatDate, fromRiyadhInput } from "../../lib/format";
import { useCycles } from "./Students";

export const WEEKDAYS = [7, 1, 2, 3, 4, 5, 6];

export interface ScheduleForm {
  name: string; type: "coop" | "summer"; start_date: string; end_date: string; weeks: string; working_days: number[];
  report_weekday: string; report_time: string; periodic_eval_due_at: string; final_eval_due_at: string;
  final_report_due_at: string;
}

export function ScheduleFields({ form, setForm, error, lockSchedule = false }: { form: ScheduleForm;
  setForm: (f: ScheduleForm) => void; error?: ApiError; lockSchedule?: boolean }) {
  const { t } = useTranslation();
  const set = (k: keyof ScheduleForm) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });
  const fe = (f: string) => error?.fieldMessage(f);
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Input label={t("cycles.name")} value={form.name} onChange={set("name")} error={fe("name")} />
        <Select label={t("vacancy.training_type")} value={form.type} onChange={set("type")} disabled={lockSchedule}
          options={[{ value: "coop", label: t("training.coop") }, { value: "summer", label: t("training.summer") }]} />
        <Input label={t("cycles.weeks")} type="number" min={1} max={30} dir="ltr" value={form.weeks} onChange={set("weeks")}
          disabled={lockSchedule} error={fe("weeks")} />
        <Input label={t("cycles.start")} type="date" value={form.start_date} onChange={set("start_date")} disabled={lockSchedule} error={fe("start_date")} />
        <Input label={t("cycles.end")} type="date" value={form.end_date} onChange={set("end_date")} disabled={lockSchedule} error={fe("end_date")} />
        <Select label={t("cycles.report_weekday")} value={form.report_weekday} onChange={set("report_weekday")} disabled={lockSchedule}
          options={WEEKDAYS.map((d) => ({ value: String(d), label: t(`weekday.${d}`) }))} />
        <Input label={t("cycles.report_time")} type="time" value={form.report_time} onChange={set("report_time")}
          disabled={lockSchedule} hint={t("common.riyadh_time")} />
        <Input label={t("cycles.periodic_eval_due")} type="datetime-local" value={form.periodic_eval_due_at} onChange={set("periodic_eval_due_at")} />
        <Input label={t("cycles.final_eval_due")} type="datetime-local" value={form.final_eval_due_at} onChange={set("final_eval_due_at")} />
        <Input label={t("cycles.final_report_due")} type="datetime-local" value={form.final_report_due_at} onChange={set("final_report_due_at")} />
      </div>
      <div>
        <p className="text-sm font-medium">{t("cycles.working_days")}</p>
        <div className="flex flex-wrap gap-x-4">
          {WEEKDAYS.map((d) => (
            <Checkbox key={d} label={t(`weekday.${d}`)} checked={form.working_days.includes(d)} disabled={lockSchedule}
              onChange={() => setForm({ ...form, working_days: form.working_days.includes(d)
                ? form.working_days.filter((x) => x !== d) : [...form.working_days, d] })} />
          ))}
        </div>
      </div>
    </div>
  );
}

export function scheduleBody(f: ScheduleForm) {
  return { name: f.name, type: f.type, start_date: f.start_date, end_date: f.end_date, weeks: Number(f.weeks),
    working_days: f.working_days, report_weekday: Number(f.report_weekday), report_time: `${f.report_time}:00`.slice(0, 8),
    periodic_eval_due_at: f.periodic_eval_due_at ? fromRiyadhInput(f.periodic_eval_due_at) : "",
    final_eval_due_at: f.final_eval_due_at ? fromRiyadhInput(f.final_eval_due_at) : "",
    final_report_due_at: f.final_report_due_at ? fromRiyadhInput(f.final_report_due_at) : "" };
}

const EMPTY: ScheduleForm = { name: "", type: "coop", start_date: "", end_date: "", weeks: "12", working_days: [7, 1, 2, 3, 4],
  report_weekday: "4", report_time: "23:59", periodic_eval_due_at: "", final_eval_due_at: "", final_report_due_at: "" };

export default function Cycles() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const cycles = useCycles();
  const [form, setForm] = useState<ScheduleForm>(EMPTY);
  const [creating, setCreating] = useState(false);
  const create = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/cycles", { body: scheduleBody(form) as never })),
    onSuccess: (c) => {
      void queryClient.invalidateQueries({ queryKey: ["cycles"] });
      navigate(`/coordinator/cycles/${c.id}`);
    },
  });
  if (cycles.isLoading) return <Loading />;
  const rows = cycles.data ?? [];
  return (
    <>
      <PageHeader title={t("menu.cycles")} actions={!creating && <Button onClick={() => setCreating(true)}>{t("cycles.new")}</Button>} />
      <div className="flex flex-col gap-4">
        {creating && (
          <Card title={t("cycles.new")}>
            <ScheduleFields form={form} setForm={setForm} error={create.error instanceof ApiError ? create.error : undefined} />
            <ErrorBox error={create.error} />
            <div className="mt-4 flex gap-2">
              <Button busy={create.isPending} onClick={() => create.mutate()}>{t("cycles.create")}</Button>
              <Button tone="secondary" onClick={() => setCreating(false)}>{t("common.cancel")}</Button>
            </div>
          </Card>
        )}
        <Card>
          <ErrorBox error={cycles.error} />
          {rows.length === 0 ? <Empty>{t("cycles.none")}</Empty> : (
            <Table head={[t("cycles.name"), t("vacancy.training_type"), t("cycles.period"), t("cycles.weeks"), t("cycles.students"), t("report.status"), ""]}>
              {rows.map((c) => (
                <tr key={c.id}>
                  <Td className="font-semibold">{c.name}</Td>
                  <Td>{t(`training.${c.type}`)}</Td>
                  <Td>{formatDate(c.start_date)} – {formatDate(c.end_date)}</Td>
                  <Td>{c.weeks}</Td>
                  <Td>{c.enrolled_students}</Td>
                  <Td><StatusChip status={c.status} /></Td>
                  <Td><Link to={`/coordinator/cycles/${c.id}`}>{t("cycles.settings")}</Link></Td>
                </tr>
              ))}
            </Table>
          )}
        </Card>
      </div>
    </>
  );
}
