from agents.core.agent_base import AgentBase

class NewAgentTemplate(AgentBase):
    name = "new-agent"  # CLIで呼び出す時のID (ex: agentlab run new-agent)
    description = "ここにエージェントの説明を書きます"

    def run(self, dry_run=False, **kwargs):
        """ここにメインの処理を実装します"""
        self.log(f"🚀 {self.name} is running!", "cyan")
        
        # 1. 何らかの処理（情報収集、AI推論など）
        tool_name = "Sample AI Tool"
        summary = "This is a sample summary of the tool."
        
        # 2. Markdown形式でレポート（実験ログの中身）を作成
        content_md = f"""## 発見した情報

| ツール | 概要 |
|--------|------|
| {tool_name} | {summary} |

---

## 考察
このツールは素晴らしい。
"""
        # 3. 共通基盤を使って実験ログ保存 ＆ manifest更新
        # これだけで experiments/NNN_new_agent.md が自動で生成されます
        filepath = self.save_experiment(
            experiment_title=f"Sample Experiment by {self.name}",
            content_markdown=content_md
        )
        
        self.log(f"✅ 完了しました！ログ: {filepath}", "green")

if __name__ == "__main__":
    # 単体テスト用
    agent = NewAgentTemplate()
    agent.run()
