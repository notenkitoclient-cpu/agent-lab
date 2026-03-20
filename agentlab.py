#!/usr/bin/env python3
"""
Agent Lab CLI (agentlab.py)
Agent Labのすべてのエージェントを管理・実行するためのエントリーポイント（OS）。

実行例:
  python agentlab.py run github-hunter
  python agentlab.py list agents
  python agentlab.py list experiments
"""

import sys
import argparse
import json
import sqlite3
import shutil
from pathlib import Path

try:
    import markdown
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    pass

from agents.registry import AGENTS

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

console = Console() if HAS_RICH else None
PROJECT_ROOT = Path(__file__).parent.resolve()
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
DATABASE_PATH = PROJECT_ROOT / "database" / "agents.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def log(msg, style=""):
    if HAS_RICH and console:
        console.print(msg, style=style)
    else:
        print(msg)


def init_db():
    if not SCHEMA_PATH.exists():
        log(f"❌ Error: Schema file not found at {SCHEMA_PATH}", "bold red")
        sys.exit(1)
    
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        script = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(script)
        conn.commit()
        conn.close()
        log(f"✅ Database initialized successfully at {DATABASE_PATH}", "bold green")
    except Exception as e:
        log(f"❌ Error initializing database: {e}", "bold red")
        sys.exit(1)


