#!/bin/bash
# Gamma Agent - Send Command Script
# Usage: ./send_command.sh "Your question here"

set -e

# Configuration
REPO="infinityempire/gamma-agent"
BRANCH="master"
COMMANDS_DIR="commands"
COMMAND_FILE="command_$(date +%s).txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              GAMMA AGENT - COMMAND SENDER                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if task is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: No task provided!${NC}"
    echo ""
    echo "Usage: ./send_command.sh \"Your question here\""
    echo ""
    echo "Example: ./send_command.sh \"Who are the prime ministers of Israel?\""
    exit 1
fi

TASK="$1"

echo -e "${YELLOW}📋 Task:${NC} $TASK"
echo ""

# Clone repo
echo -e "${YELLOW}🔄 Connecting to GitHub...${NC}"
git clone https://github.com/$REPO.git /tmp/gamma-agent 2>/dev/null || {
    echo -e "${YELLOW}📁 Repo already exists, pulling latest...${NC}"
    git pull
}


# Create commands folder if not exists
mkdir -p $COMMANDS_DIR

# Create command file
echo "$TASK" > "$COMMANDS_DIR/$COMMAND_FILE"

echo -e "${GREEN}✅ Command file created: $COMMANDS_DIR/$COMMAND_FILE${NC}"
echo -e "${GREEN}📤 Pushing to GitHub...${NC}"

# Commit and push
git add $COMMANDS_DIR/
git commit -m "🤖 New command: ${TASK:0:50}..."
git push origin $BRANCH

echo ""
echo -e "${GREEN}✅ Command sent successfully!${NC}"
echo ""
echo -e "${YELLOW}⏳ Gamma Agent will pick it up automatically...${NC}"
echo ""
echo -e "${YELLOW}📊 Check progress at:${NC}"
echo "   https://github.com/$REPO/actions"
echo ""
echo -e "${YELLOW}📁 Commands will be archived in:${NC}"
echo "   https://github.com/$REPO/tree/master/archive"
echo ""

# Cleanup
cd /
rm -rf /tmp/gamma-agent