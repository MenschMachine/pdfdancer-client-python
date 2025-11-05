#!/bin/bash

# test.sh - Configurable pytest runner for multiple servers
# Usage: ./test.sh [OPTIONS] [-- PYTEST_ARGS]

set -euo pipefail

# Default values
DEFAULT_SERVERS="http://localhost:8080"
DEFAULT_PARALLEL=1
LOGFILE=""
STDOUT_OUTPUT=false
FAIL_FAST=false
SERVERS=""
TOKEN=""
PARALLEL=""
PYTEST_ARGS=()
PYTHON_CMD=""

# Server URL parsing - handles various formats flexibly
parse_server_url() {
    local input="$1"
    local protocol="https"
    local hostname=""
    local port=""

    # Remove leading/trailing whitespace
    input=$(echo "$input" | xargs)

    # Check if input has protocol specified
    if [[ "$input" =~ ^(https?):// ]]; then
        protocol="${BASH_REMATCH[1]}"
        input="${input#${protocol}://}"
    fi

    # Split hostname and port
    if [[ "$input" =~ ^(\[?[^\]:]+\]?):([0-9]+)$ ]]; then
        # Has explicit port: hostname:port or [ipv6]:port
        hostname="${BASH_REMATCH[1]}"
        port="${BASH_REMATCH[2]}"
    elif [[ "$input" =~ ^(\[?[^\]:]+\]?)$ ]]; then
        # No port specified: just hostname
        hostname="${BASH_REMATCH[1]}"
        # Use default ports
        if [[ "$protocol" == "http" ]]; then
            port="80"
        else
            port="443"
        fi
    else
        echo "Invalid server format: $input" >&2
        return 1
    fi

    # Clean IPv6 brackets if present
    hostname="${hostname#[}"
    hostname="${hostname%]}"

    # Validate hostname is not empty
    if [[ -z "$hostname" ]]; then
        echo "Empty hostname in: $input" >&2
        return 1
    fi

    echo "$protocol://$hostname:$port"
}

# Parse comma-separated list of server URLs
parse_servers_list() {
    local servers_input="$1"
    local parsed_servers=()

    # Split by comma and process each server
    IFS=',' read -ra server_items <<< "$servers_input"

    for server_item in "${server_items[@]}"; do
        local parsed
        if ! parsed=$(parse_server_url "$server_item"); then
            echo "Error parsing server: $server_item" >&2
            return 1
        fi
        parsed_servers+=("$parsed")
    done

    # Return space-separated list
    echo "${parsed_servers[*]}"
}

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
Usage: $0 [OPTIONS] [PYTEST_ARGS]

Run pytest against configurable servers with parallel execution support.

SHORT OPTIONS:
    -s SERVERS             Comma-separated list of server URLs (default: localhost:8080)
    -t TOKEN              API token for authentication (optional)
    -p N                  Number of parallel workers per server (default: 1)
    -F                    Stop on first server failure
    -S                    Show output on stdout in addition to logfile
    -l PATH               Specify logfile path (default: random file in /tmp/)
    -h                    Show this help message

LONG OPTIONS (use either format):
    --servers SERVERS or --servers=SERVERS
                          Comma-separated list of server URLs
    --token TOKEN or --token=TOKEN
                          API token for authentication (optional)
    --parallel N or --parallel=N
                          Number of parallel workers per server
    --fail-fast           Stop on first server failure
    --stdout              Show output on stdout in addition to logfile
    --logfile PATH or --logfile=PATH
                          Specify logfile path
    --help                Show this help message

ENVIRONMENT:
    PDFDANCER_TOKEN        Token if --token/-t not provided

SERVER URL FORMATS:
    localhost:8080                  Hostname with port (auto-detects https)
    localhost                       Hostname only (uses https:443)
    https://localhost:8080          Protocol, hostname, and port
    https://localhost               Protocol and hostname (uses default port)
    http://server:9000              HTTP with custom port
    http://server                   HTTP without port (uses port 80)
    127.0.0.1:8080                  IP address with port
    [::1]:8080                      IPv6 address with port

EXAMPLES:
    $0 -s localhost:8080 -t abc123
    $0 -s https://localhost:8443,server2:9000
    $0 -s localhost -t abc123 -S -F tests/
    $0 -l /tmp/my-tests.log -p 4 -- -x -v tests/test_models.py

PYTEST_ARGS:
    All arguments after -- are passed directly to pytest
    Common options: -x (stop on first failure), -v (verbose), -k (filter tests)
EOF
}

