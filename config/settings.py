"""
Configuration settings for TikTok Script Tracking System.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = DATA_DIR / "scripts"
VIDEOS_DIR = DATA_DIR / "videos"
PRODUCTS_DIR = DATA_DIR / "products"
EXPORTS_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "tracking.db"

# TikTok settings
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "")
TIKTOK_SECUID = os.getenv("TIKTOK_SECUID", "")

# Anthropic API for script generation
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Scraping settings
SCRAPE_DELAY_MIN = 2  # seconds between requests
SCRAPE_DELAY_MAX = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Analytics thresholds
VIRAL_VIEWS_THRESHOLD = 100_000
GOOD_VIEWS_THRESHOLD = 10_000
LOW_VIEWS_THRESHOLD = 1_000

# Engagement rate benchmarks (%)
EXCELLENT_ENGAGEMENT = 10.0
GOOD_ENGAGEMENT = 5.0
AVERAGE_ENGAGEMENT = 2.0

# Affiliate tracking
AFFILIATE_COMMISSION_DEFAULT = 10.0  # default % commission
