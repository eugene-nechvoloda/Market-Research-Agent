# Railway Deployment Guide

This guide explains how to deploy the DAP Market Research Agent to Railway.

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **API Keys**: All required API keys (Perplexity, SerpAPI, Claude, OpenAI)
4. **Slack App**: Configured Slack app (see Slack Setup section)

## Deployment Steps

### 1. Create Railway Project

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `Market-Research-Agent` repository
5. Railway will automatically detect the configuration from `railway.json`

### 2. Configure Environment Variables

In the Railway dashboard, add these environment variables:

```
PERPLEXITY_API_KEY=your_perplexity_api_key
SERPAPI_API_KEY=your_serpapi_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_CHANNEL_ID=C1234567890
```

**Note**: Railway automatically sets the `PORT` environment variable, so you don't need to add it.

### 3. Deploy

1. Railway will automatically build and deploy your app
2. Wait for the deployment to complete (2-5 minutes)
3. Once deployed, Railway will provide a public URL (e.g., `https://your-app.up.railway.app`)

### 4. Configure Slack App URL

1. Go to https://api.slack.com/apps
2. Select your app
3. Go to "Event Subscriptions"
4. Set Request URL to: `https://your-app.up.railway.app/slack/events`
5. Go to "Interactivity & Shortcuts"
6. Set Request URL to: `https://your-app.up.railway.app/slack/events`
7. Go to "Slash Commands"
8. Update `/research` command URL to: `https://your-app.up.railway.app/slack/events`

### 5. Verify Deployment

1. Check health endpoint: `https://your-app.up.railway.app/health`
2. Test Slack command: `/research help` in Slack
3. Check Railway logs for any errors

## Slack App Setup

### Creating a Slack App

1. **Go to Slack API**: https://api.slack.com/apps
2. **Create New App**: Click "Create New App" → "From scratch"
3. **Name & Workspace**:
   - App Name: "DAP Market Research Agent"
   - Workspace: Select your workspace

### Configure Bot Permissions

1. Go to **OAuth & Permissions**
2. Add these **Bot Token Scopes**:
   - `chat:write` - Post messages
   - `files:write` - Upload files
   - `commands` - Add slash commands
   - `app_mentions:read` - Read mentions
   - `channels:read` - View channels

3. **Install App** to workspace
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Enable Event Subscriptions

1. Go to **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Set **Request URL**: `https://your-app.up.railway.app/slack/events`
   - **Important**: Deploy to Railway first, then set this URL
4. Subscribe to **bot events**:
   - `app_home_opened`
   - `app_mention`
   - `message.channels`

### Create Slash Command

1. Go to **Slash Commands**
2. Click **Create New Command**
3. Configure:
   - Command: `/research`
   - Request URL: `https://your-app.up.railway.app/slack/events`
   - Short Description: "Control DAP market research agent"
   - Usage Hint: `[run|status|schedule|latest|help]`

### Enable Interactivity

1. Go to **Interactivity & Shortcuts**
2. Toggle **Interactivity** to ON
3. Set **Request URL**: `https://your-app.up.railway.app/slack/events`

### Enable Home Tab

1. Go to **App Home**
2. Toggle **Home Tab** to ON
3. Toggle **Messages Tab** to ON (optional)

### Get Credentials

1. **Bot Token**: OAuth & Permissions → Bot User OAuth Token (`xoxb-...`)
2. **Signing Secret**: Basic Information → App Credentials → Signing Secret
3. **Channel ID**:
   - Right-click channel in Slack → View channel details
   - Scroll down to find Channel ID

## Slack App Commands

Once deployed, users can interact with the agent using:

### `/research` Commands

- `/research help` - Show all available commands
- `/research run` - Start research immediately
- `/research status` - Check agent status
- `/research schedule` - View schedule information
- `/research latest` - Get the latest report

### Home Tab

Users can click on the app in Slack to view:
- Quick stats (reports generated, last run, schedule)
- Quick action buttons
- Status information

## Architecture on Railway

```
Railway Service (Web)
├── Flask App (Port from $PORT env var)
│   ├── /slack/events → Handles all Slack interactions
│   ├── /health → Health check endpoint
│   └── / → Info endpoint
│
├── Slack Bolt App
│   ├── Slash commands handler
│   ├── Event handlers
│   ├── Action handlers
│   └── Home tab renderer
│
└── Market Research Agent
    ├── Research modules
    ├── Analysis (Claude)
    ├── Report generation (GPT-5)
    └── Slack notifications
```

