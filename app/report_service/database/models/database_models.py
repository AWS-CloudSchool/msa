from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from report_service.database.core.database import Base

class UserAnalysisJob(Base):
    __tablename__ = "user_analysis_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # 'youtube', 'document'
    status = Column(String(20), default='processing')  # 'processing', 'completed', 'failed'
    input_data = Column(JSONB)
    result_s3_key = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계
    reports = relationship("UserReport", back_populates="job")
    audio_files = relationship("UserAudioFile", back_populates="job")

class UserReport(Base):
    __tablename__ = "user_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("user_analysis_jobs.id"))
    user_id = Column(String(255), nullable=False, index=True)
    title = Column(String(500))
    s3_key = Column(String(500))
    file_type = Column(String(10))  # 'json', 'txt', 'pdf'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    job = relationship("UserAnalysisJob", back_populates="reports")

class UserAudioFile(Base):
    __tablename__ = "user_audio_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("user_analysis_jobs.id"))
    user_id = Column(String(255), nullable=False, index=True)
    s3_key = Column(String(500))
    duration = Column(Integer)  # 재생 시간(초)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    job = relationship("UserAnalysisJob", back_populates="audio_files")