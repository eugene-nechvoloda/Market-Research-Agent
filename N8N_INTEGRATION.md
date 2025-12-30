# n8n Research Integration - Experimental Branch

This experimental branch implements n8n webhook integration to offload research processing to external n8n workflows.

## Overview

Instead of running research internally, the agent:
1. **Triggers n8n workflow** when research is requested (manual or cron)
2. **n8n processes** the heavy research tasks
3. **Agent receives results** and generates the report
4. **Publishes to Slack & Google Docs** using existing functionality

## Architecture

```
┌─────────────────┐
│  Slack User     │
│  Clicks "Run    │
│  Report"        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Market Research Agent          │
│  (Railway)                      │
│                                 │
│  1. Trigger n8n Webhook ────────┼────►┌──────────────────┐
│     POST to N8N_WEBHOOK_URL     │     │  n8n Workflow    │
│     {date, user_id, params}     │     │                  │
│                                 │     │  - Web scraping  │
│  2. Track request_id            │     │  - API calls     │
│     pending_n8n_requests[id]    │     │  - Data mining   │
│                                 │     │  - Analysis      │
│                                 │     └─────────┬────────┘
│                                 │               │
│  3. Receive Results ◄───────────┼───────────────┘
│     POST to /n8n/webhook        │
│     {request_id, data}          │
│                                 │
│  4. Generate Report             │
│     - Process n8n data          │
│     - Generate markdown/HTML    │
│     - Store in database         │
│     - Export to Google Docs     │
│     - Notify user in Slack      │
└─────────────────────────────────┘
```

## Setup

### 1. Environment Variables

Add to your Railway environment:

```bash
# Required: n8n webhook URL to trigger research
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/dap-research

# Optional: If n8n needs authentication
N8N_WEBHOOK_SECRET=your-secret-key
```

### 2. n8n Workflow Configuration

Your n8n workflow should:

#### Input (from agent):
```json
{
  "timestamp": "2025-12-30T16:30:00Z",
  "source": "dap-market-research-agent",
  "request_type": "research",
  "params": {
    "date": "2025-12-30",
    "focus_areas": [...],
    "competitors": [...]
  }
}
```

#### Output (to agent webhook):
n8n must POST results to: `https://your-agent-url.railway.app/n8n/webhook`

**Success Response:**
```json
{
  "request_id": "unique-request-id",
  "status": "completed",
  "data": {
    "markdown": "# Full markdown report...",
    // OR
    "json": {
      "broad_research": {...},
      "competitor_analysis": {...},
      "user_feedback": {...}
    },
    // OR
    "results": {
      // Any structured data
    }
  }
}
```

**Failure Response:**
```json
{
  "request_id": "unique-request-id",
  "status": "failed",
  "error": "Description of what went wrong"
}
```

### 3. Agent Webhook Endpoint

The agent exposes: `POST /n8n/webhook`

**Headers:**
- `Content-Type: application/json`

**Authentication:** (Optional - add if needed)
You can add authentication by checking for a secret header or token.

## Data Formats

n8n can return data in two formats:

### Option 1: Raw Markdown (Recommended)
If your n8n workflow generates the complete markdown report:

```json
{
  "request_id": "abc123",
  "status": "completed",
  "data": {
    "markdown": "# 🚀 Executive Summary\n\n[Your complete report...]"
  }
}
```

Agent will:
- Use the markdown directly
- Convert to HTML
- Store in database
- Publish to Slack/Google Docs

### Option 2: Structured JSON
If your n8n workflow returns research data:

```json
{
  "request_id": "abc123",
  "status": "completed",
  "data": {
    "json": {
      "competitors": [
        {"name": "Pendo", "updates": [...], "news": [...]}
      ],
      "market_trends": [...],
      "user_feedback": [...]
    }
  }
}
```

Agent will:
- Format the data
- Use GPT to generate markdown report
- Convert to HTML
- Store and publish

## Testing

### 1. Test n8n Trigger

