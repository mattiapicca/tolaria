"""
Vercel serverless function entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize FastAPI app
app = FastAPI(
    title="Tolaria - MTG Rules AI Agent",
    description="AI agent for Magic: The Gathering rules and stack interactions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for lazy loading
_scryfall_client = None
_rules_engine = None
_stack_resolver = None


def get_components():
    """Lazy initialization of all components"""
    global _scryfall_client, _rules_engine, _stack_resolver

    if _scryfall_client is None:
        print("Initializing components...")

        # Import only when needed
        from api.scryfall import ScryfallClient
        from rules.engine_lite import RulesEngineLite
        from stack.resolver import StackResolver

        _scryfall_client = ScryfallClient()
        _rules_engine = RulesEngineLite()
        _stack_resolver = StackResolver(_scryfall_client, _rules_engine)

        print("Components ready!")

    return _scryfall_client, _rules_engine, _stack_resolver


class QuestionRequest(BaseModel):
    question: str
    cards: List[str]
    player_actions: Optional[List[dict]] = None


class StackResponse(BaseModel):
    stack_visualization: List[dict]
    resolution_steps: List[dict]
    explanation: str
    rules_references: List[str]


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Tolaria - MTG Rules AI Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "search_card": "/api/search-card/{card_name}",
            "ask_question": "/api/ask"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/search-card/{card_name}")
async def search_card(card_name: str):
    """Search for a card using Scryfall API"""
    try:
        scryfall, _, _ = get_components()
        card_data = await scryfall.search_card(card_name)
        return card_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Card not found: {str(e)}")


@app.post("/api/ask", response_model=StackResponse)
async def ask_question(request: QuestionRequest):
    """
    Main endpoint for asking questions about MTG rules and stack interactions

    Args:
        question: The user's question about the interaction
        cards: List of card names involved
        player_actions: Optional list of player actions in sequence

    Returns:
        Stack visualization, resolution steps, and explanation
    """
    try:
        # Lazy load components on first request
        _, _, resolver = get_components()

        # Resolve the stack and get explanation
        result = await resolver.resolve_interaction(
            question=request.question,
            card_names=request.cards,
            player_actions=request.player_actions
        )

        return result

    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_detail)  # Log to Vercel
        raise HTTPException(status_code=500, detail=error_detail)


# Vercel serverless function handler
handler = app
