/** The completion certificate of a placement (FR-CER-01, FR-CER-03): the coordinator issues and revokes it, the
 *  student and the coordinator open the PDF and the public verification page. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, openFile, unwrap } from "../../api/client";
import { Button, Card, DefList, Dialog, ErrorBox, Notice, StatusChip, TextArea } from "../../components/ui";
import { formatDateTime } from "../../lib/format";

export function CertificateCard({ placementId, coordinator }: { placementId: string; coordinator: boolean }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const key = ["certificate", placementId];
  const q = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}/certificate", { params: { path: { placement_id: placementId } } })) });
  const [revoking, setRevoking] = useState(false);
  const [reason, setReason] = useState("");
  const [fileError, setFileError] = useState<unknown>(null);
  const reload = () => {
    void queryClient.invalidateQueries({ queryKey: key });
    void queryClient.invalidateQueries({ queryKey: ["certificates"] });
  };
  const issue = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/placements/{placement_id}/certificate",
    { params: { path: { placement_id: placementId } } })), onSuccess: (v) => { queryClient.setQueryData(key, v); reload(); } });
  const revoke = useMutation({ mutationFn: (id: string) => unwrap(api.POST("/api/v1/certificates/{certificate_id}/revoke",
    { params: { path: { certificate_id: id } }, body: { reason } })), onSuccess: () => { setRevoking(false); reload(); } });
  const v = q.data;
  if (!v || (!v.certificate && !coordinator)) return null;
  const c = v.certificate;
  return (
    <Card title={t("certificate.title")} actions={c && <StatusChip status={c.status} />}>
      <div className="flex flex-col gap-3">
        {c ? (
          <>
            <DefList items={[
              [t("certificate.code"), <span dir="ltr" className="font-mono">{c.code}</span>],
              [t("certificate.issued"), <span dir="ltr">{formatDateTime(c.issued_at)}</span>],
              ...(c.revoked_at ? [[t("certificate.revoked_at"), <span><span dir="ltr">{formatDateTime(c.revoked_at)}</span> · {c.revoke_reason}</span>] as [string, JSX.Element]] : []),
            ]} />
            <div className="flex flex-wrap gap-2">
              <Button tone="secondary" onClick={() => openFile(c.file_id).catch(setFileError)}>{t("certificate.open_pdf")}</Button>
              <a href={`/verify/${c.code}`} target="_blank" rel="noopener" className="inline-flex min-h-[44px] items-center px-2 text-sm font-semibold">
                {t("certificate.page")}</a>
              {c.can_revoke && <Button tone="danger" onClick={() => { setRevoking(true); setReason(""); }}>{t("certificate.revoke")}</Button>}
            </div>
          </>
        ) : <p className="text-sm text-ink-muted">{t("certificate.none")}</p>}
        {coordinator && !v.can_issue && !c && <Notice>{t("certificate.issue_note")}</Notice>}
        {v.can_issue && <div><Button busy={issue.isPending} onClick={() => issue.mutate()}>{t("certificate.issue")}</Button></div>}
        <ErrorBox error={issue.error ?? fileError} />
      </div>
      <Dialog open={revoking && !!c} title={t("certificate.revoke")} onClose={() => setRevoking(false)}>
        <p className="mb-3 text-sm text-ink-muted">{t("certificate.revoke_note")}</p>
        <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
        <ErrorBox error={revoke.error} />
        <div className="mt-4 flex gap-2">
          <Button tone="danger" busy={revoke.isPending} disabled={!reason.trim()} onClick={() => c && revoke.mutate(c.id)}>{t("certificate.revoke")}</Button>
          <Button tone="secondary" onClick={() => setRevoking(false)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}
