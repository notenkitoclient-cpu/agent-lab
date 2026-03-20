# Agent Lab 🧪

> **Build. Experiment. Automate.**
> AIエージェントを実験・開発するメディア

---

## プロジェクト構造

```
agent-lab/
├── agents/
│   └── github_hunter/
│       └── github_hunter.py   # Experiment #1
├── experiments/               # 自動生成される実験ログ
├── web/                       # Agent Lab HP
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .env.example
└── requirements.txt
```

---

## セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envを編集してAPIキーを設定
```

---

## Agent Experiment #1: GitHub Hunter

GitHubのAI関連Trendingリポジトリを自動取得 → README要約 → X投稿文生成

### 実行方法

```bash
# 通常実行（Claude APIキー必要）
python agents/github_hunter/github_hunter.py

# APIキー不要のドライランテスト
python agents/github_hunter/github_hunter.py --dry-run

# 言語フィルタ（Pythonのみ）
python agents/github_hunter/github_hunter.py --language python

# 上位3件を対象にする
python agents/github_hunter/github_hunter.py --top 3
```

### 出力例

```
Agent Experiment #01

GitHubで面白いAIツール見つけた 👀

Tool: awesome-agent-framework

What it does
・マルチエージェントを簡単に構築できる
・LangChainと統合して柔軟な自動化
・小規模〜大規模まで対応

⭐ 12.3k stars (+450)
🔗 Repo
https://github.com/xxx/awesome-agent-framework

#AgentLab #AIAgent #GitHub
```

実験ログは `experiments/` フォルダに自動保存されます。

---

## HP（ローカル確認）

```bash
open web/index.html
```

---

## Experiments シリーズ

| # | タイトル | ステータス |
|---|---------|---------|
| 001 | GitHub Trending Agent | ✅ LIVE |
| 002 | YouTube AI動画要約 Agent | 🔜 Coming |
| 003 | AI News Scout Agent | 🔜 Coming |

---

*Agent Lab - AIエージェントを実験・開発するメディア*
