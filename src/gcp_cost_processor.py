import csv
import json
import os
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any # Added Dict, Any

from collections import defaultdict

# GCP Client Libraries
from google.cloud import billing_v1
from google.cloud.billing import budgets_v1
from google.protobuf.json_format import MessageToDict # To help inspect budget object
from google.api_core import exceptions as google_exceptions
import google.auth
from decimal import Decimal # For handling money values from API

from rich.console import Console

# Updated import paths and type names
from gke_finops_dashboard.gcp_client import get_billing_account_for_project
from gke_finops_dashboard.types import GCPBudgetInfo, GCPCostData, GKESummary, ProjectData

# Import Money type
from google.type.money_pb2 import Money

console = Console()


# --- Functions below will be completely refactored for GCP ---

# Placeholder for GCP cost data fetching
def _money_to_float(money: Optional[Money]) -> float:
    """Converts Google's Money proto to float, handling None."""
    if money is None or money.units is None:
        return 0.0
    # Combine units and nanos into a Decimal for precision, then convert to float
    value = Decimal(money.units) + (Decimal(money.nanos or 0) / Decimal("1e9"))
    return float(value)

def get_gcp_cost_data(project_id: str, billing_account_name: str, time_range: Optional[int] = None) -> GCPCostData:
    """
    Get cost and budget data for a GCP project using Budgets API.

    Limitation: Without BigQuery, arbitrary time_range cost calculation is not
    feasible via Billing API. This function uses the 'last_period_amount' from the
    *first* budget found as a proxy for current period cost and sets previous
    period cost to 0. Budget data reflects the state reported by the Budgets API.
    """
    budgets_client = budgets_v1.BudgetServiceClient()
    budgets_data: List[GCPBudgetInfo] = []
    current_period_cost_proxy = 0.0
    previous_period_cost_proxy = 0.0 # Cannot reliably get this without BigQuery

    # Calculate date ranges for metadata, even if not used for cost fetching
    today = date.today()
    if time_range:
        end_date = today
        start_date = today - timedelta(days=time_range)
        previous_period_end = start_date - timedelta(days=1)
        previous_period_start = previous_period_end - timedelta(days=time_range)
        current_period_name = f"Current {time_range} days"
        previous_period_name = f"Previous {time_range} days"
    else:
        start_date = today.replace(day=1)
        end_date = today
        previous_period_end = start_date - timedelta(days=1)
        previous_period_start = previous_period_end.replace(day=1)
        current_period_name = "Current month"
        previous_period_name = "Last month"

    try:
        request = budgets_v1.ListBudgetsRequest(parent=billing_account_name)
        budgets_list = budgets_client.list_budgets(request=request)

        first_budget = True
        for budget in budgets_list:
            # Extract budget details
            budget_name = budget.display_name or budget.name.split('/')[-1] # Use display name or resource name part
            
            limit_amount = 0.0
            if budget.amount and budget.amount.specified_amount:
                 limit_amount = _money_to_float(budget.amount.specified_amount.amount)
            elif budget.amount and budget.amount.last_period_amount:
                 # If budget is based on last period's spend
                 limit_amount = _money_to_float(budget.amount.last_period_amount.amount)
                 budget_name += " (based on last period)"


            actual_spend = _money_to_float(budget.last_period_amount.amount if budget.last_period_amount else None)
            forecasted_spend = _money_to_float(budget.forecasted_spend.amount if budget.forecasted_spend else None)

            budgets_data.append({
                "name": budget_name,
                "limit": limit_amount,
                "actual": actual_spend,
                "forecast": forecasted_spend if forecasted_spend > 0 else None,
            })

            # Use first budget's actual spend as proxy for current period cost
            if first_budget:
                current_period_cost_proxy = actual_spend
                first_budget = False
                console.log(f"[yellow]Using actual spend from budget '{budget_name}' (${actual_spend:.2f}) as proxy for current period cost.[/]")

    except google_exceptions.PermissionDenied:
        console.log(f"[yellow]Permission denied to list budgets for {billing_account_name}. Check IAM roles (e.g., roles/billing.budgetsViewer).[/]")
    except google.auth.exceptions.DefaultCredentialsError:
         console.log(f"[bold red]GCP authentication failed. Run 'gcloud auth application-default login'.[/]")
         raise # Re-raise
    except Exception as e:
        console.log(f"[bold red]Error getting budget data for {billing_account_name}: {str(e)}[/]")

    if not budgets_data:
         console.log(f"[yellow]No budgets found for billing account {billing_account_name}. Cost data will be limited.[/]")

    # --- Cost Fetching (Approximation) ---
    # As noted, we use the budget's actual spend as a proxy.
    # No separate Billing API call for cost is made here due to limitations.
    console.log("[yellow]Warning: Cost data is approximated based on budget's actual spend. Enable BigQuery export for accurate time-range costs.[/]")


    return {
        "project_id": project_id,
        "current_period_cost": current_period_cost_proxy,
        "previous_period_cost": previous_period_cost_proxy, # Set to 0
        "cost_by_service": [], # Cannot get service breakdown from Budgets API
        "budgets": budgets_data,
        "current_period_name": current_period_name,
        "previous_period_name": previous_period_name,
        "time_range": time_range,
        "current_period_start": start_date.isoformat(),
        "current_period_end": end_date.isoformat(),
        "previous_period_start": previous_period_start.isoformat(),
        "previous_period_end": previous_period_end.isoformat(),
    }


