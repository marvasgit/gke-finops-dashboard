import argparse
import sys
from collections import defaultdict
from typing import Dict, List, Optional
import google.auth
from rich import box
from rich.console import Console
from rich.table import Column, Table
from rich.progress import Progress, track
from rich.status import Status

# Updated import paths and names
from gke_finops_dashboard.gcp_client import (
    get_gke_summary, # Renamed from ec2_summary
    get_billing_account_for_project, # New function
)
from gke_finops_dashboard.gcp_cost_processor import ( # Updated module name
    export_to_csv,
    export_to_json,
    format_gcp_budget_info, # Renamed from format_budget_info
    format_gke_summary, # Renamed from format_ec2_summary
    get_gcp_cost_data, # Renamed from get_cost_data
    process_gcp_costs, # Renamed from process_service_costs
)
# Updated import path and type names (will define/refactor these later)
from gke_finops_dashboard.types import GCPBudgetInfo, ProjectData, GCPCostData

console = Console()


# --- Functions below will be completely refactored for GCP ---

# Placeholder for processing a single GCP project
def process_single_project(
    project_id: str,
    user_locations: Optional[List[str]] = None,
    time_range: Optional[int] = None,
) -> ProjectData:
    """Process a single GCP project and return its data."""
    # console.print(f"[bold yellow]Placeholder: process_single_project({project_id}, {user_locations}, {time_range}) not implemented[/]") # Removed placeholder
    try:
        # Get billing account
        billing_account_name = get_billing_account_for_project(project_id)
        if not billing_account_name:
             # Handle case where billing account couldn't be determined (e.g., no permissions, billing disabled)
             # We can still try to get GKE data, but cost/budget will be unavailable.
             console.log(f"[yellow]Could not determine billing account for {project_id}. Cost and budget data will be unavailable.[/]")
             cost_data: GCPCostData = { # Create dummy cost data
                 "project_id": project_id, "current_period_cost": 0.0, "previous_period_cost": 0.0,
                 "cost_by_service": [], "budgets": [], "current_period_name": "Current Period",
                 "previous_period_name": "Previous Period", "time_range": time_range,
                 "current_period_start": "N/A", "current_period_end": "N/A",
                 "previous_period_start": "N/A", "previous_period_end": "N/A",
             }
        else:
            # Get cost and budget data (uses budget proxy for cost)
            cost_data = get_gcp_cost_data(project_id, billing_account_name, time_range)

        # Get GKE data - pass user_locations (which can be None to check all)
        gke_data = get_gke_summary(project_id, user_locations)

        # Process costs (currently just total cost proxy)
        service_costs_formatted, service_cost_data = process_gcp_costs(cost_data)

        # Format budgets
        budget_info_formatted = format_gcp_budget_info(cost_data["budgets"])

        # Format GKE summary
        gke_summary_formatted = format_gke_summary(gke_data)

        return {
            "project_id": project_id,
            "previous_period_cost": cost_data["previous_period_cost"],
            "current_period_cost": cost_data["current_period_cost"],
            "service_costs": service_cost_data,
            "service_costs_formatted": service_costs_formatted,
            "budget_info": budget_info_formatted, # This now holds the formatted strings
            "gke_summary": gke_data, # Raw summary data
            "gke_summary_formatted": gke_summary_formatted, # Formatted strings
            "success": True,
            "error": None,
            "current_period_name": cost_data.get("current_period_name", "Current Period"),
            "previous_period_name": cost_data.get("previous_period_name", "Previous Period"),
            # Include dates for potential use in table headers/exports
            "current_period_start": cost_data.get("current_period_start", "N/A"),
            "current_period_end": cost_data.get("current_period_end", "N/A"),
            "previous_period_start": cost_data.get("previous_period_start", "N/A"),
            "previous_period_end": cost_data.get("previous_period_end", "N/A"),
        }

    except google.auth.exceptions.DefaultCredentialsError:
         # Catch auth errors specifically
         error_msg = "GCP authentication failed. Run 'gcloud auth application-default login'."
         console.print(f"[bold red]Authentication Error processing project {project_id}.[/]")
         # Return structure indicating failure
         return {
            "project_id": project_id, "previous_period_cost": 0, "current_period_cost": 0,
            "service_costs": [], "service_costs_formatted": [error_msg],
            "budget_info": ["Auth Error"], "gke_summary": {}, "gke_summary_formatted": ["Auth Error"],
            "success": False, "error": error_msg,
            "current_period_name": "Current Period", "previous_period_name": "Previous Period",
            "current_period_start": "N/A", "current_period_end": "N/A",
            "previous_period_start": "N/A", "previous_period_end": "N/A",
         }
    except Exception as e:
        # Catch all other errors during processing
        error_msg = f"Failed to process project: {str(e)}"
        console.print(f"[bold red]Error processing project {project_id}: {error_msg}[/]")
        # Return structure indicating failure
        return {
            "project_id": project_id, "previous_period_cost": 0, "current_period_cost": 0,
            "service_costs": [], "service_costs_formatted": [error_msg],
            "budget_info": ["Error"], "gke_summary": {}, "gke_summary_formatted": ["Error"],
            "success": False, "error": str(e),
            "current_period_name": "Current Period", "previous_period_name": "Previous Period",
            "current_period_start": "N/A", "current_period_end": "N/A",
            "previous_period_start": "N/A", "previous_period_end": "N/A",
        }


