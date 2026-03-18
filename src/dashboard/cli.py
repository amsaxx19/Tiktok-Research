"""
CLI Dashboard: Main interface for the TikTok Script Tracking System.
Run with: python -m src.dashboard.cli
"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError:
    print("Missing dependencies. Run: pip install click rich")
    sys.exit(1)

from src.utils.database import init_db
from src.scripts.manager import ScriptManager
from src.scraper.tiktok_scraper import TikTokScraper
from src.analytics.analyzer import AnalyticsEngine
from src.affiliate.tracker import AffiliateTracker
from src.product_detection.detector import ProductDetector

console = Console()
detector = ProductDetector()
scripts = ScriptManager()
scraper = TikTokScraper()
analytics = AnalyticsEngine()
affiliate = AffiliateTracker()


@click.group()
def cli():
    """TikTok Script Tracking System - Track, Analyze, Optimize."""
    init_db()


# ═══════════════════════════════════════════════════
#  SCRIPT COMMANDS
# ═══════════════════════════════════════════════════

@cli.group()
def script():
    """Manage your TikTok scripts."""
    pass


@script.command("add")
@click.option("--title", "-t", required=True, help="Script title")
@click.option("--content", "-c", required=True, help="Script content (or @file.txt)")
@click.option("--hook", "-h", default=None, help="Opening hook line")
@click.option("--cta", default=None, help="Call to action")
@click.option("--niche", "-n", default=None, help="Niche/category")
@click.option("--type", "script_type", default="organic", help="organic/affiliate/collab")
@click.option("--tags", default=None, help="Comma-separated tags")
@click.option("--notes", default=None, help="Personal notes")
def script_add(title, content, hook, cta, niche, script_type, tags, notes):
    """Add a new script."""
    # Support reading content from file
    if content.startswith("@"):
        filepath = content[1:]
        with open(filepath, "r") as f:
            content = f.read()

    script_id = scripts.create_script(
        title=title, content=content, hook=hook, cta=cta,
        niche=niche, script_type=script_type, tags=tags, notes=notes,
    )
    console.print(f"[green]Script #{script_id} created: {title}[/green]")


@script.command("list")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--niche", "-n", default=None, help="Filter by niche")
@click.option("--limit", "-l", default=20, help="Max results")
def script_list(status, niche, limit):
    """List all scripts."""
    results = scripts.list_scripts(status=status, niche=niche, limit=limit)
    if not results:
        console.print("[yellow]No scripts found.[/yellow]")
        return

    table = Table(title="Your Scripts", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Niche", style="magenta")
    table.add_column("Type", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    for s in results:
        table.add_row(
            str(s["id"]), s["title"], s.get("niche", "-"),
            s.get("script_type", "-"), s.get("status", "-"),
            str(s.get("created_at", ""))[:10],
        )
    console.print(table)


@script.command("show")
@click.argument("script_id", type=int)
def script_show(script_id):
    """Show a script's full content and performance."""
    s = scripts.get_script(script_id)
    if not s:
        console.print(f"[red]Script #{script_id} not found[/red]")
        return

    console.print(Panel(
        f"[bold]{s['title']}[/bold]\n\n"
        f"[dim]Niche:[/dim] {s.get('niche', '-')} | "
        f"[dim]Type:[/dim] {s.get('script_type', '-')} | "
        f"[dim]Status:[/dim] {s.get('status', '-')}\n\n"
        f"[yellow]Hook:[/yellow] {s.get('hook', '-')}\n\n"
        f"{s['content']}\n\n"
        f"[yellow]CTA:[/yellow] {s.get('cta', '-')}\n"
        f"[dim]Tags:[/dim] {s.get('tags', '-')}",
        title=f"Script #{script_id}",
        border_style="blue",
    ))

    # Show linked video performance
    perf = scripts.get_script_performance(script_id)
    if perf:
        console.print("\n[bold]Video Performance:[/bold]")
        for p in perf:
            verdict = analytics.classify_video(p.get("views", 0), p.get("engagement_rate", 0))
            color = {"viral": "green", "good": "blue", "average": "yellow", "flop": "red"}[verdict]
            console.print(
                f"  [{color}]{verdict.upper()}[/{color}] "
                f"Views: {p.get('views', 0):,} | "
                f"Likes: {p.get('likes', 0):,} | "
                f"Engagement: {p.get('engagement_rate', 0):.1f}%"
            )


