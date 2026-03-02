"""
Clinical Workflow Automation Engine
===================================
Automatically staging tasks and workflow objects based on AI suggestions.
Integrates with existing Task and AIEncounter models.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta
from ...models import Task

class WorkflowAutomationEngine:
    """
    Automates clinical task staging based on AI recommendations.
    """
    def __init__(self, db: Any):
        self.db = db

    def stage_tasks(
        self, 
        encounter_id: int, 
        patient_id: int, 
        user_id: int, 
        follow_up_recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Creates Task staging objects for confirmation.
        These are NOT yet promoted to live clinical tasks.
        Uses the existing Task model logic but flagged as 'staging'.
        """
        staged_tasks = []
        
        for recommendation in follow_up_recommendations:
            rec_text = recommendation.get("recommendation", "")
            rec_type = recommendation.get("follow_up_type", "General")
            urgency = recommendation.get("urgency", "routine")
            suggested_days = recommendation.get("suggested_days", 7) or 7

            # Prepare data compatible with Task creation logic
            priority = "High" if urgency == "stat" else ("Medium" if urgency == "urgent" else "Low")
            due_date = datetime.utcnow() + timedelta(days=suggested_days)

            staged_tasks.append({
                "patient_id": patient_id,
                "assigned_to_id": user_id,
                "description": f"[AI Proposed Task] {rec_text}",
                "priority": priority,
                "category": rec_type,
                "is_auto_generated": True,
                "status": "Staging", # New status for unconfirmed tasks
                "due_date": due_date.isoformat(),
            })

            # We don't save yet; they are returned for AIQualityReport persistence
            # so they can be shown to the clinician for confirmation in the UI.

        return staged_tasks
