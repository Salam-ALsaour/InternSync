/** The student's placement: reports, attendance, evaluations, and the Final grade (FR-REP-01, FR-ATT-03, FR-EVL-03,
 *  FR-WFL-06). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Empty, ErrorBox, Loading, PageHeader } from "../../components/ui";
import { PlacementView } from "../shared/PlacementReports";

export default function StudentReports() {
  const { t } = useTranslation();
  const placements = useQuery({ queryKey: ["placements", "mine"], queryFn: () =>
    unwrap(api.GET("/api/v1/placements", { params: { query: { page_size: 20 } } })) });
  if (placements.isLoading) return <Loading />;
  const rows = placements.data?.items ?? [];
  const active = rows.find((p) => p.status === "active") ?? rows[0];
  return (
    <>
      <PageHeader title={t("report.my_training")} />
      <ErrorBox error={placements.error} />
      {!active ? <Empty>{t("report.no_placement")}</Empty> : <PlacementView placementId={active.id} header={false} />}
    </>
  );
}
