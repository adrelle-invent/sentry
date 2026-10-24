from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IssueEvidence(BaseModel):
    log_ids: List[str] = Field(default_factory=list)
    request_ids: List[str] = Field(default_factory=list)

class IssueResponse(BaseModel):
    id: str = Field(..., description="Unique issue identifier following standard: [SEVERITY]-[CATEGORY]-[NUMBER]")
    title: str = Field(..., description="Descriptive title of the issue")
    category: str = Field(..., description="Issue category (DI, CON, FH, OBS, SEC, REL)")
    severity: str = Field(..., description="Issue severity (CRI, MED, LOW)")
    risk_score: float = Field(..., description="Computed risk score from 0.0 to 10.0")
    endpoint: Optional[str] = Field(None, description="Endpoint path where the issue was observed")
    method: Optional[str] = Field(None, description="HTTP method used")
    scenario: str = Field(..., description="Operational scenario description")
    observed_behavior: str = Field(..., description="Observed system behavior")
    root_cause: str = Field(..., description="Root cause analysis")
    business_impact: str = Field(..., description="Potential business impact")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    evidence: IssueEvidence = Field(..., description="Supporting log and request IDs")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the latest event")

    model_config = ConfigDict(from_attributes=True)

class PDFExportRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters to apply (id, severity, category, endpoint)")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="Optional start_date and end_date in ISO format")
    issue_ids: Optional[List[str]] = Field(default=None, description="Optional list of issue IDs to override filters")
