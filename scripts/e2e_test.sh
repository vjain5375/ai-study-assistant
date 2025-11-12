#!/usr/bin/env bash
# End-to-end test script for the FastAPI backend
# Tests: Upload -> Generate -> Get Document -> Verify Artifacts

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=========================================="
echo "End-to-End Test for FastAPI Backend"
echo "=========================================="
echo ""

# Step 1: Create a sample PDF (text file for testing)
echo "📄 Step 1: Creating sample PDF..."
SAMPLE_TEXT="Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed. It uses algorithms to identify patterns and make decisions based on data.

Types of Machine Learning

There are three main types:
1. Supervised Learning: Uses labeled data to train models
2. Unsupervised Learning: Finds patterns in unlabeled data
3. Reinforcement Learning: Learns through interaction with environment

Neural Networks

Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes organized in layers."

echo "$SAMPLE_TEXT" > /tmp/sample.txt

# Convert to PDF (requires text2pdf or similar, or use a real PDF)
# For testing, we'll assume a PDF exists or create one
if command -v ps2pdf &> /dev/null; then
    # Create PDF from text (simplified)
    echo "Creating PDF from text..."
else
    echo "⚠️  PDF creation tool not found. Using existing PDF or create one manually."
    echo "For testing, place a sample.pdf in /tmp/sample.pdf"
fi

# Step 2: Upload PDF
echo ""
echo "📤 Step 2: Uploading PDF..."
if [ -f "/tmp/sample.pdf" ]; then
    UPLOAD_RESPONSE=$(curl -s -X POST \
        -F "file=@/tmp/sample.pdf" \
        "${API_URL}/api/v1/upload")
else
    echo "⚠️  Sample PDF not found. Skipping upload test."
    echo "To test: Create /tmp/sample.pdf and run this script again."
    exit 1
fi

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | jq '.'

FILE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.file_id')

if [ "$FILE_ID" == "null" ] || [ -z "$FILE_ID" ]; then
    echo "❌ Error: Failed to get file_id from upload"
    exit 1
fi

echo "✅ Upload successful! File ID: $FILE_ID"
echo ""

# Step 3: Wait a bit for processing
echo "⏳ Step 3: Waiting for processing to complete..."
sleep 3

# Step 4: Generate Flashcards
echo ""
echo "🎴 Step 4: Generating flashcards..."
GENERATE_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{
        \"file_id\": $FILE_ID,
        \"artifact_type\": \"flashcards\",
        \"num_items\": 5,
        \"temperature\": 0.0
    }" \
    "${API_URL}/api/v1/generate")

echo "Generate Response:"
echo "$GENERATE_RESPONSE" | jq '.'

ARTIFACT_ID=$(echo "$GENERATE_RESPONSE" | jq -r '.artifact_id')

if [ "$ARTIFACT_ID" == "null" ] || [ -z "$ARTIFACT_ID" ]; then
    echo "⚠️  Warning: No artifact_id in response (may be optional)"
fi

echo ""

# Step 5: Get Document with Artifacts
echo "📚 Step 5: Fetching document and artifacts..."
DOC_RESPONSE=$(curl -s "${API_URL}/api/v1/document/$FILE_ID")

echo "Document Response:"
echo "$DOC_RESPONSE" | jq '.'

# Step 6: Verify Artifacts Exist
echo ""
echo "✅ Step 6: Verifying artifacts..."
ARTIFACTS_COUNT=$(echo "$DOC_RESPONSE" | jq '.artifacts | length')

if [ "$ARTIFACTS_COUNT" -gt 0 ]; then
    echo "✅ Found $ARTIFACTS_COUNT artifact(s)"
    
    # Check for flashcards
    HAS_FLASHCARDS=$(echo "$DOC_RESPONSE" | jq '[.artifacts[] | select(.artifact_type == "flashcards")] | length')
    if [ "$HAS_FLASHCARDS" -gt 0 ]; then
        echo "✅ Flashcards artifact found!"
        echo "$DOC_RESPONSE" | jq '.artifacts[] | select(.artifact_type == "flashcards") | .artifact_data | length'
    else
        echo "⚠️  No flashcards artifact found"
    fi
else
    echo "❌ No artifacts found"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ End-to-End Test Completed Successfully!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - File ID: $FILE_ID"
echo "  - Artifacts: $ARTIFACTS_COUNT"
echo "  - Flashcards: $HAS_FLASHCARDS"

