"""
Analytics Engine: Analyze script performance, detect patterns,
figure out why videos went viral or flopped.
"""
import json
from datetime import datetime, timedelta
from src.utils.database import fetch_all, fetch_one, execute_query, init_db


class AnalyticsEngine:

    # Thresholds for verdict classification
    VIRAL_VIEWS = 100_000
    GOOD_VIEWS = 10_000
    LOW_VIEWS = 1_000

    def __init__(self):
        init_db()

    def classify_video(self, views, engagement_rate):
        """Classify a video's performance."""
        if views >= self.VIRAL_VIEWS:
            return "viral"
        elif views >= self.GOOD_VIEWS:
            return "good"
        elif views >= self.LOW_VIEWS:
            return "average"
        else:
            return "flop"

    def get_performance_summary(self, days=None):
        """Get overall performance summary for a time period."""
        query = """
            SELECT
                v.id, v.tiktok_video_id, v.caption, v.posted_at, v.script_id,
                s.title as script_title, s.niche, s.script_type,
                vm.views, vm.likes, vm.comments, vm.shares, vm.saves,
                vm.engagement_rate
            FROM videos v
            LEFT JOIN scripts s ON s.id = v.script_id
            LEFT JOIN video_metrics vm ON vm.video_id = v.id
            AND vm.scraped_at = (
                SELECT MAX(vm2.scraped_at) FROM video_metrics vm2
                WHERE vm2.video_id = v.id
            )
            WHERE 1=1
        """
        params = []
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND v.posted_at >= ?"
            params.append(cutoff)
        query += " ORDER BY COALESCE(vm.views, 0) DESC"
        return fetch_all(query, params)

    def get_niche_performance(self):
        """Compare performance across different niches."""
        return fetch_all("""
            SELECT
                s.niche,
                COUNT(DISTINCT v.id) as total_videos,
                AVG(vm.views) as avg_views,
                AVG(vm.likes) as avg_likes,
                AVG(vm.engagement_rate) as avg_engagement,
                MAX(vm.views) as best_views,
                SUM(vm.views) as total_views
            FROM scripts s
            JOIN videos v ON v.script_id = s.id
            JOIN video_metrics vm ON vm.video_id = v.id
            AND vm.scraped_at = (
                SELECT MAX(vm2.scraped_at) FROM video_metrics vm2
                WHERE vm2.video_id = v.id
            )
            WHERE s.niche IS NOT NULL
            GROUP BY s.niche
            ORDER BY avg_views DESC
        """)

    def get_hook_analysis(self):
        """Analyze which hooks perform best."""
        return fetch_all("""
            SELECT
                s.hook,
                COUNT(DISTINCT v.id) as times_used,
                AVG(vm.views) as avg_views,
                AVG(vm.engagement_rate) as avg_engagement,
                MAX(vm.views) as best_views
            FROM scripts s
            JOIN videos v ON v.script_id = s.id
            JOIN video_metrics vm ON vm.video_id = v.id
            AND vm.scraped_at = (
                SELECT MAX(vm2.scraped_at) FROM video_metrics vm2
                WHERE vm2.video_id = v.id
            )
            WHERE s.hook IS NOT NULL AND s.hook != ''
            GROUP BY s.hook
            ORDER BY avg_views DESC
        """)

    def get_posting_time_analysis(self):
        """Analyze which posting times perform best."""
        return fetch_all("""
            SELECT
                CASE
                    WHEN CAST(strftime('%H', v.posted_at) AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning (6-12)'
                    WHEN CAST(strftime('%H', v.posted_at) AS INTEGER) BETWEEN 12 AND 17 THEN 'Afternoon (12-18)'
                    WHEN CAST(strftime('%H', v.posted_at) AS INTEGER) BETWEEN 18 AND 23 THEN 'Evening (18-24)'
                    ELSE 'Night (0-6)'
                END as time_slot,
                COUNT(*) as total_videos,
                AVG(vm.views) as avg_views,
                AVG(vm.engagement_rate) as avg_engagement
            FROM videos v
            JOIN video_metrics vm ON vm.video_id = v.id
            AND vm.scraped_at = (
                SELECT MAX(vm2.scraped_at) FROM video_metrics vm2
                WHERE vm2.video_id = v.id
            )
            WHERE v.posted_at IS NOT NULL
            GROUP BY time_slot
            ORDER BY avg_views DESC
        """)

    def compare_scripts(self, script_id_a, script_id_b):
        """Compare performance of two scripts side by side."""
        def _get_script_stats(sid):
            return fetch_one("""
                SELECT
                    s.title, s.hook, s.niche, s.content,
                    AVG(vm.views) as avg_views,
                    AVG(vm.engagement_rate) as avg_engagement,
                    MAX(vm.views) as best_views,
                    COUNT(DISTINCT v.id) as num_videos
                FROM scripts s
                LEFT JOIN videos v ON v.script_id = s.id
                LEFT JOIN video_metrics vm ON vm.video_id = v.id
                WHERE s.id = ?
            """, [sid])
        return {
            "script_a": _get_script_stats(script_id_a),
            "script_b": _get_script_stats(script_id_b),
        }

    def get_growth_trend(self, video_db_id):
        """Get how a video's metrics grew over time."""
        return fetch_all("""
            SELECT views, likes, comments, shares, saves,
                   engagement_rate, scraped_at
            FROM video_metrics
            WHERE video_id = ?
            ORDER BY scraped_at ASC
        """, [video_db_id])

    def generate_analysis_prompt(self, days=7):
        """
        Generate a comprehensive prompt for Claude to analyze your content.
        Returns a structured prompt with all data embedded.
        """
        videos = self.get_performance_summary(days=days)
        niche_perf = self.get_niche_performance()
        hook_perf = self.get_hook_analysis()

        # Build the analysis data
        video_summaries = []
        for v in videos:
            verdict = self.classify_video(
                v.get("views", 0) or 0,
                v.get("engagement_rate", 0) or 0
            )
            video_summaries.append({
                "video_id": v["tiktok_video_id"],
                "caption": v["caption"],
                "script_title": v.get("script_title", "Unknown"),
                "niche": v.get("niche", "Unknown"),
                "views": v.get("views", 0),
                "likes": v.get("likes", 0),
                "comments": v.get("comments", 0),
                "shares": v.get("shares", 0),
                "engagement_rate": round(v.get("engagement_rate", 0) or 0, 2),
                "verdict": verdict,
                "posted_at": v.get("posted_at", ""),
            })

        prompt = f"""Analyze my TikTok content performance for the last {days} days.

## Video Performance Data:
{json.dumps(video_summaries, indent=2)}

## Niche Performance:
{json.dumps([dict(r) for r in niche_perf], indent=2) if niche_perf else "No niche data yet"}

## Hook Performance:
{json.dumps([dict(r) for r in hook_perf], indent=2) if hook_perf else "No hook data yet"}

Please analyze:
1. **Viral Videos**: Why did the top-performing videos go viral? What patterns do you see?
2. **Flop Videos**: Why did the underperforming videos fail? Common mistakes?
3. **Hook Analysis**: Which opening hooks grabbed attention best?
4. **Niche Insights**: Which niches/topics resonate most with the audience?
5. **Recommendations**: Based on this data, what should I do differently?
6. **Script Patterns**: What script structure/format works best?
7. **Engagement Tips**: How to improve engagement rate?

Be specific and reference actual video data in your analysis."""

        return prompt

    def save_analysis(self, video_id=None, script_id=None, analysis_type="viral_analysis",
                      verdict="", strengths=None, weaknesses=None,
                      recommendations=None, full_analysis=""):
        """Save an AI analysis result to the database."""
        execute_query("""
            INSERT INTO analysis_results
            (video_id, script_id, analysis_type, verdict, strengths,
             weaknesses, recommendations, full_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            video_id, script_id, analysis_type, verdict,
            json.dumps(strengths or []),
            json.dumps(weaknesses or []),
            json.dumps(recommendations or []),
            full_analysis,
        ])

    def get_analyses(self, video_id=None, script_id=None, limit=20):
        """Retrieve past analyses."""
        query = "SELECT * FROM analysis_results WHERE 1=1"
        params = []
        if video_id:
            query += " AND video_id = ?"
            params.append(video_id)
        if script_id:
            query += " AND script_id = ?"
            params.append(script_id)
        query += " ORDER BY analyzed_at DESC LIMIT ?"
        params.append(limit)
        return fetch_all(query, params)
