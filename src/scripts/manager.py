"""
Script Manager: CRUD operations for TikTok scripts.
Track scripts, link them to videos, manage versions.
"""
import json
from datetime import datetime
from src.utils.database import execute_query, fetch_all, fetch_one, init_db


class ScriptManager:

    def __init__(self):
        init_db()

    def create_script(self, title, content, hook=None, cta=None, niche=None,
                      script_type="organic", product_id=None, tags=None, notes=None):
        """Create a new script and store it."""
        query = """
            INSERT INTO scripts (title, content, hook, cta, niche, script_type,
                                 product_id, tags, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        tags_str = ",".join(tags) if isinstance(tags, list) else tags
        script_id = execute_query(query, [
            title, content, hook, cta, niche, script_type,
            product_id, tags_str, notes
        ])
        return script_id

    def get_script(self, script_id):
        """Get a script by ID."""
        return fetch_one("SELECT * FROM scripts WHERE id = ?", [script_id])

    def list_scripts(self, status=None, niche=None, script_type=None, limit=50):
        """List scripts with optional filters."""
        query = "SELECT * FROM scripts WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if niche:
            query += " AND niche = ?"
            params.append(niche)
        if script_type:
            query += " AND script_type = ?"
            params.append(script_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return fetch_all(query, params)

    def update_script(self, script_id, **kwargs):
        """Update script fields."""
        allowed = {"title", "content", "hook", "cta", "niche", "script_type",
                    "product_id", "tags", "notes", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        query = f"UPDATE scripts SET {set_clause} WHERE id = ?"
        execute_query(query, list(fields.values()) + [script_id])

    def mark_as_posted(self, script_id):
        """Mark script as posted (recorded + uploaded)."""
        self.update_script(script_id, status="posted")

    def create_revision(self, script_id, new_content, notes=None):
        """Create a new version of an existing script."""
        original = self.get_script(script_id)
        if not original:
            raise ValueError(f"Script {script_id} not found")
        new_id = self.create_script(
            title=f"{original['title']} (v{original['version'] + 1})",
            content=new_content,
            hook=original["hook"],
            cta=original["cta"],
            niche=original["niche"],
            script_type=original["script_type"],
            product_id=original["product_id"],
            tags=original["tags"],
            notes=notes or original["notes"],
        )
        execute_query(
            "UPDATE scripts SET version = ?, parent_script_id = ? WHERE id = ?",
            [original["version"] + 1, script_id, new_id]
        )
        return new_id

    def link_to_video(self, script_id, video_id):
        """Link a script to a posted video."""
        execute_query(
            "UPDATE videos SET script_id = ? WHERE id = ?",
            [script_id, video_id]
        )
        self.mark_as_posted(script_id)

    def search_scripts(self, keyword):
        """Search scripts by keyword in title or content."""
        query = """
            SELECT * FROM scripts
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY created_at DESC
        """
        pattern = f"%{keyword}%"
        return fetch_all(query, [pattern, pattern, pattern])

    def get_script_performance(self, script_id):
        """Get the video performance linked to a script."""
        return fetch_all("""
            SELECT v.*, vm.views, vm.likes, vm.comments, vm.shares,
                   vm.saves, vm.engagement_rate, vm.scraped_at
            FROM videos v
            JOIN video_metrics vm ON vm.video_id = v.id
            WHERE v.script_id = ?
            ORDER BY vm.scraped_at DESC
        """, [script_id])

    def get_unlinked_scripts(self):
        """Get scripts that haven't been linked to any video yet."""
        return fetch_all("""
            SELECT s.* FROM scripts s
            LEFT JOIN videos v ON v.script_id = s.id
            WHERE v.id IS NULL AND s.status != 'archived'
            ORDER BY s.created_at DESC
        """)

    def get_top_performing_scripts(self, limit=10):
        """Get scripts sorted by their video's best performance."""
        return fetch_all("""
            SELECT s.*, MAX(vm.views) as best_views,
                   MAX(vm.engagement_rate) as best_engagement
            FROM scripts s
            JOIN videos v ON v.script_id = s.id
            JOIN video_metrics vm ON vm.video_id = v.id
            GROUP BY s.id
            ORDER BY best_views DESC
            LIMIT ?
        """, [limit])

    def get_scripts_by_verdict(self, verdict):
        """Get scripts filtered by analysis verdict (viral/good/average/flop)."""
        return fetch_all("""
            SELECT s.*, ar.verdict, ar.strengths, ar.weaknesses
            FROM scripts s
            JOIN analysis_results ar ON ar.script_id = s.id
            WHERE ar.verdict = ?
            ORDER BY s.created_at DESC
        """, [verdict])
