# Domain glossary

- ParentCompany: company with independently managed memberships, rules and provider authorizations.
- Provider: registered business identity. Authorization and outlet capabilities determine its company relationship; membership determines a person's access.
- ProviderApplication: staging workflow. Draft → Submitted → UnderReview → Validated → Approved → Provisioned. Review may return NeedsChanges or Rejected. Only approval inserts/authorizes the provider in operational master data.
- CustomerAccount: provider-local source account. Never globally identify customers from names or contact matches.
- CustomerIdentityLink: an explicit verification assertion between source accounts; status and evidence timing matter.
- VehicleActivity: a sale, rental or service with exactly one subtype and source reference. Replacement rental points to a Service record; rental vehicle and serviced vehicle may differ.
- RuleVersion / MetricDefinitionVersion: effective-dated policy and measurement definitions.
- EventEvaluation / PeriodEvaluation: preserved source decisions. Supplied CSV decisions explicitly describe manual review.
- EventAward / PeriodAward: accepted evaluations and their benefit components. Cash, points and other benefits keep distinct units.
- IncentiveRun: separate immutable snapshot produced by the supported fleet_journey_v1 engine. Imported CSV awards do not imply a matching IncentiveRun.
- OKF: versioned project interchange bundle for authorized, read-only analysis, based on open serialization standards.
