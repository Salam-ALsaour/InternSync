/** Grades of the college (coordinator: approve one or many, return, reopen; wireframe `CO_Grades`) or of the
 *  academic supervisor's students (FR-WFL-03 – 07). Each row opens the placement's grade tab. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Button, Card, Checkbox, Empty, ErrorBox, Loading, Notice, PageHeader, StatusChip, Table, Tabs, Td } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDateTime, nameOf } from "../../lib/format";

type Status = "submitted" | "draft" | "final";

export default function Grades() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const coordinator = me.role === "coordinator";
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<Status>(coordinator ? "submitted" : "draft");
  const [picked, setPicked] = useState<string[]>([]);
  const list = useQuery({ queryKey: ["grades", status], queryFn: () =>
    unwrap(api.GET("/api/v1/grades", { params: { query: { status } } })) });
  const bulk = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/grades/bulk-approve", { body: { grade_ids: picked } })),
    onSuccess: () => {
      setPicked([]);
      void queryClient.invalidateQueries({ queryKey: ["grades"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const rows = list.data ?? [];
  const toggle = (id: string) => setPicked(picked.includes(id) ? picked.filter((x) => x !== id) : [...picked, id]);
  const failed = (bulk.data ?? []).filter((r) => !r.ok);
  return (
    <>
      <PageHeader title={t("menu.grades")} />
      <Tabs value={status} onChange={(v) => { setStatus(v); setPicked([]); }} items={[
        { value: "submitted", label: t("grade.status_submitted") }, { value: "draft", label: t("grade.status_draft") },
        { value: "final", label: t("grade.status_final") }]} />
      <Card>
        <ErrorBox error={list.error ?? bulk.error} />
        {bulk.isSuccess && failed.length === 0 && <div className="mb-3"><Notice tone="success">{t("grade.bulk_done", { n: bulk.data.length })}</Notice></div>}
        {failed.length > 0 && <div className="mb-3"><Notice tone="warning">{t("grade.bulk_failed", { n: failed.length })}</Notice></div>}
        {list.isLoading ? <Loading /> : rows.length === 0 ? <Empty /> : (
          <Table head={[coordinator && status === "submitted" ? "" : null, t("field.student"), t("field.company"), t("grade.total"),
            t("report.status"), t("grade.submitted_at"), ""].filter((x) => x !== null)}>
            {rows.map((g) => (
              <tr key={g.id}>
                {coordinator && status === "submitted" && (
                  <Td><Checkbox label="" aria-label={nameOf(g.student, i18n.language)} checked={picked.includes(g.id)} onChange={() => toggle(g.id)} /></Td>
                )}
                <Td className="font-semibold">{nameOf(g.student, i18n.language)}</Td>
                <Td>{g.company_name}</Td>
                <Td><span dir="ltr">{g.total ?? "—"}</span></Td>
                <Td><StatusChip status={g.status} label={t(`grade.status_${g.status}`)} /></Td>
                <Td><span dir="ltr">{formatDateTime(g.submitted_at)}</span></Td>
                <Td><Link to={`/placements/${g.placement_id}?tab=grade`}>{t("common.open")}</Link></Td>
              </tr>
            ))}
          </Table>
        )}
        {coordinator && status === "submitted" && rows.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button tone="secondary" onClick={() => setPicked(picked.length === rows.length ? [] : rows.map((g) => g.id))}>
              {picked.length === rows.length ? t("grade.select_none") : t("grade.select_all")}</Button>
            <Button busy={bulk.isPending} disabled={picked.length === 0} onClick={() => bulk.mutate()}>{t("grade.bulk_approve", { n: picked.length })}</Button>
          </div>
        )}
      </Card>
    </>
  );
}
