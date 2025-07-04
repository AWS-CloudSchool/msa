from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class YouTubeReporterRequest(BaseModel):
    """Request model for YouTube Reporter analysis"""
    youtube_url: str = Field(..., description="YouTube video URL to analyze")


class YouTubeReporterResponse(BaseModel):
    """Response model for YouTube Reporter analysis"""
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    estimated_time: Optional[str] = Field(None, description="Estimated duration")


class VisualizationData(BaseModel):
    """Model for visualization data"""
    type: str = Field(..., description="Visualization type (chart, network, flow, table)")
    config: Optional[Dict[str, Any]] = Field(None, description="Chart.js config")
    data: Optional[Dict[str, Any]] = Field(None, description="vis.js/ReactFlow data")
    options: Optional[Dict[str, Any]] = Field(None, description="Visualization options")
    headers: Optional[List[str]] = Field(None, description="Table headers")
    rows: Optional[List[List[Any]]] = Field(None, description="Table rows")
    styling: Optional[Dict[str, Any]] = Field(None, description="Table styling")


class ReportSection(BaseModel):
    """Model for each report section"""
    id: str = Field(..., description="Section ID")
    title: str = Field(..., description="Section title")
    type: str = Field(..., description="Section type (text, visualization)")

    content: Optional[str] = Field(None, description="Text content")
    level: Optional[int] = Field(None, description="Title level (1: main, 2: sub, 3: sub-sub)")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Section keywords")

    visualization_type: Optional[str] = Field(None, description="Visualization type")
    data: Optional[Union[VisualizationData, Dict[str, Any]]] = Field(None, description="Visualization data")
    insight: Optional[str] = Field(None, description="Visualization insight")
    purpose: Optional[str] = Field(None, description="Purpose of the visualization")
    user_benefit: Optional[str] = Field(None, description="Benefit for the user")
    error: Optional[str] = Field(None, description="Error message")


class YouTubeReporterResult(BaseModel):
    """Final result model for YouTube Reporter"""
    success: bool = Field(..., description="Whether analysis succeeded")
    title: str = Field(..., description="Report title")
    summary: str = Field(..., description="Brief summary")
    sections: List[ReportSection] = Field(..., description="Report sections")
    statistics: Dict[str, int] = Field(..., description="Statistical info")
    process_info: Dict[str, Any] = Field(..., description="Processing info")
    s3_info: Optional[Dict[str, Any]] = Field(None, description="S3 storage info")
    created_at: Optional[datetime] = Field(None, description="Creation time")


class JobProgressResponse(BaseModel):
    """Job progress response model"""
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    created_at: str = Field(..., description="Job start time")
    completed_at: Optional[str] = Field(None, description="Job completion time")
    input_data: Dict[str, Any] = Field(..., description="Input data")


class JobListResponse(BaseModel):
    """Job list response model"""
    jobs: List[Dict[str, Any]] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    features: Dict[str, bool] = Field(..., description="Supported features")
    supported_visualizations: List[str] = Field(..., description="Supported visualization types")


class ChartVisualization(BaseModel):
    """Chart.js visualization model"""
    type: str = Field("chart", description="Visualization type")
    chart_type: str = Field(..., description="Chart type (bar, line, pie, radar, scatter)")
    data: Dict[str, Any] = Field(..., description="Chart.js data")
    options: Dict[str, Any] = Field(..., description="Chart.js options")


class NetworkVisualization(BaseModel):
    """vis.js network visualization model"""
    type: str = Field("network", description="Visualization type")
    nodes: List[Dict[str, Any]] = Field(..., description="Network nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Network edges")
    options: Dict[str, Any] = Field(..., description="vis.js options")


class FlowVisualization(BaseModel):
    """ReactFlow visualization model"""
    type: str = Field("flow", description="Visualization type")
    nodes: List[Dict[str, Any]] = Field(..., description="Flow nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Flow edges")
    options: Dict[str, Any] = Field(..., description="ReactFlow options")


class TableVisualization(BaseModel):
    """Table visualization model"""
    type: str = Field("table", description="Visualization type")
    headers: List[str] = Field(..., description="Table headers")
    rows: List[List[Any]] = Field(..., description="Table rows")
    styling: Optional[Dict[str, Any]] = Field(None, description="Table styling")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error info")
    job_id: Optional[str] = Field(None, description="Associated job ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp of error")
