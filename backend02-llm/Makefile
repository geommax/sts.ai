# Makefile for LLM Backend

# Variables
PORT = 5002

# Default target
.PHONY: help
help:
	@echo "LLM Backend Makefile"
	@echo "Usage:"
	@echo "  make install     - Install dependencies"
	@echo "  make run         - Run the server locally"
	@echo "  make run-ollama  - Run the server with Ollama integration"
	@echo "  make test        - Run tests"
	@echo "  make test-ollama - Test Ollama integration"

# Install dependencies
.PHONY: install
install:
	pip3 install -r requirements.txt

# Run the server locally (simulation mode)
.PHONY: run
run:
	python3 src/server.py

# Run the server with Ollama integration
.PHONY: run-ollama
run-ollama:
	USE_OLLAMA=true python3 src/server.py

# Run tests
.PHONY: test
test:
	@echo "No tests implemented yet"

# Test Ollama integration
.PHONY: test-ollama
test-ollama:
	python3 test_ollama.py

# Install development dependencies
.PHONY: install-dev
install-dev:
	pip3 install -r requirements.txt
	pip3 install pytest black flake8

# Format code
.PHONY: format
format:
	black src/ || echo "Black not installed"

# Lint code
.PHONY: lint
lint:
	flake8 src/ || echo "Flake8 not installed"