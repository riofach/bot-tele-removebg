"""
Dual Service Runner - Run both Telegram Bot and FastAPI server
Professional implementation for concurrent services
"""

import asyncio
import subprocess
import sys
import signal
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ServiceManager:
    """Professional service manager for dual services"""

    def __init__(self):
        self.telegram_process = None
        self.api_process = None
        self.running = False

    async def start_telegram_bot(self):
        """Start Telegram bot service"""
        try:
            logger.info("🤖 Starting Telegram Bot service...")

            # Check if main.py exists
            if not Path("main.py").exists():
                logger.warning("⚠️  main.py not found. Telegram bot service skipped.")
                return

            self.telegram_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            logger.info("✅ Telegram Bot service started successfully")

            # Monitor the process
            while self.running:
                if self.telegram_process.poll() is not None:
                    # Process has terminated
                    stdout, stderr = self.telegram_process.communicate()
                    logger.error(f"❌ Telegram Bot process terminated unexpectedly")
                    logger.error(f"STDOUT: {stdout}")
                    logger.error(f"STDERR: {stderr}")
                    break

                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            logger.error(f"❌ Failed to start Telegram Bot: {e}")

    async def start_api_server(self):
        """Start FastAPI server service"""
        try:
            logger.info("🚀 Starting FastAPI API service...")

            self.api_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            logger.info("✅ FastAPI service started successfully")

            # Monitor the process
            while self.running:
                if self.api_process.poll() is not None:
                    # Process has terminated
                    stdout, stderr = self.api_process.communicate()
                    logger.error(f"❌ FastAPI process terminated unexpectedly")
                    logger.error(f"STDOUT: {stdout}")
                    logger.error(f"STDERR: {stderr}")
                    break

                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            logger.error(f"❌ Failed to start FastAPI server: {e}")

    def stop_services(self):
        """Stop all running services gracefully"""
        logger.info("🔄 Stopping all services...")
        self.running = False

        if self.telegram_process and self.telegram_process.poll() is None:
            logger.info("🔄 Stopping Telegram Bot service...")
            self.telegram_process.terminate()
            try:
                self.telegram_process.wait(timeout=10)
                logger.info("✅ Telegram Bot service stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Force killing Telegram Bot service...")
                self.telegram_process.kill()

        if self.api_process and self.api_process.poll() is None:
            logger.info("🔄 Stopping FastAPI service...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
                logger.info("✅ FastAPI service stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Force killing FastAPI service...")
                self.api_process.kill()

        logger.info("✅ All services stopped")

    async def run_services(self):
        """Run both services concurrently"""
        self.running = True

        logger.info("🚀 Starting dual service mode...")
        logger.info("📝 Services to run:")
        logger.info("   - Telegram Bot (if main.py exists)")
        logger.info("   - FastAPI Server")
        logger.info("🔄 Press Ctrl+C to stop all services")

        try:
            # Start both services concurrently
            await asyncio.gather(
                self.start_telegram_bot(),
                self.start_api_server(),
                return_exceptions=True,
            )
        except Exception as e:
            logger.error(f"❌ Error in service management: {e}")
        finally:
            self.stop_services()


class APIOnlyRunner:
    """Lightweight runner for API-only mode"""

    def __init__(self):
        self.api_process = None

    async def run_api_only(self):
        """Run only the FastAPI server"""
        logger.info("🚀 Starting API-only mode...")
        logger.info("📝 Service: FastAPI Server only")
        logger.info("🔄 Press Ctrl+C to stop the service")

        try:
            # Import and run FastAPI directly
            import uvicorn
            from api_server import app
            import config

            uvicorn.run(
                app,
                host=config.API_HOST,
                port=config.API_PORT,
                log_level="info",
                access_log=True,
            )

        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")


def setup_signal_handlers(service_manager):
    """Setup signal handlers for graceful shutdown"""

    def signal_handler(signum, frame):
        logger.info(f"🔄 Received signal {signum}, shutting down gracefully...")
        service_manager.stop_services()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "api-only":
            # Run only FastAPI server
            runner = APIOnlyRunner()
            await runner.run_api_only()
            return
        elif mode == "help":
            print_help()
            return
        else:
            logger.warning(f"⚠️  Unknown mode: {mode}")
            print_help()
            return

    # Default: Run both services
    service_manager = ServiceManager()
    setup_signal_handlers(service_manager)

    try:
        await service_manager.run_services()
    except KeyboardInterrupt:
        logger.info("🔄 Received keyboard interrupt, shutting down...")
        service_manager.stop_services()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        service_manager.stop_services()


def print_help():
    """Print usage help"""
    help_text = """
🚀 Background Remover Service Runner

Usage:
    python run_services.py [mode]

Modes:
    (no argument)  - Run both Telegram Bot and FastAPI server (default)
    api-only       - Run only FastAPI server
    help           - Show this help message

Examples:
    python run_services.py              # Run both services
    python run_services.py api-only     # Run API server only
    python run_services.py help         # Show help

API Endpoints (when running):
    http://localhost:8000/docs           # Swagger UI documentation
    http://localhost:8000/redoc          # ReDoc documentation
    http://localhost:8000/api/health     # Health check
    http://localhost:8000/api/remove-background  # Background removal
    http://localhost:8000/api/pas-foto   # Passport photo creation

Configuration:
    Check config.py for API settings
    Check .env for environment variables
    """
    print(help_text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Service runner stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
