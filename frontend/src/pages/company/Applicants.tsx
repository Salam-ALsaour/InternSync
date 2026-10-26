/** Applicants of one vacancy with accept and decline (wireframe `CS_Applicants`, FR-VAC-06). The ranked view with
 *  fit scores comes in Increment 2. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api, openFile, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Loading, PageHeader, StatusChip } from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";

export default function Applicants() {
  const { t, i18n } = useTranslation();
  const { vacancyId = "" } = useParams();
  const queryClient = useQueryClient();
  const [error, setError] = useState<unknown>(null);
  const vacancy = useQuery({ queryKey: ["vacancy", vacancyId], queryFn: () =>
    unwrap(api.GET("/api/v1/vacancies/{vacancy_id}", { params: { path: { vacancy_id: vacancyId } } })) });
  const key = ["applicants", vacancyId];
  const list = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/vacancies/{vacancy_id}/applications", { params: { path: { vacancy_id: vacancyId } } })) });
  const decide = useMutation({
    mutationFn: ({ id, accept }: { id: string; accept: boolean }) => unwrap(accept
      ? api.POST("/api/v1/applications/{application_id}/accept", { params: { path: { application_id: id } } })
      : api.POST("/api/v1/applications/{application_id}/decline", { params: { path: { application_id: id } } })),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: key }),
  });
  if (list.isLoading) return <Loading />;
  const rows = list.data ?? [];
  const lang = i18n.language;
  return (
    <>
      <PageHeader title={t("company.applicants")} subtitle={vacancy.data?.title}
        actions={<Link to={`/company/vacancies/${vacancyId}`}>{t("company.back_to_vacancy")}</Link>} />
      <ErrorBox error={list.error ?? decide.error ?? error} />
      {rows.length === 0 ? <Empty>{t("company.no_applicants")}</Empty> : (
        <div className="flex flex-col gap-4">
          {rows.map((a) => (
            <Card key={a.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold">{lang === "en" ? a.student_name_en : a.student_name_ar}</h2>
                  <p className="text-sm text-ink-muted">
                    {lang === "en" ? a.major_en : a.major_ar} · {lang === "en" ? a.university_en : a.university_ar} · {t("field.gpa")} {a.gpa}
                  </p>
                  <p className="text-xs text-ink-muted">{t("applications.applied_at")}: <span dir="ltr">{formatDateTime(a.created_at)}</span></p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <StatusChip status={a.status} />
                  {a.fit_score !== null && a.fit_score !== undefined && (
                    <span className="text-xs text-advisory-fg">{t(a.match_mode === "basic" ? "company.fit_basic" : "company.fit")}: <b dir="ltr">{Math.round(Number(a.fit_score))}%</b></span>
                  )}
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {a.skills.map((s) => <span key={s.id} className="rounded-full bg-ground px-3 py-1 text-xs">{nameOf(s, lang)}</span>)}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {a.cv_file_id && <Button tone="secondary" onClick={() => openFile(a.cv_file_id as string).catch(setError)}>{t("company.view_cv")}</Button>}
                {a.status === "submitted" && (
                  <>
                    <Button busy={decide.isPending && decide.variables?.id === a.id && decide.variables.accept}
                      onClick={() => decide.mutate({ id: a.id, accept: true })}>{t("company.accept")}</Button>
                    <Button tone="danger" busy={decide.isPending && decide.variables?.id === a.id && !decide.variables.accept}
                      onClick={() => decide.mutate({ id: a.id, accept: false })}>{t("company.decline")}</Button>
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
