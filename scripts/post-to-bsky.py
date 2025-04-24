#!/usr/bin/env python3
import os
import json
import random
import requests
from atproto import Client

# --- Configuration from environment ---
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")
DATA_FILE = os.getenv("DATASETS_FILE", "datasets.json")

def load_datasets(path):
    with open(path, "r") as f:
        return json.load(f)

def format_post(dataset):
    title = dataset.get("title", "Untitled Dataset")
    description = dataset.get("description", "")[:200]
    url = dataset.get("persistentUrl")
    post = f"📊 {title}\n\n{description}\n\n{url}"
    return post

def post_to_bsky(post_text, url):
    client = Client()
    client.login(BSKY_HANDLE, BSKY_PASSWORD)

    # Find link position in text for facets
    byte_start = post_text.find(url.encode("utf-8").decode("utf-8"))
    byte_end = byte_start + len(url.encode("utf-8"))

    facets = [
        {
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]
        }
    ]

    client.send_post(post_text, facets=facets)
    print("✅ Posted to Bluesky!")

def main():
    datasets = load_datasets(DATA_FILE)
    if not datasets:
        print("No datasets found.")
        return

    dataset = random.choice(datasets)
    post = format_post(dataset)
    post_to_bsky(post, dataset.get("persistentUrl"))

if __name__ == "__main__":
    main()