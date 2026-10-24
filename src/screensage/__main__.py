"""Command-line entry point."""

from screensage.app import run


def main() -> int:
    """Run ScreenSage."""
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
