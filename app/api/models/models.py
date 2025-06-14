"""
API data models.

This module defines Pydantic models for request/response data validation and serialization.
"""

from typing import List, Dict, Union
from pydantic import BaseModel, HttpUrl, Field


class GetCVEmbeddingsRequest(BaseModel):
    """
    Request model for CV embeddings.
    """

    user_id: str = Field(..., description="User ID")


class PostCVEmbeddingsRequest(BaseModel):
    """
    Request model for CV embeddings.
    """

    cv_storage_url: str = Field(..., description="URL to the CV document in storage")
    user_id: str = Field(..., description="User ID")

    class Config:
        """
        Configuration for the PostCVEmbeddingsRequest model with example data.
        """

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "cv_storage_url": "https://storage.googleapis.com/main-storage-hireon/user_cv/fake_cv.pdf",
                "user_id": "123",
            }
        }


class PostCVEmbeddingsResponse(BaseModel):
    """
    Response model for CV embeddings containing embeddings and metadata.
    """

    embeddings: List[float] = Field(..., description="List of embeddings")
    metrics: Dict[str, float] = Field(..., description="Metrics")


class EmbeddingQueryRequest(BaseModel):
    """
    Request model for embedding query.
    """

    embeddings: List[float] = Field(..., description="List of embeddings")


class EmbeddingQueryResponse(BaseModel):
    """
    Response model for embedding query.
    """

    results: List[Dict[str, float]] = Field(..., description="List of results")


class CVJobAnalysisResponse(BaseModel):
    """
    Response model for CV job analysis containing relevance scores and improvement suggestions.
    """

    cv_relevance_score: int = Field(
        ..., description="Score indicating relevance of CV to job (0-100)"
    )
    skill_identification_dict: Dict[str, int] = Field(
        ..., description="Dictionary of skills with scores (0-100)"
    )
    areas_for_improvement: List[str] = Field(
        ..., description="Areas for improvement in CV"
    )
    analysis_explanation: str = Field(..., description="Analysis explanation")
    suggestions: List[str] = Field(
        ..., description="Personalized suggestions for CV improvement"
    )
    processing_time_seconds: float = Field(
        ..., description="Time taken to process request in seconds"
    )
    model: str = Field(..., description="AI model used for analysis")


class CoverLetterResponse(BaseModel):
    """
    Response model for cover letter generation containing access URLs and processing metadata.
    """

    pdf_url: HttpUrl = Field(..., description="Public URL to access the generated PDF")
    pdf_cloud_path: str = Field(..., description="Cloud storage path to the PDF file")
    processing_time_seconds: float = Field(
        ..., description="Time taken to process request in seconds"
    )
    model: str = Field(..., description="AI model used for generation")


class CoverLetterJobDetails(BaseModel):
    """
    Job details model containing position information and requirements for cover letter generation.
    """

    url: str
    company_name: str
    job_position: str
    working_location: str
    company_location: str
    min_experience: str
    job_desc_list: List[str]
    job_qualification_list: List[str]


class CoverLetterGeneratorRequest(BaseModel):
    """
    Request model for cover letter generation.
    """

    cv_url: str
    job_details: CoverLetterJobDetails
    current_date: str
    spesific_request: str

    class Config:
        """
        Configuration for the CoverLetterGeneratorRequest model with example data.
        """

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "cv_url": "https://storage.googleapis.com/main-storage-hireon/user_cv/fake_cv.pdf",
                "current_date": "2025-05-25",
                "spesific_request": "Use English language in the cover letter.",
                "job_details": {
                    "url": "https://dealls.com/loker/data-scientist-33~dexagroup",
                    "company_name": "Dexa Group",
                    "job_position": "Data Scientist",
                    "working_location": "Jakarta",
                    "company_location": "Jakarta",
                    "min_experience": "Min. 1 years of experience",
                    "job_desc_list": [
                        "Processing and analyzing various types of data or raw information to discover patterns, gather insights, and achieve business objectives.",
                        "Build predictive analytics and optimization models to drive actionable insights that improve business performance or related key metrics.",
                    ],
                    "job_qualification_list": [
                        "Bachelor in Mathematics, Statistics, or Information Technology from a top university.",
                        "Minimum of 1 year of working or internship experience as a Data Scientist or a related project portfolio.",
                    ],
                },
            }
        }


class CVJobDetails(BaseModel):
    """
    Job details model containing position information and requirements for CV job analysis.
    """

    job_position: str
    min_experience: str
    job_desc_list: List[str]
    job_qualification_list: List[str]


class CVJobAnalysisRequest(BaseModel):
    """
    Request model for CV analysis against job details.
    """

    job_details: CVJobDetails
    cv_url: str  # Path to the file in GCS bucket (e.g., "user_cv/filename.pdf")

    class Config:
        """
        Configuration for the CVJobAnalysisRequest model with example data.
        """

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "cv_url": "https://storage.googleapis.com/main-storage-hireon/user_cv/fake_cv.pdf",
                "job_details": {
                    "job_position": "Data Scientist",
                    "min_experience": "Min. 1 years of experience",
                    "job_desc_list": [
                        "Processing and analyzing various types of data or raw information to discover patterns, gather insights, and achieve business objectives.",
                        "Build predictive analytics and optimization models to drive actionable insights that improve business performance or related key metrics.",
                    ],
                    "job_qualification_list": [
                        "Bachelor in Mathematics, Statistics, or Information Technology from a top university.",
                        "Minimum of 1 year of working or internship experience as a Data Scientist or a related project portfolio.",
                    ],
                },
            }
        }


class JobRecommendation(BaseModel):
    """
    Model representing a job recommendation with job details and match score.
    """

    job_id: str
    similarity_score: float


class RecommendationsResponse(BaseModel):
    """
    Response model for job recommendations containing a list of job details.
    """

    recommendations: List[JobRecommendation]
    metrics: Dict[str, float]


class GeneralCVAnalysisResponse(BaseModel):
    """
    Response model for general CV analysis.
    """

    overall_score: int
    score_breakdown: Dict[str, int]
    cv_strengths: List[str]
    areas_for_improvement: List[str]
    section_analysis: Dict[str, Dict[str, Union[int, str]]]
    processing_time_seconds: float
    model: str
