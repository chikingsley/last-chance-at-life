#!/usr/bin/env python3
"""
Pure aggregation of LLM-identified patterns without imposing our own keywords or assumptions.
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd


def load_all_results():
    """Load all analysis JSON files."""
    results = []

    # List of result files to check
    result_files = [
        "qwen_analysis_results_0-300.json",
        "qwen_analysis_results_301-600.json",
        "kimi_analysis_results.json",
        "mistral_analysis_results.json",
    ]

    for filename in result_files:
        if os.path.exists(filename):
            print(f"Loading {filename}...")
            with open(filename, "r") as f:
                data = json.load(f)
                results.extend(data)
                print(f"  Loaded {len(data)} entries")

    # Sort by date for chronological analysis
    for r in results:
        r["date"] = pd.to_datetime(r["date"])
    results.sort(key=lambda x: x["date"])

    return results


def aggregate_patterns(results):
    """Simply count what the LLMs found - no filtering or keywords."""

    # Pattern counters
    all_patterns = defaultdict(Counter)

    # Temporal tracking
    patterns_by_period = defaultdict(lambda: defaultdict(Counter))

    # Key insights collection
    all_insights = []

    for entry in results:
        date = entry["date"]
        year = date.year

        # Define periods
        if year <= 2017:
            period = "2011-2017 (Pre-graduation)"
        elif year == 2018:
            period = "2018 (Graduation year)"
        elif year <= 2020:
            period = "2019-2020 (Post-grad/Russia)"
        else:
            period = "2021-2025 (Recent)"

        # Count ALL patterns exactly as LLMs identified them
        for pattern in entry.get("psychological_patterns", []):
            all_patterns["psychological"][pattern] += 1
            patterns_by_period[period]["psychological"][pattern] += 1

        for theme in entry.get("emotional_themes", []):
            all_patterns["emotional"][theme] += 1
            patterns_by_period[period]["emotional"][theme] += 1

        for mechanism in entry.get("defense_mechanisms", []):
            all_patterns["defense"][mechanism] += 1
            patterns_by_period[period]["defense"][mechanism] += 1

        for dynamic in entry.get("relationship_dynamics", []):
            all_patterns["relationship"][dynamic] += 1
            patterns_by_period[period]["relationship"][dynamic] += 1

        for pattern in entry.get("work_patterns", []):
            all_patterns["work"][pattern] += 1
            patterns_by_period[period]["work"][pattern] += 1

        # Collect insights with metadata
        if entry.get("key_insights"):
            all_insights.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "insight": entry["key_insights"],
                    "content_id": entry["content_id"],
                }
            )

    return {
        "total_entries": len(results),
        "date_range": f"{results[0]['date'].strftime('%Y-%m-%d')} to {results[-1]['date'].strftime('%Y-%m-%d')}",
        "all_patterns": {k: v.most_common() for k, v in all_patterns.items()},
        "patterns_by_period": {
            period: {k: v.most_common(10) for k, v in patterns.items()}
            for period, patterns in patterns_by_period.items()
        },
        "insights_sample": all_insights[:20],  # First 20 insights as examples
        "total_insights": len(all_insights),
    }


def find_pattern_cooccurrence(results):
    """See which patterns tend to appear together."""
    cooccurrence = defaultdict(Counter)

    for entry in results:
        # Get all patterns from this entry
        entry_patterns = []
        for field in [
            "psychological_patterns",
            "emotional_themes",
            "defense_mechanisms",
            "relationship_dynamics",
            "work_patterns",
        ]:
            patterns = entry.get(field, [])
            entry_patterns.extend([(field, p) for p in patterns])

        # Count co-occurrences
        for i, (field1, pattern1) in enumerate(entry_patterns):
            for field2, pattern2 in entry_patterns[i + 1 :]:
                if field1 != field2:  # Only count across different categories
                    key = f"{field1}: {pattern1}"
                    value = f"{field2}: {pattern2}"
                    cooccurrence[key][value] += 1

    # Get top co-occurrences
    top_cooccurrences = []
    for pattern1, related in cooccurrence.items():
        for pattern2, count in related.most_common(3):
            if count > 2:  # Only include if appears together 3+ times
                top_cooccurrences.append(
                    {"pattern1": pattern1, "pattern2": pattern2, "count": count}
                )

    return sorted(top_cooccurrences, key=lambda x: x["count"], reverse=True)[:50]


def create_readable_report(aggregated, cooccurrences):
    """Create a markdown report of the findings."""

    report = f"""# Pattern Analysis Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Overview
- **Total entries analyzed**: {aggregated["total_entries"]}
- **Date range**: {aggregated["date_range"]}

## Top Patterns Across All Entries

"""

    # Add top patterns by category
    for category, patterns in aggregated["all_patterns"].items():
        report += f"### {category.title().replace('_', ' ')}\n\n"
        for pattern, count in patterns[:15]:
            report += f"- **{count}x**: {pattern}\n"
        report += "\n"

    # Add temporal evolution
    report += "## Pattern Evolution Over Time\n\n"
    for period, data in aggregated["patterns_by_period"].items():
        report += f"### {period}\n\n"
        for category, patterns in data.items():
            if patterns:
                report += f"**{category.title()}**: "
                report += ", ".join([f"{p[0]} ({p[1]}x)" for p in patterns[:5]])
                report += "\n\n"

    # Add co-occurrence patterns
    report += "## Patterns That Appear Together\n\n"
    report += "These patterns frequently co-occur in the same entries:\n\n"

    prev_pattern1 = None
    for item in cooccurrences[:30]:
        if item["pattern1"] != prev_pattern1:
            report += f"\n**{item['pattern1']}** often appears with:\n"
            prev_pattern1 = item["pattern1"]
        report += f"  - {item['pattern2']} ({item['count']}x)\n"

    # Add sample insights
    report += "\n## Sample Key Insights\n\n"
    for insight in aggregated["insights_sample"]:
        report += f"**{insight['date']}**: {insight['insight']}\n\n"

    return report


def main():
    print("Loading all analysis results...")
    results = load_all_results()

    print("\nAggregating patterns...")
    aggregated = aggregate_patterns(results)

    print("\nFinding pattern co-occurrences...")
    cooccurrences = find_pattern_cooccurrence(results)

    # Save raw data
    with open("aggregated_raw.json", "w") as f:
        json.dump(
            {"aggregated": aggregated, "cooccurrences": cooccurrences},
            f,
            indent=2,
            default=str,
        )

    # Create readable report
    report = create_readable_report(aggregated, cooccurrences)

    with open("pattern_analysis_report.md", "w") as f:
        f.write(report)

    print("\n✅ Analysis complete!")
    print("- Raw data: aggregated_raw.json")
    print("- Report: pattern_analysis_report.md")

    # Print summary
    print(f"\nAnalyzed {aggregated['total_entries']} entries")
    print("\nTop 5 patterns by category:")
    for category, patterns in aggregated["all_patterns"].items():
        print(f"\n{category.upper()}:")
        for pattern, count in patterns[:5]:
            print(f"  {count:3d}x - {pattern}")


if __name__ == "__main__":
    main()
