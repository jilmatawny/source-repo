#!/bin/bash
# view-dashboard.sh - Script to open the dashboard in default browser

echo "Updating dashboard with current data..."

# Dashboard file location
DASHBOARD="./dashboard.html"
DATA_DIR="./data"
REPORT_PATH="./.hooks/reports/latest_validation_report.txt"

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Read data files or set defaults
COMMIT_COUNT=$(cat "$DATA_DIR/commit_count.txt" 2>/dev/null || echo "0")
LAST_COMMIT=$(cat "$DATA_DIR/last_commit.txt" 2>/dev/null || echo "No commits yet")
TODO_COUNT=$(cat "$DATA_DIR/todo_count.txt" 2>/dev/null || echo "0")
LAMBDA_STATUS=$(cat "$DATA_DIR/lambda_status.txt" 2>/dev/null || echo "SUCCESS")
LAMBDA_RESULTS=$(cat "$DATA_DIR/lambda_results.txt" 2>/dev/null || echo "No test results found")

# Read validation report if it exists
if [ -f "$REPORT_PATH" ]; then
    VALIDATION_REPORT=$(cat "$REPORT_PATH")
    echo "Found validation report"
else
    VALIDATION_REPORT="No validation report found"
    echo "No validation report found at $REPORT_PATH"
    
    # Create the reports directory if it doesn't exist
    mkdir -p "./.hooks/reports"
fi

echo "Data read from files:"
echo "- Commit count: $COMMIT_COUNT"
echo "- Last commit: $LAST_COMMIT"
echo "- TODO count: $TODO_COUNT"
echo "- Lambda status: $LAMBDA_STATUS"

# Display the dashboard with both structure and execution test results
echo "=== Lambda Test Dashboard ==="
echo ""

# Read the status file
if [ -f "$DATA_DIR/lambda_status.txt" ]; then
    while IFS=: read -r lambda status; do
        echo "Lambda: $lambda"
        echo "Status: $status"
        echo "------------------------"
    done < "$DATA_DIR/lambda_status.txt"
else
    echo "No test results found."
fi

# Display the full Lambda test results
echo ""
echo "=== Full Lambda Test Results ==="
if [ -f "$DATA_DIR/lambda_results.txt" ]; then
    cat "$DATA_DIR/lambda_results.txt"
else
    echo "No full test results found."
fi

# Create a new dashboard file with the current data
cat > "$DASHBOARD" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #2c3e50;
        }
        .metric {
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }
        .report {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        .report-content {
            white-space: pre-wrap;
            font-family: monospace;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .success {
            color: #27ae60;
        }
        .warning {
            color: #f39c12;
        }
        .error {
            color: #e74c3c;
        }
        .test-results {
            margin-top: 20px;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .test-results pre {
            white-space: pre-wrap;
            font-family: monospace;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Project Dashboard</h1>
            <p>Last updated: $(date)</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Commits</h2>
                <div class="metric">$COMMIT_COUNT</div>
                <p>Last commit: $LAST_COMMIT</p>
            </div>
            
            <div class="card">
                <h2>TODOs</h2>
                <div class="metric">$TODO_COUNT</div>
                <p>Remaining tasks</p>
            </div>
            
            <div class="card">
                <h2>Lambda Tests</h2>
                <div class="metric $([ "$LAMBDA_STATUS" = "SUCCESS" ] && echo "success" || echo "error")">$LAMBDA_STATUS</div>
                <p>Test status</p>
            </div>
        </div>
        
        <div class="test-results">
            <h2>Lambda Test Results</h2>
            <pre>$LAMBDA_RESULTS</pre>
        </div>
    </div>
</body>
</html>
EOF

echo "Dashboard updated at $DASHBOARD"

# Open the dashboard in the default browser
if command -v open &> /dev/null; then
    open "$DASHBOARD"
elif command -v xdg-open &> /dev/null; then
    xdg-open "$DASHBOARD"
else
    echo "Please open $DASHBOARD in your web browser"
fi

exit 0
