# React operations console: design decisions

Design direction: Framed sheet, seed 744845260, dealt with Taste's app-screen workflow. User explicitly requested the React/Redux migration, overriding the skill's general advice to retain an existing framework.

## Subject inventory

- Parent-company workspace and three scoped roles.
- Maple Motors, Harbour Service and Island Rentals fictional partner journey.
- Completed sale -> verified service -> replacement rental -> provider entitlement.
- CAD 150 from one rule, not an invented growth metric.
- Twelve historical fleet vehicles before the qualifying sale.
- Six policy checks with original evidence retained.
- Versioned rules and immutable evaluation runs.
- RDF/Turtle and JSON-LD export with SHACL validation.
- Company-scoped providers, activity lists, membership and audit history.
- Optional AI explanation alongside authoritative recorded facts.

## One question per screen

- Overview: What needs to happen next to qualify and explain the provider incentive?
- Activities: Which vehicle activities are recorded in this company/provider scope?
- Incentives: Which evaluations produced awards, and why?
- Providers: Which partner records and operations are connected to this company?
- Knowledge: Which source relationships support the selected decision?
- Members: Who can access this company and at what role?
- Settings: Which company context and narration settings are active?

## Visual system

A low-chroma blue-green L-frame and a white working sheet. IBM Plex Sans loaded locally; IBM Plex Mono for record IDs only. Near-black main action, restrained teal on the evidence path, and semantic status marks. Flat panels, 24px grid gap, 228px labelled navigation, 48px top bar, 16px sheet corners and 6px controls. Numeric values are tabular and table amounts align right. No fabricated trend charts or vanity figures.

Signature element: the completed vehicle journey becomes an evidence route through Sale, Service, Rental and Award, derived from the selected run's actual checks and sources. It does not claim a completed path before evaluation.

Motion is interaction feedback only: opening dialogs/panels and acknowledging a selected run through scoped GSAP useGSAP, with reduced-motion support. No entrance delays on operational data.

## Requested resources

- GSAP skills: React hook/context cleanup and transform/opacity performance guidance applied.
- Taste skill: app-screen draw, source lint and browser-inspection attempt applied.
- shadcn UI MCP: server connected through its public stdio tools. Component retrieval failed with upstream v4 registry not-found responses; official component documentation is the fallback reference. Do not claim successful component retrieval from that server.
- 21st.dev/Magic: current repository and skill inspected. No API_KEY_21ST is configured, so no authenticated catalog or credit-consuming generation calls were made.

## Verification limitation

Before inspection was attempted with the provided Taste inspector and local Chrome. Chrome failed at process-singleton socket creation with Operation not permitted. The environment does not currently support the requested browser screenshot loop. Record source lint, TypeScript/build, component/store tests and HTTP integration honestly; do not fabricate visual screenshots or a 0-FAIL browser-inspection claim.

A separate static React fixture render succeeded, but cloud-browser file navigation was blocked by protocol policy. It was not used as evidence of browser rendering.

Resource revisions inspected:

| Resource | Commit |
|---|---|
| greensock/gsap-skills | aed9cfd3277740755f6bfc1155c7aa645403b760 |
| leonxlnx/taste-skill | 12af471f627f866411b4bd785b19646d3672784c |
| 21st-dev/magic-mcp | 6b5299e8a83ceffa73d4fc4e148905bb3eeeeb55 |
| Jpisnice/shadcn-ui-mcp-server | 30efb8a0bf8d968e4c6635e4491c20da96e49d20 |

The primitives follow the public shadcn Button composition pattern with Radix, cva and local CSS. No 21st.dev-generated component is included. The resource repositories are design references, not runtime dependencies.
