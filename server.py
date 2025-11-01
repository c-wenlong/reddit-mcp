#!/usr/bin/env python3
"""
MCP Server for Reddit Problem Discovery
Helps AI discover new problem spaces and startup ideas on Reddit
"""

import os
import sys
from typing import Any, Sequence
import json
from datetime import datetime, timedelta
import re

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import praw
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for running blocking PRAW operations
_executor = ThreadPoolExecutor(max_workers=4)

# Timeout for Reddit API operations (seconds)
REDDIT_API_TIMEOUT = 30

# Initialize Reddit client
def get_reddit_client():
    """Initialize and return Reddit client using PRAW"""
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        user_agent=os.getenv("REDDIT_USER_AGENT", "MCP Startup Ideator/1.0"),
        request_timeout=REDDIT_API_TIMEOUT,
    )
    return reddit

async def run_blocking(func, *args, **kwargs):
    """Run blocking function in thread pool with timeout"""
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(_executor, func, *args, **kwargs),
        timeout=REDDIT_API_TIMEOUT
    )

def fetch_posts_sync(subreddit, method_name, limit, query=None, sort=None, time_filter=None):
    """Synchronous helper to fetch posts from Reddit"""
    if method_name == "search":
        if query:
            return list(subreddit.search(query, limit=limit, sort=sort or "relevance"))
        else:
            return list(subreddit.search(limit=limit, sort=sort or "relevance"))
    elif method_name == "top":
        return list(subreddit.top(limit=limit, time_filter=time_filter or "week"))
    elif method_name == "hot":
        return list(subreddit.hot(limit=limit))
    elif method_name == "new":
        return list(subreddit.new(limit=limit))
    elif method_name == "rising":
        return list(subreddit.rising(limit=limit))
    else:
        return list(subreddit.hot(limit=limit))

async def fetch_posts_async(subreddit, method_name, limit, query=None, sort=None, time_filter=None):
    """Async wrapper for fetching posts"""
    return await run_blocking(fetch_posts_sync, subreddit, method_name, limit, query, sort, time_filter)

# Initialize MCP Server
app = Server("reddit-startup-ideator")

def extract_problem_keywords(text: str) -> list[str]:
    """Extract potential problem indicators from text"""
    problem_patterns = [
        r'\b(?:frustrated|annoying|hate|sucks|broken|doesn\'t work|wish|need|want|struggle|difficult|pain|problem|issue|bug|glitch)\w*',
        r'\b(?:why isn\'t there|why doesn\'t|how do I|can anyone help|does anyone else|looking for|searching for)\b',
        r'\b(?:unable to|cannot|cant|hard to|impossible|tired of|fed up with)\b',
    ]
    keywords = []
    text_lower = text.lower()
    for pattern in problem_patterns:
        matches = re.findall(pattern, text_lower)
        keywords.extend(matches)
    return list(set(keywords[:10]))  # Return unique keywords, limit to 10

