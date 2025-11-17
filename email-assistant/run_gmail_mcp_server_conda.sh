#!/bin/bash

set -e

source /Users/ivamilojkovic/opt/anaconda3/etc/profile.d/conda.sh

conda activate venv-mcp-gmail
python /Users/ivamilojkovic/Projects/ai-personal-assistant/email-assistant/mcp-gmail/mcp_gmail/server.py

set +e
