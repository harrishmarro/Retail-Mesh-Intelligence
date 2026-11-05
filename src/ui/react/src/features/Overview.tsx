import {
  ArrowRight,
  Play,
  Plus,
  ArrowUpRight,
  Check,
  Clock3,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import {
  actions,
  evaluateRule,
  loadRun,
  loadWorkspace,
  selectAwardTotals,
} from "../app/store";
import { useCommand } from "../app/commands";
import { Button, Panel, Badge, Empty } from "../components/ui";
import { navigateTo } from "./Shell";
export const money = (minor: number, currency = "CAD") =>
  new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency,
    currencyDisplay: "code",
  }).format(minor / 100);
export function useRunActions() {
  const dispatch = useAppDispatch(),
    company = useAppSelector((s) => s.workspace.companyId);
  return async (
    id: number,
    view: "incentives" | "knowledge" = "incentives",
  ) => {
    if (!company) return;
    dispatch(loadRun({ companyId: company, runId: id }));
    navigateTo(view);
  };
}
export function ScenarioAction() {
  const dispatch = useAppDispatch();
  const workspace = useAppSelector((s) => s.workspace);
  const role = useAppSelector(
    (s) =>
      s.session.data?.workspaces.find(
        (c) => c.company_id === s.workspace.companyId,
      )?.Role,
  );
  const command = useCommand();
  const prepared = workspace.summary.demo_ready === true;
  if (role !== "CompanyAdmin")
    return <span className="read-only-note">Read-only access</span>;
  async function execute() {
    try {
      if (!workspace.companyId) return;
      if (!prepared) {
        await command("prepare", "/api/workspace/seed-demo");
        dispatch(
          actions.noticeChanged(
            "Fictional provider journey prepared for this company.",
          ),
        );
      } else {
        await dispatch(evaluateRule(workspace.companyId)).unwrap();
        await dispatch(loadWorkspace(workspace.companyId));
        navigateTo("incentives");
      }
    } catch {
      /* scoped errors are shown by the store */
    }
  }
  return (
    <Button variant="primary" loading={!!workspace.busy} onClick={execute}>
      {prepared ? <Play size={15} /> : <Plus size={16} />}{" "}
      {prepared ? "Evaluate incentive" : "Prepare demo journey"}
    </Button>
  );
}
export default function Overview() {
  const s = useAppSelector((s) => s.workspace.summary);
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const totals = useAppSelector(selectAwardTotals);
  const inspect = useRunActions();
  const qualified = s.runs.filter((r) => r.result === "Qualified");
  const amounts = Object.entries(totals);
  const demoActivities = s.activities.filter(
    (a) => a.SourceNamespace === `demo.workspace.${companyId}`,
  );
  const hasActivities =
    s.demo_ready === true &&
    ["NS-SALE-001", "NS-SERVICE-001", "NS-RENTAL-001"].every((ref) =>
      demoActivities.some((a) => a.OfficialActivityReference === ref),
    );
  const ordered = [...demoActivities].sort((a, b) =>
    a.StartedAt.localeCompare(b.StartedAt),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Operations overview</h1>
          <p>
            Follow your provider activity through to an explainable incentive.
          </p>
        </div>
        <ScenarioAction />
      </div>
      <div className="metrics-strip">
        <div className="metric-lead">
          <span>Calculated provider incentives</span>
          <strong>
            {amounts.length === 0
              ? money(0)
              : amounts.length === 1
                ? money(amounts[0][1], amounts[0][0])
                : "Multiple currencies"}
          </strong>
          <small>
            {amounts.length > 1
              ? amounts.map(([c, n]) => money(n, c)).join(" · ")
              : "Loaded qualified awards"}
          </small>
        </div>
        <div>
          <span>Provider network</span>
          <strong>{s.providers.length.toLocaleString()}</strong>
          <small>Provider records in your scope</small>
        </div>
        <div>
          <span>Vehicle activities</span>
          <strong>{s.activities.length.toLocaleString()}</strong>
          <small>Recorded sales, services and rentals</small>
        </div>
        <div>
          <span>Qualified loaded runs</span>
          <strong>
            {qualified.length.toLocaleString()}
            <em> / {s.runs.length}</em>
          </strong>
          <small>Based on saved rule checks</small>
        </div>
      </div>
      <div className="overview-grid">
        <Panel
          title="Fleet engine demo"
          description={
            hasActivities
              ? "Cedar Logistics · Fictional acceptance scenario"
              : "A separate scenario for automated evaluation"
          }
          action={
            <Button
              variant="ghost"
              size="small"
              onClick={() => navigateTo("activities")}
            >
              View activities
              <ArrowUpRight size={14} />
            </Button>
          }
          className="journey-panel"
        >
          {hasActivities ? (
            <>
              <div className="journey-route">
                {(["Sale", "Service", "Rental"] as const).map((kind, i) => {
                  const act = ordered.find((a) => a.ActivityKind === kind);
                  return (
                    <div key={kind} className="journey-stage">
                      <div className="stage-marker">
                        {act ? <Check size={15} /> : <Clock3 size={15} />}
                      </div>
                      <span className="stage-type">
                        {kind === "Rental" ? "Replacement rental" : kind}
                      </span>
                      <strong>
                        {act?.Provider.replace(" (fictional)", "") ??
                          "Not recorded"}
                      </strong>
                      <span className="stage-ref">
                        {act?.OfficialActivityReference ?? "Awaiting activity"}
                      </span>
                      {i < 2 && <span className="stage-line" />}
                    </div>
                  );
                })}
              </div>
              <div className="journey-outcome">
                <span className="outcome-dot" />
                <div>
                  <strong>
                    {qualified.length
                      ? "Evidence evaluated. Award retained."
                      : "Activities recorded. Ready for evaluation."}
                  </strong>
                  <span>
                    {qualified.length
                      ? "Open the award to inspect its exact rule and six evidence checks."
                      : "The rule evaluates the historical fleet, provider permissions and linked rental."}
                  </span>
                </div>
                <ArrowRight size={17} />
              </div>
            </>
          ) : (
            <Empty
              title="Connect your first provider journey"
              description="The optional fleet-engine scenario is separate from imported activities and manual-review awards. Company administrators can prepare it without replacing existing records."
            />
          )}
        </Panel>
        <Panel
          title="Incentive decisions"
          description="Results from the versioned rule engine"
          action={
            <Button
              variant="ghost"
              size="small"
              onClick={() => navigateTo("incentives")}
            >
              View all
              <ArrowUpRight size={14} />
            </Button>
          }
        >
          {s.runs.length ? (
            <div className="decision-list">
              {s.runs.slice(0, 3).map((r) => (
                <button
                  className="decision-row"
                  key={r.id}
                  onClick={() => inspect(r.id)}
                >
                  <span>
                    <strong>{r.beneficiary.replace(" (fictional)", "")}</strong>
                    <small>
                      Evaluation{" "}
                      <span className="mono">
                        RUN-{String(r.id).padStart(3, "0")}
                      </span>
                    </small>
                  </span>
                  <span>
                    <strong>
                      {r.amount_minor === null
                        ? "No award"
                        : money(r.amount_minor, r.currency)}
                    </strong>
                    <Badge
                      tone={r.result === "Qualified" ? "positive" : "negative"}
                    >
                      {r.result}
                    </Badge>
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <Empty
              title="No evaluations yet"
              description="An award appears only after the rule checks its evidence. Preparing demo activities does not preload a payout."
            />
          )}
        </Panel>
        <Panel
          title="Recent vehicle activity"
          description="Latest recorded activities in your scope"
          action={
            <Button
              variant="ghost"
              size="small"
              onClick={() => navigateTo("activities")}
            >
              View all
              <ArrowUpRight size={14} />
            </Button>
          }
        >
          {s.activities.length ? (
            <div className="compact-activity">
              {ordered
                .slice(-4)
                .reverse()
                .map((a) => (
                  <div key={a.Id}>
                    <div>
                      <strong>{a.ActivityKind}</strong>
                      <span>{a.Provider.replace(" (fictional)", "")}</span>
                    </div>
                    <span className="activity-date">
                      {a.StartedAt.slice(0, 10)}
                      <Badge>{a.ActivityStatus}</Badge>
                    </span>
                  </div>
                ))}
            </div>
          ) : (
            <Empty
              title="No vehicle activities"
              description="Recorded activity from this company will appear here."
            />
          )}
        </Panel>
        <Panel
          title="Provider network"
          description="The partners behind this journey"
          action={
            <Button
              variant="ghost"
              size="small"
              onClick={() => navigateTo("providers")}
            >
              View network
              <ArrowUpRight size={14} />
            </Button>
          }
        >
          {s.providers.length ? (
            <div className="partner-list">
              {s.providers.slice(0, 4).map((p, i) => (
                <div key={p.Id}>
                  <span className={"partner-initial partner-" + i}>
                    {p.LegalName.slice(0, 1)}
                  </span>
                  <div>
                    <strong>{p.LegalName.replace(" (fictional)", "")}</strong>
                    <small>
                      Provider{" "}
                      <span className="mono">
                        PR-{String(p.Id).padStart(3, "0")}
                      </span>
                    </small>
                  </div>
                  <Badge>In network</Badge>
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="No authorized providers"
              description="Prepare the fictional scenario to add its three demonstration providers."
            />
          )}
        </Panel>
      </div>
      <p className="scope-footnote">
        Figures are calculated from the records currently in your authorized
        scope. Imported and demo transactions are synthetic; awards do not
        represent payments.
      </p>
    </>
  );
}
