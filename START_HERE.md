# Start Retail-Mesh

In the extracted project folder:

```zsh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
chmod +x quickstart.sh
./quickstart.sh
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Create the first administrator and select **Start with the 2 supplied companies**. The reviewed database is already ingested: 574 synthetic domain records, two companies, seven providers and 35 activities. No demo credentials are shipped.

Administrators enable the separate public provider signup page in **Workspace settings**, then share its URL. Operators review submitted applications and record the three validation checks. Accepted applicants activate their own password through their private tracking page, then use the normal sign-in screen. Providers see their own dashboard, claims, assistant and concerns. Their workspace requests go to the operator/administrator and never create workspaces automatically.

Knowledge base is available to administrators, operators and analysts. Providers cannot view/export it. Company administrators alone manage members, workspace creation, signup configuration and observability. All users can change their own password in settings.

Read [README.md](README.md), [role/workflow guide](doc/ROLE_WORKFLOW_GUIDE.md) and [data review](doc/DATA_REVIEW.md). The prebuilt React interface is included; Node is only needed for UI development. Use `requirements.txt` for complete dependencies; `requirements-knowledge.txt` remains the graph-only subset.
