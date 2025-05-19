#!/bin/bash

# Check what's in your files with TODOs
echo "Current files with TODOs:"
grep -l "TODO" *.js

# Create a truly clean file
echo "// This is a properly clean file with no references to T-O-D-O at all" > proper-clean-test.js
echo "function exampleFunction() {" >> proper-clean-test.js
echo "  return 'This is a clean implementation';" >> proper-clean-test.js
echo "}" >> proper-clean-test.js
echo "" >> proper-clean-test.js
echo "// This file is fully implemented and ready for review" >> proper-clean-test.js

# Verify no TODOs are in the new file
echo ""
echo "Verifying new file is clean:"
grep "TODO" proper-clean-test.js && echo "WARNING: TODO found!" || echo "✓ File is clean, no TODOs found"

# Stage and instruct for commit
echo ""
echo "Now run these commands to test:"
echo "git add proper-clean-test.js"
echo "git commit -m \"feat: add properly clean file that should pass all checks\""
