"""
Product Detection + Auto Script Generation.

Upload a product image → Claude detects the product →
auto-generates a TikTok script optimized for affiliate sales.
"""
import os
import json
import base64
from pathlib import Path

try:
    import anthropic
except ImportError:
    anthropic = None

from src.utils.database import init_db
from src.scripts.manager import ScriptManager
from src.affiliate.tracker import AffiliateTracker
from src.analytics.analyzer import AnalyticsEngine


class ProductDetector:

    def __init__(self, api_key=None):
        init_db()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.script_manager = ScriptManager()
        self.affiliate_tracker = AffiliateTracker()
        self.analytics = AnalyticsEngine()

        if anthropic and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def detect_product(self, image_path):
        """
        Detect product from an image using Claude's vision.
        Returns product info dict.
        """
        if not self.client:
            raise RuntimeError(
                "Anthropic client not initialized. Set ANTHROPIC_API_KEY env var "
                "or pass api_key to constructor."
            )

        image_data = self._load_image(image_path)
        ext = Path(image_path).suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Analyze this product image and return a JSON object with:
{
    "name": "product name",
    "category": "product category (e.g. skincare, tech, fashion, food, home)",
    "description": "brief product description",
    "key_features": ["feature1", "feature2", "feature3"],
    "target_audience": "who would buy this",
    "price_range": "estimated price range",
    "selling_points": ["point1", "point2", "point3"]
}
Return ONLY the JSON, no other text.""",
                    },
                ],
            }],
        )

        try:
            result = json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError):
            result = {
                "name": "Unknown Product",
                "category": "general",
                "description": response.content[0].text if response.content else "",
                "key_features": [],
                "target_audience": "general",
                "price_range": "unknown",
                "selling_points": [],
            }

        return result

    def generate_script_for_product(self, product_info, style="storytelling",
                                     duration_target=30, use_top_patterns=True):
        """
        Generate a TikTok affiliate script based on product info.
        Optionally uses patterns from your top-performing scripts.
        """
        if not self.client:
            raise RuntimeError("Anthropic client not initialized.")

        # Get patterns from top scripts if requested
        pattern_context = ""
        if use_top_patterns:
            top_scripts = self.script_manager.get_top_performing_scripts(limit=5)
            if top_scripts:
                pattern_context = "\n## Your Top Performing Script Patterns:\n"
                for s in top_scripts:
                    pattern_context += f"""
- **{s['title']}** ({s.get('best_views', 0):,} views):
  Hook: {s.get('hook', 'N/A')}
  Content preview: {s['content'][:200]}...
"""

        # Get niche performance data
        niche_data = self.analytics.get_niche_performance()
        niche_context = ""
        if niche_data:
            niche_context = "\n## Your Niche Performance Data:\n"
            for n in niche_data:
                niche_context += (
                    f"- {n['niche']}: avg {n['avg_views']:.0f} views, "
                    f"{n['avg_engagement']:.1f}% engagement\n"
                )

        style_guides = {
            "storytelling": "Use a narrative format - start with a problem, introduce the product as the solution, show results",
            "review": "Direct product review style - honest first impression, key features, pros/cons, verdict",
            "tutorial": "How-to/tutorial format - show how to use the product step by step",
            "comparison": "Compare with alternatives, highlight why this product wins",
            "unboxing": "Unboxing/first impression style - build excitement, reveal, react",
            "problem_solution": "Start with a relatable problem, then reveal the product as the perfect solution",
        }
        style_guide = style_guides.get(style, style_guides["storytelling"])

        prompt = f"""Create a TikTok script for this affiliate product.

## Product Info:
{json.dumps(product_info, indent=2)}

## Script Requirements:
- Duration: ~{duration_target} seconds
- Style: {style} — {style_guide}
- Must have a STRONG hook in the first 2-3 seconds
- Include a clear CTA (call to action) at the end
- Natural, conversational tone (not salesy)
- Include "[ACTION]" cues for what to show on screen
{pattern_context}
{niche_context}

## Output Format (return ONLY this JSON):
{{
    "title": "script title",
    "hook": "the opening hook line (first 2-3 seconds)",
    "content": "full script with [ACTION] cues",
    "cta": "the call to action at the end",
    "hashtag_suggestions": ["hashtag1", "hashtag2", "hashtag3"],
    "caption_suggestion": "suggested TikTok caption",
    "estimated_duration_seconds": {duration_target},
    "tips": ["filming tip 1", "tip 2"]
}}"""

        response = self.client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            result = json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError):
            # If Claude doesn't return clean JSON, wrap the response
            text = response.content[0].text if response.content else ""
            result = {
                "title": product_info.get("name", "Untitled"),
                "hook": "",
                "content": text,
                "cta": "",
                "hashtag_suggestions": [],
                "caption_suggestion": "",
                "estimated_duration_seconds": duration_target,
                "tips": [],
            }

        return result

    def detect_and_generate(self, image_path, style="storytelling",
                            duration_target=30, save=True,
                            price=0, commission_rate=10.0,
                            affiliate_link=None, source="tiktok_shop"):
        """
        Full pipeline: detect product from image → generate script → save both.
        Returns (product_id, script_id, product_info, script_data).
        """
        # Step 1: Detect product
        product_info = self.detect_product(image_path)

        # Step 2: Save product to DB
        product_id = self.affiliate_tracker.add_product(
            name=product_info["name"],
            category=product_info.get("category"),
            image_path=str(image_path),
            description=product_info.get("description"),
            price=price,
            commission_rate=commission_rate,
            affiliate_link=affiliate_link,
            source=source,
        )

        # Step 3: Generate script
        script_data = self.generate_script_for_product(
            product_info, style=style, duration_target=duration_target
        )

        # Step 4: Save script
        script_id = None
        if save:
            script_id = self.script_manager.create_script(
                title=script_data.get("title", product_info["name"]),
                content=script_data.get("content", ""),
                hook=script_data.get("hook"),
                cta=script_data.get("cta"),
                niche=product_info.get("category"),
                script_type="affiliate",
                product_id=product_id,
                tags=script_data.get("hashtag_suggestions"),
            )

        return product_id, script_id, product_info, script_data

    def batch_generate(self, image_paths, **kwargs):
        """Process multiple product images at once."""
        results = []
        for path in image_paths:
            try:
                result = self.detect_and_generate(path, **kwargs)
                results.append({"image": str(path), "success": True, "data": result})
            except Exception as e:
                results.append({"image": str(path), "success": False, "error": str(e)})
        return results

    def _load_image(self, image_path):
        """Load and base64 encode an image."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
