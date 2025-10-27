#!/bin/bash

# test.sh - Configurable pytest runner for multiple servers
# Usage: ./test.sh [OPTIONS] [-- PYTEST_ARGS]

set -euo pipefail

# Default values
DEFAULT_SERVERS="localhost:8080"
DEFAULT_PARALLEL=1
LOGFILE=""
STDOUT_OUTPUT=false
FAIL_FAST=false
SERVERS=""
TOKEN=""
PARALLEL=""
PYTEST_ARGS=()
PYTHON_CMD=""

# Determine which python executable to use (prefer active venv)
detect_python_command() {
    if [[ -n "${PDFDANCER_PYTHON:-}" && -x "${PDFDANCER_PYTHON}" ]]; then
        echo "$PDFDANCER_PYTHON"
        return
    fi

    if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
        echo "$VIRTUAL_ENV/bin/python"
        return
    fi

    if [[ -x "venv/bin/python" ]]; then
        echo "venv/bin/python"
        return
    fi

    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi

    if command -v python >/dev/null 2>&1; then
        command -v python
        return
    fi

    echo "python"
}

# Check whether the selected python has pytest-xdist available
python_supports_xdist() {
    local python_cmd="$1"
    "$python_cmd" - <<'PY' >/dev/null 2>&1
try:
    import xdist  # modern package name
except ImportError:
    import pytest_xdist  # backward compatibility
PY
}

# Generate random logfile name in /tmp
generate_logfile() {
    echo "/tmp/pytest-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4).log"
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] [-- PYTEST_ARGS]

Run pytest against configurable servers with parallel execution support.

OPTIONS:
    --servers SERVERS       Comma-separated list of hostname:port (default: localhost:8080)
    --token TOKEN          API token for authentication (required)
    -p, --parallel N       Number of parallel workers per server (default: 1)
    -F, --fail-fast        Stop on first server failure
    -S, --stdout           Show output on stdout in addition to logfile
    -l, --logfile PATH     Specify logfile path (default: random file in /tmp/)
    -h, --help             Show this help message

ENVIRONMENT:
    PDFDANCER_TOKEN        Fallback token if --token not provided

EXAMPLES:
    $0 --token abc123 --servers server1:8080,server2:9090 -p 4
    $0 --token abc123 -S -F -- -x -v tests/
    $0 --token abc123 --logfile /tmp/my-tests.log -- tests/test_models.py

PYTEST_ARGS:
    All arguments after -- are passed directly to pytest
    Common options: -x (stop on first failure), -v (verbose), -k (filter tests)
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --servers)
                SERVERS="$2"
                shift 2
                ;;
            --token)
                TOKEN="$2"
                shift 2
                ;;
            -p|--parallel)
                PARALLEL="$2"
                shift 2
                ;;
            -F|--fail-fast)
                FAIL_FAST=true
                shift
                ;;
            -S|--stdout)
                STDOUT_OUTPUT=true
                shift
                ;;
            -l|--logfile)
                LOGFILE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --)
                shift
                PYTEST_ARGS=("$@")
                break
                ;;
            *)
                echo "Error: Unknown option $1" >&2
                echo "Use --help for usage information" >&2
                exit 1
                ;;
        esac
    done
}

# Validate arguments
validate_args() {
    # Set defaults
    if [[ -z "$SERVERS" ]]; then
        SERVERS="$DEFAULT_SERVERS"
    fi
    
    if [[ -z "$PARALLEL" ]]; then
        PARALLEL="$DEFAULT_PARALLEL"
    fi
    
    if [[ -z "$LOGFILE" ]]; then
        LOGFILE=$(generate_logfile)
    fi
    
    # Check for token
    if [[ -z "$TOKEN" ]]; then
        if [[ -n "${PDFDANCER_TOKEN:-}" ]]; then
            TOKEN="$PDFDANCER_TOKEN"
        else
            echo "Error: No token provided. Use --token or set PDFDANCER_TOKEN environment variable." >&2
            echo "" >&2
            show_help
            exit 1
        fi
    fi
    
    # Validate parallel workers
    if ! [[ "$PARALLEL" =~ ^[0-9]+$ ]] || [[ "$PARALLEL" -lt 1 ]]; then
        echo "Error: Parallel workers must be a positive integer, got: $PARALLEL" >&2
        exit 1
    fi
    
    # Validate servers format
    if [[ ! "$SERVERS" =~ ^[a-zA-Z0-9.-]+:[0-9]+(,[a-zA-Z0-9.-]+:[0-9]+)*$ ]]; then
        echo "Error: Invalid servers format. Use hostname:port,hostname:port format" >&2
        exit 1
    fi
}

