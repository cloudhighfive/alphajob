#!/bin/bash

# Quick Setup Script for Resume Tailoring System
# This script helps you get started quickly

echo "=================================="
echo "  Resume Tailoring Quick Setup"
echo "=================================="
echo ""

# Step 1: Check Python
echo "Step 1: Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi
python_version=$(python3 --version)
echo "✅ Found: $python_version"
echo ""

# Step 2: Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Step 2: Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "Step 2: Virtual environment already exists"
fi
echo ""

# Step 3: Activate and install dependencies
echo "Step 3: Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Step 4: Check for API keys
echo "Step 4: Checking AI configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp .env.example .env
    echo "✅ Created .env file - PLEASE EDIT IT WITH YOUR API KEYS"
    echo ""
    echo "📝 To use Claude (RECOMMENDED):"
    echo "   1. Get API key from: https://console.anthropic.com/"
    echo "   2. Add to .env: ANTHROPIC_API_KEY=your_key_here"
    echo ""
    echo "📝 To use OpenAI GPT-4:"
    echo "   1. Get API key from: https://platform.openai.com/api-keys"
    echo "   2. Add to .env: OPENAI_API_KEY=your_key_here"
    echo ""
    echo "📝 To use free Ollama (no API key needed):"
    echo "   1. Install Ollama: https://ollama.ai/"
    echo "   2. Run: ollama pull llama3.1"
    echo "   3. Set model in config.json to 'llama3.1'"
    echo ""
else
    if grep -q "your_anthropic_api_key_here" .env || grep -q "your_openai_api_key_here" .env; then
        echo "⚠️  .env file exists but API keys not set"
        echo "   Edit .env and add your API keys"
    else
        echo "✅ .env file configured"
    fi
fi
echo ""

# Step 5: Check resume file
echo "Step 5: Checking resume file..."
if [ ! -f "resumes/original/Julian_Thomas.docx" ]; then
    echo "⚠️  Original resume not found"
    echo "   Place your resume at: resumes/original/Your_Name.docx"
    echo "   Update path in config.json"
else
    echo "✅ Resume file found"
fi
echo ""

# Step 6: Install AI packages if API keys exist
if [ -f ".env" ]; then
    if grep -q "ANTHROPIC_API_KEY" .env && ! grep -q "your_anthropic_api_key_here" .env; then
        echo "Step 6: Installing Anthropic package..."
        pip install anthropic --quiet
        echo "✅ Anthropic package installed"
    fi
    
    if grep -q "OPENAI_API_KEY" .env && ! grep -q "your_openai_api_key_here" .env; then
        echo "Step 6: Installing OpenAI package..."
        pip install openai --quiet
        echo "✅ OpenAI package installed"
    fi
fi
echo ""

# Summary
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure AI Model:"
echo "   • For Claude (RECOMMENDED): Add ANTHROPIC_API_KEY to .env"
echo "   • For GPT-4: Add OPENAI_API_KEY to .env"
echo "   • For Ollama: Run 'ollama pull llama3.1'"
echo ""
echo "2. Update config.json:"
echo "   • Set 'model' to your chosen AI model"
echo "   • Update 'original_resume_path' with your resume"
echo ""
echo "3. Test the system:"
echo "   python test_resume_tailoring.py"
echo ""
echo "4. Run the full system:"
echo "   python main.py"
echo ""
echo "📚 Read RESUME_SETUP.md for detailed documentation"
echo ""
