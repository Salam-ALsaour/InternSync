/** Browse, filter, and apply (wireframe `ST_Vacancies`, browse tab; FR-VAC-03, FR-VAC-04). Ranking and the
 *  fit explanation come in Increment 2. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Button, Card, Chip, ErrorBox, Input, Loading, Notice, PageHeader, Select, Tabs } from "../../components/ui";
import { useAuth } from "../../lib/auth";
import { formatDate, formatDateTime, nameOf } from "../../lib/format";
import { useMajors } from "../public/Register";
import Recommended from "./Recommended";

type Vacancy = S<"VacancyOut">;

export function VacancyDetails({ v }: { v: Vacancy }) {
  const { t, i18n } = useTranslation();
  const names = (xs: { name_en: string; name_ar: string }[]) => xs.map((x) => nameOf(x, i18n.language)).join(i18n.language === "ar" ? "، " : ", ") || "—";
  return (
    <div className="mt-3 flex flex-col gap-2 text-sm">
      <p className="whitespace-pre-wrap">{v.description}</p>
      <p><b>{t("vacancy.required_skills")}:</b> {names(v.required_skills)}</p>
      <p><b>{t("vacancy.preferred_skills")}:</b> {names(v.preferred_skills)}</p>
      <p><b>{t("vacancy.majors")}:</b> {names(v.majors)}</p>
      {v.target_universities.length > 0 && <p><b>{t("vacancy.universities")}:</b> {names(v.target_universities)}</p>}
      <p><b>{t("vacancy.period")}:</b> {formatDate(v.training_start)} – {formatDate(v.training_end)}</p>
    </div>
  );
}

function VacancyCard({ v }: { v: Vacancy }) {
  const { t } = useTranslation();
  const { me } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const apply = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/vacancies/{vacancy_id}/applications", { params: { path: { vacancy_id: v.id } } })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vacancies"] });
      void queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
  const verified = me?.verification_status === "verified";
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold">{v.title}</h2>
          <p className="text-sm text-ink-muted">{v.company_name} · {v.city}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Chip tone="info">{t(`training.${v.training_type}`)}</Chip>
          {v.already_applied ? <Chip tone="success">{t("vacancy.applied")}</Chip>
            : v.eligible ? <Chip tone="success">{t("vacancy.eligible")}</Chip>
              : <Chip tone="warning">{t(`ineligible.${v.ineligible_reason ?? "not_enrolled"}`)}</Chip>}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm text-ink-muted">
        <span>{t("vacancy.deadline")}: <span dir="ltr">{formatDateTime(v.application_deadline)}</span></span>
        <span>{t("vacancy.seats")}: <span dir="ltr">{v.seats - v.seats_taken} / {v.seats}</span></span>
        {v.min_gpa && <span>{t("vacancy.min_gpa")}: {v.min_gpa}</span>}
      </div>
      {open && <VacancyDetails v={v} />}
      <ErrorBox error={apply.error} />
      {apply.isSuccess && <div className="mt-3"><Notice tone="success">{t("vacancy.applied_note")}</Notice></div>}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button tone="secondary" onClick={() => setOpen(!open)}>{open ? t("common.less") : t("common.details")}</Button>
        {verified && !v.already_applied && (
          <Button busy={apply.isPending} disabled={!v.eligible} onClick={() => apply.mutate()}>{t("vacancy.apply")}</Button>
        )}
      </div>
    </Card>
  );
}

function Browse() {
  const { t, i18n } = useTranslation();
  const { me } = useAuth();
  const majors = useMajors();
  const [filters, setFilters] = useState({ q: "", city: "", training_type: "", major_id: "" });
  const [page, setPage] = useState(1);
  const query = Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) as Record<string, string>;
  const list = useQuery({
    queryKey: ["vacancies", query, page],
    queryFn: () => unwrap(api.GET("/api/v1/vacancies", { params: { query: { ...query, page, page_size: 10 } as never } })),
  });
  const set = (k: keyof typeof filters) => (e: { target: { value: string } }) => {
    setFilters({ ...filters, [k]: e.target.value });
    setPage(1);
  };
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / 10)) : 1;
  return (
    <>
      {me?.verification_status !== "verified" && <div className="mb-4"><Notice tone="warning">{t("vacancy.pending_note")}</Notice></div>}
      <Card className="mb-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Input label={t("vacancy.search")} value={filters.q} onChange={set("q")} />
          <Input label={t("field.city")} value={filters.city} onChange={set("city")} />
          <Select label={t("vacancy.training_type")} value={filters.training_type} onChange={set("training_type")}
            placeholder={t("common.all")} options={[{ value: "coop", label: t("training.coop") }, { value: "summer", label: t("training.summer") }]} />
          <Select label={t("field.major")} value={filters.major_id} onChange={set("major_id")} placeholder={t("common.all")}
            options={(majors.data ?? []).map((m) => ({ value: m.id ?? "", label: nameOf(m, i18n.language) }))} />
        </div>
      </Card>
      {list.isLoading && <Loading />}
      <ErrorBox error={list.error} />
      <div className="flex flex-col gap-4">
        {(list.data?.items ?? []).map((v) => <VacancyCard key={v.id} v={v} />)}
        {list.data?.items.length === 0 && <Notice>{t("common.no_results")}</Notice>}
      </div>
      {pages > 1 && (
        <div className="mt-4 flex items-center gap-3">
          <Button tone="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>{t("common.previous")}</Button>
          <span className="text-sm" dir="ltr">{page} / {pages}</span>
          <Button tone="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>{t("common.next")}</Button>
        </div>
      )}
    </>
  );
}

export default function Vacancies() {
  const { t } = useTranslation();
  const { me } = useAuth();
  const verified = me?.verification_status === "verified";
  const [tab, setTab] = useState<"recommended" | "browse">(verified ? "recommended" : "browse");
  return (
    <>
      <PageHeader title={t("vacancy.browse_title")} subtitle={t("vacancy.browse_subtitle")} />
      {verified && <Tabs value={tab} onChange={setTab} items={[{ value: "recommended", label: t("match.tab") },
        { value: "browse", label: t("match.tab_browse") }]} />}
      {tab === "recommended" && verified ? <Recommended /> : <Browse />}
    </>
  );
}
