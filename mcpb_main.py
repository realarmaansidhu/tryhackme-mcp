"""Entry point for the Claude Desktop extension bundle (.mcpb)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from tryhackme_mcp.server import main  # noqa: E402

if __name__ == "__main__":
    main()