# Test server connectivity and determine protocol
test_server_connectivity() {
    local server="$1"
    local protocol=""

    echo "🔍 Testing connectivity to $server..." >&2

    # Try HTTP first (more common for local development)
    if curl -s --connect-timeout 3 --max-time 8 --fail "http://$server/version" >/dev/null 2>&1; then
        protocol="http"
        echo "✅ Server $server is available via HTTP" >&2
    # Try HTTPS
    elif curl -s --connect-timeout 3 --max-time 8 --fail "https://$server/version" >/dev/null 2>&1; then
        protocol="https"
        echo "✅ Server $server is available via HTTPS" >&2
    else
        echo "❌ Cannot connect to $server (tried both http and https)" >&2
        echo "   Make sure the PDFDancer server is running at $server" >&2
        return 1
    fi

    echo "$protocol"
}

# Log message with server prefix
log_message() {
    local server="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_line="[$timestamp] [$server] $message"
    
    echo "$log_line" >> "$LOGFILE"
    
    if [[ "$STDOUT_OUTPUT" == true ]]; then
        echo "$log_line"
    fi
}

# Run pytest with GNU parallel
run_pytest_with_gnu_parallel() {
    local server="$1"
    local protocol="$2"
    local server_url="$protocol://$server"
    local python_cmd="${PYTHON_CMD:-python}"

    log_message "$server" "Starting pytest with $PARALLEL workers using GNU parallel"
    log_message "$server" "Server URL: $server_url"
    log_message "$server" "Pytest args: ${PYTEST_ARGS[*]:-tests/ -v}"
    echo "⚡ Using $PARALLEL workers via GNU parallel (pytest-xdist not available)"
    echo "   • Streaming detailed output to $LOGFILE"
    echo "   • Use -S/--stdout for live logs"

    # Set environment variables for this test run
    export PDFDANCER_TOKEN="$TOKEN"
    export PDFDANCER_BASE_URL="$server_url"

    # Get list of test files to distribute across workers
    local test_files=()
    if [[ ${#PYTEST_ARGS[@]} -gt 0 ]]; then
        # Use provided test arguments
        test_files=("${PYTEST_ARGS[@]}")
    else
        # Find all test files
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find tests -name "test_*.py" -print0)
    fi

    if [[ ${#test_files[@]} -eq 0 ]]; then
        log_message "$server" "No test files found"
        return 1
    fi

    # Create temporary file for parallel commands
    local parallel_jobs_file=$(mktemp)

    # Generate parallel jobs
    for test_file in "${test_files[@]}"; do
        echo "$python_cmd -m pytest \"$test_file\" -v" >> "$parallel_jobs_file"
    done

    # Run tests in parallel and capture output
    local exit_code=0
    if ! parallel -j "$PARALLEL" --line-buffer < "$parallel_jobs_file" 2>&1 | while IFS= read -r line; do
        log_message "$server" "$line"
    done; then
        exit_code=${PIPESTATUS[0]}
    fi

    # Cleanup
    rm -f "$parallel_jobs_file"

    if [[ $exit_code -eq 0 ]]; then
        log_message "$server" "✓ Tests completed successfully"
    else
        log_message "$server" "✗ Tests failed with exit code $exit_code"
    fi

    return $exit_code
}

# Run pytest on a single server
run_pytest_on_server() {
    local server="$1"
    local protocol="$2"
    local strategy="${3:-sequential}"
    local server_url="$protocol://$server"
    
    log_message "$server" "Starting pytest with $PARALLEL workers"
    log_message "$server" "Server URL: $server_url"
    log_message "$server" "Pytest args: ${PYTEST_ARGS[*]:-tests/ -v}"
    
    # Set environment variables for this test run
    export PDFDANCER_TOKEN="$TOKEN"
    export PDFDANCER_BASE_URL="$server_url"
    
    # Determine python executable (prefer venv if available)
    local python_cmd="${PYTHON_CMD:-python}"

    # Build pytest command
    local pytest_cmd=(
        "$python_cmd" "-m" "pytest"
    )

    # Add parallel execution if supported and requested
    if [[ "$strategy" == "xdist" ]]; then
        pytest_cmd+=("-n" "$PARALLEL")
        echo "⚡ Using $PARALLEL parallel workers (pytest-xdist)"
        log_message "$server" "Using $PARALLEL parallel workers (pytest-xdist)"
    elif [[ "$PARALLEL" -gt 1 ]]; then
        echo "⚠️  Requested $PARALLEL workers but pytest-xdist not available; running sequentially"
        log_message "$server" "pytest-xdist unavailable, running sequentially"
    else
        echo "🔄 Running tests sequentially (1 worker)"
    fi

    # Add pytest args if any
    if [[ ${#PYTEST_ARGS[@]} -gt 0 ]]; then
        pytest_cmd+=("${PYTEST_ARGS[@]}")
    else
        # Default to running all tests with verbose output
        pytest_cmd+=("tests/" "-v")
    fi

    # Show execution details
    echo "🧪 Starting pytest execution..."
    echo "   • Workers: $PARALLEL"
    echo "   • Server URL: $server_url"
    echo "   • Command: ${pytest_cmd[*]}"
    echo ""
    
    # Run pytest and capture output
    echo "📊 Test Execution Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ "$PARALLEL" -gt 1 ]]; then
        echo "⚡ Worker Status: $PARALLEL workers running against $server"
        echo "   🔄 Tests executing in parallel..."
    else
        echo "🔄 Worker Status: 1 worker running against $server"
        echo "   📝 Tests executing sequentially..."
    fi

    echo "   ⏱️  Started at: $(date '+%H:%M:%S')"
    echo ""

    local exit_code=0
    local start_time=$(date +%s)

    if [[ "$STDOUT_OUTPUT" == true ]]; then
        # Show full output if -S flag is used
        echo "📋 Full test output (--stdout mode):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if ! "${pytest_cmd[@]}" 2>&1 | while IFS= read -r line; do
            echo "$line"
            log_message "$server" "$line"
        done; then
            exit_code=${PIPESTATUS[0]}
        fi
    else
        # Show minimal progress for normal operation
        local test_count=0
        if ! "${pytest_cmd[@]}" 2>&1 | while IFS= read -r line; do
            # Show collection and progress info
            if [[ "$line" =~ "collected" ]]; then
                echo "   📦 $line"
            elif [[ "$line" =~ "=.*test session starts.*=" ]]; then
                echo "   🚀 Test session started"
            elif [[ "$line" =~ "=.*FAILURES.*=" ]]; then
                echo "   ⚠️  Some tests failed - check log for details"
            elif [[ "$line" =~ "=.*short test summary.*=" ]]; then
                echo "   📋 Test summary:"
            elif [[ "$line" =~ "FAILED.*PASSED.*SKIPPED" ]] || [[ "$line" =~ "[0-9]+ failed.*[0-9]+ passed" ]] || [[ "$line" =~ "[0-9]+ passed" ]]; then
                echo "   📊 $line"
            fi
            log_message "$server" "$line"
        done; then
            exit_code=${PIPESTATUS[0]}
        fi

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "   ⏱️  Completed in ${duration}s"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [[ $exit_code -eq 0 ]]; then
        echo "✅ Tests completed successfully for $server"
        log_message "$server" "✓ Tests completed successfully"
    else
        echo "❌ Tests failed for $server (exit code: $exit_code)"
        echo "   📄 Check full details in: $LOGFILE"
        log_message "$server" "✗ Tests failed with exit code $exit_code"
    fi
    echo ""
    
    return $exit_code
}

# Main execution function
main() {
    parse_args "$@"
    validate_args
    PYTHON_CMD=$(detect_python_command)
    
    local parallel_strategy="sequential"
    if [[ "$PARALLEL" -gt 1 ]]; then
        if python_supports_xdist "$PYTHON_CMD"; then
            parallel_strategy="xdist"
        elif command -v parallel >/dev/null 2>&1; then
            parallel_strategy="gnu"
        else
            echo "" >&2
            echo "❌ ERROR: Parallel execution requested (-p $PARALLEL) but pytest-xdist is not installed for $PYTHON_CMD and GNU parallel is unavailable." >&2
            echo "   Fix by installing pytest-xdist (pip install pytest-xdist) or GNU parallel (brew install parallel / apt install parallel)." >&2
            echo "" >&2
            exit 1
        fi
    fi

    local parallel_backend_label="sequential (1 worker)"
    case "$parallel_strategy" in
        xdist)
            parallel_backend_label="pytest-xdist (-n $PARALLEL)"
            ;;
        gnu)
            parallel_backend_label="GNU parallel (-j $PARALLEL)"
            ;;
    esac
    
    # Initialize logfile
    echo "# PDFDancer Test Run - $(date)" > "$LOGFILE"
    echo "# Servers: $SERVERS" >> "$LOGFILE"
    echo "# Parallel workers per server: $PARALLEL" >> "$LOGFILE"
    echo "# Parallel backend: $parallel_backend_label" >> "$LOGFILE"
    echo "# Pytest args: ${PYTEST_ARGS[*]:-}" >> "$LOGFILE"
    echo "# Fail fast: $FAIL_FAST" >> "$LOGFILE"
    echo "" >> "$LOGFILE"
    
    echo "🚀 Starting PDFDancer Test Run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Configuration:"
    echo "   • Servers: $SERVERS"
    echo "   • Parallel workers per server: $PARALLEL"
    echo "   • Parallel backend: $parallel_backend_label"
    echo "   • Pytest args: ${PYTEST_ARGS[*]:-tests/ -v}"
    echo "   • Fail fast: $FAIL_FAST"
    echo "   • Log file: $LOGFILE"
    echo ""
    
    # Convert servers string to array
    IFS=',' read -ra SERVER_ARRAY <<< "$SERVERS"

    local overall_exit_code=0
    local failed_servers=()
    
    # Test each server
    local server_count=0
    local total_servers=${#SERVER_ARRAY[@]}

    for server in "${SERVER_ARRAY[@]}"; do
        ((server_count++))
        echo "🎯 Testing Server $server_count/$total_servers: $server"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_message "$server" "=== Starting tests for $server ==="

        # Test connectivity and get protocol
        local protocol
        if ! protocol=$(test_server_connectivity "$server"); then
            echo "" >&2
            echo "❌ ERROR: Server $server is not available!" >&2
            echo "   Please ensure the PDFDancer server is running and accessible." >&2
            echo "" >&2
            exit 1
        fi

        echo "🔗 Server URL: $protocol://$server"
        log_message "$server" "✓ Connectivity test passed (using $protocol)"
        
        # Run pytest (either with pytest-xdist, GNU parallel, or sequentially)
        if [[ "$parallel_strategy" == "gnu" ]]; then
            if ! run_pytest_with_gnu_parallel "$server" "$protocol"; then
                failed_servers+=("$server")
                overall_exit_code=1

                if [[ "$FAIL_FAST" == true ]]; then
                    log_message "SYSTEM" "Fail-fast enabled, stopping due to test failure"
                    break
                fi
            fi
        else
            if ! run_pytest_on_server "$server" "$protocol" "$parallel_strategy"; then
                failed_servers+=("$server")
                overall_exit_code=1

                if [[ "$FAIL_FAST" == true ]]; then
                    log_message "SYSTEM" "Fail-fast enabled, stopping due to test failure"
                    break
                fi
            fi
        fi
        
        log_message "$server" "=== Completed tests for $server ==="
        echo "" >> "$LOGFILE"
    done
    
    # Final summary
    echo "🏁 Test Run Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Results:"
    echo "   • Total servers: ${#SERVER_ARRAY[@]}"
    echo "   • Failed servers: ${#failed_servers[@]}"

    if [[ ${#failed_servers[@]} -gt 0 ]]; then
        echo "   • Failed server list: ${failed_servers[*]}"
    fi

    if [[ $overall_exit_code -eq 0 ]]; then
        echo "   • Overall result: ✅ SUCCESS"
    else
        echo "   • Overall result: ❌ FAILURE"
    fi

    echo "📄 Full log file: $LOGFILE"
    echo ""

    log_message "SYSTEM" "=== Test Run Summary ==="
    log_message "SYSTEM" "Total servers: ${#SERVER_ARRAY[@]}"
    log_message "SYSTEM" "Failed servers: ${#failed_servers[@]}"

    if [[ ${#failed_servers[@]} -gt 0 ]]; then
        log_message "SYSTEM" "Failed server list: ${failed_servers[*]}"
    fi

    log_message "SYSTEM" "Overall result: $([ $overall_exit_code -eq 0 ] && echo "SUCCESS" || echo "FAILURE")"
    log_message "SYSTEM" "Logfile: $LOGFILE"
    
    exit $overall_exit_code
}

# Run main function with all arguments
main "$@"
