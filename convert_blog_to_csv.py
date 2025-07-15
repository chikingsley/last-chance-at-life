#!/usr/bin/env python3
import json
import csv
import html
from datetime import datetime
from bs4 import BeautifulSoup

def clean_html_content(html_text):
    """Remove HTML tags and decode HTML entities"""
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()
    # Clean up extra whitespace
    text = ' '.join(text.split())
    return text

def extract_blog_data(json_file):
    """Extract relevant fields from blog JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = []
    entries = data.get('feed', {}).get('entry', [])
    
    for entry in entries:
        post = {
            'title': entry.get('title', ''),
            'published_date': entry.get('published', ''),
            'content': clean_html_content(entry.get('content', {}).get('__text', ''))
        }
        
        # Convert date to more readable format
        if post['published_date']:
            try:
                dt = datetime.fromisoformat(post['published_date'].replace('Z', '+00:00'))
                post['published_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass  # Keep original if parsing fails
        
        posts.append(post)
    
    return posts

def save_to_csv(posts, output_file):
    """Save posts to CSV file"""
    if not posts:
        print("No posts found!")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'published_date', 'content'])
        writer.writeheader()
        writer.writerows(posts)
    
    print(f"Successfully converted {len(posts)} posts to {output_file}")

if __name__ == "__main__":
    json_file = "still haven_t figured this shit out yet.json"
    output_file = "blog_posts_analysis.csv"
    
    posts = extract_blog_data(json_file)
    save_to_csv(posts, output_file)