def process_gcp_costs(
    cost_data: GCPCostData,
) -> Tuple[List[str], List[Tuple[str, float]]]:
    """Process and format GCP costs (currently total project cost proxy)."""
    total_cost = cost_data["current_period_cost"]
    # Since we only have total cost proxy, the breakdown is simple
    if total_cost > 0.001:
        formatted_costs = [f"Total Project Cost (Proxy): ${total_cost:.2f}"]
        cost_data_tuples = [("Total Project Cost (Proxy)", total_cost)]
    else:
        formatted_costs = ["No significant cost detected (based on budget proxy)."]
        cost_data_tuples = []
    return formatted_costs, cost_data_tuples


def format_gcp_budget_info(budgets: List[GCPBudgetInfo]) -> List[str]:
    """Format GCP budget information for display."""
    budget_info_lines: List[str] = []
    if not budgets:
        return ["No budgets found or accessible."]
    for budget in budgets:
        limit_str = f"${budget['limit']:.2f}" if budget['limit'] > 0 else "N/A (e.g., based on last period)"
        budget_info_lines.append(f"[bold]{budget['name']}[/]")
        budget_info_lines.append(f"  Limit: {limit_str}")
        budget_info_lines.append(f"  Actual: ${budget['actual']:.2f}")
        if budget.get('forecast') is not None:
             budget_info_lines.append(f"  Forecast: ${budget['forecast']:.2f}")
        budget_info_lines.append("") # Add spacing between budgets
    # Remove trailing empty line if budgets were processed
    if budget_info_lines:
        budget_info_lines.pop()
    return budget_info_lines


def format_gke_summary(gke_data: GKESummary) -> List[str]:
    """Format GKE cluster summary for display."""
    gke_summary_lines: List[str] = []
    # Define colors for GKE states
    status_colors = {
        "RUNNING": "bright_green",
        "PROVISIONING": "bright_cyan",
        "RECONCILING": "cyan",
        "STOPPING": "bright_yellow",
        "DEGRADED": "yellow",
        "ERROR": "bright_red",
        "STATUS_UNSPECIFIED": "dim",
        "PERMISSION_DENIED": "red", # Custom status added in gcp_client
    }

    for state, count in sorted(gke_data.items()):
        if count > 0:
            state_color = status_colors.get(state, "white") # Default to white if unknown
            gke_summary_lines.append(f"[{state_color}]{state}: {count}[/]")

    if not gke_summary_lines:
        # Check if there was an error state captured
        if gke_data.get("ERROR", 0) > 0:
             gke_summary_lines = ["[red]Error fetching GKE data[/]"]
        elif gke_data.get("PERMISSION_DENIED", 0) > 0:
             gke_summary_lines = ["[red]Permission Denied for GKE[/]"]
        else:
             gke_summary_lines = ["No GKE clusters found or accessible."]

    return gke_summary_lines


# Placeholder for CSV export (needs updated headers/data)
def export_to_csv(
    data: List[ProjectData],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
) -> Optional[str]:
    """Placeholder: Export dashboard data to a CSV file."""
    console.print("[bold yellow]Placeholder: export_to_csv not implemented[/]")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.csv"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename

        previous_period_header = f"Cost for period\n({previous_period_dates})"
        current_period_header = f"Cost for period\n({current_period_dates})"

        with open(output_filename, "w", newline="") as csvfile:
            # TODO: Update fieldnames for GCP/GKE
            fieldnames = [
                "GCP Project ID", # Updated
                previous_period_header,
                current_period_header,
                "Total Project Cost", # Updated
                "Budget Status",
                "GKE Cluster Status", # Updated
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # TODO: Update data mapping for GCP/GKE
                budgets_data = "\n".join(row["budget_info"]) if row["budget_info"] else "No budgets"
                gke_data_summary = "\n".join(
                    [f"{state}: {count}" for state, count in row["gke_summary"].items() if count > 0]
                )

                writer.writerow(
                    {
                        "GCP Project ID": row["project_id"],
                        previous_period_header: f"${row['previous_period_cost']:.2f}",
                        current_period_header: f"${row['current_period_cost']:.2f}",
                        "Total Project Cost": f"${row['current_period_cost']:.2f}", # Simplified
                        "Budget Status": budgets_data or "No budgets",
                        "GKE Cluster Status": gke_data_summary or "No clusters",
                    }
                )
        console.print(
            f"[bright_green]Exported dashboard data to {os.path.abspath(output_filename)}[/]"
        )
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to CSV: {str(e)}[/]")
        return None


# Placeholder for JSON export (needs updated data structure)
def export_to_json(
    data: List[ProjectData], filename: str, output_dir: Optional[str] = None
) -> Optional[str]:
    """Placeholder: Export dashboard data to a JSON file."""
    console.print("[bold yellow]Placeholder: export_to_json not implemented[/]")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.json"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename

        # TODO: Ensure 'data' structure matches GCP/GKE fields
        with open(output_filename, "w") as jsonfile:
            json.dump(data, jsonfile, indent=4)

        console.print(
            f"[bright_green]Exported dashboard data to {os.path.abspath(output_filename)}[/]"
        )
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to JSON: {str(e)}[/]")
        return None