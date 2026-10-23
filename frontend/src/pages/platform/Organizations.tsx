/** Universities, colleges, and companies (wireframe `PA_Organizations`, FR-ORG-01, FR-ORG-04). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Dialog, Empty, ErrorBox, Input, Loading, PageHeader, Select, StatusChip, Table, Tabs, Td, TextArea } from "../../components/ui";
import { formatDate, nameOf } from "../../lib/format";

function UniversityForm({ uni, onDone }: { uni?: S<"UniversityOut">; onDone: () => void }) {
  const { t } = useTranslation();
  const [v, setV] = useState({ name_ar: uni?.name_ar ?? "", name_en: uni?.name_en ?? "", domains: uni?.email_domains.join(", ") ?? "",
    gpa_scale: uni ? String(uni.gpa_scale) : "5.00" });
  const body = () => ({ name_ar: v.name_ar, name_en: v.name_en, gpa_scale: v.gpa_scale,
    email_domains: v.domains.split(/[,\s]+/).map((d) => d.trim().toLowerCase()).filter(Boolean) });
  const save = useMutation({
    mutationFn: () => uni
      ? unwrap(api.PATCH("/api/v1/universities/{university_id}", { params: { path: { university_id: uni.id } }, body: body() as never }))
      : unwrap(api.POST("/api/v1/universities", { body: body() as never })),
    onSuccess: onDone,
  });
  return (
    <div className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label={t("field.name_ar")} value={v.name_ar} onChange={(e) => setV({ ...v, name_ar: e.target.value })} />
        <Input label={t("field.name_en")} dir="ltr" value={v.name_en} onChange={(e) => setV({ ...v, name_en: e.target.value })} />
        <Input label={t("orgs.email_domains")} dir="ltr" value={v.domains} onChange={(e) => setV({ ...v, domains: e.target.value })} hint={t("orgs.domains_hint")} />
        <Select label={t("orgs.gpa_scale")} value={v.gpa_scale} onChange={(e) => setV({ ...v, gpa_scale: e.target.value })}
          options={[{ value: "5.00", label: "5.00" }, { value: "4.00", label: "4.00" }]} />
      </div>
      <ErrorBox error={save.error} />
      <div><Button busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button></div>
    </div>
  );
}

function Universities() {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ["admin-universities"], queryFn: () => unwrap(api.GET("/api/v1/admin/universities")) });
  const [editing, setEditing] = useState<S<"UniversityOut"> | "new" | null>(null);
  const [college, setCollege] = useState<{ uni: string; name_ar: string; name_en: string } | null>(null);
  const refresh = () => {
    setEditing(null);
    setCollege(null);
    void queryClient.invalidateQueries({ queryKey: ["admin-universities"] });
    void queryClient.invalidateQueries({ queryKey: ["universities"] });
  };
  const toggleUni = useMutation({ mutationFn: (u: S<"UniversityOut">) => unwrap(api.PATCH("/api/v1/universities/{university_id}",
    { params: { path: { university_id: u.id } }, body: { is_active: !u.is_active } })), onSuccess: refresh });
  const toggleCollege = useMutation({ mutationFn: (c: S<"CollegeOut">) => unwrap(api.PATCH("/api/v1/colleges/{college_id}",
    { params: { path: { college_id: c.id } }, body: { is_active: !c.is_active } })), onSuccess: refresh });
  const addCollege = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/universities/{university_id}/colleges",
    { params: { path: { university_id: college?.uni ?? "" } }, body: { name_ar: college?.name_ar ?? "", name_en: college?.name_en ?? "" } })),
  onSuccess: refresh });
  if (list.isLoading) return <Loading />;
  return (
    <div className="flex flex-col gap-4">
      <div><Button onClick={() => setEditing("new")}>{t("orgs.new_university")}</Button></div>
      <ErrorBox error={list.error ?? toggleUni.error ?? toggleCollege.error} />
      {(list.data ?? []).map((u) => (
        <Card key={u.id} title={nameOf(u, i18n.language)}
          actions={<>
            <StatusChip status={u.is_active ? "active" : "inactive"} label={t(u.is_active ? "team.active" : "team.inactive")} />
            <Button tone="ghost" onClick={() => setEditing(u)}>{t("common.edit")}</Button>
            <Button tone="ghost" onClick={() => toggleUni.mutate(u)}>{t(u.is_active ? "team.deactivate" : "team.reactivate")}</Button>
          </>}>
          <p className="mb-3 text-sm text-ink-muted"><span dir="ltr">{u.email_domains.join(", ") || "—"}</span> · {t("orgs.gpa_scale")} {u.gpa_scale}</p>
          <Table head={[t("field.college"), t("report.status"), ""]}>
            {u.colleges.map((c) => (
              <tr key={c.id}>
                <Td>{nameOf(c, i18n.language)}</Td>
                <Td><StatusChip status={c.is_active ? "active" : "inactive"} label={t(c.is_active ? "team.active" : "team.inactive")} /></Td>
                <Td><Button tone="ghost" onClick={() => toggleCollege.mutate(c)}>{t(c.is_active ? "team.deactivate" : "team.reactivate")}</Button></Td>
              </tr>
            ))}
          </Table>
          <Button tone="secondary" className="mt-3" onClick={() => setCollege({ uni: u.id, name_ar: "", name_en: "" })}>{t("orgs.add_college")}</Button>
        </Card>
      ))}
      <Dialog open={!!editing} title={editing === "new" ? t("orgs.new_university") : t("common.edit")} onClose={() => setEditing(null)}>
        {editing && <UniversityForm uni={editing === "new" ? undefined : editing} onDone={refresh} />}
      </Dialog>
      <Dialog open={!!college} title={t("orgs.add_college")} onClose={() => setCollege(null)}>
        {college && (
          <div className="flex flex-col gap-3">
            <Input label={t("field.name_ar")} value={college.name_ar} onChange={(e) => setCollege({ ...college, name_ar: e.target.value })} />
            <Input label={t("field.name_en")} dir="ltr" value={college.name_en} onChange={(e) => setCollege({ ...college, name_en: e.target.value })} />
            <ErrorBox error={addCollege.error} />
            <div><Button busy={addCollege.isPending} onClick={() => addCollege.mutate()}>{t("common.save")}</Button></div>
          </div>
        )}
      </Dialog>
    </div>
  );
}

function Companies() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");
  const list = useQuery({ queryKey: ["companies", status], queryFn: () =>
    unwrap(api.GET("/api/v1/companies", { params: { query: { ...(status ? { status } : {}), page_size: 100 } } })) });
  const [suspending, setSuspending] = useState<S<"CompanyOut"> | null>(null);
  const [reason, setReason] = useState("");
  const refresh = () => {
    setSuspending(null);
    void queryClient.invalidateQueries({ queryKey: ["companies"] });
  };
  const suspend = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/companies/{company_id}/suspend",
    { params: { path: { company_id: suspending?.id ?? "" } }, body: { reason } })), onSuccess: refresh });
  const reactivate = useMutation({ mutationFn: (id: string) => unwrap(api.POST("/api/v1/companies/{company_id}/reactivate",
    { params: { path: { company_id: id } } })), onSuccess: refresh });
  return (
    <Card>
      <div className="mb-4 max-w-xs">
        <Select label={t("report.status")} value={status} onChange={(e) => setStatus(e.target.value)} placeholder={t("common.all")}
          options={["pending", "verified", "rejected", "suspended"].map((s) => ({ value: s, label: t(`status.${s}`) }))} />
      </div>
      <ErrorBox error={list.error ?? reactivate.error} />
      {list.isLoading ? <Loading /> : (list.data?.items ?? []).length === 0 ? <Empty /> : (
        <Table head={[t("field.company_name"), t("field.commercial_reg_no"), t("field.city"), t("team.company_admin"), t("orgs.verified_at"), t("report.status"), ""]}>
          {(list.data?.items ?? []).map((c) => (
            <tr key={c.id}>
              <Td className="font-semibold">{c.name}<p className="text-xs font-normal text-ink-muted">{t("orgs.supervisors_n", { n: c.supervisors })}</p></Td>
              <Td><span dir="ltr">{c.commercial_reg_no}</span></Td>
              <Td>{c.city}</Td>
              <Td>{c.admin ? <span dir="ltr">{c.admin.email}</span> : "—"}</Td>
              <Td>{formatDate(c.verified_at)}</Td>
              <Td><StatusChip status={c.status} /></Td>
              <Td>
                {c.status === "verified" && <Button tone="ghost" onClick={() => { setSuspending(c); setReason(""); }}>{t("orgs.suspend")}</Button>}
                {c.status === "suspended" && <Button tone="ghost" onClick={() => reactivate.mutate(c.id)}>{t("team.reactivate")}</Button>}
              </Td>
            </tr>
          ))}
        </Table>
      )}
      <Dialog open={!!suspending} title={t("orgs.suspend")} onClose={() => setSuspending(null)}>
        <TextArea label={t("common.reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
        <ErrorBox error={suspend.error} />
        <div className="mt-4 flex gap-2">
          <Button tone="danger" busy={suspend.isPending} disabled={!reason.trim()} onClick={() => suspend.mutate()}>{t("orgs.suspend")}</Button>
          <Button tone="secondary" onClick={() => setSuspending(null)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
  );
}

export default function Organizations() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"universities" | "companies">("universities");
  return (
    <>
      <PageHeader title={t("menu.organizations")} />
      <Tabs value={tab} onChange={setTab} items={[{ value: "universities", label: t("orgs.universities") }, { value: "companies", label: t("orgs.companies") }]} />
      {tab === "universities" ? <Universities /> : <Companies />}
    </>
  );
}
