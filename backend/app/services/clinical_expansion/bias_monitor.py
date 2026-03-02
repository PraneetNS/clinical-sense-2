"""
AI Bias & Drift Monitoring Engine
=================================
Monitoring AI performance, confidence distribution, and potential bias.
Provides aggregated analytics for administrators.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...models import AIEncounter, AIQualityReport, AIUsageMetrics

class BiasMonitor:
    """
    Monitors for model bias or performance drift.
    """
    def __init__(self, db: Session):
        self.db = db

    def generate_bias_report(self) -> Dict[str, Any]:
        """
        Aggregates metrics for administrator review.
        """
        # Confidence score distribution by risk level
        risk_dist = self.db.query(
            AIQualityReport.risk_level, 
            func.avg(AIQualityReport.confidence_score).label("avg_conf"), 
            func.count(AIQualityReport.id).label("total_count")
        ).group_by(AIQualityReport.risk_level).all()

        formatted_risk_dist = [
            {"risk_level": r.risk_level, "avg_confidence": round(r.avg_conf, 2), "total_count": r.total_count}
            for r in risk_dist
        ]

        # Median Latency and Usage across all users
        usage_stats = self.db.query(
            func.avg(AIUsageMetrics.latency_ms).label("avg_latency"),
            func.avg(AIUsageMetrics.tokens_used).label("avg_tokens")
        ).first()

        # Simple bias check: Confidence by model version if multiple exist
        model_version_dist = self.db.query(
            AIEncounter.model_version,
            func.avg(AIQualityReport.confidence_score).label("avg_conf"),
            func.count(AIEncounter.id).label("total_count")
        ).join(AIQualityReport, AIEncounter.id == AIQualityReport.encounter_id)\
         .group_by(AIEncounter.model_version).all()

        formatted_model_dist = [
            {"model": m.model_version or "Unknown", "avg_confidence": round(m.avg_conf, 2), "total_count": m.total_count}
            for m in model_version_dist
        ]

        return {
            "model_performance": formatted_model_dist,
            "risk_distribution": formatted_risk_dist,
            "overall_metrics": {
                "avg_latency_ms": round(usage_stats.avg_latency or 0, 2),
                "avg_tokens": round(usage_stats.avg_tokens or 0, 2)
            }
        }
