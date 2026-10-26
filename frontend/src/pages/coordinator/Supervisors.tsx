/** Academic supervisors of the college: list, invite, resend, deactivate (wireframe `CO_Supervisors`, FR-ORG-06). */
import { type QueryKey, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Loading, PageHeader, StatusChip, Table, Td } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { nameOf } from "../../lib/format";
import { InviteForm } from "../company/Team";

/** Members of a college or a company with their account actions (shared with the Company Admin's team page). */
export function MemberTable({ rows, queryKey, selfId }: { rows: S<"MemberOut">[]; queryKey: QueryKey; selfId: string }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const action = useMutation({
    mutationFn: ({ id, kind }: { id: string; kind: "deactivate" | "reactivate" | "resend" }) => {
      const path = { params: { path: { user_id: id } } };
      if (kind === "resend") return unwrap(api.POST("/api/v1/users/{user_id}/invitation/resend", path));
      if (kind === "deactivate") return unwrap(api.POST("/api/v1/users/{user_id}/deactivate", path));
      return unwrap(api.POST("/api/v1/users/{user_id}/reactivate", path));
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey }),
  });
  if (rows.length === 0) return <Empty />;
  return (
    <>
      <ErrorBox error={action.error} />
      <Table head={[t("field.name"), t("field.email"), t("team.students"), t("report.status"), ""]}>
        {rows.map((m) => (
          <tr key={m.id}>
            <Td className="font-semibold">{nameOf(m, i18n.language)}{m.is_company_admin && <p className="text-xs font-normal text-ink-muted">{t("team.company_admin")}</p>}</Td>
            <Td><span dir="ltr">{m.email}</span></Td>
            <Td>{m.active_students}</Td>
            <Td>{m.invitation_pending ? <StatusChip status="pending" label={t("team.invitation_pending")} />
              : <StatusChip status={m.is_active ? "active" : "inactive"} label={t(m.is_active ? "team.active" : "team.inactive")} />}</Td>
            <Td>
              {m.id !== selfId && (
                <div className="flex flex-wrap gap-2">
                  {m.invitation_pending && <Button tone="ghost" onClick={() => action.mutate({ id: m.id, kind: "resend" })}>{t("team.resend")}</Button>}
                  {m.is_active
                    ? <Button tone="ghost" onClick={() => action.mutate({ id: m.id, kind: "deactivate" })}>{t("team.deactivate")}</Button>
                    : <Button tone="ghost" onClick={() => action.mutate({ id: m.id, kind: "reactivate" })}>{t("team.reactivate")}</Button>}
                </div>
              )}
            </Td>
          </tr>
        ))}
      </Table>
    </>
  );
}

export function useCollegeSupervisors(collegeId: string) {
  return useQuery({ queryKey: ["supervisors", collegeId], queryFn: () =>
    unwrap(api.GET("/api/v1/colleges/{college_id}/academic-supervisors", { params: { path: { college_id: collegeId } } })) });
}

export default function Supervisors() {
  const { t } = useTranslation();
  const me = useMe();
  const collegeId = me.organization.college_id ?? "";
  const queryClient = useQueryClient();
  const list = useCollegeSupervisors(collegeId);
  const invite = useMutation({
    mutationFn: (body: { email: string; name_en: string; name_ar: string }) =>
      unwrap(api.POST("/api/v1/colleges/{college_id}/invitations", { params: { path: { college_id: collegeId } }, body })),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["supervisors", collegeId] }),
  });
  if (list.isLoading) return <Loading />;
  return (
    <>
      <PageHeader title={t("menu.supervisors")} />
      <div className="flex flex-col gap-4">
        <Card title={t("supervisors.list")}>
          <ErrorBox error={list.error} />
          <MemberTable rows={list.data ?? []} queryKey={["supervisors", collegeId]} selfId={me.id} />
        </Card>
        <Card title={t("supervisors.invite")}>
          <InviteForm onInvite={(b) => invite.mutate(b)} busy={invite.isPending} error={invite.error} done={invite.isSuccess} />
        </Card>
      </div>
    </>
  );
}
