

import subprocess
import sys

print("Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests", "pandas", "numpy"])
print("✓ Dependencies installed!")

import json
import pandas as pd
import numpy as np
from typing import Dict
import re
import time
import requests


API_KEY = "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"  
CSV_PATH = "/content/yelp.csv"  

# ==================================================
# SETUP
# ==================================================

MODEL = "mistralai/mistral-7b-instruct:free"  
API_URL = "https://openrouter.ai/api/v1/chat/completions"

print("Loading data...")
df = pd.read_csv(CSV_PATH)

# ============================================================================
# PROMPTING APPROACHES
# ============================================================================

PROMPT_V1_DIRECT = """Analyze this review and return ONLY a JSON object with no markdown, no extra text.

Review: {review}

Return exactly this format:
{{"predicted_stars": <number 1-5>, "explanation": "<one short sentence>"}}"""

PROMPT_V2_STRUCTURED = """Analyze this review for sentiment and return ONLY JSON (no markdown, no extra text).

Rating scale:
1=Terrible (major complaints), 2=Poor (mostly negative), 3=Okay (mixed), 4=Good (mostly positive), 5=Excellent (outstanding)

Review: {review}

Return exactly:
{{"predicted_stars": <1-5>, "explanation": "<one sentence why>"}}"""

PROMPT_V3_CHAIN_OF_THOUGHT = """Analyze this review step by step.

Review: {review}

1. What positive aspects are mentioned? (food, service, value, etc.)
2. What negative aspects are mentioned?
3. Is the reviewer satisfied? Will they return?
4. Rate from 1-5 based on balance.

Return ONLY JSON (no markdown, no extra text):
{{"predicted_stars": <1-5>, "explanation": "<one sentence>"}}"""

# ============================================================================
# LLM CALLER FUNCTIONS
# ============================================================================

def call_openrouter(prompt: str) -> str:
    """Call OpenRouter API with dynamically selected model."""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://github.com/fynd",
            "X-Title": "Fynd Rating Prediction",
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200,
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            print(f"OpenRouter Error: {error_msg[:100]}")
            return ""
    except Exception as e:
        print(f"API Error: {str(e)[:100]}")
        return ""

def call_gemini(prompt: str) -> str:
    """Call Gemini API."""
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=200,
            )
        )
        return response.text if response.text else ""
    except Exception as e:
        print(f"API Error: {str(e)[:100]}")
        return ""

def call_llm(prompt: str) -> str:
    """Universal LLM caller."""
    if API_TYPE == "openrouter":
        return call_openrouter(prompt)
    else:
        return call_gemini(prompt)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_json(response: str) -> Dict:
    """Extract and validate JSON from response - very flexible."""
    if not response:
        return None

    try:
        # Remove markdown code blocks
        response_clean = response.replace("```json", "").replace("```", "").strip()

        # Try direct JSON parse
        data = json.loads(response_clean)

        if "predicted_stars" in data:
            stars = int(data.get("predicted_stars"))
            if 1 <= stars <= 5:
                explanation = str(data.get("explanation", "No explanation"))[:100]
                return {
                    "predicted_stars": stars,
                    "explanation": explanation
                }
    except:
        pass

    try:
        # Find JSON with curly braces 
        import re
        # Find the outermost JSON object
        match = re.search(r'\{[^{}]*(?:"predicted_stars"[^}]*)\}', response, re.DOTALL)
        if match:
            json_str = match.group(0)
            # Fix common issues
            json_str = json_str.replace('\n', ' ').replace('  ', ' ')
            data = json.loads(json_str)

            if "predicted_stars" in data:
                stars = int(data.get("predicted_stars"))
                if 1 <= stars <= 5:
                    explanation = str(data.get("explanation", ""))[:100]
                    return {
                        "predicted_stars": stars,
                        "explanation": explanation
                    }
    except:
        pass

    try:
        #extract star number directly
        star_match = re.search(r'"predicted_stars"\s*:\s*([1-5])', response)
        if star_match:
            stars = int(star_match.group(1))
            # Try to find explanation
            exp_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', response)
            explanation = exp_match.group(1) if exp_match else "Extracted from response"
            return {
                "predicted_stars": stars,
                "explanation": explanation[:100]
            }
    except:
        pass

    return None

