#!/usr/bin/env python3
"""
Deep content analysis using Mistral API with large/medium model fallback.
Analyzes personal documentation entries for psychological patterns.
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

# Configuration
MODEL_CASCADE = ["mistral-large-latest", "mistral-medium-latest"]
RETRY_DELAY = 5  # seconds
MAX_RETRIES = 10  # Maximum retry attempts per entry

# API Setup
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print("MISTRAL_API_KEY not found.")
    print("Please create a .env file and add your key:")
    print('MISTRAL_API_KEY="your_mistral_api_key"')
    sys.exit(1)

client = Mistral(api_key=MISTRAL_API_KEY)


@dataclass
class AnalysisResult:
    """Represents analysis of a single entry."""

    content_id: str
    date: str
    psychological_patterns: List[str]
    emotional_themes: List[str]
    defense_mechanisms: List[str]
    relationship_dynamics: List[str]
    work_patterns: List[str]
    key_insights: str
    raw_response: str


def analyze_entry(entry: pd.Series, model_index: int = 0) -> Optional[AnalysisResult]:
    """Analyze a single entry with the LLM, with model fallback."""

    system_prompt = """You are analyzing personal journal entries and transcriptions to identify psychological patterns.
Focus on:
1. Psychological patterns and dynamics
2. Emotional themes and regulation
3. Defense mechanisms
4. Relationship patterns (especially shutdown behaviors)
5. Work/project patterns (especially avoidance/abandonment)
6. Any Jungian archetypes, attachment patterns, or other psychological frameworks that emerge naturally

Be specific and cite actual content. Look for:
- Cycles and repetitions
- Triggers for shutdown behaviors
- Patterns in relationships (especially with "Lisa" mentioned)
- Work project abandonment patterns
- Emotional regulation strategies

Return a JSON object with:
{
    "psychological_patterns": ["pattern1", "pattern2"],
    "emotional_themes": ["theme1", "theme2"],
    "defense_mechanisms": ["mechanism1", "mechanism2"],
    "relationship_dynamics": ["dynamic1", "dynamic2"],
    "work_patterns": ["pattern1", "pattern2"],
    "key_insights": "Main insight from this entry"
}"""

    user_prompt = f"""Analyze this entry from {entry["date"]}:

{entry["content"]}

Title: {entry.get("title", "No title")}
Word count: {entry["word_count"]}"""

    retry_count = 0
    current_model_idx = model_index

    while retry_count < MAX_RETRIES:
        try:
            model_name = MODEL_CASCADE[current_model_idx % len(MODEL_CASCADE)]
            print(f"  Attempting with {model_name}...")

            response = client.chat.complete(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={
                    "type": "json_object",
                },
            )

            data = json.loads(response.choices[0].message.content)

            return AnalysisResult(
                content_id=entry["content_id"],
                date=str(entry["date"]),
                psychological_patterns=data.get("psychological_patterns", []),
                emotional_themes=data.get("emotional_themes", []),
                defense_mechanisms=data.get("defense_mechanisms", []),
                relationship_dynamics=data.get("relationship_dynamics", []),
                work_patterns=data.get("work_patterns", []),
                key_insights=data.get("key_insights", ""),
                raw_response=response.choices[0].message.content,
            )

        except Exception as e:
            error_msg = str(e)
            print(f"  Error with {model_name}: {error_msg[:100]}")

            # Alternate between models
            current_model_idx += 1
            retry_count += 1

            if retry_count < MAX_RETRIES:
                print(
                    f"  Retrying in {RETRY_DELAY} seconds... (attempt {retry_count}/{MAX_RETRIES})"
                )
                time.sleep(RETRY_DELAY)
            else:
                print(f"  Failed after {MAX_RETRIES} attempts")
                return None


def main():
    """Main analysis function."""
    # Load the data
    print("Loading master data...")
    df = pd.read_csv(
        "/Volumes/simons-enjoyment/GitHub/last-chance-at-life/data/master_data.csv"
    )
    print(f"Loaded {len(df)} entries")

    # Sort by date to maintain chronological order
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # For testing, analyze only 2 entries
    test_mode = False
    if test_mode:
        # Pick 2 diverse entries - one blog post and one transcription
        test_entries = pd.concat(
            [
                df[df["source_type"] == "blogpost"].iloc[:1],
                df[
                    df["source_type"].str.contains("youtube", case=False, na=False)
                ].iloc[:1],
            ]
        )
        print(f"\nTEST MODE: Analyzing {len(test_entries)} entries")
        entries_to_analyze = test_entries
    else:
        # For full run, analyze entries 601-854
        entries_to_analyze = df.iloc[600:854]
        print(f"\nAnalyzing entries 601-854 ({len(entries_to_analyze)} entries)")

    # Analyze each entry
    results = []
    start_model_idx = 0

    for idx, entry in entries_to_analyze.iterrows():
        print(
            f"\nAnalyzing {entry['content_id']} ({entry['date'].strftime('%Y-%m-%d')})..."
        )

        result = analyze_entry(entry, start_model_idx)

        if result:
            results.append(result)
            print("  ✓ Analysis complete")
            # Alternate starting model for next entry
            start_model_idx = (start_model_idx + 1) % len(MODEL_CASCADE)
        else:
            print("  ✗ Analysis failed")

    # Save results
    if results:
        output_file = (
            "mistral_analysis_test.json"
            if test_mode
            else "mistral_analysis_results.json"
        )
        with open(output_file, "w") as f:
            json.dump(
                [
                    {
                        "content_id": r.content_id,
                        "date": r.date,
                        "psychological_patterns": r.psychological_patterns,
                        "emotional_themes": r.emotional_themes,
                        "defense_mechanisms": r.defense_mechanisms,
                        "relationship_dynamics": r.relationship_dynamics,
                        "work_patterns": r.work_patterns,
                        "key_insights": r.key_insights,
                        "raw_response": r.raw_response,
                    }
                    for r in results
                ],
                f,
                indent=2,
            )

        print(
            f"\n✅ Analysis complete! Processed {len(results)}/{len(entries_to_analyze)} entries"
        )
        print(f"Results saved to: {output_file}")
    else:
        print("\n❌ No results to save")


if __name__ == "__main__":
    main()
