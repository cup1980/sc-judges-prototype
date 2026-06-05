name: build-judges

# 実行タイミング
on:
  workflow_dispatch:        # 画面から手動実行（まずはこれで動作確認）
  schedule:
    - cron: "0 18 1 * *"    # 毎月1日 18:00(UTC)=月初 3:00(JST) に自動更新

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install requests beautifulsoup4

      - name: Build judges.json
        run: |
          mkdir -p public/data
          python scripts/build_judges.py
          mv judges.json public/data/judges.json

      - name: Commit & push if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add public/data/judges.json
          if git diff --staged --quiet; then
            echo "変更なし。コミットしません。"
          else
            git commit -m "chore: update judges.json [skip ci]"
            git push
          fi
