import os
import time
from datetime import datetime
import re
from slackclient import SlackClient
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.errors import HttpError
from bot_settings import *

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = CONNECT["KEY_FILE_LOCATION"]
VIEW_ID = CONNECT["VIEW_ID"]

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    start_date = "7daysAgo"
    end_date = "today"
    words = command.split(' ')
    if 'from ' in command:
        pos = words.index('from')
        start_date = command.split()[pos+1]
    if 'to ' in command:
      pos = words.index('to')
      end_date = command.split()[pos+1]
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = ":cat2:"
    if command.startswith("kumbunwa"):
        response = ":woman-bowing:"
    if command.startswith("pageviews"):
        response = ':eye: *` Pageviews `* `{} → {}`\n{}'.format(start_date, end_date, pageviews(start_date, end_date))
    if command.startswith("top clicks"):
        response = '*Top Clicks* ({} - {})\n-------------\n{}'.format(start_date, end_date, top_clicks(start_date, end_date))
    if command.startswith("clicks on"):
        pattern = r'"([A-Za-z0-9_\./\\-]*)"'
        link_label = re.findall(r'"([^"]*)"', command)[0]
        response = '*Clicks on "{}"* ({} - {}) \n-------------\n{}'.format(link_label, start_date, end_date, clicks_on(link_label, start_date, end_date))
    elif command.split()[0] == 'help':
        response = '`pageviews from ____ to ____ (Dates are optional)` \n `top clicks from ____ to ____ (Dates are optional)` \n `clicks on "____" [link name] from ____ to ____ (Dates are optional)` \n `(Dates: today / yesterday / NdaysAgo / YYYY-MM-DD)`'

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def initialize_analyticsreporting():
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      KEY_FILE_LOCATION, SCOPES)
  analytics = build('analytics', 'v4', credentials=credentials)
  return analytics

def pageviews(start_date, end_date):
  analytics = initialize_analyticsreporting()
  response = analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          "dimensions": [{"name": "ga:segment"}],
          'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
          'metrics': [{'expression': 'ga:pageviews'}],
          "segments":[
            {"dynamicSegment":{"name": "Faculty Users","userSegment":
                {"segmentFilters":
                    [{"simpleSegment":{"orFiltersForSegment":
                        {"segmentFilterClauses": [{"dimensionFilter":
                            {"dimensionName":"ga:pagePath","operator":"PARTIAL","expressions":[SEGMENT["FACULTY"]]}
                            }]
                        }
                    }
                    }]
                }
            }
            },
            {"dynamicSegment":{"name": "Staff Users","userSegment":
                {"segmentFilters":
                    [{"simpleSegment":{"orFiltersForSegment":
                        {"segmentFilterClauses": [{"dimensionFilter":
                            {"dimensionName":"ga:pagePath","operator":"PARTIAL","expressions":[SEGMENT["STAFF"]]}
                            }]
                        }
                    }
                    }]
                }
            }
            },
            {"dynamicSegment":{"name": "Student Users","userSegment":
                {"segmentFilters":
                    [{"simpleSegment":{"orFiltersForSegment":
                        {"segmentFilterClauses": [{"dimensionFilter":
                            {"dimensionName":"ga:pagePath","operator":"PARTIAL","expressions":[SEGMENT["STUDENT"]]}
                            }]
                        }
                    }
                    }]
                }
            }
            },
            {"dynamicSegment":{"name": "Welcome Users","userSegment":
                {"segmentFilters":
                    [{"simpleSegment":{"orFiltersForSegment":
                        {"segmentFilterClauses": [{"dimensionFilter":
                            {"dimensionName":"ga:pagePath","operator":"PARTIAL","expressions":[SEGMENT["WELCOME"]]}
                            }]
                        }
                    }
                    }]
                }
            }
            }]
        }]
      }
  ).execute()
  answer_list = response['reports'][0]['data']['rows']
  answer = "```"
  for item in answer_list:
    if len(item['dimensions'][0]) < len(max(answer_list[0]['dimensions'], key=len)):
      answer += ' ' * (len(max(answer_list[0]['dimensions'], key=len)) - len(item['dimensions'][0]))
    answer += item['dimensions'][0] + ":  " + "{:,}".format(int(item['metrics'][0]['values'][0])) + "\n"
  answer += "```\n*```        TOTAL:  " + "{:,}".format(int(response['reports'][0]['data']['totals'][0]['values'][0])) + "```*"
  return answer

def top_clicks(start_date, end_date):
  analytics = initialize_analyticsreporting()
  response = analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'pageSize': 10,
          'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
          'metrics': [{'expression': 'ga:totalEvents'}],
          "dimensions": [{"name": "ga:eventAction"}, {"name":"ga:eventLabel"}],
          "orderBys": [{"fieldName": "ga:totalEvents",
                        "sortOrder": "DESCENDING"}]
        }]
      }
  ).execute()
  answer_list = response['reports'][0]['data']['rows']
  answer = ""
  for item in answer_list:
    answer += item['dimensions'][0] + " *" + item['dimensions'][1] + "* - " + "{:,}".format(int(item['metrics'][0]['values'][0])) + "\n "

  return answer

def clicks_on(link_label, start_date, end_date):
  analytics = initialize_analyticsreporting()
  response = analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
          'metrics': [{'expression': 'ga:totalEvents'}],
          "dimensionFilterClauses": [{"filters": [{
            "dimensionName": "ga:eventLabel",
            "expressions": [link_label]}],
          }],
          "dimensions": [{"name": "ga:date"}],
          "orderBys": [{
            "fieldName": "ga:date",
            "sortOrder": "DESCENDING"
          }]
        }]
      }
  ).execute()
  if response['reports'][0]['data']['totals'][0]['values'][0] != "0":
      answer_list = response['reports'][0]['data']['rows']
      answer = ""
      for item in answer_list:
          mydate = datetime.strptime(item['dimensions'][0], '%Y%m%d')
          answer += mydate.strftime("%b %-d") + " - *" + "{:,}".format(int(item['metrics'][0]['values'][0])) + "*\n "
      answer += "-------------\nTotal - *" + "{:,}".format(int(response['reports'][0]['data']['totals'][0]['values'][0])) + "*"
  else:
      answer = "no clicks found"

  return answer

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("myPugetSound Analytics Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
