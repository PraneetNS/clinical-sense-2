from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ...db.session import get_db
from ...api.deps import require_role
from ...models import AIEncounter, AIUsageMetrics, AIQualityReport, User

router = APIRouter()

@router.get("/ai-analytics")
async def get_ai_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["SUPER_ADMIN"]))
):
    """
    Returns aggregated AI performance metrics for administrators.
    Optimised into a few efficient SQL queries.
    """
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # 1. Aggregate Usage & Latency
    usage_stats = db.query(
        func.avg(AIUsageMetrics.latency_ms).label("avg_latency"),
        func.avg(AIUsageMetrics.tokens_used).label("avg_tokens"),
        func.count(AIUsageMetrics.id).label("total_encounters"),
        func.avg(AIUsageMetrics.edit_distance_score).label("avg_edit_distance")
    ).filter(AIUsageMetrics.created_at >= thirty_days_ago).first()

    # 2. Aggregate Quality Scores
    quality_stats = db.query(
        func.avg(AIQualityReport.confidence_score).label("avg_confidence"),
        func.avg(AIQualityReport.compliance_score).label("avg_compliance")
    ).filter(AIQualityReport.created_at >= thirty_days_ago).first()

    # 3. Acceptance Rate
    confirmed_count = db.query(func.count(AIEncounter.id)).filter(
        AIEncounter.is_confirmed == True,
        AIEncounter.created_at >= thirty_days_ago
    ).scalar()

    total_count = usage_stats.total_encounters or 1
    acceptance_rate = (confirmed_count / total_count) if total_count > 0 else 0

    return {
        "period": "last_30_days",
        "metrics": {
            "avg_latency_ms": round(usage_stats.avg_latency or 0, 2),
            "avg_tokens": round(usage_stats.avg_tokens or 0, 2),
            "total_encounters": total_count,
            "acceptance_rate": round(acceptance_rate, 2),
            "avg_edit_distance": round(usage_stats.avg_edit_distance or 0, 2),
            "avg_confidence_score": round(quality_stats.avg_confidence or 0, 2),
            "avg_compliance_score": round(quality_stats.avg_compliance or 0, 2),
        }
    }
@router.get("/bias-report")
async def get_bias_report(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["SUPER_ADMIN"]))
):
    """
    Returns AI bias and drift monitoring report.
    Checks for performance variations across models and risk levels.
    """
    from ...services.clinical_expansion.bias_monitor import BiasMonitor
    monitor = BiasMonitor(db)
    return monitor.generate_bias_report()
