/** Certificates issued to students of the coordinator's college (FR-CER-01, FR-CER-03). */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Card, Empty, ErrorBox, Loading, PageHeader, Select, StatusChip, Table, Td } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";

export default function Certificates() {
  const { t, i18n } = useTranslation();
  const cycles = useQuery({ queryKey: ["cycles"], queryFn: () => unwrap(api.GET("/api/v1/cycles")) });
  const [cycleId, setCycleId] = useState("");
  const list = useQuery({ queryKey: ["certificates", cycleId], queryFn: () =>
    unwrap(api.GET("/api/v1/certificates", { params: { query: cycleId ? { cycle_id: cycleId } : {} } })) });
  const rows = list.data ?? [];
  return (
    <>
      <PageHeader title={t("menu.certificates")} subtitle={t("certificate.subtitle")} />
      <div className="mb-4 max-w-sm">
        <Select label={t("field.cycle")} value={cycleId} placeholder={t("common.all")} onChange={(e) => setCycleId(e.target.value)}
          options={(cycles.data ?? []).map((c) => ({ value: c.id, label: c.name }))} />
      </div>
      <ErrorBox error={list.error} />
      <Card>
        {list.isLoading ? <Loading /> : rows.length === 0 ? <Empty /> : (
          <Table head={[t("field.student"), t("field.company"), t("field.cycle"), t("certificate.code"), t("certificate.issued"), ""]}>
            {rows.map((c) => (
              <tr key={c.id}>
                <Td className="font-semibold">{nameOf(c.student, i18n.language)}</Td>
                <Td>{c.company}</Td>
                <Td>{c.cycle}</Td>
                <Td><span dir="ltr" className="font-mono text-xs">{c.code}</span></Td>
                <Td><span dir="ltr">{formatDateTime(c.issued_at)}</span> <StatusChip status={c.status} /></Td>
                <Td><Link to={`/placements/${c.placement_id}?tab=grade`}>{t("common.open")}</Link></Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}
