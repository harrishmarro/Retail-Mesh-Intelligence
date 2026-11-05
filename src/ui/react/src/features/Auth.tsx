import { useState, type FormEvent } from "react";
import { ArrowRight, ShieldCheck, Network, Route } from "lucide-react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { loadSession } from "../app/store";
import { request } from "../app/client";
import { Button, Field, Input } from "../components/ui";
export function Brand() {
  return (
    <span className="brand">
      <svg
        width="29"
        height="29"
        viewBox="0 0 29 29"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M5 7.5L14.5 3L24 7.5V20.5L14.5 26L5 20.5V7.5Z"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path
          d="M5 7.5L14.5 13L24 7.5M14.5 13V26M5 20.5L24 7.5"
          stroke="currentColor"
          strokeWidth="1.5"
        />
      </svg>
      <span>
        Retail-Mesh<span className="brand-sub">Intelligence</span>
      </span>
    </span>
  );
}
export default function Auth() {
  const dispatch = useAppDispatch();
  const auth = useAppSelector((s) => s.session.data);
  const setup = !!auth?.needs_setup;
  const [manageImported, setManageImported] = useState(
    !!auth?.imported_company_count,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    setBusy(true);
    setError("");
    try {
      await request(
        setup ? "/api/auth/setup" : "/api/auth/login",
        values,
        auth?.csrf,
      );
      form.reset();
      await dispatch(loadSession()).unwrap();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <aside className="auth-story">
        <Brand />
        <div className="auth-story-copy">
          <span className="auth-caption">Connected vehicle operations</span>
          <h2>
            Every activity.
            <br />
            One clear picture.
          </h2>
          <p>
            Bring your provider network, vehicle journeys and incentive evidence
            into the same company workspace.
          </p>
          <div className="auth-route">
            <div>
              <Route size={18} />
              <span>Sale & service</span>
            </div>
            <span className="route-connector" />
            <div>
              <Network size={18} />
              <span>Verified evidence</span>
            </div>
            <span className="route-connector" />
            <div>
              <ShieldCheck size={18} />
              <span>Explainable award</span>
            </div>
          </div>
        </div>
        <p className="auth-footer">Retail-Mesh operations workspace</p>
      </aside>
      <main className="auth-main">
        <div className="auth-form-wrap">
          <span className="mobile-brand">
            <Brand />
          </span>
          <div className="form-heading">
            <h1>
              {setup ? "Create your workspace" : "Sign in to Retail-Mesh"}
            </h1>
            <p>
              {setup
                ? "Set up your local company account to get started."
                : "Continue to your company’s operations workspace."}
            </p>
          </div>
          <form onSubmit={submit}>
            <Field label="Email address" id="email">
              <Input
                id="email"
                type="email"
                name="email"
                autoComplete="username"
                required
                maxLength={254}
                placeholder="you@company.com"
              />
            </Field>
            <Field
              label="Password"
              id="password"
              hint={setup ? "Use 12–256 characters." : ""}
            >
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete={setup ? "new-password" : "current-password"}
                minLength={12}
                maxLength={256}
                required
              />
            </Field>
            {setup && (
              <>
                <Field label="Full name" id="display-name">
                  <Input
                    id="display-name"
                    name="display_name"
                    autoComplete="name"
                    required
                    maxLength={200}
                  />
                </Field>
                {!!auth?.imported_company_count && (
                  <label className="setup-imported-choice">
                    <input
                      type="checkbox"
                      name="manage_imported"
                      checked={manageImported}
                      onChange={(e) => setManageImported(e.target.checked)}
                    />
                    <span>
                      Start with the {auth.imported_company_count} supplied
                      companies, without creating another company
                    </span>
                  </label>
                )}
                {!manageImported && (
                  <>
                    <div className="form-divider">Company details</div>
                    <Field label="Company legal name" id="company-name">
                      <Input
                        id="company-name"
                        name="company_name"
                        required
                        maxLength={200}
                      />
                    </Field>
                    <div className="form-row">
                      <Field
                        label="Registration jurisdiction"
                        id="jurisdiction"
                      >
                        <Input
                          id="jurisdiction"
                          name="jurisdiction"
                          required
                          maxLength={50}
                          placeholder="e.g. CA-BC"
                        />
                      </Field>
                      <Field label="Business registration" id="registration">
                        <Input
                          id="registration"
                          name="registration"
                          required
                          maxLength={100}
                        />
                      </Field>
                    </div>
                  </>
                )}
                <p className="field-hint">
                  The first administrator receives access to the supplied
                  dataset companies. For a local demonstration, use clearly
                  fictional company details, jurisdiction DEMO and a SYNTHETIC
                  registration reference.
                </p>
              </>
            )}
            {error && (
              <p role="alert" className="inline-error">
                {error}
              </p>
            )}
            <Button
              variant="primary"
              type="submit"
              className="auth-submit"
              loading={busy}
            >
              {setup ? "Create workspace" : "Sign in"}
              <ArrowRight size={16} />
            </Button>
          </form>
          <div className="auth-security">
            <ShieldCheck size={15} />
            <span>Company-scoped access. Your session stays private.</span>
          </div>
          <p className="auth-local-note">
            <a href="#provider-signup">
              New provider? Open the separate signup page
            </a>
          </p>
          <p className="auth-local-note">
            Local development application. No account or password is
            preconfigured.
          </p>
        </div>
      </main>
    </div>
  );
}
