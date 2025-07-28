"""
Dual Service Runner - Background Remover Bot & API
Professional implementation untuk menjalankan Telegram Bot dan FastAPI server secara bersamaan

Usage:
    python run_dual_services.py                 # Run both services
    python run_dual_services.py --api-only      # Run API only
    python run_dual_services.py --bot-only      # Run Bot only
    python run_dual_services.py --help          # Show help

Features:
- Concurrent service management dengan asyncio
- Graceful shutdown handling
- Automatic restart on service failure
- Comprehensive logging dan monitoring
- Environment validation
- Resource cleanup
"""

import asyncio
import subprocess
import sys
import signal
import os
import argparse
import logging
import time
from pathlib import Path
from typing import Optional, List
import threading

# Setup comprehensive logging dengan Windows Unicode support
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dual_services.log", encoding="utf-8"),
        # StreamHandler dengan fallback untuk Windows console encoding
        logging.StreamHandler(),
    ],
)

# Fix Windows console encoding issues
import sys

if sys.platform.startswith("win"):
    try:
        # Try to set UTF-8 encoding untuk Windows console
        import os

        os.system("chcp 65001 > nul")
    except Exception:
        pass

logger = logging.getLogger(__name__)


class ServiceProcess:
    """
    Professional wrapper untuk managing individual service processes
    """

    def __init__(self, name: str, command: List[str], description: str):
        self.name = name
        self.command = command
        self.description = description
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.max_restarts = 3
        self.start_time = None
        self.is_running = False

    def start(self) -> bool:
        """Start the service process"""
        try:
            logger.info(f"🚀 Starting {self.name} service...")
            logger.info(f"📋 Command: {' '.join(self.command)}")

            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            self.start_time = time.time()
            self.is_running = True
            logger.info(
                f"✅ {self.name} service started successfully (PID: {self.process.pid})"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start {self.name} service: {e}")
            return False

    def stop(self) -> bool:
        """Stop the service process gracefully"""
        if not self.process or not self.is_running:
            return True

        try:
            logger.info(f"🔄 Stopping {self.name} service...")

            # Try graceful shutdown first
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
                logger.info(f"✅ {self.name} service stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning(f"⚠️  Force killing {self.name} service...")
                self.process.kill()
                self.process.wait()
                logger.info(f"✅ {self.name} service force stopped")

            self.is_running = False
            return True

        except Exception as e:
            logger.error(f"❌ Error stopping {self.name} service: {e}")
            return False

    def is_alive(self) -> bool:
        """Check if the service process is still running"""
        if not self.process or not self.is_running:
            return False

        return self.process.poll() is None

    def get_status(self) -> dict:
        """Get comprehensive status information"""
        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "name": self.name,
            "description": self.description,
            "is_running": self.is_running,
            "is_alive": self.is_alive(),
            "pid": self.process.pid if self.process else None,
            "restart_count": self.restart_count,
            "uptime_seconds": uptime,
            "uptime_formatted": f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s",
        }


class DualServiceManager:
    """
    Professional service manager untuk mengelola Telegram Bot dan FastAPI server
    """

    def __init__(self):
        self.services: List[ServiceProcess] = []
        self.running = False
        self.shutdown_requested = False

        # Setup signal handlers untuk graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Validate environment
        self._validate_environment()

    def _validate_environment(self):
        """Validate yang semua requirements terpenuhi"""
        logger.info("🔍 Validating environment...")

        # Check virtual environment
        if not hasattr(sys, "real_prefix") and not (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            logger.warning(
                "⚠️  Virtual environment not detected. Recommended to use .venv"
            )

        # Check required files
        required_files = ["main.py", "config.py", "src/api/main.py"]
        for file_path in required_files:
            if not Path(file_path).exists():
                logger.error(f"❌ Required file not found: {file_path}")
                sys.exit(1)

        # Check .env file
        if not Path(".env").exists():
            logger.warning(
                "⚠️  .env file not found. Some configurations may use defaults"
            )

        logger.info("✅ Environment validation passed")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🔄 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        self.stop_all_services()
        sys.exit(0)

    def add_service(self, name: str, command: List[str], description: str):
        """Add a service to be managed"""
        service = ServiceProcess(name, command, description)
        self.services.append(service)
        logger.info(f"➕ Added service: {name}")

    def start_all_services(self):
        """Start all registered services"""
        logger.info("🚀 Starting dual service mode...")
        logger.info("📋 Services to start:")

        for service in self.services:
            logger.info(f"   - {service.name}: {service.description}")

        print("=" * 80)
        print("*** BACKGROUND REMOVER DUAL SERVICE MODE ***")
        print("=" * 80)
        print("Bot: Handles user interactions via Telegram")
        print("API: Provides REST API for Next.js integration")
        print("API Documentation: http://localhost:8000/docs")
        print("Press Ctrl+C to stop all services")
        print("=" * 80)

        # Start all services
        failed_services = []
        for service in self.services:
            if not service.start():
                failed_services.append(service.name)

        if failed_services:
            logger.error(f"❌ Failed to start services: {', '.join(failed_services)}")
            self.stop_all_services()
            return False

        self.running = True
        logger.info("✅ All services started successfully")
        return True

    def stop_all_services(self):
        """Stop all services gracefully"""
        if not self.running:
            return

        logger.info("🔄 Stopping all services...")
        self.running = False

        # Stop all services
        for service in self.services:
            service.stop()

        logger.info("✅ All services stopped")

    def monitor_services(self):
        """Monitor services dan restart jika perlu"""
        logger.info("👁️  Starting service monitoring...")

        while self.running and not self.shutdown_requested:
            try:
                # Check each service
                for service in self.services:
                    if not service.is_alive() and service.is_running:
                        logger.warning(f"⚠️  {service.name} service died unexpectedly")

                        if service.restart_count < service.max_restarts:
                            logger.info(
                                f"🔄 Attempting to restart {service.name} (attempt {service.restart_count + 1})"
                            )
                            service.restart_count += 1
                            service.start()
                        else:
                            logger.error(
                                f"❌ {service.name} exceeded max restart attempts, giving up"
                            )
                            service.is_running = False

                # Check if all services are dead
                alive_services = [s for s in self.services if s.is_alive()]
                if not alive_services:
                    logger.error("❌ All services are dead, shutting down")
                    break

                # Wait before next check
                time.sleep(5)

            except Exception as e:
                logger.error(f"❌ Error in service monitoring: {e}")
                break

        logger.info("👁️  Service monitoring stopped")

    def print_status(self):
        """Print comprehensive status of all services dengan Windows compatibility"""
        print("\n" + "=" * 80)
        print("*** SERVICE STATUS REPORT ***")
        print("=" * 80)

        for service in self.services:
            status = service.get_status()
            status_icon = "[OK]" if status["is_alive"] else "[STOPPED]"

            print(f"{status_icon} {status['name']}:")
            print(f"   Description: {status['description']}")
            print(f"   Status: {'Running' if status['is_alive'] else 'Stopped'}")
            print(f"   PID: {status['pid'] or 'N/A'}")
            print(f"   Uptime: {status['uptime_formatted']}")
            print(f"   Restart Count: {status['restart_count']}")
            print()

        print("=" * 80)

    def run(self):
        """Main execution loop"""
        try:
            # Start all services
            if not self.start_all_services():
                return False

            # Run monitoring in background thread
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()

            # Print initial status
            time.sleep(2)  # Wait for services to initialize
            self.print_status()

            # Keep main thread alive
            while self.running and not self.shutdown_requested:
                time.sleep(10)  # Status update interval

                # Print periodic status
                if self.running:
                    self.print_status()

        except KeyboardInterrupt:
            logger.info("🔄 Keyboard interrupt received, shutting down...")
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
        finally:
            self.stop_all_services()

        return True


def create_service_manager(mode: str = "dual") -> DualServiceManager:
    """
    Factory function untuk create service manager dengan configuration yang tepat
    """
    manager = DualServiceManager()

    # Get Python executable path
    python_exe = sys.executable

    if mode in ["dual", "bot"]:
        # Add Telegram Bot service
        manager.add_service(
            name="Telegram Bot",
            command=[python_exe, "main.py"],
            description="Telegram Bot untuk user interactions",
        )

    if mode in ["dual", "api"]:
        # Add FastAPI service
        manager.add_service(
            name="FastAPI Server",
            command=[
                python_exe,
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
            ],
            description="FastAPI REST API server",
        )

    return manager


def main():
    """Main entry point dengan argument parsing"""
    parser = argparse.ArgumentParser(
        description="Background Remover Dual Service Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_dual_services.py              # Run both services (default)
    python run_dual_services.py --api-only   # Run API server only
    python run_dual_services.py --bot-only   # Run Telegram bot only
    python run_dual_services.py --help       # Show this help
        """,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--api-only", action="store_true", help="Run FastAPI server only"
    )
    group.add_argument("--bot-only", action="store_true", help="Run Telegram bot only")

    args = parser.parse_args()

    # Determine mode
    if args.api_only:
        mode = "api"
    elif args.bot_only:
        mode = "bot"
    else:
        mode = "dual"

    logger.info(f"🎯 Starting in {mode.upper()} mode")

    # Create dan run service manager
    manager = create_service_manager(mode)
    success = manager.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
