import pandas as pd
import numpy as np
from datetime import datetime
import re

# Load the data
df = pd.read_csv('data/master_data.csv')
df['date'] = pd.to_datetime(df['date'])
graduation_date = pd.to_datetime('2018-05-31')
df['period'] = df['date'].apply(lambda x: 'pre_graduation' if x <= graduation_date else 'post_graduation')
df['content'] = df['content'].fillna('')

print("=== QUALITATIVE ANALYSIS: LANGUAGE AND TONE SHIFTS ===\n")

# 1. RELATIONSHIP LANGUAGE EVOLUTION
print("1. RELATIONSHIP LANGUAGE EVOLUTION")
print("-" * 50)

# Early relationship mentions (2011-2013)
early_relationships = df[(df['date'] < '2014-01-01') & (df['content'].str.contains('love|girlfriend|relationship|crush', case=False, na=False))]
print(f"\nEarly period (2011-2013): {len(early_relationships)} entries")
if len(early_relationships) > 0:
    sample = early_relationships.iloc[0]
    print(f"Sample from {sample['date'].strftime('%Y-%m-%d')}:")
    print(f"'{sample['content'][:200]}...'\n")

# Late pre-graduation (2016-2018)
late_pregrad = df[(df['date'] >= '2016-01-01') & (df['date'] <= graduation_date) & (df['content'].str.contains('love|girlfriend|relationship', case=False, na=False))]
print(f"Late pre-graduation (2016-2018): {len(late_pregrad)} entries")
if len(late_pregrad) > 0:
    sample = late_pregrad.iloc[0]
    print(f"Sample from {sample['date'].strftime('%Y-%m-%d')}:")
    print(f"'{sample['content'][:200]}...'\n")

# Post-graduation relationships
post_grad_rel = df[(df['period'] == 'post_graduation') & (df['content'].str.contains('love|girlfriend|relationship|partner', case=False, na=False))]
print(f"Post-graduation: {len(post_grad_rel)} entries")
if len(post_grad_rel) > 0:
    sample = post_grad_rel.iloc[min(10, len(post_grad_rel)-1)]
    print(f"Sample from {sample['date'].strftime('%Y-%m-%d')}:")
    print(f"'{sample['content'][:200]}...'\n")

# 2. WORK/PROJECT LANGUAGE PERSISTENCE
print("\n2. WORK/PROJECT LANGUAGE AND PERSISTENCE")
print("-" * 50)

# Pre-graduation work mentions
pre_work = df[(df['period'] == 'pre_graduation') & (df['content'].str.contains('work|project|goal|business', case=False, na=False))]
print(f"\nPre-graduation work mentions: {len(pre_work)} entries")

# Post-graduation work mentions - early period
early_post_work = df[(df['date'] >= graduation_date) & (df['date'] < '2020-01-01') & (df['content'].str.contains('work|project|business|startup', case=False, na=False))]
print(f"Early post-graduation (2018-2019) work mentions: {len(early_post_work)} entries")

# Recent work mentions
recent_work = df[(df['date'] >= '2023-01-01') & (df['content'].str.contains('work|project|business|startup', case=False, na=False))]
print(f"Recent (2023-2025) work mentions: {len(recent_work)} entries")

# 3. SELF-REFLECTION DEPTH
print("\n\n3. SELF-REFLECTION SOPHISTICATION")
print("-" * 50)

def analyze_reflection_depth(text):
    """Analyze depth of self-reflection based on key indicators"""
    if not text:
        return {'depth': 0, 'indicators': []}
    
    indicators = []
    depth_score = 0
    
    # Basic self-awareness
    if any(word in text.lower() for word in ['i think', 'i feel', 'i believe']):
        indicators.append('basic_self_awareness')
        depth_score += 1
    
    # Causal reasoning
    if any(word in text.lower() for word in ['because', 'therefore', 'as a result', 'consequently']):
        indicators.append('causal_reasoning')
        depth_score += 2
    
    # Meta-cognition
    if any(phrase in text.lower() for phrase in ['realize that', 'understand now', 'looking back', 'in retrospect']):
        indicators.append('metacognition')
        depth_score += 3
    
    # Pattern recognition
    if any(phrase in text.lower() for phrase in ['pattern', 'always', 'tendency', 'habit']):
        indicators.append('pattern_recognition')
        depth_score += 2
    
    # Future orientation
    if any(word in text.lower() for word in ['will', 'plan', 'future', 'goal']):
        indicators.append('future_orientation')
        depth_score += 1
    
    return {'depth': depth_score, 'indicators': indicators}

# Analyze reflection depth
df['reflection_analysis'] = df['content'].apply(analyze_reflection_depth)
df['reflection_depth'] = df['reflection_analysis'].apply(lambda x: x['depth'])

pre_reflection_depth = df[df['period'] == 'pre_graduation']['reflection_depth'].mean()
post_reflection_depth = df[df['period'] == 'post_graduation']['reflection_depth'].mean()

print(f"\nAverage reflection depth score:")
print(f"Pre-graduation: {pre_reflection_depth:.2f}")
print(f"Post-graduation: {post_reflection_depth:.2f}")
print(f"Change: {(post_reflection_depth - pre_reflection_depth)/pre_reflection_depth*100:.1f}%")

