"""
API Router for investment breakdown calculations.
Provides endpoints to calculate and preview investment distributions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

from app.services.investment_breakdown import InvestmentBreakdownCalculator


router = APIRouter(prefix="/investment", tags=["investment"])


class InvestmentRequest(BaseModel):
    """Request model for investment calculation."""
    total_value: float = Field(..., gt=0, description="Total project value in BRL (R$)")
    custom_percentages: Optional[Dict[str, float]] = Field(
        None,
        description="Optional custom percentages per stage title"
    )


class StageResponse(BaseModel):
    """Response model for a single investment stage."""
    title: str
    description: str
    percentage: float
    amount: float
    amount_formatted: str


class InvestmentResponse(BaseModel):
    """Response model for investment breakdown."""
    total_value: float
    total_formatted: str
    stages: List[StageResponse]
    breakdown_text: str


@router.post("/calculate", response_model=InvestmentResponse)
async def calculate_investment(request: InvestmentRequest):
    """
    Calculate dynamic investment breakdown for a given total value.
    
    The breakdown distributes the total value across 4 development stages:
    - Planejamento & Arquitetura do MVP (15%)
    - Desenvolvimento do App Mobile (45%)
    - Backend, APIs e Integrações (28%)
    - Testes, Ajustes e Entrega do MVP (12%)
    
    You can customize the percentages by providing custom_percentages dict.
    """
    try:
        breakdown = InvestmentBreakdownCalculator.get_breakdown_as_dict(
            total_value=request.total_value,
            custom_percentages=request.custom_percentages
        )
        return InvestmentResponse(**breakdown)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/preview/{total_value}")
async def preview_investment(total_value: float):
    """
    Quick preview of investment breakdown for a given value.
    Returns formatted text ready to be inserted in proposals.
    """
    if total_value <= 0:
        raise HTTPException(status_code=400, detail="Total value must be greater than 0")
    
    breakdown = InvestmentBreakdownCalculator.get_breakdown_as_dict(total_value)
    
    return {
        "total_value": total_value,
        "total_formatted": breakdown["total_formatted"],
        "breakdown_text": breakdown["breakdown_text"],
        "stages_summary": [
            f"{s['title']}: {s['amount_formatted']}"
            for s in breakdown["stages"]
        ]
    }