```bash
# From your local machine or Railway logs
curl -X POST https://your-agent.railway.app/slack/actions \
  -H "Content-Type: application/json"
```

Or click "Run Report" in Slack.

You should see in logs:
```
🔗 Triggering n8n research workflow...
✅ n8n research triggered successfully: {request_id}
```

### 2. Test n8n Response

Manually POST to the webhook endpoint:

```bash
curl -X POST https://your-agent.railway.app/n8n/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-123",
    "status": "completed",
    "data": {
      "markdown": "# Test Report\n\nThis is a test."
    }
  }'
```

You should see:
```
📥 Received research results from n8n: test-123
Processing n8n research results and generating report...
✅ Successfully generated report from n8n data
```

## Fallback Behavior

If `N8N_WEBHOOK_URL` is **not set**, the agent will:
- Fall back to **internal research** using existing logic
- Use Perplexity, Claude, and SerpAPI as before
- Log: "n8n not enabled - using internal research agent"

This ensures backward compatibility!

## Monitoring

### Key Log Messages

**Successful Flow:**
```
🔗 Triggering n8n research workflow...
✅ n8n research triggered successfully: {request_id}
📥 Received research results from n8n: {request_id}
Processing n8n research results and generating report...
✅ Successfully generated report from n8n data
📊 Report generated and stored: {report_id}
```

**Failure Cases:**
```
❌ n8n research failed: {error}
❌ Invalid research data from n8n: {validation_error}
❌ Failed to trigger n8n workflow: {error}
```

## n8n Workflow Example

Here's a minimal n8n workflow structure:

1. **Webhook Node** - Receives trigger from agent
2. **HTTP Request Nodes** - Scrape competitor sites, APIs
3. **Data Processing** - Parse, clean, structure data
4. **HTTP Request Node** - POST results back to agent
   - URL: `{{$env.AGENT_WEBHOOK_URL}}/n8n/webhook`
   - Method: POST
   - Body:
     ```json
     {
       "request_id": "{{$node.Webhook.json.timestamp}}",
       "status": "completed",
       "data": {
         "markdown": "{{$node.GenerateReport.output}}"
       }
     }
     ```

## Switching Between Branches

### Use n8n Integration:
```bash
git checkout experiment/n8n-research-integration
git push -u origin experiment/n8n-research-integration
```

Set `N8N_WEBHOOK_URL` in Railway and redeploy.

### Return to Internal Research:
```bash
git checkout claude/new-chat-feature-YtgRj
git push
```

Remove `N8N_WEBHOOK_URL` from Railway and redeploy.

## Benefits

✅ **Offload Heavy Processing** - n8n handles scraping, API calls, data mining
✅ **Flexible Workflows** - Easily modify research logic in n8n GUI
✅ **Scalable** - n8n can run on separate infrastructure
✅ **No Code Changes** - Update research process without redeploying agent
✅ **Backward Compatible** - Falls back to internal research if n8n unavailable

## Troubleshooting

### "n8n integration not enabled"
- Check `N8N_WEBHOOK_URL` is set in Railway environment variables
- Verify URL is accessible from Railway

### "Failed to trigger n8n workflow"
- Check n8n webhook is active and accessible
- Verify n8n workflow is not paused
- Check n8n logs for incoming requests

### "Invalid research data from n8n"
- Ensure n8n returns data in correct format
- Check response includes `markdown` or `json` field
- Verify `request_id` matches

### Report not generating
- Check agent logs for errors in `/n8n/webhook` endpoint
- Verify OpenAI API key is set (needed for JSON→Report conversion)
- Check file permissions on Railway for reports directory

## Support

For questions or issues with this experimental integration:
1. Check Railway logs
2. Check n8n execution logs
3. Test endpoints manually with curl
4. Verify environment variables are set correctly

## Future Enhancements

Potential improvements:
- [ ] Add webhook authentication/security
- [ ] Support async/polling for long-running research
- [ ] Add progress updates from n8n
- [ ] Cache research results
- [ ] Multi-step workflows with intermediate checkpoints