## Scheduled Research

The agent automatically runs research every Monday at 8:00 AM CET. This is handled by:

1. Railway's always-on service keeps the app running
2. The scheduler module manages the weekly execution
3. Results are automatically posted to the configured Slack channel

**Alternative: Railway Cron Jobs**

You can also set up a separate Railway Cron service:

1. Create a new service in the same project
2. Set start command: `python -m src.main --mode once`
3. Configure cron schedule: `0 7 * * 1` (Monday 7:00 AM UTC = 8:00 AM CET)

## Monitoring

### Railway Dashboard

- **Logs**: View real-time logs in Railway dashboard
- **Metrics**: CPU, Memory, Network usage
- **Deployments**: History of all deployments

### Health Check

Monitor app health at: `https://your-app.up.railway.app/health`

### Slack Notifications

All research results are automatically posted to Slack with:
- Executive summary
- Link to full report
- HTML report file attachment

## Troubleshooting

### Slack events not working

**Problem**: Slack commands not responding

**Solutions**:
1. Verify Request URLs in Slack app settings match Railway URL
2. Check Railway logs for errors
3. Ensure `SLACK_SIGNING_SECRET` is correct
4. Test `/health` endpoint to ensure app is running

### Research failing

**Problem**: `/research run` command fails

**Solutions**:
1. Check Railway logs for API errors
2. Verify all API keys are set correctly
3. Check API key quotas/credits
4. Ensure `config/config.yaml` exists in deployment

### Reports directory missing

**Problem**: No reports being saved

**Solutions**:
1. Railway has ephemeral file systems - files are lost on restart
2. Use persistent volume for reports (Railway Settings → Volumes)
3. Or upload reports to S3/Cloud Storage
4. Slack file uploads preserve reports in Slack channels

### Deployment fails

**Problem**: Railway build/deployment fails

**Solutions**:
1. Check `requirements.txt` is valid
2. Verify `runtime.txt` Python version is supported
3. Check Railway build logs for specific errors
4. Ensure all environment variables are set

## Persistent Storage (Optional)

To persist reports across deployments:

### Option 1: Railway Volume

1. In Railway dashboard → Service Settings
2. Add a Volume
3. Mount path: `/app/reports`
4. This ensures reports survive redeploys

### Option 2: Cloud Storage

Modify the report generator to upload to:
- AWS S3
- Google Cloud Storage
- Cloudflare R2

### Option 3: Rely on Slack

Since reports are uploaded to Slack, you can retrieve them from Slack history.

## Costs

### Railway Pricing

- **Hobby Plan**: $5/month
  - 500 hours of usage
  - Good for always-on services
  - Includes all features

- **Pro Plan**: $20/month
  - Unlimited usage
  - Better for production

### API Costs

Estimate per weekly run:
- **Perplexity**: ~$0.50-$2.00 per run
- **SerpAPI**: ~$0.10-$0.50 per run
- **Claude Sonnet 4.5**: ~$1.00-$3.00 per run
- **OpenAI GPT-5**: ~$2.00-$5.00 per run (estimate)

**Total**: ~$4-$11 per weekly run = ~$16-$44/month

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `PERPLEXITY_API_KEY` | Yes | Perplexity API key | `pplx-...` |
| `SERPAPI_API_KEY` | Yes | SerpAPI key | `abc123...` |
| `ANTHROPIC_API_KEY` | Yes | Claude API key | `sk-ant-...` |
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-...` |
| `SLACK_BOT_TOKEN` | Yes | Slack bot token | `xoxb-...` |
| `SLACK_SIGNING_SECRET` | Yes | Slack signing secret | `abc123...` |
| `SLACK_CHANNEL_ID` | Yes | Channel for notifications | `C1234567890` |
| `PORT` | Auto | Railway sets this | `3000` |

## Security Best Practices

1. **Never commit** `.env` file to Git
2. **Use Railway's** secret management for API keys
3. **Rotate** API keys periodically
4. **Limit** Slack bot permissions to minimum required
5. **Monitor** Railway logs for suspicious activity
6. **Set up** alerts for failed deployments

## Support

For issues:
- Check Railway logs first
- Review Slack app event logs
- Check individual API service status pages
- Contact support for specific services

## Next Steps

After successful deployment:
1. ✅ Test all Slack commands
2. ✅ Run a manual research: `/research run`
3. ✅ Verify scheduled execution works
4. ✅ Monitor first few runs for issues
5. ✅ Set up alerts for failures
6. ✅ Document any custom configurations
