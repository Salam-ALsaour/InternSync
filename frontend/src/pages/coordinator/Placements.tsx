/** Placements: accepted applicants waiting for confirmation, and confirmed placements with supervisor change and
 *  cancellation (wireframe `CO_Placements`, FR-VAC-07, FR-VAC-08). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Dialog, Empty, ErrorBox, Loading, PageHeader, Select, StatusChip, Table, Tabs, Td, TextArea } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDateTime, nameOf } from "../../lib/format";
import { useCollegeSupervisors } from "./Supervisors";

function Candidate({ c, supervisors, onDone }: { c: S<"AcceptedApplicant">; supervisors: S<"MemberOut">[]; onDone: () => void }) {
  const { t, i18n } = useTranslation();
  const [academic, setAcademic] = useState("");
  const [company, setCompany] = useState(c.vacancy_owner.id);
  const confirm = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/placements", { body: { application_id: c.application_id,
      academic_supervisor_id: academic, company_supervisor_id: company || null } })),
    onSuccess: onDone,
  });
  const active = supervisors.filter((s) => s.is_active && !s.invitation_pending);
  return (
    <Card title={nameOf(c.student, i18n.language)} actions={<span className="text-sm text-ink-muted">{c.student_number}</span>}>
      <p className="mb-3 text-sm">{c.company_name} — {c.vacancy_title} · {t("placements.accepted_at")} <span dir="ltr">{formatDateTime(c.decided_at)}</span></p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Select label={t("field.academic_supervisor")} value={academic} onChange={(e) => setAcademic(e.target.value)} placeholder={t("common.choose")}
          options={active.map((s) => ({ value: s.id, label: `${nameOf(s, i18n.language)} (${t("placements.load", { n: s.active_students })})` }))} />
        <Select label={t("field.company_supervisor")} value={company} onChange={(e) => setCompany(e.target.value)}
          options={c.company_supervisors.map((s) => ({ value: s.id, label: nameOf(s, i18n.language) }))} hint={t("placements.owner_default")} />
      </div>
      <ErrorBox error={confirm.error} />
      <Button className="mt-4" busy={confirm.isPending} disabled={!academic} onClick={() => confirm.mutate()}>{t("placements.confirm")}</Button>
    </Card>
  );
}

function Confirmed({ supervisors }: { supervisors: S<"MemberOut">[] }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ["placements"], queryFn: () => unwrap(api.GET("/api/v1/placements", { params: { query: { page_size: 100 } } })) });
  const [dialog, setDialog] = useState<{ p: S<"PlacementOut">; kind: "change" | "cancel" } | null>(null);
  const [supervisor, setSupervisor] = useState("");
  const [reason, setReason] = useState("");
  const done = () => {
    setDialog(null);
    void queryClient.invalidateQueries({ queryKey: ["placements"] });
  };
  const act = useMutation({
    mutationFn: () => {
      const path = { params: { path: { placement_id: dialog?.p.id ?? "" } } };
      return dialog?.kind === "change"
        ? unwrap(api.PATCH("/api/v1/placements/{placement_id}/academic-supervisor", { ...path, body: { academic_supervisor_id: supervisor, reason } }))
        : unwrap(api.POST("/api/v1/placements/{placement_id}/cancel", { ...path, body: { reason } }));
    },
    onSuccess: done,
  });
  if (list.isLoading) return <Loading />;
  const rows = list.data?.items ?? [];
  return (
    <>
      <ErrorBox error={list.error} />
      {rows.length === 0 ? <Empty /> : (
        <Table head={[t("field.student"), t("field.company"), t("field.academic_supervisor"), t("report.accepted"), t("report.status"), ""]}>
          {rows.map((p) => (
            <tr key={p.id}>
              <Td className="font-semibold">{nameOf(p.student, i18n.language)}</Td>
              <Td>{p.company_name}<p className="text-xs text-ink-muted">{p.vacancy_title} · {nameOf(p.company_supervisor, i18n.language)}</p></Td>
              <Td>{nameOf(p.academic_supervisor, i18n.language)}</Td>
              <Td><span dir="ltr">{p.reports.accepted} / {p.reports.total}</span></Td>
              <Td><StatusChip status={p.status} /></Td>
              <Td>
                <div className="flex flex-col items-start gap-1">
                  <Link to={`/placements/${p.id}`}>{t("report.open_reports")}</Link>
                  {p.status === "active" && <>
                    <Button tone="ghost" className="min-h-0 px-0" onClick={() => { setDialog({ p, kind: "change" }); setSupervisor(""); setReason(""); }}>{t("placements.change_supervisor")}</Button>
                    <Button tone="ghost" className="min-h-0 px-0" onClick={() => { setDialog({ p, kind: "cancel" }); setReason(""); }}>{t("placements.cancel")}</Button>
                  </>}
                </div>
              </Td>
            </tr>
          ))}
        </Table>
      )}
      <Dialog open={!!dialog} title={dialog?.kind === "change" ? t("placements.change_supervisor") : t("placements.cancel")} onClose={() => setDialog(null)}>
        <div className="flex flex-col gap-3">
          {dialog?.kind === "change" && (
            <Select label={t("field.academic_supervisor")} value={supervisor} onChange={(e) => setSupervisor(e.target.value)} placeholder={t("common.choose")}
              options={supervisors.filter((s) => s.is_active && !s.invitation_pending && s.id !== dialog.p.academic_supervisor.id)
                .map((s) => ({ value: s.id, label: nameOf(s, i18n.language) }))} />
          )}
          <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
          <ErrorBox error={act.error} />
          <div className="flex gap-2">
            <Button tone={dialog?.kind === "cancel" ? "danger" : "primary"} busy={act.isPending}
              disabled={!reason.trim() || (dialog?.kind === "change" && !supervisor)} onClick={() => act.mutate()}>{t("common.save")}</Button>
            <Button tone="secondary" onClick={() => setDialog(null)}>{t("common.cancel")}</Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}

export default function Placements() {
  const { t } = useTranslation();
  const me = useMe();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"waiting" | "confirmed">("waiting");
  const supervisors = useCollegeSupervisors(me.organization.college_id ?? "");
  const candidates = useQuery({ queryKey: ["candidates"], queryFn: () => unwrap(api.GET("/api/v1/placements/candidates")) });
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["candidates"] });
    void queryClient.invalidateQueries({ queryKey: ["placements"] });
    void queryClient.invalidateQueries({ queryKey: ["supervisors"] });
  };
  return (
    <>
      <PageHeader title={t("menu.placements")} />
      <Tabs value={tab} onChange={setTab} items={[{ value: "waiting", label: t("placements.waiting", { n: candidates.data?.length ?? 0 }) },
        { value: "confirmed", label: t("placements.confirmed") }]} />
      {tab === "waiting" ? (
        candidates.isLoading ? <Loading /> : (
          <div className="flex flex-col gap-4">
            <ErrorBox error={candidates.error} />
            {(candidates.data ?? []).map((c) => <Candidate key={c.application_id} c={c} supervisors={supervisors.data ?? []} onDone={refresh} />)}
            {candidates.data?.length === 0 && <Empty>{t("placements.none_waiting")}</Empty>}
          </div>
        )
      ) : <Card><Confirmed supervisors={supervisors.data ?? []} /></Card>}
    </>
  );
}
