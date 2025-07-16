#!/usr/bin/env python3
"""
Create a narrative timeline from the analysis results.
Instead of counting patterns, show the actual story.
"""

import json
import os

import pandas as pd
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()


def load_all_results():
    """Load all analysis results with their original content."""
    results = []

    result_files = [
        "qwen_analysis_results_0-300.json",
        "qwen_analysis_results_301-600.json",
        "kimi_analysis_results.json",
        "mistral_analysis_results.json",
    ]

    all_data = []
    for filename in result_files:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
                all_data.extend(data)

    # Also load the original content
    df = pd.read_csv("data/master_data.csv")
    df["content_id"] = df["content_id"].astype(str)

    # Merge analysis with original content
    for entry in all_data:
        content_id = str(entry["content_id"])
        original = df[df["content_id"] == content_id]
        if not original.empty:
            entry["original_content"] = original.iloc[0]["content"]
            entry["original_title"] = original.iloc[0]["title"]

    # Sort by date
    for r in all_data:
        r["date"] = pd.to_datetime(r["date"])
    all_data.sort(key=lambda x: x["date"])

    return all_data


def find_specific_examples(results, pattern_name):
    """Find actual examples where a pattern occurs."""
    examples = []

    for entry in results:
        found = False

        # Check all pattern fields
        for field in [
            "psychological_patterns",
            "emotional_themes",
            "defense_mechanisms",
            "relationship_dynamics",
            "work_patterns",
        ]:
            patterns = entry.get(field, [])
            if any(pattern_name.lower() in p.lower() for p in patterns):
                found = True
                break

        # Also check key insights
        insights = entry.get("key_insights", "")
        if isinstance(insights, list):
            insights = " ".join(insights)
        if isinstance(insights, str) and pattern_name.lower() in insights.lower():
            found = True

        if found:
            content = entry.get("original_content", "")
            if isinstance(content, float) or pd.isna(
                content
            ):  # Handle NaN or float values
                content = ""
            content_preview = content[:500] + "..." if content else "No content"

            examples.append(
                {
                    "date": entry["date"].strftime("%Y-%m-%d"),
                    "title": entry.get("original_title", "No title"),
                    "insight": entry.get("key_insights", ""),
                    "content_preview": content_preview,
                }
            )

    return examples


def create_temporal_narrative(results):
    """Group insights by time period and show evolution."""

    periods = {
        "2011-2012: High School (Living with Parents)": [],
        "2013-2017: University Years": [],
        "2018: Graduation Year": [],
        "2019: First Job Ends → Russia (1 month)": [],
        "2020: Russia/COVID/Relationship": [],
        "2021-Mar 2022: Job Again": [],
        "2022: TikTok Viral/Vegas Year": [],
        "2023: Scottsdale - Getting Life Together": [],
        "2024-2025: Bangkok/Scottsdale": [],
    }

    for entry in results:
        date = entry["date"]
        year = date.year
        month = date.month
        insight = entry.get("key_insights", "")

        if not insight or insight == "No content available for analysis":
            continue

        entry_data = {
            "date": date.strftime("%Y-%m-%d"),
            "title": entry.get("original_title", ""),
            "insight": insight,
            "patterns": {
                "psychological": entry.get("psychological_patterns", []),
                "emotional": entry.get("emotional_themes", []),
                "defense": entry.get("defense_mechanisms", []),
                "relationship": entry.get("relationship_dynamics", []),
                "work": entry.get("work_patterns", []),
            },
        }

        # More precise period assignment based on your life events
        if year <= 2012:
            periods["2011-2012: High School (Living with Parents)"].append(entry_data)
        elif year <= 2017:
            periods["2013-2017: University Years"].append(entry_data)
        elif year == 2018:
            periods["2018: Graduation Year"].append(entry_data)
        elif year == 2019:
            periods["2019: First Job Ends → Russia (1 month)"].append(entry_data)
        elif year == 2020:
            periods["2020: Russia/COVID/Relationship"].append(entry_data)
        elif year == 2021 or (year == 2022 and month <= 3):
            periods["2021-Mar 2022: Job Again"].append(entry_data)
        elif year == 2022:
            periods["2022: TikTok Viral/Vegas Year"].append(entry_data)
        elif year == 2023:
            periods["2023: Scottsdale - Getting Life Together"].append(entry_data)
        else:  # 2024-2025
            periods["2024-2025: Bangkok/Scottsdale"].append(entry_data)

    return periods


