import { useEffect, useState } from "react";
import { AlertCircle, RefreshCw, X } from "lucide-react";
import { useAppDispatch, useAppSelector } from "./app/hooks";
import { actions, loadSession, loadWorkspace } from "./app/store";
import { Button, Empty, Skeleton } from "./components/ui";
import Auth from "./features/Auth";
import Shell from "./features/Shell";
import Overview from "./features/Overview";
import { Activities, Providers } from "./features/Records";
import { Incentives } from "./features/RunDetail";
import { Members, Settings, Modals } from "./features/Settings";
import KnowledgeBase from "./features/KnowledgeBase";
import ProviderOnboarding from "./features/ProviderOnboarding";
import Observability from "./features/Observability";
import ProviderSignup, {
  ProviderApplicationStatus,
} from "./features/ProviderSignup";
import { Claims, Concerns, ProviderChat } from "./features/ProviderWorkspace";
import { ActivateProvider } from "./features/AccountAccess";
export default function App() {
  const dispatch = useAppDispatch();
  const [publicPage, setPublicPage] = useState(
    () => location.hash.split("?")[0],
  );
  useEffect(() => {
    const update = () => setPublicPage(location.hash.split("?")[0]);
    addEventListener("hashchange", update);
    return () => removeEventListener("hashchange", update);
  }, []);
  const session = useAppSelector((s) => s.session);
  const workspace = useAppSelector((s) => s.workspace);
  const ui = useAppSelector((s) => s.ui);
  useEffect(() => {
    if (session.phase === "idle") dispatch(loadSession());
  }, [dispatch, session.phase]);
  useEffect(() => {
    if (session.data?.user && workspace.companyId) {
      const task = dispatch(loadWorkspace(workspace.companyId));
      return () => task.abort();
    }
  }, [dispatch, workspace.companyId, session.data]);
  if (session.phase === "error" && !session.data)
    return (
      <main className="connection-page">
        <AlertCircle size={25} />
        <h1>Retail-Mesh is unavailable</h1>
        <p>{session.error?.message}</p>
        <Button onClick={() => dispatch(loadSession())}>
          <RefreshCw size={15} />
          Try again
        </Button>
      </main>
    );
  if (!session.data)
    return (
      <main className="loading-page">
        <span className="loading-wordmark">Retail-Mesh</span>
        <Skeleton rows={3} />
      </main>
    );
  if (publicPage === "#activate") return <ActivateProvider />;
  if (publicPage === "#provider-signup") return <ProviderSignup />;
  if (publicPage === "#provider-application")
    return <ProviderApplicationStatus />;
  if (!session.data.user) return <Auth />;
  const company = session.data.workspaces.find(
    (c) => c.company_id === workspace.companyId,
  );
  return (
    <Shell>
      {ui.notice && (
        <div className="toast" role="status">
          <span>{ui.notice}</span>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Dismiss notification"
            onClick={() => dispatch(actions.noticeChanged(null))}
          >
            <X size={15} />
          </Button>
        </div>
      )}
      {workspace.error && (
        <div className="workspace-error" role="alert">
          <AlertCircle size={16} />
          <span>{workspace.error.message}</span>
          <Button
            variant="ghost"
            size="small"
            onClick={() =>
              workspace.companyId &&
              dispatch(loadWorkspace(workspace.companyId))
            }
          >
            Retry
          </Button>
        </div>
      )}
      {!company ? (
        <>
          <div className="page-heading">
            <h1>Company workspace</h1>
          </div>
          <Empty
            title="No active company membership"
            description="Create a company workspace or ask its administrator to grant access."
            action={
              session.data.workspaces.some((w) => w.Role === "CompanyAdmin") ? (
                <Button
                  variant="primary"
                  onClick={() => dispatch(actions.modalChanged("company"))}
                >
                  Create workspace
                </Button>
              ) : undefined
            }
          />
        </>
      ) : workspace.phase === "loading" && workspace.updatedAt === null ? (
        <>
          <div className="page-heading">
            <h1>Loading company workspace</h1>
          </div>
          <Skeleton rows={6} />
        </>
      ) : (
        <>
          {ui.view === "overview" && <Overview />}
          {ui.view === "activities" && <Activities />}
          {ui.view === "incentives" && <Incentives />}
          {ui.view === "providers" && <Providers />}
          {ui.view === "knowledge" &&
            (company.Role !== "Provider" ? (
              <KnowledgeBase key={workspace.companyId} />
            ) : (
              <Empty
                title="Use the incentive assistant"
                description="Provider access includes policy explanations and your own claim records. Knowledge graph access is reserved for operators, administrators and analysts."
              />
            ))}
          {ui.view === "claims" &&
            (["CompanyAdmin", "CompanyOperator", "Provider"].includes(
              company.Role,
            ) ? (
              <Claims key={workspace.companyId} />
            ) : (
              <Empty
                title="Claim access required"
                description="Claims are available to providers and company reviewers."
              />
            ))}
          {ui.view === "concerns" &&
            (["CompanyAdmin", "CompanyOperator", "Provider"].includes(
              company.Role,
            ) ? (
              <Concerns key={workspace.companyId} />
            ) : (
              <Empty
                title="Concern access required"
                description="Concerns are available to providers and company reviewers."
              />
            ))}
          {ui.view === "chat" && company.Role === "Provider" && (
            <ProviderChat key={workspace.companyId} />
          )}
          {ui.view === "onboarding" &&
            (["CompanyAdmin", "CompanyOperator"].includes(company.Role) ? (
              <ProviderOnboarding key={workspace.companyId} />
            ) : (
              <Empty
                title="Company administrator access required"
                description="Company operators and administrators review provider applications."
              />
            ))}
          {ui.view === "observability" &&
            (company.Role === "CompanyAdmin" ? (
              <Observability key={workspace.companyId} />
            ) : (
              <Empty
                title="Company administrator access required"
                description="Only administrators can view company observability."
              />
            ))}
          {ui.view === "members" &&
            (company.Role === "CompanyAdmin" ? (
              <Members />
            ) : (
              <Empty
                title="Company administrator access required"
                description="Only company administrators can manage workspace members."
              />
            ))}
          {ui.view === "settings" && <Settings key={workspace.companyId} />}
        </>
      )}
      <Modals />
    </Shell>
  );
}
