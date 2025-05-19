#!/bin/bash

echo "🔐 Running security checks..."

# Check for AWS credentials
if git diff --cached --name-only | xargs grep -l "AKIA[0-9A-Z]{16}" >/dev/null; then
  echo "❌ ERROR: Potential AWS access key found in code!"
  echo "Please remove credentials before committing."
  exit 1
fi

# Check for private keys
if git diff --cached --name-only | xargs grep -l "BEGIN.*PRIVATE KEY" >/dev/null; then
  echo "❌ ERROR: Private key found in code!"
  echo "Please remove private keys before committing."
  exit 1
fi

# Add more security checks as needed

echo "✅ Security checks passed!"
exit 0
