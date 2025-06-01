import asyncio

from dotenv import load_dotenv

from src.app import PickleballCourtApp


async def main() -> None:
    """Run the Pickleball Court Availability Checker."""
    # Load environment variables from .env file
    load_dotenv()

    # Create and run the app
    app = PickleballCourtApp(
        days=["Tuesday", "Thursday", "Saturday", "Sunday"], times=["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
    )
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
