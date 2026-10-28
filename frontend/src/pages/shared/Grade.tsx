/** The grade of one placement (wireframe `AS_Grade`, FR-WFL-02 – 06): components with the computed company part,
 *  the total, the preconditions checklist, and the actions the caller may take. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, api, type S, unwrap } from "../../api/client";
import { Button, Card, Dialog, ErrorBox, Loading, Notice, StatusChip, Table, Td, TextArea } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDateTime, nameOf } from "../../lib/format";
import { CertificateCard } from "./Certificate";
import { History } from "./History";

type GradeOut = S<"GradeOut">;

type T = (k: string, o?: Record<string, unknown>) => string;

function checkLabel(c: S<"Check">, t: T, components: GradeOut["components"], lang: string) {
  if (c.item === "component") {
    const comp = components.find((x) => x.id === c.component_id);
    return t("grade.check_component", { name: comp ? nameOf(comp, lang) : "" });
  }
  return t(`grade.check_${c.item}`);
}

/** One line per condition, except the weekly reports: they share one line that lists the weeks still open. */
function checkLines(g: GradeOut, t: T, lang: string) {
  const open = g.preconditions.filter((c) => c.item === "weekly_report" && !c.ok).map((c) => c.week_no);
  const lines: { ok: boolean; label: string }[] = [];
  let weekly = false;
  for (const c of g.preconditions) {
    if (c.item !== "weekly_report") lines.push({ ok: c.ok, label: checkLabel(c, t, g.components, lang) });
    else if (!weekly) {
      weekly = true;
      lines.push({ ok: open.length === 0, label: open.length === 0 ? t("grade.check_weekly_all")
        : t("grade.check_weekly_open", { weeks: open.join(lang === "ar" ? "، " : ", ") }) });
    }
  }
  return lines;
}

