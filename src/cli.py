import argparse
import sys
from rich.console import Console

console = Console()

# TODO: Update banner for GKE/GCP
def welcome_banner() -> None:
    banner = """
[bold red]
    ______   __    __  ________        ________  __             ______                      
 /      \ /  |  /  |/        |      /        |/  |           /      \                     
/$$$$$$  |$$ | /$$/ $$$$$$$$/       $$$$$$$$/ $$/  _______  /$$$$$$  |  ______    _______ 
$$ | _$$/ $$ |/$$/  $$ |__          $$ |__    /  |/       \ $$ |  $$ | /      \  /       |
$$ |/    |$$  $$<   $$    |         $$    |   $$ |$$$$$$$  |$$ |  $$ |/$$$$$$  |/$$$$$$$/ 
$$ |$$$$ |$$$$$  \  $$$$$/          $$$$$/    $$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |$$      \ 
$$ \__$$ |$$ |$$  \ $$ |_____       $$ |      $$ |$$ |  $$ |$$ \__$$ |$$ |__$$ | $$$$$$  |
$$    $$/ $$ | $$  |$$       |      $$ |      $$ |$$ |  $$ |$$    $$/ $$    $$/ /     $$/ 
 $$$$$$/  $$/   $$/ $$$$$$$$/       $$/       $$/ $$/   $$/  $$$$$$/  $$$$$$$/  $$$$$$$/  
                                                                      $$ |                
                                                                      $$ |                
                                                                      $$/                 
[/]
[bold bright_blue]GKE FinOps Dashboard CLI (v0.1.0)[/] # Updated Name/Version
"""
    console.print(banner)


# TODO: Update arguments for GCP (--projects, --locations)
def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the GKE FinOps Dashboard."""
    parser = argparse.ArgumentParser(description="GKE FinOps Dashboard CLI") # Updated description

    parser.add_argument(
        "--projects", # Renamed from --profiles
        "-p",
        nargs="+",
        help="Specific GCP Project IDs to use (space-separated)", # Updated help
        type=str,
        required=True, # Made projects required for now
    )
    parser.add_argument(
        "--locations", # Renamed from --regions
        "-l", # Changed short flag
        nargs="+",
        help="GCP locations (regions/zones) to check for GKE clusters (space-separated)", # Updated help
        type=str,
    )
    # Removed --all argument
    # Removed --combine argument
    parser.add_argument(
        "--report-name",
        "-n",
        help="Specify the base name for the report file (without extension)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--report-type",
        "-y",
        nargs="+",
        choices=["csv", "json"],
        help="Specify one or more report types: csv and/or json (space-separated)",
        type=str,
        default=["csv"],
    )
    parser.add_argument(
        "--dir",
        "-d",
        help="Directory to save the report files (default: current directory)",
        type=str,
    )
    parser.add_argument(
        "--time-range",
        "-t",
        help="Time range for cost data in days (default: current month). Examples: 7, 30, 90",
        type=int,
    )

    return parser.parse_args()


def main() -> int:
    """Command-line interface entry point."""
    welcome_banner()
    # Updated import path
    from gke_finops_dashboard.main import run_dashboard

    args = parse_args()
    result = run_dashboard(args)
    return 0 if result == 0 else 1


if __name__ == "__main__":
    sys.exit(main())