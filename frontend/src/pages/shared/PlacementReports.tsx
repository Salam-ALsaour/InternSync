/** One placement and its report slots, for the student, both supervisors, and the coordinator (FR-REP-01). */
import { useQuery } from "@tanstack/react-query";
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api, type S, unwrap } from "../../api/client";
import { Card, Chip, DefList, ErrorBox, Loading, PageHeader, StatusChip, Table, Td } from "../../components/ui";
import { formatDate, formatDateTime, nameOf } from "../../lib/format";

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

export default function PlacementReports() {
  const { t, i18n } = useTranslation();
  const { placementId = "" } = useParams();
  const placement = useQuery({ queryKey: ["placement", placementId], queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}", { params: { path: { placement_id: placementId } } })) });
  if (placement.isLoading) return <Loading />;
  if (placement.error || !placement.data) return <ErrorBox error={placement.error} />;
  const p = placement.data;
  return (
    <>
      <PageHeader title={nameOf(p.student, i18n.language)} subtitle={`${p.company_name} — ${p.vacancy_title}`}
        actions={<StatusChip status={p.status} />} />
      <div className="flex flex-col gap-4">
        <Card><PlacementSummary p={p} /></Card>
        <Card title={t("report.list")}><SlotTable placementId={p.id} /></Card>
      </div>
    </>
  );
}
