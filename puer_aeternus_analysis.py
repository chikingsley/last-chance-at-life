#!/usr/bin/env python3
"""
Deep analysis focusing on Puer Aeternus archetype patterns.
Looking for the "eternal boy" who avoids commitment and responsibility.
"""

import json
import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

load_dotenv()


def load_all_analysis_results():
    """Load all LLM analysis results."""
    all_results = []
    
    files = [
        "qwen_analysis_results_0-300.json",
        "qwen_analysis_results_301-600.json", 
        "kimi_analysis_results.json",
        "mistral_analysis_results.json"
    ]
    
    for file in files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                all_results.extend(json.load(f))
    
    # Sort by date
    for r in all_results:
        r['date'] = pd.to_datetime(r['date'])
    all_results.sort(key=lambda x: x['date'])
    
    return all_results


def identify_puer_patterns(results):
    """Identify specific Puer Aeternus patterns in the data."""
    
    puer_indicators = {
        "flight_from_commitment": [],
        "eternal_potential": [],
        "mother_complex": [],
        "fantasy_over_reality": [],
        "provisional_life": [],
        "fear_of_ordinary": [],
        "wanderlust": [],
        "project_abandonment": [],
        "idealization_cycles": [],
        "peter_pan_syndrome": []
    }
    
    for entry in results:
        content_id = entry['content_id']
        date = entry['date'].strftime('%Y-%m-%d')
        insights = entry.get('key_insights', '')
        
        # Convert insights to string if it's a list
        if isinstance(insights, list):
            insights = ' '.join(insights)
        
        # Get all patterns
        all_patterns = []
        for field in ['psychological_patterns', 'emotional_themes', 'defense_mechanisms', 
                     'relationship_dynamics', 'work_patterns']:
            patterns = entry.get(field, [])
            if patterns:
                all_patterns.extend(patterns)
        
        patterns_str = ' '.join(all_patterns).lower()
        insights_lower = insights.lower() if insights else ''
        
        # Flight from commitment
        if any(term in patterns_str or term in insights_lower for term in 
               ['avoidance', 'commitment', 'shutdown', 'withdraw', 'escape', 'flee']):
            puer_indicators['flight_from_commitment'].append({
                'date': date,
                'content_id': content_id,
                'evidence': insights[:300]
            })
        
        # Eternal potential (never actualizing)
        if any(term in patterns_str or term in insights_lower for term in
               ['potential', 'someday', 'future', 'planning', 'dreaming', 'could be']):
            puer_indicators['eternal_potential'].append({
                'date': date,
                'content_id': content_id,
                'evidence': insights[:300]
            })
        
        # Mother complex / female idealization
        if any(term in patterns_str or term in insights_lower for term in
               ['mother', 'maternal', 'idealization', 'goddess', 'perfect woman']):
            puer_indicators['mother_complex'].append({
                'date': date,
                'content_id': content_id,
                'evidence': insights[:300]
            })
        
        # Fantasy over reality
        if any(term in patterns_str or term in insights_lower for term in
               ['fantasy', 'imagination', 'idealize', 'dream', 'escape reality']):
            puer_indicators['fantasy_over_reality'].append({
                'date': date,
                'content_id': content_id,
                'evidence': insights[:300]
            })
        
        # Provisional life ("real life hasn't started yet")
        if any(term in patterns_str or term in insights_lower for term in
               ['provisional', 'temporary', 'not yet', 'waiting', 'when i', 'someday']):
            puer_indicators['provisional_life'].append({
                'date': date,
                'content_id': content_id,
                'evidence': insights[:300]
            })
        
        # Project abandonment
        if 'abandonment' in patterns_str or 'abandon' in insights_lower:
            puer_indicators['project_abandonment'].append({
                'date': date, 
                'content_id': content_id,
                'evidence': insights[:300]
            })
        
        # Wanderlust / geographical cure
        if any(term in patterns_str or term in insights_lower for term in
               ['travel', 'move', 'russia', 'vegas', 'bangkok', 'escape', 'new place']):
            puer_indicators['wanderlust'].append({
                'date': date,
                'content_id': content_id,
                'evidence': insights[:300]
            })
    
    return puer_indicators


def analyze_lisa_mary_dynamic(results):
    """Specifically analyze the Lisa/Mary dynamic through Puer lens."""
    
    lisa_mary_entries = []
    
    # Load original CSV for content
    df = pd.read_csv("data/master_data.csv")
    
    for entry in results:
        insights = entry.get('key_insights', '')
        if isinstance(insights, list):
            insights = ' '.join(insights)
        
        content_id = str(entry['content_id'])
        
        # Look for Lisa or Mary mentions
        if insights and ('lisa' in insights.lower() or 'mary' in insights.lower()):
            # Get original content
            original = df[df['content_id'] == content_id]
            if not original.empty:
                content = original.iloc[0]['content']
                if isinstance(content, str):
                    lisa_mary_entries.append({
                        'date': entry['date'],
                        'content_id': content_id,
                        'insights': insights,
                        'content_preview': content[:500] if len(content) > 500 else content,
                        'patterns': {
                            'psychological': entry.get('psychological_patterns', []),
                            'relationship': entry.get('relationship_dynamics', [])
                        }
                    })
    
    return sorted(lisa_mary_entries, key=lambda x: x['date'])


