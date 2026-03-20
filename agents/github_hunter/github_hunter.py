#!/usr/bin/env python3
"""
GitHub Hunter Agent - Agent Lab Experiment #1 (Refactored for Phase 2)
GitHubのAI関連Trendingリポジトリを取得し、要約してX投稿文を生成するエージェント
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from agents.core.agent_base import AgentBase, PROJECT_ROOT

# プロジェクトルートの.envを読み込む
load_dotenv(PROJECT_ROOT / ".env")

AI_KEYWORDS = [
    "agent", "ai", "llm", "gpt", "claude", "gemini", "openai",
    "automation", "machine-learning", "deep-learning", "neural",
    "transformer", "rag", "vector", "embedding", "langchain",
    "autogen", "crewai", "multi-agent", "copilot", "diffusion",
    "browser-use", "agents"
]


class GitHubHunterAgent(AgentBase):
    name = "github-hunter"
    description = "GitHub Trendingを監視してAIツールを発掘・要約する"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_trending_repos(self, language: str = "") -> list[dict]:
        """GitHub Trendingからリポジトリ一覧を取得"""
        url = "https://github.com/trending"
        if language:
            url += f"/{language}"

        self.log(f"\n🔍 GitHub Trendingを取得中... ({url})", "cyan")
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        repos = []

        for article in soup.select("article.Box-row"):
            try:
                h2 = article.select_one("h2 a")
                if not h2: continue
                full_name = h2.get("href", "").strip("/")
                owner, repo_name = full_name.split("/")

                desc_el = article.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                stars_el = article.select("a.Link--muted")
                stars = stars_el[0].get_text(strip=True) if stars_el else "0"

                today_stars_el = article.select_one("span.d-inline-block.float-sm-right")
                today_stars = today_stars_el.get_text(strip=True) if today_stars_el else ""

                lang_el = article.select_one("[itemprop='programmingLanguage']")
                language_name = lang_el.get_text(strip=True) if lang_el else "Unknown"

                repos.append({
                    "owner": owner, "name": repo_name, "full_name": full_name,
                    "url": f"https://github.com/{full_name}", "description": description,
                    "stars": stars, "today_stars": today_stars, "language": language_name,
                })
            except Exception:
                continue

        self.log(f"✅ {len(repos)}件のリポジトリを取得しました", "green")
        return repos

    def filter_ai_repos(self, repos: list[dict]) -> list[dict]:
        """AI/LLM/Agent関連リポジトリをフィルタリング"""
        ai_repos = []
        for repo in repos:
            text = f"{repo['name']} {repo['description']}".lower()
            if any(kw in text for kw in AI_KEYWORDS):
                ai_repos.append(repo)
        self.log(f"🤖 AI関連: {len(ai_repos)}件／全体: {len(repos)}件", "yellow")
        return ai_repos

    def fetch_repo_details(self, owner: str, repo_name: str) -> dict:
        """Fetch repo details from GitHub API to get topics, forks and created_at."""
        url = f"https://api.github.com/repos/{owner}/{repo_name}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "topics": data.get("topics", []),
                    "created_at": data.get("created_at", ""),
                    "forks": data.get("forks_count", 0),
                    "stars": data.get("stargazers_count", 0),
                    "language": data.get("language", "")
                }
        except Exception as e:
            self.log(f"⚠️ API Error fetching details: {e}", "yellow")
        return {}

    def fetch_readme(self, owner: str, repo_name: str) -> str:
        """GitHub APIでREADMEを取得（トークンがあれば使用）"""
        url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.raw"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                text = response.text
                return text[:3000] if len(text) > 3000 else text
        except Exception:
            pass
        return ""

    def summarize_with_claude(self, readme: str, repo: dict) -> str:
        """Claude APIでREADMEを要約する"""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return f"（要約スキップ: ANTHROPIC_API_KEYが未設定）\n説明: {repo.get('description', 'なし')}"

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = f"""You are a technical writer for 'Agent Lab', an AI agent discovery platform.

Repository: {repo['full_name']}
Description: {repo.get('description', 'No description')}
Stars: {repo.get('stars', 0)}
Language: {repo.get('language', 'Unknown')}
README (excerpt):
{readme}

Write EXACTLY 3 bullet points in ENGLISH. Be SPECIFIC and TECHNICAL.
- Bullet 1: What it does (use concrete technical terms)
- Bullet 2: The specific problem it solves (mention real use cases)
- Bullet 3: Who benefits most (be specific: 'RAG pipeline developers' not 'developers')
- NEVER use vague phrases like 'great for', 'useful for', 'helps you'
- Each bullet under 80 characters

Format:
- [bullet 1]
- [bullet 2]
- [bullet 3]

