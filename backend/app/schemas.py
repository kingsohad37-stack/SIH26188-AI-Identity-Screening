from typing import Any
from pydantic import BaseModel

class AnalysisResponse(BaseModel):
    screening_id: str
    status: str
    document_type: str | None = None
    extracted_data: dict[str, Any] = {}
    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    message: str
