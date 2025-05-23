"""
API data models.

This module defines Pydantic models for request/response data validation and serialization.
"""

from typing import List
from pydantic import BaseModel


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

    cv_cloud_path: str
    job_details: CoverLetterJobDetails

    class Config:
        """
        Configuration for the CoverLetterGeneratorRequest model with example data.
        """

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "cv_cloud_path": "user_cv/CV EVAN - CAPSTONE.pdf",
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
                        "Explore and develop AI use cases aimed at enhancing productivity, automating processes, and adopting new technologies within the organization.",
                        "Work closely with cross-functional teams, including business stakeholders, to understand their needs, communicate findings effectively, and implement data-driven solutions.",
                        "Engage in continuous learning and stay updated on data science methods, use cases, and technology advancements.",
                    ],
                    "job_qualification_list": [
                        "Bachelor in Mathematics, Statistics, or Information Technology from a top university.",
                        "Minimum of 1 year of working or internship experience as a Data Scientist or a related project portfolio.",
                        "Fresh graduates are welcome to apply",
                        "Strong analytical and statistical skills with a high sense of logical thinking.",
                        "Experience in big data analysis, data warehousing, and business intelligence.",
                        "Proficient in using R and Python to build machine learning models.",
                        "Experience with Hadoop, Spark, Graph DB, and Gen-AI use cases is an advantage.",
                        "Ability to work both individually and as part of a team",
                        "Willing to work on site & full time in Head Office Bintaro",
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
    cv_cloud_path: str  # Path to the file in GCS bucket (e.g., "user_cv/filename.pdf")

    class Config:
        """
        Configuration for the CVJobAnalysisRequest model with example data.
        """

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "cv_cloud_path": "user_cv/CV EVAN - CAPSTONE.pdf",
                "job_details": {
                    "job_position": "Data Scientist",
                    "min_experience": "Min. 1 years of experience",
                    "job_desc_list": [
                        "Processing and analyzing various types of data or raw information to discover patterns, gather insights, and achieve business objectives.",
                        "Build predictive analytics and optimization models to drive actionable insights that improve business performance or related key metrics.",
                        "Explore and develop AI use cases aimed at enhancing productivity, automating processes, and adopting new technologies within the organization.",
                        "Work closely with cross-functional teams, including business stakeholders, to understand their needs, communicate findings effectively, and implement data-driven solutions.",
                        "Engage in continuous learning and stay updated on data science methods, use cases, and technology advancements.",
                    ],
                    "job_qualification_list": [
                        "Bachelor in Mathematics, Statistics, or Information Technology from a top university.",
                        "Minimum of 1 year of working or internship experience as a Data Scientist or a related project portfolio.",
                        "Fresh graduates are welcome to apply",
                        "Strong analytical and statistical skills with a high sense of logical thinking.",
                        "Experience in big data analysis, data warehousing, and business intelligence.",
                        "Proficient in using R and Python to build machine learning models.",
                        "Experience with Hadoop, Spark, Graph DB, and Gen-AI use cases is an advantage.",
                        "Ability to work both individually and as part of a team",
                        "Willing to work on site & full time in Head Office Bintaro",
                    ],
                },
            }
        }
