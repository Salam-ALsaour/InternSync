/** Profile and CV with skill confirmation (wireframe `ST_Profile`, FR-PRF-02 – 05). Extracted skills are only
 *  suggestions in an Advisory panel; the student confirms what is saved. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, openFile, type S, sendForm, unwrap } from "../../api/client";
import {
  Advisory, Button, Card, Checkbox, Chip, DefList, ErrorBox, Input, Loading, Notice, PageHeader, Select, Table, Td,
} from "../../components/ui";
import { formatDateTime, nameOf } from "../../lib/format";
import { useMajors } from "../public/Register";

type Choice = { id: string; name_en: string; name_ar: string; source: "extracted" | "manual" };

export function SkillPicker({ onPick, exclude }: { onPick: (s: S<"SkillOut">) => void; exclude: string[] }) {
  const { t, i18n } = useTranslation();
  const [q, setQ] = useState("");
  const found = useQuery({
    queryKey: ["skills", q],
    queryFn: () => unwrap(api.GET("/api/v1/skills", { params: { query: { q, page_size: 10 } } })),
    enabled: q.trim().length >= 2,
  });
  return (
    <div className="flex flex-col gap-2">
      <Input label={t("profile.add_skill")} value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("profile.search_skill")} />
      {q.trim().length >= 2 && (
        <div className="flex flex-wrap gap-2">
          {(found.data?.items ?? []).filter((s) => !exclude.includes(s.id)).map((s) => (
            <button key={s.id} type="button" onClick={() => { onPick(s); setQ(""); }}
              className="min-h-[36px] rounded-full border border-line bg-white px-3 text-sm hover:bg-ground">
              + {nameOf(s, i18n.language)}
            </button>
          ))}
          {found.data?.items.length === 0 && <span className="text-sm text-ink-muted">{t("common.no_results")}</span>}
        </div>
      )}
    </div>
  );
}

function AcademicCard({ profile }: { profile: S<"ProfileOut"> }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const majors = useMajors();
  const [values, setValues] = useState({ student_number: profile.student_number, major_id: profile.major.id,
    gpa: String(profile.gpa), level: profile.level ? String(profile.level) : "" });
  const save = useMutation({
    mutationFn: () => unwrap(api.PATCH("/api/v1/students/me/profile", { body: {
      level: values.level ? Number(values.level) : null,
      ...(profile.academic_read_only ? {} : { student_number: values.student_number, major_id: values.major_id,
        gpa: values.gpa }),
    } })),
    onSuccess: (p) => queryClient.setQueryData(["profile"], p),
  });
  if (profile.academic_read_only) {
    return (
      <Card title={t("profile.academic")}>
        <DefList items={[
          [t("field.university"), i18n.language === "en" ? profile.university_en : profile.university_ar],
          [t("field.college"), i18n.language === "en" ? profile.college_en : profile.college_ar],
          [t("field.student_number"), profile.student_number],
          [t("field.major"), nameOf(profile.major, i18n.language)],
          [t("field.gpa"), <span dir="ltr">{profile.gpa} / {profile.gpa_scale}</span>],
          [t("field.level"), profile.level ?? "—"],
          [t("field.cycle"), profile.enrolled_cycle_name ?? "—"],
        ]} />
        <p className="mt-3 text-xs text-ink-muted">{t("profile.read_only_note")}</p>
      </Card>
    );
  }
  return (
    <Card title={t("profile.academic")}>
      <Notice tone="warning">{t("profile.pending_note")}</Notice>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Input label={t("field.student_number")} dir="ltr" value={values.student_number}
          onChange={(e) => setValues({ ...values, student_number: e.target.value })} />
        <Select label={t("field.major")} value={values.major_id} onChange={(e) => setValues({ ...values, major_id: e.target.value })}
          options={(majors.data ?? []).map((m) => ({ value: m.id ?? "", label: nameOf(m, i18n.language) }))} />
        <Input label={t("field.gpa")} dir="ltr" value={values.gpa} onChange={(e) => setValues({ ...values, gpa: e.target.value })}
          hint={`/ ${profile.gpa_scale}`} />
        <Input label={t("field.level")} dir="ltr" value={values.level} onChange={(e) => setValues({ ...values, level: e.target.value })} />
      </div>
      <ErrorBox error={save.error} />
      <Button className="mt-4" busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button>
    </Card>
  );
}

function InterestsCard({ profile }: { profile: S<"ProfileOut"> }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [languages, setLanguages] = useState(profile.languages.join(", "));
  const [interests, setInterests] = useState(profile.interests.join(", "));
  const split = (s: string) => s.split(/[,،]/).map((x) => x.trim()).filter(Boolean);
  const save = useMutation({
    mutationFn: () => unwrap(api.PATCH("/api/v1/students/me/profile", { body: { languages: split(languages),
      interests: split(interests) } })),
    onSuccess: (p) => queryClient.setQueryData(["profile"], p),
  });
  return (
    <Card title={t("profile.preferences")}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label={t("field.languages")} value={languages} onChange={(e) => setLanguages(e.target.value)} hint={t("profile.comma_hint")} />
        <Input label={t("field.interests")} value={interests} onChange={(e) => setInterests(e.target.value)} hint={t("profile.comma_hint")} />
      </div>
      <ErrorBox error={save.error} />
      {save.isSuccess && <div className="mt-3"><Notice tone="success">{t("common.saved")}</Notice></div>}
      <Button className="mt-4" busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button>
    </Card>
  );
}

function SkillsCard({ profile }: { profile: S<"ProfileOut"> }) {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [chosen, setChosen] = useState<Choice[]>([]);
  const [candidates, setCandidates] = useState<S<"ExtractedSkill">[] | null>(null);
  const [upload, setUpload] = useState<S<"CvUploadOut"> | null>(null);
  useEffect(() => {
    setChosen(profile.skills.map((s) => ({ id: s.id, name_en: s.name_en, name_ar: s.name_ar,
      source: s.source as Choice["source"] })));
  }, [profile.skills]);
  const cvs = useQuery({ queryKey: ["cvs"], queryFn: () => unwrap(api.GET("/api/v1/students/me/cvs")) });
  const send = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.set("file", file);
      return sendForm<S<"CvUploadOut">>("POST", "/api/v1/students/me/cvs", form);
    },
    onSuccess: (out) => {
      setUpload(out);
      setCandidates(out.extracted_skills);
      setChosen((current) => [...current, ...out.extracted_skills.filter((s) => !current.some((c) => c.id === s.id))
        .map((s) => ({ id: s.id, name_en: s.name_en, name_ar: s.name_ar, source: "extracted" as const }))]);
      void queryClient.invalidateQueries({ queryKey: ["cvs"] });
    },
  });
  const confirm = useMutation({
    mutationFn: () => unwrap(api.PUT("/api/v1/students/me/skills", { body: { skills: chosen.map((c) => ({
      skill_id: c.id, source: c.source })) } })),
    onSuccess: () => {
      setCandidates(null);
      void queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
  const toggle = (c: Choice) => setChosen((cur) => cur.some((x) => x.id === c.id) ? cur.filter((x) => x.id !== c.id) : [...cur, c]);
  return (
    <Card title={t("profile.cv_and_skills")}>
      <div className="flex flex-col gap-4">
        <Input label={t("profile.upload_cv")} type="file" accept=".pdf,.docx" hint={t("profile.cv_hint")}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) send.mutate(f); e.target.value = ""; }} />
        {send.isPending && <Loading />}
        <ErrorBox error={send.error} />
        {upload && upload.text_status !== "ok" && <Notice tone="warning">{t(`profile.text_${upload.text_status}`)}</Notice>}
        {candidates && candidates.length > 0 && (
          <Advisory>
            <p className="mb-2 text-sm">{t("profile.extracted_intro")}</p>
            <ul className="flex flex-col">
              {candidates.map((s) => (
                <li key={s.id}>
                  <Checkbox label={<><b>{nameOf(s, i18n.language)}</b>{s.evidence && <span className="ms-2 text-xs opacity-80">“{s.evidence}”</span>}</>}
                    checked={chosen.some((c) => c.id === s.id)}
                    onChange={() => toggle({ id: s.id, name_en: s.name_en, name_ar: s.name_ar, source: "extracted" })} />
                </li>
              ))}
            </ul>
          </Advisory>
        )}
        <div>
          <p className="mb-2 text-sm font-medium">{t("profile.my_skills")}</p>
          <div className="flex flex-wrap gap-2">
            {chosen.map((c) => (
              <button key={c.id} type="button" onClick={() => toggle(c)} title={t("common.remove")}
                className="min-h-[36px] rounded-full bg-[#E6EEFB] px-3 text-sm text-[#1F4E9A]">
                {nameOf(c, i18n.language)} ×
              </button>
            ))}
            {chosen.length === 0 && <span className="text-sm text-ink-muted">{t("profile.no_skills")}</span>}
          </div>
        </div>
        <SkillPicker exclude={chosen.map((c) => c.id)}
          onPick={(s) => setChosen((cur) => [...cur, { id: s.id, name_en: s.name_en, name_ar: s.name_ar, source: "manual" }])} />
        <ErrorBox error={confirm.error} />
        {confirm.isSuccess && <Notice tone="success">{t("profile.skills_saved")}</Notice>}
        <div className="flex flex-wrap items-center gap-3">
          <Button busy={confirm.isPending} onClick={() => confirm.mutate()}>{t("profile.confirm_skills")}</Button>
          {profile.skills_confirmed_at && <span className="text-xs text-ink-muted">{t("profile.confirmed_at")} <span dir="ltr">{formatDateTime(profile.skills_confirmed_at)}</span></span>}
        </div>
        {(cvs.data ?? []).length > 0 && (
          <Table head={[t("profile.cv_version"), t("profile.cv_file"), t("profile.cv_uploaded"), t("profile.cv_text")]}>
            {(cvs.data ?? []).map((cv) => (
              <tr key={cv.id}>
                <Td>{cv.version_no}</Td>
                <Td><button type="button" className="text-primary underline" onClick={() => void openFile(cv.file_id)}>{cv.original_name}</button></Td>
                <Td><span dir="ltr">{formatDateTime(cv.uploaded_at)}</span></Td>
                <Td><Chip tone={cv.text_status === "ok" ? "success" : "warning"}>{t(`profile.text_short_${cv.text_status}`)}</Chip></Td>
              </tr>
            ))}
          </Table>
        )}
      </div>
    </Card>
  );
}

export default function Profile() {
  const { t } = useTranslation();
  const profile = useQuery({ queryKey: ["profile"], queryFn: () => unwrap(api.GET("/api/v1/students/me/profile")) });
  if (profile.isLoading) return <Loading />;
  if (profile.error || !profile.data) return <ErrorBox error={profile.error} />;
  return (
    <>
      <PageHeader title={t("profile.title")} subtitle={profile.data.email} />
      <div className="flex flex-col gap-4">
        <AcademicCard profile={profile.data} />
        <SkillsCard profile={profile.data} />
        <InterestsCard profile={profile.data} />
      </div>
    </>
  );
}
