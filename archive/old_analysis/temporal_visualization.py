import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Load data
df = pd.read_csv('data/master_data.csv')
df['date'] = pd.to_datetime(df['date'])
graduation_date = pd.to_datetime('2018-05-31')
df['period'] = df['date'].apply(lambda x: 'pre_graduation' if x <= graduation_date else 'post_graduation')

# Create temporal analysis
df['year'] = df['date'].dt.year
df['year_quarter'] = df['date'].dt.to_period('Q')

# Set up the plot style
plt.style.use('default')
fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle('Temporal Analysis: Pre vs Post Graduation Patterns', fontsize=16)

# 1. Entry frequency over time
ax = axes[0, 0]
yearly_counts = df.groupby('year').size()
colors = ['coral' if year <= 2018 else 'skyblue' for year in yearly_counts.index]
yearly_counts.plot(kind='bar', ax=ax, color=colors)
ax.axvline(x=yearly_counts.index.get_loc(2018) + 0.5, color='red', linestyle='--', label='Graduation')
ax.set_title('Entry Frequency by Year')
ax.set_xlabel('Year')
ax.set_ylabel('Number of Entries')
ax.legend()

# 2. Average word count over time
ax = axes[0, 1]
yearly_wordcount = df.groupby('year')['word_count'].mean()
colors = ['coral' if year <= 2018 else 'skyblue' for year in yearly_wordcount.index]
yearly_wordcount.plot(kind='bar', ax=ax, color=colors)
ax.axvline(x=yearly_wordcount.index.get_loc(2018) + 0.5, color='red', linestyle='--', label='Graduation')
ax.set_title('Average Word Count by Year')
ax.set_xlabel('Year')
ax.set_ylabel('Average Words')
ax.legend()

# 3. Source type distribution
ax = axes[1, 0]
source_pivot = pd.crosstab(df['year'], df['source_type'])
source_pivot_pct = source_pivot.div(source_pivot.sum(axis=1), axis=0) * 100
source_pivot_pct.plot(kind='area', ax=ax, alpha=0.7)
ax.axvline(x=2018, color='red', linestyle='--', label='Graduation')
ax.set_title('Source Type Distribution Over Time (%)')
ax.set_xlabel('Year')
ax.set_ylabel('Percentage')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 4. Theme evolution
ax = axes[1, 1]
# Define and count themes
themes = {
    'relationships': ['love', 'girlfriend', 'boyfriend', 'relationship', 'dating', 'kiss'],
    'work_projects': ['work', 'project', 'job', 'career', 'business', 'goal'],
    'self_reflection': ['think', 'feel', 'realize', 'understand', 'learn', 'growth']
}

for theme, keywords in themes.items():
    df[f'{theme}_present'] = df['content'].fillna('').apply(
        lambda x: 1 if any(word in str(x).lower() for word in keywords) else 0
    )

theme_yearly = df.groupby('year')[['relationships_present', 'work_projects_present', 'self_reflection_present']].mean() * 100
theme_yearly.columns = ['Relationships', 'Work/Projects', 'Self-reflection']
theme_yearly.plot(ax=ax, marker='o')
ax.axvline(x=2018, color='red', linestyle='--', label='Graduation')
ax.set_title('Theme Prevalence Over Time')
ax.set_xlabel('Year')
ax.set_ylabel('% of Entries Mentioning Theme')
ax.legend()

# 5. Monthly patterns pre vs post graduation
ax = axes[2, 0]
df['month'] = df['date'].dt.month
monthly_pre = df[df['period'] == 'pre_graduation'].groupby('month').size()
monthly_post = df[df['period'] == 'post_graduation'].groupby('month').size()

x = np.arange(1, 13)
width = 0.35
ax.bar(x - width/2, monthly_pre.reindex(range(1, 13), fill_value=0), width, label='Pre-graduation', color='coral')
ax.bar(x + width/2, monthly_post.reindex(range(1, 13), fill_value=0), width, label='Post-graduation', color='skyblue')
ax.set_xlabel('Month')
ax.set_ylabel('Number of Entries')
ax.set_title('Seasonal Patterns: Pre vs Post Graduation')
ax.set_xticks(x)
ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
ax.legend()

# 6. Cumulative growth in themes
ax = axes[2, 1]
df_sorted = df.sort_values('date')
df_sorted['cumsum_work'] = df_sorted['work_projects_present'].cumsum()
df_sorted['cumsum_rel'] = df_sorted['relationships_present'].cumsum()

ax.plot(df_sorted['date'], df_sorted['cumsum_work'], label='Work/Projects', color='green')
ax.plot(df_sorted['date'], df_sorted['cumsum_rel'], label='Relationships', color='purple')
ax.axvline(x=graduation_date, color='red', linestyle='--', label='Graduation')
ax.set_title('Cumulative Theme Mentions Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Cumulative Mentions')
ax.legend()

plt.tight_layout()
plt.savefig('graduation_temporal_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a summary statistics table
print("\n=== TEMPORAL PATTERN SUMMARY ===")
print("-" * 50)

# Year-by-year statistics
yearly_stats = df.groupby(['year', 'period']).agg({
    'content_id': 'count',
    'word_count': 'mean'
}).round(1)

print("\nYear-by-year entry counts and average word counts:")
print(yearly_stats)

# Calculate the growth rate
pre_grad_years = df[df['period'] == 'pre_graduation']['year'].nunique()
post_grad_years = df[df['period'] == 'post_graduation']['year'].nunique()

pre_entries_per_year = len(df[df['period'] == 'pre_graduation']) / pre_grad_years
post_entries_per_year = len(df[df['period'] == 'post_graduation']) / post_grad_years

print(f"\n\nAverage entries per year:")
print(f"Pre-graduation: {pre_entries_per_year:.1f} entries/year")
print(f"Post-graduation: {post_entries_per_year:.1f} entries/year")
print(f"Change: {(post_entries_per_year - pre_entries_per_year)/pre_entries_per_year*100:.1f}% increase")

print("\n\nVisualization saved as 'graduation_temporal_analysis.png'")