"""
Product Detection + Script Generation — NO API KEY NEEDED.

This module works with Claude Code chat directly:
1. CLI command exports your data context (top scripts, niche performance)
2. You paste product info or share image in Claude Code chat
3. Claude (this chat) generates the script
4. CLI command saves the generated script to the database

No API calls. Everything goes through your Claude Code subscription.
"""
import json
from pathlib import Path

from src.utils.database import init_db
from src.scripts.manager import ScriptManager
from src.affiliate.tracker import AffiliateTracker
from src.analytics.analyzer import AnalyticsEngine


class ProductDetector:

    def __init__(self):
        init_db()
        self.script_manager = ScriptManager()
        self.affiliate_tracker = AffiliateTracker()
        self.analytics = AnalyticsEngine()

    def get_context_for_chat(self):
        """
        Generate context data that you paste into Claude Code chat.
        This gives Claude all the info needed to generate optimized scripts.
        """
        # Get top performing script patterns
        pattern_context = ""
        top_scripts = self.script_manager.get_top_performing_scripts(limit=5)
        if top_scripts:
            pattern_context = "## Your Top Performing Script Patterns:\n"
            for s in top_scripts:
                pattern_context += (
                    f"- **{s['title']}** ({s.get('best_views', 0):,} views, "
                    f"{s.get('best_engagement', 0):.1f}% engagement):\n"
                    f"  Hook: {s.get('hook', 'N/A')}\n"
                    f"  Content: {s['content'][:200]}...\n\n"
                )

        # Get niche performance
        niche_context = ""
        niche_data = self.analytics.get_niche_performance()
        if niche_data:
            niche_context = "## Your Niche Performance:\n"
            for n in niche_data:
                niche_context += (
                    f"- {n['niche']}: avg {n['avg_views']:.0f} views, "
                    f"{n['avg_engagement']:.1f}% engagement, "
                    f"{n['total_videos']} videos\n"
                )

        # Get hook analysis
        hook_context = ""
        hook_data = self.analytics.get_hook_analysis()
        if hook_data:
            hook_context = "## Your Best Performing Hooks:\n"
            for h in hook_data[:5]:
                hook_context += (
                    f"- \"{h['hook']}\" → avg {h['avg_views']:,.0f} views, "
                    f"{h['avg_engagement']:.1f}% engagement\n"
                )

        return f"""# Your TikTok Performance Context

{pattern_context}
{niche_context}
{hook_context}

Use this data to generate scripts that match my best-performing patterns."""

    def generate_prompt_for_product(self, product_name, product_description=None,
                                     category=None, style="storytelling",
                                     duration_target=30):
        """
        Generate a complete prompt to paste into Claude Code chat
        for script generation. No API needed.
        """
        context = self.get_context_for_chat()

        style_guides = {
            "storytelling": "Narrative format - problem → product as solution → results",
            "review": "Honest review - first impression, features, pros/cons, verdict",
            "tutorial": "How-to format - step by step usage",
            "comparison": "Compare with alternatives, highlight why this wins",
            "unboxing": "Unboxing style - excitement, reveal, reaction",
            "problem_solution": "Relatable problem → product as perfect solution",
        }
        style_guide = style_guides.get(style, style_guides["storytelling"])

        prompt = f"""Buatin TikTok script untuk produk affiliate ini.

## Product:
- Name: {product_name}
- Category: {category or 'general'}
- Description: {product_description or 'N/A'}

## Requirements:
- Duration: ~{duration_target} detik
- Style: {style} — {style_guide}
- Hook KUAT di 2-3 detik pertama
- CTA jelas di akhir
- Tone natural, conversational (jangan salesy)
- Kasih [ACTION] cues buat apa yang ditampilin di layar

{context}

## Format Output:
Kasih gue output dalam format ini:
- Title:
- Hook:
- Script: (full script dengan [ACTION] cues)
- CTA:
- Hashtags:
- Caption suggestion:
- Tips filming:"""

        return prompt

    def save_product_and_script(self, product_name, category=None,
                                 image_path=None, description=None,
                                 price=0, commission_rate=10.0,
                                 affiliate_link=None, source="tiktok_shop",
                                 script_title=None, script_content="",
                                 hook=None, cta=None, tags=None):
        """
        Save a product and its script to the database.
        Call this AFTER Claude generates the script in chat.
        """
        # Save product
        product_id = self.affiliate_tracker.add_product(
            name=product_name,
            category=category,
            image_path=str(image_path) if image_path else None,
            description=description,
            price=price,
            commission_rate=commission_rate,
            affiliate_link=affiliate_link,
            source=source,
        )

        # Save script
        script_id = self.script_manager.create_script(
            title=script_title or product_name,
            content=script_content,
            hook=hook,
            cta=cta,
            niche=category,
            script_type="affiliate",
            product_id=product_id,
            tags=tags,
        )

        return product_id, script_id
