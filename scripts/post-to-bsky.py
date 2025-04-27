#!/usr/bin/env python3
import os
import json
import random
import requests
import regex  # requires: pip install regex
from atproto import Client

# --- Configuration from environment ---
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")
DATA_FILE = os.getenv("DATASETS_FILE", "datasets.json")
MAX_LENGTH = 290

def load_datasets(path):
    with open(path, "r") as f:
        data = json.load(f)
        # Return the datasets array from the new JSON structure
        return data.get("datasets", [])

def truncate_graphemes(text, limit):
    graphemes = regex.findall(r'\X', text)
    if len(graphemes) <= limit:
        return text
    return ''.join(graphemes[:limit - 1]) + '…'

def format_post(dataset):
    title = dataset.get("title", "Untitled Dataset")
    url = dataset.get("persistentUrl", "")
    description = dataset.get("description", "").replace("\n", " ").strip()
    source = dataset.get("source_dataverse", "")
    
    # Add source dataverse to the post if available
    source_text = f" (from {source})" if source else ""
    
    base = f"📊 {title}{source_text}\n\n{description}\n\n{url}"
    return truncate_graphemes(base, MAX_LENGTH)

def compute_byte_offsets(text, substring):
    char_start = text.find(substring)
    if char_start == -1:
        return None, None
    byte_start = len(text[:char_start].encode("utf-8"))
    byte_end = byte_start + len(substring.encode("utf-8"))
    return byte_start, byte_end

def post_to_bsky(post_text, url):
    client = Client()
    client.login(BSKY_HANDLE, BSKY_PASSWORD)
    
    byte_start, byte_end = compute_byte_offsets(post_text, url)
    if byte_start is None:
        print("⚠️ Could not find URL in post_text for facet.")
        facets = []
    else:
        facets = [
            {
                "index": {"byteStart": byte_start, "byteEnd": byte_end},
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        "uri": url
                    }
                ]
            }
        ]
    
    client.send_post(post_text, facets=facets)
    print("✅ Posted to Bluesky!")

def main():
    # Load datasets from the new JSON structure
    datasets = load_datasets(DATA_FILE)
    
    if not datasets:
        print("No datasets found.")
        return
    
    # Filter out datasets with empty titles or URLs
    valid_datasets = [d for d in datasets if d.get("title") and d.get("persistentUrl")]
    
    if not valid_datasets:
        print("No valid datasets found with titles and URLs.")
        return
        
    dataset = random.choice(valid_datasets)
    post = format_post(dataset)
    
    print(f"Selected dataset: {dataset.get('title', 'Untitled')}")
    print(f"From dataverse: {dataset.get('source_dataverse', 'unknown')}")
    print(f"Post preview:\n{post}")
    
    post_to_bsky(post, dataset.get("persistentUrl"))

if __name__ == "__main__":
    main()
