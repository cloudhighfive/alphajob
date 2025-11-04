#!/bin/bash

echo "🔍 Verifying AI Job Bidder Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "1. Checking Python..."
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version)
    echo -e "   ${GREEN}✓${NC} Python found: $VERSION"
else
    echo -e "   ${RED}✗${NC} Python not found"
fi

# Check virtual environment
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo -e "   ${GREEN}✓${NC} Virtual environment exists"
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo -e "   ${GREEN}✓${NC} Virtual environment is activated"
    else
        echo -e "   ${YELLOW}⚠${NC} Virtual environment exists but not activated"
        echo "      Run: source venv/bin/activate"
    fi
else
    echo -e "   ${RED}✗${NC} Virtual environment not found"
fi

# Check config
echo "3. Checking configuration..."
if [ -f "config.json" ]; then
    echo -e "   ${GREEN}✓${NC} config.json exists"
else
    echo -e "   ${RED}✗${NC} config.json not found"
    echo "      Run: cp config.json.example config.json"
fi

# Check Ollama
echo "4. Checking Ollama..."
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Ollama is running"
else
    echo -e "   ${YELLOW}⚠${NC} Ollama not responding"
    echo "      Run: ollama serve"
fi

# Check directory structure
echo "5. Checking directory structure..."
DIRS=("src" "data" "scripts" "tests" "resumes")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✓${NC} $dir/ exists"
    else
        echo -e "   ${RED}✗${NC} $dir/ missing"
    fi
done

# Check data organization
echo "6. Checking data organization..."
echo "   Screenshots: $(find data/screenshots -name "*.png" 2>/dev/null | wc -l | tr -d ' ') files"
echo "   Applications: $(find data/applications -name "*.json" 2>/dev/null | wc -l | tr -d ' ') files"
echo "   Debug files: $(find data/debug -name "*" -type f 2>/dev/null | wc -l | tr -d ' ') files"

# Check key files
echo "7. Checking key files..."
KEY_FILES=("ai_job_bidder.py" "main.py" "requirements.txt" "README.md" "QUICKSTART.md")
for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
    else
        echo -e "   ${RED}✗${NC} $file missing"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Setup Status:"

# Count checks
TOTAL=7
PASSED=0

if command -v python3 &> /dev/null; then ((PASSED++)); fi
if [ -d "venv" ]; then ((PASSED++)); fi
if [ -f "config.json" ]; then ((PASSED++)); fi
if curl -s http://localhost:11434/api/tags &> /dev/null; then ((PASSED++)); fi
if [ -d "src" ] && [ -d "data" ] && [ -d "scripts" ]; then ((PASSED++)); fi
if [ -f "ai_job_bidder.py" ] && [ -f "main.py" ]; then ((PASSED++)); fi
if [ -f "README.md" ]; then ((PASSED++)); fi

if [ $PASSED -eq $TOTAL ]; then
    echo -e "${GREEN}✓ All checks passed! ($PASSED/$TOTAL)${NC}"
    echo ""
    echo "🚀 Ready to run:"
    echo "   python ai_job_bidder.py    # Full featured (recommended)"
    echo "   python main.py             # New architecture (demo)"
else
    echo -e "${YELLOW}⚠ Setup partially complete ($PASSED/$TOTAL)${NC}"
    echo ""
    echo "📖 See QUICKSTART.md for setup instructions"
fi

echo ""
