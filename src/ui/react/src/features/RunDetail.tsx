import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowDownToLine,
  Check,
  ArrowRight,
  Network,
  ShieldCheck,
  Send,
  Copy,
  CheckCheck,
  AlertCircle,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { actions, askQuestion, loadRun } from "../app/store";
import {
  Button,
  Badge,
  Empty,
  FeedbackRegion,
  Panel,
  Switch,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui";
import { money, ScenarioAction } from "./Overview";
import { RunsTable, RecordedAwards } from "./Records";
const checkNames: Record<string, string> = {
  completed_sale: "Completed sale",
  program_active: "Active incentive program",
  program_enrollment: "Provider enrollment",
  sale_authorization: "Outlet & sale capability",
  pre_sale_fleet: "Historical fleet threshold",
  verified_service_and_replacement: "Verified service & replacement rental",
};
export function useDefaultRun() {
  const dispatch = useAppDispatch();
  const { companyId, summary, run } = useAppSelector((s) => s.workspace);
  const latest = summary.runs[0]?.id;
  useEffect(() => {
    if (companyId && latest && !run)
      dispatch(loadRun({ companyId, runId: latest }));
  }, [companyId, latest, dispatch]);
}
export function Incentives() {
  useDefaultRun();
  const selected = useAppSelector(
    (s) => s.workspace.run || s.workspace.busy === "run",
  );
  const [tab, setTab] = useState(selected ? "detail" : "decisions");
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Incentives</h1>
          <p>
            Calculated entitlements, with the exact evidence behind every
            decision.
          </p>
        </div>
        <ScenarioAction />
      </div>
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="underline-tabs primary-tabs">
          <TabsTrigger className="underline-tab" value="decisions">
            Evaluation register
          </TabsTrigger>
          <TabsTrigger className="underline-tab" value="recorded">
            Recorded awards
          </TabsTrigger>
          <TabsTrigger className="underline-tab" value="detail">
            Selected decision
          </TabsTrigger>
        </TabsList>
        <TabsContent value="decisions">
          <RunsTable onInspect={() => setTab("detail")} />
          <div className="inline-link-row">
            <Button variant="ghost" onClick={() => setTab("detail")}>
              Open selected decision
              <ArrowRight size={15} />
            </Button>
          </div>
        </TabsContent>
        <TabsContent value="recorded">
          <RecordedAwards />
        </TabsContent>
        <TabsContent value="detail">
          <DecisionDetail />
        </TabsContent>
      </Tabs>
    </>
  );
}
export function Knowledge() {
  useDefaultRun();
  const summary = useAppSelector((s) => s.workspace.summary);
  const run = useAppSelector((s) => s.workspace.run);
  const dispatch = useAppDispatch();
  const companyId = useAppSelector((s) => s.workspace.companyId);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Knowledge & AI</h1>
          <p>
            Trace a recorded result through its source relationships and policy
            checks.
          </p>
        </div>
        {summary.runs.length > 0 && (
          <label className="run-picker">
            Evaluation
            <select
              aria-label="Select evaluation"
              value={run?.run_id ?? ""}
              onChange={(e) =>
                companyId &&
                dispatch(loadRun({ companyId, runId: Number(e.target.value) }))
              }
            >
              {summary.runs.map((r) => (
                <option key={r.id} value={r.id}>
                  RUN-{r.id} · {r.result}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <DecisionDetail explanationFirst />
    </>
  );
}
export function DecisionDetail({
  explanationFirst = false,
}: {
  explanationFirst?: boolean;
}) {
  const run = useAppSelector((s) => s.workspace.run);
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const role = useAppSelector(
    (s) =>
      s.session.data?.workspaces.find((c) => c.company_id === companyId)?.Role,
  );
  const busy = useAppSelector((s) => s.workspace.busy);
  const [copied, setCopied] = useState(false);
  if (!run)
    return (
      <Empty
        title={busy === "run" ? "Loading decision…" : "No decision selected"}
        description="Evaluate the company journey or inspect a saved run to see its checks and explanation."
      />
    );
  const passed = run.checks.filter((c) => c.passed).length;
  async function copyHash() {
    if (!run) return;
    try {
      await navigator.clipboard.writeText(run.input_hash);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }
  const copyButton = (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Copy evidence snapshot hash"
      onClick={copyHash}
    >
      {copied ? <CheckCheck size={15} /> : <Copy size={15} />}
    </Button>
  );
  return (
    <FeedbackRegion identity={run.run_id}>
      <div className="decision-header">
        <div>
          <div className="decision-kicker">
            <span className="mono">
              RUN-{String(run.run_id).padStart(3, "0")}
            </span>
            <Badge tone={run.result === "Qualified" ? "positive" : "negative"}>
              {run.result}
            </Badge>
          </div>
          <h2>{run.beneficiary.replace(" (fictional)", "")}</h2>
          <p>
            Rule version <span className="mono">RV-{run.rule_version_id}</span>{" "}
            · {run.evaluated_at.slice(0, 10)} · {run.evaluated_at.slice(11, 16)}{" "}
            UTC
          </p>
        </div>
        <div className="decision-amount">
          <span>Calculated entitlement</span>
          <strong>
            {run.event_award_id
              ? money(run.reward.amount_minor, run.reward.currency)
              : "No award"}
          </strong>
          <small>
            {passed} of {run.checks.length} policy checks passed
          </small>
        </div>
      </div>
      {run.review_required && (
        <div className="review-notice">
          <AlertCircle size={17} />
          <p>
            Source evidence changed after issuance. The original decision is
            preserved and requires review; it has not been recalculated or paid
            again.
          </p>
        </div>
      )}
      <div className="decision-body">
        <div className="decision-evidence">
          <Panel
            title="Evidence path"
            description="Connections accepted by this evaluation"
          >
            <div className="evidence-path">
              {[
                { label: "Sale", value: `Activity #${run.activity_id}` },
                {
                  label: "Service",
                  value: run.evidence?.selected?.service
                    ?.OfficialActivityReference as string | undefined,
                },
                {
                  label: "Rental",
                  value: run.evidence?.selected?.rental
                    ?.OfficialActivityReference as string | undefined,
                },
                { label: "Decision", value: run.result },
              ].map((item, i) => (
                <div key={item.label}>
                  <span
                    className={
                      "evidence-node" +
                      (run.result === "Qualified" ? " evidence-accepted" : "")
                    }
                  >
                    <span>{i + 1}</span>
                    <strong>{item.label}</strong>
                    <small>
                      {item.value ??
                        (role === "Provider"
                          ? "Restricted evidence"
                          : "No accepted path")}
                    </small>
                  </span>
                  {i < 3 && <ChevronRight size={14} />}
                </div>
              ))}
            </div>
            <p className="path-note">
              {role === "Provider"
                ? "Your role can view the award summary. Full cross-provider evidence is restricted to company readers."
                : "Historical fleet membership and verified identity assertions are retained in the immutable source snapshot."}
            </p>
          </Panel>
          <Panel
            title="Qualification checks"
            description={`${run.fleet_count_before_sale} qualifying fleet vehicles existed before the sale.`}
          >
            <ol className="check-list">
              {run.checks.map((c) => (
                <li key={c.name}>
                  <span
                    className={
                      "check-indicator " +
                      (c.passed ? "check-pass" : "check-fail")
                    }
                  >
                    {c.passed ? <Check size={14} /> : <span>!</span>}
                  </span>
                  <div>
                    <strong>{checkNames[c.name] ?? c.name}</strong>
                    <p>{c.detail}</p>
                  </div>
                  <span className="check-result">
                    {c.passed ? "Passed" : "Failed"}
                  </span>
                </li>
              ))}
            </ol>
          </Panel>
        </div>
        <div className="decision-side">
          <Explanation primary={explanationFirst} />
          <Panel
            title="Source snapshot"
            description="The evidence used at evaluation time"
          >
            <div className="source-row">
              <span>Rule version</span>
              <strong className="mono">RV-{run.rule_version_id}</strong>
            </div>
            <div className="source-row">
              <span>Evaluation</span>
              <strong className="mono">RUN-{run.run_id}</strong>
            </div>
            <div className="hash-row">
              <span className="mono" title={run.input_hash}>
                {run.input_hash.slice(0, 12)}…{run.input_hash.slice(-8)}
              </span>
              {copyButton}
            </div>
            {role !== "Provider" && (
              <div className="export-actions">
                <Button asChild size="small">
                  <a
                    href={`/api/workspace/graph?company_id=${companyId}&run_id=${run.run_id}&format=turtle`}
                  >
                    <ArrowDownToLine size={14} />
                    Turtle
                  </a>
                </Button>
                <Button asChild size="small">
                  <a
                    href={`/api/workspace/graph?company_id=${companyId}&run_id=${run.run_id}&format=json-ld`}
                  >
                    <ArrowDownToLine size={14} />
                    JSON-LD
                  </a>
                </Button>
              </div>
            )}
          </Panel>
        </div>
      </div>
      {explanationFirst && (
        <p className="scope-footnote">
          <Network size={13} />
          Graph exports are checked with SHACL before download. AI narration
          does not change the recorded result.
        </p>
      )}
    </FeedbackRegion>
  );
}
function Explanation({ primary = false }: { primary?: boolean }) {
  const dispatch = useAppDispatch();
  const { run, answer, busy } = useAppSelector((s) => s.workspace);
  const { question, useAI } = useAppSelector((s) => s.ui);
  const auth = useAppSelector((s) => s.session.data)!;
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const role = auth.workspaces.find((c) => c.company_id === companyId)?.Role;
  const allowed = auth.ai.configured && role !== "Provider";
  async function ask(e: FormEvent) {
    e.preventDefault();
    if (run) dispatch(askQuestion());
  }
  return (
    <section className="panel assistant-panel">
      <div className="panel-header">
        <div className="assistant-heading">
          <Network size={17} />
          <h2>Ask the evidence</h2>
        </div>
        <span className="assistant-mode">
          {useAI ? "AI narration" : "Graph query"}
        </span>
      </div>
      <p className="assistant-intro">
        Get a reason you can check against the recorded sources.
      </p>
      <form onSubmit={ask}>
        <label className="sr-only" htmlFor="explanation-question">
          Question about the selected decision
        </label>
        <textarea
          id="explanation-question"
          className="textarea"
          value={question}
          onChange={(e) => dispatch(actions.questionChanged(e.target.value))}
          maxLength={1000}
          required
          rows={3}
        />
        <Button
          type="submit"
          variant={primary ? "primary" : "secondary"}
          className="ask-submit"
          loading={busy === "ask"}
          disabled={!run}
        >
          <Send size={14} />
          Explain this result
        </Button>
        <div className="ai-toggle">
          <div>
            <strong>Optional AI narration</strong>
            <span>
              {allowed
                ? "A separate wording layer, with your permission."
                : role === "Provider"
                  ? "Not available for this role."
                  : "No external model is configured."}
            </span>
          </div>
          <Switch
            checked={useAI}
            disabled={!allowed}
            onCheckedChange={(v) => dispatch(actions.aiChanged(v))}
            label="Use optional OpenAI narration"
          />
        </div>
        {useAI && (
          <p className="ai-consent">
            Sends this question and a reduced authorized evidence summary to
            OpenAI. API charges may apply. Your recorded decision stays
            unchanged.
          </p>
        )}
      </form>
      {answer && (
        <div className="assistant-response" aria-live="polite">
          <div className="response-label">
            <ShieldCheck size={14} />
            Authoritative answer
          </div>
          <p>{answer.answer}</p>
          <div className="source-links">
            {answer.sources.map((s, i) => (
              <span key={i}>
                <ExternalLink size={11} />
                {s.type} {s.id ?? s.sha256?.slice(0, 8)}
              </span>
            ))}
          </div>
          {answer.ai_narrative && (
            <div className="ai-narrative">
              <strong>AI wording · review against the evidence</strong>
              <p>{answer.ai_narrative}</p>
            </div>
          )}
          <small>
            {answer.live_llm
              ? "AI narration returned."
              : answer.ai_status === "not_configured"
                ? "Model not configured. Graph answer retained."
                : "Answered from the recorded graph or scoped summary."}
          </small>
        </div>
      )}
    </section>
  );
}
