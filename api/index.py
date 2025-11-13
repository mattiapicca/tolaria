"""
Vercel serverless function entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os

# Import app components
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.scryfall import ScryfallClient
from rules.engine_lite import RulesEngineLite  # Lightweight version for Vercel
from stack.resolver import StackResolver

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

# Initialize components (lazy loading for rules engine)
scryfall_client = ScryfallClient()
rules_engine = None
stack_resolver = None


def get_rules_engine():
    """Lazy initialization of rules engine"""
    global rules_engine, stack_resolver
    if rules_engine is None:
        print("Initializing Lightweight Rules Engine for Vercel...")
        rules_engine = RulesEngineLite()  # Lightweight version without ChromaDB
        stack_resolver = StackResolver(scryfall_client, rules_engine)
        print("Rules Engine ready!")
    return rules_engine, stack_resolver


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
        card_data = await scryfall_client.search_card(card_name)
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
        # Lazy load rules engine on first request
        _, resolver = get_rules_engine()

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
