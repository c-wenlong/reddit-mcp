# MCP Reddit Startup Ideator Server

An MCP (Model Context Protocol) server that helps AI discover new problem spaces and startup ideas by analyzing Reddit discussions.

## Features

This MCP server provides tools to:

1. **Search Reddit for Problems** - Search Reddit posts that indicate problems or unmet needs
2. **Analyze Subreddit Problems** - Analyze entire subreddits to identify common pain points
3. **Get Trending Problems** - Find trending discussions across Reddit that indicate problems
4. **Extract Startup Ideas** - Analyze specific posts and their comments to extract startup opportunities
5. **Discover Problem Patterns** - Find recurring problem patterns across multiple queries/subreddits

## Prerequisites

- Python 3.8 or higher
- Reddit API credentials (Client ID and Client Secret)

## Setup

### 1. Get Reddit API Credentials

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "create another app" or "create app"
3. Select "script" as the app type
4. Fill in the name, description, and redirect URI (use `http://localhost:8080` for script apps)
5. Save your **Client ID** (under the app name) and **Client Secret** (labeled "secret")

### 2. Install Dependencies

**If using `uv` (recommended):**
```bash
uv pip install -r requirements.txt
```

**If using standard `pip`:**
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your Reddit credentials:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MCP Startup Ideator/1.0
```

**Note:** The `user_agent` should be a unique identifier for your application. Reddit requires this for API access.

### 4. Configure MCP Client

Add this server to your MCP client configuration. For example, in Claude Desktop, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "reddit-startup-ideator": {
      "command": "/path/to/python/interpreter",
      "args": ["/path/to/mcp-startup-ideator/server.py"],
      "env": {
        "REDDIT_CLIENT_ID": "your_client_id_here",
        "REDDIT_CLIENT_SECRET": "your_client_secret_here",
        "REDDIT_USER_AGENT": "MCP Startup Ideator/1.0"
      }
    }
  }
}
```

**Note:** If using `uv`, you must use `uv run` to execute the server so it uses the correct Python environment with installed packages.

## Available Tools

### 1. search_reddit_problems

Search Reddit for posts that likely indicate problems or unmet needs.

**Parameters:**
- `query` (required): Search query string
- `subreddit` (optional): Limit search to specific subreddit
- `limit` (optional): Number of posts (default: 20, max: 100)
- `sort` (optional): Sort order - "relevance", "hot", "top", "new", "comments"
- `time_filter` (optional): Time filter for "top" sort - "hour", "day", "week", "month", "year", "all"

### 2. analyze_subreddit_problems

Analyze a subreddit to identify common problems, pain points, and unmet needs.

**Parameters:**
- `subreddit` (required): Subreddit name (without r/)
- `limit` (optional): Number of posts to analyze (default: 50)
- `sort` (optional): Sort order - "hot", "top", "new", "rising"
- `time_filter` (optional): Time filter - "hour", "day", "week", "month", "year", "all"

### 3. get_trending_problems

Get trending discussions across Reddit that indicate problems.

**Parameters:**
- `subreddits` (optional): Array of subreddit names to search
- `limit` (optional): Number of posts (default: 30)
- `min_score` (optional): Minimum upvote score (default: 10)
- `min_comments` (optional): Minimum number of comments (default: 5)

### 4. get_startup_ideas_from_post

Analyze a specific Reddit post to extract potential startup ideas.

**Parameters:**
- `post_url` (required): Full URL to Reddit post
- `include_comments` (optional): Include comments in analysis (default: true)
- `comment_limit` (optional): Number of top comments to analyze (default: 20)

### 5. discover_problem_patterns

Discover recurring problem patterns across multiple subreddits or queries.

**Parameters:**
- `queries` (required): Array of search queries
- `subreddits` (optional): Array of subreddit names to limit search
- `posts_per_query` (optional): Posts to analyze per query (default: 10)

## Usage Examples

### Example 1: Search for Problem Posts

```
Use search_reddit_problems with:
- query: "I wish there was a tool for"
- limit: 20
- sort: "top"
- time_filter: "month"
```

### Example 2: Analyze a Subreddit

```
Use analyze_subreddit_problems with:
- subreddit: "entrepreneur"
- limit: 50
- sort: "top"
- time_filter: "week"
```

### Example 3: Find Trending Problems

```
Use get_trending_problems with:
- limit: 30
- min_score: 50
- min_comments: 10
```

## How It Works

The server uses Reddit's public API via PRAW (Python Reddit API Wrapper) to:

1. Search and retrieve Reddit posts and comments
2. Analyze text for problem indicators using pattern matching (keywords like "frustrated", "wish", "need", "problem", etc.)
3. Calculate a "problem score" based on:
   - Number of problem keywords found
   - Post upvote score
   - Number of comments
4. Aggregate and rank results to identify the most significant problems
5. Extract potential startup opportunities from problem patterns

## Problem Detection

The server identifies problems using regex patterns that match common problem indicators:

- Frustration words: "frustrated", "annoying", "hate", "sucks"
- Problem statements: "doesn't work", "broken", "bug", "issue"
- Wish statements: "wish", "need", "want"
- Help-seeking: "why isn't there", "how do I", "can anyone help"
- Difficulty indicators: "unable to", "hard to", "impossible"

## Rate Limits

Reddit's API has rate limits:
- 60 requests per minute for authenticated requests
- The server respects these limits through PRAW's built-in rate limiting

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

