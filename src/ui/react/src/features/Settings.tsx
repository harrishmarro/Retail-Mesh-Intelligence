import { useState, type FormEvent } from "react";
import {
  Plus,
  ShieldCheck,
  UserPlus,
  ArrowUpRight,
  LogOut,
  Check,
  AlertCircle,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { actions, loadSession } from "../app/store";
import { useCommand } from "../app/commands";
import { request } from "../app/client";
import {
  Badge,
  Button,
  Dialog,
  Empty,
  Field,
  Input,
  Panel,
} from "../components/ui";
import {
  ChangePassword,
  ImportDataset,
  ProviderSignupSettings,
} from "./AccountAccess";
export function Members() {
  const dispatch = useAppDispatch();
  const members = useAppSelector((s) => s.workspace.members);
  const user = useAppSelector((s) => s.session.data?.user);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Team members</h1>
          <p>
            Control who can access this company and the evidence they can see.
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => dispatch(actions.modalChanged("member"))}
        >
          <UserPlus size={16} />
          Add member
        </Button>
      </div>
      <div className="table-caption">
        {members.filter((m) => m.Status === "Active").length} active members
      </div>
      {members.length ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Role</th>
                <th>Provider scope</th>
                <th>Access</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.Id}>
                  <td>
                    <div className="table-identity">
                      <span className="avatar">
                        {m.DisplayName.split(" ")
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join("")}
                      </span>
                      <div>
                        <strong>
                          {m.DisplayName}
                          {m.Id === user?.Id && (
                            <span className="you-label">You</span>
                          )}
                        </strong>
                        <small>{m.Email}</small>
                      </div>
                    </div>
                  </td>
                  <td>
                    {m.Role === "CompanyAdmin"
                      ? "Company administrator"
                      : m.Role}
                  </td>
                  <td>
                    {m.ProviderId ? (
                      <span className="mono">
                        PR-{String(m.ProviderId).padStart(3, "0")}
                      </span>
                    ) : (
                      "Company-wide"
                    )}
                  </td>
                  <td>
                    <Badge tone={m.Status === "Active" ? "neutral" : "warning"}>
                      {m.Status}
                    </Badge>
                  </td>
                  <td>
                    {m.Id !== user?.Id && m.Status === "Active" && (
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={() => dispatch(actions.revokeChosen(m.Id))}
                      >
                        Revoke access
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No members in this workspace"
          description="An administrator can grant a local user access to this company."
        />
      )}
      <div className="role-guide">
        <div>
          <ShieldCheck size={18} />
          <h3>Company administrator</h3>
          <p>
            Evaluate rules and manage the company’s members and complete
            evidence.
          </p>
        </div>
        <div>
          <ShieldCheck size={18} />
          <h3>Company operator</h3>
          <p>
            Validate provider applications, review claims, answer concerns and
            inspect company knowledge.
          </p>
        </div>
        <div>
          <ShieldCheck size={18} />
          <h3>Analyst</h3>
          <p>
            Read company activity, decisions and exported evidence without
            modifying them.
          </p>
        </div>
        <div>
          <ShieldCheck size={18} />
          <h3>Provider</h3>
          <p>
            Read only the assigned provider’s activities and beneficiary award
            summaries.
          </p>
        </div>
      </div>
      <p className="scope-footnote">
        Access is checked on every request. Revocation affects subsequent
        requests, including existing login sessions.
      </p>
    </>
  );
}
export function Settings() {
  const dispatch = useAppDispatch();
  const auth = useAppSelector((s) => s.session.data)!;
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const company = auth.workspaces.find((c) => c.company_id === companyId);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Workspace settings</h1>
          <p>Company context, account access and explanation configuration.</p>
        </div>
      </div>
      <section className="setting-row">
        <div>
          <h2>Company workspace</h2>
          <p>
            Your selected company determines the records and permissions
            available throughout Retail-Mesh.
          </p>
        </div>
        <div className="setting-well">
          <dl className="settings-list">
            <div>
              <dt>Company</dt>
              <dd>{company?.company_name}</dd>
            </div>
            <div>
              <dt>Your role</dt>
              <dd>
                {company?.Role === "CompanyAdmin"
                  ? "Company administrator"
                  : company?.Role}
              </dd>
            </div>
            <div>
              <dt>Workspace ID</dt>
              <dd className="mono">COMPANY-{companyId}</dd>
            </div>
          </dl>
          {company?.Role === "CompanyAdmin" ? (
            <Button onClick={() => dispatch(actions.modalChanged("company"))}>
              <Plus size={15} />
              Create another workspace
            </Button>
          ) : (
            <p className="field-hint">
              Workspace creation is controlled by the company administrator.
              Providers can request workspace access through My concerns.
            </p>
          )}
        </div>
      </section>
      <section className="setting-row">
        <div>
          <h2>Evidence explanations</h2>
          <p>
            Graph queries provide the authoritative answer. Optional model
            wording is separate and requires consent for each request.
          </p>
        </div>
        <div className="setting-well">
          <div className="configuration-row">
            <span>OpenAI narration</span>
            <Badge tone={auth.ai.configured ? "positive" : "neutral"}>
              {auth.ai.configured ? "Configured" : "Not configured"}
            </Badge>
          </div>
          <p>
            {auth.ai.configured
              ? `Model: ${auth.ai.model}. Narration is off until explicitly selected.`
              : "Deterministic explanations remain available. An operator can configure an API key and available model on the local server."}
          </p>
          <p className="field-hint">
            Keys are never entered or returned through the browser. Provider
            roles cannot use external narration.
          </p>
        </div>
      </section>
      <section className="setting-row">
        <div>
          <h2>Your account</h2>
          <p>
            A private local session with company membership checked on every
            request.
          </p>
        </div>
        <div className="setting-well">
          <dl className="settings-list">
            <div>
              <dt>Name</dt>
              <dd>{auth.user?.DisplayName}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{auth.user?.Email}</dd>
            </div>
            <div>
              <dt>Session</dt>
              <dd>Eight-hour maximum, revocable</dd>
            </div>
          </dl>
          <p className="field-hint">
            Self-service password changes are available below.
            Forgotten-password recovery, MFA and verified organizational
            ownership remain planned.
          </p>
        </div>
      </section>
      <ChangePassword />
      {company?.Role === "CompanyAdmin" && (
        <>
          <ProviderSignupSettings />
          <ImportDataset />
        </>
      )}
    </>
  );
}
export function Modals() {
  const dispatch = useAppDispatch();
  const ui = useAppSelector((s) => s.ui);
  const auth = useAppSelector((s) => s.session.data)!;
  const workspace = useAppSelector((s) => s.workspace);
  const command = useCommand();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  function close() {
    setError("");
    dispatch(actions.modalChanged(null));
  }
  async function createCompany(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setError("");
    setBusy(true);
    try {
      const payload = Object.fromEntries(new FormData(form));
      const r = await request<{ company_id: number }>(
        "/api/workspaces",
        payload,
        auth.csrf,
      );
      form.reset();
      await dispatch(loadSession()).unwrap();
      dispatch(actions.selectCompany(r.company_id));
      close();
      dispatch(actions.noticeChanged("Company workspace created."));
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Workspace could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function addMember(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setError("");
    setBusy(true);
    try {
      await command(
        "member",
        "/api/workspace/members",
        Object.fromEntries(new FormData(form)),
      );
      form.reset();
      close();
      dispatch(
        actions.noticeChanged(
          "Company membership saved. Existing passwords were not changed.",
        ),
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Membership could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function revoke() {
    setError("");
    setBusy(true);
    try {
      await command("revoke", "/api/workspace/revoke-member", {
        user_id: ui.revokeId,
      });
      close();
      dispatch(
        actions.noticeChanged(
          "Membership revoked. Subsequent requests will be denied.",
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Access could not be revoked.");
    } finally {
      setBusy(false);
    }
  }
  const member = workspace.members.find((m) => m.Id === ui.revokeId);
  return (
    <>
      <Dialog
        open={ui.modal === "company"}
        onOpenChange={(v) => !v && close()}
        title="Create company workspace"
        description="A separate company context with its own network, activities and awards."
      >
        <form onSubmit={createCompany}>
          <Field label="Company legal name" id="new-company">
            <Input
              id="new-company"
              name="company_name"
              maxLength={200}
              required
            />
          </Field>
          <div className="form-row">
            <Field label="Registration jurisdiction" id="new-jurisdiction">
              <Input
                id="new-jurisdiction"
                name="jurisdiction"
                required
                maxLength={50}
              />
            </Field>
            <Field
              label="Business registration reference"
              id="new-registration"
            >
              <Input
                id="new-registration"
                name="registration"
                required
                maxLength={100}
              />
            </Field>
          </div>
          <p className="field-hint">
            Use clearly fictional details for a demo. Creating a workspace does
            not verify ownership of a real business.
          </p>
          {error && (
            <p role="alert" className="inline-error">
              {error}
            </p>
          )}
          <div className="dialog-footer">
            <Button type="button" onClick={close}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={busy}>
              Create workspace
            </Button>
          </div>
        </form>
      </Dialog>
      <Dialog
        open={ui.modal === "member"}
        onOpenChange={(v) => !v && close()}
        title="Add company member"
        description="Grant a local user access to this company. No invitation email is sent."
      >
        <form onSubmit={addMember}>
          <Field label="Email address" id="member-email">
            <Input id="member-email" name="email" type="email" required />
          </Field>
          <Field label="Display name for a new user" id="member-name">
            <Input id="member-name" name="display_name" maxLength={200} />
          </Field>
          <Field
            label="Initial password for a new user"
            id="member-password"
            hint="12–256 characters. Existing users retain their current password."
          >
            <Input
              id="member-password"
              name="password"
              type="password"
              minLength={12}
              maxLength={256}
              autoComplete="new-password"
            />
          </Field>
          <div className="form-row">
            <Field label="Workspace role" id="member-role">
              <select id="member-role" name="role" className="input">
                <option value="Analyst">Analyst</option>
                <option value="Provider">Provider</option>
                <option value="CompanyAdmin">Company administrator</option>
                <option value="CompanyOperator">Company operator</option>
              </select>
            </Field>
            <Field label="Provider scope, if applicable" id="member-provider">
              <select id="member-provider" name="provider_id" className="input">
                <option value="">No provider scope</option>
                {workspace.summary.providers.map((p) => (
                  <option value={p.Id} key={p.Id}>
                    {p.LegalName.replace(" (fictional)", "")}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          {error && (
            <p role="alert" className="inline-error">
              {error}
            </p>
          )}
          <div className="dialog-footer">
            <Button type="button" onClick={close}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={busy}>
              Save membership
            </Button>
          </div>
        </form>
      </Dialog>
      <Dialog
        open={ui.modal === "revoke"}
        onOpenChange={(v) => !v && close()}
        title="Revoke company access?"
        description={`${member?.DisplayName ?? "This member"} will lose access to this workspace on their next request. Other company memberships are unaffected.`}
      >
        <p className="field-hint">
          An administrator can restore this membership later.
        </p>
        {error && (
          <p role="alert" className="inline-error">
            {error}
          </p>
        )}
        <div className="dialog-footer">
          <Button onClick={close}>Keep access</Button>
          <Button variant="danger" loading={busy} onClick={revoke}>
            Revoke access
          </Button>
        </div>
      </Dialog>
    </>
  );
}
