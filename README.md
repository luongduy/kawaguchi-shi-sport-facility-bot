# Sports Facility Checker

An automated script that checks for available sports facility reservations and sends notifications to Slack.

## Features

- 🏃‍♂️ Checks multiple sports facilities for availability (Kawaguchi-shi)
- 🕒 Includes execution timestamp in notifications
- 📱 Sends results to Slack via webhooks
- ⏰ Runs automatically every hour via GitHub Actions
- 🖥️ Can be run locally for testing

## Setup

### 1. GitHub Secrets

For the GitHub Actions workflow to work, you need to set up a secret in your repository:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `SLACK_WEBHOOK_URL`
5. Value: Your Slack webhook URL (e.g., `https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK`)

### 2. Slack Webhook Setup

1. Go to your Slack workspace
2. Navigate to **Apps** → **Incoming Webhooks**
3. Create a new webhook for your desired channel
4. Copy the webhook URL and add it as a GitHub secret (see step 1)

### 3. GitHub Actions

The workflow is configured to run:
- **Automatically**: Every hour at minute 0
- **Manually**: You can trigger it from the Actions tab

## Local Development

### Prerequisites

```bash
pip install -r requirements.txt
playwright install chromium
```

### Running Locally

```bash
# Set your Slack webhook URL as an environment variable
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Run the script
python main.py
```

### Local Testing Without Slack

```bash
# Run without Slack notifications
python -c "
import asyncio
from main import run
asyncio.run(run(headless=False))
"
```

## Configuration

### Schedule

To change the execution schedule, edit `.github/workflows/sports-facility-checker.yml`:

```yaml
schedule:
  # Run every hour
  - cron: '0 * * * *'
  
  # Run every 30 minutes
  # - cron: '*/30 * * * *'
  
  # Run daily at 9 AM
  # - cron: '0 9 * * *'
```

### Target Day

The script currently checks for Saturday availability. To change this, modify the `day_of_week` parameter in the `check_for_taikukan` function call in `main.py`.

## Facilities Checked

- 芝スポーツセンター
- 体育武道センター  
- 鳩ヶ谷スポーツセンター
- 戸塚スポーツセンター
- 西スポーツセンター
- 安行スポーツセンター
- 東スポーツセンター

## Troubleshooting

### GitHub Actions Issues

1. **Workflow not running**: Check that the repository has Actions enabled
2. **Missing dependencies**: Ensure `requirements.txt` is up to date
3. **Slack notifications not working**: Verify the `SLACK_WEBHOOK_URL` secret is set correctly

### Local Issues

1. **Browser not opening**: Make sure Playwright browsers are installed: `playwright install chromium`
2. **Import errors**: Install dependencies: `pip install -r requirements.txt`

