"""
RedTrack Data Pipeline
Pulls campaign performance data from RedTrack API and saves it locally
for the /score bot's Monte Carlo simulation.

Usage:
    python pull_redtrack.py                  # Pull last 30 days
    python pull_redtrack.py --days 7         # Pull last 7 days
    python pull_redtrack.py --from 2026-01-01 --to 2026-02-15  # Custom range
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "redtrack_performance.json")
BASE_URL = "https://api.redtrack.io"


def load_api_key():
    """Load API key from .env file."""
    if not os.path.exists(ENV_FILE):
        print("ERROR: .env file not found at", ENV_FILE)
        print("Create it with: REDTRACK_API_KEY=your_key_here")
        sys.exit(1)

    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("REDTRACK_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key == "your_api_key_here" or not key:
                    print("ERROR: Replace 'your_api_key_here' in .env with your actual RedTrack API key.")
                    print("File:", ENV_FILE)
                    sys.exit(1)
                return key

    print("ERROR: REDTRACK_API_KEY not found in .env file.")
    sys.exit(1)


def parse_args():
    """Parse command line arguments for date range."""
    date_from = None
    date_to = None
    days = 30

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--from" and i + 1 < len(args):
            date_from = args[i + 1]
            i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            date_to = args[i + 1]
            i += 2
        else:
            i += 1

    if not date_from:
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")

    return date_from, date_to


def pull_campaigns(api_key, date_from, date_to):
    """Pull campaign data with statistics from RedTrack."""
    print(f"Pulling campaigns from {date_from} to {date_to}...")

    params = {
        "api_key": api_key,
        "date_from": date_from,
        "date_to": date_to,
        "total_stat": "true",
        "per": 100,
        "page": 1
    }

    response = requests.get(f"{BASE_URL}/campaigns", params=params)

    if response.status_code != 200:
        print(f"ERROR: API returned status {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()
    return data


def pull_conversions(api_key, date_from, date_to):
    """Pull conversion data from RedTrack."""
    print(f"Pulling conversions from {date_from} to {date_to}...")

    params = {
        "api_key": api_key,
        "date_from": date_from,
        "date_to": date_to,
        "per": 100,
        "page": 1
    }

    response = requests.get(f"{BASE_URL}/conversions", params=params)

    if response.status_code != 200:
        print(f"ERROR: Conversions API returned status {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    return data


def build_output(campaigns_data, conversions_data, date_from, date_to):
    """Structure the data for the scoring bot."""
    output = {
        "metadata": {
            "source": "RedTrack API",
            "pulled_at": datetime.now().isoformat(),
            "date_range": {
                "from": date_from,
                "to": date_to
            }
        },
        "campaigns": [],
        "summary": {
            "total_campaigns": 0,
            "total_clicks": 0,
            "total_conversions": 0,
            "total_cost": 0,
            "total_revenue": 0,
            "avg_ctr": 0,
            "avg_cpc": 0,
            "avg_cpm": 0,
            "avg_conversion_rate": 0,
            "avg_roas": 0
        }
    }

    # Handle different response formats
    items = []
    if isinstance(campaigns_data, list):
        items = campaigns_data
    elif isinstance(campaigns_data, dict):
        items = campaigns_data.get("items", [])

    total_clicks = 0
    total_impressions = 0
    total_conversions = 0
    total_cost = 0
    total_revenue = 0

    for campaign in items:
        # Extract whatever stats RedTrack provides
        # Field names may vary - we capture everything available
        camp_data = {
            "id": campaign.get("id", ""),
            "name": campaign.get("title", campaign.get("name", "Unknown")),
            "status": campaign.get("status", ""),
            "stats": {}
        }

        # RedTrack may nest stats in different ways
        # Try common field patterns
        stat_fields = [
            "clicks", "impressions", "conversions", "cost", "revenue",
            "ctr", "cpc", "cpm", "cr", "roi", "epc", "cpa",
            "lp_clicks", "lp_ctr", "unique_clicks",
            "total_conversions", "approved_conversions",
            "total_revenue", "approved_revenue"
        ]

        for field in stat_fields:
            if field in campaign:
                camp_data["stats"][field] = campaign[field]

        # Also grab any nested stat object
        if "stat" in campaign and isinstance(campaign["stat"], dict):
            camp_data["stats"].update(campaign["stat"])
        if "statistics" in campaign and isinstance(campaign["statistics"], dict):
            camp_data["stats"].update(campaign["statistics"])

        # Accumulate totals
        clicks = camp_data["stats"].get("clicks", 0) or 0
        imps = camp_data["stats"].get("impressions", 0) or 0
        convs = camp_data["stats"].get("conversions", camp_data["stats"].get("total_conversions", 0)) or 0
        cost = camp_data["stats"].get("cost", 0) or 0
        rev = camp_data["stats"].get("revenue", camp_data["stats"].get("total_revenue", 0)) or 0

        total_clicks += clicks
        total_impressions += imps
        total_conversions += convs
        total_cost += float(cost)
        total_revenue += float(rev)

        output["campaigns"].append(camp_data)

    # Calculate summary averages
    output["summary"]["total_campaigns"] = len(items)
    output["summary"]["total_clicks"] = total_clicks
    output["summary"]["total_conversions"] = total_conversions
    output["summary"]["total_cost"] = round(total_cost, 2)
    output["summary"]["total_revenue"] = round(total_revenue, 2)

    if total_impressions > 0:
        output["summary"]["avg_ctr"] = round((total_clicks / total_impressions) * 100, 2)
        output["summary"]["avg_cpm"] = round((total_cost / total_impressions) * 1000, 2)

    if total_clicks > 0:
        output["summary"]["avg_cpc"] = round(total_cost / total_clicks, 2)
        output["summary"]["avg_conversion_rate"] = round((total_conversions / total_clicks) * 100, 2)

    if total_cost > 0:
        output["summary"]["avg_roas"] = round(total_revenue / total_cost, 2)

    # Add conversion details if available
    if conversions_data:
        conv_items = []
        if isinstance(conversions_data, dict):
            conv_items = conversions_data.get("items", [])
        output["conversions_count"] = len(conv_items)

    return output


def save_output(output):
    """Save structured data to JSON file."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nData saved to: {OUTPUT_FILE}")
    print(f"  Campaigns: {output['summary']['total_campaigns']}")
    print(f"  Clicks: {output['summary']['total_clicks']}")
    print(f"  Conversions: {output['summary']['total_conversions']}")
    print(f"  Cost: ${output['summary']['total_cost']}")
    print(f"  Revenue: ${output['summary']['total_revenue']}")
    if output["summary"]["avg_ctr"]:
        print(f"  Avg CTR: {output['summary']['avg_ctr']}%")
    if output["summary"]["avg_cpc"]:
        print(f"  Avg CPC: ${output['summary']['avg_cpc']}")
    if output["summary"]["avg_conversion_rate"]:
        print(f"  Avg Conv Rate: {output['summary']['avg_conversion_rate']}%")
    if output["summary"]["avg_roas"]:
        print(f"  Avg ROAS: {output['summary']['avg_roas']}x")


def main():
    print("=" * 50)
    print("RedTrack Data Pipeline")
    print("=" * 50)

    api_key = load_api_key()
    date_from, date_to = parse_args()

    campaigns_data = pull_campaigns(api_key, date_from, date_to)
    conversions_data = pull_conversions(api_key, date_from, date_to)

    output = build_output(campaigns_data, conversions_data, date_from, date_to)
    save_output(output)

    print("\nDone. The /score bot will use this data for Monte Carlo calibration.")


if __name__ == "__main__":
    main()
