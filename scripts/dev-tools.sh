#!/bin/bash

# Development tools script for code quality and formatting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is available
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed or not in PATH"
    exit 1
fi

# Function to install dependencies
install_deps() {
    print_status "Installing dependencies..."
    uv sync
}

# Function to format code with Black
format_code() {
    print_status "Formatting Python code with Black..."
    uv run black backend/ --diff --color || true
    uv run black backend/
    print_status "Code formatting completed"
}

# Function to check code formatting
check_format() {
    print_status "Checking code formatting with Black..."
    if uv run black backend/ --check --diff --color; then
        print_status "Code formatting is correct"
        return 0
    else
        print_error "Code formatting issues found"
        return 1
    fi
}

# Function to run all quality checks
quality_check() {
    print_status "Running code quality checks..."
    
    local failed=0
    
    # Check formatting
    if ! check_format; then
        failed=1
    fi
    
    # Run tests if available
    if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
        print_status "Running tests..."
        if uv run pytest; then
            print_status "Tests passed"
        else
            print_error "Tests failed"
            failed=1
        fi
    else
        print_warning "No test configuration found, skipping tests"
    fi
    
    if [ $failed -eq 0 ]; then
        print_status "All quality checks passed"
        return 0
    else
        print_error "Some quality checks failed"
        return 1
    fi
}

# Function to fix code issues automatically
fix_code() {
    print_status "Fixing code issues automatically..."
    format_code
    print_status "Auto-fix completed"
}

# Function to show help
show_help() {
    echo "Development Tools Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install     Install project dependencies"
    echo "  format      Format code with Black"
    echo "  check       Check code formatting and quality"
    echo "  fix         Automatically fix code issues"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 format   # Format all Python code"
    echo "  $0 check    # Run quality checks"
    echo "  $0 fix      # Fix issues automatically"
}

# Main script logic
case "${1:-help}" in
    install)
        install_deps
        ;;
    format)
        format_code
        ;;
    check)
        quality_check
        ;;
    fix)
        fix_code
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac