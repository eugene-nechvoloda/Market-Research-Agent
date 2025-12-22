# DAP Market Research Agent

An intelligent agent that conducts comprehensive weekly market research on the Digital Adoption Platform (DAP) competitive landscape, industry trends, and user sentiment.

## Overview

This automated agent performs weekly research every Monday at 8:00 AM CET, analyzing:
- **Broad Market Research**: DAP market trends, news, acquisitions, investments
- **Competitor Analysis**: Product updates, press releases, announcements from 5 key competitors (Pendo, WalkMe, WhatFix, Apty, Appcues)
- **User Feedback**: Real user reviews from G2, Gartner, social media (LinkedIn, Reddit)

The agent uses:
- **Perplexity API & SerpAPI** for comprehensive web research
- **Claude Sonnet 4.5** for deep data analysis
- **GPT-5** for report generation
- **Slack** for automated notifications

## Features

- Automated weekly execution on schedule
- Multi-source data collection (APIs, web scraping, review platforms)
- Intelligent time-aware filtering (7-day/30-day windows)
- Deep analysis with Claude Sonnet 4.5
- Professional report generation with GPT-5
- Multiple output formats (Markdown, HTML, Google Docs)
- Slack notifications with report summaries
- Comprehensive logging and error handling

## Project Structure

```
Market-Research-Agent/
├── config/
│   └── config.yaml              # Configuration for competitors, keywords, scheduling
├── src/
│   ├── main.py                  # Main orchestrator
│   ├── api_clients/             # API client implementations
│   │   ├── perplexity_client.py
│   │   ├── serpapi_client.py
│   │   ├── claude_client.py
│   │   ├── openai_client.py
│   │   └── slack_client.py
│   ├── research_modules/        # Research modules
│   │   ├── broad_research.py
│   │   ├── competitor_analysis.py
│   │   └── feedback_search.py
│   ├── analysis/                # Data analysis with Claude
│   │   └── analyzer.py
│   ├── report_generation/       # Report generation with GPT-5
│   │   └── report_generator.py
│   └── scheduler/               # Scheduling logic
│       └── scheduler.py
├── reports/                     # Generated reports (created automatically)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Market-Research-Agent
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
PERPLEXITY_API_KEY=your_perplexity_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_CHANNEL_ID=your_slack_channel_id_here
```

### 5. Configure competitors and settings

Edit `config/config.yaml` to customize:
- Competitor URLs
- Search keywords
- Schedule settings
- Output preferences

## Usage

### Run Once (Immediate Execution)

```bash
python -m src.main --mode once
```

This runs the research immediately and generates a report.

### Run on Schedule (Weekly on Monday 8:00 AM CET)

```bash
python -m src.main --mode schedule
```

This starts the scheduler and waits for the configured time (Monday 8:00 AM CET).

### Run Daily (Testing Mode)

```bash
python -m src.main --mode daily
```

This schedules daily execution at the configured time for testing purposes.

### Custom Configuration

```bash
python -m src.main --mode once --config path/to/custom/config.yaml
```

### Using Run Scripts

Linux/Mac:
```bash
chmod +x run.sh
./run.sh once      # Run once
./run.sh schedule  # Run on schedule
./run.sh daily     # Run daily
```

Windows:
```cmd
run.bat once      # Run once
run.bat schedule  # Run on schedule
run.bat daily     # Run daily
```

## API Keys Required

### 1. Perplexity API
- Sign up at https://www.perplexity.ai/
- Get API key from dashboard
- Used for: Comprehensive web research with citations

### 2. SerpAPI
- Sign up at https://serpapi.com/
- Get API key from dashboard
- Used for: Google search results, news search

### 3. Anthropic Claude API
- Sign up at https://console.anthropic.com/
- Get API key
- Used for: Deep data analysis (Claude Sonnet 4.5)

### 4. OpenAI API
- Sign up at https://platform.openai.com/
- Get API key
- Used for: Report generation (GPT-5/GPT-4)

### 5. Slack App
- Create Slack app at https://api.slack.com/apps
- Add Bot Token Scopes: `chat:write`, `files:write`
- Install app to workspace
- Get Bot User OAuth Token
- Get Channel ID where reports should be posted

