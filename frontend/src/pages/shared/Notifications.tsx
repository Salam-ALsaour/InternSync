/** The notification list of every role (FR-NOT-01) with the push switch of this browser (FR-PWA-02). Texts come
 *  from the API in the user's language (FR-NOT-06). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Button, Card, Empty, ErrorBox, Loading, Notice, PageHeader } from "../../components/ui";
import { formatDateTime } from "../../lib/format";
import { type PushState, pushState, turnOff, turnOn } from "../../lib/push";

function PushSwitch() {
  const { t } = useTranslation();
  const [state, setState] = useState<PushState | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    void pushState().then(setState).catch(() => setState("unavailable"));
  }, []);
  if (state === null) return null;
  const toggle = async () => {
    setBusy(true);
    try {
      setState(state === "on" ? await turnOff() : await turnOn());
    } catch {
      setState("unavailable");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Card title={t("notifications.push_title")}>
      <p className="mb-3 text-sm text-ink-muted">{t(`notifications.push_${state}`)}</p>
      {(state === "on" || state === "off") && (
        <Button tone={state === "on" ? "secondary" : "primary"} busy={busy} onClick={() => void toggle()}>
          {t(state === "on" ? "notifications.push_turn_off" : "notifications.push_turn_on")}
        </Button>
      )}
      <p className="mt-3 text-xs text-ink-muted">{t("notifications.push_email_note")}</p>
    </Card>
  );
}

export default function Notifications() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ["notifications", "list"], queryFn: () =>
    unwrap(api.GET("/api/v1/notifications", { params: { query: { page_size: 50 } } })) });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["notifications"] });
  const readAll = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/notifications/read-all")), onSuccess: refresh });
  const open = async (id: string, read: boolean, link: string | null | undefined) => {
    if (!read) {
      await unwrap(api.POST("/api/v1/notifications/{notification_id}/read", { params: { path: { notification_id: id } } }));
      refresh();
    }
    if (link) navigate(link);
  };
  if (list.isLoading) return <Loading />;
  const items = list.data?.items ?? [];
  return (
    <>
      <PageHeader title={t("notifications.title")}
        subtitle={t("notifications.unread_n", { n: list.data?.unread_count ?? 0 })}
        actions={(list.data?.unread_count ?? 0) > 0 &&
          <Button tone="secondary" busy={readAll.isPending} onClick={() => readAll.mutate()}>{t("notifications.read_all")}</Button>} />
      <ErrorBox error={list.error ?? readAll.error} />
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            {items.length === 0 ? <Empty /> : (
              <ul className="divide-y divide-line">
                {items.map((n) => (
                  <li key={n.id}>
                    <button type="button" onClick={() => void open(n.id, !!n.read_at, n.link)}
                      className={`flex w-full flex-col gap-1 px-2 py-3 text-start hover:bg-ground ${n.read_at ? "" : "bg-[#E6EEFB]/40"}`}>
                      <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                        {!n.read_at && <span className="h-2 w-2 shrink-0 rounded-full bg-primary" aria-label={t("notifications.unread")} />}
                        {n.title}
                      </span>
                      <span className="text-sm text-ink-muted">{n.body}</span>
                      <span className="text-xs text-ink-muted" dir="ltr">{formatDateTime(n.created_at)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {(list.data?.total ?? 0) > items.length && <Notice>{t("notifications.older")}</Notice>}
          </Card>
        </div>
        <div><PushSwitch /></div>
      </div>
    </>
  );
}
