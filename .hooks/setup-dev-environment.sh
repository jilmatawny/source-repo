#!/bin/bash
# setup-dev-environment.sh

echo "Setting up development environment..."

# Set up Git hooks
git config core.hooksPath .hooks
chmod +x .hooks/*

# Initialize dashboard data
mkdir -p .dashboard/data
echo "0" > .dashboard/data/commit_count.txt
echo "None yet" > .dashboard/data/last_commit.txt
echo "0" > .dashboard/data/todo_count.txt
echo "Unknown" > .dashboard/data/lambda_status.txt

# Make dashboard viewer executable
chmod +x view-dashboard.sh

echo "Setup complete! Run './view-dashboard.sh' to open your development dashboard."
