import { useState, type FormEvent } from "react";
import { Plus, Send, MessageCircle } from "lucide-react";
import { useWorkspaceResource } from "../app/resources";
import { useCommand } from "../app/commands";
import { useAppSelector } from "../app/hooks";
import { request } from "../app/client";
import type { ClaimDocument, ClaimRecord, ConcernDocument } from "../app/types";
import {
  Button,
  Panel,
  Dialog,
  Field,
  Input,
  Badge,
  Empty,
  Skeleton,
} from "../components/ui";
const label = (s: string) =>
  s === "ChangesNeeded"
    ? "Changes needed"
    : s === "UnderReview"
      ? "Under review"
      : s;
export function Claims() {
  const resource = useWorkspaceResource<ClaimDocument>("claims");
  const command = useCommand();
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState<ClaimRecord | null>(null);
  const [ruleId, setRuleId] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const data = resource.data;
  const own = data?.role === "Provider";
  const row = data?.claims.find((c) => c.Id === selected) ?? data?.claims[0];
  const options = data?.options;
  const rule = options?.rules.find((r) => String(r.Id) === ruleId);
  async function perform(path: string, payload: Record<string, unknown>) {
    setBusy(true);
    setError("");
    try {
      const result = await command(path, path, payload);
      resource.reload();
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Claim action failed");
      return null;
    } finally {
      setBusy(false);
    }
  }
  function startForm(claim: ClaimRecord | null) {
    setEdit(claim);
    setRuleId(
      String(
        claim?.IncentiveRuleId ??
          options?.rules.find((r) => r.AssessmentBasis === "Period")?.Id ??
          options?.rules[0]?.Id ??
          "",
      ),
    );
    setError("");
    setOpen(true);
  }
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const result = (await perform("/api/workspace/claims", {
      ...Object.fromEntries(new FormData(e.currentTarget)),
      ...(edit ? { claim_id: edit.Id, version: edit.Version } : {}),
    })) as { claim_id: number } | null;
    if (result) {
      setSelected(result.claim_id);
      setOpen(false);
    }
  }
  async function decide(status: string) {
    if (!row) return;
    const result = await perform("/api/workspace/review-claim", {
      claim_id: row.Id,
      version: row.Version,
      status,
      note:
        status === "UnderReview" ? "Review started by company operator" : note,
    });
    if (result) setNote("");
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{own ? "My incentive claims" : "Incentive claim review"}</h1>
          <p>
            {own
              ? "Request an incentive review and track the operator’s decision."
              : "Review claim evidence within the selected company."}
          </p>
        </div>
        {own && (
          <Button
            variant="primary"
            disabled={!options?.rules.length}
            onClick={() => startForm(null)}
          >
            <Plus size={15} />
            Request incentive claim
          </Button>
        )}
      </div>
      {error || resource.error ? (
        <p className="inline-error" role="alert">
          {error || resource.error?.message}
        </p>
      ) : null}
      {resource.phase === "loading" && !data ? (
        <Skeleton rows={4} />
      ) : (
        <div className="onboarding-layout">
          <section className="panel application-list">
            <div className="panel-header">
              <h2>{own ? "My requests" : "Company requests"}</h2>
            </div>
            {data?.claims.length ? (
              data.claims.map((c) => (
                <button
                  className={
                    "knowledge-node" +
                    (row?.Id === c.Id ? " knowledge-node-selected" : "")
                  }
                  key={c.Id}
                  onClick={() => {
                    setSelected(c.Id);
                    setNote("");
                  }}
                >
                  <span>
                    <strong>{c.Reference}</strong>
                    <small>
                      {c.ClaimType} ·{" "}
                      {own
                        ? new Date(c.CreatedAt * 1000).toLocaleDateString()
                        : c.ProviderName}
                    </small>
                  </span>
                  <Badge
                    tone={
                      c.Status === "Approved"
                        ? "positive"
                        : c.Status === "Rejected"
                          ? "negative"
                          : "neutral"
                    }
                  >
                    {label(c.Status)}
                  </Badge>
                </button>
              ))
            ) : (
              <Empty
                title="No claim requests yet"
                description={
                  own
                    ? "Submit a request with a reporting period or your own activity and an evidence reference."
                    : "Provider requests appear here after submission."
                }
              />
            )}
          </section>
          {row ? (
            <Panel
              title={row.Reference}
              description={row.ProviderName}
              action={<Badge>{label(row.Status)}</Badge>}
            >
              <dl className="knowledge-properties">
                <div>
                  <dt>Claim basis</dt>
                  <dd>
                    {row.ClaimType} · Rule #{row.IncentiveRuleId}
                  </dd>
                </div>
                <div>
                  <dt>Activity or period</dt>
                  <dd>
                    {row.VehicleActivityId
                      ? "Activity #" + row.VehicleActivityId
                      : `${row.PeriodStart} to ${row.PeriodEnd} (end exclusive)`}
                  </dd>
                </div>
                <div>
                  <dt>Provider statement</dt>
                  <dd>{row.Statement}</dd>
                </div>
                <div>
                  <dt>Evidence</dt>
                  <dd>{row.EvidenceReference}</dd>
                </div>
                <div>
                  <dt>Requested cash amount</dt>
                  <dd>
                    {row.RequestedAmountMinor === null
                      ? "Not specified; policy review requested"
                      : `${row.Currency} ${(row.RequestedAmountMinor / 100).toFixed(2)}`}
                  </dd>
                </div>
              </dl>
              {row.ReviewNote && (
                <div className="review-note">
                  <strong>Operator review</strong>
                  <p>{row.ReviewNote}</p>
                </div>
              )}
              {own && row.Status === "ChangesNeeded" && (
                <div className="workflow-actions">
                  <Button onClick={() => startForm(row)}>
                    Edit and resubmit claim
                  </Button>
                </div>
              )}
              {!own && row.Status === "Submitted" && (
                <div className="workflow-actions">
                  <Button
                    variant="primary"
                    loading={busy}
                    onClick={() => decide("UnderReview")}
                  >
                    Start claim review
                  </Button>
                </div>
              )}
              {!own && row.Status === "UnderReview" && (
                <div className="review-form">
                  <Field
                    label="Claim review explanation"
                    id="claim-review-note"
                  >
                    <textarea
                      id="claim-review-note"
                      className="textarea"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      rows={3}
                      maxLength={1000}
                    />
                  </Field>
                  <div className="button-row">
                    {["Approved", "ChangesNeeded", "Rejected"].map((status) => (
                      <Button
                        key={status}
                        variant={
                          status === "Approved"
                            ? "primary"
                            : status === "Rejected"
                              ? "danger"
                              : "secondary"
                        }
                        disabled={!note.trim()}
                        loading={busy}
                        onClick={() => decide(status)}
                      >
                        {label(status)}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
              <h3 className="knowledge-relations-heading">Claim history</h3>
              <ol className="application-history">
                {row.history.map((h, i) => (
                  <li key={i}>
                    <strong>{label(h.Action)}</strong>
                    <p>{h.Message}</p>
                    <small>
                      User #{h.ActorId} ·{" "}
                      {new Date(h.CreatedAt * 1000).toLocaleString()}
                    </small>
                  </li>
                ))}
              </ol>
              <p className="scope-footnote">
                A claim approval records the review outcome. It does not issue
                an award or settle a payment.
              </p>
            </Panel>
          ) : (
            <Empty
              title="Select a claim"
              description="The request, review notes and status history appear here."
            />
          )}
        </div>
      )}
      {own && !options?.rules.length && (
        <p className="scope-footnote">
          Your provider needs active incentive-program enrolment before
          requesting a claim. Contact the company operator through My concerns.
        </p>
      )}
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title={edit ? "Update incentive claim" : "Request incentive claim"}
        description="Only your provider’s records can be selected. The operator reviews eligibility and evidence."
      >
        <form onSubmit={submit} key={edit?.Id ?? "new"}>
          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
          <Field label="Incentive rule" id="claim-rule">
            <select
              id="claim-rule"
              name="rule_id"
              className="input"
              value={ruleId}
              onChange={(e) => setRuleId(e.target.value)}
              required
            >
              <option value="">Choose a rule</option>
              {options?.rules.map((r) => (
                <option key={r.Id} value={r.Id}>
                  {r.RuleName} · {r.AssessmentBasis}
                </option>
              ))}
            </select>
          </Field>
          {rule?.AssessmentBasis === "Event" ? (
            <Field label="Your activity" id="claim-activity">
              <select
                id="claim-activity"
                className="input"
                name="activity_id"
                defaultValue={edit?.VehicleActivityId ?? ""}
                required
              >
                <option value="">Select your activity</option>
                {options?.activities.map((a) => (
                  <option key={a.Id} value={a.Id}>
                    {a.OfficialActivityReference} · {a.ActivityKind}
                  </option>
                ))}
              </select>
            </Field>
          ) : rule?.AssessmentBasis === "Period" ? (
            <div className="form-row">
              <Field label="Period start" id="claim-start">
                <Input
                  id="claim-start"
                  name="period_start"
                  type="date"
                  defaultValue={edit?.PeriodStart ?? ""}
                  required
                />
              </Field>
              <Field label="Period end (exclusive)" id="claim-end">
                <Input
                  id="claim-end"
                  name="period_end"
                  type="date"
                  defaultValue={edit?.PeriodEnd ?? ""}
                  required
                />
              </Field>
            </div>
          ) : null}
          <Field label="Claim explanation" id="claim-statement">
            <textarea
              id="claim-statement"
              name="statement"
              className="textarea"
              defaultValue={edit?.Statement}
              rows={3}
              required
              maxLength={2000}
            />
          </Field>
          <Field label="Evidence reference" id="claim-evidence">
            <Input
              id="claim-evidence"
              name="evidence_reference"
              defaultValue={edit?.EvidenceReference}
              required
              maxLength={500}
            />
          </Field>
          <div className="form-row">
            <Field label="Requested cash amount (optional)" id="claim-amount">
              <Input
                id="claim-amount"
                name="requested_amount"
                type="number"
                min="0"
                step="0.01"
                defaultValue={
                  edit?.RequestedAmountMinor === undefined ||
                  edit.RequestedAmountMinor === null
                    ? ""
                    : (edit.RequestedAmountMinor / 100).toFixed(2)
                }
              />
            </Field>
            <Field label="Currency" id="claim-currency">
              <Input
                id="claim-currency"
                name="currency"
                defaultValue={edit?.Currency ?? "CAD"}
                pattern="[A-Za-z]{3}"
                maxLength={3}
              />
            </Field>
          </div>
          <div className="dialog-actions">
            <Button type="button" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={busy}
              disabled={!rule}
            >
              {edit ? "Resubmit claim" : "Submit claim request"}
            </Button>
          </div>
        </form>
      </Dialog>
    </>
  );
}
export function Concerns() {
  const resource = useWorkspaceResource<ConcernDocument>("concerns");
  const command = useCommand();
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<"Incentive" | "WorkspaceAccess">(
    "Incentive",
  );
  const [selected, setSelected] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("UnderReview");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const data = resource.data;
  const own = data?.role === "Provider";
  const concern =
    data?.concerns.find((c) => c.Id === selected) ?? data?.concerns[0];
  async function perform(payload: Record<string, unknown>) {
    setBusy(true);
    setError("");
    try {
      const result = await command<{ concern_id: number }>(
        "concern",
        "/api/workspace/concerns",
        payload,
      );
      if (result) {
        resource.reload();
        setSelected(result.concern_id);
        setOpen(false);
        setMessage("");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Concern could not be saved");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{own ? "My concerns" : "Provider concerns"}</h1>
          <p>
            Questions and calculation concerns, with private operator responses.
          </p>
        </div>
        {own && (
          <div className="button-row">
            <Button
              onClick={() => {
                setKind("WorkspaceAccess");
                setOpen(true);
              }}
            >
              Request workspace access
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setKind("Incentive");
                setOpen(true);
              }}
            >
              <Plus size={15} />
              Raise a concern
            </Button>
          </div>
        )}
      </div>
      {error || resource.error ? (
        <p role="alert" className="inline-error">
          {error || resource.error?.message}
        </p>
      ) : null}
      {!data && resource.phase === "loading" ? (
        <Skeleton rows={4} />
      ) : (
        <div className="onboarding-layout">
          <section className="panel application-list">
            <div className="panel-header">
              <h2>Conversations</h2>
            </div>
            {data?.concerns.length ? (
              data.concerns.map((c) => (
                <button
                  className={
                    "knowledge-node" +
                    (concern?.Id === c.Id ? " knowledge-node-selected" : "")
                  }
                  key={c.Id}
                  onClick={() => {
                    setSelected(c.Id);
                    setMessage("");
                  }}
                >
                  <span>
                    <strong>{c.Subject}</strong>
                    <small>
                      {own ? "Your provider" : "Provider #" + c.ProviderId} ·
                      CON-{c.Id}
                    </small>
                  </span>
                  <Badge>{label(c.Status)}</Badge>
                </button>
              ))
            ) : (
              <Empty
                title="No concerns raised"
                description={
                  own
                    ? "Ask about incentive calculations or a claim review."
                    : "Provider questions and disputes appear here."
                }
              />
            )}
          </section>
          {concern ? (
            <Panel
              title={concern.Subject}
              description={`CON-${concern.Id}${concern.ClaimId ? " · Claim #" + concern.ClaimId : ""}`}
              action={<Badge>{label(concern.Status)}</Badge>}
            >
              {concern.Kind === "WorkspaceAccess" && (
                <div className="review-note">
                  <strong>Workspace access request</strong>
                  <p>
                    {concern.RequestedWorkspaceName}. Workspace creation and
                    permissions remain administrator-controlled.
                  </p>
                </div>
              )}
              <ol className="concern-messages">
                {concern.messages.map((m, i) => (
                  <li key={i}>
                    <p>{m.Message}</p>
                    <small>
                      User #{m.ActorId} ·{" "}
                      {new Date(m.CreatedAt * 1000).toLocaleString()}
                    </small>
                  </li>
                ))}
              </ol>
              {(!own || concern.Status !== "Closed") && (
                <form
                  className="review-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    perform({
                      concern_id: concern.Id,
                      version: concern.Version,
                      message,
                      status,
                    });
                  }}
                >
                  <Field label="Your response" id="concern-response">
                    <textarea
                      id="concern-response"
                      className="textarea"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      required
                      maxLength={2000}
                      rows={3}
                    />
                  </Field>
                  {!own && (
                    <Field label="Concern status" id="concern-status">
                      <select
                        id="concern-status"
                        className="input"
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                      >
                        {["Open", "UnderReview", "Resolved", "Closed"].map(
                          (s) => (
                            <option key={s} value={s}>
                              {label(s)}
                            </option>
                          ),
                        )}
                      </select>
                    </Field>
                  )}
                  <Button type="submit" loading={busy}>
                    <Send size={14} />
                    {own ? "Send response" : "Respond and update status"}
                  </Button>
                </form>
              )}
            </Panel>
          ) : (
            <Empty
              title="Select a concern"
              description="The conversation and review status appear here."
            />
          )}
        </div>
      )}
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title={
          kind === "WorkspaceAccess"
            ? "Request workspace access"
            : "Raise an incentive concern"
        }
        description="Visible only to your provider and the company review team."
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            perform(Object.fromEntries(new FormData(e.currentTarget)));
          }}
        >
          <input type="hidden" name="kind" value={kind} />
          {kind === "WorkspaceAccess" && (
            <>
              <Field
                label="Requested workspace or company"
                id="requested-workspace"
              >
                <Input
                  id="requested-workspace"
                  name="workspace_name"
                  required
                  maxLength={200}
                />
              </Field>
              <p className="field-hint">
                The operator or administrator will review this request. Only an
                administrator can create workspaces or grant permissions;
                submission grants no access.
              </p>
            </>
          )}
          <Field label="Subject" id="concern-subject">
            <Input
              id="concern-subject"
              name="subject"
              defaultValue={
                kind === "WorkspaceAccess" ? "Workspace access request" : ""
              }
              required
              maxLength={200}
            />
          </Field>
          {kind === "Incentive" && (
            <Field
              label="Claim number (optional)"
              id="concern-claim"
              hint="Use the numeric claim ID shown in your claim detail, if relevant."
            >
              <Input id="concern-claim" name="claim_id" type="number" min="1" />
            </Field>
          )}
          <Field label="Concern details" id="concern-message">
            <textarea
              id="concern-message"
              name="message"
              className="textarea"
              required
              maxLength={2000}
              rows={4}
            />
          </Field>
          {error && (
            <p role="alert" className="inline-error">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <Button type="button" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={busy}>
              Submit concern
            </Button>
          </div>
        </form>
      </Dialog>
    </>
  );
}
export function ProviderChat() {
  const cid = useAppSelector((s) => s.workspace.companyId);
  const csrf = useAppSelector((s) => s.session.data?.csrf ?? "");
  const [question, setQuestion] = useState("How is my incentive calculated?");
  const [answer, setAnswer] = useState<{
    answer: string;
    sources: { type: string; id: number }[];
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function ask(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      setAnswer(
        await request(
          "/api/workspace/provider-chat",
          { company_id: cid, question },
          csrf,
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "The assistant is unavailable");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Incentive assistant</h1>
          <p>
            Understand your applicable policy, claim status and review options.
          </p>
        </div>
        <Button onClick={() => (location.hash = "concerns")}>
          <MessageCircle size={15} />
          Raise a concern
        </Button>
      </div>
      <div className="knowledge-bottom">
        <Panel
          title="Ask about your incentive"
          description="Answers use your company policy and your provider records. No graph browsing or external AI call."
        >
          <form onSubmit={ask}>
            <Field label="Your question" id="provider-chat-question">
              <textarea
                id="provider-chat-question"
                className="textarea"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                required
                maxLength={1000}
                rows={4}
              />
            </Field>
            <Button type="submit" variant="primary" loading={busy}>
              <Send size={14} />
              Ask incentive assistant
            </Button>
          </form>
          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
          {answer && (
            <div className="assistant-response" aria-live="polite">
              <p>{answer.answer}</p>
              <div className="source-links">
                {answer.sources.map((s) => (
                  <span key={s.type + s.id}>
                    {s.type} #{s.id}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Panel>
        <Panel
          title="Need a company decision?"
          description="The chatbot explains records; the company operator reviews claims and concerns."
        >
          <div className="provider-help-actions">
            <p>
              Use My incentive claims to request a review and track its status.
              If you disagree with a calculation or need clarification, raise a
              concern for the company operator.
            </p>
            <Button onClick={() => (location.hash = "claims")}>
              Open my claims
            </Button>
            <Button onClick={() => (location.hash = "concerns")}>
              Open my concerns
            </Button>
          </div>
        </Panel>
      </div>
    </>
  );
}
