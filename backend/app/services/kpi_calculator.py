"""
Service for calculating KPI metrics.
Centralizes all KPI calculation logic for reuse across endpoints.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class KPICalculator:
    """Service for calculating KPI metrics."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_overview_kpis(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        location_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate overview KPIs for dashboard.

        Args:
            from_date: Start date filter
            to_date: End date filter
            location_id: Location filter

        Returns:
            Dictionary with overview KPIs
        """
        # Get sales metrics from vw_tx_cogs
        query = """
            SELECT
                COUNT(*) as total_sales,
                SUM(revenue) as total_revenue,
                SUM(cogs) as total_cogs,
                SUM(gross_profit) as total_gross_profit,
                CASE 
                    WHEN SUM(revenue) > 0 
                    THEN (SUM(gross_profit) / SUM(revenue) * 100)::numeric(5,2)
                    ELSE 0 
                END as gross_margin_pct,
                COUNT(DISTINCT drink_id) as unique_drinks,
                COUNT(DISTINCT term_id) as active_terminals
            FROM vw_tx_cogs
            WHERE 1=1
        """
        
        params = {}
        if from_date:
            query += " AND tx_date >= :from_date"
            params['from_date'] = from_date
        if to_date:
            query += " AND tx_date <= :to_date"
            params['to_date'] = to_date
        if location_id:
            query += " AND location_id = :location_id"
            params['location_id'] = location_id
        
        try:
            result = self.db.execute(text(query), params).fetchone()
            
            # Get variable expenses for same period
            expense_query = """
                SELECT COALESCE(SUM(amount_rub), 0) as total_expenses
                FROM variable_expenses
                WHERE 1=1
            """
            expense_params = {}
            if from_date:
                expense_query += " AND expense_date >= :from_date"
                expense_params['from_date'] = from_date
            if to_date:
                expense_query += " AND expense_date <= :to_date"
                expense_params['to_date'] = to_date
            if location_id:
                expense_query += " AND location_id = :location_id"
                expense_params['location_id'] = location_id
            
            expenses_result = self.db.execute(text(expense_query), expense_params).fetchone()
            total_expenses = float(expenses_result[0]) if expenses_result and expenses_result[0] else 0.0
            
            # Calculate net profit
            total_gross_profit = float(result[3] or 0) if result else 0.0
            total_revenue = float(result[1] or 0) if result else 0.0
            net_profit = total_gross_profit - total_expenses
            net_margin_pct = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0
            
            return {
                "total_sales": result[0] or 0 if result else 0,
                "total_revenue": total_revenue,
                "total_cogs": float(result[2] or 0) if result else 0.0,
                "total_gross_profit": total_gross_profit,
                "gross_margin_pct": float(result[4] or 0) if result else 0.0,
                "unique_drinks": result[5] or 0 if result else 0,
                "active_terminals": result[6] or 0 if result else 0,
                "total_variable_expenses": total_expenses,
                "net_profit": net_profit,
                "net_margin_pct": round(net_margin_pct, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating overview KPIs: {str(e)}")
            raise

    def calculate_daily_kpis(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        location_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate daily sales KPIs.

        Args:
            from_date: Start date filter
            to_date: End date filter
            location_id: Location filter

        Returns:
            List of daily KPI dictionaries
        """
        query = """
            SELECT
                tx_date,
                location_id,
                sales_count,
                revenue,
                cogs,
                gross_profit,
                gross_margin_pct
            FROM vw_kpi_daily
            WHERE 1=1
        """
        
        params = {}
        if from_date:
            query += " AND tx_date >= :from_date"
            params['from_date'] = from_date
        if to_date:
            query += " AND tx_date <= :to_date"
            params['to_date'] = to_date
        if location_id:
            query += " AND location_id = :location_id"
            params['location_id'] = location_id
        
        query += " ORDER BY tx_date DESC"
        
        try:
            results = self.db.execute(text(query), params).fetchall()
            daily_kpis = []
            
            for row in results:
                daily_kpis.append({
                    "date": row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                    "location_id": row[1],
                    "sales_count": row[2] or 0,
                    "revenue": float(row[3] or 0),
                    "cogs": float(row[4] or 0),
                    "gross_profit": float(row[5] or 0),
                    "gross_margin_pct": float(row[6] or 0)
                })
            
            return daily_kpis
        except Exception as e:
            logger.error(f"Error calculating daily KPIs: {str(e)}")
            raise

    def calculate_product_kpis(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        location_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate product-level KPIs.

        Args:
            from_date: Start date filter
            to_date: End date filter
            location_id: Location filter
            limit: Maximum number of products to return

        Returns:
            List of product KPI dictionaries
        """
        query = """
            SELECT
                drink_id,
                drink_name,
                location_id,
                location_name,
                sales_count,
                revenue,
                cogs,
                gross_profit,
                CASE 
                    WHEN revenue > 0 
                    THEN (gross_profit / revenue * 100)::numeric(5,2)
                    ELSE 0 
                END as gross_margin_pct
            FROM vw_kpi_product
            WHERE 1=1
        """
        
        params = {}
        if from_date:
            query += " AND tx_date >= :from_date"
            params['from_date'] = from_date
        if to_date:
            query += " AND tx_date <= :to_date"
            params['to_date'] = to_date
        if location_id:
            query += " AND location_id = :location_id"
            params['location_id'] = location_id
        
        query += " ORDER BY revenue DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            results = self.db.execute(text(query), params).fetchall()
            product_kpis = []
            
            for row in results:
                product_kpis.append({
                    "drink_id": row[0],
                    "drink_name": row[1],
                    "location_id": row[2],
                    "location_name": row[3],
                    "sales_count": row[4] or 0,
                    "revenue": float(row[5] or 0),
                    "cogs": float(row[6] or 0),
                    "gross_profit": float(row[7] or 0),
                    "gross_margin_pct": float(row[8] or 0)
                })
            
            return product_kpis
        except Exception as e:
            logger.error(f"Error calculating product KPIs: {str(e)}")
            raise

    def calculate_sales_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        location_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate sales summary with aggregated metrics.

        Args:
            from_date: Start date filter
            to_date: End date filter
            location_id: Location filter

        Returns:
            Dictionary with sales summary metrics
        """
        overview = self.calculate_overview_kpis(from_date, to_date, location_id)
        daily_kpis = self.calculate_daily_kpis(from_date, to_date, location_id)
        
        # Calculate additional metrics
        avg_daily_revenue = overview["total_revenue"] / len(daily_kpis) if daily_kpis else 0
        avg_daily_sales = overview["total_sales"] / len(daily_kpis) if daily_kpis else 0
        
        return {
            **overview,
            "period_days": len(daily_kpis),
            "avg_daily_revenue": round(avg_daily_revenue, 2),
            "avg_daily_sales": round(avg_daily_sales, 2),
            "daily_breakdown": daily_kpis
        }

    def calculate_margin_analysis(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        location_id: Optional[int] = None,
        min_margin: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate detailed margin analysis by products.

        Args:
            from_date: Start date filter
            to_date: End date filter
            location_id: Location filter
            min_margin: Minimum margin threshold (filters products below this)

        Returns:
            Dictionary with margin analysis
        """
        products = self.calculate_product_kpis(from_date, to_date, location_id)
        
        if min_margin is not None:
            products = [p for p in products if p["gross_margin_pct"] >= min_margin]
        
        # Calculate statistics
        margins = [p["gross_margin_pct"] for p in products if p["gross_margin_pct"] > 0]
        
        margin_stats = {}
        if margins:
            margin_stats = {
                "min": min(margins),
                "max": max(margins),
                "avg": sum(margins) / len(margins),
                "median": sorted(margins)[len(margins) // 2] if margins else 0
            }
        
        # Group by margin ranges
        margin_ranges = {
            "high": [p for p in products if p["gross_margin_pct"] >= 50],
            "medium": [p for p in products if 30 <= p["gross_margin_pct"] < 50],
            "low": [p for p in products if 0 < p["gross_margin_pct"] < 30],
            "negative": [p for p in products if p["gross_margin_pct"] <= 0]
        }
        
        return {
            "total_products": len(products),
            "margin_statistics": margin_stats,
            "by_range": {
                "high": len(margin_ranges["high"]),
                "medium": len(margin_ranges["medium"]),
                "low": len(margin_ranges["low"]),
                "negative": len(margin_ranges["negative"])
            },
            "products": products
        }