def analyze_post_for_problems(post: Any) -> dict:
    """Analyze a Reddit post for problem indicators"""
    title = post.title
    selftext = post.selftext if hasattr(post, 'selftext') else ""
    combined_text = f"{title} {selftext}"
    
    problem_keywords = extract_problem_keywords(combined_text)
    score = post.score
    num_comments = post.num_comments
    created_utc = datetime.fromtimestamp(post.created_utc)
    
    # Calculate problem score (higher = more likely a problem)
    problem_score = len(problem_keywords) + (score / 100) + (num_comments / 50)
    
    return {
        "title": title,
        "text": selftext[:500] + "..." if len(selftext) > 500 else selftext,
        "url": f"https://reddit.com{post.permalink}",
        "subreddit": str(post.subreddit),
        "score": score,
        "comments": num_comments,
        "created": created_utc.isoformat(),
        "problem_keywords": problem_keywords,
        "problem_score": round(problem_score, 2),
        "author": str(post.author) if post.author else "[deleted]",
    }

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for Reddit problem discovery"""
    return [
        Tool(
            name="search_reddit_problems",
            description="Search Reddit for posts that likely indicate problems or unmet needs. Searches Reddit posts and returns results sorted by problem indicators.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find problem-related posts"
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Optional: Limit search to a specific subreddit"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to return (default: 20, max: 100)",
                        "default": 20
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'relevance', 'hot', 'top', 'new', 'comments'",
                        "enum": ["relevance", "hot", "top", "new", "comments"],
                        "default": "relevance"
                    },
                    "time_filter": {
                        "type": "string",
                        "description": "Time filter for 'top' sort: 'hour', 'day', 'week', 'month', 'year', 'all'",
                        "enum": ["hour", "day", "week", "month", "year", "all"],
                        "default": "week"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_subreddit_problems",
            description="Analyze a subreddit to identify common problems, pain points, and unmet needs discussed by the community. Returns aggregated insights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Name of the subreddit to analyze (without r/)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to analyze (default: 50, max: 100)",
                        "default": 50
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'hot', 'top', 'new', 'rising'",
                        "enum": ["hot", "top", "new", "rising"],
                        "default": "top"
                    },
                    "time_filter": {
                        "type": "string",
                        "description": "Time filter for analysis: 'hour', 'day', 'week', 'month', 'year', 'all'",
                        "enum": ["hour", "day", "week", "month", "year", "all"],
                        "default": "week"
                    }
                },
                "required": ["subreddit"]
            }
        ),
        Tool(
            name="get_trending_problems",
            description="Get trending discussions across Reddit that indicate problems or pain points. Focuses on posts with high engagement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddits": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: List of subreddits to search (without r/). If empty, searches all of Reddit."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to return (default: 30, max: 100)",
                        "default": 30
                    },
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum upvote score (default: 10)",
                        "default": 10
                    },
                    "min_comments": {
                        "type": "integer",
                        "description": "Minimum number of comments (default: 5)",
                        "default": 5
                    }
                }
            }
        ),
        Tool(
            name="get_startup_ideas_from_post",
            description="Analyze a specific Reddit post (by URL) to extract potential startup ideas and problem-solution opportunities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_url": {
                        "type": "string",
                        "description": "Full URL or permalink to the Reddit post"
                    },
                    "include_comments": {
                        "type": "boolean",
                        "description": "Include top comments in analysis (default: true)",
                        "default": True
                    },
                    "comment_limit": {
                        "type": "integer",
                        "description": "Number of top comments to analyze (default: 20)",
                        "default": 20
                    }
                },
                "required": ["post_url"]
            }
        ),
        Tool(
            name="discover_problem_patterns",
            description="Discover recurring problem patterns across multiple subreddits or search queries. Helps identify widespread problems that could be startup opportunities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of search queries to analyze for common patterns"
                    },
                    "subreddits": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: List of subreddits to limit search to"
                    },
                    "posts_per_query": {
                        "type": "integer",
                        "description": "Number of posts to analyze per query (default: 10)",
                        "default": 10
                    }
                },
                "required": ["queries"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    reddit = get_reddit_client()
    
    try:
        if name == "search_reddit_problems":
            query = arguments.get("query")
            subreddit_name = arguments.get("subreddit")
            limit = min(arguments.get("limit", 20), 100)
            sort = arguments.get("sort", "relevance")
            time_filter = arguments.get("time_filter", "week")
            
            subreddit = reddit.subreddit(subreddit_name or "all")
            
            # Use async wrapper for Reddit API calls
            if sort == "relevance":
                posts = await fetch_posts_async(subreddit, "search", limit, query=query, sort=sort)
            elif sort == "top":
                posts = await fetch_posts_async(subreddit, "top", limit, time_filter=time_filter)
            elif sort == "hot":
                posts = await fetch_posts_async(subreddit, "hot", limit)
            elif sort == "new":
                posts = await fetch_posts_async(subreddit, "new", limit)
            else:  # comments
                posts = await fetch_posts_async(subreddit, "search", limit, query=query, sort="comments")
            
            results = [analyze_post_for_problems(post) for post in posts]
            results.sort(key=lambda x: x["problem_score"], reverse=True)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "subreddit": subreddit_name or "all",
                    "results_count": len(results),
                    "posts": results[:limit]
                }, indent=2)
            )]
        
        elif name == "analyze_subreddit_problems":
            subreddit_name = arguments.get("subreddit")
            limit = min(arguments.get("limit", 50), 100)
            sort = arguments.get("sort", "top")
            time_filter = arguments.get("time_filter", "week")
            
            subreddit = reddit.subreddit(subreddit_name)
            
            # Use async wrapper for Reddit API calls
            if sort == "top":
                posts = await fetch_posts_async(subreddit, "top", limit, time_filter=time_filter)
            elif sort == "hot":
                posts = await fetch_posts_async(subreddit, "hot", limit)
            elif sort == "new":
                posts = await fetch_posts_async(subreddit, "new", limit)
            else:  # rising
                posts = await fetch_posts_async(subreddit, "rising", limit)
            
            analyzed_posts = [analyze_post_for_problems(post) for post in posts]
            analyzed_posts.sort(key=lambda x: x["problem_score"], reverse=True)
            
            # Aggregate insights
            all_keywords = []
            for post in analyzed_posts:
                all_keywords.extend(post["problem_keywords"])
            
            keyword_counts = {}
            for keyword in all_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            avg_score = sum(p["score"] for p in analyzed_posts) / len(analyzed_posts) if analyzed_posts else 0
            avg_comments = sum(p["comments"] for p in analyzed_posts) / len(analyzed_posts) if analyzed_posts else 0
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "subreddit": subreddit_name,
                    "analysis_summary": {
                        "posts_analyzed": len(analyzed_posts),
                        "average_score": round(avg_score, 2),
                        "average_comments": round(avg_comments, 2),
                        "top_problem_keywords": [{"keyword": k, "frequency": v} for k, v in top_keywords],
                        "top_problem_posts": analyzed_posts[:10]
                    },
                    "all_posts": analyzed_posts
                }, indent=2)
            )]
        
        elif name == "get_trending_problems":
            subreddits = arguments.get("subreddits", [])
            limit = min(arguments.get("limit", 30), 100)
            min_score = arguments.get("min_score", 10)
            min_comments = arguments.get("min_comments", 5)
            
            all_posts = []
            
            if subreddits:
                for subreddit_name in subreddits:
                    try:
                        subreddit = reddit.subreddit(subreddit_name)
                        posts = await fetch_posts_async(subreddit, "hot", limit // len(subreddits) + 5)
                        all_posts.extend(posts)
                    except Exception as e:
                        continue
            else:
                # Get from r/all
                all_subreddit = reddit.subreddit("all")
                all_posts = await fetch_posts_async(all_subreddit, "hot", limit * 2)
            
            # Filter and analyze
            filtered_posts = [
                p for p in all_posts 
                if p.score >= min_score and p.num_comments >= min_comments
            ]
            
            analyzed_posts = [analyze_post_for_problems(post) for post in filtered_posts]
            analyzed_posts.sort(key=lambda x: x["problem_score"], reverse=True)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "scope": subreddits if subreddits else "all",
                    "filters": {
                        "min_score": min_score,
                        "min_comments": min_comments
                    },
                    "results_count": len(analyzed_posts),
                    "trending_problems": analyzed_posts[:limit]
                }, indent=2)
            )]
        
        elif name == "get_startup_ideas_from_post":
            post_url = arguments.get("post_url")
            include_comments = arguments.get("include_comments", True)
            comment_limit = arguments.get("comment_limit", 20)
            
            # Extract submission ID from URL
            submission_id = None
            if "/comments/" in post_url:
                parts = post_url.split("/comments/")
                if len(parts) > 1:
                    submission_id = parts[1].split("/")[0]
            
            if not submission_id:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Invalid Reddit post URL"}, indent=2)
                )]
            
            # Fetch submission asynchronously
            def get_submission_sync():
                return reddit.submission(id=submission_id)
            
            submission = await run_blocking(get_submission_sync)
            post_analysis = analyze_post_for_problems(submission)
            
            insights = {
                "post": post_analysis,
                "potential_problems": post_analysis["problem_keywords"],
                "startup_opportunities": []
            }
            
            if include_comments:
                # Replace "more comments" and fetch asynchronously
                def fetch_comments_sync():
                    submission.comments.replace_more(limit=0)
                    return submission.comments.list()[:comment_limit]
                
                top_comments = await run_blocking(fetch_comments_sync)
                
                comment_insights = []
                for comment in top_comments:
                    if hasattr(comment, 'body') and comment.body and comment.body != "[deleted]":
                        comment_keywords = extract_problem_keywords(comment.body)
                        if comment_keywords:
                            comment_insights.append({
                                "text": comment.body[:300] + "..." if len(comment.body) > 300 else comment.body,
                                "score": comment.score,
                                "problem_keywords": comment_keywords
                            })
                
                insights["top_comments"] = comment_insights
                
                # Aggregate insights
                all_problem_keywords = post_analysis["problem_keywords"].copy()
                for comment in comment_insights:
                    all_problem_keywords.extend(comment["problem_keywords"])
                
                keyword_freq = {}
                for keyword in all_problem_keywords:
                    keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
                
                top_problems = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                
                insights["aggregated_problems"] = [
                    {"problem_indicator": k, "mentions": v} 
                    for k, v in top_problems
                ]
                
                startup_opps = []
                for prob in insights["aggregated_problems"]:
                    startup_opps.append(f"Problem: {prob['problem_indicator']} (mentioned {prob['mentions']} times)")
                    startup_opps.append(f"Opportunity: Build a solution addressing '{prob['problem_indicator']}' mentioned in r/{post_analysis['subreddit']}")
                insights["startup_opportunities"] = startup_opps
            
            return [TextContent(
                type="text",
                text=json.dumps(insights, indent=2)
            )]
        
        elif name == "discover_problem_patterns":
            queries = arguments.get("queries")
            subreddits = arguments.get("subreddits", [])
            posts_per_query = arguments.get("posts_per_query", 10)
            
            all_posts = []
            
            search_scope = subreddits if subreddits else ["all"]
            
            for query in queries:
                for subreddit_name in search_scope:
                    try:
                        if subreddit_name == "all":
                            all_subreddit = reddit.subreddit("all")
                            posts = await fetch_posts_async(all_subreddit, "search", posts_per_query, query=query)
                        else:
                            subreddit = reddit.subreddit(subreddit_name)
                            posts = await fetch_posts_async(subreddit, "search", posts_per_query, query=query)
                        
                        for post in posts:
                            analysis = analyze_post_for_problems(post)
                            analysis["source_query"] = query
                            analysis["source_subreddit"] = subreddit_name
                            all_posts.append(analysis)
                    except Exception as e:
                        continue
            
            # Find patterns
            all_keywords = []
            for post in all_posts:
                all_keywords.extend(post["problem_keywords"])
            
            keyword_patterns = {}
            for keyword in all_keywords:
                keyword_patterns[keyword] = keyword_patterns.get(keyword, 0) + 1
            
            top_patterns = sorted(keyword_patterns.items(), key=lambda x: x[1], reverse=True)[:15]
            
            # Group by subreddit
            subreddit_groups = {}
            for post in all_posts:
                sub = post["subreddit"]
                if sub not in subreddit_groups:
                    subreddit_groups[sub] = []
                subreddit_groups[sub].append(post)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "queries_analyzed": queries,
                    "posts_analyzed": len(all_posts),
                    "recurring_problem_patterns": [
                        {"pattern": k, "frequency": v, "percentage": round(v / len(all_posts) * 100, 2)}
                        for k, v in top_patterns
                    ],
                    "problems_by_subreddit": {
                        sub: {
                            "count": len(posts),
                            "top_problems": sorted(
                                [p for p in posts],
                                key=lambda x: x["problem_score"],
                                reverse=True
                            )[:5]
                        }
                        for sub, posts in subreddit_groups.items()
                    },
                    "potential_startup_ideas": [
                        {
                            "problem": pattern[0],
                            "frequency": pattern[1],
                            "potential_impact": "high" if pattern[1] >= len(all_posts) * 0.1 else "medium" if pattern[1] >= len(all_posts) * 0.05 else "low"
                        }
                        for pattern in top_patterns[:5]
                    ]
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
    
    except asyncio.TimeoutError:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Request timed out",
                "message": f"Reddit API request exceeded {REDDIT_API_TIMEOUT} seconds. Please try again with a smaller limit or more specific query."
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "error_type": type(e).__name__
            }, indent=2)
        )]

async def main():
    """Run the MCP server"""
    # Smithery wraps stdio servers with HTTP automatically
    # The server uses stdio, and Smithery handles the HTTP layer
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

def run():
    """Entry point for the MCP server"""
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())

