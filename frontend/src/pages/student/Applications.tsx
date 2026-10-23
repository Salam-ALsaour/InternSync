/** My applications with their status and withdrawal (FR-VAC-04, FR-VAC-05). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Loading, PageHeader, StatusChip, Table, Td } from "../../components/ui";
import { formatDateTime } from "../../lib/format";

export default function Applications() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ["applications"], queryFn: () =>
    unwrap(api.GET("/api/v1/applications", { params: { query: { page_size: 100 } } })) });
  const withdraw = useMutation({
    mutationFn: (id: string) => unwrap(api.POST("/api/v1/applications/{application_id}/withdraw", { params: { path: { application_id: id } } })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["applications"] });
      void queryClient.invalidateQueries({ queryKey: ["vacancies"] });
    },
  });
  if (list.isLoading) return <Loading />;
  const rows = list.data?.items ?? [];
  return (
    <>
      <PageHeader title={t("applications.title")} />
      <ErrorBox error={list.error ?? withdraw.error} />
      <Card>
        {rows.length === 0 ? <Empty>{t("applications.none")}</Empty> : (
          <Table head={[t("vacancy.title"), t("field.company"), t("applications.applied_at"), t("report.status"), ""]}>
            {rows.map((a) => (
              <tr key={a.id}>
                <Td className="font-semibold">{a.vacancy_title}</Td>
                <Td>{a.company_name}</Td>
                <Td><span dir="ltr">{formatDateTime(a.created_at)}</span></Td>
                <Td>
                  <StatusChip status={a.status} />
                  {a.withdraw_reason && a.withdraw_reason !== "student" && (
                    <p className="mt-1 text-xs text-ink-muted">{t(`withdraw_reason.${a.withdraw_reason}`)}</p>
                  )}
                </Td>
                <Td>
                  {a.status === "submitted" && (
                    <Button tone="danger" busy={withdraw.isPending && withdraw.variables === a.id}
                      onClick={() => withdraw.mutate(a.id)}>{t("applications.withdraw")}</Button>
                  )}
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}
