#!/usr/bin/env python3
"""
Audit Shopify Help Docs for Built-in Features using GPT-4o

Instructions:
1. Ensure you have Python 3, pandas, and openai installed (`pip install pandas openai`).
2. Set your OpenAI API key in the environment variable OPENAI_API_KEY.
3. Place this script in docs/audits/built-in-features/.
4. Run from the project root: `python3 docs/audits/built-in-features/audit_help_docs_gpt4o.py`
5. Results will be saved in docs/audits/built-in-features/results_gpt4o/ as markdown files.
"""
import os
import glob
import pandas as pd
import re
from pathlib import Path
import time

# Retrieve API key and base URL from environment
api_key = os.environ.get('OPENAI_API_KEY')
base_url = os.environ.get('OPENAI_BASE_URL')
if not api_key:
    print("[ERROR] Please set your OpenAI API key in the OPENAI_API_KEY environment variable.")
    exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url)

# Config
CSV_PATH = 'docs/audits/built-in-features/Built in feature scraping - clean up.csv'
DOC_DIRS = ['content/pages/en/manual']  # Only scan English manual content files
RESULTS_DIR = 'docs/audits/built-in-features/results_gpt4o'
MODEL = 'gpt-4o'
MAX_TOKENS = 8000  # GPT-4o context window is 128k, but be conservative for prompt+response
BATCH_SLEEP = 2    # seconds between API calls to avoid rate limits

PROMPT_TEMPLATE = '''\
You are an expert technical writer for Shopify. Here is the official description and limitations of the Shopify built-in feature "{feature_name}":

---
{csv_feature_text}
---

Here is the help documentation content:

---
{doc_text}
---

Please answer the following:
1. Does the documentation clearly identify this as a built-in feature?
2. Does it accurately describe the feature's scope and limitations?
3. Is the information up-to-date and consistent with the CSV?
4. Are there any gaps or missing features compared to the CSV?
5. Does it provide guidance on when to use the Shopify App Store?
6. If apps are referenced, are they official Shopify apps? If not, is there a link to the relevant App Store category?
7. Other notes or recommendations for improvement.
'''

CHECKLIST_HEADER = '# Documentation Audit (GPT-4o): {feature_name}\n\n**Feature URL:** {feature_url}\n\n## Files referencing this feature:\n\n'
FILE_SUMMARY_HEADER = '### File: `{file_path}`\n\n'

# Utility functions
def safe_makedirs(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def read_markdown_files():
    files = []
    for doc_dir in DOC_DIRS:
        for root, dirs, filenames in os.walk(doc_dir):
            # Only check index.md first
            index_path = os.path.join(root, 'index.md')
            if os.path.exists(index_path):
                files.append((root, index_path, filenames))
    return files

def extract_features_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    features = []
    for _, row in df.iterrows():
        url = row['URL']
        name = row['Cleaned up'].split('\n')[0].strip().split('–')[0].split('-')[0].strip()
        slug = url.split('/')[-1]
        csv_text = row['Cleaned up']
        features.append({'name': name, 'slug': slug, 'url': url, 'csv_text': csv_text})
    return features

def count_tokens(text):
    # Rough estimate: 1 token ≈ 4 chars in English
    return len(text) // 4

def call_gpt4o(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        return f"[ERROR] OpenAI API call failed: {e}"

def main():
    safe_makedirs(RESULTS_DIR)
    features = extract_features_from_csv(CSV_PATH)
    md_files = read_markdown_files()

    for feature in features:
        file_summaries = ''
        for root, index_path, filenames in read_markdown_files():
            # Check index.md for a match
            try:
                with open(index_path, encoding='utf-8') as f:
                    index_content = f.read()
            except Exception as e:
                print(f"[WARN] Could not read {index_path}: {e}")
                continue
            # Match by feature name or slug in index.md
            if (re.search(r'\b' + re.escape(feature['name'].lower()) + r'\b', index_content.lower()) or
                re.search(r'\b' + re.escape(feature['slug'].replace('-', ' ')) + r'\b', index_content.lower()) or
                feature['slug'] in index_content.lower()):
                # If index.md matches, process all .md files in this directory
                for fname in filenames:
                    if fname.endswith('.md'):
                        md_file = os.path.join(root, fname)
                        try:
                            with open(md_file, encoding='utf-8') as f:
                                content = f.read()
                        except Exception as e:
                            print(f"[WARN] Could not read {md_file}: {e}")
                            continue
                        # Check context window
                        prompt = PROMPT_TEMPLATE.format(
                            feature_name=feature['name'],
                            csv_feature_text=feature['csv_text'],
                            doc_text=content[:20000]  # Truncate to avoid huge docs
                        )
                        if count_tokens(prompt) > MAX_TOKENS:
                            print(f"[WARN] Skipping {md_file} for {feature['name']} (prompt too long)")
                            continue
                        print(f"[INFO] Auditing {md_file} for feature {feature['name']}...")
                        llm_response = call_gpt4o(prompt)
                        file_summaries += FILE_SUMMARY_HEADER.format(file_path=md_file) + llm_response + '\n\n'
                        time.sleep(BATCH_SLEEP)
            else:
                print(f"[INFO] Skipping directory {root} for feature {feature['name']} (index.md not a match)")
        if file_summaries:
            out_path = os.path.join(RESULTS_DIR, f"{feature['slug']}-audit-gpt4o.md")
            with open(out_path, 'w', encoding='utf-8') as out:
                out.write(CHECKLIST_HEADER.format(
                    feature_name=feature['name'],
                    feature_url=feature['url']
                ))
                out.write(file_summaries)

if __name__ == '__main__':
    main() 
