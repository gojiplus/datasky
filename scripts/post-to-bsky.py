#!/usr/bin/env python3
import os
import json
import random
import re
import html
import regex
from atproto import Client

# Configuration
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")
DATA_FILE = os.getenv("DATASETS_FILE", "datasets.json")
MAX_LENGTH = 290  # leave room for facets and link text


def load_datasets(path):
    """Load a list of dataset dicts from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("datasets", [])


def truncate_graphemes(text, limit):
    """Truncate to a maximum number of Unicode grapheme clusters."""
    graphemes = regex.findall(r'\X', text)
    if len(graphemes) <= limit:
        return text
    return ''.join(graphemes[:limit - 1]) + '…'


def clean_text(text):
    """Strip HTML tags, unescape entities, normalize spaces."""
    no_tags = re.sub(r'<[^>]+>', '', text)
    unescaped = html.unescape(no_tags)
    return unescaped.replace('\u00a0', ' ').strip()


def format_post(dataset):
    """Build the post body and facets for a random dataset."""
    title = clean_text(dataset.get("title", "Untitled Dataset"))
    desc_raw = dataset.get("description", "")
    description = clean_text(desc_raw)
    # take a snippet
    snippet = (description[:200].rsplit(" ", 1)[0] + "…") if description else ""

    source = dataset.get("source_dataverse", "")
    source_text = f" (from {clean_text(source)})" if source else ""

    link_label = "dataverse link"
    sep = "\n\n"

    # Reserve graphemes for link label and separator
    link_gr = len(regex.findall(r'\X', link_label))
    sep_gr = len(regex.findall(r'\X', sep))
    max_body = MAX_LENGTH - link_gr - sep_gr

    body = f"📊 {title}{source_text}{sep}{snippet}"
    if len(regex.findall(r'\X', body)) > max_body:
        body = truncate_graphemes(body, max_body)
        # back off to last full word
        if " " in body:
            body = body.rsplit(" ", 1)[0]
        body += '…'

    full = f"{body}{sep}{link_label}"

    # Compute byte offsets for facet
    b_full = full.encode('utf-8')
    b_body = body.encode('utf-8') + sep.encode('utf-8')
    start = len(b_body)
    end = start + len(link_label.encode('utf-8'))

    facets = [{
        "index": {"byteStart": start, "byteEnd": end},
        "features": [{
            "$type": "app.bsky.richtext.facet#link",
            "uri": dataset.get("persistentUrl", "")
        }]
    }]

    return full, facets


def post_to_bsky(text, facets):
    """Login and send a post with facets."""
    client = Client()
    client.login(BSKY_HANDLE, BSKY_PASSWORD)
    client.send_post(text, facets=facets)
    print("✅ Posted to Bluesky!")


def main():
    if not BSKY_HANDLE or not BSKY_PASSWORD:
        print("ERROR: BSKY_HANDLE and BSKY_PASSWORD must be set", file=sys.stderr)
        return

    datasets = load_datasets(DATA_FILE)
    valid = [d for d in datasets if d.get("title") and d.get("persistentUrl")]
    if not valid:
        print("No valid datasets found.")
        return

    dataset = random.choice(valid)
    post_text, facets = format_post(dataset)

    print(f"Selected dataset: {dataset.get('title')}")
    print(f"Preview:\n{post_text}")

    post_to_bsky(post_text, facets)


if __name__ == "__main__":
    main()
