/** Privacy notice and consent at first login (wireframe `Consent`, NFR-PRV-01). */
import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Button, Card, ErrorBox } from "../../components/ui";
import { landing, useAuth } from "../../lib/auth";

export default function Consent() {
  const { t } = useTranslation();
  const { me, refresh, logout } = useAuth();
  const navigate = useNavigate();
  const action = useMutation({
    mutationFn: () => unwrap(api.POST("/api/v1/me/consent")),
    onSuccess: async () => {
      const user = await refresh();
      if (user) navigate(landing(user), { replace: true });
    },
  });
  if (me && !me.consent_required) return <Navigate to={landing(me)} replace />;
  const points = ["collect", "use", "ai", "share", "retention", "rights"];
  return (
    <Card title={t("consent.title")}>
      <p className="mb-4 text-sm text-ink-muted">{t("consent.intro")}</p>
      <ul className="mb-6 flex list-disc flex-col gap-2 ps-5 text-sm text-ink">
        {points.map((p) => <li key={p}>{t(`consent.${p}`)}</li>)}
      </ul>
      <ErrorBox error={action.error} />
      <div className="mt-4 flex flex-wrap gap-2">
        <Button busy={action.isPending} onClick={() => action.mutate()}>{t("consent.accept")}</Button>
        <Button tone="secondary" onClick={() => void logout()}>{t("common.logout")}</Button>
      </div>
    </Card>
  );
}