def synthesize_period(period_name, entries, client):
    """Use AI to synthesize what happened in each period."""

    if not entries:
        return "No significant entries in this period."

    # Prepare the insights for synthesis
    insights_text = "\n\n".join(
        [
            f"{e['date']}: {e['insight']}"
            for e in entries[:20]  # Limit to prevent context overflow
        ]
    )

    prompt = f"""
    Analyze these insights from {period_name} and tell me:
    1. What were the main psychological dynamics in this period?
    2. What specific events or relationships drove these patterns?
    3. How did defense mechanisms and coping strategies evolve?
    4. What were the key turning points?
    
    Be specific and reference actual events/people mentioned.
    
    Insights from this period:
    {insights_text}
    """

    try:
        response = client.chat.completions.create(
            model="qwen-3-32b",
            messages=[
                {
                    "role": "system",
                    "content": "You are synthesizing psychological patterns across time periods. Be specific about events and people mentioned.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_completion_tokens=40000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error synthesizing: {str(e)}"


def main():
    print("Loading analysis results with original content...")
    results = load_all_results()
    print(f"Loaded {len(results)} analyzed entries")

    # Create temporal narrative
    print("\nCreating temporal narrative...")
    periods = create_temporal_narrative(results)

    # Find specific examples
    print("\nFinding specific examples...")
    shutdown_examples = find_specific_examples(results, "shutdown")
    lisa_examples = find_specific_examples(results, "lisa")
    abandonment_examples = find_specific_examples(results, "abandon")

    # Initialize Cerebras for synthesis
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
    client = None
    if CEREBRAS_API_KEY:
        client = Cerebras(api_key=CEREBRAS_API_KEY)

    # Create the narrative report
    report = "# Psychological Journey: A Temporal Narrative\n\n"
    report += f"Analyzing {len(results)} entries from {results[0]['date'].strftime('%Y-%m-%d')} to {results[-1]['date'].strftime('%Y-%m-%d')}\n\n"

    # Add period-by-period narrative
    for period_name, entries in periods.items():
        report += f"## {period_name}\n\n"
        report += f"*{len(entries)} significant entries*\n\n"

        if client and entries:
            print(f"Synthesizing {period_name}...")
            synthesis = synthesize_period(period_name, entries, client)
            report += synthesis + "\n\n"

        # Add a few example insights
        if entries:
            report += "### Key Moments:\n\n"
            for entry in entries[:3]:
                report += f"**{entry['date']}** - {entry['title']}\n"
                report += f"> {entry['insight'][:300]}...\n\n"

        report += "---\n\n"

    # Add specific pattern examples
    report += "## Specific Pattern Examples\n\n"

    if shutdown_examples:
        report += "### Shutdown Patterns\n\n"
        for ex in shutdown_examples[:5]:
            report += f"**{ex['date']}** - {ex['title']}\n"
            report += f"> {ex['insight'][:200]}...\n\n"

    if lisa_examples:
        report += "### Lisa Mentions\n\n"
        for ex in lisa_examples[:5]:
            report += f"**{ex['date']}** - {ex['title']}\n"
            report += f"> {ex['insight'][:200]}...\n\n"

    # Save report
    with open("narrative_analysis.md", "w") as f:
        f.write(report)

    # Also save the structured data
    with open("temporal_narrative.json", "w") as f:
        json.dump(
            {
                "periods": periods,
                "examples": {
                    "shutdown": shutdown_examples,
                    "lisa": lisa_examples,
                    "abandonment": abandonment_examples,
                },
            },
            f,
            indent=2,
            default=str,
        )

    print("\n✅ Narrative analysis complete!")
    print("- narrative_analysis.md - The story of your psychological journey")
    print("- temporal_narrative.json - Structured data with examples")


if __name__ == "__main__":
    main()
