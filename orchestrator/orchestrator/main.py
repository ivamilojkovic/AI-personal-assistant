"""
Main entry point for Orchestrator Agent.
"""
import asyncio
import argparse
from orchestrator.a2a.server import start_server
from orchestrator.core.logger import Logger

logger = Logger.get_logger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Email Orchestrator Agent")
    parser.add_argument(
        "--mode",
        choices=["server"],
        default="server",
        help="Run mode (currently only 'server' is supported)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "server":
        logger.info("Starting orchestrator in server mode...")
        start_server()
    else:
        logger.error(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()