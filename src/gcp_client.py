from collections import defaultdict
from typing import List, Optional

# GCP Client Libraries
from google.cloud import billing_v1
from google.cloud import container_v1
from google.api_core import exceptions as google_exceptions
import google.auth

# from boto3.session import Session # Will be replaced
from rich.console import Console

# Updated import path and type names
from gke_finops_dashboard.types import GKESummary, LocationName

console = Console()


# --- Functions below will be completely refactored for GCP ---

# Placeholder for GCP project/credential handling
def get_gcp_projects() -> List[str]:
    """Placeholder: Get configured GCP projects."""
    console.print("[bold yellow]Placeholder: get_gcp_projects not implemented[/]")
    return ["your-gcp-project-id"]


# Placeholder for getting billing account associated with a project
def get_billing_account_for_project(project_id: str) -> Optional[str]:
    """Get the billing account name associated with a GCP project."""
    try:
        billing_client = billing_v1.CloudBillingClient()
        project_name = f"projects/{project_id}"
        project_billing_info = billing_client.get_project_billing_info(name=project_name)

        if project_billing_info.billing_enabled:
            return project_billing_info.billing_account_name
        else:
            console.log(f"[yellow]Billing is not enabled for project {project_id}[/]")
            return None
    except google_exceptions.NotFound:
        console.log(f"[yellow]Project {project_id} not found or access denied.[/]")
        return None
    except google_exceptions.PermissionDenied:
        console.log(f"[yellow]Permission denied to get billing info for project {project_id}. Check IAM roles (e.g., roles/billing.viewer).[/]")
        return None
    except google.auth.exceptions.DefaultCredentialsError:
         # This exception might be caught higher up, but good to be specific
         console.log(f"[bold red]GCP authentication failed. Run 'gcloud auth application-default login'.[/]")
         raise # Re-raise to be handled by the main loop
    except Exception as e:
        console.log(f"[bold red]Error getting billing account for project {project_id}: {str(e)}[/]")
        return None


# Placeholder for getting GCP locations
def get_all_locations() -> List[LocationName]:
    """Placeholder: Get all available GCP locations (regions/zones)."""
    console.print("[bold yellow]Placeholder: get_all_locations not implemented[/]")
    # Example: return ['us-central1', 'europe-west1', 'us-central1-a']
    return ["us-central1", "europe-west1"]


# Placeholder for getting accessible locations
def get_accessible_locations(project_id: str) -> List[LocationName]:
    """Placeholder: Get locations accessible with current credentials for a project."""
    console.print(
        f"[bold yellow]Placeholder: get_accessible_locations({project_id}) not implemented[/]"
    )
    return ["us-central1", "europe-west1"]


def get_gke_summary(
    project_id: str, locations: Optional[List[LocationName]] = None
) -> GKESummary:
    """Get GKE cluster summary across specified locations or all locations."""
    cluster_summary: GKESummary = defaultdict(int)
    try:
        container_client = container_v1.ClusterManagerClient()
        
        locations_to_check = locations if locations else ["-"] # Use "-" to check all locations if none specified

        for loc in locations_to_check:
            parent = f"projects/{project_id}/locations/{loc}"
            try:
                response = container_client.list_clusters(parent=parent)
                for cluster in response.clusters:
                    # Status is an enum, get its name
                    status_name = container_v1.Cluster.Status(cluster.status).name
                    cluster_summary[status_name] += 1
            except google_exceptions.NotFound:
                 # This might happen if a specific location is invalid or has no GKE resources/permissions
                 console.log(f"[yellow]No GKE clusters found or access denied in location '{loc}' for project {project_id}.[/]")
                 continue # Continue to the next location
            except google_exceptions.PermissionDenied:
                 console.log(f"[yellow]Permission denied for GKE in location '{loc}' for project {project_id}. Check IAM roles (e.g., roles/container.viewer).[/]")
                 # If checking all locations ("-"), permission denied might stop the whole process.
                 # If checking specific locations, we can continue.
                 if loc == "-":
                     cluster_summary["PERMISSION_DENIED"] += 1 # Mark as permission denied
                     break # Stop checking other locations if wildcard fails on permissions
                 else:
                     continue
            except Exception as loc_e:
                 # Catch other potential errors per location
                 console.log(f"[bold red]Error listing GKE clusters in location '{loc}' for project {project_id}: {str(loc_e)}[/]")
                 cluster_summary["ERROR"] += 1 # Generic error count

        if not cluster_summary and locations_to_check != ["-"]:
             # If specific locations were given but none yielded results or errors
             console.log(f"[yellow]No GKE clusters found in specified locations for project {project_id}.[/]")

    except google.auth.exceptions.DefaultCredentialsError:
         console.log(f"[bold red]GCP authentication failed. Run 'gcloud auth application-default login'.[/]")
         raise # Re-raise to be handled by the main loop
    except Exception as e:
        console.log(f"[bold red]Error initializing GKE client or processing locations for project {project_id}: {str(e)}[/]")
        cluster_summary["ERROR"] += 1 # Add to generic error count

    # Ensure common statuses exist, even if zero, for consistent reporting
    if "RUNNING" not in cluster_summary: cluster_summary["RUNNING"] = 0
    if "STOPPED" not in cluster_summary: cluster_summary["STOPPED"] = 0 # Note: GKE uses STOPPING state during deletion

    return cluster_summary