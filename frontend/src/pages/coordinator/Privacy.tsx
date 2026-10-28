/** Retention period of the college and anonymization of a closed cycle (NFR-PRV-04). The counts are shown and
 *  confirmed before anything is removed. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Button, Card, Dialog, ErrorBox, Input, Loading, Notice } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDate } from "../../lib/format";

export default function Privacy({ cycleId }: { cycleId: string }) {
  const { t } = useTranslation();
  const me = useMe();
  const queryClient = useQueryClient();
  const collegeId = me.organization.college_id ?? "";
  const key = ["anonymization", cycleId];
  const state = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/cycles/{cycle_id}/anonymization", { params: { path: { cycle_id: cycleId } } })) });
  const [months, setMonths] = useState("");
  const [confirming, setConfirming] = useState(false);
  useEffect(() => {
    if (state.data) setMonths(String(state.data.retention_months));
  }, [state.data]);
  const retention = useMutation({ mutationFn: () => unwrap(api.PUT("/api/v1/colleges/{college_id}/retention", {
    params: { path: { college_id: collegeId } }, body: { retention_months: Number(months) } })),
  onSuccess: () => void queryClient.invalidateQueries({ queryKey: key }) });
  const anonymize = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/cycles/{cycle_id}/anonymize", {
    params: { path: { cycle_id: cycleId } }, body: { confirm: true } })),
  onSuccess: (v) => {
    queryClient.setQueryData(key, v);
    setConfirming(false);
    void queryClient.invalidateQueries();
  } });
  if (state.isLoading) return <Loading />;
  if (!state.data) return <ErrorBox error={state.error} />;
  const a = state.data;
  return (
    <Card title={t("privacy.title")}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end gap-2">
          <div className="w-64">
            <Input label={t("privacy.retention")} hint={t("privacy.retention_note")} type="number" min={0} max={120} dir="ltr"
              value={months} onChange={(e) => setMonths(e.target.value)} />
          </div>
          <Button tone="secondary" busy={retention.isPending}
            disabled={months === "" || Number(months) === a.retention_months} onClick={() => retention.mutate()}>{t("common.save")}</Button>
        </div>
        <ErrorBox error={retention.error} />
        {a.status === "open" && <Notice>{t("privacy.open")}</Notice>}
        {a.status === "waiting" && <Notice>{t("privacy.waiting", { date: formatDate(a.eligible_at) })}</Notice>}
        {a.status === "ready" && (
          <>
            <Notice tone="warning">{t("privacy.ready", { n: a.students, skipped: a.skipped })}</Notice>
            <div><Button tone="danger" disabled={a.students === 0} onClick={() => setConfirming(true)}>{t("privacy.anonymize")}</Button></div>
          </>
        )}
        {a.status === "done" && <Notice tone="success">{t("privacy.done", { date: formatDate(a.anonymized_at) })}</Notice>}
      </div>
      <Dialog open={confirming} title={t("privacy.confirm_title")} onClose={() => setConfirming(false)}>
        <p className="mb-2 text-sm">{t("privacy.ready", { n: a.students, skipped: a.skipped })}</p>
        <p className="mb-4 text-sm text-[#A61B1B]">{t("privacy.confirm_note")}</p>
        <ErrorBox error={anonymize.error} />
        <div className="mt-4 flex gap-2">
          <Button tone="danger" busy={anonymize.isPending} onClick={() => anonymize.mutate()}>{t("privacy.anonymize")}</Button>
          <Button tone="secondary" onClick={() => setConfirming(false)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}
