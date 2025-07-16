import pandas as pd
import numpy as np
from datetime import datetime
import re
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

# Load the data
df = pd.read_csv('data/master_data.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Define graduation date (May 2018)
graduation_date = pd.to_datetime('2018-05-31')

# Create pre/post graduation flag
df['period'] = df['date'].apply(lambda x: 'pre_graduation' if x <= graduation_date else 'post_graduation')

# Clean content column - handle NaN values
df['content'] = df['content'].fillna('')

print("=== GRADUATION IMPACT ANALYSIS ===")
print(f"\nTotal entries: {len(df)}")
print(f"Pre-graduation entries: {sum(df['period'] == 'pre_graduation')} ({sum(df['period'] == 'pre_graduation')/len(df)*100:.1f}%)")
print(f"Post-graduation entries: {sum(df['period'] == 'post_graduation')} ({sum(df['period'] == 'post_graduation')/len(df)*100:.1f}%)")

# 1. QUANTITATIVE ANALYSIS

print("\n\n=== 1. QUANTITATIVE PATTERNS ===")

# Word count analysis
pre_grad_word_count = df[df['period'] == 'pre_graduation']['word_count'].mean()
post_grad_word_count = df[df['period'] == 'post_graduation']['word_count'].mean()

print(f"\nAverage word count:")
print(f"Pre-graduation: {pre_grad_word_count:.1f} words")
print(f"Post-graduation: {post_grad_word_count:.1f} words")
print(f"Change: {(post_grad_word_count - pre_grad_word_count)/pre_grad_word_count*100:.1f}%")

# Entry frequency over time
df['year_month'] = df['date'].dt.to_period('M')
monthly_counts = df.groupby(['year_month', 'period']).size().reset_index(name='count')

# Source type distribution
source_dist = pd.crosstab(df['source_type'], df['period'], normalize='columns') * 100
print("\n\nSource type distribution (%):")
print(source_dist.round(1))

# 2. THEME ANALYSIS

print("\n\n=== 2. THEMATIC ANALYSIS ===")

# Define theme keywords
themes = {
    'relationships': ['love', 'girlfriend', 'boyfriend', 'relationship', 'dating', 'kiss', 'hug', 'miss you', 'like you', 'cute', 'beautiful', 'feelings', 'heart', 'crush'],
    'work_projects': ['work', 'project', 'job', 'career', 'business', 'goal', 'success', 'money', 'startup', 'company', 'build', 'create', 'launch'],
    'self_reflection': ['think', 'feel', 'realize', 'understand', 'learn', 'growth', 'change', 'myself', 'identity', 'purpose', 'meaning', 'life'],
    'emotional_struggle': ['sad', 'depressed', 'anxiety', 'stress', 'cry', 'hate', 'angry', 'frustrated', 'pain', 'hurt', 'fail', 'mistake', 'regret'],
    'achievement': ['success', 'accomplish', 'achieve', 'win', 'proud', 'complete', 'finish', 'best', 'improve', 'progress']
}

# Calculate theme frequencies
def count_theme_words(text, theme_words):
    if pd.isna(text):
        return 0
    text_lower = text.lower()
    count = sum(1 for word in theme_words if word in text_lower)
    return count

theme_results = {}
for theme, keywords in themes.items():
    df[f'{theme}_count'] = df['content'].apply(lambda x: count_theme_words(x, keywords))
    
    pre_avg = df[df['period'] == 'pre_graduation'][f'{theme}_count'].mean()
    post_avg = df[df['period'] == 'post_graduation'][f'{theme}_count'].mean()
    
    theme_results[theme] = {
        'pre_graduation': pre_avg,
        'post_graduation': post_avg,
        'change_pct': (post_avg - pre_avg) / pre_avg * 100 if pre_avg > 0 else 0
    }

print("\nTheme frequency (avg keywords per entry):")
for theme, results in theme_results.items():
    print(f"\n{theme.upper()}:")
    print(f"  Pre-graduation: {results['pre_graduation']:.2f}")
    print(f"  Post-graduation: {results['post_graduation']:.2f}")
    print(f"  Change: {results['change_pct']:.1f}%")

# 3. SENTIMENT ANALYSIS

print("\n\n=== 3. SENTIMENT ANALYSIS ===")

def get_sentiment(text):
    if pd.isna(text) or text == '':
        return 0
    try:
        blob = TextBlob(str(text))
        return blob.sentiment.polarity
    except:
        return 0

df['sentiment'] = df['content'].apply(get_sentiment)

pre_sentiment = df[df['period'] == 'pre_graduation']['sentiment'].mean()
post_sentiment = df[df['period'] == 'post_graduation']['sentiment'].mean()

print(f"\nAverage sentiment (polarity -1 to 1):")
print(f"Pre-graduation: {pre_sentiment:.3f}")
print(f"Post-graduation: {post_sentiment:.3f}")
print(f"Change: {(post_sentiment - pre_sentiment):.3f}")

# 4. LANGUAGE SOPHISTICATION

print("\n\n=== 4. LANGUAGE SOPHISTICATION ===")

# Average sentence length
def avg_sentence_length(text):
    if pd.isna(text) or text == '':
        return 0
    sentences = re.split('[.!?]+', str(text))
    sentences = [s for s in sentences if len(s.strip()) > 0]
    if not sentences:
        return 0
    word_counts = [len(s.split()) for s in sentences]
    return np.mean(word_counts)

df['avg_sentence_length'] = df['content'].apply(avg_sentence_length)

pre_sent_length = df[df['period'] == 'pre_graduation']['avg_sentence_length'].mean()
post_sent_length = df[df['period'] == 'post_graduation']['avg_sentence_length'].mean()

print(f"\nAverage sentence length:")
print(f"Pre-graduation: {pre_sent_length:.1f} words")
print(f"Post-graduation: {post_sent_length:.1f} words")
print(f"Change: {(post_sent_length - pre_sent_length)/pre_sent_length*100:.1f}%")

# 5. SPECIFIC PATTERN ANALYSIS

print("\n\n=== 5. SPECIFIC BEHAVIORAL PATTERNS ===")

# Relationship language evolution
relationship_words_pre = []
relationship_words_post = []

for _, row in df.iterrows():
    if row['content'] and any(word in str(row['content']).lower() for word in themes['relationships']):
        if row['period'] == 'pre_graduation':
            relationship_words_pre.append(row['content'])
        else:
            relationship_words_post.append(row['content'])

print(f"\nEntries mentioning relationships:")
print(f"Pre-graduation: {len(relationship_words_pre)} ({len(relationship_words_pre)/sum(df['period']=='pre_graduation')*100:.1f}%)")
print(f"Post-graduation: {len(relationship_words_post)} ({len(relationship_words_post)/sum(df['period']=='post_graduation')*100:.1f}%)")

# Work/project persistence
work_entries_pre = df[(df['period'] == 'pre_graduation') & (df['work_projects_count'] > 0)]
work_entries_post = df[(df['period'] == 'post_graduation') & (df['work_projects_count'] > 0)]

print(f"\nWork/project mentions:")
print(f"Pre-graduation: {len(work_entries_pre)} entries")
print(f"Post-graduation: {len(work_entries_post)} entries")

# 6. TESTABLE HYPOTHESES

print("\n\n=== 6. TESTABLE HYPOTHESES WITH EVIDENCE ===")

hypotheses = []

# Hypothesis 1: Relationship focus
if theme_results['relationships']['change_pct'] < -20:
    hypotheses.append({
        'hypothesis': 'Post-graduation shows decreased focus on romantic relationships',
        'evidence': f"Relationship keywords decreased by {theme_results['relationships']['change_pct']:.1f}%",
        'interpretation': 'Shift from adolescent relationship concerns to other life priorities'
    })

# Hypothesis 2: Work/career focus
if theme_results['work_projects']['change_pct'] > 20:
    hypotheses.append({
        'hypothesis': 'Post-graduation shows increased career/project orientation',
        'evidence': f"Work/project keywords increased by {theme_results['work_projects']['change_pct']:.1f}%",
        'interpretation': 'Natural transition to professional life focus'
    })

# Hypothesis 3: Emotional maturity
if post_sentiment > pre_sentiment:
    hypotheses.append({
        'hypothesis': 'Post-graduation shows improved emotional regulation',
        'evidence': f"Sentiment improved from {pre_sentiment:.3f} to {post_sentiment:.3f}",
        'interpretation': 'Potential emotional maturation and better coping strategies'
    })

# Hypothesis 4: Communication complexity
if post_sent_length > pre_sent_length:
    hypotheses.append({
        'hypothesis': 'Post-graduation shows more complex thought expression',
        'evidence': f"Sentence length increased by {(post_sent_length - pre_sent_length)/pre_sent_length*100:.1f}%",
        'interpretation': 'Cognitive development and communication sophistication'
    })

# Hypothesis 5: Self-reflection depth
if theme_results['self_reflection']['change_pct'] > 0:
    hypotheses.append({
        'hypothesis': 'Post-graduation shows deeper self-reflection',
        'evidence': f"Self-reflection keywords changed by {theme_results['self_reflection']['change_pct']:.1f}%",
        'interpretation': 'Increased introspection and self-awareness'
    })

for i, hyp in enumerate(hypotheses, 1):
    print(f"\nHypothesis {i}: {hyp['hypothesis']}")
    print(f"Evidence: {hyp['evidence']}")
    print(f"Interpretation: {hyp['interpretation']}")

# 7. STATISTICAL SIGNIFICANCE

print("\n\n=== 7. STATISTICAL TESTS ===")

from scipy import stats

# T-test for word count difference
t_stat_words, p_val_words = stats.ttest_ind(
    df[df['period'] == 'pre_graduation']['word_count'].dropna(),
    df[df['period'] == 'post_graduation']['word_count'].dropna()
)
print(f"\nWord count difference t-test: p-value = {p_val_words:.4f}")

# T-test for sentiment difference
t_stat_sent, p_val_sent = stats.ttest_ind(
    df[df['period'] == 'pre_graduation']['sentiment'].dropna(),
    df[df['period'] == 'post_graduation']['sentiment'].dropna()
)
print(f"Sentiment difference t-test: p-value = {p_val_sent:.4f}")

# Save detailed results
results_df = df[['date', 'period', 'word_count', 'sentiment'] + [f'{theme}_count' for theme in themes.keys()]]
results_df.to_csv('graduation_impact_results.csv', index=False)

print("\n\nAnalysis complete. Results saved to graduation_impact_results.csv")