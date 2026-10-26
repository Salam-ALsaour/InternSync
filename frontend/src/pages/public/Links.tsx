/** Pages opened from emails: confirm email, accept invitation, forgot and reset password (FR-AUT-02, FR-AUT-04). */
import { useMutation, useQuery } from "@tanstack/react-query";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api, unwrap } from "../../api/client";
import { Button, Card, ErrorBox, Input, Loading, Notice } from "../../components/ui";
import { nameOf } from "../../lib/format";

export function ConfirmEmail() {
  const { t } = useTranslation();
  const { token = "" } = useParams();
  const fired = useRef(false);
  const action = useMutation({ mutationFn: () => unwrap(api.POST("/api/v1/auth/email/confirm", { body: { token } })) });
  useEffect(() => {
    if (!fired.current) {
      fired.current = true;
      action.mutate();
    }
  }, [action]);
  return (
    <Card title={t("confirm.title")}>
      {action.isPending && <Loading />}
      <ErrorBox error={action.error} />
      {action.isSuccess && <Notice tone="success">{t("confirm.done")}</Notice>}
      <Link to="/login" className="mt-4 inline-block font-semibold">{t("register.to_login")}</Link>
    </Card>
  );
}

function PasswordForm({ submitLabel, onSubmit, busy, error }: { submitLabel: string; busy: boolean; error: unknown;
  onSubmit: (password: string) => void }) {
  const { t } = useTranslation();
  const [password, setPassword] = useState("");
  const [again, setAgain] = useState("");
  const mismatch = again.length > 0 && again !== password;
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!mismatch) onSubmit(password);
  };
  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <ErrorBox error={error} />
      <Input label={t("field.new_password")} type="password" dir="ltr" autoComplete="new-password" value={password}
        onChange={(e) => setPassword(e.target.value)} hint={t("register.password_hint")} />
      <Input label={t("field.repeat_password")} type="password" dir="ltr" autoComplete="new-password" value={again}
        onChange={(e) => setAgain(e.target.value)} error={mismatch ? t("reset.mismatch") : undefined} />
      <Button type="submit" busy={busy} disabled={!password || mismatch}>{submitLabel}</Button>
    </form>
  );
}

export function AcceptInvite() {
  const { t, i18n } = useTranslation();
  const { token = "" } = useParams();
  const check = useQuery({ queryKey: ["token", token],
    queryFn: () => unwrap(api.GET("/api/v1/auth/tokens/{token}", { params: { path: { token } } })) });
  const action = useMutation({ mutationFn: (password: string) =>
    unwrap(api.POST("/api/v1/auth/invitations/accept", { body: { token, password } })) });
  if (check.isLoading) return <Loading />;
  const info = check.data;
  return (
    <Card title={t("invite.title")}>
      {info && (!info.valid || info.purpose !== "invitation") ? (
        <Notice tone="warning">{t(`link.${info.reason ?? "invalid"}`)}</Notice>
      ) : action.isSuccess ? (
        <>
          <Notice tone="success">{t("invite.done")}</Notice>
          <Link to="/login" className="mt-4 inline-block font-semibold">{t("register.to_login")}</Link>
        </>
      ) : (
        <>
          {info && (
            <p className="mb-4 text-sm text-ink-muted">
              {t("invite.for", { name: info.name_en ? nameOf({ name_en: info.name_en, name_ar: info.name_ar ?? "" },
                i18n.language) : "", email: info.email })}
            </p>
          )}
          <PasswordForm submitLabel={t("invite.submit")} busy={action.isPending} error={action.error}
            onSubmit={(p) => action.mutate(p)} />
        </>
      )}
    </Card>
  );
}

export function ForgotPassword() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const action = useMutation({ mutationFn: () =>
    unwrap(api.POST("/api/v1/auth/password/forgot", { body: { email: email.trim() } })) });
  return (
    <Card title={t("forgot.title")}>
      {action.isSuccess ? (
        <Notice tone="success">{t("forgot.done")}</Notice>
      ) : (
        <form className="flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); action.mutate(); }} noValidate>
          <ErrorBox error={action.error} />
          <Input label={t("field.email")} type="email" dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Button type="submit" busy={action.isPending}>{t("forgot.submit")}</Button>
        </form>
      )}
      <Link to="/login" className="mt-4 inline-block text-sm">{t("register.to_login")}</Link>
    </Card>
  );
}

export function ResetPassword() {
  const { t } = useTranslation();
  const { token = "" } = useParams();
  const action = useMutation({ mutationFn: (password: string) =>
    unwrap(api.POST("/api/v1/auth/password/reset", { body: { token, password } })) });
  return (
    <Card title={t("reset.title")}>
      {action.isSuccess ? (
        <>
          <Notice tone="success">{t("reset.done")}</Notice>
          <Link to="/login" className="mt-4 inline-block font-semibold">{t("register.to_login")}</Link>
        </>
      ) : (
        <PasswordForm submitLabel={t("reset.submit")} busy={action.isPending} error={action.error}
          onSubmit={(p) => action.mutate(p)} />
      )}
    </Card>
  );
}
