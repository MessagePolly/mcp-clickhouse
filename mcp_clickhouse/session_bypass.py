"""Session bypass middleware for FastMCP to accept thread IDs as session IDs.

This module provides a way to bypass FastMCP's session validation and accept
any session ID provided in the headers, treating thread IDs as valid sessions.
"""

import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger("mcp-clickhouse.session_bypass")

# Global session store for thread-based sessions
THREAD_SESSIONS: Dict[str, Dict[str, Any]] = {}


def is_session_bypass_enabled() -> bool:
    """Check if session bypass mode is enabled."""
    return os.getenv("MCP_SESSION_BYPASS", "false").lower() == "true"


def register_thread_session(session_id: str) -> None:
    """Register a thread ID as a valid session.

    Args:
        session_id: The thread/session ID to register
    """
    if session_id and session_id not in THREAD_SESSIONS:
        THREAD_SESSIONS[session_id] = {
            "created_at": None,
            "thread_id": session_id,
            "active": True
        }
        logger.info(f"Registered thread session: {session_id}")


def is_valid_thread_session(session_id: str) -> bool:
    """Check if a session ID is valid (when bypass is enabled).

    Args:
        session_id: The session ID to validate

    Returns:
        True if the session is valid or bypass is enabled
    """
    if not session_id:
        return False

    if is_session_bypass_enabled():
        # In bypass mode, auto-register any session ID
        register_thread_session(session_id)
        return True

    # Normal mode - check if session exists
    return session_id in THREAD_SESSIONS


def extract_session_id(headers: Dict[str, str]) -> Optional[str]:
    """Extract session ID from request headers.

    Looks for session ID in various header formats:
    - X-Session-ID
    - mcp-session-id
    - x-session-id (lowercase)

    Args:
        headers: Request headers dictionary

    Returns:
        The session ID if found, None otherwise
    """
    # Check various header formats
    for header_name in ["X-Session-ID", "mcp-session-id", "x-session-id", "X-Session-Id"]:
        session_id = headers.get(header_name)
        if session_id:
            return session_id

    # Also check lowercase versions
    headers_lower = {k.lower(): v for k, v in headers.items()}
    for header_name in ["x-session-id", "mcp-session-id"]:
        session_id = headers_lower.get(header_name)
        if session_id:
            return session_id

    return None


def clear_thread_sessions() -> None:
    """Clear all thread sessions."""
    global THREAD_SESSIONS
    THREAD_SESSIONS.clear()
    logger.info("Cleared all thread sessions")
