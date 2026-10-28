/** Similarity checks of the supervisor's students (FR-SIM-02, FR-DSH-01): flagged ones without a decision first.
 *  Each row opens the report, where the passages are shown side by side. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Advisory, Card, Empty, ErrorBox, Loading, PageHeader, StatusChip, Table, Tabs, Td } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";
import { slotTitle } from "../shared/PlacementReports";

type View = "open" | "decided" | "all";

export default function SimilarityChecks() {
  const { t, i18n } = useTranslation();
  const [view, setView] = useState<View>("open");
  const query = view === "open" ? { flagged: true, decided: false } : view === "decided" ? { decided: true } : {};
  const list = useQuery({ queryKey: ["similarity-checks", view], queryFn: () =>
    unwrap(api.GET("/api/v1/similarity-checks", { params: { query } })) });
  const rows = list.data ?? [];
  return (
    <>
      <PageHeader title={t("menu.similarity")} subtitle={t("similarity.list_subtitle")} />
      <Advisory><p>{t("similarity.advisory_note")}</p></Advisory>
      <div className="mt-4">
        <Tabs value={view} onChange={setView} items={[{ value: "open", label: t("similarity.view_open") },
          { value: "decided", label: t("similarity.view_decided") }, { value: "all", label: t("similarity.view_all") }]} />
      </div>
      <ErrorBox error={list.error} />
      <Card>
        {list.isLoading ? <Loading /> : rows.length === 0 ? <Empty /> : (
          <Table head={[t("field.student"), t("report.title"), t("similarity.score"), t("common.status"), t("similarity.checked_at"), ""]}>
            {rows.map((c) => (
              <tr key={c.check_id}>
                <Td className="font-semibold">{nameOf(c.student, i18n.language)}</Td>
                <Td>{slotTitle(c, t)} · {t("report.version_n", { n: c.version_no })}</Td>
                <Td><span dir="ltr">{c.max_score === null ? "—" : `${Math.round(Number(c.max_score) * 100)}%`}</span></Td>
                <Td>
                  {c.status !== "done" ? <StatusChip status="pending" label={t(`similarity.status_${c.status}`)} />
                    : c.decision ? <StatusChip status="closed" label={t(`similarity.decision_${c.decision}`)} />
                      : <StatusChip status={c.is_flagged ? "flagged" : "clear"}
                        label={c.is_flagged ? t("similarity.flagged") : t("similarity.not_flagged")} />}
                </Td>
                <Td>{c.checked_at ? <span dir="ltr">{formatDateTime(c.checked_at)}</span> : "—"}</Td>
                <Td><Link to={`/reports/${c.slot_id}`}>{t("common.open")}</Link></Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}
