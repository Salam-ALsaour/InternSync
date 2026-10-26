/** The company's trainees and their reports, read-only (FR-REP-06). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Card, Empty, ErrorBox, Loading, PageHeader, StatusChip, Table, Td } from "../../components/ui";
import { nameOf } from "../../lib/format";

/** Placements visible to the caller, with report counts; used by the company and the academic supervisor. */
export function PlacementTable({ title }: { title: string }) {
  const { t, i18n } = useTranslation();
  const list = useQuery({ queryKey: ["placements"], queryFn: () =>
    unwrap(api.GET("/api/v1/placements", { params: { query: { page_size: 100 } } })) });
  if (list.isLoading) return <Loading />;
  const rows = list.data?.items ?? [];
  return (
    <>
      <PageHeader title={title} />
      <ErrorBox error={list.error} />
      <Card>
        {rows.length === 0 ? <Empty /> : (
          <Table head={[t("field.student"), t("field.company"), t("field.cycle"), t("report.accepted"),
            t("report.waiting"), t("status.late"), t("status.missing"), ""]}>
            {rows.map((p) => (
              <tr key={p.id}>
                <Td className="font-semibold">{nameOf(p.student, i18n.language)}{p.status !== "active" && <div className="mt-1"><StatusChip status={p.status} /></div>}</Td>
                <Td>{p.company_name}<p className="text-xs text-ink-muted">{p.vacancy_title}</p></Td>
                <Td>{p.cycle_name}</Td>
                <Td><span dir="ltr">{p.reports.accepted} / {p.reports.total}</span></Td>
                <Td>{p.reports.submitted}</Td>
                <Td>{p.reports.late}</Td>
                <Td>{p.reports.missing}</Td>
                <Td><Link to={`/placements/${p.id}`}>{t("report.open_reports")}</Link></Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}

export default function CompanyTrainees() {
  const { t } = useTranslation();
  return <PlacementTable title={t("menu.trainees")} />;
}
