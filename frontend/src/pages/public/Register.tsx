/** Registration for students, coordinators, and companies with the verification documents (wireframe `Register`,
 *  FR-AUT-02, FR-ORG-03 – 05). */
import { useMutation, useQuery } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ApiError, api, type S, sendForm, unwrap } from "../../api/client";
import { Button, Card, ErrorBox, Input, Notice, Select, Tabs } from "../../components/ui";
import { nameOf } from "../../lib/format";

type Kind = "student" | "coordinator" | "company";

export const DOCUMENTS: Record<Kind, string[]> = {
  student: ["course_registration"],
  coordinator: ["appointment_letter"],
  company: ["commercial_registration", "authorization_letter"],
};

export function useColleges() {
  const { i18n } = useTranslation();
  const universities = useQuery({ queryKey: ["universities"], queryFn: () => unwrap(api.GET("/api/v1/universities")) });
  const options = (universities.data ?? []).flatMap((u) =>
    u.colleges.map((c) => ({ value: c.id, label: `${nameOf(c, i18n.language)} — ${nameOf(u, i18n.language)}` })));
  return { universities, options };
}

export function useMajors() {
  return useQuery({ queryKey: ["majors"], queryFn: () => unwrap(api.GET("/api/v1/majors")) });
}

export default function Register() {
  const { t, i18n } = useTranslation();
  const [kind, setKind] = useState<Kind>("student");
  const [values, setValues] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const colleges = useColleges();
  const majors = useMajors();
  const set = (k: string) => (e: { target: { value: string } }) => setValues((v) => ({ ...v, [k]: e.target.value }));

  const action = useMutation({
    mutationFn: () => {
      const form = new FormData();
      form.set("kind", kind);
      for (const [k, v] of Object.entries(values)) if (v.trim()) form.set(k, v.trim());
      for (const doc of DOCUMENTS[kind]) {
        const file = files[doc];
        if (file) form.set(doc, file);
      }
      return sendForm<S<"RegisterOut">>("POST", "/api/v1/auth/register", form);
    },
  });
  const err = action.error instanceof ApiError ? action.error : undefined;
  const fieldError = (f: string) => err?.fieldMessage(f);

  if (action.isSuccess) {
    return (
      <Card title={t("register.done_title")}>
        <Notice tone="success">{t("register.done_text", { email: values.email })}</Notice>
        <p className="mt-4 text-sm text-ink-muted">
          {t(action.data.verification.reviewer === "coordinator" ? "register.reviewer_coordinator" : "register.reviewer_platform")}
        </p>
        <Link to="/login" className="mt-4 inline-block font-semibold">{t("register.to_login")}</Link>
      </Card>
    );
  }

  const submit = (e: FormEvent) => {
    e.preventDefault();
    action.mutate();
  };

  return (
    <Card title={t("register.title")}>
      <Tabs value={kind} onChange={(k) => { setKind(k); action.reset(); }}
        items={[{ value: "student", label: t("register.kind_student") },
          { value: "coordinator", label: t("register.kind_coordinator") },
          { value: "company", label: t("register.kind_company") }]} />
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <ErrorBox error={action.error} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label={t("field.name_ar")} value={values.name_ar ?? ""} onChange={set("name_ar")} required
            error={fieldError("name_ar")} />
          <Input label={t("field.name_en")} value={values.name_en ?? ""} onChange={set("name_en")} required dir="ltr"
            error={fieldError("name_en")} />
        </div>
        <Input label={kind === "company" ? t("field.work_email") : t("field.university_email")} type="email" dir="ltr"
          value={values.email ?? ""} onChange={set("email")} required error={fieldError("email")} />
        <Input label={t("field.password")} type="password" dir="ltr" value={values.password ?? ""}
          onChange={set("password")} required hint={t("register.password_hint")} error={fieldError("password")} />
        {kind !== "company" && (
          <Select label={t("field.college")} value={values.college_id ?? ""} onChange={set("college_id")}
            options={colleges.options} placeholder={t("common.choose")} error={fieldError("college_id")} />
        )}
        {kind === "student" && (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t("field.student_number")} dir="ltr" value={values.student_number ?? ""}
              onChange={set("student_number")} error={fieldError("student_number")} />
            <Select label={t("field.major")} value={values.major_id ?? ""} onChange={set("major_id")}
              options={(majors.data ?? []).map((m) => ({ value: m.id ?? "", label: nameOf(m, i18n.language) }))}
              placeholder={t("common.choose")} error={fieldError("major_id")} />
            <Input label={t("field.gpa")} inputMode="decimal" dir="ltr" value={values.gpa ?? ""} onChange={set("gpa")}
              error={fieldError("gpa")} />
            <Input label={t("field.level")} inputMode="numeric" dir="ltr" value={values.level ?? ""}
              onChange={set("level")} error={fieldError("level")} />
          </div>
        )}
        {kind === "company" && (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t("field.company_name")} value={values.company_name ?? ""} onChange={set("company_name")}
              error={fieldError("company_name")} />
            <Input label={t("field.commercial_reg_no")} dir="ltr" value={values.commercial_reg_no ?? ""}
              onChange={set("commercial_reg_no")} error={fieldError("commercial_reg_no")} />
            <Input label={t("field.city")} value={values.city ?? ""} onChange={set("city")} error={fieldError("city")} />
            <Input label={t("field.website")} dir="ltr" value={values.website ?? ""} onChange={set("website")} />
          </div>
        )}
        {DOCUMENTS[kind].map((doc) => (
          <Input key={doc} label={t(`document.${doc}`)} type="file" accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => setFiles((f) => ({ ...f, [doc]: e.target.files?.[0] ?? null }))}
            hint={t("register.document_hint")} error={fieldError(doc)} />
        ))}
        <Button type="submit" busy={action.isPending} className="min-h-[48px]">{t("register.submit")}</Button>
        <Link to="/login" className="text-sm">{t("register.have_account")}</Link>
      </form>
    </Card>
  );
}
