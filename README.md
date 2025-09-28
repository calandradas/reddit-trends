# Reddit AI Trend Reports

[English](README.md) | [中文](README_CN.md)

Forked from  liyedanpdx/reddit-ai-trends, thanks for his contributions.

Added support for OpenAI, xAI Grok, and Google Gemini LLM. For details, please view the configuration information in the .env.example file and configure your own key.

Automatically generate trend reports from AI, Crypto, Biotech-related Reddit communities, supporting both English and Chinese languages. Stay up-to-date with the latest developments in the AI, Crypto, Biotech field through daily reports.

## Features

- **Real-time Industry Trend Monitoring**: Track emerging industry technologies, discussions, and breakthroughs as they happen
- **Mutiple LLMs Support**: Support for OpenAI, xAI Grok, and Google Gemini LLM
- **Multi-industries Analysis, Customizable**: Add support for AI, Biotech, and Cryptopip industry communities, and customize the addition of multiple communities
- **Reports Separately**: Generate reports by industry and define multiple planned tasks
- **Multi-community Analysis**: Collect data from various industry-related subreddits to provide a comprehensive view
- **Detailed Trend Analysis**: Generate in-depth reports including today's highlights, weekly trend comparisons, monthly technology evolution, and more
- **Bilingual Support**: Generate reports in both English and Chinese
- **Organized File Structure**: Store reports in year/month/day folders for easy access
- **Docker Deployment**: Easy containerized deployment
- **MongoDB Persistence**: Store all data for historical analysis

## Directory Structure

```
reports/
  ├── YYYY/           # Year directory
  │   ├── MM/         # Month directory
  │   │   ├── DD/     # Day directory
  │   │   │   ├── report_YYYYMMDD_HHMMSS_en.md  # English report
  │   │   │   └── report_YYYYMMDD_HHMMSS_zh.md  # Chinese report
  ├── latest_report_en.md  # Symlink to latest English report
  └── latest_report_zh.md  # Symlink to latest Chinese report
```

## Installation and Setup

### Prerequisites

- Docker and Docker Compose
- Reddit API credentials
- LLM API key, OpenAI | Google Gemini | xAI Grok

### Environment Variables Setup

1. Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your API keys and other configurations: choose LLM vendor and configuring the corresponding key

```
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent

#LLM Vendor
VENDOR=gemini
#VENDOR=grok
#VENDOR=openai

#gemini api key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash # You can change to gemini-2.5-flash, gemini-3, etc.

#grok api key
GROK_API_KEY=your_grok_api_key
GROK_API_BASE=https://api.grok.com/v1_
GROK_MODEL=grok-4 # You can change to grok-4, grok-5, etc.

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o # You can change to gpt-4.1, gpt-4o, gpt-5-mini, etc.

```

Reddit API credentials website: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

Google gemini API website: [https://aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys)

xAI grok API website: [https://x.ai/api](https://x.ai/api)

OpenAI API website: [https://platform.openai.com/](https://platform.openai.com/)

## Usage

### Deploy with Docker Compose

1. Build and start the containers:

```bash
docker-compose up -d
```

2. View the logs:

```bash
docker-compose logs -f app
```

### Run Manually

1. Install dependencies:

```bash
python3 -m venv reddit-trends
cd reddit-trends
source ./bin/activate
pip install -r requirements.txt
```

2. Generate a one-time report:

```bash
python report_generation.py --languages en zh --skip-mongodb --industry ai
```

3. Set up scheduled report generation:

```bash
python report_generation.py --interval 24
```

## Creating a GitHub Repository

1. Create a new repository on GitHub

2. Initialize your local repository and push:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/reddit-ai-trends.git
git push -u origin main
```

## Custom Configuration

You can modify the following configurations in the `config.py` file:

- List of subreddits to monitor
- Number of posts to fetch per subreddit
- Report generation time
- Supported languages
- LLM model parameters

## How to add a new industry community

- Edit the `REDDIT_COMMUNITIES` parameter in the `config.py` file
- Add the industry community you want to monitor at the beginning of `REDDIT_COMMUNITIES`, for example

```py
    "biotech_communities": [
        "Biotech",
        "Bioinformatics",
        "medicine",
        "biology"
    ],
```

When running the script, add the `--industry` parameter. Note that the parameter name must match the prefix of the added industry community.

```bash
python report_generation.py --languages ​​en zh --skip-mongodb --industry biotech
```

## Multi-Industries Trend Monitoring

This system is designed to keep you informed about the latest developments in the multi-indtustries field by:

- Tracking emerging technologies and breakthroughs in real-time
- Identifying trending topics across different industry communities
- Comparing current trends with historical data to spot emerging patterns
- Highlighting unique discussions from smaller communities that might be overlooked
- Providing technical deep dives into particularly interesting or important trends

The daily reports give you a comprehensive view of what's happening in the industry world, helping you stay ahead of the curve and identify important developments as they emerge.

## Troubleshooting

- **Reports not generating**: Check if your API keys are correct and look for error messages in the logs
- **MongoDB connection failing**: Ensure MongoDB service is running and the connection URI is correct
- **Symlinks not working**: On Windows systems, you may need administrator privileges to create symlinks

## License

MIT