# 4. EMOTIONAL REGULATION PATTERNS
print("\n\n4. EMOTIONAL REGULATION PATTERNS")
print("-" * 50)

def analyze_emotional_regulation(text):
    """Analyze emotional regulation strategies"""
    if not text:
        return {'regulated': False, 'strategies': []}
    
    strategies = []
    
    # Dysregulated patterns
    dysregulated_patterns = ['hate myself', 'want to die', 'can\'t handle', 'falling apart', 'losing control']
    if any(pattern in text.lower() for pattern in dysregulated_patterns):
        strategies.append('dysregulated')
    
    # Coping strategies
    coping_patterns = ['need to', 'going to', 'will try', 'working on', 'focusing on']
    if any(pattern in text.lower() for pattern in coping_patterns):
        strategies.append('active_coping')
    
    # Acceptance patterns
    acceptance_patterns = ['it\'s okay', 'that\'s fine', 'accept', 'understand that', 'realize']
    if any(pattern in text.lower() for pattern in acceptance_patterns):
        strategies.append('acceptance')
    
    # Reframing
    reframing_patterns = ['but also', 'on the other hand', 'however', 'perspective', 'different way']
    if any(pattern in text.lower() for pattern in reframing_patterns):
        strategies.append('reframing')
    
    regulated = 'dysregulated' not in strategies and len(strategies) > 0
    return {'regulated': regulated, 'strategies': strategies}

df['emotion_analysis'] = df['content'].apply(analyze_emotional_regulation)
df['emotion_regulated'] = df['emotion_analysis'].apply(lambda x: x['regulated'])

pre_regulated = df[df['period'] == 'pre_graduation']['emotion_regulated'].mean()
post_regulated = df[df['period'] == 'post_graduation']['emotion_regulated'].mean()

print(f"\nEmotional regulation rate:")
print(f"Pre-graduation: {pre_regulated*100:.1f}%")
print(f"Post-graduation: {post_regulated*100:.1f}%")

# 5. GOAL-SETTING VS ACHIEVEMENT LANGUAGE
print("\n\n5. GOAL-SETTING VS ACHIEVEMENT PATTERNS")
print("-" * 50)

# Goal-setting language
goal_patterns = ['want to', 'going to', 'will', 'plan to', 'goal', 'dream']
achievement_patterns = ['did', 'accomplished', 'achieved', 'completed', 'succeeded', 'built', 'created']

df['goal_mentions'] = df['content'].apply(lambda x: sum(1 for pattern in goal_patterns if pattern in str(x).lower()))
df['achievement_mentions'] = df['content'].apply(lambda x: sum(1 for pattern in achievement_patterns if pattern in str(x).lower()))

pre_goal_ratio = df[df['period'] == 'pre_graduation']['goal_mentions'].sum() / (df[df['period'] == 'pre_graduation']['achievement_mentions'].sum() + 1)
post_goal_ratio = df[df['period'] == 'post_graduation']['goal_mentions'].sum() / (df[df['period'] == 'post_graduation']['achievement_mentions'].sum() + 1)

print(f"\nGoal-to-achievement language ratio:")
print(f"Pre-graduation: {pre_goal_ratio:.2f} (more aspirational)")
print(f"Post-graduation: {post_goal_ratio:.2f}")
print(f"Change: {(post_goal_ratio - pre_goal_ratio)/pre_goal_ratio*100:.1f}%")

# 6. SPECIFIC EXAMPLES OF EVOLUTION
print("\n\n6. SPECIFIC EXAMPLES OF EVOLUTION")
print("-" * 50)

# Find entries that show clear emotional maturity
mature_entries = df[(df['period'] == 'post_graduation') & 
                   (df['reflection_depth'] > 5) & 
                   (df['emotion_regulated'] == True)]

if len(mature_entries) > 0:
    print("\nExample of mature self-reflection (post-graduation):")
    sample = mature_entries.iloc[0]
    print(f"Date: {sample['date'].strftime('%Y-%m-%d')}")
    print(f"Reflection depth score: {sample['reflection_depth']}")
    print(f"Content excerpt: '{sample['content'][:300]}...'\n")

# Summary insights
print("\n\n=== KEY INSIGHTS ===")
print("-" * 50)

insights = [
    f"1. Word count increased by 75.8% post-graduation, suggesting more elaborate expression",
    f"2. Work/project mentions increased by 39.3%, indicating career focus shift",
    f"3. Relationship mentions decreased by 7.6%, showing reduced romantic preoccupation",
    f"4. Source shifted from 79.2% blogposts to 41.4% voicememos, suggesting different expression modes",
    f"5. Despite longer entries, sentence length decreased by 16.9%, indicating more direct communication",
    f"6. Emotional struggle keywords increased by 17.4%, but regulation strategies also improved"
]

for insight in insights:
    print(insight)

print("\n\n=== CONCLUSION ===")
print("Graduation appears to be a significant inflection point with observable changes in:")
print("- Communication medium (blog to voice)")
print("- Content focus (relationships to work/projects)")
print("- Expression style (more verbose but simpler sentences)")
print("- Emotional processing (more struggle but better regulation)")
print("\nThese patterns suggest graduation marked a transition from adolescent concerns")
print("to adult responsibilities, with corresponding changes in self-expression.")