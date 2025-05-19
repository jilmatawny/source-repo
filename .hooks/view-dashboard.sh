#!/bin/bash
# view-dashboard.sh - Script to open the dashboard in default browser

# Check if the dashboard file exists
DASHBOARD="./dashboard.html"
if [ ! -f "$DASHBOARD" ]; then
  echo "Error: Dashboard file not found at $DASHBOARD"
  echo "Creating a basic dashboard file..."
  
  # Create a basic dashboard file if it doesn't exist
  cat > "$DASHBOARD" << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <title>Development Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .metric { border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }
    .success { background-color: #e6ffe6; }
    .warning { background-color: #fff9e6; }
    .error { background-color: #ffe6e6; }
  </style>
</head>
<body>
  <h1>Local Development Dashboard</h1>
  <div class="metric success">
    <h2>Commits Today: <span id="commit-count">0</span></h2>
    <p>Last commit: <span id="last-commit">None</span></p>
  </div>
  <div class="metric">
    <h2>Lambda Tests</h2>
    <p>Success rate: <span id="lambda-success">100%</span></p>
  </div>
  <div class="metric warning">
    <h2>Code Quality</h2>
    <p>TODOs: <span id="todo-count">0</span></p>
  </div>
  
  <script>
    // Function to fetch text data from a file
    async function fetchData(file) {
      try {
        const response = await fetch(file);
        if (!response.ok) {
          throw new Error(`Failed to fetch ${file}`);
          return 'N/A';
        }
        return await response.text();
      } catch (error) {
        console.error(`Error fetching ${file}: ${error.message}`);
        return 'N/A';
      }
    }

    // Update dashboard with real data
    async function updateDashboard() {
      try {
        // Fetch data and update elements
        const commitCount = await fetchData('data/commit_count.txt');
        const lastCommit = await fetchData('data/last_commit.txt');
        const todoCount = await fetchData('data/todo_count.txt');
        const lambdaStatus = await fetchData('data/lambda_status.txt');
        
        // Update text content only if fetch was successful
        if (commitCount !== 'N/A') document.getElementById('commit-count').textContent = commitCount;
        if (lastCommit !== 'N/A') document.getElementById('last-commit').textContent = lastCommit;
        if (todoCount !== 'N/A') document.getElementById('todo-count').textContent = todoCount;
        
        // Update lambda success rate and styling
        if (lambdaStatus !== 'N/A') {
          document.getElementById('lambda-success').textContent = 
            (lambdaStatus === 'SUCCESS') ? '100%' : '0%';
          
          // Update lambda status color
          const lambdaMetric = document.querySelector('.metric:nth-child(2)');
          
          // Remove any existing status classes
          lambdaMetric.classList.remove('success', 'warning', 'error');
          
          // Add appropriate class based on status
          if (lambdaStatus === 'SUCCESS') {
            lambdaMetric.classList.add('success');
          } else if (lambdaStatus === 'FAILED') {
            lambdaMetric.classList.add('error');
          }
        }
        
        console.log('Dashboard updated successfully');
      } catch (error) {
        console.error('Error updating dashboard:', error);
      }
    }

    // Initial update
    updateDashboard();
    
    // Refresh every 10 seconds
    setInterval(updateDashboard, 10000);
  </script>
</body>
</html>
EOF
  echo "Created basic dashboard file."
fi

# Ensure the data directory exists
mkdir -p data

# Check if any browser command is available
BROWSER=""
if command -v xdg-open >/dev/null 2>&1; then
  # Linux
  BROWSER="xdg-open"
elif command -v open >/dev/null 2>&1; then
  # macOS
  BROWSER="open"
elif command -v start >/dev/null 2>&1; then
  # Windows
  BROWSER="start"
else
  echo "No compatible browser opener found. Please open manually:"
  echo "file://$(pwd)/$DASHBOARD"
  exit 1
fi

# Open the dashboard in the browser
if [ -n "$BROWSER" ]; then
  echo "Opening dashboard in browser..."
  $BROWSER "$DASHBOARD"
else
  echo "Failed to open dashboard. Please open manually:"
  echo "file://$(pwd)/$DASHBOARD"
  exit 1
fi

exit 0
