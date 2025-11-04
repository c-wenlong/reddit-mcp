# JSON-RPC Test Files for Reddit MCP Server

This directory contains test JSON files for testing JSON-RPC communication with the Reddit MCP server.

## Test File Structure

### Initialization Tests
- `01-initialize-request.json` - Client initialization request
- `02-initialize-response.json` - Expected server initialization response

### Tool Listing Tests
- `03-tools-list-request.json` - Request to list all available tools
- `04-tools-list-response.json` - Expected response with all 5 tools

### Tool Call Tests

#### search_reddit_problems
- `05-search-reddit-problems-basic.json` - Basic search with minimal parameters
- `06-search-reddit-problems-full.json` - Full search with all parameters

#### analyze_subreddit_problems
- `07-analyze-subreddit-problems-basic.json` - Basic subreddit analysis
- `08-analyze-subreddit-problems-full.json` - Full subreddit analysis with all parameters

#### get_trending_problems
- `09-get-trending-problems-basic.json` - Basic trending problems (no parameters)
- `10-get-trending-problems-with-subreddits.json` - Trending problems with subreddit filters

#### get_startup_ideas_from_post
- `11-get-startup-ideas-from-post-basic.json` - Basic post analysis
- `12-get-startup-ideas-from-post-full.json` - Full post analysis with comments

#### discover_problem_patterns
- `13-discover-problem-patterns-basic.json` - Basic pattern discovery
- `14-discover-problem-patterns-full.json` - Full pattern discovery with subreddits

### Error Cases
- `15-error-response-invalid-tool.json` - Invalid tool name
- `16-error-response-missing-required-param.json` - Missing required parameter

### Notifications
- `17-notification-initialized.json` - Initialized notification
- `18-notification-progress.json` - Progress notification
- `19-notification-cancelled.json` - Cancelled notification

### Example Responses
- `20-example-response-success.json` - Example successful tool call response
- `21-example-response-error.json` - Example error response

## How to Use These Tests

### Manual Testing with stdio

You can test individual requests by piping them to the server:

```bash
# Test initialization
cat tests/01-initialize-request.json | python server.py

# Test tool listing
cat tests/03-tools-list-request.json | python server.py

# Test a tool call
cat tests/05-search-reddit-problems-basic.json | python server.py
```

### Testing with curl (if using HTTP transport)

If your server is running on HTTP, you can test with curl:

```bash
curl -X POST http://localhost:3000 \
  -H "Content-Type: application/json" \
  -d @tests/05-search-reddit-problems-basic.json
```

### Automated Testing Script

You can create a test script that sends multiple requests:

```bash
#!/bin/bash
# test-all.sh

echo "Testing initialization..."
cat tests/01-initialize-request.json | python server.py

echo "Testing tool listing..."
cat tests/03-tools-list-request.json | python server.py

echo "Testing search..."
cat tests/05-search-reddit-problems-basic.json | python server.py
```

## JSON-RPC Format

All requests follow the JSON-RPC 2.0 specification:

- `jsonrpc`: Always "2.0"
- `id`: Unique request identifier (number or string)
- `method`: Method name (e.g., "initialize", "tools/list", "tools/call")
- `params`: Method parameters (object)

All responses include:
- `jsonrpc`: "2.0"
- `id`: Matching request ID
- Either `result` (success) or `error` (failure)

Notifications (no response expected):
- `jsonrpc`: "2.0"
- `method`: Notification method name
- `params`: Notification parameters
- No `id` field

## Expected Tool Behaviors

### search_reddit_problems
- **Required**: `query`
- **Optional**: `subreddit`, `limit`, `sort`, `time_filter`
- **Returns**: JSON array of posts with problem scores

### analyze_subreddit_problems
- **Required**: `subreddit`
- **Optional**: `limit`, `sort`, `time_filter`
- **Returns**: Aggregated analysis with top keywords and problem posts

### get_trending_problems
- **Optional**: `subreddits`, `limit`, `min_score`, `min_comments`
- **Returns**: Trending posts filtered by engagement metrics

### get_startup_ideas_from_post
- **Required**: `post_url`
- **Optional**: `include_comments`, `comment_limit`
- **Returns**: Analysis with problem keywords and startup opportunities

### discover_problem_patterns
- **Required**: `queries` (array)
- **Optional**: `subreddits`, `posts_per_query`
- **Returns**: Recurring patterns across multiple queries

## Notes

- All test files use valid JSON-RPC 2.0 format
- Request IDs are unique within each test file
- Example responses show expected structure but actual data will vary
- Error responses follow JSON-RPC error code standards:
  - `-32600`: Invalid Request
  - `-32601`: Method not found
  - `-32602`: Invalid params
  - `-32603`: Internal error
  - `-32700`: Parse error

