#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import json
from tqdm import tqdm

def parse_arguments():
    parser = argparse.ArgumentParser(description="List Dataverse datasets from multiple dataverses.")
    parser.add_argument("-b", "--base-url", required=True, help="Dataverse base URL (e.g. https://dataverse.harvard.edu)")
    parser.add_argument("-t", "--api-token", required=True, help="API token for authentication")
    parser.add_argument("-d", "--dataverses", nargs="+", help="List of dataverse aliases to search (e.g. soodoku sawasdee)")
    parser.add_argument("--include-mine", action="store_true", help="Also include your primary dataverse based on API token")
    parser.add_argument("-o", "--output", help="Output file to save dataset list as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display verbose output")
    return parser.parse_args()

def get_user_dataverse(base_url, api_token):
    """Get the user's primary dataverse alias based on API token"""
    headers = {"X-Dataverse-key": api_token}
    try:
        r = requests.get(f"{base_url}/api/users/:me", headers=headers)
        r.raise_for_status()
        user_data = r.json().get("data", {})
        alias = user_data.get("persistentUserId") or user_data.get("userName")
        return alias
    except requests.exceptions.RequestException as e:
        print(f"Error getting user dataverse: {e}", file=sys.stderr)
        return None

def get_dataverse_datasets(base_url, api_token, alias):
    """Get datasets from a specific dataverse"""
    headers = {"X-Dataverse-key": api_token}
    
    try:
        print(f"Accessing dataverse: {alias}", file=sys.stderr)
        r = requests.get(f"{base_url}/api/dataverses/{alias}/contents", headers=headers)
        r.raise_for_status()
        contents = r.json().get("data", [])
        
        datasets = []
        print(f"Found {sum(1 for item in contents if item.get('type') == 'dataset')} datasets in {alias}", file=sys.stderr)
        
        # Use tqdm for progress bar
        for item in tqdm(contents, desc=f"Processing {alias}", unit="item"):
            if item.get("type") != "dataset":
                continue
                
            persistent_id = item.get("persistentUrl", "").replace("https://doi.org/", "doi:")
            if not persistent_id:
                continue
                
            detail_url = f"{base_url}/api/datasets/:persistentId/?persistentId={persistent_id}"
            detail_resp = requests.get(detail_url, headers=headers)
            if detail_resp.status_code != 200:
                print(f"Error accessing dataset {persistent_id}: {detail_resp.text}", file=sys.stderr)
                continue
                
            detail_data = detail_resp.json().get("data", {})
            fields = detail_data.get("latestVersion", {}).get("metadataBlocks", {}).get("citation", {}).get("fields", [])
            
            title = ""
            description = ""
            
            for field in fields:
                if field.get("typeName") == "title":
                    title = field.get("value", "")
                elif field.get("typeName") == "dsDescription":
                    desc_list = field.get("value", [])
                    if isinstance(desc_list, list):
                        for d in desc_list:
                            val = d.get("dsDescriptionValue", {}).get("value")
                            if val:
                                description = val
                                break
            
            # Add source dataverse information and enriched metadata
            item["source_dataverse"] = alias
            item["title"] = title
            item["description"] = description
            datasets.append(item)
            
        return datasets
    except requests.exceptions.RequestException as e:
        print(f"Error processing dataverse {alias}: {e}", file=sys.stderr)
        return []

def main():
    args = parse_arguments()
    all_datasets = []
    dataverse_aliases = []
    
    # Add user's primary dataverse if requested
    if args.include_mine:
        user_alias = get_user_dataverse(args.base_url, args.api_token)
        if user_alias and user_alias not in (args.dataverses or []):
            dataverse_aliases.append(user_alias)
    
    # Add explicitly specified dataverses
    if args.dataverses:
        dataverse_aliases.extend(args.dataverses)
    
    if not dataverse_aliases:
        print("Error: No dataverses specified. Use --dataverses or --include-mine", file=sys.stderr)
        sys.exit(1)
        
    print(f"Processing {len(dataverse_aliases)} dataverses: {', '.join(dataverse_aliases)}", file=sys.stderr)
    
    # Process each dataverse
    for alias in dataverse_aliases:
        datasets = get_dataverse_datasets(args.base_url, args.api_token, alias)
        all_datasets.extend(datasets)
        
    # Output results
    result = {
        "base_url": args.base_url,
        "dataverses": dataverse_aliases,
        "count": len(all_datasets),
        "datasets": all_datasets
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Saved {len(all_datasets)} datasets to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
