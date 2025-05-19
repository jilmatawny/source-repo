#!/bin/bash

# Script to install Git hooks

echo "Setting up Git hooks..."

# Make sure the hooks directory exists
mkdir -p .hooks

# Ensure all hooks are executable
chmod +x .hooks/*

# Configure Git to use custom hooks path
git config core.hooksPath .hooks

echo "Git hooks installed successfully!"
echo "The following hooks are now active:"
ls -la .hooks | grep -v "README\|setup" | grep -v "^d\|^total"
