# myps-slack-bot
Slack bot for myPugetSound analytics :zap:

## Usage
Allows access to myPugetSound analytics via Slack commands.

```
@myPS pageviews from ____ to ____ (Dates are optional)
```
```
@myPS top clicks from ____ to ____ (Dates are optional)
```
```
@myPS clicks on "____" [link name] from ____ to ____ (Dates are optional)
```

Dates use the following formats.
```
today / yesterday / NdaysAgo / YYYY-MM-DD
```

Use the `help` command for instructions.

```
@myPS help
```

## Setup
Save `bot_settings.example.py` as `bot_settings.py` and fill in values.

---
Based on this fantastic tutorial https://www.twilio.com/blog/2018/03/google-analytics-slack-bot-python.html
