from pydantic import BaseModel, Field


class IncidentExtraction(BaseModel):
    pipeline_name: str = Field(description="Name of the affected pipeline")
    dataset_name: str = Field(description="Name of the affected dataset or table")
    layer: str = Field(description="Affected data layer, for example bronze, silver or gold")
    issue: str = Field(description="Short technical description of the issue")
    severity: str = Field(description="Severity, for example low, medium or high")
    business_impact: str = Field(description="Business impact caused by the incident")


class IncidentResponse(BaseModel):
    incident_summary: str = Field(description="Short summary of the incident")
    business_impact: str = Field(description="Business impact in plain language")
    next_action: str = Field(description="Recommended immediate next action")
    owner_team: str = Field(description="Suggested team that should own the issue")
