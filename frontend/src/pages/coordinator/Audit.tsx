/** Audit log with filters (wireframe `CO_Audit`, FR-AUD-02). The coordinator sees the college's entries; the
 *  Platform Admin sees accounts, organizations, verification, and the catalog. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Input, Loading, PageHeader, Select, Table, Td } from "../../components/ui";
import { useMe } from "../../lib/auth";
import { formatDateTime, fromRiyadhInput } from "../../lib/format";

const COLLEGE_TYPES = ["user", "verification_request", "training_cycle", "cycle_week", "student_profile", "cv", "application",
  "placement", "report_slot", "attendance_week", "evaluation", "grade"];
const PLATFORM_TYPES = ["user", "university", "college", "company", "verification_request", "skill", "major", "settings"];

function short(value: unknown): string {
  if (value == null) return "";
  const text = JSON.stringify(value);
  return text.length > 140 ? `${text.slice(0, 140)}…` : text;
}

export default function AuditLog() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const [filters, setFilters] = useState({ entity_type: "", date_from: "", date_to: "", student: "" });
  const [page, setPage] = useState(1);
  const students = useQuery({
    queryKey: ["audit-students", filters.student],
    enabled: me.role === "coordinator" && filters.student.trim().length >= 2,
    queryFn: () => unwrap(api.GET("/api/v1/users", { params: { query: { role: "student", q: filters.student, page_size: 10 } } })),
  });
  const [studentId, setStudentId] = useState("");
  const query: Record<string, string | number> = { page, page_size: 25 };
  if (filters.entity_type) query.entity_type = filters.entity_type;
  if (filters.date_from) query.date_from = fromRiyadhInput(`${filters.date_from}T00:00`);
  if (filters.date_to) query.date_to = fromRiyadhInput(`${filters.date_to}T23:59`);
  if (studentId) query.student_id = studentId;
  const list = useQuery({ queryKey: ["audit", query], queryFn: () => unwrap(api.GET("/api/v1/audit-log", { params: { query: query as never } })) });
  const types = me.role === "coordinator" ? COLLEGE_TYPES : PLATFORM_TYPES;
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / 25)) : 1;
  const set = (k: keyof typeof filters) => (e: { target: { value: string } }) => {
    setFilters({ ...filters, [k]: e.target.value });
    setPage(1);
  };
  return (
    <>
      <PageHeader title={t("menu.audit")} subtitle={t("audit.subtitle")} />
      <Card className="mb-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Select label={t("audit.entity_type")} value={filters.entity_type} onChange={set("entity_type")} placeholder={t("common.all")}
            options={types.map((x) => ({ value: x, label: t(`entity.${x}`) }))} />
          <Input label={t("audit.from")} type="date" value={filters.date_from} onChange={set("date_from")} />
          <Input label={t("audit.to")} type="date" value={filters.date_to} onChange={set("date_to")} />
          {me.role === "coordinator" && (
            <div>
              <Input label={t("field.student")} value={filters.student} onChange={(e) => { set("student")(e); setStudentId(""); }} placeholder={t("audit.search_student")} />
              {!studentId && (students.data?.items ?? []).length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {(students.data?.items ?? []).map((s) => (
                    <button key={s.id} type="button" className="rounded-full border border-line px-2 py-1 text-xs"
                      onClick={() => { setStudentId(s.id); setFilters({ ...filters, student: i18n.language === "en" ? s.name_en : s.name_ar }); }}>
                      {i18n.language === "en" ? s.name_en : s.name_ar}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
      <Card>
        {list.isLoading ? <Loading /> : <ErrorBox error={list.error} />}
        {list.data && (list.data.items.length === 0 ? <Empty /> : (
          <Table head={[t("audit.time"), t("audit.user"), t("audit.action"), t("audit.entity"), t("field.student"), t("audit.change")]}>
            {list.data.items.map((e) => (
              <tr key={e.id}>
                <Td><span dir="ltr" className="whitespace-nowrap">{formatDateTime(e.at)}</span></Td>
                <Td>{(i18n.language === "en" ? e.user_en : e.user_ar) ?? t("audit.system")}<p className="text-xs text-ink-muted">{t(`role.${e.role}`)}</p></Td>
                <Td className="font-semibold">{t(`action.${e.action}`, { defaultValue: e.action })}</Td>
                <Td>{t(`entity.${e.entity_type}`, { defaultValue: e.entity_type })}</Td>
                <Td>{(i18n.language === "en" ? e.student_en : e.student_ar) ?? "—"}</Td>
                <Td><code dir="ltr" className="block max-w-xs break-all text-xs text-ink-muted">{short(e.new_value)}{e.reason ? ` · ${e.reason}` : ""}</code></Td>
              </tr>
            ))}
          </Table>
        ))}
        {pages > 1 && (
          <div className="mt-4 flex items-center gap-3">
            <Button tone="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>{t("common.previous")}</Button>
            <span className="text-sm" dir="ltr">{page} / {pages}</span>
            <Button tone="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>{t("common.next")}</Button>
          </div>
        )}
      </Card>
    </>
  );
}