def test_prompt_approach(
    reviews_df: pd.DataFrame,
    prompt_template: str,
    approach_name: str,
    sample_size: int = 200
) -> Dict:
    """Test a prompting approach on a sample of reviews."""

    sample = reviews_df.sample(min(sample_size, len(reviews_df)), random_state=42).reset_index(drop=True)

    results = {
        "approach": approach_name,
        "total_tested": len(sample),
        "valid_json_count": 0,
        "correct_predictions": 0,
        "predictions": []
    }

    print(f"\n{'='*70}")
    print(f"Testing: {approach_name}")
    print(f"{'='*70}")

    for idx, row in sample.iterrows():
        review = str(row['text'])[:500]
        actual_stars = int(row['stars'])

        prompt = prompt_template.format(review=review)
        response = call_llm(prompt)
        prediction = extract_json(response)

        # Debug: show first response
        if idx == 0:
            print(f"\n[DEBUG] Raw response sample:\n{response[:200]}\n")

        if prediction:
            results["valid_json_count"] += 1

            is_correct = actual_stars == prediction["predicted_stars"]
            if is_correct:
                results["correct_predictions"] += 1

            results["predictions"].append({
                "actual": actual_stars,
                "predicted": prediction["predicted_stars"],
                "explanation": prediction["explanation"],
                "correct": is_correct,
                "review_snippet": review[:100] + "..."
            })

        if (idx + 1) % 20 == 0:
            print(f"  ✓ Processed {idx + 1}/{len(sample)} reviews...")

        time.sleep(0.3)

    results["json_validity_rate"] = (results["valid_json_count"] / len(sample)) * 100
    results["accuracy"] = (results["correct_predictions"] / results["valid_json_count"] * 100) if results["valid_json_count"] > 0 else 0

    print(f"\n✓ {approach_name} Complete")
    print(f"  Valid JSON: {results['json_validity_rate']:.1f}%")
    print(f"  Accuracy: {results['accuracy']:.1f}%")

    return results

# ============================================================================
# LOAD DATASET
# ============================================================================

print("\n" + "="*80)
print("STEP 2: LOAD YELP REVIEWS DATASET")
print("="*80)

from google.colab import files

print("\nChoose how to load data:")
print("1. Upload CSV file from computer")
print("2. Use sample data (for testing)")

choice = input("Enter choice (1 or 2): ").strip()

if choice == "1":
    print("\nUploading file...")
    uploaded = files.upload()
    filename = list(uploaded.keys())[0]
    df = pd.read_csv(filename)
    print(f"✓ Loaded: {filename}")
else:
    print("\nCreating sample Yelp data for testing...")
    sample_reviews = [
        {"text": "Amazing place! Food was delicious and service was excellent. Highly recommend!", "stars": 5},
        {"text": "Good food but a bit pricey. Service was slow.", "stars": 3},
        {"text": "Terrible experience. Food was cold and staff was rude.", "stars": 1},
        {"text": "Really great restaurant. Everything was perfect.", "stars": 5},
        {"text": "It was okay. Nothing special but not bad either.", "stars": 3},
        {"text": "Disappointing. Expected much better quality.", "stars": 2},
        {"text": "Fantastic! Best meal I've had in months.", "stars": 5},
        {"text": "Not great. Waited too long and food wasn't fresh.", "stars": 2},
        {"text": "Excellent service and amazing food. Will visit again!", "stars": 5},
        {"text": "Average restaurant. Some good dishes, some not so good.", "stars": 3},
    ] * 20

    df = pd.DataFrame(sample_reviews)
    print("✓ Sample data created")

print(f"\nDataset: {len(df)} reviews")
print(f"Columns: {df.columns.tolist()}")
print(f"\nStar Distribution:\n{df['stars'].value_counts().sort_index()}")

# ============================================================================
# TEST ALL APPROACHES
# ============================================================================

print("\n" + "="*80)
print("STEP 3: TEST ALL THREE PROMPTING APPROACHES")
print("="*80)

results_all = []

print("\n→ Testing Approach 1: Direct Prompt")
result_v1 = test_prompt_approach(df, PROMPT_V1_DIRECT, "Approach 1: Direct Prompt", sample_size=200)
results_all.append(result_v1)

print("\n→ Testing Approach 2: Structured with Guidelines")
result_v2 = test_prompt_approach(df, PROMPT_V2_STRUCTURED, "Approach 2: Structured with Guidelines", sample_size=200)
results_all.append(result_v2)

print("\n→ Testing Approach 3: Chain of Thought")
result_v3 = test_prompt_approach(df, PROMPT_V3_CHAIN_OF_THOUGHT, "Approach 3: Chain of Thought", sample_size=200)
results_all.append(result_v3)

# ============================================================================
# RESULTS & ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("COMPARISON TABLE")
print("="*80)

comparison_data = []
for result in results_all:
    comparison_data.append({
        "Approach": result["approach"],
        "Samples": result["total_tested"],
        "Valid JSON (%)": f"{result['json_validity_rate']:.1f}%",
        "Accuracy (%)": f"{result['accuracy']:.1f}%",
        "Correct": result["correct_predictions"]
    })

comparison_df = pd.DataFrame(comparison_data)
print("\n" + comparison_df.to_string(index=False))

# ============================================================================
# DETAILED ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("DETAILED ANALYSIS & SAMPLE PREDICTIONS")
print("="*80)

for i, result in enumerate(results_all, 1):
    print(f"\n{i}. {result['approach']}")
    print("-" * 70)

    if result["predictions"]:
        print("Sample Predictions (first 5):")
        for pred in result["predictions"][:5]:
            status = "✓" if pred["correct"] else "✗"
            print(f"\n  {status} Actual: {pred['actual']} → Predicted: {pred['predicted']}")
            print(f"     Review: {pred['review_snippet']}")
            print(f"     Reasoning: {pred['explanation']}")

    print(f"\n  JSON Validity: {result['json_validity_rate']:.1f}%")
    print(f"  Accuracy: {result['accuracy']:.1f}%")

