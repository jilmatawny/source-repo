#!/bin/bash

# Simple CI pipeline for local testing

echo "🚀 Running local CI pipeline..."

# Check if we're in test mode
if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "⚠️ Running in TEST MODE - some steps will be simulated"
fi

# Step 1: Clean build
echo "📦 Building project..."
if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "Simulating build process..."
  sleep 1  # Simulate build time
else
  # Add your actual build commands here
  echo "No build steps defined yet"
fi

# Step 2: Run tests
echo "🧪 Running tests..."
if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "Simulating test execution..."
  sleep 1  # Simulate test time
else
  # Add your actual test commands here
  echo "No test steps defined yet"
fi

# Step 3: Run Lambda validation
echo "🔍 Validating Lambda functions..."
if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "Simulating Lambda validation..."
  sleep 1  # Simulate validation time
else
  # Run the actual Lambda validation
  echo "Running Lambda tests..."
  
  # Ensure data directory exists
  mkdir -p data
  
  # Activate virtual environment and run the Lambda tests
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    if python test_lambda_local.py; then
      echo "✅ Lambda tests completed successfully"
      echo "SUCCESS" > data/lambda_status.txt
    else
      echo "❌ Lambda tests failed"
      echo "FAILED" > data/lambda_status.txt
      # Don't exit here, continue to generate the report
    fi
    deactivate
  else
    echo "❌ Virtual environment not found. Please run 'make setup' first."
    echo "FAILED" > data/lambda_status.txt
    exit 1
  fi
  
  # Update the dashboard with the latest results
  ./view-dashboard.sh
fi

# Step 4: Generate report
echo "📊 Generating report..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p .ci/reports

if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "CI Pipeline Test Run: $TIMESTAMP" > .ci/reports/last_run.txt
  echo "Status: Test Completed (Simulated)" >> .ci/reports/last_run.txt
else
  # Read Lambda status from file
  LAMBDA_STATUS=$(cat data/lambda_status.txt 2>/dev/null || echo "UNKNOWN")
  
  echo "CI Pipeline Run: $TIMESTAMP" > .ci/reports/last_run.txt
  echo "Status: $LAMBDA_STATUS" >> .ci/reports/last_run.txt
  echo "Lambda Test Results:" >> .ci/reports/last_run.txt
  cat data/lambda_results.txt >> .ci/reports/last_run.txt 2>/dev/null || echo "No Lambda test results found"
fi

# Add debug logging
if [ "${CI_TEST_MODE}" = "true" ] || [ "${DEBUG}" = "true" ]; then
  echo "Debug information:"
  echo "  Working directory: $(pwd)"
  echo "  Environment: ${ENV:-production}"
  echo "  Git branch: $(git branch --show-current)"
  echo "  Lambda Status: $LAMBDA_STATUS"
fi

# Set final exit status based on Lambda test results
if [ "$LAMBDA_STATUS" = "FAILED" ]; then
  echo "❌ CI pipeline completed with errors!"
  exit 1
else
  echo "✅ CI pipeline completed successfully!"
  exit 0
fi
