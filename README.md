# GKE FinOps Dashboard (CLI) v0.1.0

[![PyPI version](https://img.shields.io/pypi/v/gke-finops-dashboard.svg)](https://pypi.org/project/gke-finops-dashboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/marvasgit/gke-finops-dashboard.svg)](https://github.com/marvasgit/gke-finops-dashboard/stargazers)
[![Downloads](https://static.pepy.tech/badge/gke-finops-dashboard)](https://pepy.tech/project/gke-finops-dashboard)

A terminal-based GKE/GCP cost and resource dashboard built with Python and the [Rich](https://github.com/Textualize/rich) library. It provides an overview of GCP project spend, budget tracking, GKE cluster summaries, and allows exporting data to CSV or JSON.

---

## Features

- **Cost Analysis by Time Period**:
  - View current & previous month's total project spend by default.
  - Set custom time ranges (e.g., 7, 30, 90 days) with `--time-range` option (using Cloud Billing API).
- **GCP Budgets Information**: Displays budget limits and actual spend (using Budgets API).
- **GKE Cluster Status**: Detailed state information across specified/accessible locations (using GKE API).
- **Project Management**:
  - Specify target GCP Project IDs with `--projects`.
- **Location Control**: Specify GCP locations (regions/zones) for GKE discovery using `--locations`.
- **Export Options**:
  - CSV export with `--report-name` and `--report-type csv`.
  - JSON export with `--report-name` and `--report-type json`.
  - Export to both CSV and JSON formats with `--report-name` and `--report-type csv json`.
  - Specify output directory using `--dir`.
- **Improved Error Handling**: Resilient and user-friendly error messages for GCP APIs.
- **Beautiful Terminal UI**: Styled with the Rich library for a visually appealing experience.

---

## Prerequisites

- **Python 3.8 or later**: Ensure you have the required Python version installed.
- **Google Cloud SDK (`gcloud`) configured**: Set up `gcloud` and authenticate.
- **Application Default Credentials (ADC)**: Authenticate using `gcloud auth application-default login`.
- **GCP credentials with necessary IAM roles** on the target projects/billing account:
  - `roles/billing.viewer` (or `roles/billing.user` for cost, `roles/billing.costsManager` might be needed depending on API usage)
  - `roles/billing.budgetsViewer`
  - `roles/container.viewer`
  - Ensure required APIs are enabled: Cloud Billing API, Cloud Billing Budget API, Kubernetes Engine API.

---

## Installation

*(Note: Package name might change if published)*

There are several ways to install the GKE FinOps Dashboard:

### Option 1: Using pipx (Recommended when published)
```bash
pipx install gke-finops-dashboard
```
If you don't have `pipx`, install it with:
```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

### Option 2: Using pip (Recommended when published)
```bash
pip install gke-finops-dashboard
```

### Option 3: Using uv (Fast Python Package Installer)
[uv](https://github.com/astral-sh/uv) is a modern Python package installer and resolver that's extremely fast.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

uv pip install gke-finops-dashboard
```

### Option 4: From Source (Current method)
```bash
# Clone the repository (Update URL if needed)
git clone https://github.com/marvasgit/gke-finops-dashboard.git
cd gke-finops-dashboard

# Install using pip (or uv)
pip install -e .
# or
uv pip install -e .
```

---

## Set Up GCP Authentication

Ensure you have authenticated with Google Cloud and set up Application Default Credentials:

```bash
# Log in to Google Cloud
gcloud auth login

# Set up Application Default Credentials
gcloud auth application-default login

# Set your default project (optional, but recommended)
# gcloud config set project YOUR_PROJECT_ID
```

The tool will use these credentials to make API calls.

---

## Command Line Usage

Run the script using `gke-finops` followed by options:

```bash
gke-finops [options]
```

### Command Line Options

| Flag | Description | Required |
|---|---|---|
| `--projects`, `-p` | Specific GCP Project IDs to analyze (space-separated). | **Yes** |
| `--locations`, `-l` | Specific GCP locations (regions/zones) for GKE discovery (space-separated). If omitted, behavior depends on implementation (may default or require). | No |
| `--report-name`, `-n` | Specify the base name for the report file (without extension). | No |
| `--report-type`, `-y` | Specify one or more report types (space-separated): 'csv' and/or 'json'. Default: 'csv'. | No |
| `--dir`, `-d` | Directory to save the report file(s) (default: current directory). | No |
| `--time-range`, `-t` | Time range for cost data in days (default: current month). Examples: 7, 30, 90. | No |

---

## Examples

```bash
# Analyze projects 'my-dev-project' and 'my-prod-project', show output in terminal only
gke-finops --projects my-dev-project my-prod-project

# Analyze 'my-staging-project' and check GKE clusters only in 'us-central1' and 'europe-west1'
gke-finops --projects my-staging-project --locations us-central1 europe-west1

# Analyze 'my-dev-project' for the last 7 days
gke-finops --projects my-dev-project --time-range 7

# Analyze 'my-prod-project' and export data to CSV only
gke-finops --projects my-prod-project --report-name gcp_dashboard_data --report-type csv

# Analyze 'my-prod-project' and export data to JSON only in a specific directory
gke-finops --projects my-prod-project --report-name gcp_dashboard_data --report-type json --dir output_reports

# Analyze multiple projects and export to both CSV and JSON
gke-finops --projects proj-a proj-b proj-c --report-name multi_proj_report --report-type csv json
```

You'll see a live-updating table of your GCP project cost and GKE details in the terminal. If export options are specified, report file(s) will also be generated.

---

## Example Terminal Output

*(Placeholder - Screenshot/output needs to be updated for GCP/GKE)*

<!-- ![Dashboard Image](GKE-FinOps-Dashboard-CLI-Image.png) -->
```
(Example Rich table output showing GCP Project ID, Costs, Budgets, GKE Status)
```

---

## Export Formats

### CSV Output Format

When exporting to CSV, a file is generated with columns like:

- `GCP Project ID`
- `Cost for period (YYYY-MM-DD to YYYY-MM-DD)` (Previous Period)
- `Cost for period (YYYY-MM-DD to YYYY-MM-DD)` (Current Period)
- `Total Project Cost` (Current Period)
- `Budget Status` (Each budget's limit and actual spend appears on a new line within the cell)
- `GKE Cluster Status` (Each cluster state and its count appears on a new line within the cell)

**Note:** Due to potential multi-line formatting in some cells, it's best viewed in spreadsheet software.

### JSON Output Format

When exporting to JSON, a structured file is generated including all dashboard data (project ID, costs, budgets, GKE summary) per project.

---

## API Usage & Costs

This script makes API calls to Google Cloud, primarily to:
- Cloud Billing API (for costs and project billing info)
- Cloud Billing Budget API (for budgets)
- Kubernetes Engine API (for GKE cluster status)
- Potentially others (e.g., Compute API for locations, Resource Manager API)

Google Cloud APIs have free tiers and quotas. High usage might incur costs or hit rate limits. Refer to the pricing and quota documentation for each API used.

**To manage API usage:**
- Specify only the `--projects` you need.
- Use `--locations` to limit GKE discovery scope if you have many clusters across many locations.

---

## Contributing

Contributions are welcome! Feel free to fork and improve the project.

### Development Setup with pip

```bash
# Fork this repository on GitHub first (Update URL if needed)
# https://github.com/marvasgit/gke-finops-dashboard

# Then clone your fork locally
git clone https://github.com/your-username/gke-finops-dashboard.git
cd gke-finops-dashboard

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies (including dev)
pip install -e ".[dev]"

# Run the formatter (using hatch via pip)
# You might need to install hatch separately: pip install hatch
hatch run fmt

# Run linters
hatch run lint

# Run the tool
python -m gke_finops_dashboard.cli --help
# or directly if the script is installed in the venv path
gke-finops --help
```

### Development Setup with uv

`uv` provides a much faster development environment setup:

```bash
# Fork this repository on GitHub first (Update URL if needed)
# https://github.com/marvasgit/gke-finops-dashboard

# Then clone your fork locally
git clone https://github.com/your-username/gke-finops-dashboard.git
cd gke-finops-dashboard

# Install uv if you don't have it yet
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and sync the virtual environment (.venv) including dev dependencies
uv venv
uv pip install -e ".[dev]"

# Activate the virtual environment
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Run the formatter (using hatch via uv)
uv run hatch run fmt

# Run linters
uv run hatch run lint

# Run tests (if configured)
# uv run hatch run test

# Run the tool
gke-finops --help
```


---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.