def synthesize_puer_narrative(puer_indicators, lisa_mary_entries, client):
    """Create a deep synthesis of Puer Aeternus patterns."""
    
    # Prepare data for synthesis
    pattern_summary = {
        pattern: len(entries) for pattern, entries in puer_indicators.items()
    }
    
    # Get examples of each pattern
    examples = {}
    for pattern, entries in puer_indicators.items():
        if entries:
            examples[pattern] = entries[:3]  # First 3 examples
    
    prompt = f"""
    Analyze these Puer Aeternus (eternal boy) archetype patterns found across 14 years of personal documentation.
    
    Pattern frequencies:
    {json.dumps(pattern_summary, indent=2)}
    
    Key examples:
    {json.dumps(examples, indent=2, default=str)}
    
    The subject revealed: "i picked lisa then treated her like garbage and then basically got back with mary, 
    and cheated on them both with each other"
    
    Provide a deep, cohesive analysis addressing:
    
    1. How the Puer Aeternus archetype manifests in this person's life
    2. The specific dynamics with Lisa (met 2020) and Mary that exemplify these patterns
    3. Why they "shut down with girls they like" - especially Lisa
    4. The connection between relationship shutdowns and work project abandonment
    5. The role of geographical moves (Russia, Vegas, Bangkok) as escape mechanisms
    6. How graduation (2018) and first job ending (2019) triggered these patterns
    7. The deeper psychological wounds driving these behaviors
    8. The cycle of idealization → disappointment → abandonment
    
    Be specific, reference actual patterns, and create a cohesive narrative that explains
    the deep issues rather than surface symptoms. This should feel like a thorough psychological
    examination, not a spot check.
    """
    
    try:
        response = client.chat.completions.create(
            model="qwen-3-32b",
            messages=[
                {"role": "system", "content": "You are a Jungian analyst examining Puer Aeternus patterns. Be thorough, specific, and psychologically insightful."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=40000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error in synthesis: {str(e)}"


def main():
    print("Loading all analysis results...")
    results = load_all_analysis_results()
    print(f"Loaded {len(results)} entries")
    
    print("\nIdentifying Puer Aeternus patterns...")
    puer_indicators = identify_puer_patterns(results)
    
    print("\nAnalyzing Lisa/Mary dynamic...")
    lisa_mary_entries = analyze_lisa_mary_dynamic(results)
    
    # Initialize Cerebras
    client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
    
    print("\nSynthesizing deep analysis...")
    synthesis = synthesize_puer_narrative(puer_indicators, lisa_mary_entries, client)
    
    # Create comprehensive report
    report = f"""# Puer Aeternus: Deep Psychological Analysis
    
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Pattern Summary

Total entries analyzed: {len(results)}
Date range: {results[0]['date'].strftime('%Y-%m-%d')} to {results[-1]['date'].strftime('%Y-%m-%d')}

### Puer Aeternus Indicators Found:
"""
    
    for pattern, entries in puer_indicators.items():
        if entries:
            report += f"\n**{pattern.replace('_', ' ').title()}**: {len(entries)} instances\n"
            for example in entries[:2]:
                report += f"- {example['date']}: {example['evidence'][:150]}...\n"
    
    report += f"\n## Deep Synthesis\n\n{synthesis}\n"
    
    report += "\n## Lisa/Mary Dynamic Timeline\n\n"
    for entry in lisa_mary_entries:
        report += f"**{entry['date'].strftime('%Y-%m-%d')}**\n"
        report += f"Insights: {entry['insights'][:300]}...\n"
        report += f"Patterns: {', '.join(entry['patterns']['psychological'][:3])}\n\n"
    
    # Save report
    with open("puer_aeternus_analysis.md", "w") as f:
        f.write(report)
    
    # Save raw data
    with open("puer_patterns_raw.json", "w") as f:
        json.dump({
            'puer_indicators': puer_indicators,
            'lisa_mary_entries': lisa_mary_entries
        }, f, indent=2, default=str)
    
    print("\n✅ Deep analysis complete!")
    print("- puer_aeternus_analysis.md - Comprehensive psychological analysis")
    print("- puer_patterns_raw.json - Raw pattern data")


if __name__ == "__main__":
    main()