from typing import Literal, Optional

from pydantic import BaseModel, Field


class Visual(BaseModel):
    type: Literal["emoji", "notion_icon"]
    value: str
    color: Optional[str] = None


class RecommendRequest(BaseModel):
    title: str = Field(..., min_length=1)


class RankedCandidate(BaseModel):
    rank: int
    candidate_id: str
    visual: Visual
    score: float
    label: str
    summary_reason: str


class RecommendResponse(BaseModel):
    recommendation_id: str
    visual: Optional[Visual] = None
    reason: str
    no_candidate: bool = False
    recommendation_path: str
    candidates: list[RankedCandidate] = Field(default_factory=list)


class RankingSnapshotInput(BaseModel):
    top1_candidate_id: Optional[str] = None
    top1_visual: Optional[str] = None
    top1_score: Optional[float] = None
    top2_candidate_id: Optional[str] = None
    top2_visual: Optional[str] = None
    top2_score: Optional[float] = None
    top1_top2_margin: Optional[float] = None
    ranking_confidence: Optional[Literal["low", "medium", "high", "unknown"]] = None


OVERRIDE_REASONS: frozenset[str] = frozenset(
    {
        "wrong_top_candidate",
        "catalog_gap",
        "action_vs_object",
        "channel_vs_object",
        "document_vs_status",
        "boundary_ambiguity",
        "personal_preference",
        "other",
    }
)


class FeedbackRequest(BaseModel):
    recommendation_id: Optional[str] = None
    input_title: str = Field(..., min_length=1)
    feedback_type: Literal["accepted", "override", "no_candidate", "no_candidate_selected"]
    system_recommended_visual: Optional[Visual] = None
    final_selected_visual: Optional[Visual] = None
    override_reason: Optional[str] = None
    user_note: Optional[str] = None
    accept_quality: Optional[Literal["stable", "unstable", "unsure"]] = None
    ranking_confidence_note: Optional[str] = None
    ranking_snapshot: Optional[RankingSnapshotInput] = None


class FeedbackResponse(BaseModel):
    ok: bool = True
    feedback_type: str


class VisualCatalogItem(BaseModel):
    candidate_id: str
    visual: Visual
    label: str


class VisualCatalogResponse(BaseModel):
    items: list[VisualCatalogItem]
