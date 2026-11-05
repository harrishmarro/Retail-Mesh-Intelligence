import { useEffect, type ReactNode } from "react";
import {
  LayoutDashboard,
  Activity,
  ClipboardCheck,
  MessageCircle,
  ArrowLeftRight,
  ReceiptText,
  Building2,
  Network,
  Users,
  Settings,
  ChevronDown,
  LogOut,
  Menu,
  Plus,
  RefreshCw,
  PanelLeftClose,
} from "lucide-react";
import * as Select from "@radix-ui/react-select";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { actions, loadSession, signedOut } from "../app/store";
import { request } from "../app/client";
import type { View } from "../app/types";
import { Button } from "../components/ui";
import { Brand } from "./Auth";
const links: { view: View; label: string; icon: typeof LayoutDashboard }[] = [
  { view: "overview", label: "Overview", icon: LayoutDashboard },
  { view: "activities", label: "Vehicle activities", icon: ArrowLeftRight },
  { view: "incentives", label: "Incentives", icon: ReceiptText },
  { view: "providers", label: "Provider network", icon: Building2 },
  { view: "knowledge", label: "Knowledge base", icon: Network },
  { view: "onboarding", label: "Provider applications", icon: ClipboardCheck },
  { view: "observability", label: "Observability", icon: Activity },
  { view: "claims", label: "Incentive claims", icon: ReceiptText },
  { view: "chat", label: "Incentive assistant", icon: MessageCircle },
  { view: "concerns", label: "Provider concerns", icon: MessageCircle },
  { view: "members", label: "Team members", icon: Users },
  { view: "settings", label: "Workspace settings", icon: Settings },
];
export function navigateTo(view: View) {
  window.location.hash = view;
}
export default function Shell({ children }: { children: ReactNode }) {
  const dispatch = useAppDispatch();
  const session = useAppSelector((s) => s.session.data)!;
  const ui = useAppSelector((s) => s.ui);
  const workspace = useAppSelector((s) => s.workspace);
  const company = session.workspaces.find(
    (c) => c.company_id === workspace.companyId,
  );
  useEffect(() => {
    const change = () => {
      const id = location.hash.slice(1) as View;
      if (links.some((l) => l.view === id)) dispatch(actions.navigate(id));
      else dispatch(actions.navigate("overview"));
    };
    change();
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, [dispatch]);
  async function logout() {
    try {
      await request("/api/auth/logout", {}, session.csrf);
      dispatch(signedOut);
      dispatch(loadSession());
    } catch (e) {
      dispatch(
        actions.noticeChanged(
          e instanceof Error ? e.message : "Unable to sign out.",
        ),
      );
    }
  }
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      {ui.mobileOpen && (
        <button
          className="nav-scrim"
          aria-label="Close navigation"
          onClick={() => dispatch(actions.mobileChanged(false))}
        />
      )}
      <aside
        className={"sidebar" + (ui.mobileOpen ? " sidebar-open" : "")}
        aria-label="Main navigation"
      >
        <div className="sidebar-brand">
          <Brand />
          <Button
            variant="ghost"
            size="icon"
            className="nav-close"
            aria-label="Close navigation"
            onClick={() => dispatch(actions.mobileChanged(false))}
          >
            <PanelLeftClose size={18} />
          </Button>
        </div>
        <div className="workspace-switch">
          <span className="workspace-emblem">
            {company?.company_name.slice(0, 1) || "W"}
          </span>
          <Select.Root
            value={workspace.companyId?.toString() ?? ""}
            onValueChange={(v) => dispatch(actions.selectCompany(Number(v)))}
          >
            <Select.Trigger
              className="workspace-trigger"
              aria-label="Switch company workspace"
            >
              <span>
                <span className="workspace-hint">Company workspace</span>
                <Select.Value placeholder="Select company">
                  {company?.company_name}
                </Select.Value>
              </span>
              <Select.Icon>
                <ChevronDown size={15} />
              </Select.Icon>
            </Select.Trigger>
            <Select.Portal>
              <Select.Content
                className="select-content"
                position="popper"
                sideOffset={8}
              >
                <Select.Viewport>
                  {session.workspaces.map((c) => (
                    <Select.Item
                      className="select-item"
                      key={c.company_id}
                      value={String(c.company_id)}
                    >
                      <Select.ItemText>{c.company_name}</Select.ItemText>
                    </Select.Item>
                  ))}
                </Select.Viewport>
              </Select.Content>
            </Select.Portal>
          </Select.Root>
        </div>
        <span className="nav-group-label">Workspace</span>
        <nav>
          {links
            .filter((l) =>
              l.view === "chat"
                ? company?.Role === "Provider"
                : ["onboarding", "claims", "concerns"].includes(l.view)
                  ? (l.view !== "onboarding" && company?.Role === "Provider") ||
                    ["CompanyAdmin", "CompanyOperator"].includes(
                      company?.Role ?? "",
                    )
                  : ["members", "observability"].includes(l.view)
                    ? company?.Role === "CompanyAdmin"
                    : ["knowledge", "providers"].includes(l.view)
                      ? company?.Role !== "Provider"
                      : true,
            )
            .map(({ view, label, icon: Icon }) => (
              <a
                key={view}
                href={"#" + view}
                className={"nav-link" + (ui.view === view ? " nav-active" : "")}
                aria-current={ui.view === view ? "page" : undefined}
              >
                <Icon size={17} />
                {company?.Role === "Provider"
                  ? ((
                      {
                        overview: "My dashboard",
                        claims: "My incentive claims",
                        concerns: "My concerns",
                        settings: "My account",
                      } as Record<string, string>
                    )[view] ?? label)
                  : label}
              </a>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="workspace-note">
            <ShieldMark />
            <div>
              <strong>Evidence you can trace</strong>
              <p>Every award keeps its sources.</p>
            </div>
          </div>
          <div className="user-row">
            <span className="avatar">
              {session.user?.DisplayName.split(" ")
                .map((n) => n[0])
                .slice(0, 2)
                .join("")}
            </span>
            <div>
              <strong>{session.user?.DisplayName}</strong>
              <span>
                {company?.Role === "CompanyAdmin"
                  ? "Company administrator"
                  : (company?.Role ?? "No membership")}
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Sign out"
              onClick={logout}
            >
              <LogOut size={16} />
            </Button>
          </div>
        </div>
      </aside>
      <div className="workspace-area">
        <header className="topbar">
          <div className="breadcrumb">
            <Button
              variant="ghost"
              size="icon"
              className="nav-open"
              aria-label="Open navigation"
              onClick={() => dispatch(actions.mobileChanged(true))}
            >
              <Menu size={19} />
            </Button>
            <span>{company?.company_name ?? "Retail-Mesh"}</span>
            <span className="breadcrumb-slash">/</span>
            <strong>{links.find((l) => l.view === ui.view)?.label}</strong>
          </div>
          <div className="topbar-actions">
            <span className="local-chip">Local workspace</span>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Refresh workspace"
              title="Refresh workspace"
              onClick={() => dispatch(loadSession())}
            >
              <RefreshCw size={15} />
            </Button>
            {company?.Role === "CompanyAdmin" && (
              <Button
                variant="ghost"
                size="icon"
                aria-label="Create company workspace"
                title="Create company workspace"
                onClick={() => dispatch(actions.modalChanged("company"))}
              >
                <Plus size={18} />
              </Button>
            )}
          </div>
        </header>
        <main id="main-content" className="content-sheet">
          {children}
        </main>
      </div>
    </div>
  );
}
function ShieldMark() {
  return (
    <svg
      width="22"
      height="25"
      viewBox="0 0 22 25"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M11 2L20 5V12C20 17 16 21 11 23C6 21 2 17 2 12V5L11 2Z"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <path d="M7 12L10 15L15 9" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}
