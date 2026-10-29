"""app/schemas/__init__.py"""
from .auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
)
from .document import (
    DocumentListItem,
    DocumentListResponse,
    DocumentMetadata,
    ExternalIngestRequest,
    ExternalMetadataPreview,
    TextInputRequest,
)
from .analysis import (
    AnalysisListItem,
    AnalysisListResponse,
    AnalysisResult,
    AnalyzeDocumentRequest,
    DashboardStats,
    DetectedSection,
    DocumentStatistics,
    KeyPhrase,
)

__all__ = [
    # auth
    "RegisterRequest", "RegisterResponse", "LoginRequest",
    "TokenResponse", "UserProfile", "UpdateProfileRequest", "ChangePasswordRequest",
    # document
    "DocumentMetadata", "DocumentListItem", "DocumentListResponse", "TextInputRequest",
    "ExternalIngestRequest", "ExternalMetadataPreview",
    # analysis
    "AnalysisResult", "AnalysisListItem", "AnalysisListResponse",
    "AnalyzeDocumentRequest", "DashboardStats",
    "KeyPhrase", "DetectedSection", "DocumentStatistics",
]

