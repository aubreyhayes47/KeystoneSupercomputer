#!/bin/bash
# CLI Demo Script - Keystone Supercomputer
# This script demonstrates all CLI commands with example usage

set -e

echo "========================================================================"
echo "Keystone Supercomputer CLI Demo"
echo "========================================================================"
echo ""
echo "This script demonstrates the CLI commands for workflow submission"
echo "and job monitoring. Most commands will fail without Redis/Celery"
echo "running, but this shows the command structure and help text."
echo ""

cd "$(dirname "$0")/src/agent"

echo "1. Display main CLI help"
echo "----------------------------------------"
python3 cli.py --help
echo ""
read -p "Press Enter to continue..."
echo ""

echo "2. Check worker health (requires Redis + Celery)"
echo "----------------------------------------"
echo "$ python3 cli.py health"
python3 cli.py health 2>&1 || echo "Note: This fails without running services"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "3. List available simulation tools (requires Redis + Celery)"
echo "----------------------------------------"
echo "$ python3 cli.py list-tools"
python3 cli.py list-tools 2>&1 || echo "Note: This fails without running services"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "4. Submit command help"
echo "----------------------------------------"
python3 cli.py submit --help
echo ""
read -p "Press Enter to continue..."
echo ""

echo "5. Example submit commands (not executed)"
echo "----------------------------------------"
cat << 'EOF'
# Basic submission
python3 cli.py submit fenicsx poisson.py

# With parameters
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}'

# With wait
python3 cli.py submit fenicsx poisson.py --wait --timeout 600

# Full example
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 128}' --wait
EOF
echo ""
read -p "Press Enter to continue..."
echo ""

echo "6. Status command help"
echo "----------------------------------------"
python3 cli.py status --help
echo ""
read -p "Press Enter to continue..."
echo ""

echo "7. Example status commands (not executed)"
echo "----------------------------------------"
cat << 'EOF'
# Check once
python3 cli.py status abc123-task-id

# Monitor continuously
python3 cli.py status abc123-task-id --monitor

# Monitor with custom interval
python3 cli.py status abc123-task-id -m -i 5
EOF
echo ""
read -p "Press Enter to continue..."
echo ""

echo "8. Cancel command help"
echo "----------------------------------------"
python3 cli.py cancel --help
echo ""
read -p "Press Enter to continue..."
echo ""

echo "9. Submit-workflow command help"
echo "----------------------------------------"
python3 cli.py submit-workflow --help
echo ""
read -p "Press Enter to continue..."
echo ""

echo "10. Example workflow file"
echo "----------------------------------------"
cat ../../example_workflow.json
echo ""
read -p "Press Enter to continue..."
echo ""

echo "11. Example workflow commands (not executed)"
echo "----------------------------------------"
cat << 'EOF'
# Submit workflow
python3 cli.py submit-workflow workflow.json

# Parallel workflow with wait
python3 cli.py submit-workflow workflow.json --parallel --wait

# Sequential workflow with custom timeout
python3 cli.py submit-workflow workflow.json --sequential --wait --timeout 1200
EOF
echo ""
read -p "Press Enter to continue..."
echo ""

echo "12. Workflow-status command help"
echo "----------------------------------------"
python3 cli.py workflow-status --help
echo ""
read -p "Press Enter to continue..."
echo ""

echo "13. Example workflow-status command (not executed)"
echo "----------------------------------------"
cat << 'EOF'
# Check multiple tasks
python3 cli.py workflow-status task-id-1 task-id-2 task-id-3
EOF
echo ""

echo "========================================================================"
echo "CLI Demo Complete!"
echo "========================================================================"
echo ""
echo "To actually run commands, start the services first:"
echo "  docker compose up -d redis celery-worker"
echo ""
echo "For full documentation, see:"
echo "  - CLI_REFERENCE.md - Complete CLI reference"
echo "  - TASK_PIPELINE.md - Python API documentation"
echo "  - DOCKER_COMPOSE.md - Service setup guide"
echo ""
