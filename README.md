# 📊 Dataverse to Bluesky GitHub Action

This GitHub Action:
1. Pulls datasets from your Harvard Dataverse collection
2. Commits the dataset list as `datasets.json` to the repository
3. Posts a random dataset to your Bluesky feed with title + link

Perfect for sharing research assets and building visibility.

---

## 🔧 Setup

### 1. Required Secrets
Set the following secrets in your GitHub repository:

| Secret Name       | Description                                      |
|------------------|--------------------------------------------------|
| `DATAVERSE_TOKEN`| Your Harvard Dataverse API token                 |
| `BSKY_HANDLE`     | Your Bluesky handle (e.g. soodoku.bsky.social)  |
| `BSKY_PASSWORD`   | Your Bluesky password or app password           |

---

### 2. Sample Workflow (`.github/workflows/monthly.yml`)

```yaml
name: Monthly Dataverse + Bsky

on:
  schedule:
    - cron: "0 6 1 * *"  # Run on the 1st of every month
  workflow_dispatch:

jobs:
  update-and-post:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests atproto

      - name: List datasets
        env:
          DATAVERSE_TOKEN: ${{ secrets.DATAVERSE_TOKEN }}
        run: |
          python scripts/list_datasets.py \
            -b https://dataverse.harvard.edu \
            -t $DATAVERSE_TOKEN \
            --alias soodoku \
            -o datasets.json

      - name: Commit datasets.json
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add datasets.json
          git commit -m "Update datasets.json [skip ci]" || echo "No changes"
          git push

      - name: Post to Bluesky
        env:
          BSKY_HANDLE: ${{ secrets.BSKY_HANDLE }}
          BSKY_PASSWORD: ${{ secrets.BSKY_PASSWORD }}
        run: python scripts/post_random_dataset_bsky.py
```

---

## 📜 License
MIT © Gojiplus