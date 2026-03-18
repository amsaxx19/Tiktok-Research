"""
TikTok Video Scraper: Fetch video data and metrics from TikTok profile.

Supports multiple methods:
1. TikTok Research API (if you have access)
2. Playwright browser automation (primary method)
3. Manual CSV import (fallback)
"""
import json
import time
import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.database import execute_query, fetch_all, fetch_one, init_db


class TikTokScraper:

    def __init__(self, username=None):
        init_db()
        self.username = username

    # ─── Method 1: Manual Import (most reliable) ───

    def import_from_csv(self, csv_path):
        """
        Import video data from TikTok Analytics CSV export.
        TikTok Creator Studio lets you export your video data.

        Expected CSV columns:
        video_id, url, caption, views, likes, comments, shares, saves, posted_at
        """
        imported = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                video_id = self._upsert_video(
                    tiktok_video_id=row.get("video_id", ""),
                    url=row.get("url", ""),
                    caption=row.get("caption", ""),
                    hashtags=row.get("hashtags", ""),
                    sound_name=row.get("sound_name", ""),
                    duration_seconds=float(row.get("duration", 0)),
                    posted_at=row.get("posted_at", ""),
                )
                self._add_metrics(
                    video_id=video_id,
                    views=int(row.get("views", 0)),
                    likes=int(row.get("likes", 0)),
                    comments=int(row.get("comments", 0)),
                    shares=int(row.get("shares", 0)),
                    saves=int(row.get("saves", 0)),
                )
                imported += 1
        return imported

    def import_from_json(self, json_path):
        """
        Import video data from a JSON file.

        Expected format: list of objects with fields:
        tiktok_video_id, url, caption, hashtags, views, likes, comments, shares, saves, posted_at
        """
        with open(json_path, "r", encoding="utf-8") as f:
            videos = json.load(f)

        imported = 0
        for v in videos:
            video_id = self._upsert_video(
                tiktok_video_id=v.get("tiktok_video_id", v.get("video_id", "")),
                url=v.get("url", ""),
                caption=v.get("caption", ""),
                hashtags=v.get("hashtags", ""),
                sound_name=v.get("sound_name", ""),
                duration_seconds=float(v.get("duration_seconds", v.get("duration", 0))),
                posted_at=v.get("posted_at", ""),
            )
            self._add_metrics(
                video_id=video_id,
                views=int(v.get("views", 0)),
                likes=int(v.get("likes", 0)),
                comments=int(v.get("comments", 0)),
                shares=int(v.get("shares", 0)),
                saves=int(v.get("saves", 0)),
            )
            imported += 1
        return imported

    def manual_add_video(self, tiktok_video_id, url, caption="",
                         hashtags="", sound_name="", duration_seconds=0,
                         posted_at=None, views=0, likes=0, comments=0,
                         shares=0, saves=0, script_id=None):
        """Manually add a single video with its metrics."""
        video_id = self._upsert_video(
            tiktok_video_id=tiktok_video_id,
            url=url,
            caption=caption,
            hashtags=hashtags,
            sound_name=sound_name,
            duration_seconds=duration_seconds,
            posted_at=posted_at or datetime.now().isoformat(),
        )
        if script_id:
            execute_query(
                "UPDATE videos SET script_id = ? WHERE id = ?",
                [script_id, video_id]
            )
        self._add_metrics(video_id, views, likes, comments, shares, saves)
        return video_id

    def update_video_metrics(self, video_db_id, views=0, likes=0,
                             comments=0, shares=0, saves=0):
        """Add a new metrics snapshot for an existing video."""
        self._add_metrics(video_db_id, views, likes, comments, shares, saves)

    # ─── Method 2: Playwright Browser Automation ───

    def scrape_profile_playwright(self, max_videos=30):
        """
        Scrape videos from your TikTok profile using Playwright.
        Requires: pip install playwright && playwright install chromium
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

        videos_data = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            page.goto(f"https://www.tiktok.com/@{self.username}", timeout=30000)
            time.sleep(3)

            # Scroll to load videos
            for _ in range(max_videos // 10):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1.5, 3.0))

            # Extract video links
            video_elements = page.query_selector_all('div[data-e2e="user-post-item"] a')
            urls = []
            for el in video_elements[:max_videos]:
                href = el.get_attribute("href")
                if href and "/video/" in href:
                    urls.append(href)

            # Visit each video page to get metrics
            for url in urls:
                try:
                    page.goto(url, timeout=15000)
                    time.sleep(random.uniform(2, 4))

                    vid_id = url.split("/video/")[-1].split("?")[0]

                    # Try to extract metrics from the page
                    caption_el = page.query_selector('span[data-e2e="browse-video-desc"]')
                    caption = caption_el.inner_text() if caption_el else ""

                    video_data = {
                        "tiktok_video_id": vid_id,
                        "url": url,
                        "caption": caption,
                    }
                    videos_data.append(video_data)
                except Exception:
                    continue

            browser.close()

        # Save to database
        imported = 0
        for v in videos_data:
            self._upsert_video(
                tiktok_video_id=v["tiktok_video_id"],
                url=v["url"],
                caption=v.get("caption", ""),
            )
            imported += 1
        return imported

    # ─── Query Methods ───

    def get_videos(self, days=None, limit=50):
        """Get videos, optionally filtered by recency."""
        query = "SELECT * FROM videos WHERE 1=1"
        params = []
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND posted_at >= ?"
            params.append(cutoff)
        query += " ORDER BY posted_at DESC LIMIT ?"
        params.append(limit)
        return fetch_all(query, params)

    def get_video_with_metrics(self, video_db_id):
        """Get a single video with its latest metrics."""
        return fetch_one("""
            SELECT v.*, vm.views, vm.likes, vm.comments, vm.shares,
                   vm.saves, vm.engagement_rate, vm.scraped_at
            FROM videos v
            LEFT JOIN video_metrics vm ON vm.video_id = v.id
            WHERE v.id = ?
            ORDER BY vm.scraped_at DESC
            LIMIT 1
        """, [video_db_id])

    def get_videos_with_latest_metrics(self, days=None, limit=50):
        """Get all videos with their most recent metrics."""
        query = """
            SELECT v.*, vm.views, vm.likes, vm.comments, vm.shares,
                   vm.saves, vm.engagement_rate, vm.scraped_at
            FROM videos v
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
        query += " ORDER BY v.posted_at DESC LIMIT ?"
        params.append(limit)
        return fetch_all(query, params)

    def get_unlinked_videos(self):
        """Get videos that haven't been linked to a script."""
        return fetch_all("""
            SELECT v.*, vm.views, vm.likes, vm.comments, vm.shares, vm.saves
            FROM videos v
            LEFT JOIN video_metrics vm ON vm.video_id = v.id
            AND vm.scraped_at = (
                SELECT MAX(vm2.scraped_at) FROM video_metrics vm2
                WHERE vm2.video_id = v.id
            )
            WHERE v.script_id IS NULL
            ORDER BY v.posted_at DESC
        """)

    def get_metrics_history(self, video_db_id):
        """Get all metric snapshots for a video (to see growth over time)."""
        return fetch_all("""
            SELECT * FROM video_metrics
            WHERE video_id = ?
            ORDER BY scraped_at ASC
        """, [video_db_id])

    # ─── Internal Helpers ───

    def _upsert_video(self, tiktok_video_id, url="", caption="",
                      hashtags="", sound_name="", duration_seconds=0,
                      posted_at=None):
        """Insert or get existing video, return DB id."""
        existing = fetch_one(
            "SELECT id FROM videos WHERE tiktok_video_id = ?",
            [tiktok_video_id]
        )
        if existing:
            return existing["id"]

        return execute_query("""
            INSERT INTO videos (tiktok_video_id, url, caption, hashtags,
                               sound_name, duration_seconds, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [tiktok_video_id, url, caption, hashtags, sound_name,
              duration_seconds, posted_at])

    def _add_metrics(self, video_id, views=0, likes=0, comments=0,
                     shares=0, saves=0):
        """Add a metrics snapshot."""
        total_interactions = likes + comments + shares + saves
        engagement_rate = (total_interactions / views * 100) if views > 0 else 0.0

        execute_query("""
            INSERT INTO video_metrics (video_id, views, likes, comments,
                                       shares, saves, engagement_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [video_id, views, likes, comments, shares, saves, engagement_rate])
