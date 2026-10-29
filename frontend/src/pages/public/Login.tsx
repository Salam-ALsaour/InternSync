/** Login (wireframe `Login`, FR-AUT-01). */
import { useMutation } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { Button, Card, ErrorBox, Input, Notice } from "../../components/ui";
import { landing, useAuth } from "../../lib/auth";
import { useOnline } from "../../lib/online";

export default function Login() {
  const { t } = useTranslation();
  const { login, me } = useAuth();
  const online = useOnline();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const action = useMutation({
    mutationFn: () => login(email.trim(), password),
    onSuccess: (user) => navigate(landing(user), { replace: true }),
  });

  if (me && !action.isPending) return <Navigate to={landing(me)} replace />;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    action.mutate();
  };

  return (
    <Card title={t("login.title")}>
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {params.get("expired") && <Notice tone="warning">{t("login.expired")}</Notice>}
        {!online && <Notice tone="warning">{t("offline.sign_in")}</Notice>}
        <ErrorBox error={action.error} />
        <Input label={t("field.email")} type="email" autoComplete="username" required value={email}
          onChange={(e) => setEmail(e.target.value)} dir="ltr" />
        <Input label={t("field.password")} type="password" autoComplete="current-password" required value={password}
          onChange={(e) => setPassword(e.target.value)} dir="ltr" />
        <Button type="submit" busy={action.isPending} className="min-h-[48px]">{t("login.submit")}</Button>
        <div className="flex flex-wrap justify-between gap-2 text-sm">
          <Link to="/forgot">{t("login.forgot")}</Link>
          <Link to="/register">{t("login.register")}</Link>
        </div>
      </form>
    </Card>
  );
}
