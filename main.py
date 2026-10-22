# /// script
# dependencies = [
#     "cffi",
#     "raylib",
# ]
# ///
"""Entry point for the meditation game (desktop and pygbag web builds)."""

import asyncio

from meditation.game import run


async def main() -> None:
    """Run the meditation game."""
    await run()


asyncio.run(main())
