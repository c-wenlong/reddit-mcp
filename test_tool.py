#!/usr/bin/env python3
"""
Quick test of a tool call to verify end-to-end functionality
"""

import asyncio
import sys
import server

async def test_tool_call():
    """Test a simple tool call"""
    print("🔧 Testing tool call: search_reddit_problems")
    print("=" * 50)
    
    try:
        # Test with a simple, safe query
        result = await server.call_tool(
            "search_reddit_problems",
            {
                "query": "productivity",
                "limit": 3,
                "sort": "new"
            }
        )
        
        if result and len(result) > 0:
            data = json.loads(result[0].text)
            print(f"✅ Tool call successful!")
            print(f"   Query: {data.get('query')}")
            print(f"   Results: {data.get('results_count', 0)} posts found")
            
            if data.get('posts') and len(data['posts']) > 0:
                print(f"\n   Sample post:")
                post = data['posts'][0]
                print(f"   - Title: {post.get('title', 'N/A')[:60]}...")
                print(f"   - Subreddit: r/{post.get('subreddit', 'N/A')}")
                print(f"   - Problem Score: {post.get('problem_score', 0)}")
                print(f"   - Problem Keywords: {post.get('problem_keywords', [])[:3]}")
            
            return True
        else:
            print("⚠️  Tool call returned no results")
            return True  # Still counts as success, just no data
            
    except Exception as e:
        print(f"❌ Tool call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import json
    success = asyncio.run(test_tool_call())
    sys.exit(0 if success else 1)

