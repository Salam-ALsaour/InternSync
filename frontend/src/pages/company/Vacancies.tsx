/** The company's vacancies: the supervisor's own, or all of the company for the Company Admin (FR-VAC-01). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Loading, PageHeader, StatusChip, Table, Td } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDateTime, nameOf } from "../../lib/format";

export default function CompanyVacancies() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const list = useQuery({ queryKey: ["company-vacancies"], queryFn: () =>
    unwrap(api.GET("/api/v1/vacancies", { params: { query: { page_size: 100 } } })) });
  if (list.isLoading) return <Loading />;
  const rows = (list.data?.items ?? []).filter((v) => me.is_company_admin || v.company_supervisor.id === me.id);
  return (
    <>
      <PageHeader title={t("company.vacancies_title")}
        actions={<Link to="/company/vacancies/new"><Button>{t("company.new_vacancy")}</Button></Link>} />
      <ErrorBox error={list.error} />
      <Card>
        {rows.length === 0 ? <Empty>{t("company.no_vacancies")}</Empty> : (
          <Table head={[t("vacancy.title"), t("field.company_supervisor"), t("vacancy.deadline"), t("vacancy.seats"),
            t("company.applicants"), t("report.status"), ""]}>
            {rows.map((v) => (
              <tr key={v.id}>
                <Td className="font-semibold">{v.title}<p className="text-xs font-normal text-ink-muted">{v.city} · {t(`training.${v.training_type}`)}</p></Td>
                <Td>{nameOf(v.company_supervisor, i18n.language)}</Td>
                <Td><span dir="ltr">{formatDateTime(v.application_deadline)}</span></Td>
                <Td><span dir="ltr">{v.seats_taken} / {v.seats}</span></Td>
                <Td>{v.applicants ?? 0}</Td>
                <Td><StatusChip status={v.status} /></Td>
                <Td>
                  <div className="flex flex-col gap-1">
                    <Link to={`/company/vacancies/${v.id}`}>{t("common.open")}</Link>
                    {v.status !== "draft" && <Link to={`/company/vacancies/${v.id}/applicants`}>{t("company.applicants")}</Link>}
                  </div>
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}