export default function Grade({ placementId }: { placementId: string }) {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const queryClient = useQueryClient();
  const key = ["grade", placementId];
  const data = useQuery({ queryKey: key, queryFn: () =>
    unwrap(api.GET("/api/v1/placements/{placement_id}/grade", { params: { path: { placement_id: placementId } } })) });
  const [values, setValues] = useState<Record<string, string>>({});
  const [dialog, setDialog] = useState<"return" | "reopen" | null>(null);
  const [text, setText] = useState("");
  useEffect(() => {
    if (data.data) setValues(Object.fromEntries(data.data.components.filter((c) => !c.computed).map((c) => [c.id, c.score ?? ""])));
  }, [data.data]);
  const done = (g: GradeOut) => {
    queryClient.setQueryData(key, g);
    void queryClient.invalidateQueries({ queryKey: ["placement", placementId] });
    void queryClient.invalidateQueries({ queryKey: ["grades"] });
    setDialog(null);
  };
  const g = data.data;
  const id = g?.id ?? "";
  const save = useMutation({ mutationFn: () => unwrap(api.PUT("/api/v1/placements/{placement_id}/grade", {
    params: { path: { placement_id: placementId } },
    body: { component_scores: Object.entries(values).filter(([, v]) => v !== "").map(([component_id, score]) => ({ component_id, score })) } as never,
  })), onSuccess: done });
  const submit = useMutation({ mutationFn: async () => {
    if (g?.can_edit) await save.mutateAsync();
    return unwrap(api.POST("/api/v1/grades/{grade_id}/submit", { params: { path: { grade_id: id } } }));
  }, onSuccess: done });
  const approve = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/grades/{grade_id}/approve", { params: { path: { grade_id: id } } })), onSuccess: done });
  const decide = useMutation({ mutationFn: () => dialog === "return"
    ? unwrap(api.POST("/api/v1/grades/{grade_id}/return", { params: { path: { grade_id: id } }, body: { comment: text } }))
    : unwrap(api.POST("/api/v1/grades/{grade_id}/reopen", { params: { path: { grade_id: id } }, body: { reason: text } })), onSuccess: done });
  if (data.isLoading) return <Loading />;
  if (data.error || !g) return <ErrorBox error={data.error} />;
  if (!g.visible) return <Card title={t("grade.title")}><Notice>{t("grade.hidden")}</Notice></Card>;
  const missing = submit.error instanceof ApiError ? (submit.error.extra.missing as { item: string }[] | undefined) : undefined;
  return (
    <>
    <Card title={t("grade.title")} actions={<StatusChip status={g.status ?? "draft"} label={t(`grade.status_${g.status}`)} />}>
      <div className="flex flex-col gap-4">
        {g.return_comment && g.status === "draft" && <Notice tone="warning">{t("grade.returned")}: {g.return_comment}</Notice>}
        {g.reopen_reason && g.status === "draft" && <Notice tone="warning">{t("grade.reopened")}: {g.reopen_reason}</Notice>}
        <Table head={[t("grade.component"), t("cycles.weight"), t("grade.score"), t("cycles.source")]}>
          {g.components.map((c) => (
            <tr key={c.id}>
              <Td className="font-semibold">{nameOf(c, i18n.language)}</Td>
              <Td><span dir="ltr">{Number(c.weight)}%</span></Td>
              <Td>
                {g.can_edit && !c.computed ? (
                  <input aria-label={nameOf(c, i18n.language)} type="number" min={0} max={100} step="0.01" dir="ltr"
                    className="min-h-[40px] w-28 rounded-ctl border border-line px-2" value={values[c.id] ?? ""}
                    onChange={(e) => setValues({ ...values, [c.id]: e.target.value })} />
                ) : <span dir="ltr">{c.score ?? "—"}</span>}
              </Td>
              <Td><span className="text-xs text-ink-muted">{c.computed ? t("grade.computed") : t("cycles.source_academic")}</span></Td>
            </tr>
          ))}
        </Table>
        <p className="text-lg font-bold">{t("grade.total")}: <span dir="ltr">{g.total ?? "—"}</span></p>
        {g.preconditions.length > 0 && g.status === "draft" && (
          <div>
            <p className="mb-2 text-sm font-semibold">{t("grade.preconditions")}</p>
            <ul className="grid gap-1 text-sm sm:grid-cols-2">
              {checkLines(g, t, i18n.language).map((c, i) => (
                <li key={i} className={c.ok ? "text-[#1E6B34]" : "text-[#A61B1B]"}>{c.ok ? "✓" : "✗"} {c.label}</li>
              ))}
            </ul>
          </div>
        )}
        {(g.submitted_at || g.approved_at) && (
          <p className="text-xs text-ink-muted">
            {g.submitted_at && <>{t("grade.submitted_at")}: <span dir="ltr">{formatDateTime(g.submitted_at)}</span> </>}
            {g.approved_at && <>· {t("grade.approved_at")}: <span dir="ltr">{formatDateTime(g.approved_at)}</span></>}
          </p>
        )}
        <ErrorBox error={save.error ?? submit.error ?? approve.error} />
        {g.id && <History type="grade" id={g.id} />}
        {missing && <p className="text-sm text-[#A61B1B]">{t("grade.missing_n", { n: missing.length })}</p>}
        <div className="flex flex-wrap gap-2">
          {g.can_edit && <Button tone="secondary" busy={save.isPending} onClick={() => save.mutate()}>{t("common.save")}</Button>}
          {g.can_edit && <Button busy={submit.isPending} onClick={() => submit.mutate()}>{t("grade.submit")}</Button>}
          {g.can_decide && <Button busy={approve.isPending} onClick={() => approve.mutate()}>{t("grade.approve")}</Button>}
          {g.can_decide && <Button tone="secondary" onClick={() => { setDialog("return"); setText(""); }}>{t("grade.return")}</Button>}
          {g.can_reopen && <Button tone="danger" onClick={() => { setDialog("reopen"); setText(""); }}>{t("grade.reopen")}</Button>}
        </div>
      </div>
      <Dialog open={!!dialog} title={dialog === "return" ? t("grade.return") : t("grade.reopen")} onClose={() => setDialog(null)}>
        <TextArea label={dialog === "return" ? t("grade.return_comment") : t("common.reason")} value={text} onChange={(e) => setText(e.target.value)} />
        <ErrorBox error={decide.error} />
        <div className="mt-4 flex gap-2">
          <Button busy={decide.isPending} disabled={!text.trim()} onClick={() => decide.mutate()}>{t("common.save")}</Button>
          <Button tone="secondary" onClick={() => setDialog(null)}>{t("common.cancel")}</Button>
        </div>
      </Dialog>
    </Card>
    {(me.role === "coordinator" || me.role === "student") &&
      <div className="mt-4"><CertificateCard placementId={placementId} coordinator={me.role === "coordinator"} /></div>}
    </>
  );
}
