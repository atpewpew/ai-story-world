#!/bin/bash
# AI Story Agent CLI Wrapper Script
# Usage: ./story_cli.sh [options]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
API_URL="http://localhost:8000"
API_MODE=false
API_TOKEN=""

# Function to print colored output
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show help
show_help() {
    echo "AI Story Agent CLI"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -a, --api               Use API backend mode"
    echo "  -u, --url URL           API backend URL (default: http://localhost:8000)"
    echo "  -t, --token TOKEN       API authentication token"
    echo "  -s, --session-id ID     Load specific session ID"
    echo "  -c, --create NAME       Create new session with given name"
    echo "  -l, --list              List all sessions and exit"
    echo "  -d, --delete ID         Delete session with given ID and exit"
    echo "  --action ACTION         Take a single action (requires --session-id)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Interactive mode (standalone)"
    echo "  $0 --api                             # Interactive mode (API backend)"
    echo "  $0 --api --create \"My Adventure\"     # Create new session via API"
    echo "  $0 --list                            # List all sessions"
    echo "  $0 --session-id 12345 --action \"walk north\"  # Take single action"
    echo ""
}

# Function to check if Python is available
check_python() {
    if ! command -v python &> /dev/null; then
        print_colored $RED "Error: Python is not installed or not in PATH"
        exit 1
    fi
}

# Function to check if required packages are installed
check_dependencies() {
    python -c "import requests, dotenv" 2>/dev/null
    if [ $? -ne 0 ]; then
        print_colored $YELLOW "Warning: Some required packages may not be installed"
        print_colored $YELLOW "Run: pip install requests python-dotenv"
    fi
}

# Function to check API connection
check_api_connection() {
    if [ "$API_MODE" = true ]; then
        print_colored $BLUE "Checking API connection..."
        response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" 2>/dev/null)
        if [ "$response" = "200" ]; then
            print_colored $GREEN "✅ API backend is running"
        else
            print_colored $RED "❌ Cannot connect to API backend at $API_URL"
            print_colored $YELLOW "Make sure the server is running with: uvicorn ai_story.main:app --reload"
            exit 1
        fi
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--api)
            API_MODE=true
            shift
            ;;
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -t|--token)
            API_TOKEN="$2"
            shift 2
            ;;
        -s|--session-id)
            SESSION_ID="$2"
            shift 2
            ;;
        -c|--create)
            CREATE_NAME="$2"
            shift 2
            ;;
        -l|--list)
            LIST_SESSIONS=true
            shift
            ;;
        -d|--delete)
            DELETE_ID="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        *)
            print_colored $RED "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_colored $BLUE "🎮 AI Story Agent CLI"
    print_colored $BLUE "===================="
    
    # Check prerequisites
    check_python
    check_dependencies
    
    # Build command
    CMD="python cli.py"
    
    if [ "$API_MODE" = true ]; then
        CMD="$CMD --api --api-url $API_URL"
        if [ -n "$API_TOKEN" ]; then
            CMD="$CMD --api-token $API_TOKEN"
        fi
        check_api_connection
    fi
    
    if [ -n "$SESSION_ID" ]; then
        CMD="$CMD --session-id $SESSION_ID"
    fi
    
    if [ -n "$CREATE_NAME" ]; then
        CMD="$CMD --create \"$CREATE_NAME\""
    fi
    
    if [ "$LIST_SESSIONS" = true ]; then
        CMD="$CMD --list-sessions"
    fi
    
    if [ -n "$DELETE_ID" ]; then
        CMD="$CMD --delete-session $DELETE_ID"
    fi
    
    if [ -n "$ACTION" ]; then
        CMD="$CMD --action \"$ACTION\""
    fi
    
    # Execute command
    print_colored $BLUE "Running: $CMD"
    echo ""
    eval $CMD
}

# Run main function
main
