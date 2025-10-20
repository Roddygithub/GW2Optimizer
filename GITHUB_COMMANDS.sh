#!/bin/bash

# 🚀 GW2Optimizer v1.1.0 - GitHub Publication Commands
# Execute these commands to publish to GitHub

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  GW2Optimizer v1.1.0 - GitHub Publication                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Add GitHub remote${NC}"
echo "git remote add origin https://github.com/Roddygithub/GW2Optimizer.git"
echo ""

echo -e "${BLUE}Step 2: Push main branch${NC}"
echo "git push -u origin main"
echo ""

echo -e "${BLUE}Step 3: Push tag v1.1.0${NC}"
echo "git push origin v1.1.0"
echo ""

echo -e "${YELLOW}After pushing, create the GitHub release:${NC}"
echo "1. Go to: https://github.com/Roddygithub/GW2Optimizer/releases"
echo "2. Click 'Draft a new release'"
echo "3. Select tag: v1.1.0"
echo "4. Title: GW2Optimizer v1.1.0 - Meta Analysis System"
echo "5. Copy description from GITHUB_RELEASE_GUIDE.md"
echo "6. Attach files from release/v1.1.0/"
echo "7. Click 'Publish release'"
echo ""

echo -e "${GREEN}Repository URL: https://github.com/Roddygithub/GW2Optimizer$\{NC\}"
echo ""

# Prompt user
read -p "Do you want to execute these commands now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${BLUE}Adding remote...${NC}"
    git remote add origin https://github.com/Roddygithub/GW2Optimizer.git
    
    echo -e "${BLUE}Pushing main branch...${NC}"
    git push -u origin main
    
    echo -e "${BLUE}Pushing tag v1.1.0...${NC}"
    git push origin v1.1.0
    
    echo -e "${GREEN}✅ Done! Now create the release on GitHub.${NC}"
    echo -e "${GREEN}Visit: https://github.com/Roddygithub/GW2Optimizer/releases/new$\{NC\}"
else
    echo "Commands not executed. Run them manually when ready."
fi
