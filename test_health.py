#!/usr/bin/env python3
"""
Health check script for MCP Reddit Startup Ideator server
Tests basic functionality without requiring Reddit API calls
"""

import asyncio
import json
import sys
from typing import Any

async def test_server_health():
    """Test the MCP server health"""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool
    
    print("🔍 Testing MCP Server Health...")
    print("=" * 50)
    
    # Test 1: Import server module
    try:
        import server
        print("✅ Server module imports successfully")
    except Exception as e:
        print(f"❌ Failed to import server: {e}")
        return False
    
    # Test 2: Check Reddit client initialization
    try:
        reddit = server.get_reddit_client()
        client_id = reddit.config.client_id
        if client_id:
            print(f"✅ Reddit client initialized (Client ID: {client_id[:10]}...)")
        else:
            print("⚠️  Reddit client initialized but no Client ID found (may need .env setup)")
    except Exception as e:
        print(f"⚠️  Reddit client initialization issue: {e}")
        print("   (This is OK if Reddit credentials aren't configured yet)")
    
    # Test 3: Test helper functions
    try:
        test_text = "I'm frustrated with this tool that doesn't work properly"
        keywords = server.extract_problem_keywords(test_text)
        if keywords:
            print(f"✅ Problem keyword extraction works: {keywords}")
        else:
            print("⚠️  Problem keyword extraction returned no keywords")
    except Exception as e:
        print(f"❌ Problem keyword extraction failed: {e}")
        return False
    
    # Test 4: Check server app initialization
    try:
        app = server.app
        if app:
            print(f"✅ MCP server app initialized: {app.name}")
        else:
            print("❌ MCP server app is None")
            return False
    except Exception as e:
        print(f"❌ Failed to get server app: {e}")
        return False
    
    # Test 5: Test list_tools function
    try:
        tools = await server.list_tools()
        if tools and len(tools) > 0:
            print(f"✅ Server exposes {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.name}")
        else:
            print("⚠️  Server returned no tools")
            return False
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        return False
    
    # Test 6: Verify required tools exist
    required_tools = [
        "search_reddit_problems",
        "analyze_subreddit_problems", 
        "get_trending_problems",
        "get_startup_ideas_from_post",
        "discover_problem_patterns"
    ]
    
    tool_names = [tool.name for tool in tools]
    missing_tools = [t for t in required_tools if t not in tool_names]
    
    if missing_tools:
        print(f"❌ Missing required tools: {missing_tools}")
        return False
    else:
        print("✅ All required tools are available")
    
    print("=" * 50)
    print("✅ Server health check PASSED")
    print("\n💡 To test with actual Reddit API calls, ensure:")
    print("   1. REDDIT_CLIENT_ID is set in .env")
    print("   2. REDDIT_CLIENT_SECRET is set in .env")
    print("   3. REDDIT_USER_AGENT is set in .env")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_server_health())
    sys.exit(0 if success else 1)

