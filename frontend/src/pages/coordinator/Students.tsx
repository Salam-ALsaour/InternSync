/** Students: verification requests with approve-and-enrol or reject, and the students of each cycle (wireframe
 *  `CO_Students`, FR-ORG-05, FR-AUT-06). The Platform Admin's verification page uses the same request view. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, openFile, type S, unwrap } from "../../api/client";
import {
  Button, Card, Chip, DefList, Dialog, Empty, ErrorBox, Loading, Notice, PageHeader, Select, StatusChip, Table, Tabs, Td,
  TextArea,
} from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";

type Request = S<"VerificationRequestOut">;

function dataRows(r: Request, t: (k: string) => string, lang: string): [string, string][] {
  const d = r.submitted_data as Record<string, string | number | null>;
  if (r.kind === "student") {
    return [[t("field.student_number"), String(d.student_number ?? "—")],
      [t("field.major"), String((lang === "en" ? d.major_en : d.major_ar) ?? "—")],
      [t("field.gpa"), String(d.gpa ?? "—")], [t("field.level"), String(d.level ?? "—")]];
  }
  if (r.kind === "company" && r.company) {
    const c = r.company as Record<string, string | null>;
    return [[t("field.company_name"), c.name ?? ""], [t("field.commercial_reg_no"), c.commercial_reg_no ?? ""],
      [t("field.city"), c.city ?? ""], [t("field.website"), c.website ?? "—"]];
  }
  return [[t("field.college"), r.college ? nameOf(r.college, lang) : "—"],
    [t("field.university"), (lang === "en" ? r.university_en : r.university_ar) ?? "—"]];
}

/** One verification request with its documents, earlier decisions, and the decision buttons. */
export function RequestCard({ r, cycles, queryKey }: { r: Request; cycles?: S<"CycleOut">[]; queryKey: unknown[] }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [cycleId, setCycleId] = useState(cycles?.find((c) => c.status === "open")?.id ?? "");
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [fileError, setFileError] = useState<unknown>(null);
  const path = { params: { path: { request_id: r.id } } };
  const refresh = () => {
    setRejecting(false);
    void queryClient.invalidateQueries({ queryKey });
  };
  const approve = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/verification-requests/{request_id}/approve",
    { ...path, body: { cycle_id: cycleId || null } })), onSuccess: refresh });
  const reject = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/verification-requests/{request_id}/reject",
    { ...path, body: { reason } })), onSuccess: refresh });
  const a = r.applicant;
  const openCycles = (cycles ?? []).filter((c) => c.status === "open");
  return (
    <Card title={nameOf(a, i18n.language)} actions={<StatusChip status={r.status} />}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap gap-2 text-sm">
          <span dir="ltr">{a.email}</span>
          <Chip tone={a.email_confirmed ? "success" : "warning"}>{t(a.email_confirmed ? "requests.email_confirmed" : "requests.email_not_confirmed")}</Chip>
          {a.email_matches_university_domain === false && <Chip tone="warning">{t("requests.domain_mismatch")}</Chip>}
          {a.email_matches_university_domain === true && <Chip tone="success">{t("requests.domain_match")}</Chip>}
        </div>
        <DefList items={[[t("requests.submitted_at"), formatDateTime(r.submitted_at)], ...dataRows(r, t, i18n.language)]} />
        <div>
          <p className="mb-1 text-xs text-ink-muted">{t("verification.documents")}</p>
          <div className="flex flex-wrap gap-2">
            {r.documents.map((d) => d.purged || !d.file_id
              ? <Chip key={d.kind}>{t(`document.${d.kind}`)} ({t("verification.purged")})</Chip>
              : <Button key={d.kind} tone="secondary" onClick={() => openFile(d.file_id as string).catch(setFileError)}>{t(`document.${d.kind}`)}</Button>)}
          </div>
          <ErrorBox error={fileError} />
        </div>
        {r.earlier_decisions.length > 0 && (
          <Notice tone="warning">
            {t("requests.earlier")}: {r.earlier_decisions.map((e) => `${t(`status.${e.status}`)} — ${e.reason ?? ""} (${formatDateTime(e.decided_at)})`).join(" · ")}
          </Notice>
        )}
        {r.reason && <Notice>{t("verification.reason")}: {r.reason}</Notice>}
        {r.status === "pending" && (
          <>
            {r.kind === "student" && r.no_open_cycle && <Notice tone="warning">{t("requests.no_open_cycle")}</Notice>}
            {r.kind === "student" && openCycles.length > 0 && (
              <div className="max-w-sm">
                <Select label={t("requests.enrol_in")} value={cycleId} onChange={(e) => setCycleId(e.target.value)}
                  options={openCycles.map((c) => ({ value: c.id, label: `${c.name} (${t(`training.${c.type}`)})` }))} />
              </div>
            )}
            <ErrorBox error={approve.error} />
            <div className="flex flex-wrap gap-2">
              <Button busy={approve.isPending} disabled={r.kind === "student" && !cycleId} onClick={() => approve.mutate()}>
                {t(r.kind === "student" ? "requests.approve_enrol" : "requests.approve")}</Button>
              <Button tone="danger" onClick={() => setRejecting(true)}>{t("requests.reject")}</Button>
            </div>
          </>
        )}
      </div>
      <Dialog open={rejecting} title={t("requests.reject")} onClose={() => setRejecting(false)}>
        <TextArea label={t("requests.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
        <ErrorBox error={reject.error} />
        <div className="mt-4 flex gap-2">
          <Button tone="danger" busy={reject.isPending} disabled={!reason.trim()} onClick={() => reject.mutate()}>{t("requests.reject")}</Button>
          <Button tone="secondary" onClick={() => setRejecting(false)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}

export function RequestList({ cycles }: { cycles?: S<"CycleOut">[] }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">("pending");
  const key = ["requests", status];
  const list = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/verification-requests", { params: { query: { status, page_size: 50 } } })) });
  return (
    <>
      <Tabs value={status} onChange={setStatus} items={[{ value: "pending", label: t("status.pending") },
        { value: "approved", label: t("status.approved") }, { value: "rejected", label: t("status.rejected") }]} />
      {list.isLoading && <Loading />}
      <ErrorBox error={list.error} />
      <div className="flex flex-col gap-4">
        {(list.data?.items ?? []).map((r) => <RequestCard key={r.id} r={r} cycles={cycles} queryKey={["requests"]} />)}
        {list.data?.items.length === 0 && <Empty>{t("requests.none")}</Empty>}
      </div>
    </>
  );
}

function Enrolled({ cycles }: { cycles: S<"CycleOut">[] }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [cycleId, setCycleId] = useState(cycles[0]?.id ?? "");
  const rows = useQuery({ queryKey: ["enrollments", cycleId], enabled: !!cycleId, queryFn: () =>
    unwrap(api.GET("/api/v1/cycles/{cycle_id}/enrollments", { params: { path: { cycle_id: cycleId } } })) });
  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => unwrap(active
      ? api.POST("/api/v1/users/{user_id}/deactivate", { params: { path: { user_id: id } } })
      : api.POST("/api/v1/users/{user_id}/reactivate", { params: { path: { user_id: id } } })),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["enrollments", cycleId] }),
  });
  if (cycles.length === 0) return <Empty>{t("cycles.none")}</Empty>;
  return (
    <>
      <div className="mb-4 max-w-sm">
        <Select label={t("field.cycle")} value={cycleId} onChange={(e) => setCycleId(e.target.value)}
          options={cycles.map((c) => ({ value: c.id, label: c.name }))} />
      </div>
      <ErrorBox error={rows.error ?? toggle.error} />
      {rows.isLoading ? <Loading /> : (rows.data ?? []).length === 0 ? <Empty /> : (
        <Table head={[t("field.name"), t("field.student_number"), t("field.major"), t("field.gpa"), t("students.placement"), ""]}>
          {(rows.data ?? []).map((s) => (
            <tr key={s.student_id}>
              <Td className="font-semibold">{nameOf(s, i18n.language)}<p className="text-xs font-normal text-ink-muted" dir="ltr">{s.email}</p></Td>
              <Td>{s.student_number}</Td>
              <Td>{i18n.language === "en" ? s.major_en : s.major_ar}</Td>
              <Td>{s.gpa}</Td>
              <Td>{s.placed ? <StatusChip status="placed" /> : <StatusChip status="pending" label={t("students.not_placed")} />}
                {!s.is_active && <div className="mt-1"><StatusChip status="inactive" label={t("team.inactive")} /></div>}</Td>
              <Td><Button tone="ghost" onClick={() => toggle.mutate({ id: s.student_id, active: s.is_active })}>
                {t(s.is_active ? "team.deactivate" : "team.reactivate")}</Button></Td>
            </tr>
          ))}
        </Table>
      )}
    </>
  );
}

export function useCycles() {
  return useQuery({ queryKey: ["cycles"], queryFn: () => unwrap(api.GET("/api/v1/cycles")) });
}

export default function CoordinatorStudents() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"requests" | "enrolled">("requests");
  const cycles = useCycles();
  return (
    <>
      <PageHeader title={t("menu.students")} />
      <Tabs value={tab} onChange={setTab} items={[{ value: "requests", label: t("students.requests") },
        { value: "enrolled", label: t("students.enrolled") }]} />
      {cycles.isLoading ? <Loading /> : tab === "requests" ? <RequestList cycles={cycles.data} /> : <Enrolled cycles={cycles.data ?? []} />}
    </>
  );
}
