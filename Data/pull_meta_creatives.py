"""
Meta Marketing API — Creative Puller
Pulls ad creatives (copy, headlines, CTAs) from all ad accounts
across multiple Business Managers.

Usage:
    python pull_meta_creatives.py                    # Pull all active ads
    python pull_meta_creatives.py --status PAUSED    # Pull paused ads
    python pull_meta_creatives.py --status ALL       # Pull all statuses
    python pull_meta_creatives.py --days 30          # Ads updated in last 30 days
    python pull_meta_creatives.py --bm 1             # Only pull from BM 1
    python pull_meta_creatives.py --accounts 10      # Only scan first 10 accounts per BM
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
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "meta_creatives.json")
BASE_URL = "https://graph.facebook.com/v21.0"


def load_env():
    """Load all credentials from .env file."""
    if not os.path.exists(ENV_FILE):
        print("ERROR: .env file not found at", ENV_FILE)
        sys.exit(1)

    env = {}
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()

    return env


def get_business_managers(env):
    """Parse BM configs from env vars."""
    bms = []
    i = 1
    while True:
        bm_id = env.get(f"META_BM_{i}_ID")
        bm_token = env.get(f"META_BM_{i}_TOKEN")
        bm_name = env.get(f"META_BM_{i}_NAME", f"BM {i}")

        if not bm_id or not bm_token:
            break

        if bm_id.startswith("your_") or bm_token.startswith("your_"):
            print(f"WARNING: BM {i} ({bm_name}) has placeholder credentials — skipping.",
                  flush=True)
            i += 1
            continue

        bms.append({
            "id": bm_id,
            "token": bm_token,
            "name": bm_name
        })
        i += 1

    if not bms:
        print("ERROR: No valid Business Manager credentials found in .env")
        print("Fill in META_BM_1_ID, META_BM_1_TOKEN, etc.")
        sys.exit(1)

    return bms


def parse_args():
    """Parse command line arguments."""
    status_filter = "ACTIVE"
    days = None
    bm_filter = None
    account_limit = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            status_filter = args[i + 1].upper()
            i += 2
        elif args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--bm" and i + 1 < len(args):
            bm_filter = int(args[i + 1])
            i += 2
        elif args[i] == "--accounts" and i + 1 < len(args):
            account_limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    return status_filter, days, bm_filter, account_limit


def get_ad_accounts(bm_id, token):
    """Get all ad accounts under a Business Manager (owned + client)."""
    accounts = []
    seen_ids = set()

    for edge in ["owned_ad_accounts", "client_ad_accounts"]:
        url = f"{BASE_URL}/{bm_id}/{edge}"
        params = {
            "access_token": token,
            "fields": "id,name,account_status",
            "limit": 200
        }

        while url:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"  ERROR fetching {edge}: {response.status_code}", flush=True)
                print(f"  {response.text[:500]}", flush=True)
                break

            data = response.json()
            for acct in data.get("data", []):
                acct_id = acct["id"]
                if acct_id not in seen_ids:
                    seen_ids.add(acct_id)
                    accounts.append({
                        "id": acct_id,
                        "name": acct.get("name", "Unknown"),
                        "status": acct.get("account_status", 0)
                    })

            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}

    return accounts


def get_ads_for_account(account_id, token, status_filter, since_date=None):
    """Get all ads with creative details for an ad account."""
    ads = []
    url = f"{BASE_URL}/{account_id}/ads"
    params = {
        "access_token": token,
        "fields": ",".join([
            "id",
            "name",
            "status",
            "effective_status",
            "campaign_id",
            "adset_id",
            "creative{id,name,title,body,call_to_action_type,"
            "object_story_spec,asset_feed_spec}",
            "created_time",
            "updated_time"
        ]),
        "limit": 100
    }

    # Filter by status
    all_statuses = ["ACTIVE", "PAUSED", "ARCHIVED", "CAMPAIGN_PAUSED", "ADSET_PAUSED"]
    if status_filter == "ALL":
        params["effective_status"] = json.dumps(all_statuses)
    else:
        params["effective_status"] = json.dumps([status_filter])

    # Filter by date
    if since_date:
        params["updated_since"] = int(since_date.timestamp())

    while url:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            error_data = {}
            try:
                error_data = response.json().get("error", {})
            except Exception:
                pass
            code = error_data.get("code", 0)
            if code in (100, 190, 200):
                break
            print(f"    ERROR fetching ads: {response.status_code}", flush=True)
            print(f"    {response.text[:300]}", flush=True)
            break

        data = response.json()
        for ad in data.get("data", []):
            ads.append(ad)

        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}

    return ads


def extract_creative_text(ad):
    """Extract all text content from an ad creative."""
    creative = ad.get("creative", {})
    texts = {
        "ad_id": ad.get("id", ""),
        "ad_name": ad.get("name", ""),
        "status": ad.get("effective_status", ""),
        "campaign_id": ad.get("campaign_id", ""),
        "adset_id": ad.get("adset_id", ""),
        "created": ad.get("created_time", ""),
        "updated": ad.get("updated_time", ""),
        "creative_id": creative.get("id", ""),
        "headline": creative.get("title", ""),
        "body": creative.get("body", ""),
        "description": "",
        "cta_type": creative.get("call_to_action_type", ""),
    }

    # Get text from object_story_spec (single creative ads)
    story_spec = creative.get("object_story_spec", {})
    if story_spec:
        link_data = story_spec.get("link_data", {})
        if link_data:
            if not texts["body"]:
                texts["body"] = link_data.get("message", "")
            if not texts["headline"]:
                texts["headline"] = link_data.get("name", "")
            if not texts["description"]:
                texts["description"] = link_data.get("description", "")

        video_data = story_spec.get("video_data", {})
        if video_data:
            if not texts["body"]:
                texts["body"] = video_data.get("message", "")
            if not texts["headline"]:
                texts["headline"] = video_data.get("title", "")

    # Get text from asset_feed_spec (dynamic creative ads)
    feed_spec = creative.get("asset_feed_spec", {})
    if feed_spec:
        bodies = feed_spec.get("bodies", [])
        if bodies:
            texts["body_variations"] = [b.get("text", "") for b in bodies]
        titles = feed_spec.get("titles", [])
        if titles:
            texts["headline_variations"] = [t.get("text", "") for t in titles]
        descriptions = feed_spec.get("descriptions", [])
        if descriptions:
            texts["description_variations"] = [d.get("text", "") for d in descriptions]

    return texts


def pull_all_creatives(bms, status_filter, days, bm_filter, account_limit):
    """Main pull logic across all BMs and accounts."""
    since_date = None
    if days:
        since_date = datetime.now() - timedelta(days=days)

    all_creatives = []
    total_accounts = 0
    total_ads = 0
    skipped_accounts = 0

    for idx, bm in enumerate(bms, 1):
        if bm_filter and idx != bm_filter:
            continue

        print(f"\n{'=' * 50}", flush=True)
        print(f"Business Manager: {bm['name']} ({bm['id']})", flush=True)
        print(f"{'=' * 50}", flush=True)

        accounts = get_ad_accounts(bm["id"], bm["token"])
        print(f"  Found {len(accounts)} ad accounts", flush=True)

        if account_limit:
            if len(accounts) > account_limit:
                skipped_accounts += len(accounts) - account_limit
                print(f"  Limiting to first {account_limit} accounts", flush=True)
            accounts = accounts[:account_limit]

        total_accounts += len(accounts)

        for i, acct in enumerate(accounts, 1):
            acct_name = acct["name"][:60]
            print(f"  [{i}/{len(accounts)}] {acct_name}...", end=" ", flush=True)

            ads = get_ads_for_account(acct["id"], bm["token"], status_filter, since_date)

            if not ads:
                print("0 ads", flush=True)
                continue

            print(f"{len(ads)} ads", flush=True)
            total_ads += len(ads)

            for ad in ads:
                creative_data = extract_creative_text(ad)
                creative_data["bm_name"] = bm["name"]
                creative_data["bm_id"] = bm["id"]
                creative_data["account_name"] = acct["name"]
                creative_data["account_id"] = acct["id"]
                all_creatives.append(creative_data)

    if skipped_accounts:
        print(f"\n  ({skipped_accounts} accounts skipped due to --accounts limit)", flush=True)

    return all_creatives, total_accounts, total_ads


def save_output(creatives, total_accounts, total_ads, status_filter):
    """Save structured data to JSON file."""
    output = {
        "metadata": {
            "source": "Meta Marketing API",
            "pulled_at": datetime.now().isoformat(),
            "status_filter": status_filter,
            "total_accounts_scanned": total_accounts,
            "total_ads_found": total_ads,
            "total_creatives_extracted": len(creatives)
        },
        "creatives": creatives
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 50}", flush=True)
    print(f"DONE", flush=True)
    print(f"{'=' * 50}", flush=True)
    print(f"  Accounts scanned: {total_accounts}", flush=True)
    print(f"  Ads found: {total_ads}", flush=True)
    print(f"  Creatives saved: {len(creatives)}", flush=True)
    print(f"  Output: {OUTPUT_FILE}", flush=True)


def main():
    print("=" * 50, flush=True)
    print("Meta Creative Puller", flush=True)
    print("=" * 50, flush=True)

    env = load_env()
    bms = get_business_managers(env)
    status_filter, days, bm_filter, account_limit = parse_args()

    print(f"  Business Managers: {len(bms)}", flush=True)
    print(f"  Status filter: {status_filter}", flush=True)
    if days:
        print(f"  Updated within: {days} days", flush=True)
    if account_limit:
        print(f"  Account limit: {account_limit} per BM", flush=True)

    creatives, total_accounts, total_ads = pull_all_creatives(
        bms, status_filter, days, bm_filter, account_limit
    )

    save_output(creatives, total_accounts, total_ads, status_filter)
    print("\nThe /score bot will use this data alongside RedTrack performance data.",
          flush=True)


if __name__ == "__main__":
    main()
