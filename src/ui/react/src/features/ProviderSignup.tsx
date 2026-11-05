import { useEffect, useState, type FormEvent } from "react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { loadSession, signedOut } from "../app/store";
import { request } from "../app/client";
import { Button, Field, Input, Badge } from "../components/ui";
interface Portal {
  company_name: string;
  capability_options: string[];
  programs: { Id: number; ProgramName: string }[];
}
interface ApplicationStatus extends Portal {
  Id: number;
  Version: number;
  LegalName: string;
  RegistrationJurisdiction: string;
  BusinessRegistrationNumber: string;
  ContactName: string;
  ContactEmail: string;
  ContactPhone: string;
  OutletName: string;
  OutletAddress: string;
  Website: string;
  ApplicantEvidenceReferences: string;
  capabilities: string[];
  program_ids: number[];
  State: string;
  decision: string;
  review_note: string;
  activation_available: boolean;
}
export function ApplicationForm({
  portal,
  application,
  onSubmit,
  busy,
}: {
  portal: Portal;
  application?: ApplicationStatus;
  onSubmit: (data: Record<string, unknown>) => void;
  busy: boolean;
}) {
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    onSubmit({
      ...Object.fromEntries(form),
      capabilities: form.getAll("capabilities"),
      program_ids: form.getAll("program_ids").map(Number),
    });
  }
  return (
    <form onSubmit={submit} className="public-signup-form">
      <div className="form-row">
        <Field label="Legal business name" id="signup-legal">
          <Input
            id="signup-legal"
            name="legal_name"
            defaultValue={application?.LegalName}
            required
            maxLength={200}
          />
        </Field>
        <Field label="Registration jurisdiction" id="signup-jurisdiction">
          <Input
            id="signup-jurisdiction"
            name="jurisdiction"
            defaultValue={application?.RegistrationJurisdiction}
            required
            maxLength={50}
          />
        </Field>
      </div>
      <Field label="Business registration number" id="signup-registration">
        <Input
          id="signup-registration"
          name="registration"
          defaultValue={application?.BusinessRegistrationNumber}
          required
          maxLength={100}
        />
      </Field>
      <div className="form-row">
        <Field label="Contact name" id="signup-name">
          <Input
            id="signup-name"
            name="contact_name"
            defaultValue={application?.ContactName}
            required
            maxLength={200}
          />
        </Field>
        <Field label="Contact email" id="signup-email">
          <Input
            id="signup-email"
            name="contact_email"
            type="email"
            defaultValue={application?.ContactEmail}
            required
            maxLength={254}
          />
        </Field>
      </div>
      <div className="form-row">
        <Field label="Contact phone" id="signup-phone">
          <Input
            id="signup-phone"
            name="contact_phone"
            type="tel"
            defaultValue={application?.ContactPhone}
            required
            maxLength={40}
          />
        </Field>
        <Field label="Website (optional)" id="signup-website">
          <Input
            id="signup-website"
            name="website"
            type="url"
            defaultValue={application?.Website}
            maxLength={300}
            placeholder="https://"
          />
        </Field>
      </div>
      <Field label="Outlet name" id="signup-outlet">
        <Input
          id="signup-outlet"
          name="outlet_name"
          defaultValue={application?.OutletName}
          required
          maxLength={200}
        />
      </Field>
      <Field label="Outlet address" id="signup-address">
        <Input
          id="signup-address"
          name="outlet_address"
          defaultValue={application?.OutletAddress}
          required
          maxLength={500}
        />
      </Field>
      <fieldset className="capability-options">
        <legend>Requested services</legend>
        {portal.capability_options.map((code) => (
          <label key={code}>
            <input
              type="checkbox"
              name="capabilities"
              value={code}
              defaultChecked={application?.capabilities.includes(code)}
            />
            {code}
          </label>
        ))}
      </fieldset>
      {portal.programs.length > 0 && (
        <fieldset className="capability-options">
          <legend>Requested incentive programs</legend>
          {portal.programs.map((p) => (
            <label key={p.Id}>
              <input
                type="checkbox"
                name="program_ids"
                value={p.Id}
                defaultChecked={
                  application ? application.program_ids.includes(p.Id) : true
                }
              />
              {p.ProgramName}
            </label>
          ))}
        </fieldset>
      )}
      <Field
        label="Supporting evidence references"
        id="signup-evidence"
        hint="Provide registration, contact-authority and capability document references. Do not enter passwords or sensitive document contents."
      >
        <textarea
          id="signup-evidence"
          name="supporting_evidence"
          className="textarea"
          defaultValue={application?.ApplicantEvidenceReferences}
          required
          maxLength={2000}
          rows={3}
        />
      </Field>
      <p className="scope-footnote">
        Your company operator reviews the application. Provider login access
        becomes available only after acceptance.
      </p>
      <Button type="submit" variant="primary" loading={busy}>
        {application
          ? "Submit changes for review"
          : "Submit application for review"}
      </Button>
    </form>
  );
}
export default function ProviderSignup() {
  const [code, setCode] = useState(
    () =>
      new URLSearchParams(location.hash.split("?")[1] ?? "").get("code") ?? "",
  );
  const [portal, setPortal] = useState<Portal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tracking, setTracking] = useState("");
  const [reference, setReference] = useState("");
  const csrf = useAppSelector((s) => s.session.data?.csrf ?? "");
  async function openPortal() {
    setBusy(true);
    setError("");
    try {
      setPortal(
        await request<Portal>(
          "/api/public/provider-signup?code=" + encodeURIComponent(code),
        ),
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Company signup is unavailable",
      );
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (code) openPortal();
  }, []);
  async function submit(data: Record<string, unknown>) {
    setBusy(true);
    setError("");
    try {
      const response = await request<{
        tracking_token: string;
        application_reference: string;
      }>("/api/public/provider-submit", { ...data, code }, csrf);
      setTracking(
        location.origin +
          "/#provider-application?token=" +
          encodeURIComponent(response.tracking_token),
      );
      setReference(response.application_reference);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Application could not be submitted",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="public-portal">
      <section className="public-card">
        <a href="#" className="loading-wordmark">
          Retail-Mesh
        </a>
        <h1>Provider signup</h1>
        <p>
          Apply to provide vehicle retail, rental or service operations within a
          company network.
        </p>
        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
        {tracking ? (
          <div role="status">
            <Badge tone="positive">Submitted</Badge>
            <h2>Application {reference}</h2>
            <p>
              Save this private link to track the operator’s review and submit
              any requested changes. No account or email has been created or
              sent.
            </p>
            <Input
              aria-label="Private application tracking link"
              readOnly
              value={tracking}
            />
            <div className="button-row">
              <Button asChild variant="primary">
                <a href={tracking}>Track my application</a>
              </Button>
              <Button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(tracking);
                  } catch {
                    setError("Copy the displayed tracking link manually.");
                  }
                }}
              >
                Copy private link
              </Button>
            </div>
          </div>
        ) : portal ? (
          <>
            <h2>{portal.company_name}</h2>
            <ApplicationForm portal={portal} onSubmit={submit} busy={busy} />
          </>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              openPortal();
            }}
          >
            <Field
              label="Company signup code"
              id="public-company-code"
              hint="Ask the company operator for the signup link or code."
            >
              <Input
                id="public-company-code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                maxLength={100}
              />
            </Field>
            <Button type="submit" variant="primary" loading={busy}>
              Open company signup
            </Button>
          </form>
        )}
        <p className="scope-footnote">
          <a href="#">Already onboarded? Sign in</a>
        </p>
      </section>
    </main>
  );
}
export function ProviderApplicationStatus() {
  const dispatch = useAppDispatch();
  const auth = useAppSelector((s) => s.session.data);
  const csrf = auth?.csrf ?? "";
  const [token] = useState(
    () =>
      new URLSearchParams(location.hash.split("?")[1] ?? "").get("token") ?? "",
  );
  const [application, setApplication] = useState<ApplicationStatus | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function refresh() {
    setBusy(true);
    setError("");
    try {
      setApplication(
        await request<ApplicationStatus>(
          "/api/public/provider-status",
          { token },
          csrf,
        ),
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Application status is unavailable",
      );
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    history.replaceState(null, "", location.pathname + "#provider-application");
    if (token) refresh();
    else
      setError(
        "Open the full private application link you saved after submission.",
      );
  }, []);
  async function resubmit(data: Record<string, unknown>) {
    setBusy(true);
    setError("");
    try {
      await request(
        "/api/public/provider-resubmit",
        { ...data, token, version: application?.Version },
        csrf,
      );
      await refresh();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Changes could not be submitted",
      );
    } finally {
      setBusy(false);
    }
  }
  async function activate(e: FormEvent<HTMLFormElement>) {
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
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Activation failed");
    } finally {
      setBusy(false);
    }
  }
  async function signin() {
    try {
      if (auth?.user) await request("/api/auth/logout", {}, csrf);
      dispatch(signedOut);
      location.hash = "";
      await dispatch(loadSession());
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not sign out the current session",
      );
    }
  }
  return (
    <main className="public-portal">
      <section className="public-card">
        <span className="loading-wordmark">Retail-Mesh</span>
        <h1>My provider application</h1>
        {error && (
          <p role="alert" className="inline-error">
            {error}
          </p>
        )}
        {application && (
          <>
            <div className="application-status-heading">
              <div>
                <h2>{application.LegalName}</h2>
                <p>
                  {application.company_name} · APP-{application.Id}
                </p>
              </div>
              <Badge
                tone={
                  application.State === "Rejected"
                    ? "negative"
                    : application.State === "Provisioned"
                      ? "positive"
                      : "neutral"
                }
              >
                {application.decision}
              </Badge>
            </div>
            {application.review_note && (
              <div className="review-note">
                <strong>Operator review</strong>
                <p>{application.review_note}</p>
              </div>
            )}
            {application.State === "NeedsChanges" ? (
              <ApplicationForm
                key={application.Version}
                portal={application}
                application={application}
                onSubmit={resubmit}
                busy={busy}
              />
            ) : application.State === "Approved" ? (
              application.activation_available ? (
                <form onSubmit={activate}>
                  <h3>Activate your provider account</h3>
                  <Field
                    label="Password"
                    id="accepted-password"
                    hint="New account: choose 12–256 characters. Existing account: enter your current password."
                  >
                    <Input
                      id="accepted-password"
                      name="password"
                      type="password"
                      required
                      minLength={12}
                      maxLength={256}
                      autoComplete="off"
                    />
                  </Field>
                  <Button type="submit" variant="primary" loading={busy}>
                    Activate accepted provider account
                  </Button>
                </form>
              ) : (
                <p>
                  The application is accepted. Ask the operator to reissue
                  activation access if your link has expired.
                </p>
              )
            ) : application.State === "Provisioned" ? (
              <>
                <p>
                  Your account is active. Sign in to view your own dashboard,
                  claims and incentive assistant.
                </p>
                <Button variant="primary" onClick={signin}>
                  Sign in to my dashboard
                </Button>
              </>
            ) : (
              <p>
                {application.State === "Rejected"
                  ? "The operator has rejected this application. Review the explanation above."
                  : "Your application is awaiting the company operator’s review. Changes and decisions will appear here."}
              </p>
            )}
            <Button loading={busy} onClick={refresh}>
              Refresh application status
            </Button>
          </>
        )}
      </section>
    </main>
  );
}
