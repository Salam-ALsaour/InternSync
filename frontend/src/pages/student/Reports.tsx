/** The student's placement and report list (wireframe `ST_Report` list; FR-REP-01). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Card, Empty, ErrorBox, Loading, PageHeader, StatusChip } from "../../components/ui";
import { PlacementSummary, SlotTable } from "../shared/PlacementReports";

export default function StudentReports() {
  const { t } = useTranslation();
  const placements = useQuery({ queryKey: ["placements", "mine"], queryFn: () =>
    unwrap(api.GET("/api/v1/placements", { params: { query: { page_size: 20 } } })) });
  if (placements.isLoading) return <Loading />;
  const rows = placements.data?.items ?? [];
  const active = rows.find((p) => p.status === "active") ?? rows[0];
  return (
    <>
      <PageHeader title={t("report.my_reports")} />
      <ErrorBox error={placements.error} />
      {!active ? <Empty>{t("report.no_placement")}</Empty> : (
        <div className="flex flex-col gap-4">
          <Card title={t("report.my_training")} actions={<StatusChip status={active.status} />}>
            <PlacementSummary p={active} />
          </Card>
          <Card title={t("report.list")}><SlotTable placementId={active.id} /></Card>
        </div>
      )}
    </>
  );
}
