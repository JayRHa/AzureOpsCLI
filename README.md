<!-- jr-brand:start -->
<div align="center">
  <a href="https://jannikreinhard.com/">
    <img src="https://raw.githubusercontent.com/JayRHa/.github/main/assets/readme/tool.svg" alt="Jannik Reinhard — AI, Cloud and Endpoint Management" width="100%">
  </a>
  <h1>Azure Ops CLI</h1>
  <p><strong>Agent-friendly Azure operations evidence for resources, deployments, activity logs and health.</strong></p>
  <p>
  <a href="https://jannikreinhard.com/"><img src="https://img.shields.io/badge/Website-0A5FC0?style=flat-square&amp;logo=wordpress&amp;logoColor=white" alt="Website"></a>
  <a href="https://github.com/JayRHa"><img src="https://img.shields.io/badge/GitHub-081427?style=flat-square&amp;logo=github&amp;logoColor=white" alt="GitHub"></a>
  <a href="https://www.linkedin.com/in/jannik-r/"><img src="https://img.shields.io/badge/LinkedIn-0795FF?style=flat-square&amp;logo=linkedin&amp;logoColor=white" alt="LinkedIn"></a>
  <a href="https://x.com/jannik_reinhard"><img src="https://img.shields.io/badge/X-081427?style=flat-square&amp;logo=x&amp;logoColor=white" alt="X"></a>
  <a href="https://www.youtube.com/@ModernDevMgmt/featured"><img src="https://img.shields.io/badge/YouTube-0A5FC0?style=flat-square&amp;logo=youtube&amp;logoColor=white" alt="YouTube"></a>
</p>
  <p><sub>Tool · App · CLI · Python · Practical by design</sub></p>
</div>
<!-- jr-brand:end -->

Agent-friendly Azure operations evidence for resources, App Service, deployments, activity logs and health.

Inspect. Correlate. Recover.


Azure Resource Manager | Python CLI | JSON-first | Agent Ready


## Overview

Azure Ops CLI is a lightweight operations toolkit for collecting Azure Resource Manager evidence in a predictable JSON shape. It is built for terminal troubleshooting, CI checks and AI-agent workflows where the agent needs to inspect what is deployed, when it changed and whether Azure reports health issues.

The CLI focuses on read-heavy operational paths: subscription resources, App Service metadata and config, resource group deployments, Activity Log events and Resource Health. Every command supports `--dry-run` so the exact ARM request can be reviewed before execution.

## How It Works

```mermaid
flowchart LR
    Operator[Human, script or AI agent] --> CLI[azure-ops CLI]
    CLI --> Auth[Azure access token or client credentials]
    CLI --> ARM[Azure Resource Manager]
    ARM --> Evidence[Resources, deployments, logs, health]
    Evidence --> JSON[Structured JSON output]
```

## Quickstart

```bash
git clone https://github.com/JayRHa/AzureOpsCLI.git
cd AzureOpsCLI
python -m pip install -e .

export AZURE_ACCESS_TOKEN="<access-token>"
azure-ops resources --subscription-id "<subscription-id>" --dry-run
```

Use client credentials instead of a prebuilt token:

```bash
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_ID="<app-registration-client-id>"
export AZURE_CLIENT_SECRET="<client-secret>"

azure-ops appservice show --subscription-id "<subscription-id>" --resource-group "rg-prod" --name "app-prod"
```

## Commands

| Command | Purpose |
| --- | --- |
| `azure-ops resources` | List subscription resources and optionally filter by resource type or name. |
| `azure-ops appservice show` | Read App Service resource metadata. |
| `azure-ops appservice config` | Read App Service web configuration. |
| `azure-ops deployments` | List resource group ARM deployments. |
| `azure-ops activity-log` | Read Azure Activity Log management events for a lookback window. |
| `azure-ops health` | Read Azure Resource Health for one resource ID. |
| `azure-ops request` | Execute a custom ARM request by path and api-version. |

## Examples

```bash
azure-ops resources --subscription-id "<sub>" --resource-type Microsoft.Web/sites
azure-ops deployments --subscription-id "<sub>" --resource-group "rg-prod" --top 10
azure-ops activity-log --subscription-id "<sub>" --resource-group "rg-prod" --since-hours 6
azure-ops health --resource-id "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app>"
```

## Azure Permissions

The CLI uses Azure Resource Manager read operations. A service principal with Reader permissions on the target subscription or resource group is enough for most commands. App Service config reads may require access to the specific App Service resource.

## Output Contract

All commands write JSON to stdout. Errors are written to stderr with a non-zero exit code. This keeps the tool predictable for shell scripts, CI jobs and agent toolchains.

## License

MIT License. See [LICENSE](LICENSE).

<!-- jr-brand-footer:start -->

---

<div align="center">
  <p><sub>Built and maintained by <a href="https://jannikreinhard.com/">Jannik Reinhard</a> · Microsoft MVP for Security and AI Platform.</sub></p>
  <p><a href="https://www.buymeacoffee.com/jannikreinf">Support the open-source work</a></p>
  <p><strong>Stay healthy, Cheers Jannik</strong></p>
</div>

<!-- jr-brand-footer:end -->
