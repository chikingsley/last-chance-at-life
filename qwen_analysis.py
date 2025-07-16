#!/usr/bin/env python3
"""
Deep content analysis using Cerebras/Qwen API with retry logic.
Analyzes personal documentation entries for psychological patterns.
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()

# Configuration
# MODEL = "qwen-3-235b-a22b"
MODEL = "qwen-3-32b"
RETRY_DELAY = 5  # seconds
MAX_RETRIES = 20  # Maximum retry attempts per entry

# API Setup
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
if not CEREBRAS_API_KEY:
    print("CEREBRAS_API_KEY not found.")
    print("Please create a .env file and add your key:")
    print('CEREBRAS_API_KEY="your_cerebras_api_key"')
    sys.exit(1)

client = Cerebras(api_key=CEREBRAS_API_KEY)


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


def analyze_entry(entry: pd.Series) -> Optional[AnalysisResult]:
    """Analyze a single entry with the LLM, with retry logic."""

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

Return ONLY a valid JSON object (no other text) with the exact format specified in the schema."""

    analysis_schema = {
        "type": "object",
        "properties": {
            "psychological_patterns": {"type": "array", "items": {"type": "string"}},
            "emotional_themes": {"type": "array", "items": {"type": "string"}},
            "defense_mechanisms": {"type": "array", "items": {"type": "string"}},
            "relationship_dynamics": {"type": "array", "items": {"type": "string"}},
            "work_patterns": {"type": "array", "items": {"type": "string"}},
            "key_insights": {"type": "string"},
        },
        "required": [
            "psychological_patterns",
            "emotional_themes",
            "defense_mechanisms",
            "relationship_dynamics",
            "work_patterns",
            "key_insights",
        ],
        "additionalProperties": False,
    }

    content = str(entry["content"]) if pd.notna(entry["content"]) else ""
    if len(content) > 20000:
        content = content[:20000] + "... [truncated]"

    user_prompt = f"""Analyze this entry from {entry["date"]}:

{content}

Title: {entry.get("title", "No title")}
Word count: {entry["word_count"]}"""

    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            print("  Attempting analysis...")

            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.6,
                max_completion_tokens=40000,
                top_p=0.95,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "analysis_schema",
                        "strict": True,
                        "schema": analysis_schema,
                    },
                },
            )

            response_content = completion.choices[0].message.content
            print(f"  Raw response preview: {response_content[:200]}...")

            # Try to extract JSON from the response
            import re

            json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                data = json.loads(response_content)

            return AnalysisResult(
                content_id=entry["content_id"],
                date=str(entry["date"]),
                psychological_patterns=data.get("psychological_patterns", []),
                emotional_themes=data.get("emotional_themes", []),
                defense_mechanisms=data.get("defense_mechanisms", []),
                relationship_dynamics=data.get("relationship_dynamics", []),
                work_patterns=data.get("work_patterns", []),
                key_insights=data.get("key_insights", ""),
                raw_response=response_content,
            )

        except Exception as e:
            error_msg = str(e)
            print(f"  Error: {error_msg[:100]}")

            if "rate" in error_msg.lower() or "429" in error_msg:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    wait_time = RETRY_DELAY * retry_count
                    print(
                        f"  Rate limited. Waiting {wait_time} seconds... (attempt {retry_count}/{MAX_RETRIES})"
                    )
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {MAX_RETRIES} attempts")
                    return None
            else:
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
    print("Loading master data...")
    df = pd.read_csv(
        "/Volumes/simons-enjoyment/GitHub/last-chance-at-life/data/master_data.csv"
    )
    print(f"Loaded {len(df)} entries")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    test_mode = False
    output_file = (
        "qwen_analysis_test.json" if test_mode else "qwen_analysis_results.json"
    )

    existing_results = []
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                existing_results = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {output_file}. Starting fresh.")
            existing_results = []

    processed_content_ids = {str(r.get("content_id")) for r in existing_results}
    print(f"Found {len(existing_results)} existing results.")

    if test_mode:
        test_entries = pd.concat(
            [
                df[df["source_type"] == "blogpost"].iloc[5:6],
                df[
                    df["source_type"].str.contains("youtube", case=False, na=False)
                ].iloc[2:3],
            ]
        )
        print(f"\nTEST MODE: Analyzing {len(test_entries)} entries")
        entries_to_analyze = test_entries
    else:
        entries_to_analyze = df.iloc[300:600]
        print(f"\nAnalyzing entries 301-600 ({len(entries_to_analyze)} entries)")

    entries_to_analyze["content_id"] = entries_to_analyze["content_id"].astype(str)
    entries_to_analyze = entries_to_analyze[
        ~entries_to_analyze["content_id"].isin(processed_content_ids)
    ]
    print(
        f"Skipped {len(processed_content_ids)} entries. Analyzing {len(entries_to_analyze)} new entries."
    )

    new_results = []

    for idx, entry in entries_to_analyze.iterrows():
        print(
            f"\nAnalyzing {entry['content_id']} ({entry['date'].strftime('%Y-%m-%d')})..."
        )

        result = analyze_entry(entry)

        if result:
            new_results.append(result)
            print("  ✓ Analysis complete")

            # Save progress after each successful analysis
            all_results = existing_results + [
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
                for r in new_results
            ]

            with open(output_file, "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"  Progress saved: {len(all_results)} total entries")
        else:
            print("  ✗ Analysis failed")

    if new_results:
        all_results = existing_results + [
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
            for r in new_results
        ]

        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)

        print(
            f"\n✅ Analysis complete! Added {len(new_results)} new results. Total: {len(all_results)}."
        )
        print(f"Results saved to: {output_file}")
    else:
        print("\n❌ No new results to save")


if __name__ == "__main__":
    main()
