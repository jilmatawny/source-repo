# Lambda Development Dashboard

This repository contains a development dashboard system for monitoring Lambda functions and development metrics.

## Dashboard System Overview

The dashboard system consists of several components:

### 1. Lambda Testing (`ds_test_workflow_1.py`)
- Validates Lambda function structure
- Checks for required elements:
  - `config`
  - `sagemaker_runtime`
  - `VisionFrame`
  - `WARP_TEMPLATES`
  - `convert_parsed_response_to_ndarray`
  - `Preprocessing`
  - `Postprocessing`
  - `lambda_handler`

### 2. Dashboard Components
- `dashboard.template.html`: Base template for the dashboard
- `view-dashboard.sh`: Script to generate and open the dashboard
- `dashboard.html`: Generated dashboard file (do not edit directly)

### 3. Data Sources
The dashboard reads data from:
- `./data/commit_count.txt`: Number of commits
- `./data/last_commit.txt`: Last commit information
- `./data/todo_count.txt`: Number of TODOs in code
- `./data/lambda_status.txt`: Lambda test status
- `./.hooks/reports/latest_validation_report.txt`: Detailed validation report

## How to Use

### 1. Initial Setup
```bash
# Set up the development environment and Git hooks
./.hooks/setup-dev-environment.sh
```

### 2. Development Workflow
When working on a new feature:

1. **Local Testing**
   ```bash
   # Test your Lambda function locally
   python test_lambda_local.py
   ```
   This will:
   - Check Lambda function structure
   - Test Lambda execution with mock data
   - Update dashboard status
   - Show detailed test results

2. **Run Lambda Tests**
   ```bash
   python ds_test_workflow_1.py ./lambdas
   ```

3. **View Dashboard**
   ```bash
   ./view-dashboard.sh
   ```

The dashboard will automatically open in your default browser showing:
- Commit statistics
- Lambda test results
- Code quality metrics
- Detailed validation report

## Git Hooks

The repository includes several Git hooks in the `.hooks` directory:

### Pre-commit Hook
The pre-commit hook performs several checks before allowing a commit:
1. Checks for TODO items in staged files
   - Warns about TODOs and asks for confirmation
   - Updates dashboard with TODO count
2. Runs Lambda tests
   - Validates Lambda function structure
   - Updates dashboard with test status
3. Runs security checks
   - Performs basic security validations
4. Updates commit statistics
   - Tracks daily commit count
   - Updates dashboard data

### Other Hooks
- `post-commit`: Updates dashboard after successful commits
- `pre-push`: Additional checks before pushing
- `commit-msg`: Validates commit messages
- `prepare-commit-msg`: Prepares commit message template

## Local Testing

The `test_lambda_local.py` script provides comprehensive local testing:

### Structure Testing
- Validates all required elements are present
- Checks for proper class and function definitions
- Ensures correct module structure

### Execution Testing
- Tests Lambda function with mock event data
- Validates response format
- Checks error handling
- Updates dashboard status

### Test Results
- Shows detailed test results in a table format
- Color-coded pass/fail indicators
- Updates dashboard with test status
- Provides clear error messages for failures

## Dashboard Features
- Real-time metrics display
- Collapsible validation report section
- Color-coded status indicators:
  - Green: Success
  - Yellow: Warning
  - Red: Error

## Directory Structure
```
.
├── lambdas/              # Lambda function directories
│   ├── lambda1/
│   └── lambda2/
├── data/                # Dashboard data files
├── .hooks/             # Git hooks and reports
│   ├── pre-commit     # Pre-commit hook
│   ├── post-commit    # Post-commit hook
│   ├── security-check.sh  # Security validation
│   └── reports/       # Validation reports
├── dashboard.html      # Generated dashboard
├── dashboard.template.html  # Dashboard template
├── ds_test_workflow_1.py   # Lambda testing script
├── test_lambda_local.py    # Local testing script
└── view-dashboard.sh   # Dashboard viewer script
```

## Notes
- The dashboard is automatically generated - do not edit `dashboard.html` directly
- To modify the dashboard layout, edit `dashboard.template.html`
- Data files in the `data/` directory are updated by the testing scripts
- Validation reports are stored in `.hooks/reports/`
- Git hooks are automatically set up by `setup-dev-environment.sh`
- Always run local tests before committing changes
