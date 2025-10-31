"""Request-scoped dependencies"""
from typing import Optional
from fastapi import Request
from ..services.provider_service import ProviderService
from ..services.validation import ValidationService
from ..services.drafting_service import DraftingService


def get_provider_service(request: Request) -> ProviderService:
    """Get provider service from app state"""
    return request.app.state.provider_service


def get_validation_service(request: Request) -> ValidationService:
    """Get validation service from app state"""
    return request.app.state.validation_service


def get_drafting_service(request: Request) -> DraftingService:
    """Get drafting service from app state"""
    return request.app.state.drafting_service


def get_workspace_id(
    x_workspace_id: Optional[str] = None
) -> str:
    """Extract workspace ID from headers"""
    return x_workspace_id or "default"
