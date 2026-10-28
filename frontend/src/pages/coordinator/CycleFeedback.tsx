/** The coordinator's view of the students' answers and the final evaluations of a cycle: job-offer rate
 *  (FR-DSH-03), evaluation of the companies (FR-EVL-05), and the leniency alert (FR-DSH-04, informational). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Card, Chip, Empty, ErrorBox, Loading, Table, Td } from "../../components/ui";

const RATINGS = ["learning_opportunities", "supervision_quality", "work_environment", "relevance_to_major"] as const;

function pct(x: number | null | undefined): string {
  return x === null || x === undefined ? "—" : `${x}%`;
}

function num(x: string | number | null | undefined): string {
  return x === null || x === undefined ? "—" : Number(x).toFixed(2);
}

export function OutcomesCard({ cycleId }: { cycleId: string }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["outcomes", cycleId], queryFn: () =>
    unwrap(api.GET("/api/v1/cycles/{cycle_id}/outcomes", { params: { path: { cycle_id: cycleId } } })) });
  if (q.isLoading) return <Loading />;
  if (!q.data) return <ErrorBox error={q.error} />;
  const rows = [{ company_id: "all", company_name: t("ratings.all"), ...q.data.overall }, ...q.data.companies];
  return (
    <Card title={t("outcomes.title")}>
      {q.data.overall.answers === 0 ? <Empty>{t("outcomes.none")}</Empty> : (
        <Table head={[t("field.company"), t("outcomes.answers"), t("outcomes.yes"), t("outcomes.no"), t("outcomes.pending"), t("outcomes.rate")]}>
          {rows.map((c, i) => (
            <tr key={c.company_id} className={i === 0 ? "font-semibold" : ""}>
              <Td>{c.company_name}</Td>
              <Td><span dir="ltr">{c.answers}</span></Td>
              <Td><span dir="ltr">{c.yes}</span></Td>
              <Td><span dir="ltr">{c.no}</span></Td>
              <Td><span dir="ltr">{c.pending}</span></Td>
              <Td><span dir="ltr">{pct(c.job_offer_rate)}</span></Td>
            </tr>
          ))}
        </Table>
      )}
      <p className="mt-3 text-xs text-ink-muted">{t("outcomes.note")}</p>
    </Card>
  );
}

export function RatingsCard({ cycleId }: { cycleId: string }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["company-ratings", cycleId], queryFn: () =>
    unwrap(api.GET("/api/v1/cycles/{cycle_id}/company-evaluations", { params: { path: { cycle_id: cycleId } } })) });
  if (q.isLoading) return <Loading />;
  if (!q.data) return <ErrorBox error={q.error} />;
  const rows = [{ company_id: "all", company_name: t("ratings.all"), ...q.data.overall }, ...q.data.companies];
  return (
    <Card title={t("ratings.title")}>
      {q.data.overall.answers === 0 ? <Empty>{t("outcomes.none")}</Empty> : (
        <Table head={[t("field.company"), t("outcomes.answers"), ...RATINGS.map((r) => t(`feedback.${r}`)), t("ratings.recommend")]}>
          {rows.map((c, i) => (
            <tr key={c.company_id} className={i === 0 ? "font-semibold" : ""}>
              <Td>{c.company_name}</Td>
              <Td><span dir="ltr">{c.answers}</span></Td>
              {RATINGS.map((r) => <Td key={r}><span dir="ltr">{num(c[r])}</span></Td>)}
              <Td><span dir="ltr">{pct(c.recommend_rate)}</span></Td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}

export function LeniencyCard({ cycleId }: { cycleId: string }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["leniency", cycleId], queryFn: () =>
    unwrap(api.GET("/api/v1/cycles/{cycle_id}/leniency-alerts", { params: { path: { cycle_id: cycleId } } })) });
  if (q.isLoading) return <Loading />;
  if (!q.data) return <ErrorBox error={q.error} />;
  const l = q.data;
  return (
    <Card title={t("leniency.title")}>
      {l.companies.length === 0 ? <Empty>{t("leniency.none")}</Empty> : (
        <Table head={[t("field.company"), t("leniency.evaluations"), t("leniency.mean"), t("leniency.difference"), ""]}>
          {l.companies.map((c) => (
            <tr key={c.company_id}>
              <Td className="font-semibold">{c.company_name}</Td>
              <Td><span dir="ltr">{c.evaluations}</span></Td>
              <Td><span dir="ltr">{num(c.mean)}</span></Td>
              <Td><span dir="ltr">{Number(c.difference) > 0 ? "+" : ""}{num(c.difference)}</span></Td>
              <Td>{c.alert && <Chip tone="warning">{t("leniency.alert")}</Chip>}</Td>
            </tr>
          ))}
        </Table>
      )}
      <p className="mt-3 text-xs text-ink-muted">{t("leniency.note", { min: l.min_evaluations, delta: num(l.delta), mean: num(l.cycle_mean) })}</p>
    </Card>
  );
}