## Output

The agent generates:

1. **Markdown Report** (`reports/DAP_Market_Report_YYYY-MM-DD_HH-MM.md`)
   - Structured report with all sections
   - Inline citations
   - Time-filtered content

2. **HTML Report** (`reports/DAP_Market_Report_YYYY-MM-DD_HH-MM.html`)
   - Styled web version
   - Easy to share and view in browser

3. **Slack Notification**
   - Executive summary
   - Link to full report
   - Uploaded HTML file

4. **Log File** (`market_research_agent.log`)
   - Detailed execution logs
   - Error tracking
   - Performance metrics

## Report Structure

The generated report includes:

- **Executive Summary**: 3-4 key strategic insights
- **Recent Market News**: DAP industry news (7-day window)
- **Competitors Spotlights**: Detailed analysis per competitor
  - Strategic Moves
  - Product Updates
  - Partnerships & Integrations
  - Case Studies
  - User Feedback
- **Overall Market Data**: Market size, growth rates, trends
- **Industry Reports & Analysis**: Analyst reports, forecasts
- **Strategic Insights**: Opportunities, threats, recommendations
- **Emerging Markets & Niches**: New product categories, trends

## Temporal Intelligence

The agent uses intelligent time filtering:

- **General News**: 7-day window (current week)
- **Product Updates**: 30-day lookback
- **Press Releases**: Current calendar month
- **User Reviews**: 30-day period

This ensures only relevant, recent information is included.

## Rules & Guardrails

The agent follows strict rules to ensure report quality:

1. **NO HALLUCINATION**: Only verified data from sources
2. **NO HISTORICAL BACKFILLING**: No data outside timeframe
3. **MANDATORY INLINE CITATIONS**: Every claim has a source link
4. **EXTREME BREVITY**: Short, focused paragraphs
5. **STRICT PLACEHOLDERS**: "*No new updates this week.*" when no data exists

## Scheduling with Cron (Production)

For production deployment, you can use cron (Linux/Mac):

```bash
# Edit crontab
crontab -e

# Add line for Monday 8:00 AM CET (7:00 AM UTC in winter, 6:00 AM UTC in summer)
0 7 * * 1 cd /path/to/Market-Research-Agent && /path/to/venv/bin/python -m src.main --mode once >> /path/to/logs/cron.log 2>&1
```

Or use systemd timer (Linux):

1. Create service file: `/etc/systemd/system/market-research.service`
2. Create timer file: `/etc/systemd/system/market-research.timer`
3. Enable timer: `systemctl enable market-research.timer`

## Development

### Running Tests

```bash
# TODO: Add tests
pytest tests/
```

### Adding New Competitors

Edit `config/config.yaml` and add new competitor with URLs:

```yaml
competitors:
  - name: "NewCompetitor"
    urls:
      main: "https://www.newcompetitor.com"
      blog: "https://www.newcompetitor.com/blog"
      newsroom: "https://www.newcompetitor.com/news"
      releases: "https://www.newcompetitor.com/releases"
      g2: "https://www.g2.com/products/newcompetitor"
```

### Customizing Search Keywords

Edit `config/config.yaml` under `search_keywords` section.

## Troubleshooting

### "API key not provided" error
- Ensure `.env` file exists with all required API keys
- Check that `.env` is in the project root directory

### Reports not being generated
- Check `market_research_agent.log` for errors
- Verify API keys are valid and have sufficient credits
- Ensure `reports/` directory is writable

### Slack notifications failing
- Verify Slack bot token and channel ID
- Ensure bot has been added to the target channel
- Check bot has `chat:write` and `files:write` permissions

### Web scraping errors
- Some websites may block scraping
- Consider adding delays or using proxy services
- APIs provide more reliable data than scraping

## License

MIT License

## Support

For issues and questions, please contact the product manager at Userlane.

## Roadmap

- [ ] Add unit tests
- [ ] Implement Google Docs export
- [ ] Add retry logic for API failures
- [ ] Implement caching for web requests
- [ ] Add dashboard for viewing historical reports
- [ ] Integrate with additional data sources
- [ ] Add sentiment analysis for user feedback
- [ ] Implement trend detection algorithms