# Test Fixtures

This directory contains test files used by Playwright E2E tests.

## Files

- **test-image.jpg** - Sample image file for first frame upload tests
- **test-audio.mp3** - Sample audio file for voice cloning tests

## Usage

These files are referenced in test specs:
- `./e2e/fixtures/test-image.jpg`
- `./e2e/fixtures/test-audio.mp3`

## Adding New Fixtures

When adding new test files:
1. Keep file sizes small (< 1MB) to avoid bloating the repository
2. Use appropriate file formats (JPG for images, MP3 for audio)
3. Document the purpose in this README
4. Reference them using relative paths in test specs

## Mock Data

For testing purposes, you can use placeholder files or download sample media:
- Sample images: Use 1280x720 resolution (720p)
- Sample audio: Use short clips (5-10 seconds) for voice samples
