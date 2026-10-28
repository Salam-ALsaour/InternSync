/** The history of a report, an evaluation, or a grade (FR-AUD-03): state changes with user and time, from the audit
 *  log. Loaded when opened. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, unwrap } from "../../api/client";
import { Button, ErrorBox, Loading } from "../../components/ui";
import { formatDateTime } from "../../lib/format";

const ACTIONS = ["submit", "accept", "request_revision", "close_missing", "comment", "flag_missing",
  "similarity_decision", "update", "return", "approve", "reopen"];

export function History({ type, id }: { type: "report_slot" | "evaluation" | "grade"; id: string }) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const q = useQuery({ queryKey: ["history", type, id], enabled: open, queryFn: () =>
    unwrap(api.GET("/api/v1/history/{entity_type}/{entity_id}", { params: { path: { entity_type: type, entity_id: id } } })) });
  const status = (value: unknown) => typeof value === "string" ? t(`status.${value}`, { defaultValue: value }) : null;
  return (
    <div className="mt-3">
      <Button tone="ghost" offlineOk className="min-h-0 px-0" onClick={() => setOpen(!open)}>
        {t(open ? "history.hide" : "history.show")}
      </Button>
      {open && (q.isLoading ? <Loading /> : (
        <>
          <ErrorBox error={q.error} />
          <ol className="mt-2 flex flex-col gap-2 border-s-2 border-line ps-4 text-sm">
            {(q.data ?? []).map((e, i) => {
              const before = status(e.old?.status);
              const after = status(e.new?.status);
              const who = e.role === "system" ? t("history.system")
                : (i18n.language === "ar" ? e.user_ar : e.user_en) ?? e.role;
              return (
                <li key={i}>
                  <p className="font-semibold text-ink">
                    {ACTIONS.includes(e.action) ? t(`history.action_${e.action}`) : e.action}
                    {before && after && before !== after && <span className="font-normal text-ink-muted"> · {before} {i18n.language === "ar" ? "←" : "→"} {after}</span>}
                  </p>
                  <p className="text-xs text-ink-muted">{who} · <span dir="ltr">{formatDateTime(e.at)}</span></p>
                  {e.reason && <p className="mt-1 whitespace-pre-wrap text-xs text-ink">{e.reason}</p>}
                </li>
              );
            })}
            {(q.data ?? []).length === 0 && <li className="text-ink-muted">{t("history.empty")}</li>}
          </ol>
        </>
      ))}
    </div>
  );
}
