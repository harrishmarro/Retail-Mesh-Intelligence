import { useEffect, useState, type FormEvent } from "react";
import { Copy, Check, KeyRound } from "lucide-react";
import { useWorkspaceResource } from "../app/resources";
import { useCommand } from "../app/commands";
import { useAppSelector } from "../app/hooks";
import type { ApplicationsDocument, ProviderApplication } from "../app/types";
import {
  Button,
  Panel,
  Field,
  Input,
  Badge,
  Empty,
  Skeleton,
} from "../components/ui";
function stateLabel(state: string) {
  return (
    (
      {
        Approved: "Accepted",
        NeedsChanges: "Changes needed",
        Provisioned: "Account active",
      } as Record<string, string>
    )[state] ?? state
  );
}
export default function ProviderOnboarding() {
  const resource = useWorkspaceResource<ApplicationsDocument>("applications");
  const command = useCommand();
  const [selected, setSelected] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [programs, setPrograms] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [invite, setInvite] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const data = resource.data;
  const app =
    data?.applications.find((a) => a.Id === selected) ?? data?.applications[0];
  const role = useAppSelector(
    (s) =>
      s.session.data?.workspaces.find(
        (c) => c.company_id === s.workspace.companyId,
      )?.Role,
  );
  useEffect(() => {
    setNote("");
    setInvite(null);
    setPrograms(
      app?.RequestedProgramsJson ? JSON.parse(app.RequestedProgramsJson) : [],
    );
  }, [app?.Id]);
  async function perform(path: string, payload: Record<string, unknown>) {
    setBusy(true);
    setError("");
    try {
      const result = await command(path, path, payload);
      resource.reload();
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review action failed");
      return null;
    } finally {
      setBusy(false);
    }
  }
  async function start() {
    if (app)
      await perform("/api/workspace/application-transition", {
        application_id: app.Id,
        version: app.Version,
        state: "UnderReview",
      });
  }
  async function decide(decision: string) {
    if (!app) return;
    const result = await perform("/api/workspace/review-provider-application", {
      application_id: app.Id,
      version: app.Version,
      decision,
      note,
      program_ids: programs,
    });
    if (result) setNote("");
  }
  async function check(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!app) return;
    const form = e.currentTarget;
    const result = await perform("/api/workspace/application-check", {
      application_id: app.Id,
      version: app.Version,
      ...Object.fromEntries(new FormData(form)),
    });
    if (result) form.reset();
  }
  async function reissue() {
    if (!app) return;
    const result = (await perform("/api/workspace/application-invite", {
      application_id: app.Id,
      version: app.Version,
    })) as { token: string } | null;
    if (result)
      setInvite(
        location.origin +
          "/#activate?token=" +
          encodeURIComponent(result.token),
      );
  }
  const signupUrl =
    data?.signup?.enabled && data.signup.public_code
      ? location.origin +
        "/#provider-signup?code=" +
        encodeURIComponent(data.signup.public_code)
      : "";
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Provider applications</h1>
          <p>
            Company-operator review of applications submitted from the separate
            provider signup page.
          </p>
        </div>
      </div>
      <Panel
        title="Provider signup page"
        description="Providers submit their own business details. No provider master record or account exists before acceptance."
      >
        {signupUrl ? (
          <div className="signup-link-well">
            <Input
              aria-label="Public provider signup link"
              readOnly
              value={signupUrl}
            />
            <div className="button-row">
              <Button asChild>
                <a href={signupUrl} target="_blank" rel="noreferrer">
                  Open provider signup
                </a>
              </Button>
              <Button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(signupUrl);
                    setCopied(true);
                  } catch {
                    setError("Copy the displayed signup link manually.");
                  }
                }}
              >
                <Copy size={14} />
                {copied ? "Copied" : "Copy signup link"}
              </Button>
            </div>
          </div>
        ) : (
          <p className="scope-footnote">
            {role === "CompanyAdmin"
              ? "Enable the provider signup page in Workspace settings to receive applications."
              : "Ask the company administrator to enable the provider signup page."}
          </p>
        )}
      </Panel>
      {(error || resource.error) && (
        <p role="alert" className="inline-error">
          {error || resource.error?.message}
        </p>
      )}
      {resource.phase === "loading" && !data ? (
        <Skeleton rows={4} />
      ) : (
        <div className="onboarding-layout">
          <section className="panel application-list">
            <div className="panel-header">
              <h2>Applications</h2>
              <span>{data?.applications.length ?? 0}</span>
            </div>
            {data?.applications.length ? (
              data.applications.map((a) => (
                <button
                  className={
                    "knowledge-node" +
                    (app?.Id === a.Id ? " knowledge-node-selected" : "")
                  }
                  key={a.Id}
                  onClick={() => setSelected(a.Id)}
                >
                  <span>
                    <strong>{a.LegalName}</strong>
                    <small>
                      APP-{a.Id} · {a.ContactEmail}
                    </small>
                  </span>
                  <Badge
                    tone={
                      a.State === "Provisioned"
                        ? "positive"
                        : a.State === "Rejected"
                          ? "negative"
                          : "neutral"
                    }
                  >
                    {stateLabel(a.State)}
                  </Badge>
                </button>
              ))
            ) : (
              <Empty
                title="No submitted applications"
                description="Share the signup link with providers. Submitted applications will appear here."
              />
            )}
          </section>
          {app ? (
            <div>
              <Panel
                title={app.LegalName}
                description={`APP-${app.Id} · version ${app.Version}`}
                action={<Badge>{stateLabel(app.State)}</Badge>}
              >
                <dl className="knowledge-properties">
                  <div>
                    <dt>Business registration</dt>
                    <dd>
                      {app.RegistrationJurisdiction} ·{" "}
                      {app.BusinessRegistrationNumber}
                    </dd>
                  </div>
                  <div>
                    <dt>Contact</dt>
                    <dd>
                      {app.ContactName} · {app.ContactEmail}
                      <br />
                      {app.ContactPhone}
                    </dd>
                  </div>
                  <div>
                    <dt>Outlet</dt>
                    <dd>
                      {app.OutletName} · {app.OutletAddress}
                    </dd>
                  </div>
                  <div>
                    <dt>Requested capabilities</dt>
                    <dd>{app.capabilities.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Applicant evidence references</dt>
                    <dd>
                      {app.ApplicantEvidenceReferences ||
                        "Legacy application; no applicant-supplied references"}
                    </dd>
                  </div>
                  <div>
                    <dt>Provider record</dt>
                    <dd>
                      {app.ProviderId
                        ? "PR-" + app.ProviderId
                        : "Not inserted; application under review"}
                    </dd>
                  </div>
                </dl>
                {app.ReviewNote && (
                  <div className="review-note">
                    <strong>Last operator review</strong>
                    <p>{app.ReviewNote}</p>
                  </div>
                )}
                <h3 className="knowledge-relations-heading">
                  Validation checks
                </h3>
                <div className="validation-checks">
                  {Object.entries(data?.check_definitions ?? {}).map(
                    ([code, label]) => {
                      const evidence = app.checks.find(
                        (c) => c.CheckCode === code,
                      );
                      return (
                        <div key={code}>
                          <span
                            className={
                              evidence
                                ? "check-indicator check-pass"
                                : "check-indicator"
                            }
                          >
                            {evidence ? <Check size={13} /> : <span>—</span>}
                          </span>
                          <div>
                            <strong>{label}</strong>
                            <p>
                              {evidence?.EvidenceReference ??
                                "Not yet validated"}
                            </p>
                          </div>
                        </div>
                      );
                    },
                  )}
                </div>
                {app.State === "Submitted" && (
                  <div className="workflow-actions">
                    <Button variant="primary" loading={busy} onClick={start}>
                      Start application review
                    </Button>
                  </div>
                )}
                {app.State === "UnderReview" && (
                  <>
                    <form className="review-form" onSubmit={check}>
                      <Field label="Validation check" id="check-code">
                        <select
                          id="check-code"
                          name="check_code"
                          className="input"
                        >
                          {Object.entries(data?.check_definitions ?? {}).map(
                            ([code, label]) => (
                              <option key={code} value={code}>
                                {label}
                              </option>
                            ),
                          )}
                        </select>
                      </Field>
                      <Field
                        label="Reviewed evidence reference"
                        id="check-evidence"
                      >
                        <Input
                          id="check-evidence"
                          name="evidence_reference"
                          required
                          maxLength={500}
                        />
                      </Field>
                      <Button loading={busy} type="submit">
                        Record validated evidence
                      </Button>
                    </form>
                    <div className="review-form">
                      <fieldset className="capability-options">
                        <legend>Programs to enrol on acceptance</legend>
                        {(data?.program_options ?? []).map((p) => (
                          <label key={p.Id}>
                            <input
                              type="checkbox"
                              checked={programs.includes(p.Id)}
                              onChange={(e) =>
                                setPrograms(
                                  e.target.checked
                                    ? [...programs, p.Id]
                                    : programs.filter((id) => id !== p.Id),
                                )
                              }
                            />
                            {p.ProgramName}
                          </label>
                        ))}
                        {!data?.program_options?.length && (
                          <p>No active programs in this company.</p>
                        )}
                      </fieldset>
                      <Field
                        label="Operator review explanation"
                        id="operator-review"
                      >
                        <textarea
                          id="operator-review"
                          className="textarea"
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          maxLength={500}
                          required
                          rows={3}
                        />
                      </Field>
                      <div className="button-row">
                        <Button
                          variant="primary"
                          loading={busy}
                          disabled={app.checks.length !== 3 || !note.trim()}
                          onClick={() => decide("Accepted")}
                        >
                          Accept application
                        </Button>
                        <Button
                          loading={busy}
                          disabled={!note.trim()}
                          onClick={() => decide("Changes needed")}
                        >
                          Changes needed
                        </Button>
                        <Button
                          variant="danger"
                          loading={busy}
                          disabled={!note.trim()}
                          onClick={() => decide("Rejected")}
                        >
                          Reject application
                        </Button>
                      </div>
                      <p className="scope-footnote">
                        Acceptance requires all three validation checks. The
                        review explanation is visible to the applicant. Actual
                        business verification is performed by the operator.
                      </p>
                    </div>
                  </>
                )}
                {app.State === "NeedsChanges" && (
                  <p className="scope-footnote">
                    The provider can correct and resubmit from the private
                    application status page.
                  </p>
                )}
                {app.State === "Approved" && (
                  <div className="review-form">
                    <p>
                      The application is accepted. The applicant can choose a
                      password from the private status link within 48 hours.
                    </p>
                    <Button loading={busy} onClick={reissue}>
                      <KeyRound size={15} />
                      Reissue activation link
                    </Button>
                    {invite && (
                      <>
                        <p className="field-hint">
                          Share this replacement link privately. No email was
                          sent.
                        </p>
                        <Input
                          aria-label="Replacement activation link"
                          readOnly
                          value={invite}
                        />
                      </>
                    )}
                  </div>
                )}
                {app.State === "Provisioned" && (
                  <p className="scope-footnote">
                    Provider login is active with access to its own dashboard,
                    claims, chatbot and concerns.
                  </p>
                )}
              </Panel>
              <Panel
                title="Application history"
                description="Submission and operator-review actions are retained."
              >
                <ol className="application-history">
                  {app.history.map((h) => (
                    <li key={h.Id}>
                      <span>
                        {h.Action.replace("provider.", "").replaceAll("_", " ")}
                      </span>
                      <small>
                        {h.UserId
                          ? "User #" + h.UserId
                          : "Applicant submission"}{" "}
                        · {new Date(h.CreatedAt * 1000).toLocaleString()}
                      </small>
                    </li>
                  ))}
                </ol>
              </Panel>
            </div>
          ) : (
            <Empty
              title="Select a submitted application"
              description="Review the provider’s details, validate evidence and record your decision."
            />
          )}
        </div>
      )}
    </>
  );
}
