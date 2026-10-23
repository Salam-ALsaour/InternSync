/** The Company Admin's team: company details, supervisors, invitations, deactivation (wireframe `CS_Team`,
 *  FR-ORG-04, FR-AUT-06). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Button, Card, ErrorBox, Input, Loading, Notice, PageHeader } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { MemberTable } from "../coordinator/Supervisors";

export function InviteForm({ onInvite, busy, error, done }: { onInvite: (b: { email: string; name_en: string; name_ar: string }) => void;
  busy: boolean; error: unknown; done: boolean }) {
  const { t } = useTranslation();
  const [v, setV] = useState({ email: "", name_en: "", name_ar: "" });
  useEffect(() => {
    if (done) setV({ email: "", name_en: "", name_ar: "" });
  }, [done]);
  return (
    <div className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <Input label={t("field.name_ar")} value={v.name_ar} onChange={(e) => setV({ ...v, name_ar: e.target.value })} />
        <Input label={t("field.name_en")} dir="ltr" value={v.name_en} onChange={(e) => setV({ ...v, name_en: e.target.value })} />
        <Input label={t("field.email")} type="email" dir="ltr" value={v.email} onChange={(e) => setV({ ...v, email: e.target.value })} />
      </div>
      <ErrorBox error={error} />
      {done && <Notice tone="success">{t("team.invited")}</Notice>}
      <div><Button busy={busy} onClick={() => onInvite(v)}>{t("team.send_invitation")}</Button></div>
    </div>
  );
}

export default function CompanyTeam() {
  const { t } = useTranslation();
  const me = useMe();
  const companyId = me.organization.company_id ?? "";
  const queryClient = useQueryClient();
  const path = { params: { path: { company_id: companyId } } };
  const company = useQuery({ queryKey: ["company", companyId], queryFn: () => unwrap(api.GET("/api/v1/companies/{company_id}", path)) });
  const team = useQuery({ queryKey: ["team", companyId], queryFn: () => unwrap(api.GET("/api/v1/companies/{company_id}/supervisors", path)) });
  const [info, setInfo] = useState({ city: "", website: "" });
  useEffect(() => {
    if (company.data) setInfo({ city: company.data.city, website: company.data.website ?? "" });
  }, [company.data]);
  const saveInfo = useMutation({
    mutationFn: () => unwrap(api.PATCH("/api/v1/companies/{company_id}", { ...path, body: { city: info.city, website: info.website || null } })),
    onSuccess: (c) => queryClient.setQueryData(["company", companyId], c),
  });
  const invite = useMutation({
    mutationFn: (body: { email: string; name_en: string; name_ar: string }) =>
      unwrap(api.POST("/api/v1/companies/{company_id}/invitations", { ...path, body })),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["team", companyId] }),
  });
  if (!me.is_company_admin) return <Notice tone="warning">{t("team.admin_only")}</Notice>;
  if (company.isLoading || team.isLoading) return <Loading />;
  return (
    <>
      <PageHeader title={t("menu.team")} subtitle={company.data?.name} />
      <div className="flex flex-col gap-4">
        <Card title={t("team.company")}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t("field.commercial_reg_no")} value={company.data?.commercial_reg_no ?? ""} disabled dir="ltr" />
            <Input label={t("field.city")} value={info.city} onChange={(e) => setInfo({ ...info, city: e.target.value })} />
            <Input label={t("field.website")} dir="ltr" value={info.website} onChange={(e) => setInfo({ ...info, website: e.target.value })} />
          </div>
          <ErrorBox error={saveInfo.error} />
          <Button className="mt-4" busy={saveInfo.isPending} onClick={() => saveInfo.mutate()}>{t("common.save")}</Button>
        </Card>
        <Card title={t("team.members")}>
          <MemberTable rows={team.data ?? []} queryKey={["team", companyId]} selfId={me.id} />
        </Card>
        <Card title={t("team.invite")}>
          <InviteForm onInvite={(b) => invite.mutate(b)} busy={invite.isPending} error={invite.error} done={invite.isSuccess} />
        </Card>
      </div>
    </>
  );
}
