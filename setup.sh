#!/bin/bash
# Test script to verify all required files exist

cd /Users/rohanmorris/PycharmProjects/AiChat2

echo "═══════════════════════════════════════════════════════════"
echo "✓ Checking Project Setup"
echo "═══════════════════════════════════════════════════════════"

echo ""
echo "📁 Current directory:"
pwd

echo ""
echo "📋 Python files in project:"
ls -1 *.py 2>/dev/null || echo "❌ No .py files found!"

echo ""
echo "📄 Data files:"
ls -1 data.txt .env 2>/dev/null || echo "⚠️  Missing data.txt or .env"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🔍 Checking Python packages:"
echo "═══════════════════════════════════════════════════════════"

python -c "import streamlit; print('✅ streamlit installed')" 2>/dev/null || echo "❌ streamlit not installed"
python -c "import ollama; print('✅ ollama installed')" 2>/dev/null || echo "❌ ollama not installed"
python -c "import langchain; print('✅ langchain installed')" 2>/dev/null || echo "❌ langchain not installed"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🚀 Ready to run?"
echo "═══════════════════════════════════════════════════════════"

# Find the app file
APP_FILE=$(ls -1 app_fixed.py app.py 2>/dev/null | head -1)

if [ -z "$APP_FILE" ]; then
    echo "❌ No app file found!"
    echo "Copy one of these:"
    echo "  cp app.py ."
else
    echo "✅ App file found: $APP_FILE"
    echo ""
    echo "To run your chatbot:"
    echo "  Terminal 1: ollama serve"
    echo "  Terminal 2: streamlit run $APP_FILE"
fi