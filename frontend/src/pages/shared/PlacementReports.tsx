/** One placement and its report slots, for the student, both supervisors, and the coordinator (FR-REP-01). */
import { useQuery } from "@tanstack/react-query";
import type { TFunction } from "i18next";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, downloadFile, type S, unwrap } from "../../api/client";
import { Button, Card, Chip, DefList, ErrorBox, Loading, PageHeader, StatusChip, Table, Tabs, Td } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDate, formatDateTime, nameOf } from "../../lib/format";
import Attendance from "./Attendance";
import Evaluations from "./Evaluations";
import Grade from "./Grade";

export function SlotStatus({ slot }: { slot: { status: string; is_late: boolean; is_missing: boolean } }) {
  const { t } = useTranslation();
  return (
    <span className="flex flex-wrap gap-1">
      <StatusChip status={slot.status} />
      {slot.is_late && <StatusChip status="late" label={t("status.late")} />}
      {slot.is_missing && slot.status !== "closed_missing" && <StatusChip status="missing" label={t("status.missing")} />}
    </span>
  );
}

export function slotTitle(slot: { kind: string; week_no?: number | null }, t: TFunction) {
  return slot.kind === "final" ? t("report.final") : t("report.week", { n: slot.week_no });
}

/** FR-EXP-03: the student's training record as a PDF, for the coordinator and the assigned supervisor. */
function TrainingRecord({ placementId }: { placementId: string }) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const download = async () => {
    setBusy(true);
    setError(null);
    try {
      await downloadFile(`/api/v1/placements/${placementId}/exports/training-record`, "training-record.pdf");
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="mt-3">
      <Button tone="secondary" busy={busy} onClick={() => void download()}>{t("exports.training_record")}</Button>
      <ErrorBox error={error} />
    </div>
  );
}

export function PlacementSummary({ p }: { p: S<"PlacementOut"> }) {
  const { t, i18n } = useTranslation();
  return (
    <DefList items={[
      [t("field.student"), nameOf(p.student, i18n.language)],
      [t("field.company"), `${p.company_name} — ${p.vacancy_title}`],
      [t("field.company_supervisor"), nameOf(p.company_supervisor, i18n.language)],
      [t("field.academic_supervisor"), nameOf(p.academic_supervisor, i18n.language)],
      [t("field.cycle"), p.cycle_name],
      [t("field.confirmed_at"), formatDate(p.confirmed_at)],
    ]} />
  );
}

export function SlotTable({ placementId }: { placementId: string }) {
  const { t } = useTranslation();
  const slots = useQuery({ queryKey: ["slots", placementId], queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}/report-slots", { params: { path: { placement_id: placementId } } })) });
  if (slots.isLoading) return <Loading />;
  if (slots.error) return <ErrorBox error={slots.error} />;
  return (
    <Table head={[t("report.slot"), t("report.due"), t("report.status"), t("report.versions"), ""]}>
      {(slots.data ?? []).map((s) => (
        <tr key={s.id}>
          <Td className="font-semibold">{slotTitle(s, t)}</Td>
          <Td><span dir="ltr">{formatDateTime(s.due_at)}</span></Td>
          <Td><SlotStatus slot={s} /></Td>
          <Td>{s.versions > 0 ? s.versions : s.has_draft ? <Chip>{t("report.has_draft")}</Chip> : "—"}</Td>
          <Td><Link to={`/reports/${s.id}`}>{t("common.open")}</Link></Td>
        </tr>
      ))}
    </Table>
  );
}

type Tab = "reports" | "attendance" | "evaluations" | "grade";

/** Everything about one trainee in tabs: reports, attendance, evaluations, and the grade (not for the company). */
export function PlacementView({ placementId, header = true }: { placementId: string; header?: boolean }) {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const [params, setParams] = useSearchParams();
  const placement = useQuery({ queryKey: ["placement", placementId], queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}", { params: { path: { placement_id: placementId } } })) });
  if (placement.isLoading) return <Loading />;
  if (placement.error || !placement.data) return <ErrorBox error={placement.error} />;
  const p = placement.data;
  const tabs: Tab[] = me.role === "company_supervisor" ? ["reports", "attendance", "evaluations"]
    : ["reports", "attendance", "evaluations", "grade"];
  const tab = (tabs as string[]).includes(params.get("tab") ?? "") ? (params.get("tab") as Tab) : "reports";
  return (
    <>
      {header && (
        <PageHeader title={nameOf(p.student, i18n.language)} subtitle={`${p.company_name} — ${p.vacancy_title}`}
          actions={<StatusChip status={p.status} />} />
      )}
      <div className="flex flex-col gap-4">
        <Card>
          <PlacementSummary p={p} />
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Chip tone="info">{t("attendance.percent")}: <span dir="ltr" className="ms-1">{p.attendance_percent === null || p.attendance_percent === undefined ? "—" : `${p.attendance_percent}%`}</span></Chip>
            {p.grade_status && me.role !== "company_supervisor" && (me.role !== "student" || p.grade_status === "final") &&
              <Chip tone={p.grade_status === "final" ? "success" : "neutral"}>{t("grade.title")}: {t(`grade.status_${p.grade_status}`)}</Chip>}
          </div>
          {(me.role === "academic_supervisor" || me.role === "coordinator") && <TrainingRecord placementId={p.id} />}
        </Card>
        <Tabs value={tab} onChange={(v) => setParams({ tab: v }, { replace: true })}
          items={tabs.map((x) => ({ value: x, label: t(`placement.tab_${x}`) }))} />
        {tab === "reports" && <Card title={t("report.list")}><SlotTable placementId={p.id} /></Card>}
        {tab === "attendance" && <Attendance placementId={p.id} />}
        {tab === "evaluations" && <Evaluations placementId={p.id} />}
        {tab === "grade" && <Grade placementId={p.id} />}
      </div>
    </>
  );
}

export default function PlacementReports() {
  const { placementId = "" } = useParams();
  return <PlacementView placementId={placementId} />;
}
