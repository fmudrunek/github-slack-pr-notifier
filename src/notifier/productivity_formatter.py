from notifier.repository import TeamProductivityMetrics
from notifier.slack_client import SlackBlock, SlackBlockKitMessage


class ProductivityMessageFormatter:

    def get_messages_for_team_metrics(self, metrics: TeamProductivityMetrics) -> list[SlackBlockKitMessage]:
        blocks = []
        
        # Header
        blocks.append(self.__format_header(metrics))
        
        # Team totals
        blocks.append({"type": "divider"})
        blocks.append(self.__format_team_totals(metrics))
        
        # Repository breakdown
        if metrics.repository_breakdown:
            blocks.append({"type": "divider"})
            blocks.append(self.__format_repository_breakdown(metrics))
        
        # Top reviewers
        if metrics.reviewer_approvals:
            blocks.append({"type": "divider"})
            blocks.append(self.__format_top_reviewers(metrics))
        
        return [blocks]

    def __format_header(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":rocket: *Team Effort Summary* in _Last {metrics.time_window_days} days_ :chart_with_upwards_trend:"
            }
        }

    def __format_team_totals(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":dart: *Team Totals*\n" +
                        f":white_check_mark: *{metrics.total_merged_prs}* merged PRs\n" +
                        f":heavy_plus_sign: *+{metrics.total_lines_added:,}* lines added\n" +
                        f":heavy_minus_sign: *-{metrics.total_lines_deleted:,}* lines deleted\n"
            }
        }

    def __format_repository_breakdown(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        repo_text = ":bar_chart: *Repository Breakdown*\n"
        
        active_repos = [repo for repo in metrics.repository_breakdown if repo.merged_prs_count > 0]
        
        for repo in active_repos:
            # Get repo name (remove org prefix for cleaner display)
            repo_display = repo.repository_name.split('/')[-1] if '/' in repo.repository_name else repo.repository_name
            
            # Color code based on activity level
            if repo.merged_prs_count >= 5:
                pr_emoji = ":fire:"
            elif repo.merged_prs_count >= 2:
                pr_emoji = ":zap:"
            else:
                pr_emoji = ":small_blue_diamond:"
                
            repo_text += f"{pr_emoji} *{repo_display}*: {repo.merged_prs_count} PRs (+{repo.lines_added:,}/-{repo.lines_deleted:,})\n"
        
        if not active_repos:
            repo_text += ":zzz: _No repository activity in this period_"
            
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": repo_text.strip()
            }
        }

    def __format_top_reviewers(self, metrics: TeamProductivityMetrics) -> SlackBlock:
        reviewer_text = ":trophy: *Top Reviewers*\n"
        
        # Sort reviewers by approval count (descending)
        sorted_reviewers = sorted(metrics.reviewer_approvals.items(), key=lambda x: x[1], reverse=True)
        active_reviewers = [(username, count) for username, count in sorted_reviewers[:5] if count > 0]
        
        if not active_reviewers:
            reviewer_text += ":thinking_face: _No reviews found in this period_"
        else:
            # Medal emojis for top 3
            medals = [":first_place_medal:", ":second_place_medal:", ":third_place_medal:", ":medal:", ":medal:"]
            
            for i, (username, approval_count) in enumerate(active_reviewers):
                medal = medals[i] if i < len(medals) else ":small_orange_diamond:"
                # Pluralize approvals
                approval_text = "approval" if approval_count == 1 else "approvals"
                reviewer_text += f"{i+1}. {medal} *{username}*: {approval_count} {approval_text}\n"
                
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": reviewer_text.strip()
            }
        }