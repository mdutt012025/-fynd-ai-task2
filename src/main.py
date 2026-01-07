# backend/src/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
import json
import httpx
import asyncio
from supabase import create_client, Client

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="AI Review Feedback System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== PYDANTIC MODELS ====================

class ReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    user_review: str = Field(..., min_length=1, max_length=1000)

    @validator('user_review')
    def validate_review(cls, v):
        if not v.strip():
            raise ValueError("Review cannot be empty")
        return v.strip()


class ReviewResponse(BaseModel):
    id: str
    rating: int
    user_review: str
    ai_response: str
    ai_summary: str
    recommended_actions: str
    created_at: str


class AdminStatsResponse(BaseModel):
    total_reviews: int
    avg_rating: float
    rating_distribution: dict
    recent_reviews: List[ReviewResponse]


# ==================== LLM FUNCTIONS ====================

async def generate_ai_response(review: str, rating: int) -> str:
    """Generate AI response to user review using Gemini"""
    prompt = f"""You are a professional and empathetic customer service representative responding to a review.

Customer Rating: {rating}/5 stars
Customer Review: {review}

Write a brief, warm, and professional response that:
- Acknowledges their specific feedback
- If positive: Thanks them and highlights what you appreciated
- If negative: Apologizes, addresses their concerns, and offers to improve
- Maximum 2-3 sentences (under 150 words)

Response:"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 200,
                        "topP": 0.9,
                    }
                },
                params={"key": GEMINI_API_KEY}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return text.strip()
            
            # Fallback response
            responses = {
                5: "Thank you so much for the wonderful 5-star review! We're thrilled you had such a great experience with us. Your positive feedback truly motivates our team!",
                4: "Thank you for your 4-star review! We're glad you enjoyed your experience. We'd love to hear what could make it even better!",
                3: "Thank you for your feedback. We appreciate you taking the time to share. We're always working to improve our service!",
                2: "Thank you for letting us know about your experience. We're sorry it wasn't quite what you expected. We'd like to make it right!",
                1: "We sincerely apologize that your experience fell short of expectations. Your feedback is important, and we'd like the opportunity to improve.",
            }
            return responses.get(rating, responses[3])
    except Exception as e:
        print(f"LLM Error in generate_ai_response: {e}")
        responses = {
            5: "Thank you so much for the wonderful 5-star review! We're thrilled you had such a great experience with us.",
            4: "Thank you for your 4-star review! We're glad you enjoyed your experience.",
            3: "Thank you for your feedback. We appreciate you taking the time to share.",
            2: "Thank you for letting us know about your experience. We're sorry it wasn't quite what you expected.",
            1: "We sincerely apologize that your experience fell short of expectations.",
        }
        return responses.get(rating, responses[3])


async def generate_ai_summary(review: str) -> str:
    """Generate summary of review for admin"""
    prompt = f"""Extract the key points from this customer review in 1-2 concise sentences (max 50 words).
Focus on specific issues, praise, or problems mentioned.

Review: "{review}"

Summary (be specific, not generic):"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 100,
                        "topP": 0.9,
                    }
                },
                params={"key": GEMINI_API_KEY}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_text = text.strip()
                    if clean_text:
                        return clean_text
            
            return "Review provides customer feedback."
    except Exception as e:
        print(f"LLM Error in generate_ai_summary: {e}")
        return "Review provides customer feedback."


async def generate_recommended_actions(review: str, rating: int) -> str:
    """Generate recommended business actions for admin"""
    prompt = f"""Based on this customer feedback, suggest 1-2 specific, concrete business actions.

Rating: {rating}/5 stars
Review: "{review}"

For POSITIVE feedback: How to leverage or reinforce this?
For NEGATIVE feedback: What specific issues need addressing?

Provide 2 actionable items (max 60 words):

Actions:"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.6,
                        "maxOutputTokens": 150,
                        "topP": 0.9,
                    }
                },
                params={"key": GEMINI_API_KEY}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_text = text.strip()
                    if clean_text:
                        return clean_text
            
            # Fallback based on rating
            if rating >= 4:
                return "1. Share this feedback with the team to reinforce best practices. 2. Feature this positive review in marketing."
            elif rating == 3:
                return "1. Identify specific pain points mentioned. 2. Create improvement plan and track progress."
            else:
                return "1. Contact customer immediately to resolve issues. 2. Implement corrective actions and follow up."
    except Exception as e:
        print(f"LLM Error in generate_recommended_actions: {e}")
        if rating >= 4:
            return "1. Share this feedback with the team to reinforce best practices. 2. Feature this review in marketing."
        elif rating == 3:
            return "1. Identify specific improvements needed. 2. Create and implement action plan."
        else:
            return "1. Contact customer to resolve issues. 2. Implement corrective actions."


# ==================== API ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "AI Review Feedback System"}


@app.post("/api/reviews", response_model=ReviewResponse)
async def submit_review(request: ReviewRequest):
    """Submit a new review and get AI response"""
    try:
        # Generate AI content in parallel
        ai_response, ai_summary, recommended_actions = await asyncio.gather(
            generate_ai_response(request.user_review, request.rating),
            generate_ai_summary(request.user_review),
            generate_recommended_actions(request.user_review, request.rating)
        )
        
        # Insert into Supabase
        # Use IST timezone (UTC+5:30)
        ist = timezone(timedelta(hours=5, minutes=30))
        current_time = datetime.now(ist).isoformat()
        
        data = {
            "rating": request.rating,
            "user_review": request.user_review,
            "ai_response": ai_response,
            "ai_summary": ai_summary,
            "recommended_actions": recommended_actions,
            "created_at": current_time
        }
        
        result = supabase.table("reviews").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save review")
        
        review_data = result.data[0]
        return ReviewResponse(
            id=review_data["id"],
            rating=review_data["rating"],
            user_review=review_data["user_review"],
            ai_response=review_data["ai_response"],
            ai_summary=review_data["ai_summary"],
            recommended_actions=review_data["recommended_actions"],
            created_at=review_data["created_at"]
        )
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")


@app.get("/api/reviews", response_model=dict)
async def get_reviews(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50)):
    """Get all reviews with pagination"""
    try:
        offset = (page - 1) * limit
        
        # Get total count
        count_result = supabase.table("reviews").select("id", count="exact").execute()
        total = len(count_result.data) if count_result.data else 0
        
        # Get paginated data
        result = supabase.table("reviews")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": result.data if result.data else []
        }
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching reviews")


@app.get("/api/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats():
    """Get admin statistics"""
    try:
        result = supabase.table("reviews").select("*").order("created_at", desc=True).execute()
        
        if not result.data:
            return AdminStatsResponse(
                total_reviews=0,
                avg_rating=0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                recent_reviews=[]
            )
        
        reviews_data = result.data
        total = len(reviews_data)
        avg_rating = sum(r["rating"] for r in reviews_data) / total if total > 0 else 0
        
        # Distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews_data:
            distribution[review["rating"]] += 1
        
        # Recent 20
        recent = [ReviewResponse(
            id=r["id"],
            rating=r["rating"],
            user_review=r["user_review"],
            ai_response=r["ai_response"],
            ai_summary=r["ai_summary"],
            recommended_actions=r["recommended_actions"],
            created_at=r["created_at"]
        ) for r in reviews_data[:20]]
        
        return AdminStatsResponse(
            total_reviews=total,
            avg_rating=round(avg_rating, 2),
            rating_distribution=distribution,
            recent_reviews=recent
        )
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stats")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)