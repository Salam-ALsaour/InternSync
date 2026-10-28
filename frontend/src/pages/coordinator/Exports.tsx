/** Exports of a cycle (FR-EXP-01, FR-EXP-02; wireframe `CO_Exports`): the grade sheet in Excel and PDF, and the
 *  term summary. Files are built by the API in the coordinator's language. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, downloadFile, unwrap } from "../../api/client";
import { Button, Card, ErrorBox, Loading, Notice, PageHeader, Select } from "../../components/ui";

export default function Exports() {
  const { t } = useTranslation();
  const cycles = useQuery({ queryKey: ["cycles"], queryFn: () => unwrap(api.GET("/api/v1/cycles")) });
  const [cycleId, setCycleId] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<unknown>(null);
  if (cycles.isLoading) return <Loading />;
  const items = cycles.data ?? [];
  const chosen = cycleId || items[0]?.id || "";
  const get = async (what: string, path: string, name: string) => {
    setBusy(what);
    setError(null);
    try {
      await downloadFile(path, name);
    } catch (e) {
      setError(e);
    } finally {
      setBusy("");
    }
  };
  const base = `/api/v1/cycles/${chosen}/exports`;
  return (
    <>
      <PageHeader title={t("menu.exports")} subtitle={t("exports.subtitle")} />
      <ErrorBox error={cycles.error ?? error} />
      {items.length === 0 ? <Notice>{t("exports.no_cycles")}</Notice> : (
        <div className="flex flex-col gap-4">
          <Card>
            <Select label={t("field.cycle")} value={chosen} onChange={(e) => setCycleId(e.target.value)}
              options={items.map((c) => ({ value: c.id, label: c.name }))} />
          </Card>
          <Card title={t("exports.grade_sheet")}>
            <p className="mb-3 text-sm text-ink-muted">{t("exports.grade_sheet_note")}</p>
            <div className="flex flex-wrap gap-2">
              <Button busy={busy === "xlsx"} onClick={() => void get("xlsx", `${base}/grade-sheet?format=xlsx`, "grade-sheet.xlsx")}>
                {t("exports.excel")}</Button>
              <Button tone="secondary" busy={busy === "pdf"}
                onClick={() => void get("pdf", `${base}/grade-sheet?format=pdf`, "grade-sheet.pdf")}>{t("exports.pdf")}</Button>
            </div>
          </Card>
          <Card title={t("exports.term_summary")}>
            <p className="mb-3 text-sm text-ink-muted">{t("exports.term_summary_note")}</p>
            <Button tone="secondary" busy={busy === "summary"}
              onClick={() => void get("summary", `${base}/term-summary`, "term-summary.pdf")}>{t("exports.pdf")}</Button>
          </Card>
          <Notice>{t("exports.training_record_note")}</Notice>
        </div>
      )}
    </>
  );
}