Repository: {repo['full_name']}
Description: {repo.get('description', 'No description')}
README (excerpt):
{readme}

Summarize this repository in EXACTLY 3 bullet points in ENGLISH.
Focus on:
- What it does
- Why it is useful / What problem it solves
- Who should use it

Format:
- [bullet 1]
- [bullet 2]
- [bullet 3]

Keep each bullet under 60 characters. Be specific and interesting."""

            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
            
        except ImportError:
            return f"（要約エラー: anthropicライブラリが未インストール）\n説明: {repo.get('description', 'なし')}"
        except Exception as e:
            return f"（要約エラー: {e}）\n説明: {repo.get('description', 'なし')}"

    def generate_x_post(self, repo: dict, summary: str, exp_id: str) -> str:
        """X投稿文を生成"""
        desc = repo.get('description', '')
        return f"Agent Experiment #{exp_id}\n\nDiscovered an interesting AI tool 👀\n\nTool: {repo['name']}\n\nWhat it does:\n{summary}\n\n⭐ {repo['stars']} stars\n🔗 Repo: {repo['url']}\n\n#AgentLab #AIAgent #GitHub"

    def run(self, dry_run=False, language="", top=1, **kwargs):
        """エージェントのメイン処理（CLIから呼ばれる）"""
        if HAS_RICH:
            self.log(Panel("[bold green]🤖 GitHub Hunter Agent[/bold green]", border_style="green"))
        else:
            self.log("🤖 GitHub Hunter Agent")

        # STEP 1: Trending取得
        if HAS_RICH:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("GitHub Trendingを取得中...", total=None)
                repos = self.fetch_trending_repos(language)
                progress.remove_task(task)
        else:
            repos = self.fetch_trending_repos(language)

        if not repos:
            self.log("❌ リポジトリが取得できませんでした。", "red")
            return

        # STEP 2: AI関連絞り込み
        ai_repos = self.filter_ai_repos(repos)
        targets = ai_repos[:top] if ai_repos else repos[:top]

        for selected in targets:
            exp_id = self.get_next_experiment_id_str()
            self.log(f"\n🧪 実験 #{exp_id}: [{selected['full_name']}]", "bold cyan")

            # STEP 3: README & Repo details
            self.log("📖 Fetching Repository Details...", "dim")
            if not dry_run:
                details = self.fetch_repo_details(selected["owner"], selected["name"])
                readme = self.fetch_readme(selected["owner"], selected["name"])
                
                # Merge details into selected
                if details:
                    selected["topics"] = details.get("topics", [])
                    selected["created_at"] = details.get("created_at", "")
                    selected["forks"] = details.get("forks", 0)
                    if details.get("stars"):
                        selected["stars"] = details.get("stars")
                    if details.get("language"):
                        selected["language"] = details.get("language")
            else:
                readme = ""
                selected["topics"] = ["LLM", "Python", "Agent"]
                selected["created_at"] = "2024-01-01T00:00:00Z"
                selected["forks"] = 123
                selected["stars"] = 9999

            # STEP 4: Claude要約
            self.log("🧠 Generating summary with Claude...", "dim")
            if dry_run:
                summary = f"- {selected.get('description', 'AI Tool')[:50]}\n- Trending rapidly on GitHub\n- Great for developers and researchers"
            else:
                summary = self.summarize_with_claude(readme, selected)

            # STEP 5: X投稿文生成
            x_post = self.generate_x_post(selected, summary, exp_id)

            # STEP 6: Markdownレポジトリコンテンツ作成 (AgentBaseに渡す中身)
            content_md = f"""## Discovered Repository

| Property | Value |
|----------|-------|
| Repository | [{selected['full_name']}]({selected['url']}) |
| Description | {selected.get('description', 'None')} |
| Stars | {selected['stars']} |
| Forks | {selected.get('forks', 0)} |
| Language | {selected['language']} |
| Topics | {', '.join(selected.get('topics', []))} |

---

## AI Summary

{summary}

---

## X Post Draft

```text
{x_post}
```

---

*Agent Lab - Build. Experiment. Automate.*
"""
            # STEP 7: 共通基盤による自動保存・Manifest登録・YAML付与
            log_path = self.save_experiment(
                experiment_title=f"GitHub Trending: {selected['name']}",
                content_markdown=content_md,
                agent_data=selected,
                summary=summary
            )
            
            if HAS_RICH:
                self.log(Panel(x_post, title="🐦 X投稿文", border_style="blue"))
            else:
                self.log("\n🐦 X投稿文:\n" + x_post + "\n")
                
            self.log(f"💾 実験ログを保存しました: {log_path}", "green")

if __name__ == "__main__":
    # 単体でのテスト実行
    agent = GitHubHunterAgent()
    agent.run(dry_run=True, top=1)
