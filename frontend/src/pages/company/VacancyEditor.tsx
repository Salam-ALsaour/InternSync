/** Create, edit, publish, and close a vacancy (wireframe `CS_VacancyEditor`, FR-VAC-01, FR-VAC-02). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, api, type S, unwrap } from "../../api/client";
import { Button, Card, Checkbox, ErrorBox, Input, Loading, Notice, PageHeader, Select, StatusChip, TextArea } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { fromRiyadhInput, nameOf, toRiyadhInput } from "../../lib/format";
import { useMajors } from "../public/Register";
import { SkillPicker } from "../student/Profile";

type Ref = { id: string; name_en: string; name_ar: string };
interface Form {
  title: string; city: string; description: string; training_type: "coop" | "summer"; training_start: string;
  training_end: string; min_gpa: string; seats: string; application_deadline: string; required: Ref[]; preferred: Ref[];
  major_ids: string[]; target_university_ids: string[]; company_supervisor_id: string;
}

const EMPTY: Form = { title: "", city: "", description: "", training_type: "coop", training_start: "", training_end: "",
  min_gpa: "", seats: "1", application_deadline: "", required: [], preferred: [], major_ids: [], target_university_ids: [],
  company_supervisor_id: "" };

function fromVacancy(v: S<"VacancyOut">): Form {
  return { title: v.title, city: v.city, description: v.description, training_type: v.training_type as Form["training_type"],
    training_start: v.training_start, training_end: v.training_end, min_gpa: v.min_gpa ?? "", seats: String(v.seats),
    application_deadline: toRiyadhInput(v.application_deadline), required: v.required_skills, preferred: v.preferred_skills,
    major_ids: v.majors.map((m) => m.id), target_university_ids: v.target_universities.map((u) => u.id),
    company_supervisor_id: v.company_supervisor.id };
}

function SkillList({ label, items, onChange, exclude }: { label: string; items: Ref[]; exclude: string[];
  onChange: (items: Ref[]) => void }) {
  const { i18n, t } = useTranslation();
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium">{label}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((s) => (
          <button key={s.id} type="button" title={t("common.remove")} onClick={() => onChange(items.filter((x) => x.id !== s.id))}
            className="min-h-[36px] rounded-full bg-[#E6EEFB] px-3 text-sm text-[#1F4E9A]">{nameOf(s, i18n.language)} ×</button>
        ))}
      </div>
      <SkillPicker exclude={exclude} onPick={(s) => onChange([...items, s])} />
    </div>
  );
}

export default function VacancyEditor() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const { vacancyId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Form>(EMPTY);
  const majors = useMajors();
  const universities = useQuery({ queryKey: ["universities"], queryFn: () => unwrap(api.GET("/api/v1/universities")) });
  const team = useQuery({
    queryKey: ["team", me.organization.company_id],
    queryFn: () => unwrap(api.GET("/api/v1/companies/{company_id}/supervisors",
      { params: { path: { company_id: me.organization.company_id ?? "" } } })),
    enabled: me.is_company_admin && !!vacancyId,
  });
  const existing = useQuery({
    queryKey: ["vacancy", vacancyId],
    queryFn: () => unwrap(api.GET("/api/v1/vacancies/{vacancy_id}", { params: { path: { vacancy_id: vacancyId ?? "" } } })),
    enabled: !!vacancyId,
  });
  useEffect(() => {
    if (existing.data) setForm(fromVacancy(existing.data));
  }, [existing.data]);

  const body = () => ({
    title: form.title, city: form.city, description: form.description, training_type: form.training_type,
    training_start: form.training_start, training_end: form.training_end, min_gpa: form.min_gpa || null,
    seats: Number(form.seats), application_deadline: form.application_deadline ? fromRiyadhInput(form.application_deadline) : "",
    required_skill_ids: form.required.map((s) => s.id), preferred_skill_ids: form.preferred.map((s) => s.id),
    major_ids: form.major_ids, target_university_ids: form.target_university_ids,
  });
  const done = (v: S<"VacancyOut">) => {
    void queryClient.invalidateQueries({ queryKey: ["company-vacancies"] });
    queryClient.setQueryData(["vacancy", v.id], v);
    if (!vacancyId) navigate(`/company/vacancies/${v.id}`, { replace: true });
  };
  const save = useMutation({
    mutationFn: (publish: boolean) => vacancyId
      ? unwrap(api.PATCH("/api/v1/vacancies/{vacancy_id}", { params: { path: { vacancy_id: vacancyId } },
        body: { ...body(), ...(me.is_company_admin && form.company_supervisor_id ? { company_supervisor_id: form.company_supervisor_id } : {}) } as never }))
        .then((v) => publish ? unwrap(api.POST("/api/v1/vacancies/{vacancy_id}/publish", { params: { path: { vacancy_id: v.id } } })) : v)
      : unwrap(api.POST("/api/v1/vacancies", { body: { ...body(), publish } as never })),
    onSuccess: done,
  });
  const close = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/vacancies/{vacancy_id}/close", { params: { path: { vacancy_id: vacancyId ?? "" } } })),
    onSuccess: done,
  });
  if (vacancyId && existing.isLoading) return <Loading />;
  const status = existing.data?.status ?? "draft";
  const err = save.error instanceof ApiError ? save.error : undefined;
  const fe = (f: string) => err?.fieldMessage(f);
  const set = (k: keyof Form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });
  const toggle = (k: "major_ids" | "target_university_ids", id: string) =>
    setForm({ ...form, [k]: form[k].includes(id) ? form[k].filter((x) => x !== id) : [...form[k], id] });
  const readOnly = status === "closed";
  return (
    <>
      <PageHeader title={vacancyId ? form.title || t("company.vacancy") : t("company.new_vacancy")}
        actions={<>{vacancyId && <StatusChip status={status} />}
          {vacancyId && status !== "draft" && <Link to={`/company/vacancies/${vacancyId}/applicants`}><Button tone="secondary">{t("company.applicants")}</Button></Link>}</>} />
      <ErrorBox error={existing.error} />
      {readOnly && <div className="mb-4"><Notice>{t("company.closed_note")}</Notice></div>}
      <fieldset disabled={readOnly} className="flex flex-col gap-4">
        <Card title={t("company.vacancy_basics")}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t("vacancy.title")} value={form.title} onChange={set("title")} error={fe("title")} />
            <Input label={t("field.city")} value={form.city} onChange={set("city")} error={fe("city")} />
            <Select label={t("vacancy.training_type")} value={form.training_type} onChange={set("training_type")}
              options={[{ value: "coop", label: t("training.coop") }, { value: "summer", label: t("training.summer") }]} />
            <Input label={t("vacancy.seats")} type="number" min={1} max={100} dir="ltr" value={form.seats} onChange={set("seats")} error={fe("seats")} />
            <Input label={t("vacancy.training_start")} type="date" value={form.training_start} onChange={set("training_start")} error={fe("training_start")} />
            <Input label={t("vacancy.training_end")} type="date" value={form.training_end} onChange={set("training_end")} error={fe("training_end")} />
            <Input label={t("vacancy.deadline")} type="datetime-local" value={form.application_deadline}
              onChange={set("application_deadline")} hint={t("common.riyadh_time")} error={fe("application_deadline")} />
            <Input label={t("vacancy.min_gpa")} dir="ltr" inputMode="decimal" value={form.min_gpa} onChange={set("min_gpa")}
              hint={t("company.min_gpa_hint")} error={fe("min_gpa")} />
          </div>
          <div className="mt-4">
            <TextArea label={t("vacancy.description")} value={form.description} rows={6} onChange={set("description")} error={fe("description")} />
          </div>
          {me.is_company_admin && vacancyId && (
            <div className="mt-4 max-w-sm">
              <Select label={t("field.company_supervisor")} value={form.company_supervisor_id} onChange={set("company_supervisor_id")}
                options={(team.data ?? []).filter((m) => !m.invitation_pending && m.is_active).map((m) => ({ value: m.id, label: nameOf(m, i18n.language) }))} />
            </div>
          )}
        </Card>
        <Card title={t("company.vacancy_skills")}>
          <div className="grid gap-6 md:grid-cols-2">
            <SkillList label={t("vacancy.required_skills")} items={form.required} exclude={[...form.required, ...form.preferred].map((s) => s.id)}
              onChange={(required) => setForm({ ...form, required })} />
            <SkillList label={t("vacancy.preferred_skills")} items={form.preferred} exclude={[...form.required, ...form.preferred].map((s) => s.id)}
              onChange={(preferred) => setForm({ ...form, preferred })} />
          </div>
        </Card>
        <Card title={t("company.vacancy_audience")}>
          <p className="mb-2 text-sm font-medium">{t("vacancy.majors")}</p>
          {fe("major_ids") && <p className="mb-2 text-xs text-[#A61B1B]">{fe("major_ids")}</p>}
          <div className="grid gap-x-4 sm:grid-cols-2 lg:grid-cols-3">
            {(majors.data ?? []).map((m) => (
              <Checkbox key={m.id} label={nameOf(m, i18n.language)} checked={form.major_ids.includes(m.id ?? "")}
                onChange={() => toggle("major_ids", m.id ?? "")} />
            ))}
          </div>
          <p className="mb-2 mt-4 text-sm font-medium">{t("vacancy.universities")}</p>
          <p className="mb-2 text-xs text-ink-muted">{t("company.universities_hint")}</p>
          <div className="grid gap-x-4 sm:grid-cols-2">
            {(universities.data ?? []).map((u) => (
              <Checkbox key={u.id} label={nameOf(u, i18n.language)} checked={form.target_university_ids.includes(u.id)}
                onChange={() => toggle("target_university_ids", u.id)} />
            ))}
          </div>
        </Card>
      </fieldset>
      <div className="mt-4 flex flex-col gap-3">
        <ErrorBox error={save.error ?? close.error} />
        {save.isSuccess && <Notice tone="success">{t("common.saved")}</Notice>}
        <div className="flex flex-wrap gap-2">
          {status !== "closed" && <Button tone="secondary" busy={save.isPending && save.variables === false} onClick={() => save.mutate(false)}>
            {status === "draft" ? t("company.save_draft") : t("common.save")}</Button>}
          {status === "draft" && <Button busy={save.isPending && save.variables === true} onClick={() => save.mutate(true)}>{t("company.publish")}</Button>}
          {status === "published" && <Button tone="danger" busy={close.isPending} onClick={() => close.mutate()}>{t("company.close_vacancy")}</Button>}
        </div>
      </div>
    </>
  );
}
