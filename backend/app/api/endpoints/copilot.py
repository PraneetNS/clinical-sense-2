from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
from ...services.ai.ai_service import AIService
from ...core.logging import logger

router = APIRouter()

@router.websocket("/ws/copilot")
async def copilot_endpoint(websocket: WebSocket):
    """
    Real-time AI Clinical Copilot WebSocket.
    Streams suggestions as the doctor types.
    """
    await websocket.accept()
    service = AIService()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            partial_text = data
            try:
                # If frontend sends JSON with more context
                json_data = json.loads(data)
                if "text" in json_data:
                    partial_text = json_data["text"]
            except:
                pass
            
            # meaningful length check
            if len(partial_text) < 10:
                continue

            # Get AI suggestions
            suggestions = await service.get_copilot_suggestion(partial_text)
            
            # Add mandatory safety disclaimer
            suggestions["disclaimer"] = "AI-generated suggestion. Clinical validation required."
            
            await websocket.send_json(suggestions)
            
    except WebSocketDisconnect:
        logger.info("Copilot WebSocket disconnected")
    except Exception as e:
        logger.error(f"Copilot WebSocket error: {e}")
        try:
            await websocket.close() 
        except:
            pass
