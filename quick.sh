#!/bin/bash
# Gamma Agent - Quick Command (Using GitHub CLI)
# Usage: ./quick.sh "Your question here"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🤖 GAMMA AGENT${NC}"
echo ""

# Check if task is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Usage: ./quick.sh \"Your question\"${NC}"
    exit 1
fi

TASK="$1"

echo -e "${YELLOW}📋 Task: ${NC}$TASK"
echo ""
echo -e "${YELLOW}⏳ Sending to GitHub...${NC}"
echo ""

# Send via GitHub CLI
gh workflow run gamma-agent.yml -f task="$TASK" --repo infinityempire/gamma-agent

echo ""
echo -e "${GREEN}✅ Sent!${NC}"
echo -e "${YELLOW}📊 Check progress:${NC}"
echo "   https://github.com/infinityempire/gamma-agent/actions"
echo ""
echo -e "${YELLOW}📄 View responses:${NC}"
echo "   https://github.com/infinityempire/gamma-agent/tree/master/archive"