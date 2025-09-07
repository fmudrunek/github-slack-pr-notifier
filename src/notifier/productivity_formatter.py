from notifier.repository import TeamProductivityMetrics
from notifier.slack_client import SlackBlock, SlackBlockKitMessage


class ProductivityMessageFormatter:

    def get_messages_for_team_metrics(self, metrics: TeamProductivityMetrics) -> list[SlackBlockKitMessage]:
        blocks = []
        
        # Header
        blocks.append(self.__format_header(metrics))
        
        # Team totals section
        blocks.append(self.__format_team_totals(metrics))
        
        # Repository breakdown section
        if metrics.repository_breakdown:
            blocks.append(self.__format_repository_breakdown(metrics))
        
        # Top reviewers section
        if metrics.reviewer_approvals:
            blocks.append(self.__format_top_reviewers(metrics))
        
        return [blocks]  # Return as single message with multiple blocks

    def __format_header(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        repo_names = [repo.repository_name for repo in metrics.repository_breakdown]
        repo_list = ", ".join(repo_names[:3])  # Show first 3 repos
        if len(repo_names) > 3:
            repo_list += f" (+{len(repo_names) - 3} more)"
        
        return {
            "type": "header",
            "text": {
                "type": "plain_text", 
                "text": f"📊 Team Productivity Summary (Last {metrics.time_window_days} days)"
            }
        }

    def __format_team_totals(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        elements = [
            {"type": "text", "text": "🎯 ", "style": {"bold": True}},
            {"type": "text", "text": "Team Totals", "style": {"bold": True}},
            {"type": "text", "text": f"\n• Merged PRs: {metrics.total_merged_prs}"},
            {"type": "text", "text": f"\n• Lines Added: +{metrics.total_lines_added:,}"},
            {"type": "text", "text": f"\n• Lines Deleted: -{metrics.total_lines_deleted:,}"}
        ]
        
        return {
            "type": "rich_text",
            "elements": [{"type": "rich_text_section", "elements": elements}]
        }

    def __format_repository_breakdown(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        elements = [
            {"type": "text", "text": "📈 ", "style": {"bold": True}},
            {"type": "text", "text": "Repository Breakdown", "style": {"bold": True}}
        ]
        
        for repo in metrics.repository_breakdown:
            if repo.merged_prs_count > 0:  # Only show repos with activity
                elements.append({
                    "type": "text", 
                    "text": f"\n• {repo.repository_name}: {repo.merged_prs_count} PRs merged (+{repo.lines_added:,}/-{repo.lines_deleted:,} lines)"
                })
        
        return {
            "type": "rich_text",
            "elements": [{"type": "rich_text_section", "elements": elements}]
        }

    def __format_top_reviewers(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        elements = [
            {"type": "text", "text": "👥 ", "style": {"bold": True}},
            {"type": "text", "text": "Top Reviewers", "style": {"bold": True}}
        ]
        
        # Sort reviewers by approval count (descending)
        sorted_reviewers = sorted(metrics.reviewer_approvals.items(), key=lambda x: x[1], reverse=True)
        
        for username, approval_count in sorted_reviewers[:5]:  # Show top 5 reviewers
            if approval_count > 0:
                elements.append({
                    "type": "text",
                    "text": f"\n• {username}: {approval_count} approvals"
                })
        
        return {
            "type": "rich_text",
            "elements": [{"type": "rich_text_section", "elements": elements}]
        }