"""Type definitions for GKE FinOps Dashboard."""

from typing import Dict, List, Optional, Tuple, TypedDict, Any # Added Any


# Renamed from BudgetInfo
class GCPBudgetInfo(TypedDict):
    """Type for a GCP budget entry."""
    name: str
    limit: float
    actual: float # Note: Actual spend might need separate calculation depending on API
    forecast: Optional[float]
    # Add other relevant GCP budget fields if needed


# Renamed from CostData
class GCPCostData(TypedDict):
    """Type for cost data returned from GCP Billing API."""
    project_id: str # Changed from account_id
    current_period_cost: float # Renamed from current_month
    previous_period_cost: float # Renamed from last_month
    cost_by_service: List[Dict[str, Any]] # Renamed, structure might change (or be empty if only total cost)
    budgets: List[GCPBudgetInfo] # Use renamed type
    current_period_name: str
    previous_period_name: str
    time_range: Optional[int]
    current_period_start: str
    current_period_end: str
    previous_period_start: str
    previous_period_end: str


# Renamed from ProfileData
class ProjectData(TypedDict):
    """Type for processed project data."""
    project_id: str # Changed from profile
    # account_id: str # Removed, project_id is the primary identifier
    previous_period_cost: float # Renamed from last_month
    current_period_cost: float # Renamed from current_month
    service_costs: List[Tuple[str, float]] # Structure might change (e.g., just total cost)
    service_costs_formatted: List[str] # Structure might change
    budget_info: List[str] # Formatted budget strings
    gke_summary: Dict[str, int] # Renamed from ec2_summary
    gke_summary_formatted: List[str] # Renamed from ec2_summary_formatted
    success: bool
    error: Optional[str]
    current_period_name: str
    previous_period_name: str


# Updated CLIArgs
class CLIArgs(TypedDict, total=False):
    """Type for CLI arguments."""
    projects: Optional[List[str]] # Renamed from profiles
    locations: Optional[List[str]] # Renamed from regions
    # all: bool # Removed
    # combine: bool # Removed
    report_name: Optional[str]
    report_type: Optional[List[str]]
    dir: Optional[str]
    time_range: Optional[int]


# Renamed type aliases
LocationName = str
GKESummary = Dict[str, int] # Renamed from EC2Summary