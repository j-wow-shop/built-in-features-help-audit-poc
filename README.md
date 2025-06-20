# Shopify Help Documentation Audit: Built-in Features

This repository contains an audit of the Shopify help documentation, focusing on how built-in features are presented to merchants. The goal is to ensure clarity, accuracy, and consistency in the documentation.

## Overview

The audit identifies whether help documentation clearly communicates:
- What features are included with a Shopify subscription.
- The scope and limitations of these built-in features.
- When merchants should use the Shopify App Store for additional functionality.
- That only official Shopify apps are referenced directly.

The audit was conducted using a series of Python scripts that leverage the OpenAI GPT-4o API to analyze documentation at scale and provide actionable recommendations.

## Directory Structure

- **`results_gpt4o/`**: Contains the final, detailed audit reports for each built-in feature. Each file includes a high-level summary and a breakdown of the analysis for every relevant help doc.
- **`audit_help_docs_gpt4o.py`**: The primary script that scans help documentation and uses GPT-4o to generate the initial audit reports.
- **`summarize_audits.py`**: A helper script that reads the raw audit reports and uses GPT-4o to generate the actionable summaries at the top of each file.
- **`Built in feature scraping - clean up.csv`**: The source data containing the list of built-in features, their descriptions, and limitations.
- **`built-in-features-audit-context.md`**: The initial audit plan and context file.
- **`built-in-features-doc-review-template.md`**: The manual review checklist template.

## How to Use the Scripts

To re-run or update the audit, you can use the provided Python scripts.

### Prerequisites

- Python 3
- A Python virtual environment (`.venv` is recommended)
- Required packages: `pandas`, `openai`
- An OpenAI API key with access to GPT-4o

### 1. Initial Audit Script

This script scans the help documentation and generates the raw audit reports.

**Instructions:**
1.  Install dependencies: `pip install pandas openai`
2.  Set your environment variables for your API key and base URL:
    ```sh
    export OPENAI_API_KEY="your-key-here"
    export OPENAI_BASE_URL="your-base-url-here"
    ```
3.  Run the script from the project root:
    ```sh
    python3 audit_help_docs_gpt4o.py
    ```

### 2. Summarization Script

This script reads the raw reports and adds the high-level, actionable summaries.

**Instructions:**
1.  Ensure the initial audit has been run.
2.  Set your environment variables (if not already set in your session).
3.  Run the script from the project root:
    ```sh
    python3 summarize_audits.py
    ```

## Contributing

You can contribute to this audit by:
- Reviewing the generated reports and validating the findings.
- Creating GitHub Issues to track remediation work for specific documentation files.
- Updating the scripts to improve the analysis or reporting. 
