/** Own verification status, documents, the rejection reason, and resubmission (wireframe `Verification_Pending`,
 *  FR-ORG-02, FR-ORG-09). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, sendForm, unwrap } from "../../api/client";
import { Button, Card, DefList, Empty, ErrorBox, Input, Loading, Notice, PageHeader, StatusChip } from "../../components/ui";
import { useAuth } from "../../lib/auth";
import { formatDateTime } from "../../lib/format";
import { DOCUMENTS } from "../public/Register";

type Kind = keyof typeof DOCUMENTS;

function Resubmit({ kind, onDone }: { kind: Kind; onDone: () => void }) {
  const { t } = useTranslation();
  const [values, setValues] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const action = useMutation({
    mutationFn: () => {
      const form = new FormData();
      for (const [k, v] of Object.entries(values)) if (v.trim()) form.set(k, v.trim());
      for (const doc of DOCUMENTS[kind]) if (files[doc]) form.set(doc, files[doc] as File);
      return sendForm<S<"MyRequestOut">[]>("POST", "/api/v1/me/verification", form);
    },
    onSuccess: onDone,
  });
  const set = (k: string) => (e: { target: { value: string } }) => setValues((v) => ({ ...v, [k]: e.target.value }));
  const submit = (e: FormEvent) => {
    e.preventDefault();
    action.mutate();
  };
  return (
    <Card title={t("verification.resubmit")}>
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <p className="text-sm text-ink-muted">{t("verification.resubmit_hint")}</p>
        <ErrorBox error={action.error} />
        {kind === "student" && (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t("field.student_number")} dir="ltr" value={values.student_number ?? ""} onChange={set("student_number")} />
            <Input label={t("field.gpa")} dir="ltr" value={values.gpa ?? ""} onChange={set("gpa")} />
          </div>
        )}
        {kind === "company" && (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t("field.company_name")} value={values.company_name ?? ""} onChange={set("company_name")} />
            <Input label={t("field.commercial_reg_no")} dir="ltr" value={values.commercial_reg_no ?? ""}
              onChange={set("commercial_reg_no")} />
          </div>
        )}
        {DOCUMENTS[kind].map((doc) => (
          <Input key={doc} label={t(`document.${doc}`)} type="file" accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => setFiles((f) => ({ ...f, [doc]: e.target.files?.[0] ?? null }))} />
        ))}
        <Button type="submit" busy={action.isPending}>{t("verification.resubmit_button")}</Button>
      </form>
    </Card>
  );
}

export default function Verification() {
  const { t, i18n } = useTranslation();
  const { refresh } = useAuth();
  const queryClient = useQueryClient();
  const mine = useQuery({ queryKey: ["my-verification"], queryFn: () => unwrap(api.GET("/api/v1/me/verification")) });
  if (mine.isLoading) return <Loading />;
  const requests = mine.data ?? [];
  const latest = requests[0];
  const done = async () => {
    await queryClient.invalidateQueries({ queryKey: ["my-verification"] });
    await refresh();
  };
  return (
    <>
      <PageHeader title={t("verification.title")} />
      <ErrorBox error={mine.error} />
      {!latest && <Empty>{t("verification.none")}</Empty>}
      {latest && (
        <div className="flex flex-col gap-4">
          {latest.status === "pending" && <Notice tone="warning">{t(`verification.pending_${latest.kind}`)}</Notice>}
          {latest.status === "approved" && <Notice tone="success">{t("verification.approved")}</Notice>}
          {requests.map((r) => (
            <Card key={r.id} title={formatDateTime(r.submitted_at)} actions={<StatusChip status={r.status} />}>
              <DefList items={[
                [t("verification.kind"), t(`register.kind_${r.kind}`)],
                [t("verification.decided_at"), formatDateTime(r.decided_at)],
                ...(r.reason ? [[t("verification.reason"), r.reason] as [string, string]] : []),
                [t("verification.documents"), r.documents.map((d) => `${t(`document.${d.kind}`)}${d.purged ? ` (${t("verification.purged")})` : ""}`).join(i18n.language === "ar" ? "، " : ", ")],
              ]} />
            </Card>
          ))}
          {latest.status === "rejected" && <Resubmit kind={latest.kind as Kind} onDone={() => void done()} />}
        </div>
      )}
    </>
  );
}
