"""
SQLite database layer for the Script Tracking System.
All data (scripts, videos, products, analytics) stored in one DB.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "tracking.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        -- Scripts table: stores every script you create
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            hook TEXT,                          -- opening hook line
            cta TEXT,                           -- call to action
            niche TEXT,                         -- e.g. 'skincare', 'tech', 'fashion'
            script_type TEXT DEFAULT 'organic',  -- 'organic', 'affiliate', 'collab'
            product_id INTEGER,                 -- linked product if affiliate
            tags TEXT,                          -- comma-separated tags
            notes TEXT,                         -- your personal notes
            version INTEGER DEFAULT 1,
            parent_script_id INTEGER,           -- if this is a revision of another script
            status TEXT DEFAULT 'draft',        -- 'draft', 'recorded', 'posted', 'archived'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (parent_script_id) REFERENCES scripts(id)
        );

        -- Videos table: tracks every TikTok video posted
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tiktok_video_id TEXT UNIQUE,         -- TikTok's video ID
            url TEXT,
            script_id INTEGER,                   -- which script was used
            caption TEXT,
            hashtags TEXT,
            sound_name TEXT,
            duration_seconds REAL,
            posted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (script_id) REFERENCES scripts(id)
        );

        -- Video metrics: snapshots of video performance over time
        CREATE TABLE IF NOT EXISTS video_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        -- Products table: affiliate products
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            image_path TEXT,                    -- local path to product image
            description TEXT,
            price REAL,
            commission_rate REAL DEFAULT 10.0,
            affiliate_link TEXT,
            source TEXT,                        -- 'tiktok_shop', 'shopee', 'tokopedia', etc.
            status TEXT DEFAULT 'active',       -- 'active', 'discontinued', 'out_of_stock'
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Product sales tracking
        CREATE TABLE IF NOT EXISTS product_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            video_id INTEGER,
            units_sold INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0.0,
            commission_earned REAL DEFAULT 0.0,
            period_start DATE,
            period_end DATE,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        -- Analysis results: stores AI analysis of why videos performed well/poorly
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            script_id INTEGER,
            analysis_type TEXT,                 -- 'viral_analysis', 'comparison', 'trend'
            verdict TEXT,                       -- 'viral', 'good', 'average', 'flop'
            strengths TEXT,                     -- JSON array of strengths
            weaknesses TEXT,                    -- JSON array of weaknesses
            recommendations TEXT,               -- JSON array of recommendations
            full_analysis TEXT,                 -- full AI analysis text
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id),
            FOREIGN KEY (script_id) REFERENCES scripts(id)
        );

        -- Create indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_videos_script ON videos(script_id);
        CREATE INDEX IF NOT EXISTS idx_videos_posted ON videos(posted_at);
        CREATE INDEX IF NOT EXISTS idx_metrics_video ON video_metrics(video_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_scraped ON video_metrics(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_sales_product ON product_sales(product_id);
        CREATE INDEX IF NOT EXISTS idx_sales_video ON product_sales(video_id);
        CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(status);
        CREATE INDEX IF NOT EXISTS idx_scripts_niche ON scripts(niche);
    """)
    conn.commit()
    conn.close()


def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.execute(query, params or [])
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def fetch_all(query, params=None):
    conn = get_connection()
    rows = conn.execute(query, params or []).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(query, params=None):
    conn = get_connection()
    row = conn.execute(query, params or []).fetchone()
    conn.close()
    return dict(row) if row else None
