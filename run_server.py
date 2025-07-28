"""
Background Remover API - Production Server Runner
Standardized way to run the API server with optimal configuration

Usage:
    python run_server.py                    # Run API server only
    python run_server.py --with-bot         # Run API + Telegram Bot (calls run_dual_services.py)
    python run_server.py --help             # Show help

This will automatically start the server using uvicorn with proper configuration:
- Host: 0.0.0.0 (accessible from all interfaces)
- Port: 8000 (configurable via .env)
- Auto-reload: Enabled for development
- Workers: 1 (suitable for development, increase for production)

💡 TIP: For production deployment running both services, use:
    python run_dual_services.py
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_api_only():
    """
    Run FastAPI server only
    """
    print("🚀 Starting Background Remover API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("💡 Press Ctrl+C to stop the server")
    print("💡 TIP: Use 'python run_dual_services.py' to run both API and Bot")
    print("-" * 60)

    # Ensure we're in the correct directory
    current_dir = Path(__file__).parent
    os.chdir(current_dir)

    # Command to run uvicorn with optimal settings
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
        "--reload-dir",
        "src",
        "--log-level",
        "info",
    ]

    try:
        # Start the server
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def run_with_bot():
    """
    Run both API server and Telegram bot using dual services runner
    """
    print("🚀 Switching to Dual Service Mode...")
    print("🤖 This will start both API Server and Telegram Bot")
    print("-" * 60)

    # Run the dual services script
    cmd = [sys.executable, "run_dual_services.py"]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 All services stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dual services: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def main():
    """
    Main function dengan argument parsing untuk flexibility
    """
    parser = argparse.ArgumentParser(
        description="Background Remover API Server Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_server.py              # Run API server only (default)
    python run_server.py --with-bot   # Run API server + Telegram bot
    python run_server.py --help       # Show this help

For full dual service management with monitoring, use:
    python run_dual_services.py
        """,
    )

    parser.add_argument(
        "--with-bot", action="store_true", help="Run both API server and Telegram bot"
    )

    args = parser.parse_args()

    if args.with_bot:
        run_with_bot()
    else:
        run_api_only()

    # Ensure we're in the correct directory
    current_dir = Path(__file__).parent
    os.chdir(current_dir)

    # Command to run uvicorn with optimal settings
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
        "--reload-dir",
        "src",
        "--log-level",
        "info",
    ]

    try:
        # Start the server
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
