"""Pydantic v2 domain models (placeholders)"""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DocDraft:
    title: str
    content: str


@dataclass
class ProjectBrief:
    name: str
    details: Dict[str, Any]


@dataclass
class DocumentBundle:
    drafts: List[DocDraft]
