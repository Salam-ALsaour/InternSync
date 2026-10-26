/** Weekly attendance of one placement (wireframe `CS_Attendance`, FR-ATT-01 – 04). "Full attendance" is one
 *  button; the coordinator unlocks a locked week with a reason. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Chip, Dialog, ErrorBox, Input, Loading, Notice, Table, Td, TextArea } from "../../components/ui";
import { formatDate } from "../../lib/format";

type Week = S<"AttendanceWeekOut">;

const TONE: Record<string, "neutral" | "info" | "success" | "warning" | "danger"> = {
  upcoming: "neutral", open: "info", pending: "warning", overdue: "danger", recorded: "success",
};

function WeekEditor({ week, onSave, onCancel, busy }: { week: Week; busy: boolean; onCancel: () => void;
  onSave: (body: { full?: boolean; attended_days?: number; note?: string }) => void }) {
  const { t } = useTranslation();
  const [days, setDays] = useState(String(week.attended_days ?? week.scheduled_days));
  const [note, setNote] = useState(week.note ?? "");
  return (
    <div className="flex flex-col gap-3">
      <Button busy={busy} className="min-h-[48px]" onClick={() => onSave({ full: true })}>
        {t("attendance.full", { n: week.scheduled_days })}</Button>
      <p className="text-center text-xs text-ink-muted">{t("attendance.or_partial")}</p>
      <Input label={t("attendance.attended_days")} type="number" min={0} max={week.scheduled_days} dir="ltr" value={days}
        onChange={(e) => setDays(e.target.value)} hint={t("attendance.of_scheduled", { n: week.scheduled_days })} />
      <TextArea label={t("attendance.note")} rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
      <Button tone="secondary" busy={busy} onClick={() => onSave({ attended_days: Number(days), note })}>{t("common.save")}</Button>
      <Button tone="ghost" onClick={onCancel}>{t("common.cancel")}</Button>
    </div>
  );
}

export default function Attendance({ placementId }: { placementId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const key = ["attendance", placementId];
  const path = { params: { path: { placement_id: placementId } } };
  const data = useQuery({ queryKey: key, queryFn: () => unwrap(api.GET("/api/v1/placements/{placement_id}/attendance", path)) });
  const [editing, setEditing] = useState<Week | null>(null);
  const [unlocking, setUnlocking] = useState<Week | null>(null);
  const [reason, setReason] = useState("");
  const done = (out: S<"AttendanceOut">) => {
    queryClient.setQueryData(key, out);
    void queryClient.invalidateQueries({ queryKey: ["placement", placementId] });
    setEditing(null);
    setUnlocking(null);
  };
  const record = useMutation({
    mutationFn: ({ week, body }: { week: number; body: { full?: boolean; attended_days?: number; note?: string } }) =>
      unwrap(api.PUT("/api/v1/placements/{placement_id}/attendance/{week_no}", {
        params: { path: { placement_id: placementId, week_no: week } }, body: { ...body, full: body.full ?? false } })),
    onSuccess: done,
  });
  const unlock = useMutation({
    mutationFn: (week: number) => unwrap(api.POST("/api/v1/placements/{placement_id}/attendance/{week_no}/unlock", {
      params: { path: { placement_id: placementId, week_no: week } }, body: { reason } })),
    onSuccess: done,
  });
  if (data.isLoading) return <Loading />;
  if (data.error || !data.data) return <ErrorBox error={data.error} />;
  const a = data.data;
  return (
    <Card title={t("attendance.title")}
      actions={<span className="text-sm font-semibold">{t("attendance.percent")}: <span dir="ltr">{a.percent === null ? "—" : `${a.percent}%`}</span>
        <span className="ms-2 text-xs font-normal text-ink-muted" dir="ltr">({a.attended_days} / {a.scheduled_days})</span></span>}>
      <ErrorBox error={record.error ?? unlock.error} />
      <Table head={[t("cycles.week"), t("cycles.from_to"), t("attendance.days"), t("attendance.note"), t("report.status"), ""]}>
        {a.weeks.map((w) => (
          <tr key={w.week_no}>
            <Td className="font-semibold">{w.week_no}</Td>
            <Td>{formatDate(w.starts_on)} – {formatDate(w.ends_on)}</Td>
            <Td><span dir="ltr">{w.attended_days === null ? "—" : `${w.attended_days} / ${w.scheduled_days}`}</span></Td>
            <Td><span className="text-xs">{w.note ?? ""}</span></Td>
            <Td>
              <span className="flex flex-wrap gap-1">
                <Chip tone={TONE[w.state] ?? "neutral"}>{t(`attendance.state_${w.state}`)}</Chip>
                {w.locked && <Chip tone="neutral">{t("attendance.locked")}</Chip>}
              </span>
            </Td>
            <Td>
              {a.can_record && w.state !== "upcoming" && !w.locked && (
                <Button tone="ghost" className="min-h-0 px-0" onClick={() => setEditing(w)}>
                  {w.state === "recorded" ? t("common.edit") : t("attendance.record")}</Button>
              )}
              {a.can_unlock && w.locked && (
                <Button tone="ghost" className="min-h-0 px-0" onClick={() => { setUnlocking(w); setReason(""); }}>{t("attendance.unlock")}</Button>
              )}
            </Td>
          </tr>
        ))}
      </Table>
      {a.can_record && <div className="mt-3"><Notice>{t("attendance.window_note")}</Notice></div>}
      <Dialog open={!!editing} title={t("attendance.week_title", { n: editing?.week_no })} onClose={() => setEditing(null)}>
        {editing && <WeekEditor week={editing} busy={record.isPending} onCancel={() => setEditing(null)} onSave={(body) => record.mutate({ week: editing.week_no, body })} />}
        <ErrorBox error={record.error} />
      </Dialog>
      <Dialog open={!!unlocking} title={t("attendance.unlock_title", { n: unlocking?.week_no })} onClose={() => setUnlocking(null)}>
        <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
        <ErrorBox error={unlock.error} />
        <div className="mt-4 flex gap-2">
          <Button busy={unlock.isPending} disabled={!reason.trim()} onClick={() => unlocking && unlock.mutate(unlocking.week_no)}>{t("attendance.unlock")}</Button>
          <Button tone="secondary" onClick={() => setUnlocking(null)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}
