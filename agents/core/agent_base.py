import os
import json
import datetime
import sqlite3
from pathlib import Path

try:
    from slugify import slugify
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

console = Console() if HAS_RICH else None

# プロジェクトルートの絶対・相対パスを解決
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"


class AgentBase:
    name = "base-agent"
    description = "Base Agent for Agent Lab"

    def __init__(self):
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.init_manifest()

    def normalize_topics(self, raw_topics: list) -> str:
        TOPIC_MAP = {
            "llm": "LLM", "large-language-model": "LLM", "gpt": "LLM",
            "ai": "AI", "artificial-intelligence": "AI",
            "agent": "Agents", "agents": "Agents", "ai-agents": "Agents",
            "automation": "Automation",
            "machine-learning": "Machine Learning",
            "deep-learning": "Deep Learning",
            "nlp": "NLP", "rag": "RAG",
            "devtools": "DevTools", "developer-tools": "DevTools",
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript"
        }
        normalized = set()
        for t in raw_topics:
            clean = t.lower().strip()
            if clean in TOPIC_MAP:
                normalized.add(TOPIC_MAP[clean])
            else:
                normalized.add("Other")
        
        res = list(normalized)
        if "Other" in res and len(res) > 1:
            res.remove("Other")
        return ",".join(sorted(res))

    def generate_slug(self, name: str, owner: str, cursor) -> str:
        """Owner/RepoベースのSlugを生成（例: microsoft-autogen）し衝突を防ぐ"""
        base_str = f"{owner}-{name}" if owner else name
        try:
            from slugify import slugify
            slug = slugify(base_str)
        except ImportError:
            slug = base_str.lower().replace(" ", "-")
        
        # Conflict check (fallback with incrementing number just in case)
        original_slug = slug
        counter = 1
        while True:
            cursor.execute("SELECT id FROM agents WHERE slug = ?", (slug,))
            if not cursor.fetchone():
                return slug
            slug = f"{original_slug}-{counter}"
            counter += 1

    def save_to_db(self, agent_data: dict, exp_id: str, summary: str, filepath: str):
        db_path = PROJECT_ROOT / "database" / "agents.db"
        if not db_path.exists():
            self.log("⚠️ Database not found. Please run `agentlab init-db`.", "yellow")
            return
            
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        created_at = agent_data.get("created_at", now)[:10]
        
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            # Growth Score calculation
            stars = int(agent_data.get("stars", 0))
            try:
                c_date = datetime.datetime.strptime(created_at, "%Y-%m-%d")
                days = max(1, (datetime.datetime.now() - c_date).days)
            except:
                days = 1
            growth_score = stars / days
            
            topics_str = self.normalize_topics(agent_data.get("topics", []))
            slug = self.generate_slug(agent_data['name'], agent_data.get('owner', ''), cur)
            
            # UPSERT agent
            cur.execute("""
                INSERT INTO agents (
                    id, slug, name, github_url, source, stars, forks, language,
                    topics, description, growth_score, agent_score, created_at,
                    discovered_at, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    stars=excluded.stars,
                    forks=excluded.forks,
                    description=excluded.description,
                    growth_score=excluded.growth_score,
                    last_updated=excluded.last_updated
            """, (
                agent_data.get('full_name', agent_data['name']), slug, agent_data['name'], 
                agent_data.get('url', ''), self.name, stars, agent_data.get('forks', 0), 
                agent_data.get('language', 'Unknown'), topics_str, 
                agent_data.get('description', ''), growth_score, 0.0,
                created_at, now, now
            ))
            
            # UPSERT experiment
            cur.execute("""
                INSERT INTO experiments (
                    id, agent_id, title, summary, created_at, file_path
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    summary=excluded.summary,
                    file_path=excluded.file_path
            """, (
                exp_id, self.name, f"Experiment #{exp_id}: {agent_data['name']}", summary, now, filepath
            ))
            
            conn.commit()
            conn.close()
            self.log(f"💾 Saved {agent_data['name']} to SQLite database.", "green")
            
        except Exception as e:
            self.log(f"❌ Database error: {e}", "red")

    def log(self, message: str, style: str = ""):
        """richを使った統一フォーマット出力"""
        if HAS_RICH and console:
            console.print(message, style=style)
        else:
            print(message)

    def init_manifest(self):
        """manifest.jsonが存在しなければ初期化し、自エージェントを登録する"""
        if not MANIFEST_PATH.exists():
            manifest = {
                "version": "1.0.0",
                "agents": [],
                "experiments": []
            }
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        
        self.update_agent_manifest()

    def update_agent_manifest(self):
        """manifest.json の agents リストに自エージェントを登録"""
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            agents = data.get("agents", [])
            for a in agents:
                if a.get("id") == self.name:
                    return # 登録済み
            
            agents.append({
                "id": self.name,
                "name": self.name.replace("-", " ").title(),
                "description": self.description,
                "status": "active",
                "version": "1.0.0"
            })
            data["agents"] = agents
            MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            self.log(f"Manifest update error [Agent]: {e}", "red")

    def get_next_experiment_id_str(self) -> str:
        """次の実験IDを '001' のような3桁文字列で返す"""
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            experiments = data.get("experiments", [])
            if not experiments:
                return "001"
            
            max_id = 0
            for exp in experiments:
                try:
                    num = int(exp.get("id", 0))
                    max_id = max(max_id, num)
                except ValueError:
                    continue
            return f"{max_id + 1:03d}"
            
        except Exception:
            # manifest解析失敗時はファイル一覧から推測
            existing = list(EXPERIMENTS_DIR.glob("*.md"))
            max_id = 0
            for f in existing:
                try:
                    num = int(f.name.split("_")[0])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
            return f"{max_id + 1:03d}"

    def save_experiment(self, experiment_title: str, content_markdown: str, status: str = "complete", agent_data=None, summary: str = "") -> Path:
        """実験ログを保存し、manifest.json と SQLite の experiments を更新する"""
        exp_id = self.get_next_experiment_id_str()
        filename = f"{exp_id}_{self.name.replace('-', '_')}.md"
        filepath = EXPERIMENTS_DIR / filename
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # YAML Frontmatter ブロック
        frontmatter = f"""---
id: {exp_id}
agent: {self.name}
title: {experiment_title}
date: {date_str}
status: {status}
---

"""
        full_content = frontmatter + content_markdown
        filepath.write_text(full_content, encoding="utf-8")
        
        # manifest.json の実験一覧更新
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            experiments = data.get("experiments", [])
            
            # 既存の同IDがあれば上書き削除
            experiments = [e for e in experiments if e.get("id") != exp_id]
            
            experiments.append({
                "id": exp_id,
                "agent_id": self.name,
                "title": experiment_title,
                "date": date_str,
                "status": status,
                "file": f"experiments/{filename}"
            })
            
            # ID順にソートする
            experiments.sort(key=lambda x: int(x["id"]) if x["id"].isdigit() else 999)
            data["experiments"] = experiments
            MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            
        except Exception as e:
            self.log(f"Manifest update error [Experiment]: {e}", "red")
            
        # SQLite DB Update
        if agent_data:
            self.save_to_db(agent_data, exp_id, summary, f"experiments/{filename}")

        return filepath

    def run(self, **kwargs):
        """このメソッドを子クラスでオーバーライドして実装する"""
        raise NotImplementedError("run() method must be implemented")