# Removed process_combined_profiles as --combine flag is removed


# Placeholder: Create display table for GCP/GKE
def create_display_table(
    previous_period_dates: str,
    current_period_dates: str,
    previous_period_name: str = "Previous Period Cost",
    current_period_name: str = "Current Period Cost",
) -> Table:
    """Create and configure the display table for GCP/GKE data."""
    # console.print("[bold yellow]Placeholder: create_display_table needs GCP/GKE columns[/]") # Removed placeholder
    table = Table(
        "GCP Project ID",
        Column(f"{previous_period_name} Cost\n({previous_period_dates})", justify="right"), # Right align costs
        Column(f"{current_period_name} Cost\n({current_period_dates})", justify="right"), # Right align costs
        Column("Total Cost (Proxy)"), # Display the proxy cost
        Column("Budget Status"),
        Column("GKE Cluster Summary", justify="left"), # Left align summary text
        title="GKE FinOps Dashboard",
        caption="GKE FinOps Dashboard CLI - Costs are approximated based on budget data.", # Added caption note
        box=box.ASCII_DOUBLE_HEAD,
        show_lines=True,
        style="bright_cyan",
        padding=(0, 1), # Add padding
    )
    # Set specific column widths if needed (optional)
    # table.columns[0].width = 25 # Project ID
    # table.columns[3].width = 40 # Budget Status
    # table.columns[4].width = 25 # GKE Summary
    return table


# Placeholder: Add project data to table
def add_project_to_table(table: Table, project_data: ProjectData) -> None:
    """Add project data to the display table."""
    # console.print("[bold yellow]Placeholder: add_project_to_table needs GCP/GKE data mapping[/]") # Removed placeholder
    if project_data["success"]:
        # Join the formatted lists with newlines for multi-line cell content
        cost_str = "\n".join(project_data["service_costs_formatted"])
        budget_str = "\n".join(project_data["budget_info"])
        gke_str = "\n".join(project_data["gke_summary_formatted"])

        table.add_row(
            f"[bright_magenta]{project_data['project_id']}[/]",
            f"[bright_red]${project_data['previous_period_cost']:.2f}[/]", # Note: Likely $0.00
            f"[bright_green]${project_data['current_period_cost']:.2f}[/]",
            cost_str, # Display the formatted total cost proxy string
            budget_str,
            gke_str,
        )
    else:
        # Display error row
        error_msg = project_data.get('error', 'Unknown Error')
        table.add_row(
            f"[bright_magenta]{project_data['project_id']}[/]",
            "[red]Error[/]",
            "[red]Error[/]",
            f"[red]{error_msg}[/]",
            "[red]Error[/]",
            "[red]Error[/]",
        )


