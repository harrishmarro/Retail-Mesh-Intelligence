import {
  Search,
  ArrowUpRight,
  CarFront,
  KeyRound,
  Wrench,
  Filter,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { actions } from "../app/store";
import {
  Badge,
  Button,
  Empty,
  Input,
  Tabs,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { ScenarioAction, money, useRunActions } from "./Overview";
export function Filters({
  tabs,
  placeholder,
}: {
  tabs: string[];
  placeholder: string;
}) {
  const dispatch = useAppDispatch();
  const { query, status } = useAppSelector((s) => s.ui);
  return (
    <>
      <Tabs
        value={status}
        onValueChange={(v) => dispatch(actions.statusChanged(v))}
      >
        <TabsList className="underline-tabs">
          {tabs.map((t) => (
            <TabsTrigger className="underline-tab" key={t} value={t}>
              {t}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <div className="filter-row">
        <div className="search-field">
          <Search size={16} />
          <Input
            aria-label={placeholder}
            placeholder={placeholder}
            value={query}
            onChange={(e) => dispatch(actions.queryChanged(e.target.value))}
          />
        </div>
        <span className="filter-hint">
          <Filter size={14} />
          Current workspace scope
        </span>
      </div>
    </>
  );
}
export function ActivityIcon({ kind }: { kind: string }) {
  const Icon =
    kind === "Sale" ? CarFront : kind === "Rental" ? KeyRound : Wrench;
  return <Icon size={17} strokeWidth={1.5} />;
}
export function Activities() {
  const s = useAppSelector((s) => s.workspace.summary);
  const { query, status } = useAppSelector((s) => s.ui);
  const rows = s.activities.filter(
    (a) =>
      (status === "All" || a.ActivityKind === status) &&
      [
        a.Provider,
        a.ActivityKind,
        a.OfficialActivityReference,
        a.ActivityStatus,
      ].some((v) => v.toLowerCase().includes(query.toLowerCase())),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Vehicle activities</h1>
          <p>A consistent record of sales, services and replacement rentals.</p>
        </div>
        <ScenarioAction />
      </div>
      <Filters
        tabs={["All", "Sale", "Service", "Rental"]}
        placeholder="Search reference or provider"
      />
      <div className="table-caption">
        {rows.length} {rows.length === 1 ? "activity" : "activities"}
      </div>
      {rows.length ? (
        <div className="data-table-wrap">
          <table className="data-table activity-table">
            <thead>
              <tr>
                <th>Activity reference</th>
                <th>Provider</th>
                <th>Type</th>
                <th>Status</th>
                <th className="num">Started</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.Id}>
                  <td>
                    <div className="table-identity">
                      <ActivityIcon kind={a.ActivityKind} />
                      <div>
                        <strong className="mono">
                          {a.OfficialActivityReference}
                        </strong>
                        <small>Activity #{a.Id}</small>
                      </div>
                    </div>
                  </td>
                  <td>{a.Provider.replace(" (fictional)", "")}</td>
                  <td>{a.ActivityKind}</td>
                  <td>
                    <Badge>{a.ActivityStatus}</Badge>
                  </td>
                  <td className="num">
                    <span>{a.StartedAt.slice(0, 10)}</span>
                    <small>{a.StartedAt.slice(11, 16)} UTC</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title={
            query || status !== "All"
              ? "No matching activities"
              : "No vehicle activities yet"
          }
          description={
            query || status !== "All"
              ? "Try another reference, provider or activity type."
              : "Prepare the fictional company journey to record its sale, service and rental."
          }
        />
      )}
      <p className="scope-footnote">
        Activity timestamps are shown in UTC. The supplied CSV records and the
        optional demo are synthetic, with separate source references.
      </p>
    </>
  );
}
export function Providers() {
  const s = useAppSelector((s) => s.workspace.summary);
  const { query } = useAppSelector((s) => s.ui);
  const rows = s.providers.filter((p) =>
    p.LegalName.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Provider network</h1>
          <p>Partner records connected to this company.</p>
        </div>
        <ScenarioAction />
      </div>
      <Filters tabs={["All"]} placeholder="Search provider name" />
      <div className="table-caption">
        {rows.length} {rows.length === 1 ? "provider" : "providers"} in your
        scope
      </div>
      {rows.length ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Provider</th>
                <th>Recorded operations</th>
                <th>Network</th>
                <th className="num">Loaded incentive awards</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p, i) => {
                const kinds = [
                  ...new Set(
                    s.activities
                      .filter((a) => a.Provider === p.LegalName)
                      .map((a) => a.ActivityKind),
                  ),
                ];
                const runs = s.runs.filter(
                  (r) => r.beneficiary_id === p.Id && r.result === "Qualified",
                );
                const totals: Record<string, number> = {};
                for (const r of new Map(runs.map((r) => [r.id, r])).values())
                  totals[r.currency] =
                    (totals[r.currency] ?? 0) + (r.amount_minor ?? 0);
                return (
                  <tr key={p.Id}>
                    <td>
                      <div className="table-identity">
                        <span className={"partner-initial partner-" + i}>
                          {p.LegalName[0]}
                        </span>
                        <div>
                          <strong>
                            {p.LegalName.replace(" (fictional)", "")}
                          </strong>
                          <small className="mono">
                            PR-{String(p.Id).padStart(3, "0")}
                          </small>
                        </div>
                      </div>
                    </td>
                    <td>{kinds.join(", ") || "—"}</td>
                    <td>
                      <Badge>In network</Badge>
                    </td>
                    <td className="num">
                      {runs.length
                        ? Object.entries(totals).map(([currency, total]) => (
                            <div key={currency}>{money(total, currency)}</div>
                          ))
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No providers found"
          description={
            query
              ? "Try another provider name."
              : "Prepare the fictional scenario to add its authorized providers."
          }
        />
      )}
      <p className="scope-footnote">
        Recorded operations describe the loaded activity, rather than a complete
        list of each provider’s approved capabilities.
      </p>
    </>
  );
}
export function RunsTable({ onInspect }: { onInspect?: () => void }) {
  const s = useAppSelector((s) => s.workspace.summary);
  const { query, status } = useAppSelector((s) => s.ui);
  const inspect = useRunActions();
  const rows = s.runs.filter(
    (r) =>
      (status === "All" || r.result === status) &&
      [r.beneficiary, String(r.id), r.result].some((v) =>
        v.toLowerCase().includes(query.toLowerCase()),
      ),
  );
  return (
    <>
      <Filters
        tabs={["All", "Qualified", "Rejected"]}
        placeholder="Search evaluation or provider"
      />
      <div className="table-caption">
        {rows.length} saved {rows.length === 1 ? "evaluation" : "evaluations"}
      </div>
      {rows.length ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Evaluation</th>
                <th>Beneficiary</th>
                <th>Result</th>
                <th className="num">Calculated amount</th>
                <th className="num">Evaluated</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">RUN-{String(r.id).padStart(3, "0")}</td>
                  <td>{r.beneficiary.replace(" (fictional)", "")}</td>
                  <td>
                    <Badge
                      tone={r.result === "Qualified" ? "positive" : "negative"}
                    >
                      {r.result}
                    </Badge>
                  </td>
                  <td className="num">
                    {r.amount_minor === null
                      ? "—"
                      : money(r.amount_minor, r.currency)}
                  </td>
                  <td className="num">{r.created_at.slice(0, 10)}</td>
                  <td>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={() => {
                        inspect(r.id);
                        onInspect?.();
                      }}
                    >
                      Inspect
                      <ArrowUpRight size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No matching evaluations"
          description="An evaluation is saved when the versioned rule checks a provider journey."
        />
      )}
    </>
  );
}

export function RecordedAwards() {
  const rows = useAppSelector((s) => s.workspace.summary.recorded_awards ?? []);
  return (
    <>
      <p className="scope-footnote">
        These are recorded Event/Period awards and their declared benefit units.
        Imported awards retain the CSV's manual-review decisions; they are
        separate from automated engine evaluations and do not represent settled
        payments.
      </p>
      {rows.length ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Award</th>
                <th>Source decision</th>
                <th>Benefits</th>
                <th>Status</th>
                <th>Issued</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.kind + ":" + r.id}>
                  <td>
                    {r.kind} #{r.id}
                  </td>
                  <td>
                    {r.origin}
                    <small className="table-secondary">
                      Evaluation #{r.evaluation_id} · Rule #{r.rule_id}
                    </small>
                  </td>
                  <td>
                    {r.components.map((c, i) => (
                      <div key={i}>
                        {c.BenefitValue} {c.Currency ?? c.UnitCode} ·{" "}
                        {c.RewardType}
                      </div>
                    ))}
                  </td>
                  <td>
                    <Badge>{r.status}</Badge>
                  </td>
                  <td>{r.issued_at.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No recorded awards in this company"
          description="Imported Event/Period awards appear here. Engine evaluations are in the evaluation register."
        />
      )}
    </>
  );
}
