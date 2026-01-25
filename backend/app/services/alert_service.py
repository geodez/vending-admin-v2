"""
Service for generating and managing alerts.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of alerts."""
    LOW_STOCK = "low_stock"
    LOW_MARGIN = "low_margin"
    SYNC_ERROR = "sync_error"
    EXPIRING_STOCK = "expiring_stock"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertService:
    """Service for generating and managing alerts."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_alerts(
        self,
        location_id: Optional[int] = None,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active alerts.

        Args:
            location_id: Filter by location ID
            alert_type: Filter by alert type
            severity: Filter by severity level

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # Get low stock alerts
        if alert_type is None or alert_type == AlertType.LOW_STOCK:
            alerts.extend(self._get_low_stock_alerts(location_id))

        # Get low margin alerts
        if alert_type is None or alert_type == AlertType.LOW_MARGIN:
            alerts.extend(self._get_low_margin_alerts(location_id))

        # Get sync error alerts
        if alert_type is None or alert_type == AlertType.SYNC_ERROR:
            alerts.extend(self._get_sync_error_alerts(location_id))

        # Get expiring stock alerts
        if alert_type is None or alert_type == AlertType.EXPIRING_STOCK:
            alerts.extend(self._get_expiring_stock_alerts(location_id))

        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity.value]

        # Sort by severity (critical first) and then by timestamp
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda x: (severity_order.get(x.get("severity", "info"), 2), x.get("timestamp", "")))

        return alerts

    def _get_low_stock_alerts(self, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get alerts for low stock levels."""
        alerts = []

        query = """
            SELECT
                ingredient_code,
                display_name_ru,
                location_id,
                location_name,
                balance,
                alert_threshold,
                unit,
                alert_days_threshold
            FROM vw_inventory_balance
            WHERE alert_threshold IS NOT NULL 
              AND balance <= alert_threshold
        """
        params = {}
        if location_id:
            query += " AND location_id = :location_id"
            params['location_id'] = location_id

        try:
            results = self.db.execute(text(query), params).fetchall()
            for row in results:
                balance = float(row[4]) if row[4] else 0
                threshold = float(row[5]) if row[5] else 0
                days_left = row[7] if row[7] else None

                # Determine severity based on how low the stock is
                if balance <= threshold * 0.5:
                    severity = AlertSeverity.CRITICAL
                elif balance <= threshold * 0.75:
                    severity = AlertSeverity.WARNING
                else:
                    severity = AlertSeverity.INFO

                alerts.append({
                    "type": AlertType.LOW_STOCK.value,
                    "severity": severity.value,
                    "ingredient_code": row[0],
                    "ingredient_name": row[1],
                    "location_id": row[2],
                    "location_name": row[3],
                    "balance": balance,
                    "threshold": threshold,
                    "unit": row[6],
                    "days_left": days_left,
                    "message": f"Низкий остаток: {row[1]} в {row[3]} ({balance:.2f} {row[6]} <= {threshold:.2f} {row[6]})",
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error getting low stock alerts: {str(e)}")

        return alerts

    def _get_low_margin_alerts(self, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get alerts for products with low margin (< 30%)."""
        alerts = []

        query = """
            SELECT
                drink_id,
                drink_name,
                location_id,
                location_name,
                gross_margin_pct,
                revenue,
                sales_count
            FROM vw_kpi_product
            WHERE gross_margin_pct < 30 AND revenue > 0
        """
        params = {}
        if location_id:
            query += " AND location_id = :location_id"
            params['location_id'] = location_id

        query += " ORDER BY revenue DESC LIMIT 20"

        try:
            results = self.db.execute(text(query), params).fetchall()
            for row in results:
                margin_pct = float(row[4]) if row[4] else 0
                revenue = float(row[5]) if row[5] else 0

                # Determine severity based on margin
                if margin_pct < 10:
                    severity = AlertSeverity.CRITICAL
                elif margin_pct < 20:
                    severity = AlertSeverity.WARNING
                else:
                    severity = AlertSeverity.INFO

                alerts.append({
                    "type": AlertType.LOW_MARGIN.value,
                    "severity": severity.value,
                    "drink_id": row[0],
                    "drink_name": row[1],
                    "location_id": row[2],
                    "location_name": row[3],
                    "margin_pct": margin_pct,
                    "revenue": revenue,
                    "sales_count": int(row[6]) if row[6] else 0,
                    "message": f"Низкая маржа: {row[1]} ({margin_pct:.1f}% маржа, выручка {revenue:.2f} руб.)",
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error getting low margin alerts: {str(e)}")

        return alerts

    def _get_sync_error_alerts(self, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get alerts for sync errors."""
        alerts = []

        query = """
            SELECT
                id,
                run_at,
                status,
                error_message,
                location_id
            FROM sync_runs
            WHERE status = 'error'
              AND run_at >= NOW() - INTERVAL '7 days'
            ORDER BY run_at DESC
            LIMIT 10
        """
        params = {}

        if location_id:
            query = query.replace("WHERE status = 'error'", "WHERE status = 'error' AND location_id = :location_id")
            params['location_id'] = location_id

        try:
            results = self.db.execute(text(query), params).fetchall()
            for row in results:
                run_at = row[1] if isinstance(row[1], str) else row[1].isoformat() if row[1] else None
                error_message = row[3] if row[3] else "Неизвестная ошибка"

                alerts.append({
                    "type": AlertType.SYNC_ERROR.value,
                    "severity": AlertSeverity.CRITICAL.value,
                    "sync_run_id": row[0],
                    "run_at": run_at,
                    "error_message": error_message,
                    "location_id": row[4] if len(row) > 4 else None,
                    "message": f"Ошибка синхронизации: {error_message}",
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error getting sync error alerts: {str(e)}")

        return alerts

    def _get_expiring_stock_alerts(self, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get alerts for expiring stock (based on alert_days_threshold)."""
        alerts = []

        query = """
            SELECT
                ingredient_code,
                display_name_ru,
                location_id,
                location_name,
                balance,
                alert_days_threshold,
                unit,
                expiry_date
            FROM vw_inventory_balance
            WHERE alert_days_threshold IS NOT NULL
              AND expiry_date IS NOT NULL
              AND expiry_date <= CURRENT_DATE + (alert_days_threshold || ' days')::INTERVAL
              AND expiry_date > CURRENT_DATE
        """
        params = {}
        if location_id:
            query += " AND location_id = :location_id"
            params['location_id'] = location_id

        try:
            results = self.db.execute(text(query), params).fetchall()
            for row in results:
                balance = float(row[4]) if row[4] else 0
                days_threshold = int(row[5]) if row[5] else 3
                expiry_date = row[7].isoformat() if hasattr(row[7], 'isoformat') else str(row[7]) if row[7] else None

                # Calculate days until expiry
                if expiry_date:
                    try:
                        if isinstance(expiry_date, str):
                            expiry = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                        else:
                            expiry = expiry_date
                        days_until_expiry = (expiry.date() - date.today()).days
                    except:
                        days_until_expiry = None
                else:
                    days_until_expiry = None

                # Determine severity
                if days_until_expiry is not None:
                    if days_until_expiry <= 1:
                        severity = AlertSeverity.CRITICAL
                    elif days_until_expiry <= days_threshold:
                        severity = AlertSeverity.WARNING
                    else:
                        severity = AlertSeverity.INFO
                else:
                    severity = AlertSeverity.WARNING

                alerts.append({
                    "type": AlertType.EXPIRING_STOCK.value,
                    "severity": severity.value,
                    "ingredient_code": row[0],
                    "ingredient_name": row[1],
                    "location_id": row[2],
                    "location_name": row[3],
                    "balance": balance,
                    "unit": row[6],
                    "expiry_date": expiry_date,
                    "days_until_expiry": days_until_expiry,
                    "message": f"Скоро истекает срок: {row[1]} в {row[3]} (осталось {days_until_expiry} дней)" if days_until_expiry else f"Скоро истекает срок: {row[1]} в {row[3]}",
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error getting expiring stock alerts: {str(e)}")

        return alerts

    def get_alert_summary(self, location_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get summary of alerts by type and severity.

        Args:
            location_id: Filter by location ID

        Returns:
            Dictionary with alert counts by type and severity
        """
        all_alerts = self.get_all_alerts(location_id=location_id)

        summary = {
            "total": len(all_alerts),
            "by_type": {},
            "by_severity": {
                "critical": 0,
                "warning": 0,
                "info": 0
            }
        }

        for alert in all_alerts:
            alert_type = alert.get("type", "unknown")
            severity = alert.get("severity", "info")

            # Count by type
            if alert_type not in summary["by_type"]:
                summary["by_type"][alert_type] = 0
            summary["by_type"][alert_type] += 1

            # Count by severity
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1

        return summary
