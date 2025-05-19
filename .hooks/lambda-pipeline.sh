#!/bin/bash
# Local CI/CD Pipeline for Lambda Structure Testing
# ------------------------------------------------

set -e  # Exit on error

# Get the absolute path to the repository root
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.hooks"

# Configuration with paths relative to repository root
LAMBDA_REPO_DIR="$REPO_ROOT/lambdas"
LOG_DIR="$REPO_ROOT/.hooks/pipeline_logs"
REPORT_DIR="$REPO_ROOT/.hooks/reports"

# Try to locate the checker scripts
PYTHON_CHECKER_SCRIPT=""
SHELL_CHECKER_SCRIPT=""

# Find the Python checker script
for loc in "$REPO_ROOT/ds_test_workflow.py" "$HOOKS_DIR/ds_test_workflow.py" "/Users/Chris-Folder/lambda_checker/ds_test_workflow.py"; do
  if [ -f "$loc" ]; then
    PYTHON_CHECKER_SCRIPT="$loc"
    break
  fi
done

# Find the shell checker script
for loc in "$REPO_ROOT/lambda-test-pipeline.sh" "$HOOKS_DIR/lambda-test-pipeline.sh" "/Users/Chris-Folder/lambda_checker/lambda-test-pipeline.sh"; do
  if [ -f "$loc" ]; then
    SHELL_CHECKER_SCRIPT="$loc"
    break
  fi
done

# Create required directories
mkdir -p $LOG_DIR $REPORT_DIR

# Define pipeline stages
echo "🚀 Starting Local Lambda Testing Pipeline"
echo "----------------------------------------"

# Stage 1: Setup Environment
echo "⚙️  Stage 1: Setting up test environment"
if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "Simulating environment setup..."
else
  # Make sure we have at least one of the checker scripts
  if [ -z "$PYTHON_CHECKER_SCRIPT" ] && [ -z "$SHELL_CHECKER_SCRIPT" ]; then
    echo "❌ ERROR: Could not find any Lambda checker scripts!"
    echo "Looked for ds_test_workflow.py and lambda-test-pipeline.sh in common locations."
    if [ "${CI_TEST_MODE}" != "true" ]; then
      exit 1
    fi
  else
    if [ -n "$PYTHON_CHECKER_SCRIPT" ]; then
      echo "✅ Found Python checker script at $PYTHON_CHECKER_SCRIPT"
      chmod +x "$PYTHON_CHECKER_SCRIPT" 2>/dev/null || true
    fi
    
    if [ -n "$SHELL_CHECKER_SCRIPT" ]; then
      echo "✅ Found Shell checker script at $SHELL_CHECKER_SCRIPT"
      chmod +x "$SHELL_CHECKER_SCRIPT" 2>/dev/null || true
    fi
  fi
fi

# Stage 2: Prepare Test Lambdas
echo "📦 Stage 2: Preparing test lambdas"
if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "Simulating lambda preparation..."
else
  # Check if lambda directory exists
  if [ ! -d $LAMBDA_REPO_DIR ]; then
    echo "Creating test lambda directory structure..."
    mkdir -p $LAMBDA_REPO_DIR/lambda1
    mkdir -p $LAMBDA_REPO_DIR/lambda2

    # Create a valid lambda function
    cat > $LAMBDA_REPO_DIR/lambda1/lambda_function.py << EOF
# Valid lambda with all required elements
config = {}
sagemaker_runtime = {}
WARP_TEMPLATES = {}

class VisionFrame:
    def __init__(self):
        pass

class Preprocessing:
    def __init__(self):
        pass

class Postprocessing:
    def __init__(self):
        pass

def convert_parsed_response_to_ndarray():
    pass

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
EOF

    # Create an invalid lambda function (missing elements)
    cat > $LAMBDA_REPO_DIR/lambda2/lambda_function.py << EOF
# Invalid lambda missing some required elements
config = {}

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
EOF

    echo "✅ Test lambda functions created in $LAMBDA_REPO_DIR"
  else
    echo "✅ Using existing lambda functions in $LAMBDA_REPO_DIR"
  fi
fi

# Stage 3: Run Structure Validation
echo "🔍 Stage 3: Running structure validation"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/validation_$TIMESTAMP.log"

if [ "${CI_TEST_MODE}" = "true" ]; then
  echo "Simulating validation checks..."
  echo "Test validation result: PASS" > "$LOG_FILE"
else
  echo "Running validation checks..."
  
  # Create a temporary wrapper to avoid the nested script issue
  TEMP_WRAPPER="$LOG_DIR/temp_checker_wrapper.sh"
  cat > "$TEMP_WRAPPER" << EOF
#!/bin/bash
# Temporary wrapper to isolate the execution environment

# If we have the Python checker script, use it directly
if [ -n "$PYTHON_CHECKER_SCRIPT" ]; then
  echo "Running Python checker script: $PYTHON_CHECKER_SCRIPT"
  "$PYTHON_CHECKER_SCRIPT" "$LAMBDA_REPO_DIR" "$@"
  exit \$?
elif [ -n "$SHELL_CHECKER_SCRIPT" ]; then
  # If we have the shell checker script, modify it to use our found Python script
  echo "Running Shell checker script: $SHELL_CHECKER_SCRIPT"
  
  # Export the Python script location so the shell script can find it
  export PYTHON_CHECKER_SCRIPT="$PYTHON_CHECKER_SCRIPT"
  
  # Run the shell script
  "$SHELL_CHECKER_SCRIPT" "$@"
  exit \$?
else
  echo "No checker scripts found."
  exit 1
fi
EOF
  chmod +x "$TEMP_WRAPPER"
  
  # Run the wrapper script
  "$TEMP_WRAPPER" > "$LOG_FILE" 2>&1
  VALIDATION_RESULT=$?
  
  if [ $VALIDATION_RESULT -ne 0 ]; then
    echo "❌ Validation failed! See log for details: $LOG_FILE"
    cat "$LOG_FILE"
    echo ""
    echo "Pipeline failed at structure validation stage."
    exit 1
  else
    echo "✅ Validation passed!"
  fi
  
  # Clean up the temporary wrapper
  rm -f "$TEMP_WRAPPER"
fi

# Stage 4: Generate Reports
echo "📊 Stage 4: Generating reports"
cp "$LOG_FILE" "$REPORT_DIR/latest_validation_report.txt"
echo "✅ Report generated: $REPORT_DIR/latest_validation_report.txt"

# Add summary to a more accessible location
SUMMARY_FILE="$REPO_ROOT/.hooks/last_validation.log"
echo "Lambda Validation Run: $(date)" > "$SUMMARY_FILE"
echo "Status: SUCCESS" >> "$SUMMARY_FILE"
echo "Log: $LOG_FILE" >> "$SUMMARY_FILE"

# Pipeline completion
echo ""
echo "✅ Pipeline completed successfully!"
echo "Check $REPORT_DIR for validation reports"

# Add debug logging
if [ "${DEBUG}" = "true" ]; then
  echo ""
  echo "Debug information:"
  echo "  Repository root: $REPO_ROOT"
  echo "  Hooks directory: $HOOKS_DIR"
  echo "  Lambda directory: $LAMBDA_REPO_DIR"
  echo "  Python checker: $PYTHON_CHECKER_SCRIPT"
  echo "  Shell checker: $SHELL_CHECKER_SCRIPT"
  echo "  Log file: $LOG_FILE"
fi
