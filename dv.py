#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import json


def parse_arguments():
    parser = argparse.ArgumentParser(description="List all Dataverse datasets owned by the authenticated user.")
    parser.add_argument("-b", "--base-url", required=True, help="Dataverse base URL (e.g. https://dataverse.harvard.edu)")
    parser.add_argument("-t", "--api-token", required=True, help="API token for authentication")
    parser.add_argument("--alias", help="Optional Dataverse alias override (e.g. soodoku)")
    parser.add_argument("-o", "--output", help="Output file to save dataset list as JSON")
    return parser.parse_args()


def get_owned_datasets(base_url, api_token, alias=None):
    headers = {"X-Dataverse-key": api_token}

    if not alias:
        r = requests.get(f"{base_url}/api/users/:me", headers=headers)
        r.raise_for_status()
        user_data = r.json().get("data", {})
        alias = user_data.get("persistentUserId") or user_data.get("userName")

    if not alias:
        raise RuntimeError("Unable to determine Dataverse alias from API token")

    r = requests.get(f"{base_url}/api/dataverses/{alias}/contents", headers=headers)
    r.raise_for_status()
    contents = r.json().get("data", [])

    datasets = []
    for item in contents:
        if item.get("type") != "dataset":
            continue

        persistent_id = item.get("persistentUrl", "").replace("https://doi.org/", "doi:")
        if not persistent_id:
            continue

        detail_url = f"{base_url}/api/datasets/:persistentId/?persistentId={persistent_id}"
        detail_resp = requests.get(detail_url, headers=headers)
        if detail_resp.status_code != 200:
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

        item["title"] = title
        item["description"] = description
        datasets.append(item)

    return datasets


def main():
    args = parse_arguments()

    try:
        datasets = get_owned_datasets(args.base_url, args.api_token, args.alias)
        print(f"Found {len(datasets)} owned datasets.", file=sys.stderr)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(datasets, f, indent=2)
            print(f"Saved to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(datasets, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
