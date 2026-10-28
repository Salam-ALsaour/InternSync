/** Skills with synonyms and learning resources, majors, and system settings (wireframe `PA_Settings`, FR-CYC-04,
 *  NFR-MNT-03). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, api, type S, unwrap } from "../../api/client";
import { Button, Card, Dialog, Empty, ErrorBox, Input, Loading, Notice, PageHeader, StatusChip, Table, Tabs, Td } from "../../components/ui";
import { nameOf } from "../../lib/format";

type Resource = S<"ResourceIO">;

function SkillDialog({ skill, onDone }: { skill: S<"SkillOut"> | "new"; onDone: () => void }) {
  const { t } = useTranslation();
  const existing = skill === "new" ? null : skill;
  const [v, setV] = useState({ name_ar: existing?.name_ar ?? "", name_en: existing?.name_en ?? "", synonyms: existing?.synonyms.join(", ") ?? "" });
  const [resources, setResources] = useState<Resource[]>([]);
  const res = useQuery({ queryKey: ["resources", existing?.id], enabled: !!existing, queryFn: () =>
    unwrap(api.GET("/api/v1/skills/{skill_id}/resources", { params: { path: { skill_id: existing?.id ?? "" } } })) });
  useEffect(() => {
    if (res.data) setResources(res.data);
  }, [res.data]);
  const body = { name_ar: v.name_ar, name_en: v.name_en, synonyms: v.synonyms.split(/[,،]/).map((s) => s.trim()).filter(Boolean) };
  const save = useMutation({
    mutationFn: async () => {
      const out = existing
        ? await unwrap(api.PATCH("/api/v1/skills/{skill_id}", { params: { path: { skill_id: existing.id } }, body }))
        : await unwrap(api.POST("/api/v1/skills", { body }));
      if (existing) {
        await unwrap(api.PUT("/api/v1/skills/{skill_id}/resources", { params: { path: { skill_id: out.id } },
          body: resources.filter((r) => r.title.trim() && r.url.trim()) }));
      }
      return out;
    },
    onSuccess: onDone,
  });
  const update = (i: number, patch: Partial<Resource>) => setResources(resources.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  return (
    <div className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label={t("field.name_ar")} value={v.name_ar} onChange={(e) => setV({ ...v, name_ar: e.target.value })} />
        <Input label={t("field.name_en")} dir="ltr" value={v.name_en} onChange={(e) => setV({ ...v, name_en: e.target.value })} />
      </div>
      <Input label={t("catalog.synonyms")} value={v.synonyms} onChange={(e) => setV({ ...v, synonyms: e.target.value })} hint={t("catalog.synonyms_hint")} />
      {existing && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">{t("catalog.resources")}</p>
          {resources.map((r, i) => (
            <div key={i} className="grid gap-2 rounded-ctl border border-line p-2 sm:grid-cols-2">
              <Input label={t("catalog.resource_title")} value={r.title} onChange={(e) => update(i, { title: e.target.value })} />
              <Input label={t("catalog.resource_url")} dir="ltr" value={r.url} onChange={(e) => update(i, { url: e.target.value })} />
              <Input label={t("catalog.resource_effort")} value={r.estimated_effort ?? ""} onChange={(e) => update(i, { estimated_effort: e.target.value })} />
              <div className="flex items-end"><Button tone="ghost" onClick={() => setResources(resources.filter((_, j) => j !== i))}>{t("common.remove")}</Button></div>
            </div>
          ))}
          <div><Button tone="secondary" onClick={() => setResources([...resources, { title: "", url: "https://", estimated_effort: null, language: null }])}>
            {t("catalog.add_resource")}</Button></div>
        </div>
      )}
      <ErrorBox error={save.error} />
      <div><Button busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button></div>
    </div>
  );
}

function Skills() {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<S<"SkillOut"> | "new" | null>(null);
  const list = useQuery({ queryKey: ["admin-skills", q, page], queryFn: () =>
    unwrap(api.GET("/api/v1/skills", { params: { query: { q: q || undefined, include_inactive: true, page, page_size: 25 } } })) });
  const refresh = () => {
    setEditing(null);
    void queryClient.invalidateQueries({ queryKey: ["admin-skills"] });
  };
  const toggle = useMutation({ mutationFn: (s: S<"SkillOut">) => unwrap(api.PATCH("/api/v1/skills/{skill_id}",
    { params: { path: { skill_id: s.id } }, body: { is_active: !s.is_active } })), onSuccess: refresh });
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / 25)) : 1;
  return (
    <Card actions={<Button onClick={() => setEditing("new")}>{t("catalog.new_skill")}</Button>} title={t("catalog.skills_n", { n: list.data?.total ?? 0 })}>
      <div className="mb-4 max-w-sm"><Input label={t("vacancy.search")} value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></div>
      <ErrorBox error={list.error ?? toggle.error} />
      {list.isLoading ? <Loading /> : (list.data?.items ?? []).length === 0 ? <Empty /> : (
        <Table head={[t("field.name"), t("catalog.synonyms"), t("catalog.resources"), t("report.status"), ""]}>
          {(list.data?.items ?? []).map((s) => (
            <tr key={s.id}>
              <Td className="font-semibold">{nameOf(s, i18n.language)}<p className="text-xs font-normal text-ink-muted">{i18n.language === "en" ? s.name_ar : s.name_en}</p></Td>
              <Td><span className="text-xs">{s.synonyms.join(", ") || "—"}</span></Td>
              <Td>{s.resources}</Td>
              <Td><StatusChip status={s.is_active ? "active" : "inactive"} label={t(s.is_active ? "team.active" : "team.inactive")} /></Td>
              <Td><div className="flex gap-2">
                <Button tone="ghost" onClick={() => setEditing(s)}>{t("common.edit")}</Button>
                <Button tone="ghost" onClick={() => toggle.mutate(s)}>{t(s.is_active ? "team.deactivate" : "team.reactivate")}</Button>
              </div></Td>
            </tr>
          ))}
        </Table>
      )}
      {pages > 1 && (
        <div className="mt-4 flex items-center gap-3">
          <Button tone="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>{t("common.previous")}</Button>
          <span className="text-sm" dir="ltr">{page} / {pages}</span>
          <Button tone="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>{t("common.next")}</Button>
        </div>
      )}
      <Dialog open={!!editing} title={editing === "new" ? t("catalog.new_skill") : t("common.edit")} onClose={() => setEditing(null)}>
        {editing && <SkillDialog skill={editing} onDone={refresh} />}
      </Dialog>
    </Card>
  );
}

function Majors() {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ["majors"], queryFn: () => unwrap(api.GET("/api/v1/majors")) });
  const [v, setV] = useState({ name_ar: "", name_en: "" });
  const add = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/majors", { body: v })), onSuccess: () => {
    setV({ name_ar: "", name_en: "" });
    void queryClient.invalidateQueries({ queryKey: ["majors"] });
  } });
  return (
    <Card title={t("catalog.majors")}>
      <div className="mb-4 grid items-end gap-3 sm:grid-cols-[1fr_1fr_auto]">
        <Input label={t("field.name_ar")} value={v.name_ar} onChange={(e) => setV({ ...v, name_ar: e.target.value })} />
        <Input label={t("field.name_en")} dir="ltr" value={v.name_en} onChange={(e) => setV({ ...v, name_en: e.target.value })} />
        <Button busy={add.isPending} onClick={() => add.mutate()}>{t("catalog.add_major")}</Button>
      </div>
      <ErrorBox error={add.error} />
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {(list.data ?? []).map((m) => <li key={m.id} className="rounded-ctl border border-line p-3 text-sm">{nameOf(m, i18n.language)}</li>)}
      </ul>
    </Card>
  );
}

function Settings() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const current = useQuery({ queryKey: ["settings"], queryFn: () => unwrap(api.GET("/api/v1/settings")) });
  const [values, setValues] = useState<Record<string, string>>({});
  useEffect(() => {
    if (current.data) setValues(Object.fromEntries(Object.entries(current.data).map(([k, v]) => [k, String(v)])));
  }, [current.data]);
  const save = useMutation({
    mutationFn: () => unwrap(api.PATCH("/api/v1/settings", { body: Object.fromEntries(Object.entries(values).map(([k, v]) => [k, Number(v)])) })),
    onSuccess: (data) => queryClient.setQueryData(["settings"], data),
  });
  if (current.isLoading) return <Loading />;
  return (
    <Card title={t("catalog.settings")}>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Object.keys(values).map((k) => (
          <Input key={k} label={t(`setting.${k.replace(".", "_")}`)} type="number" dir="ltr" value={values[k]}
            step={k.startsWith("matching.") || (k.startsWith("similarity.") && k !== "similarity.ngram_size") ? "0.01" : "1"}
            onChange={(e) => setValues({ ...values, [k]: e.target.value })}
            error={save.error instanceof ApiError ? save.error.fieldMessage(k) : undefined} />
        ))}
      </div>
      <ErrorBox error={save.error} />
      {save.isSuccess && <div className="mt-3"><Notice tone="success">{t("common.saved")}</Notice></div>}
      <Button className="mt-4" busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button>
    </Card>
  );
}

export default function Catalog() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"skills" | "majors" | "settings">("skills");
  return (
    <>
      <PageHeader title={t("menu.catalog")} />
      <Tabs value={tab} onChange={setTab} items={[{ value: "skills", label: t("catalog.skills") }, { value: "majors", label: t("catalog.majors") },
        { value: "settings", label: t("catalog.settings") }]} />
      {tab === "skills" && <Skills />}
      {tab === "majors" && <Majors />}
      {tab === "settings" && <Settings />}
    </>
  );
}
