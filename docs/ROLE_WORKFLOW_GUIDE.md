# Roles and provider workflow

Permissions are enforced by the HTTP API and company membership. Administrator access applies to companies they administer; it does not bypass another company's membership boundary. A person can have different roles in different companies.

| Capability | CompanyAdmin | CompanyOperator | Analyst | Provider |
| --- | --- | --- | --- | --- |
| Company dashboard and records | Assigned company | Assigned company | Assigned company | Own provider only |
| Graph / knowledge / OKF | Yes | Yes | Yes | No |
| Review provider applications and record checks | Yes | Yes | No | No |
| Submit public signup | Public applicant flow | Public applicant flow | Public applicant flow | Public applicant flow |
| Review claims and respond to concerns | Yes | Yes | No | Own requests and replies only |
| Incentive policy chatbot | Knowledge tools | Knowledge tools | Knowledge tools | Own enrolled policies and claim status |
| Create workspaces | Yes | No | No | No; request access |
| Team members, roles, signup configuration | Yes | No | No | No |
| Import data / company observability | Yes | No | No | No |
| Change own password | Yes | Yes | Yes | Yes |

## Signup and review

1. An administrator enables signup in settings. The company-specific public link opens a separate form without requiring a provider login.
2. Applicant supplies legal name, jurisdiction, registration number, contact name/email/phone, outlet/address, capability selections and supporting evidence references; website and requested programs are available. References are text pointers, not an implemented file-upload or verification service.
3. Submission creates an application and returns a private tracking link, not a provider, membership or user account. Keep that link: tracking tokens are hashed in storage and omitted from URL queries and Redux state.
4. Operator starts review and records business registration, contact authority and capability compliance evidence. Acceptance requires all three checks. Review history uses version checks to prevent stale decisions.
5. **Changes needed** returns a note to the applicant. They edit/resubmit using the private tracking page; prior validation checks are cleared. **Rejected** creates no provider or login.
6. **Accepted** creates the provider, company authorization, selected capabilities/program enrollment and single-use activation invitation atomically. The applicant sets their own password. An existing account must prove its current password; acceptance never overwrites it or grants administrator privileges. Activation expires after 48 hours; reviewers can reissue a private activation link. No email is sent automatically.

The private tracking token lasts up to 30 days; losing it requires contacting the reviewing company. Persisting references and reviewer checks does not itself verify external documents. Older staged internal applications remain readable after migration; new HTTP applications use public signup.

## Restricted provider operations

After activation, the normal login opens a provider-scoped dashboard. Claims can reference their own event activity or an eligible period rule. Requested money is stored in integer minor units. Each claim records evidence, statement, status, reviewer notes and immutable history. Statuses are Submitted, UnderReview, ChangesNeeded, Approved or Rejected. Returned claims can be corrected and resubmitted. Approval records a review decision and does not create awards or settle money.

The incentive assistant explains enrolled policy thresholds and claim status with rule references. It uses deterministic retrieval, not an unrestricted external model or graph download. Providers raise incentive concerns and converse with the operator/administrator privately. Other providers cannot read the thread or link someone else's claim.

**Request workspace access** creates a concern of kind WorkspaceAccess with a requested name. The operator may discuss and escalate it; only an administrator can deliberately create a workspace and grant membership. Marking a request resolved does neither automatically.

## Administrator and operator

Administrator has full implemented company management, including operator assignment, intake configuration, import, members and observability. Operator performs operational reviews, evidence checks, claim decisions and concern responses, with company graph access; they cannot grant roles, create companies or read administrator observability. Analyst has company analysis and knowledge access without review privileges. Existing password change revokes previous sessions; forgetting a password is not an implemented recovery flow.

The app binds to loopback. It has not been deployed, connected to business verification/email, or tested against a live external LLM. Historical milestone documents may describe older roles and table counts; this guide supersedes those descriptions.
