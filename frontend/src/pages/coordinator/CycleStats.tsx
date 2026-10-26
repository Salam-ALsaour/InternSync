/** The coordinator's cycle status overall and per company (FR-DSH-02). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type S, unwrap } from "../../api/client";
import { Card, ErrorBox, Loading, Table, Td } from "../../components/ui";

type Figures = S<"Figures">;

function pct(x: number | null | undefined): string {
  return x === null || x === undefined ? "—" : `${x}%`;
}

export default function CycleStats({ cycleId }: { cycleId: string }) {
  const { t } = useTranslation();
  const stats = useQuery({ queryKey: ["cycle-stats", cycleId], queryFn: () =>
    unwrap(api.GET("/api/v1/cycles/{cycle_id}/stats", { params: { path: { cycle_id: cycleId } } })) });
  if (stats.isLoading) return <Loading />;
  if (!stats.data) return <ErrorBox error={stats.error} />;
  const o: Figures = stats.data.overall;
  const tiles: [string, string][] = [
    [t("stats.placed"), `${o.placed} / ${o.enrolled ?? "—"}`], [t("stats.unplaced"), String(o.unplaced ?? "—")],
    [t("stats.submission_rate"), pct(o.submission_rate)], [t("stats.late_rate"), pct(o.late_rate)],
    [t("stats.attendance_rate"), pct(o.attendance_rate)], [t("stats.evaluation_completion"), pct(o.evaluation_completion)],
  ];
  return (
    <div className="flex flex-col gap-4">
      <Card title={t("stats.overall")}>
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          {tiles.map(([k, v]) => (
            <div key={k}><dt className="text-xs text-ink-muted">{k}</dt><dd className="text-2xl font-bold text-primary" dir="ltr">{v}</dd></div>
          ))}
        </dl>
        <p className="mt-3 text-xs text-ink-muted">{t("stats.note")}</p>
      </Card>
      <Card title={t("stats.per_company")}>
        <Table head={[t("field.company"), t("stats.placed"), t("stats.submission_rate"), t("stats.late_rate"),
          t("stats.attendance_rate"), t("stats.evaluation_completion")]}>
          {stats.data.companies.map((c) => (
            <tr key={c.company_id}>
              <Td className="font-semibold">{c.company_name}</Td>
              <Td><span dir="ltr">{c.placed}</span></Td>
              <Td><span dir="ltr">{pct(c.submission_rate)}</span></Td>
              <Td><span dir="ltr">{pct(c.late_rate)}</span></Td>
              <Td><span dir="ltr">{pct(c.attendance_rate)}</span></Td>
              <Td><span dir="ltr">{pct(c.evaluation_completion)}</span></Td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
}
