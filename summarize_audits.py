#!/usr/bin/env python3
"""
Summarize GPT-4o Audit Reports

Instructions:
1. Ensure the audit script (`audit_help_docs_gpt4o.py`) has been run and results exist.
2. Ensure you have Python 3, pandas, and openai installed (`pip install pandas openai`).
3. Set your OpenAI API key in the environment variable OPENAI_API_KEY.
4. Run from the project root: `python3 docs/audits/built-in-features/summarize_audits.py`
5. The summaries will be prepended to the top of each audit file in `results_gpt4o/`.
"""
import os
import glob
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
AUDIT_DIR = 'docs/audits/built-in-features/results_gpt4o'
MODEL = 'gpt-4o'
# Increased MAX_TOKENS to better fit gpt-4o's large context window.
MAX_TOKENS = 120000 
BATCH_SLEEP = 2

SUMMARY_PROMPT_TEMPLATE = '''\
You are a senior technical writer at Shopify, tasked with creating an actionable summary from a documentation audit report.

Below is a raw audit report for a specific feature. Please synthesize this information into a concise, high-level summary.

Your summary should contain:
1.  **Overall Summary:** Briefly describe the most common issues found across all reviewed docs for this feature (e.g., "Lack of clarity on built-in status," "Missing details on limitations," etc.).
2.  **Files to Update:** A clear list of the file paths that require changes.
3.  **Recommended Changes:** For each file listed, provide specific, actionable recommendations for improvement.

---
{audit_content}
---

Please provide the summary in markdown format.
'''

CHUNK_SUMMARY_PROMPT_TEMPLATE = '''\
You are an expert technical writer at Shopify. Below is a portion of a larger documentation audit report. Please summarize the key findings and recommended changes from this chunk.

---
{chunk_content}
---

Provide a concise summary of the issues and recommendations in this chunk.
'''

FINAL_SUMMARY_PROMPT_TEMPLATE = '''\
You are a senior technical writer at Shopify. Below are several partial summaries from a large documentation audit report. Please synthesize them into a single, high-level, actionable summary.

Your final summary should contain:
1.  **Overall Summary:** Briefly describe the most common issues found across all reviewed docs.
2.  **Files to Update:** A clear list of the file paths that require changes.
3.  **Recommended Changes:** For each file listed, provide specific, actionable recommendations for improvement.

---
{all_chunk_summaries}
---

Please provide the final, consolidated summary in markdown format.
'''

def call_gpt4o(prompt, max_response_tokens=2048):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_response_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        return f"[ERROR] OpenAI API call failed: {e}"

def count_tokens(text):
    return len(text) // 4 # Rough estimate

def summarize_in_chunks(audit_content):
    print("[INFO] Content is too long for a single call. Summarizing in chunks...")
    # Split the audit content by individual file reviews
    chunks = audit_content.split('### File:')
    file_reviews = ['### File:' + chunk for chunk in chunks[1:]]

    chunk_summaries = []
    current_chunk = ""

    for review in file_reviews:
        # If adding the next review exceeds the context window, process the current chunk
        if count_tokens(current_chunk + review) > (MAX_TOKENS - 2000): # leave room for prompt and response
            if current_chunk:
                prompt = CHUNK_SUMMARY_PROMPT_TEMPLATE.format(chunk_content=current_chunk)
                summary = call_gpt4o(prompt)
                chunk_summaries.append(summary)
                print(f"[INFO] Summarized a chunk of {count_tokens(current_chunk)} tokens.")
                time.sleep(BATCH_SLEEP)
            current_chunk = review
        else:
            current_chunk += review
    
    # Process the last remaining chunk
    if current_chunk:
        prompt = CHUNK_SUMMARY_PROMPT_TEMPLATE.format(chunk_content=current_chunk)
        summary = call_gpt4o(prompt)
        chunk_summaries.append(summary)
        print(f"[INFO] Summarized the final chunk of {count_tokens(current_chunk)} tokens.")
        time.sleep(BATCH_SLEEP)

    all_summaries = "\n\n---\n\n".join(chunk_summaries)
    
    # Final summarization step
    print("[INFO] Creating final summary from chunks...")
    final_prompt = FINAL_SUMMARY_PROMPT_TEMPLATE.format(all_chunk_summaries=all_summaries)
    final_summary = call_gpt4o(final_prompt, max_response_tokens=4096)
    return final_summary

def main():
    audit_files = glob.glob(os.path.join(AUDIT_DIR, '*-audit-gpt4o.md'))

    for audit_file in audit_files:
        print(f"[INFO] Summarizing {audit_file}...")
        try:
            with open(audit_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            print(f"[WARN] Could not read {audit_file}: {e}")
            continue

        if original_content.startswith('# Actionable Summary'):
            print(f"[INFO] Skipping {audit_file}, summary already exists.")
            continue
        
        prompt = SUMMARY_PROMPT_TEMPLATE.format(audit_content=original_content)
        if count_tokens(prompt) > MAX_TOKENS:
            summary = summarize_in_chunks(original_content)
        else:
            summary = call_gpt4o(prompt)

        new_content = f"# Actionable Summary\n\n{summary}\n\n---\n\n{original_content}"

        try:
            with open(audit_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"[INFO] Successfully added summary to {audit_file}")
        except Exception as e:
            print(f"[ERROR] Could not write summary to {audit_file}: {e}")

        time.sleep(BATCH_SLEEP)

if __name__ == '__main__':
    main() 
