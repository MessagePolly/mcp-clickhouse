"""Thread-based session handler for MCP requests.

This module provides a custom handler that accepts thread IDs as session IDs
and processes MCP requests without FastMCP's session management.
"""

import logging
import json
from typing import Dict, Any, Optional
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastmcp.exceptions import ToolError

logger = logging.getLogger("mcp-clickhouse.thread_session")


async def handle_thread_session_request(request: Request, mcp_instance) -> JSONResponse:
    """Handle MCP requests using thread IDs as session IDs.

    This bypasses FastMCP's session management and directly processes requests.

    Args:
        request: The incoming HTTP request
        mcp_instance: The FastMCP instance with registered tools

    Returns:
        JSONResponse with the result or error
    """
    try:
        # Extract session ID from headers
        session_id = (
            request.headers.get("X-Session-ID") or
            request.headers.get("mcp-session-id") or
            request.headers.get("x-session-id")
        )

        if not session_id:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": "No session ID provided in headers"
                },
                "id": None
            }, status_code=400)

        # Parse request body
        body = await request.json()
        method = body.get("method", "")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"Thread session {session_id}: {method} with params {params}")

        # Handle different methods
        if method == "tools/list":
            # Return list of available tools
            tools = []
            # FastMCP stores tools in _tools dictionary
            if hasattr(mcp_instance, '_tools'):
                for tool_name, tool_def in mcp_instance._tools.items():
                    tool_info = {
                        "name": tool_name,
                        "description": tool_def.description if hasattr(tool_def, 'description') else f"Tool: {tool_name}"
                    }
                    # Add input schema if available
                    if hasattr(tool_def, 'input_schema'):
                        tool_info["inputSchema"] = tool_def.input_schema
                    tools.append(tool_info)

            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            })

        elif method == "tools/call":
            # Call a specific tool
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if not tool_name:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": "Tool name not provided"
                    },
                    "id": request_id
                }, status_code=400)

            # Find and execute the tool
            if hasattr(mcp_instance, '_tools') and tool_name in mcp_instance._tools:
                tool_def = mcp_instance._tools[tool_name]
                try:
                    # Execute the tool - FastMCP tools have a handler function
                    if hasattr(tool_def, 'handler'):
                        result = await tool_def.handler(**tool_args)
                    else:
                        # Fallback to direct call if it's a function
                        result = await tool_def(**tool_args)

                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result) if not isinstance(result, str) else result
                                }
                            ]
                        },
                        "id": request_id
                    })
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": f"Tool execution failed: {str(e)}"
                        },
                        "id": request_id
                    }, status_code=500)
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    },
                    "id": request_id
                }, status_code=404)

        elif method == "prompts/list":
            # Return list of available prompts
            prompts = []
            if hasattr(mcp_instance, '_prompts'):
                for prompt_name in mcp_instance._prompts:
                    prompts.append({"name": prompt_name})

            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {"prompts": prompts},
                "id": request_id
            })

        else:
            # Unknown method
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }, status_code=404)

    except json.JSONDecodeError as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            },
            "id": None
        }, status_code=400)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": None
        }, status_code=500)