def build_site():
    """SQLite + Markdown から静的サイトとSEOファイル(sitemap/rss/robots)を public/ 以下に生成"""
    log("🚀 Starting Agent Lab build process...", "bold cyan")
    public_dir = PROJECT_ROOT / "public"
    web_dir = PROJECT_ROOT / "web"
    
    # 1. Prepare directories
    if public_dir.exists():
        shutil.rmtree(public_dir)
    public_dir.mkdir(parents=True)
    (public_dir / "agents").mkdir()
    (public_dir / "experiments").mkdir()
    
    # Copy assets
    if (web_dir / "assets").exists():
        shutil.copytree(web_dir / "assets", public_dir / "assets")
    else:
        log("⚠️ No web/assets directory found to copy.", "yellow")
        
    # 2. Extract Data from DB
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get Agents (Top 9 for index)
        cur.execute("SELECT * FROM agents ORDER BY growth_score DESC")
        all_agents = [dict(row) for row in cur.fetchall()]
        top_agents = all_agents[:9]
        
        # Get Experiments (Top 6 for index)
        cur.execute("SELECT * FROM experiments ORDER BY id DESC")
        all_experiments = [dict(row) for row in cur.fetchall()]
        latest_experiments = all_experiments[:6]
        
        conn.close()
    except Exception as e:
        log(f"❌ Error reading Database: {e}", "bold red")
        return

    # 3. Setup Jinja2 Environment
    try:
        env = Environment(loader=FileSystemLoader(str(web_dir / "templates")))
    except NameError:
        log("❌ Error: Jinja2 is not installed. Run `pip install Jinja2`.", "bold red")
        return
    
    site_url = "https://agentlab.example.com"
    
    # 4. Generate Top Page (index.html)
    try:
        index_template = env.get_template("index.html")
        index_html = index_template.render(
            total_agents=len(all_agents),
            total_experiments=len(all_experiments),
            top_agents=top_agents,
            latest_experiments=latest_experiments
        )
        (public_dir / "index.html").write_text(index_html, encoding="utf-8")
        log("✅ Generated index.html", "green")
    except Exception as e:
        log(f"❌ Error generating index.html: {e}", "red")
        
    # 5. Generate Agent Detail Pages
    try:
        agent_template = env.get_template("agent.html")
        for agent in all_agents:
            agent_exps = [e for e in all_experiments if agent['id'] in e.get('title', '') or agent['source'] == e.get('agent_id', '')]
            html = agent_template.render(agent=agent, experiments=agent_exps)
            (public_dir / "agents" / f"{agent['slug']}.html").write_text(html, encoding="utf-8")
        log(f"✅ Generated {len(all_agents)} Agent pages", "green")
    except Exception as e:
        log(f"❌ Error generating Agent pages: {e}", "red")
        
    # 6. Generate Experiment Logs
    try:
        exp_template = env.get_template("experiment.html")
        for exp in all_experiments:
            md_path = PROJECT_ROOT / exp["file_path"]
            if not md_path.exists():
                continue
            md_text = md_path.read_text(encoding="utf-8")
            
            # Remove YAML Frontmatter block
            if md_text.startswith("---"):
                parts = md_text.split("---", 2)
                if len(parts) >= 3:
                    md_text = parts[2]
            
            content_html = markdown.markdown(md_text, extensions=['tables'])
            html = exp_template.render(exp=exp, content_html=content_html)
            (public_dir / "experiments" / f"{exp['id']}.html").write_text(html, encoding="utf-8")
        log(f"✅ Generated {len(all_experiments)} Experiment pages", "green")
    except Exception as e:
        log(f"❌ Error generating Experiment pages: {e}", "red")
        
    # 7. Generate SEO files (Sitemap, RSS, Robots)
    try:
        # Sitemap
        sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        sitemap_xml += f'  <url><loc>{site_url}/</loc></url>\n'
        for agent in all_agents:
            sitemap_xml += f'  <url><loc>{site_url}/agents/{agent["slug"]}.html</loc></url>\n'
        for exp in all_experiments:
            sitemap_xml += f'  <url><loc>{site_url}/experiments/{exp["id"]}.html</loc></url>\n'
        sitemap_xml += "</urlset>"
        (public_dir / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
        
        # RSS
        rss_xml = f'<?xml version="1.0" encoding="UTF-8" ?>\n<rss version="2.0">\n<channel>\n  <title>Agent Lab</title>\n  <link>{site_url}</link>\n  <description>The Ultimate AI Agent Discovery Platform</description>\n'
        for exp in latest_experiments:
            rss_xml += f'  <item>\n    <title>{exp["title"]}</title>\n    <link>{site_url}/experiments/{exp["id"]}.html</link>\n    <description>{exp["summary"]}</description>\n  </item>\n'
        rss_xml += "</channel>\n</rss>"
        (public_dir / "rss.xml").write_text(rss_xml, encoding="utf-8")
        
        # Robots.txt
        robots_txt = f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml"
        (public_dir / "robots.txt").write_text(robots_txt, encoding="utf-8")
        
        log("✅ Generated sitemap.xml, rss.xml, robots.txt", "green")
        log("🎉 Build complete! Check the `public/` directory.", "bold green")
    except Exception as e:
        log(f"❌ Error generating SEO files: {e}", "red")

def list_agents():
    """登録されているエージェント一覧を表示"""
    if not HAS_RICH:
        print("Registered Agents:")
        for name in AGENTS.keys():
            print(f"- {name}")
        return

    table = Table(title="🤖 Available Agents", show_header=True, header_style="bold cyan")
    table.add_column("Agent ID", style="bold green")
    table.add_column("Class", style="dim")
    table.add_column("Description")
    
    for name, cls in AGENTS.items():
        desc = getattr(cls, "description", "No description")
        table.add_row(name, cls.__name__, desc)
    console.print(table)


def list_experiments():
    """完了した実験一覧を表示"""
    if not MANIFEST_PATH.exists():
        log("No manifest found. Run experiments first.", "yellow")
        return
        
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        experiments = data.get("experiments", [])
        
        if not experiments:
            log("No experiments recorded yet.", "yellow")
            return
            
        if not HAS_RICH:
            print(f"Experiments ({len(experiments)} total):")
            for e in experiments:
                print(f"[{e.get('id')}] {e.get('title')} (by {e.get('agent_id')})")
            return
            
        table = Table(title="🧪 Agent Lab Experiments", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="bold green", justify="right")
        table.add_column("Agent", style="cyan")
        table.add_column("Title")
        table.add_column("Date", style="dim")
        table.add_column("Status")
        
        for e in experiments:
            status = e.get("status", "")
            if status == "complete":
                status = "[green]complete[/green]"
            table.add_row(e.get("id"), e.get("agent_id"), e.get("title"), e.get("date"), status)
        console.print(table)
    except Exception as e:
        log(f"Error reading manifest: {e}", "red")


def main():
    parser = argparse.ArgumentParser(description="Agent Lab Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init-db コマンド
    subparsers.add_parser("init-db", help="Initialize the SQLite database")

    # run コマンド
    run_parser = subparsers.add_parser("run", help="Run an agent")
    run_parser.add_argument("agent_name", help="Name of the agent to run (e.g. github-hunter)")
    run_parser.add_argument("--dry-run", action="store_true", help="Run in API-key-free mode if supported")
    run_parser.add_argument("--top", type=int, default=1, help="Number of items to process")
    
    # list コマンド
    list_parser = subparsers.add_parser("list", help="List registered resources")
    list_parser.add_argument("resource", choices=["agents", "experiments"], help="Resource to list")
    
    # build コマンド
    subparsers.add_parser("build", help="Build static site from SQLite to public directory")
    
    # status コマンド
    subparsers.add_parser("status", help="Show the current manifest status")

    args = parser.parse_args()

    # コマンド未指定時はヘルプ表示
    if not args.command:
        if HAS_RICH and console:
            console.print(Panel("[bold green]Agent Lab CLI[/bold green]\nBuild. Experiment. Automate.", border_style="green"))
        parser.print_help()
        sys.exit(0)

    if args.command == "init-db":
        init_db()
        
    elif args.command == "run":
        agent_name = args.agent_name
        if agent_name not in AGENTS:
            log(f"❌ Error: Agent '{agent_name}' not found.", "bold red")
            log("Use 'python agentlab.py list agents' to see available agents.", "yellow")
            sys.exit(1)
            
        # 対象のエージェントをインスタンス化して実行
        agent_cls = AGENTS[agent_name]
        try:
            agent = agent_cls()
            agent.run(dry_run=args.dry_run, top=args.top)
            log("\n✅ Agent run completed successfully.", "bold green")
        except Exception as e:
            log(f"\n❌ Agent run failed: {e}", "bold red")
            sys.exit(1)
            
    elif args.command == "list":
        if args.resource == "agents":
            list_agents()
        elif args.resource == "experiments":
            list_experiments()
            
    elif args.command == "build":
        build_site()
            
    elif args.command == "status":
        if MANIFEST_PATH.exists():
            if HAS_RICH:
                # 綺麗にJSONをハイライト表示するなら Syntax を使うことも可能
                console.print_json(MANIFEST_PATH.read_text(encoding="utf-8"))
            else:
                print(MANIFEST_PATH.read_text(encoding="utf-8"))
        else:
            log("No manifest.json found.", "yellow")


if __name__ == "__main__":
    main()