# Placeholder: Main dashboard logic for GCP
def run_dashboard(args: argparse.Namespace) -> int:
    """Main function to run the GKE FinOps dashboard."""
    # console.print("[bold yellow]Placeholder: run_dashboard needs GCP logic[/]") # Removed placeholder
    export_data: List[ProjectData] = []
    first_project_data: Optional[ProjectData] = None # To store data from first successful project for headers

    # Validate projects argument
    projects_to_use = args.projects
    if not projects_to_use:
         console.print("[bold red]No GCP projects specified. Use the --projects argument.[/]")
         return 1

    user_locations = args.locations
    time_range = args.time_range

    # Process projects
    console.print(f"[cyan]Processing {len(projects_to_use)} GCP project(s)...[/]")
    auth_error_encountered = False
    for project_id in track(projects_to_use, description="[bright_cyan]Fetching GCP data..."):
        try:
            project_data = process_single_project(project_id, user_locations, time_range)
            export_data.append(project_data)
            if project_data["success"] and first_project_data is None:
                first_project_data = project_data # Store first success for headers
        except google.auth.exceptions.DefaultCredentialsError:
             # Handle auth error raised from process_single_project
             auth_error_encountered = True
             # Create error entry for export
             error_msg = "GCP authentication failed. Run 'gcloud auth application-default login'."
             export_data.append({
                 "project_id": project_id, "previous_period_cost": 0, "current_period_cost": 0,
                 "service_costs": [], "service_costs_formatted": [error_msg],
                 "budget_info": ["Auth Error"], "gke_summary": {}, "gke_summary_formatted": ["Auth Error"],
                 "success": False, "error": error_msg,
                 "current_period_name": "Current Period", "previous_period_name": "Previous Period",
                 "current_period_start": "N/A", "current_period_end": "N/A",
                 "previous_period_start": "N/A", "previous_period_end": "N/A",
             })
             # Stop processing further projects on auth error
             console.print("[bold red]Authentication failed. Aborting further processing.[/]")
             break
        except Exception as e:
             # Handle unexpected errors during the loop itself (less likely)
             console.print(f"[bold red]Unexpected error processing project {project_id}: {e}[/]")
             error_msg = f"Unexpected error: {str(e)}"
             export_data.append({
                 "project_id": project_id, "previous_period_cost": 0, "current_period_cost": 0,
                 "service_costs": [], "service_costs_formatted": [error_msg],
                 "budget_info": ["Error"], "gke_summary": {}, "gke_summary_formatted": ["Error"],
                 "success": False, "error": error_msg,
                 "current_period_name": "Current Period", "previous_period_name": "Previous Period",
                 "current_period_start": "N/A", "current_period_end": "N/A",
                 "previous_period_start": "N/A", "previous_period_end": "N/A",
             })

    # Determine headers from first successful project or use defaults
    if first_project_data:
        previous_period_name = first_project_data.get("previous_period_name", "Previous Period")
        current_period_name = first_project_data.get("current_period_name", "Current Period")
        previous_period_dates = f"{first_project_data.get('previous_period_start', 'N/A')} to {first_project_data.get('previous_period_end', 'N/A')}"
        current_period_dates = f"{first_project_data.get('current_period_start', 'N/A')} to {first_project_data.get('current_period_end', 'N/A')}"
    else:
        # Use defaults if no project succeeded or auth failed immediately
        previous_period_name = "Previous Period"
        current_period_name = "Current Period"
        previous_period_dates = "N/A"
        current_period_dates = "N/A"

    # Create and populate the table
    table = create_display_table(previous_period_dates, current_period_dates, previous_period_name, current_period_name)
    for data in export_data:
        add_project_to_table(table, data)

    console.print(table)

    # Export if requested
    if args.report_name and args.report_type:
        console.print("[cyan]Exporting data...[/]")
        # Pass the actual dates used in the table headers to the export functions
        export_kwargs = {
            "previous_period_dates": previous_period_dates,
            "current_period_dates": current_period_dates,
        }
        for report_type in args.report_type:
            if report_type == "csv":
                csv_path = export_to_csv(export_data, args.report_name, args.dir, **export_kwargs)
                # Output handled within export_to_csv
            elif report_type == "json":
                json_path = export_to_json(export_data, args.report_name, args.dir)
                # Output handled within export_to_json

    # Return non-zero exit code if auth failed
    return 1 if auth_error_encountered else 0


# Keep main entry point structure, update import
def main() -> int:
    """Entry point for the module when run directly."""
    # Updated import path
    from gke_finops_dashboard.cli import parse_args

    args = parse_args()
    return run_dashboard(args)


if __name__ == "__main__":
    sys.exit(main())