# Parse command line arguments using getopts
parse_args() {
    local OPTIND opt

    while getopts "s:t:p:FSl:h-:" opt; do
        case $opt in
            s)
                SERVERS="$OPTARG"
                ;;
            t)
                TOKEN="$OPTARG"
                ;;
            p)
                PARALLEL="$OPTARG"
                ;;
            F)
                FAIL_FAST=true
                ;;
            S)
                STDOUT_OUTPUT=true
                ;;
            l)
                LOGFILE="$OPTARG"
                ;;
            h)
                show_help
                exit 0
                ;;
            -)
                # Handle long options
                case "${OPTARG}" in
                    servers=*)
                        SERVERS="${OPTARG#*=}"
                        ;;
                    servers)
                        # Handle --servers VALUE (not --servers=VALUE)
                        SERVERS="${!OPTIND}"
                        ((OPTIND++))
                        ;;
                    token=*)
                        TOKEN="${OPTARG#*=}"
                        ;;
                    token)
                        # Handle --token VALUE (not --token=VALUE)
                        TOKEN="${!OPTIND}"
                        ((OPTIND++))
                        ;;
                    parallel=*)
                        PARALLEL="${OPTARG#*=}"
                        ;;
                    parallel)
                        # Handle --parallel VALUE (not --parallel=VALUE)
                        PARALLEL="${!OPTIND}"
                        ((OPTIND++))
                        ;;
                    fail-fast)
                        FAIL_FAST=true
                        ;;
                    stdout)
                        STDOUT_OUTPUT=true
                        ;;
                    logfile=*)
                        LOGFILE="${OPTARG#*=}"
                        ;;
                    logfile)
                        # Handle --logfile VALUE (not --logfile=VALUE)
                        LOGFILE="${!OPTIND}"
                        ((OPTIND++))
                        ;;
                    help)
                        show_help
                        exit 0
                        ;;
                    *)
                        echo "Error: Unknown option --${OPTARG}" >&2
                        echo "Use --help for usage information" >&2
                        exit 1
                        ;;
                esac
                ;;
            *)
                echo "Error: Invalid option -$OPTARG" >&2
                echo "Use --help for usage information" >&2
                exit 1
                ;;
        esac
    done

    # Handle remaining arguments (pytest args after --)
    shift $((OPTIND - 1))
    if [[ $# -gt 0 && "$1" == "--" ]]; then
        shift
        PYTEST_ARGS=("$@")
    elif [[ $# -gt 0 ]]; then
        PYTEST_ARGS=("$@")
    fi
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
    
    # Check for token (optional - use from args or environment)
    if [[ -z "$TOKEN" ]]; then
        if [[ -n "${PDFDANCER_TOKEN:-}" ]]; then
            TOKEN="$PDFDANCER_TOKEN"
        else
            TOKEN=""
        fi
    fi
    
    # Validate parallel workers
    if ! [[ "$PARALLEL" =~ ^[0-9]+$ ]] || [[ "$PARALLEL" -lt 1 ]]; then
        echo "Error: Parallel workers must be a positive integer, got: $PARALLEL" >&2
        exit 1
    fi
    
    # Parse and validate servers format
    local parsed_servers
    if ! parsed_servers=$(parse_servers_list "$SERVERS"); then
        echo "Error: Invalid servers format" >&2
        echo "Supported formats:" >&2
        echo "  • localhost:8080 (hostname:port)" >&2
        echo "  • localhost (hostname, uses https:443)" >&2
        echo "  • https://localhost:8080 (protocol://hostname:port)" >&2
        echo "  • https://localhost (protocol://hostname, uses default port)" >&2
        echo "  • [::1]:8080 (IPv6 with port)" >&2
        exit 1
    fi
    # Update SERVERS to use the normalized, parsed format
    SERVERS="$parsed_servers"
}

# Test server connectivity
test_server_connectivity() {
    local server_url="$1"

    echo "🔍 Testing connectivity to $server_url..." >&2

    if curl -s --connect-timeout 3 --max-time 8 --fail "$server_url/version" >/dev/null 2>&1; then
        echo "✅ Server $server_url is reachable" >&2
        return 0
    else
        echo "❌ Cannot connect to $server_url" >&2
        echo "   Make sure the PDFDancer server is running and accessible" >&2
        return 1
    fi
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
    local server_url="$1"
    local python_cmd="${PYTHON_CMD:-python}"
    local server="${server_url##*/}"  # Extract hostname:port for logging

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
    local server_url="$1"
    local strategy="${2:-sequential}"
    local server="${server_url##*/}"  # Extract hostname:port for logging

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
    
    # Convert servers string to array (space-separated after parsing)
    read -ra SERVER_ARRAY <<< "$SERVERS"

    local overall_exit_code=0
    local failed_servers=()

    # Test each server
    local server_count=0
    local total_servers=${#SERVER_ARRAY[@]}

    for server_url in "${SERVER_ARRAY[@]}"; do
        ((server_count++))
        local server="${server_url##*/}"  # Extract hostname:port for display
        echo "🎯 Testing Server $server_count/$total_servers: $server_url"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_message "$server" "=== Starting tests for $server_url ==="

        # Test connectivity
        if ! test_server_connectivity "$server_url"; then
            echo "" >&2
            echo "❌ ERROR: Server $server_url is not available!" >&2
            echo "   Please ensure the PDFDancer server is running and accessible." >&2
            echo "" >&2
            exit 1
        fi

        log_message "$server" "✓ Connectivity test passed"

        # Run pytest (either with pytest-xdist, GNU parallel, or sequentially)
        if [[ "$parallel_strategy" == "gnu" ]]; then
            if ! run_pytest_with_gnu_parallel "$server_url"; then
                failed_servers+=("$server")
                overall_exit_code=1

                if [[ "$FAIL_FAST" == true ]]; then
                    log_message "SYSTEM" "Fail-fast enabled, stopping due to test failure"
                    break
                fi
            fi
        else
            if ! run_pytest_on_server "$server_url" "$parallel_strategy"; then
                failed_servers+=("$server")
                overall_exit_code=1

                if [[ "$FAIL_FAST" == true ]]; then
                    log_message "SYSTEM" "Fail-fast enabled, stopping due to test failure"
                    break
                fi
            fi
        fi

        log_message "$server" "=== Completed tests for $server_url ==="
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
