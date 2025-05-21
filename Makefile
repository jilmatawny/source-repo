.PHONY: start-moto stop-moto status-moto test-lambda setup view-dashboard help run-pipeline pre-push

PYTHON := /usr/local/bin/python3.12
VENV := venv
ACTIVATE := . $(VENV)/bin/activate

# AWS environment variables for Moto testing
export AWS_ACCESS_KEY_ID := fake
export AWS_SECRET_ACCESS_KEY := fake
export AWS_DEFAULT_REGION := us-east-1
export MOTO_ENDPOINT_URL := http://localhost:5001
export AWS_ENDPOINT_URL := http://localhost:5001

# Setup virtual environment and install dependencies
setup:
	@echo "Setting up virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install -r requirements.txt
	@echo "✅ Setup complete!"

# Start Moto Docker container
start-moto:
	@echo "Starting Moto container..."
	@if ! docker ps | grep -q "moto"; then \
		docker run -d -p 5001:5000 --name moto \
			-e SERVICES=s3,sagemaker,lambda \
			-e MOTO_PORT=5000 \
			-e MOTO_HOST=0.0.0.0 \
			motoserver/moto:latest; \
		echo "✅ Moto container started!"; \
	else \
		echo "Moto container already running"; \
	fi

# Stop Moto Docker container
stop-moto:
	@echo "Stopping Moto container..."
	@if docker ps | grep -q "moto"; then \
		docker stop moto && docker rm moto; \
		echo "✅ Moto container stopped!"; \
	else \
		echo "Moto container not running"; \
	fi

# Check Moto Docker container status
status-moto:
	@if docker ps | grep -q "moto"; then \
		echo "✅ Moto container is running."; \
		docker ps | grep moto; \
	else \
		echo "❌ Moto container is NOT running."; \
	fi

# Run Lambda tests with Moto
test-lambda: start-moto
	@echo "Running Lambda tests..."
	$(ACTIVATE) && $(PYTHON) test_lambda_local.py

# View the dashboard
view-dashboard:
	@echo "Opening dashboard..."
	./view-dashboard.sh

# Run the full CI pipeline
run-pipeline:
	@echo "🚀 Running CI pipeline..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi
	@if ! docker ps | grep -q "moto"; then \
		echo "Starting Moto container..."; \
		$(MAKE) start-moto; \
	fi
	@echo "Running Lambda tests..."
	@echo "----------------------------------------"
	@echo "🔍 Lambda Test Results:"
	@echo "----------------------------------------"
	-$(ACTIVATE) && $(PYTHON) test_lambda_local.py
	@echo "----------------------------------------"
	@echo "📊 Moto Test Results:"
	@echo "----------------------------------------"
	@if [ -f "data/lambda_results.txt" ]; then \
		cat data/lambda_results.txt | grep -A 100 "Moto Test Output"; \
	else \
		echo "No Moto test results found"; \
	fi
	@echo "----------------------------------------"
	@echo "Generating dashboard..."
	./view-dashboard.sh
	@echo "Opening dashboard in browser..."
	@DASHBOARD_PATH="$(shell pwd)/dashboard.html"; \
	echo "Dashboard path: $$DASHBOARD_PATH"; \
	if [ -f "$$DASHBOARD_PATH" ]; then \
		echo "Dashboard file exists"; \
		if [ "$(shell uname)" = "Darwin" ]; then \
			echo "Using 'open' command for macOS"; \
			open "$$DASHBOARD_PATH" || echo "Failed to open with 'open' command"; \
		elif [ "$(shell uname)" = "Linux" ]; then \
			echo "Using 'xdg-open' command for Linux"; \
			xdg-open "$$DASHBOARD_PATH" || echo "Failed to open with 'xdg-open' command"; \
		elif [ "$(shell uname)" = "MINGW"* ] || [ "$(shell uname)" = "MSYS"* ]; then \
			echo "Using 'start' command for Windows"; \
			start "$$DASHBOARD_PATH" || echo "Failed to open with 'start' command"; \
		else \
			echo "Unsupported OS. Please open manually: $$DASHBOARD_PATH"; \
		fi \
	else \
		echo "❌ Dashboard file not found at: $$DASHBOARD_PATH"; \
		echo "Current directory: $$(pwd)"; \
		echo "Files in current directory:"; \
		ls -la; \
	fi
	@echo "✅ Pipeline completed!"

# Run the pre-push hook manually
pre-push:
	@echo "Running pre-push hook..."
	@.git/hooks/pre-push

# Show help message
help:
	@echo "Available commands:"
	@echo "  make setup          - Create virtual environment and install dependencies"
	@echo "  make start-moto     - Start Moto Docker container"
	@echo "  make stop-moto      - Stop Moto Docker container"
	@echo "  make status-moto    - Check Moto Docker container status"
	@echo "  make test-lambda    - Run Lambda tests with Moto"
	@echo "  make view-dashboard - View the dashboard"
	@echo "  make run-pipeline   - Run the full CI pipeline"
	@echo "  make pre-push       - Run the pre-push hook manually"
	@echo "  make help           - Show this help message" 