"""
Affiliate Product Tracker: Track products, sales, and commissions.
Links products → scripts → videos → sales data.
"""
import json
from datetime import datetime, timedelta
from src.utils.database import execute_query, fetch_all, fetch_one, init_db


class AffiliateTracker:

    def __init__(self):
        init_db()

    # ─── Product Management ───

    def add_product(self, name, category=None, image_path=None,
                    description=None, price=0, commission_rate=10.0,
                    affiliate_link=None, source="tiktok_shop"):
        """Add a new affiliate product."""
        return execute_query("""
            INSERT INTO products (name, category, image_path, description,
                                  price, commission_rate, affiliate_link, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [name, category, image_path, description, price,
              commission_rate, affiliate_link, source])

    def get_product(self, product_id):
        return fetch_one("SELECT * FROM products WHERE id = ?", [product_id])

    def list_products(self, status="active", category=None, limit=50):
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY added_at DESC LIMIT ?"
        params.append(limit)
        return fetch_all(query, params)

    def update_product(self, product_id, **kwargs):
        allowed = {"name", "category", "image_path", "description", "price",
                    "commission_rate", "affiliate_link", "source", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        query = f"UPDATE products SET {set_clause} WHERE id = ?"
        execute_query(query, list(fields.values()) + [product_id])

    # ─── Sales Tracking ───

    def record_sale(self, product_id, video_id=None, units_sold=0,
                    revenue=0, period_start=None, period_end=None):
        """Record sales data for a product (optionally linked to a video)."""
        product = self.get_product(product_id)
        commission = revenue * (product["commission_rate"] / 100) if product else 0

        return execute_query("""
            INSERT INTO product_sales (product_id, video_id, units_sold,
                                       revenue, commission_earned,
                                       period_start, period_end)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [product_id, video_id, units_sold, revenue, commission,
              period_start, period_end])

    def get_product_sales(self, product_id, days=None):
        """Get sales history for a product."""
        query = """
            SELECT ps.*, v.tiktok_video_id, v.caption, v.url
            FROM product_sales ps
            LEFT JOIN videos v ON v.id = ps.video_id
            WHERE ps.product_id = ?
        """
        params = [product_id]
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND ps.recorded_at >= ?"
            params.append(cutoff)
        query += " ORDER BY ps.recorded_at DESC"
        return fetch_all(query, params)

    # ─── Analytics ───

    def get_top_products(self, days=None, limit=10):
        """Get top-selling products."""
        query = """
            SELECT p.*, SUM(ps.units_sold) as total_units,
                   SUM(ps.revenue) as total_revenue,
                   SUM(ps.commission_earned) as total_commission,
                   COUNT(DISTINCT ps.video_id) as videos_promoting
            FROM products p
            JOIN product_sales ps ON ps.product_id = p.id
            WHERE 1=1
        """
        params = []
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND ps.recorded_at >= ?"
            params.append(cutoff)
        query += " GROUP BY p.id ORDER BY total_revenue DESC LIMIT ?"
        params.append(limit)
        return fetch_all(query, params)

    def get_video_sales_performance(self, days=None):
        """See which videos drove the most sales."""
        query = """
            SELECT v.id, v.tiktok_video_id, v.caption, v.url,
                   p.name as product_name,
                   ps.units_sold, ps.revenue, ps.commission_earned,
                   vm.views, vm.engagement_rate,
                   CASE WHEN vm.views > 0
                        THEN CAST(ps.units_sold AS REAL) / vm.views * 100
                        ELSE 0 END as conversion_rate
            FROM product_sales ps
            JOIN videos v ON v.id = ps.video_id
            JOIN products p ON p.id = ps.product_id
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
            query += " AND ps.recorded_at >= ?"
            params.append(cutoff)
        query += " ORDER BY ps.revenue DESC"
        return fetch_all(query, params)

    def get_category_performance(self, days=None):
        """Performance breakdown by product category."""
        query = """
            SELECT p.category,
                   COUNT(DISTINCT p.id) as products,
                   SUM(ps.units_sold) as total_units,
                   SUM(ps.revenue) as total_revenue,
                   SUM(ps.commission_earned) as total_commission,
                   AVG(CASE WHEN vm.views > 0
                        THEN CAST(ps.units_sold AS REAL) / vm.views * 100
                        ELSE 0 END) as avg_conversion_rate
            FROM products p
            JOIN product_sales ps ON ps.product_id = p.id
            LEFT JOIN videos v ON v.id = ps.video_id
            LEFT JOIN video_metrics vm ON vm.video_id = v.id
            WHERE p.category IS NOT NULL
        """
        params = []
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND ps.recorded_at >= ?"
            params.append(cutoff)
        query += " GROUP BY p.category ORDER BY total_revenue DESC"
        return fetch_all(query, params)

    def get_earnings_summary(self, days=None):
        """Get total earnings summary."""
        query = """
            SELECT
                COUNT(DISTINCT ps.product_id) as products_sold,
                COUNT(DISTINCT ps.video_id) as videos_with_sales,
                SUM(ps.units_sold) as total_units,
                SUM(ps.revenue) as total_revenue,
                SUM(ps.commission_earned) as total_commission
            FROM product_sales ps
            WHERE 1=1
        """
        params = []
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND ps.recorded_at >= ?"
            params.append(cutoff)
        return fetch_one(query, params)

    def get_product_video_matrix(self):
        """Matrix of which products were promoted in which videos."""
        return fetch_all("""
            SELECT p.name as product, v.tiktok_video_id as video,
                   v.caption, ps.units_sold, ps.revenue,
                   vm.views, vm.engagement_rate
            FROM product_sales ps
            JOIN products p ON p.id = ps.product_id
            JOIN videos v ON v.id = ps.video_id
            LEFT JOIN video_metrics vm ON vm.video_id = v.id
            AND vm.scraped_at = (
                SELECT MAX(vm2.scraped_at) FROM video_metrics vm2
                WHERE vm2.video_id = v.id
            )
            ORDER BY p.name, ps.revenue DESC
        """)
