import { useEffect } from "react";
import {
  RefreshCw,
  Activity,
  Building2,
  ShieldCheck,
  Clock,
} from "lucide-react";
import { useWorkspaceResource } from "../app/resources";
import type { ObservabilityDocument } from "../app/types";
import { Button, Panel, Badge, Skeleton, Empty } from "../components/ui";
export default function Observability() {
  const { data, phase, error, reload } =
    useWorkspaceResource<ObservabilityDocument>("observability");
  useEffect(() => {
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") reload();
    }, 30000);
    return () => clearInterval(interval);
  }, [reload]);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Company observability</h1>
          <p>Operational status across the companies you administer.</p>
        </div>
        <Button onClick={reload} loading={phase === "loading"}>
          <RefreshCw size={15} />
          Refresh
        </Button>
      </div>
      {error && (
        <p className="inline-error" role="alert">
          {error.message}
        </p>
      )}
      {!data ? (
        phase === "loading" ? (
          <Skeleton rows={5} />
        ) : (
          <Empty
            title="No administrator telemetry"
            description="Only active CompanyAdmin memberships can access this dashboard."
          />
        )
      ) : (
        <>
          <div className="knowledge-summary">
            <span>
              <Building2 size={16} />
              <strong>{data.companies.length}</strong> administered companies
            </span>
            <Badge
              tone={
                data.service.database === "reachable" ? "positive" : "negative"
              }
            >
              Database {data.service.database}
            </Badge>
            <span>
              <Clock size={14} />
              Updated {new Date(data.generated_at).toLocaleTimeString()} ·
              refreshes every 30 seconds
            </span>
          </div>
          <p className="scope-footnote">{data.scope}</p>
          <div className="observability-companies">
            {data.companies.map((c) => (
              <Panel
                key={c.company_id}
                title={c.company_name}
                description={`COMPANY-${c.company_id}`}
                action={<Badge>{c.active_members} active members</Badge>}
              >
                <div className="observability-metrics">
                  <div>
                    <span>Provider records</span>
                    <strong>{c.providers}</strong>
                  </div>
                  <div>
                    <span>Vehicle activities</span>
                    <strong>{c.activities}</strong>
                  </div>
                  <div>
                    <span>Onboarding in progress</span>
                    <strong>{c.pending_applications}</strong>
                  </div>
                  <div>
                    <span>Recorded awards</span>
                    <strong>{c.recorded_awards}</strong>
                  </div>
                </div>
                <div className="telemetry-row">
                  <span>
                    <Activity size={14} />
                    {c.requests_24h} API requests / 24h
                  </span>
                  <span>{c.errors_24h} HTTP errors</span>
                  <span>
                    p95 {c.p95_ms === null ? "No samples" : `${c.p95_ms} ms`}
                  </span>
                  <span>{c.engine_runs} loaded engine runs</span>
                </div>
                <div className="company-benefits">
                  <strong>Recorded cash entitlement</strong>
                  {Object.entries(c.recorded_cash).length ? (
                    Object.entries(c.recorded_cash).map(([currency, value]) => (
                      <span key={currency}>
                        {currency}{" "}
                        {Number(value).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    ))
                  ) : (
                    <span>No cash award records</span>
                  )}
                  {Object.entries(c.other_benefits).map(([unit, value]) => (
                    <span key={unit}>
                      {value} {unit}
                    </span>
                  ))}
                </div>
                <div className="state-chips">
                  {Object.entries(c.onboarding_states).map(([state, count]) => (
                    <Badge key={state}>
                      {state} {count}
                    </Badge>
                  ))}
                </div>
                {c.imports.map((i) => (
                  <p className="scope-footnote" key={i.Id}>
                    <ShieldCheck size={13} />
                    Imported {i.SourceName} · {i.ContentSha256.slice(0, 12)}… ·{" "}
                    {new Date(i.ImportedAt * 1000).toLocaleString()}
                  </p>
                ))}
              </Panel>
            ))}
          </div>
          <Panel
            title="Company audit trail"
            description="Most recent 100 events across your administered companies."
          >
            {data.events.length ? (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Company</th>
                      <th>Action</th>
                      <th>Reference</th>
                      <th>Actor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.events.map((e) => (
                      <tr key={e.Id}>
                        <td>{new Date(e.CreatedAt * 1000).toLocaleString()}</td>
                        <td>{e.company_name}</td>
                        <td>{e.Action}</td>
                        <td className="audit-reference">{e.TargetReference}</td>
                        <td>User #{e.UserId}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty
                title="No company events yet"
                description="Imports, membership changes and provider reviews create audit entries."
              />
            )}
          </Panel>
          <div className="observability-notes">
            {data.limitations.map((l) => (
              <p className="scope-footnote" key={l}>
                {l}
              </p>
            ))}
          </div>
        </>
      )}
    </>
  );
}