@script.command("search")
@click.argument("keyword")
def script_search(keyword):
    """Search scripts by keyword."""
    results = scripts.search_scripts(keyword)
    if not results:
        console.print(f"[yellow]No scripts matching '{keyword}'[/yellow]")
        return
    for s in results:
        console.print(f"  [cyan]#{s['id']}[/cyan] {s['title']} [{s.get('status', '-')}]")


@script.command("link")
@click.argument("script_id", type=int)
@click.argument("video_id", type=int)
def script_link(script_id, video_id):
    """Link a script to a video."""
    scripts.link_to_video(script_id, video_id)
    console.print(f"[green]Linked script #{script_id} to video #{video_id}[/green]")


@script.command("top")
@click.option("--limit", "-l", default=10, help="Number of results")
def script_top(limit):
    """Show top performing scripts."""
    results = scripts.get_top_performing_scripts(limit=limit)
    if not results:
        console.print("[yellow]No performance data yet. Link scripts to videos first.[/yellow]")
        return

    table = Table(title="Top Performing Scripts", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Best Views", style="green", justify="right")
    table.add_column("Engagement", style="blue", justify="right")

    for s in results:
        table.add_row(
            str(s["id"]), s["title"],
            f"{s.get('best_views', 0):,}",
            f"{s.get('best_engagement', 0):.1f}%",
        )
    console.print(table)


@script.command("unlinked")
def script_unlinked():
    """Show scripts not yet linked to any video."""
    results = scripts.get_unlinked_scripts()
    if not results:
        console.print("[green]All scripts are linked to videos![/green]")
        return
    console.print(f"[yellow]{len(results)} unlinked scripts:[/yellow]")
    for s in results:
        console.print(f"  [cyan]#{s['id']}[/cyan] {s['title']} [{s.get('status', '-')}]")


# ═══════════════════════════════════════════════════
#  VIDEO COMMANDS
# ═══════════════════════════════════════════════════

@cli.group()
def video():
    """Manage and scrape TikTok videos."""
    pass


@video.command("import-csv")
@click.argument("csv_path")
def video_import_csv(csv_path):
    """Import videos from CSV file."""
    count = scraper.import_from_csv(csv_path)
    console.print(f"[green]Imported {count} videos from CSV[/green]")


@video.command("import-json")
@click.argument("json_path")
def video_import_json(json_path):
    """Import videos from JSON file."""
    count = scraper.import_from_json(json_path)
    console.print(f"[green]Imported {count} videos from JSON[/green]")


@video.command("add")
@click.option("--vid", required=True, help="TikTok video ID")
@click.option("--url", required=True, help="Video URL")
@click.option("--caption", default="", help="Video caption")
@click.option("--views", default=0, type=int, help="Current views")
@click.option("--likes", default=0, type=int, help="Current likes")
@click.option("--comments", default=0, type=int, help="Current comments")
@click.option("--shares", default=0, type=int, help="Current shares")
@click.option("--saves", default=0, type=int, help="Current saves")
@click.option("--script-id", default=None, type=int, help="Link to script ID")
def video_add(vid, url, caption, views, likes, comments, shares, saves, script_id):
    """Manually add a video with metrics."""
    video_id = scraper.manual_add_video(
        tiktok_video_id=vid, url=url, caption=caption,
        views=views, likes=likes, comments=comments,
        shares=shares, saves=saves, script_id=script_id,
    )
    console.print(f"[green]Video #{video_id} added[/green]")


@video.command("update")
@click.argument("video_db_id", type=int)
@click.option("--views", default=0, type=int)
@click.option("--likes", default=0, type=int)
@click.option("--comments", default=0, type=int)
@click.option("--shares", default=0, type=int)
@click.option("--saves", default=0, type=int)
def video_update(video_db_id, views, likes, comments, shares, saves):
    """Update metrics for a video (adds new snapshot)."""
    scraper.update_video_metrics(video_db_id, views, likes, comments, shares, saves)
    console.print(f"[green]Metrics updated for video #{video_db_id}[/green]")


@video.command("list")
@click.option("--days", "-d", default=None, type=int, help="Last N days")
@click.option("--limit", "-l", default=20, help="Max results")
def video_list(days, limit):
    """List videos with latest metrics."""
    results = scraper.get_videos_with_latest_metrics(days=days, limit=limit)
    if not results:
        console.print("[yellow]No videos found.[/yellow]")
        return

    table = Table(title=f"Videos{f' (last {days} days)' if days else ''}", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Caption", max_width=40)
    table.add_column("Views", justify="right", style="green")
    table.add_column("Likes", justify="right")
    table.add_column("Eng%", justify="right", style="blue")
    table.add_column("Script", style="magenta", width=8)
    table.add_column("Posted", style="dim", width=10)

    for v in results:
        views = v.get("views", 0) or 0
        verdict = analytics.classify_video(views, v.get("engagement_rate", 0) or 0)
        view_color = {"viral": "bold green", "good": "green", "average": "yellow", "flop": "red"}[verdict]

        table.add_row(
            str(v["id"]),
            (v.get("caption", "") or "")[:40],
            f"[{view_color}]{views:,}[/{view_color}]",
            f"{v.get('likes', 0) or 0:,}",
            f"{v.get('engagement_rate', 0) or 0:.1f}%",
            str(v.get("script_id", "-") or "-"),
            str(v.get("posted_at", ""))[:10],
        )
    console.print(table)


@video.command("unlinked")
def video_unlinked():
    """Show videos not linked to any script."""
    results = scraper.get_unlinked_videos()
    if not results:
        console.print("[green]All videos are linked to scripts![/green]")
        return
    console.print(f"[yellow]{len(results)} unlinked videos:[/yellow]")
    for v in results:
        console.print(
            f"  [cyan]#{v['id']}[/cyan] {(v.get('caption', '') or '')[:50]} "
            f"({v.get('views', 0) or 0:,} views)"
        )


@video.command("scrape")
@click.option("--username", "-u", required=True, help="TikTok username")
@click.option("--max", "max_videos", default=30, type=int, help="Max videos to scrape")
def video_scrape(username, max_videos):
    """Scrape videos from a TikTok profile (requires Playwright)."""
    s = TikTokScraper(username=username)
    try:
        count = s.scrape_profile_playwright(max_videos=max_videos)
        console.print(f"[green]Scraped {count} videos from @{username}[/green]")
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Scraping failed: {e}[/red]")


# ═══════════════════════════════════════════════════
#  ANALYTICS COMMANDS
# ═══════════════════════════════════════════════════

@cli.group()
def analyze():
    """Analyze your content performance."""
    pass


@analyze.command("summary")
@click.option("--days", "-d", default=None, type=int, help="Last N days")
def analyze_summary(days):
    """Show performance summary."""
    results = analytics.get_performance_summary(days=days)
    if not results:
        console.print("[yellow]No data to analyze.[/yellow]")
        return

    # Count verdicts
    verdicts = {"viral": 0, "good": 0, "average": 0, "flop": 0}
    total_views = 0
    for v in results:
        views = v.get("views", 0) or 0
        total_views += views
        verdict = analytics.classify_video(views, v.get("engagement_rate", 0) or 0)
        verdicts[verdict] += 1

    period = f"Last {days} days" if days else "All time"
    console.print(Panel(
        f"[bold]Total Videos:[/bold] {len(results)}\n"
        f"[bold]Total Views:[/bold] {total_views:,}\n\n"
        f"[green]Viral (100k+):[/green] {verdicts['viral']}\n"
        f"[blue]Good (10k+):[/blue] {verdicts['good']}\n"
        f"[yellow]Average (1k+):[/yellow] {verdicts['average']}\n"
        f"[red]Flop (<1k):[/red] {verdicts['flop']}",
        title=f"Performance Summary — {period}",
        border_style="blue",
    ))


@analyze.command("niches")
def analyze_niches():
    """Compare performance across niches."""
    results = analytics.get_niche_performance()
    if not results:
        console.print("[yellow]No niche data yet. Add niches to your scripts.[/yellow]")
        return

    table = Table(title="Niche Performance", box=box.ROUNDED)
    table.add_column("Niche", style="bold")
    table.add_column("Videos", justify="right")
    table.add_column("Avg Views", justify="right", style="green")
    table.add_column("Avg Engagement", justify="right", style="blue")
    table.add_column("Best Video", justify="right", style="magenta")
    table.add_column("Total Views", justify="right")

    for n in results:
        table.add_row(
            n["niche"],
            str(n["total_videos"]),
            f"{n['avg_views']:,.0f}",
            f"{n['avg_engagement']:.1f}%",
            f"{n['best_views']:,}",
            f"{n['total_views']:,}",
        )
    console.print(table)


@analyze.command("hooks")
def analyze_hooks():
    """See which hooks perform best."""
    results = analytics.get_hook_analysis()
    if not results:
        console.print("[yellow]No hook data. Add hooks to your scripts.[/yellow]")
        return

    table = Table(title="Hook Performance", box=box.ROUNDED)
    table.add_column("Hook", style="bold", max_width=50)
    table.add_column("Used", justify="right")
    table.add_column("Avg Views", justify="right", style="green")
    table.add_column("Avg Engagement", justify="right", style="blue")

    for h in results:
        table.add_row(
            h["hook"][:50],
            str(h["times_used"]),
            f"{h['avg_views']:,.0f}",
            f"{h['avg_engagement']:.1f}%",
        )
    console.print(table)


@analyze.command("prompt")
@click.option("--days", "-d", default=7, type=int, help="Period to analyze")
def analyze_prompt(days):
    """Generate an AI analysis prompt with all your data."""
    prompt = analytics.generate_analysis_prompt(days=days)
    console.print(Panel(prompt, title="Copy this prompt to Claude", border_style="green"))


@analyze.command("time")
def analyze_time():
    """Analyze best posting times."""
    results = analytics.get_posting_time_analysis()
    if not results:
        console.print("[yellow]No posting time data available.[/yellow]")
        return

    table = Table(title="Posting Time Analysis", box=box.ROUNDED)
    table.add_column("Time Slot", style="bold")
    table.add_column("Videos", justify="right")
    table.add_column("Avg Views", justify="right", style="green")
    table.add_column("Avg Engagement", justify="right", style="blue")

    for r in results:
        table.add_row(
            r["time_slot"], str(r["total_videos"]),
            f"{r['avg_views']:,.0f}", f"{r['avg_engagement']:.1f}%",
        )
    console.print(table)


# ═══════════════════════════════════════════════════
#  AFFILIATE COMMANDS
# ═══════════════════════════════════════════════════

@cli.group()
def product():
    """Manage affiliate products and sales."""
    pass


@product.command("add")
@click.option("--name", "-n", required=True, help="Product name")
@click.option("--category", "-c", default=None, help="Product category")
@click.option("--price", "-p", default=0, type=float, help="Product price")
@click.option("--commission", default=10.0, type=float, help="Commission rate %")
@click.option("--link", default=None, help="Affiliate link")
@click.option("--source", default="tiktok_shop", help="Source platform")
def product_add(name, category, price, commission, link, source):
    """Add a new affiliate product."""
    pid = affiliate.add_product(
        name=name, category=category, price=price,
        commission_rate=commission, affiliate_link=link, source=source,
    )
    console.print(f"[green]Product #{pid} added: {name}[/green]")


@product.command("list")
@click.option("--category", "-c", default=None)
@click.option("--limit", "-l", default=20)
def product_list(category, limit):
    """List all products."""
    results = affiliate.list_products(category=category, limit=limit)
    if not results:
        console.print("[yellow]No products yet.[/yellow]")
        return

    table = Table(title="Affiliate Products", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Name", style="bold")
    table.add_column("Category", style="magenta")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Commission", justify="right", style="blue")
    table.add_column("Source")

    for p in results:
        table.add_row(
            str(p["id"]), p["name"], p.get("category", "-"),
            f"Rp{p.get('price', 0):,.0f}",
            f"{p.get('commission_rate', 0):.0f}%",
            p.get("source", "-"),
        )
    console.print(table)


@product.command("sale")
@click.option("--product-id", "-p", required=True, type=int)
@click.option("--video-id", "-v", default=None, type=int)
@click.option("--units", "-u", default=1, type=int)
@click.option("--revenue", "-r", required=True, type=float)
def product_sale(product_id, video_id, units, revenue):
    """Record a product sale."""
    affiliate.record_sale(product_id=product_id, video_id=video_id,
                          units_sold=units, revenue=revenue)
    console.print(f"[green]Sale recorded: {units} units, Rp{revenue:,.0f}[/green]")


@product.command("top")
@click.option("--days", "-d", default=None, type=int)
@click.option("--limit", "-l", default=10)
def product_top(days, limit):
    """Show top selling products."""
    results = affiliate.get_top_products(days=days, limit=limit)
    if not results:
        console.print("[yellow]No sales data yet.[/yellow]")
        return

    table = Table(title="Top Products", box=box.ROUNDED)
    table.add_column("Name", style="bold")
    table.add_column("Units", justify="right")
    table.add_column("Revenue", justify="right", style="green")
    table.add_column("Commission", justify="right", style="blue")
    table.add_column("Videos", justify="right")

    for p in results:
        table.add_row(
            p["name"], str(p["total_units"]),
            f"Rp{p['total_revenue']:,.0f}",
            f"Rp{p['total_commission']:,.0f}",
            str(p["videos_promoting"]),
        )
    console.print(table)


@product.command("earnings")
@click.option("--days", "-d", default=None, type=int)
def product_earnings(days):
    """Show earnings summary."""
    result = affiliate.get_earnings_summary(days=days)
    if not result or not result.get("total_revenue"):
        console.print("[yellow]No earnings data yet.[/yellow]")
        return

    period = f"Last {days} days" if days else "All time"
    console.print(Panel(
        f"[bold]Products Sold:[/bold] {result['products_sold']}\n"
        f"[bold]Videos with Sales:[/bold] {result['videos_with_sales']}\n"
        f"[bold]Total Units:[/bold] {result['total_units']:,}\n"
        f"[bold green]Total Revenue:[/bold green] Rp{result['total_revenue']:,.0f}\n"
        f"[bold blue]Total Commission:[/bold blue] Rp{result['total_commission']:,.0f}",
        title=f"Earnings Summary — {period}",
        border_style="green",
    ))


# ═══════════════════════════════════════════════════
#  PRODUCT + SCRIPT GENERATION (NO API KEY NEEDED)
# ═══════════════════════════════════════════════════

@cli.group()
def generate():
    """Generate scripts via Claude Code chat (no API key needed)."""
    pass


@generate.command("context")
def generate_context():
    """Show your performance context (paste this into Claude Code chat)."""
    context = detector.get_context_for_chat()
    if context.strip():
        console.print(Panel(context, title="Your Performance Context", border_style="cyan"))
    else:
        console.print("[yellow]No performance data yet. Add scripts and videos first.[/yellow]")


@generate.command("prompt")
@click.option("--name", "-n", required=True, help="Product name")
@click.option("--desc", "-d", default=None, help="Product description")
@click.option("--category", "-c", default=None, help="Product category")
@click.option("--style", "-s", default="storytelling",
              type=click.Choice(["storytelling", "review", "tutorial",
                                 "comparison", "unboxing", "problem_solution"]))
@click.option("--duration", default=30, type=int, help="Target duration in seconds")
def generate_prompt(name, desc, category, style, duration):
    """Generate a prompt for Claude Code chat to create a script."""
    prompt = detector.generate_prompt_for_product(
        product_name=name, product_description=desc,
        category=category, style=style, duration_target=duration,
    )
    console.print(Panel(
        prompt,
        title="Copy this prompt to Claude Code chat (or just tell Claude directly!)",
        border_style="green",
    ))


@generate.command("save")
@click.option("--product-name", "-n", required=True, help="Product name")
@click.option("--category", "-c", default=None, help="Category")
@click.option("--price", "-p", default=0, type=float, help="Price")
@click.option("--commission", default=10.0, type=float, help="Commission %")
@click.option("--link", default=None, help="Affiliate link")
@click.option("--source", default="tiktok_shop", help="Source platform")
@click.option("--script-title", "-t", default=None, help="Script title")
@click.option("--script-file", "-f", required=True, help="Path to script text file")
@click.option("--hook", default=None, help="Hook line")
@click.option("--cta", default=None, help="CTA line")
@click.option("--tags", default=None, help="Comma-separated tags")
def generate_save(product_name, category, price, commission, link, source,
                  script_title, script_file, hook, cta, tags):
    """Save a product + script that Claude generated in chat."""
    with open(script_file, "r") as f:
        script_content = f.read()

    product_id, script_id = detector.save_product_and_script(
        product_name=product_name, category=category,
        price=price, commission_rate=commission,
        affiliate_link=link, source=source,
        script_title=script_title, script_content=script_content,
        hook=hook, cta=cta, tags=tags,
    )
    console.print(
        f"[green]Saved! Product #{product_id} + Script #{script_id}[/green]\n"
        f"[dim]Now link the script to a video after posting: "
        f"python main.py script link {script_id} <video_id>[/dim]"
    )


# ═══════════════════════════════════════════════════
#  DASHBOARD OVERVIEW
# ═══════════════════════════════════════════════════

@cli.command("dashboard")
@click.option("--days", "-d", default=7, type=int)
def dashboard(days):
    """Show full dashboard overview."""
    console.print(f"\n[bold]TikTok Script Tracker — Last {days} Days[/bold]\n")

    # Video stats
    videos = analytics.get_performance_summary(days=days)
    verdicts = {"viral": 0, "good": 0, "average": 0, "flop": 0}
    total_views = 0
    for v in videos:
        views = v.get("views", 0) or 0
        total_views += views
        verdict = analytics.classify_video(views, v.get("engagement_rate", 0) or 0)
        verdicts[verdict] += 1

    console.print(Panel(
        f"Videos: {len(videos)} | Views: {total_views:,}\n"
        f"[green]Viral: {verdicts['viral']}[/green] | "
        f"[blue]Good: {verdicts['good']}[/blue] | "
        f"[yellow]Avg: {verdicts['average']}[/yellow] | "
        f"[red]Flop: {verdicts['flop']}[/red]",
        title="Content Performance",
    ))

    # Top 5 videos
    if videos[:5]:
        table = Table(title="Top 5 Videos", box=box.SIMPLE)
        table.add_column("Caption", max_width=40)
        table.add_column("Views", justify="right", style="green")
        table.add_column("Engagement", justify="right", style="blue")
        table.add_column("Script", style="magenta")
        for v in videos[:5]:
            table.add_row(
                (v.get("caption", "") or "")[:40],
                f"{v.get('views', 0) or 0:,}",
                f"{v.get('engagement_rate', 0) or 0:.1f}%",
                v.get("script_title", "-") or "-",
            )
        console.print(table)

    # Earnings
    earnings = affiliate.get_earnings_summary(days=days)
    if earnings and earnings.get("total_revenue"):
        console.print(Panel(
            f"Revenue: Rp{earnings['total_revenue']:,.0f} | "
            f"Commission: Rp{earnings['total_commission']:,.0f} | "
            f"Units: {earnings['total_units']:,}",
            title="Affiliate Earnings",
        ))

    # Unlinked items
    unlinked_scripts = scripts.get_unlinked_scripts()
    unlinked_videos = scraper.get_unlinked_videos()
    if unlinked_scripts or unlinked_videos:
        console.print(Panel(
            f"[yellow]Unlinked scripts: {len(unlinked_scripts)}[/yellow]\n"
            f"[yellow]Unlinked videos: {len(unlinked_videos)}[/yellow]\n"
            f"[dim]Use 'script link <script_id> <video_id>' to connect them[/dim]",
            title="Action Required",
            border_style="yellow",
        ))


if __name__ == "__main__":
    cli()
