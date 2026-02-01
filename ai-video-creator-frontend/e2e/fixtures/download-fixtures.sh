#!/bin/bash
# Script to download sample test fixtures
# Run this script to populate the fixtures directory with test files

echo "Downloading test fixtures..."

# Download a sample image (1280x720 landscape)
curl -o test-image.jpg "https://picsum.photos/1280/720" && \
  echo "✓ Downloaded test-image.jpg"

# For audio, you would need to provide your own sample
# or use a text-to-speech service to generate a sample
echo ""
echo "⚠️  Please add test-audio.mp3 manually:"
echo "   - Record a 5-10 second voice sample"
echo "   - Or use a sample from https://freesound.org"
echo "   - Save as test-audio.mp3 in this directory"
echo ""
echo "Fixtures setup complete!"
