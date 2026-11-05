import { useMemo, useState, type FormEvent } from "react";
import {
  Database,
  Download,
  Search,
  Network,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { useWorkspaceResource } from "../app/resources";
import { useAppSelector } from "../app/hooks";
import { request } from "../app/client";
import type { KnowledgeDocument, KnowledgeNode } from "../app/types";
import {
  Button,
  Panel,
  Input,
  Empty,
  Skeleton,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui";
import { Knowledge as DecisionKnowledge } from "./RunDetail";
export function nodeLabel(n: KnowledgeNode) {
  for (const k of [
    "LegalName",
    "OfficialActivityReference",
    "RuleName",
    "MetricName",
    "ProgramName",
    "ModelName",
    "ExistingCustomerReference",
    "VIN",
    "ExistingCapabilityDesignation",
    "OutletName",
  ])
    if (typeof n["rm:" + k] === "string") return n["rm:" + k] as string;
  return `${n["rm:sourceTable"]} #${n["rm:sourceRowId"]}`;
}
function isLink(v: unknown): v is { "@id": string } {
  return !!v && typeof v === "object" && "@id" in v;
}
export default function KnowledgeBase() {
  const { data, phase, error, reload, companyId } =
    useWorkspaceResource<KnowledgeDocument>("knowledge");
  const [query, setQuery] = useState("");
  const [table, setTable] = useState("All");
  const [selectedId, setSelectedId] = useState("");
  const [question, setQuestion] = useState(
    "Which providers are in this company?",
  );
  const [answer, setAnswer] = useState<{
    answer: string;
    sources: { type: string; id: number; uri: string }[];
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [askError, setAskError] = useState("");
  const csrf = useAppSelector((s) => s.session.data?.csrf ?? "");
  const nodes = data?.["@graph"] ?? [];
  const byId = useMemo(() => new Map(nodes.map((n) => [n["@id"], n])), [data]);
  const filtered = nodes.filter(
    (n) =>
      (table === "All" || n["rm:sourceTable"] === table) &&
      JSON.stringify(n).toLowerCase().includes(query.toLowerCase()),
  );
  const selected = byId.get(selectedId) || filtered[0];
  const relations = selected
    ? nodes
        .flatMap((n) =>
          Object.entries(n).flatMap(([key, value]) =>
            isLink(value) &&
            (n === selected || value["@id"] === selected["@id"])
              ? [
                  {
                    from: n,
                    to: byId.get(value["@id"])!,
                    label: key.replace("rm:", ""),
                  },
                ]
              : [],
          ),
        )
        .filter((r) => r.to)
    : [];
  async function ask(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true);
    setAskError("");
    try {
      setAnswer(
        await request(
          "/api/workspace/knowledge-ask",
          { company_id: companyId, question },
          csrf,
        ),
      );
    } catch (e) {
      setAskError(e instanceof Error ? e.message : "Could not answer");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Knowledge base</h1>
          <p>
            Browse source records, follow relationships and export an
            agent-readable snapshot.
          </p>
        </div>
        <div className="button-row">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Refresh knowledge base"
            onClick={reload}
          >
            <RefreshCw size={16} />
          </Button>
          <Button asChild variant="primary">
            <a href={`/api/workspace/knowledge-export?company_id=${companyId}`}>
              <Download size={15} />
              Download OKF
            </a>
          </Button>
        </div>
      </div>
      <Tabs defaultValue="records">
        <TabsList className="underline-tabs primary-tabs">
          <TabsTrigger className="underline-tab" value="records">
            Company knowledge
          </TabsTrigger>
          <TabsTrigger className="underline-tab" value="decisions">
            Engine decision evidence
          </TabsTrigger>
        </TabsList>
        <TabsContent value="records">
          {error && (
            <p role="alert" className="inline-error">
              {error.message} <Button onClick={reload}>Retry</Button>
            </p>
          )}
          {phase === "loading" && !data ? (
            <Skeleton rows={5} />
          ) : data ? (
            <>
              <div className="knowledge-summary">
                <span>
                  <Database size={16} />
                  <strong>{data.summary.nodes}</strong> source records
                </span>
                <span>
                  <Network size={16} />
                  <strong>{data.summary.edges}</strong> relations
                </span>
                <Badge
                  tone={data.validation.conforms ? "positive" : "negative"}
                >
                  {data.validation.conforms
                    ? "Scope validated"
                    : "Validation failed"}
                </Badge>
                <span>
                  {data.scope.role === "Provider"
                    ? "Provider scope"
                    : "Company scope"}
                </span>
              </div>
              <div className="knowledge-layout">
                <section className="panel knowledge-register">
                  <div className="knowledge-filters">
                    <label className="search-field">
                      <Search size={16} />
                      <Input
                        aria-label="Search knowledge records"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search record, reference or policy"
                      />
                    </label>
                    <select
                      aria-label="Filter knowledge table"
                      className="input"
                      value={table}
                      onChange={(e) => setTable(e.target.value)}
                    >
                      <option>All</option>
                      {Object.keys(data.summary.tables)
                        .sort()
                        .map((t) => (
                          <option key={t}>{t}</option>
                        ))}
                    </select>
                  </div>
                  <p className="table-caption">
                    {filtered.length} matching records · first 100 shown
                  </p>
                  <div className="knowledge-node-list">
                    {filtered.slice(0, 100).map((n) => (
                      <button
                        className={
                          "knowledge-node" +
                          (selected === n ? " knowledge-node-selected" : "")
                        }
                        key={n["@id"]}
                        onClick={() => setSelectedId(n["@id"])}
                      >
                        <span>
                          <strong>{nodeLabel(n)}</strong>
                          <small>
                            {n["rm:sourceTable"]} · DB #{n["rm:sourceRowId"]}
                            {n["rm:sourceCsvId"]
                              ? ` · CSV #${n["rm:sourceCsvId"]}`
                              : ""}
                          </small>
                        </span>
                        <ArrowRight size={14} />
                      </button>
                    ))}
                    {!filtered.length && (
                      <Empty
                        title="No matching source records"
                        description="Try a different table or search term."
                      />
                    )}
                  </div>
                </section>
                <div>
                  {selected ? (
                    <Panel
                      title={nodeLabel(selected)}
                      description={`${selected["rm:sourceTable"]} · source record ${selected["rm:sourceRowId"]}`}
                    >
                      <div className="record-uri mono">{selected["@id"]}</div>
                      <dl className="knowledge-properties">
                        {Object.entries(selected)
                          .filter(([k, v]) => !k.startsWith("@") && !isLink(v))
                          .map(([k, v]) => (
                            <div key={k}>
                              <dt>{k.replace("rm:", "")}</dt>
                              <dd>{String(v)}</dd>
                            </div>
                          ))}
                      </dl>
                      <h3 className="knowledge-relations-heading">
                        Relationships
                      </h3>
                      {relations.length ? (
                        <>
                          <RelationshipGraph
                            selected={selected}
                            relations={relations.slice(0, 6)}
                            onSelect={setSelectedId}
                          />
                          <ul className="relation-list">
                            {relations.map((r, i) => (
                              <li key={i}>
                                <span>
                                  {r.from === selected
                                    ? "Outgoing"
                                    : "Incoming"}{" "}
                                  · {r.label}
                                </span>
                                <button
                                  onClick={() =>
                                    setSelectedId(
                                      (r.from === selected ? r.to : r.from)[
                                        "@id"
                                      ],
                                    )
                                  }
                                >
                                  {nodeLabel(
                                    r.from === selected ? r.to : r.from,
                                  )}
                                  <ArrowRight size={13} />
                                </button>
                              </li>
                            ))}
                          </ul>
                        </>
                      ) : (
                        <p className="scope-footnote">
                          No outgoing or incoming relationships in this exported
                          scope.
                        </p>
                      )}
                    </Panel>
                  ) : (
                    <Empty
                      title="No company records yet"
                      description="Import the supplied CSV dataset from Workspace settings or prepare the fictional scenario."
                    />
                  )}
                </div>
              </div>
              <div className="knowledge-bottom">
                <Panel
                  title="Ask the company knowledge"
                  description="A bounded read query with source citations. No external AI call."
                >
                  <form onSubmit={ask}>
                    <label htmlFor="knowledge-question" className="sr-only">
                      Company knowledge question
                    </label>
                    <textarea
                      id="knowledge-question"
                      className="textarea"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      maxLength={1000}
                      required
                      rows={2}
                    />
                    <Button type="submit" loading={busy}>
                      Ask knowledge base
                    </Button>
                  </form>
                  {askError && (
                    <p role="alert" className="inline-error">
                      {askError}
                    </p>
                  )}
                  {answer && (
                    <div className="assistant-response" aria-live="polite">
                      <p>{answer.answer}</p>
                      <div className="source-links">
                        {answer.sources.map((s) => (
                          <button
                            key={s.uri}
                            onClick={() => {
                              setSelectedId(s.uri);
                              setTable("All");
                              setQuery("");
                            }}
                          >
                            {s.type} #{s.id}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </Panel>
                <Panel
                  title="Open Knowledge Format · v1.0"
                  description="A documented project format built on JSON-LD, RDF, JSON Schema and SHACL."
                >
                  <p className="scope-footnote">
                    The OKF ZIP includes a manifest, source hashes, graph,
                    schema, provenance, glossary, SPARQL examples and an agent
                    guide. Customer contact details and credentials are
                    excluded.
                  </p>
                  <p className="scope-footnote">
                    {data.provenance.decision_semantics}
                  </p>
                  <div className="hash-row">
                    <span className="mono" title={data.snapshot_sha256}>
                      Snapshot {data.snapshot_sha256.slice(0, 16)}…
                    </span>
                  </div>
                  {data.provenance.sources.map((s) => (
                    <p className="scope-footnote" key={s.sha256}>
                      {s.filename} · {s.sha256.slice(0, 12)}…
                    </p>
                  ))}
                </Panel>
              </div>
            </>
          ) : (
            <Empty
              title="Knowledge base is loading"
              description="Company-scoped source records appear here after the request completes."
            />
          )}
        </TabsContent>
        <TabsContent value="decisions">
          <DecisionKnowledge />
        </TabsContent>
      </Tabs>
    </>
  );
}
function RelationshipGraph({
  selected,
  relations,
  onSelect,
}: {
  selected: KnowledgeNode;
  relations: { from: KnowledgeNode; to: KnowledgeNode; label: string }[];
  onSelect: (id: string) => void;
}) {
  const height = Math.max(116, relations.length * 62);
  return (
    <svg
      className="relationship-graph"
      viewBox={`0 0 560 ${height}`}
      role="img"
      aria-label={`Relationship graph for ${nodeLabel(selected)}; first ${relations.length} relations. Full list follows.`}
    >
      <defs>
        <marker
          id="relation-arrow"
          markerWidth="7"
          markerHeight="7"
          refX="6"
          refY="3"
          orient="auto"
        >
          <path d="M0 0L6 3L0 6" fill="none" stroke="currentColor" />
        </marker>
      </defs>
      <rect
        x="8"
        y={height / 2 - 25}
        width="175"
        height="50"
        rx="7"
        className="graph-current"
      />
      <text x="20" y={height / 2 - 3}>
        {selected["rm:sourceTable"]}
      </text>
      <text x="20" y={height / 2 + 14} className="graph-reference">
        DB #{selected["rm:sourceRowId"]}
      </text>
      {relations.map((r, i) => {
        const incoming = r.to === selected;
        const n = incoming ? r.from : r.to;
        const y = i * 62 + 30;
        return (
          <g key={i}>
            <path
              d={
                incoming
                  ? `M360 ${y} C270 ${y} 270 ${height / 2} 183 ${height / 2}`
                  : `M183 ${height / 2} C270 ${height / 2} 270 ${y} 360 ${y}`
              }
              fill="none"
              className="graph-edge"
              markerEnd="url(#relation-arrow)"
            />
            <text x="230" y={y - 8} className="graph-edge-label">
              {r.label}
            </text>
            <a
              href="#knowledge"
              onClick={(e) => {
                e.preventDefault();
                onSelect(n["@id"]);
              }}
              aria-label={`Inspect ${nodeLabel(n)}`}
            >
              <rect
                x="360"
                y={y - 22}
                width="190"
                height="45"
                rx="7"
                className="graph-related"
              />
              <text x="371" y={y - 3}>
                {n["rm:sourceTable"]}
              </text>
              <text x="371" y={y + 13} className="graph-reference">
                DB #{n["rm:sourceRowId"]}
              </text>
            </a>
          </g>
        );
      })}
    </svg>
  );
}
