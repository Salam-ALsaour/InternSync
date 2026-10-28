/** Items of the college still outstanding 3 days after their deadline (FR-NOT-04): reports, attendance weeks, and
 *  evaluations. Each row opens the placement. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Card, Empty, ErrorBox, Loading, PageHeader, StatusChip, Table, Tabs, Td } from "../../components/ui";
import { formatDateTime } from "../../lib/format";

type Kind = "all" | "report" | "attendance" | "evaluation";

export default function Escalations() {
  const { t, i18n } = useTranslation();
  const [kind, setKind] = useState<Kind>("all");
  const list = useQuery({ queryKey: ["escalations", kind], queryFn: () =>
    unwrap(api.GET("/api/v1/escalations", { params: { query: kind === "all" ? {} : { type: kind } } })) });
  const rows = list.data ?? [];
  const ar = i18n.language === "ar";
  return (
    <>
      <PageHeader title={t("menu.escalations")} subtitle={t("escalations.subtitle")} />
      <Tabs value={kind} onChange={setKind} items={(["all", "report", "attendance", "evaluation"] as Kind[])
        .map((k) => ({ value: k, label: t(`escalations.kind_${k}`) }))} />
      <ErrorBox error={list.error} />
      <Card>
        {list.isLoading ? <Loading /> : rows.length === 0 ? <Empty /> : (
          <Table head={[t("field.student"), t("escalations.item"), t("report.due"), t("escalations.overdue"), ""]}>
            {rows.map((e, i) => (
              <tr key={i}>
                <Td className="font-semibold">{ar ? e.student_ar : e.student_en}</Td>
                <Td>{ar ? e.item_ar : e.item_en}</Td>
                <Td><span dir="ltr">{formatDateTime(e.due_at)}</span></Td>
                <Td><StatusChip status="missing" label={String(e.days_overdue)} /></Td>
                <Td><Link to={`/placements/${e.placement_id}`}>{t("common.open")}</Link></Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}
