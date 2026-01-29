from sqlalchemy.orm import Session
from ...db import session as db_session
from ...models import ClinicalNote, AuditLog, User, NoteVersion
from ...schemas.notes import NoteCreateRequest, NoteUpdateRequest
from ...services.ai.ai_service import AIService
from ...services.embedding_service import embedding_service
from ...services.safety_service import safety_service
import json
import numpy as np

ai_service = AIService()

class NoteService:
    @staticmethod
    async def create_and_structure_note(db: Session, user_id: int, note_in: NoteCreateRequest):
        from fastapi.concurrency import run_in_threadpool
        
        # 0. Idempotency Check
        if note_in.idempotency_key:
            existing_note = db.query(ClinicalNote).filter(
                ClinicalNote.idempotency_key == note_in.idempotency_key,
                ClinicalNote.user_id == user_id
            ).first()
            if existing_note:
                return existing_note

        # 1. Safety Check
        is_safe, violations = safety_service.validate_content(note_in.raw_content)
        if not is_safe:
             raise ValueError(f"Safety Violation: {'; '.join(violations)}")
        
        try:
            # 2. Generate structure using AI
            structured_data = await ai_service.structure_clinical_note(note_in.raw_content, note_in.note_type)
            
            # 3. Generate embedding (CPU bound)
            embedding = await run_in_threadpool(embedding_service.generate_embedding, f"{note_in.title} {note_in.raw_content}")
            
            # 4. Store in DB
            db_note = ClinicalNote(
                raw_content=note_in.raw_content,
                structured_content=json.dumps(structured_data),
                title=note_in.title,
                user_id=user_id,
                status="draft",
                note_type=note_in.note_type,
                patient_id=note_in.patient_id,
                embedding=embedding,
                idempotency_key=note_in.idempotency_key
            )
            db.add(db_note)
            db.flush() 
            
            # 5. Audit Log
            audit = AuditLog(
                user_id=user_id,
                note_id=db_note.id,
                action="structure",
                details="AI restructuring performed"
            )
            db.add(audit)
            db.commit()
            return db_note
            
        except Exception:
            db.rollback()
            raise

    # ... (skipping retrieve methods which are fine) ...

    @staticmethod
    def get_user_notes(db: Session, user_id: int, search: str = None):
        query = db.query(ClinicalNote).filter(
            ClinicalNote.user_id == user_id,
            ClinicalNote.is_deleted == False
        )
        if search:
            query = query.filter(ClinicalNote.title.ilike(f"%{search}%"))
        return query.order_by(ClinicalNote.created_at.desc()).all()

    @staticmethod
    def get_note_by_id(db: Session, note_id: int, user_id: int):
        return db.query(ClinicalNote).filter(
            ClinicalNote.id == note_id, 
            ClinicalNote.user_id == user_id,
            ClinicalNote.is_deleted == False
        ).first()

    @staticmethod
    def soft_delete_note(db: Session, note_id: int, user_id: int):
        import datetime
        db_note = NoteService.get_note_by_id(db, note_id, user_id)
        if not db_note:
            return False
        
        try:
            db_note.is_deleted = True
            db_note.deleted_at = datetime.datetime.utcnow()
            
            # Audit Log for Deletion
            audit = AuditLog(
                user_id=user_id,
                note_id=db_note.id,
                action="delete",
                details="User soft-deleted note"
            )
            db.add(audit)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def update_note(db: Session, note_id: int, user_id: int, note_in: NoteUpdateRequest):
        db_note = NoteService.get_note_by_id(db, note_id, user_id)
        if not db_note:
            return None
        
        update_data = note_in.dict(exclude_unset=True)
        
        # Safety Check
        if "raw_content" in update_data:
            is_safe, violations = safety_service.validate_content(update_data["raw_content"])
            if not is_safe:
                raise ValueError(f"Safety Violation: {'; '.join(violations)}")
        
        if "structured_content" in update_data:
            content_str = json.dumps(update_data["structured_content"])
            is_safe, violations = safety_service.validate_content(content_str)
            if not is_safe:
                 raise ValueError(f"Safety Violation in structured content: {'; '.join(violations)}")
        
        try:
            # Save Version
            if "structured_content" in update_data or "raw_content" in update_data:
                version = NoteVersion(
                    note_id=db_note.id,
                    structured_content=db_note.structured_content,
                    raw_content=db_note.raw_content,
                    created_by=user_id
                )
                db.add(version)
            
            if "structured_content" in update_data:
                if not isinstance(update_data["structured_content"], str):
                     update_data["structured_content"] = json.dumps(update_data["structured_content"])
                
                # Audit manual edit
                audit = AuditLog(user_id=user_id, note_id=db_note.id, action="edit", details="User modified structured content")
                db.add(audit)

            for field, value in update_data.items():
                setattr(db_note, field, value)
                
            db.commit()
            db.refresh(db_note)
            return db_note
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def semantic_search(db: Session, user_id: int, query: str, limit: int = 5):
        query_embedding_json = embedding_service.generate_embedding(query)
        if not query_embedding_json:
            return []
            
        params_vec = np.array(json.loads(query_embedding_json))
        
        # Fetch all notes that have embeddings
        notes = db.query(ClinicalNote).filter(
            ClinicalNote.user_id == user_id, 
            ClinicalNote.is_deleted == False,
            ClinicalNote.embedding.isnot(None)
        ).all()
        
        results = []
        for note in notes:
            try:
                note_vec = np.array(json.loads(note.embedding))
                # Cosine Similarity
                norm_p = np.linalg.norm(params_vec)
                norm_n = np.linalg.norm(note_vec)
                if norm_p > 0 and norm_n > 0:
                    similarity = np.dot(params_vec, note_vec) / (norm_p * norm_n)
                    if similarity > 0.3: # Threshold
                        results.append((note, similarity))
            except Exception:
                continue
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    @staticmethod
    def get_patient_timeline(db: Session, patient_id: int, skip: int = 0, limit: int = 100):
        return db.query(ClinicalNote).filter(
            ClinicalNote.patient_id == patient_id,
            ClinicalNote.is_deleted == False
        ).order_by(ClinicalNote.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_note_history(db: Session, note_id: int, user_id: int):
        # Verify access
        note = NoteService.get_note_by_id(db, note_id, user_id)
        if not note: 
            return []
        return db.query(NoteVersion).filter(NoteVersion.note_id == note_id).order_by(NoteVersion.created_at.desc()).all()
