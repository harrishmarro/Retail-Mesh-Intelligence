import { useEffect, useState, type FormEvent } from "react";
import { KeyRound, Database } from "lucide-react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { actions, loadSession, signedOut } from "../app/store";
import { request } from "../app/client";
import { Button, Field, Input, Panel } from "../components/ui";
export function ChangePassword() {
  const dispatch = useAppDispatch();
  const csrf = useAppSelector((s) => s.session.data?.csrf ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    if (values.new_password !== values.confirm_password) {
      setError("New passwords must match.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await request(
        "/api/auth/change-password",
        {
          current_password: values.current_password,
          new_password: values.new_password,
        },
        csrf,
      );
      form.reset();
      dispatch(signedOut);
      location.hash = "";
      await dispatch(loadSession());
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Password could not be changed",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <Panel
      title="Change your password"
      description="Verify your current password, then choose a new one. All sessions, including this one, will be signed out."
    >
      <form className="account-password-form" onSubmit={submit}>
        <Field label="Current password" id="current-password">
          <Input
            id="current-password"
            name="current_password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={256}
          />
        </Field>
        <Field
          label="New password"
          id="new-password"
          hint="Use 12–256 characters, different from your current password."
        >
          <Input
            id="new-password"
            name="new_password"
            type="password"
            autoComplete="new-password"
            required
            minLength={12}
            maxLength={256}
          />
        </Field>
        <Field label="Confirm new password" id="confirm-password">
          <Input
            id="confirm-password"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            required
            minLength={12}
            maxLength={256}
          />
        </Field>
        {error && (
          <p role="alert" className="inline-error">
            {error}
          </p>
        )}
        <Button type="submit" loading={busy}>
          <KeyRound size={15} />
          Change password and sign out
        </Button>
      </form>
    </Panel>
  );
}
export function ImportDataset() {
  const dispatch = useAppDispatch();
  const auth = useAppSelector((s) => s.session.data)!;
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function run() {
    setBusy(true);
    setError("");
    try {
      const result = await request<{
        replayed: boolean;
        company_ids: number[];
      }>("/api/workspace/import-csv", { company_id: companyId }, auth.csrf);
      await dispatch(loadSession()).unwrap();
      setMessage(
        `${result.replayed ? "Dataset already imported; no duplicate rows added." : "Dataset imported."} Use the company selector to open its companies.`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Panel
      title="Supplied CSV dataset"
      description="Import the bundled RetailMesh_CSV_Files.zip into this local installation. Existing rows are preserved."
    >
      <p className="scope-footnote">
        The dataset contains two companies. Access is granted to the importing
        administrator only for unclaimed dataset companies, or retained where
        they already administer them. Imported records remain synthetic and
        preserve their source decisions.
      </p>
      <Button loading={busy} onClick={run}>
        <Database size={15} />
        Import supplied dataset
      </Button>
      {message && (
        <p role="status" className="scope-footnote">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="inline-error">
          {error}
        </p>
      )}
    </Panel>
  );
}
export function ActivateProvider() {
  const dispatch = useAppDispatch();
  const signedIn = useAppSelector((s) => !!s.session.data?.user);
  const csrf = useAppSelector((s) => s.session.data?.csrf ?? "");
  const [token] = useState(
    () =>
      new URLSearchParams(location.hash.split("?")[1] ?? "").get("token") ?? "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  useEffect(() => {
    history.replaceState(null, "", location.pathname + "#activate");
  }, []);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setBusy(true);
    setError("");
    try {
      await request(
        "/api/auth/activate-provider",
        { token, password: new FormData(form).get("password") },
        csrf,
      );
      form.reset();
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Activation failed");
    } finally {
      setBusy(false);
    }
  }
  async function goToSignIn() {
    setBusy(true);
    setError("");
    try {
      if (signedIn) await request("/api/auth/logout", {}, csrf);
      dispatch(signedOut);
      location.hash = "";
      await dispatch(loadSession());
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not sign out the current session",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="activation-page">
      <div className="activation-card">
        <span className="loading-wordmark">Retail-Mesh</span>
        <h1>Activate provider access</h1>
        {done ? (
          <>
            {error && (
              <p role="alert" className="inline-error">
                {error}
              </p>
            )}
            <p>
              Your provider access is active. Sign in with your contact email
              and password.
            </p>
            <Button variant="primary" loading={busy} onClick={goToSignIn}>
              Go to sign in
            </Button>
          </>
        ) : (
          <>
            <p>
              Use the single-use link issued after company approval. New users
              choose a password; existing users enter their current account
              password. Existing passwords are never reset by activation.
            </p>
            <form onSubmit={submit}>
              <Field
                label="Password"
                id="activation-password"
                hint="New account: 12–256 characters. Existing account: your current password."
              >
                <Input
                  id="activation-password"
                  name="password"
                  type="password"
                  autoComplete="off"
                  minLength={12}
                  maxLength={256}
                  required
                  disabled={!token}
                />
              </Field>
              {!token && (
                <p role="alert">
                  Open the full activation link from your company administrator.
                </p>
              )}
              {error && (
                <p role="alert" className="inline-error">
                  {error}
                </p>
              )}
              <Button
                variant="primary"
                type="submit"
                disabled={!token}
                loading={busy}
              >
                Activate provider access
              </Button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}

export function ProviderSignupSettings() {
  const auth = useAppSelector((s) => s.session.data);
  const cid = useAppSelector((s) => s.workspace.companyId);
  const [enabled, setEnabled] = useState(false);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    if (cid)
      request<{ enabled: boolean; public_code: string | null }>(
        `/api/workspace/provider-signup?company_id=${cid}`,
      )
        .then((value) => {
          if (live) {
            setEnabled(value.enabled);
            setCode(value.public_code ?? "");
          }
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    return () => {
      live = false;
    };
  }, [cid]);
  async function change() {
    setBusy(true);
    setError("");
    try {
      const value = await request<{ enabled: boolean; public_code: string }>(
        "/api/workspace/provider-signup",
        { company_id: cid, enabled: !enabled },
        auth?.csrf,
      );
      setEnabled(value.enabled);
      setCode(value.public_code);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not configure provider signup",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <Panel
      title="Provider signup page"
      description="Enable a separate public application page for this company. Operators review submissions before provider account access is granted."
    >
      <div className="signup-link-well">
        <Button loading={busy} onClick={change}>
          {enabled
            ? "Disable new provider applications"
            : "Enable provider signup"}
        </Button>
        {enabled && code && (
          <>
            <Field label="Public provider signup link" id="signup-share">
              <Input
                id="signup-share"
                readOnly
                value={
                  location.origin +
                  "/#provider-signup?code=" +
                  encodeURIComponent(code)
                }
              />
            </Field>
            <p className="field-hint">
              Share this public application link with providers. Applicant
              tracking links are private and are issued only to the applicant.
            </p>
          </>
        )}
        {error && (
          <p role="alert" className="inline-error">
            {error}
          </p>
        )}
      </div>
    </Panel>
  );
}
