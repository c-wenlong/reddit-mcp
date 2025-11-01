# JSON-RPC in MCP Servers

## What is JSON-RPC?

JSON-RPC is a lightweight remote procedure call (RPC) protocol that uses JSON for data exchange. In MCP servers, it's how the client and server communicate.

## Basic Structure

Every JSON-RPC message has these fields:

```json
{
  "jsonrpc": "2.0",  // Protocol version (always "2.0")
  "id": 1,          // Request ID (for matching responses)
  "method": "initialize",  // Method name
  "params": { ... }  // Parameters (optional)
}
```

## Two Types of Messages

### 1. **Requests** - Client asks server to do something
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### 2. **Notifications** - One-way messages (no response expected)

MCP supports these notification types:

**Progress Notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progressToken": "token-123",
    "progress": {
      "type": "step",
      "label": "Fetching Reddit posts...",
      "percentage": 50
    }
  }
}
```

**Cancelled Notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/cancelled",
  "params": {
    "requestId": 1,
    "reason": "User cancelled"
  }
}
```

**Initialized Notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized",
  "params": {}
}
```

(Notice: No `id` field in notifications - they are fire-and-forget)

## How It Works in Your MCP Server

### Step 1: Initialization
Client sends:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "cursor",
      "version": "1.0"
    }
  }
}
```

Server responds:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "reddit-startup-ideator",
      "version": "0.1.0"
    }
  }
}
```

### Step 2: List Available Tools
Client sends:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

Server responds:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "search_reddit_problems",
        "description": "Search Reddit for posts that likely indicate problems...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Search query to find problem-related posts"
            },
            "limit": {
              "type": "integer",
              "default": 20
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "get_trending_problems",
        ...
      }
    ]
  }
}
```

### Step 3: Call a Tool
Client sends:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_reddit_problems",
    "arguments": {
      "query": "I wish there was a tool",
      "limit": 10
    }
  }
}
```

Server responds:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"query\": \"I wish there was a tool\", \"results_count\": 10, \"posts\": [...]}"
      }
    ]
  }
}
```

### Error Response
If something goes wrong:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Reddit API error: Rate limit exceeded"
  }
}
```

## Communication Flow

```
┌─────────┐                    ┌─────────┐
│ Client  │                    │ Server │
└────┬────┘                    └────┬───┘
     │                              │
     │ 1. initialize (request)      │
     │──────────────────────────────>│
     │                              │
     │ 2. initialize (response)     │
     │<──────────────────────────────│
     │                              │
     │ 3. tools/list (request)      │
     │──────────────────────────────>│
     │                              │
     │ 4. tools/list (response)     │
     │<──────────────────────────────│
     │                              │
     │ 5. tools/call (request)     │
     │──────────────────────────────>│
     │                              │
     │ 6. tools/call (response)     │
     │<──────────────────────────────│
     │                              │
```

## How Your Server Uses It

Looking at your `server.py`:

1. **`stdio_server()`** - Sets up stdin/stdout for JSON-RPC communication
2. **`@app.list_tools()`** - Handles `tools/list` requests
3. **`@app.call_tool()`** - Handles `tools/call` requests

The MCP library (`mcp.server`) automatically:
- Parses incoming JSON-RPC messages from stdin
- Routes to your handlers (`list_tools`, `call_tool`)
- Serializes responses to JSON
- Writes to stdout

You don't manually parse JSON - the framework does it!

## Transport: stdio vs HTTP

Your server uses **stdio** (standard input/output):
- Messages sent via stdin/stdout
- No network ports needed
- Process-to-process communication

Some MCP servers use **HTTP** instead:
- Messages sent via HTTP POST requests
- Requires a port (e.g., `localhost:3000`)
- Network-based communication

## Example: Manual Test

To manually test JSON-RPC communication:

```bash
# Write a request to a file
cat > request.json <<EOF
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
EOF

# Send it to your server
cat request.json | python server.py
```

The server will read the JSON from stdin, process it, and write the response to stdout.

