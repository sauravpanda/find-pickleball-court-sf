import asyncio
import sys
from typing import Optional

from dotenv import load_dotenv

from src.app import PickleballCourtApp
from src.exceptions import PickleballCheckerError
from src.logger import setup_logger


async def main() -> Optional[int]:
    """Run the Pickleball Court Availability Checker.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Set up logging
    logger = setup_logger(level="INFO")
    
    try:
        # Load environment variables from .env file
        load_dotenv()
        logger.info("Starting Pickleball Court Availability Checker")

        # Create and run the app with default settings
        app = PickleballCourtApp()
        await app.run()
        
        logger.info("Application completed successfully")
        return 0
        
    except PickleballCheckerError as e:
        logger.error(f"Application error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    if exit_code:
        sys.exit(exit_code)
