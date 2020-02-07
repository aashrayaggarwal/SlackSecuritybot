# SlackGuard

It is widely believed that humans are the weakest link in security. SlackGuard helps in real-time detection of phishing links, malicious links, links containing invalid SSL/TLS certificates, http links, and offensive words. In case of a match, it can delete the message OR warn the user that a malicious link has been posted in a channel. It then sends an Alert to an administrator via a private slack channel. These messages are stored in database.

## Getting Started

The instructions below will enable you to run the project.

### Prerequisites

#### Configuring a Slack Application

* Create a Slack application in your workspace: [Slack Applications](https://api.slack.com/apps)
* Your slack applications can be found in [Slack Applications](https://api.slack.com/apps). Open this link to obtain necessary information about your applicaion.
* Install the Slack application to your workspace
* Create a private admin channel. SlackGuard will send alerts to this channel. Add Administrators to this channel.
* Authorize the Slack application with proper permissions to allow SlackGuard to read/write messages to Slack Channel
* Copy the Slack User token from 'OAuth and Permissions'. SlackGuard will use this token for identification and authentication.
  * You can use Slack Bot token, if you do not want messages to be deleted. But Bot token will not allow SlackGuard to delete messages that are not sent by bot
* Copy the Signing Secret. Slack signs the requests it sends using this secret.
* Suscribe to the events that you want Slack to send to SlackGuard from 'Event Subscriptions' page. 'message.channels' and 'message.groups' events are essential for functioning of SlackGuard
* In the 'Event Subscriptions' page, enter a publicly accessible endpoint that Slack can send events to.
  * In case you are behind a NAT, you can use [ngrok](https://ngrok.com/) to create a tunnel, so that events from Slack pass through this tunnel to your machine


### Installing


* Clone the project using `git clone https://github.com/aashrayaggarwal/SlackSecuritybot.git`
* Install `postgres` database server
  * Create a database in your postgres server. Events from slack will be stored in tables in this database.
* Install required python libraries

```
pip install slackeventsapi
pip install slackclient
pip install flask
pip install psycopg2
```

### Configuration

#### File `config_details.json`

Enter the values for

* Slack Endpoint in `"SLACK_ENDPOINT"`
* Slack Admin token in `"SLACK_ADMIN_TOKEN"`
* Slack Signing Secret in `"SLACK_SIGNING_SECRET"`
* Slack Admin channel in `"ADMIN_CHANNEL_NAME"`
* Slack log file in `"LOG_FILE_PATH"`

#### File `database_details.json`

Enter the values for

* Host in `"host"`
* Port in `"port"`
* Database in `"database"`
* Table name in `"table_name"`

#### File `policy_details.json`

This file acts as a policy document

* For each detection filter (such as `offensve_words`), `true` or `false` values have been defined for `to_Delete` and `to_Warn`
* If `to_Delete` in any detection filter is `true`, the message is deleted if it is flagged by any detection filter
* If `to_Warn` in any detection filter is `true` `AND` `to_Delete` is `false`, a warning message is posted in channel, and the message is not deleted.
* If `to_Warn` `AND` `to_Delete` both are `true`, the message is deleted directly. Sending a warning message in this case leaks sensitive information in the Slack channel.
* You can change these default policy settings.

#### Creating your own filter in `detector_modules`

You can create your own filters in the following manner

* Create a python file in `detector_modules` folder.
* This python file should contain a function which inspects the message, and returns `True` if it flagged the message or `False`, if it did not flag the message
* Import the created function in the format specified in `detector_modules/__init__.py` file
* If your function requires reading a file for comparison, place that file in `known_databases` folder
* Add the filter in the file `policy_details.json` in the format
  ``` 
  "your_filter_name"`: {"to_Delete": false, "to_Warn": true, "database_path": "your_filter_function_reference_file", "detector_func": "your_filter_function_name"}
  ```
* If your filter function does not use a reference file, `"database_path"` should be `""`

#### Other files/folders

* File `my_app.py`: Main application file
* File `SlackbotWeb.py`: Contains Slack specific functions for sending messages, deleting messages, getting uesr information, getting channel information, etc.
* File `detectors.py`: Calls all detection filters specified in `policy_details.json`
* File `read_files.py`: Reads json files, Creates a dictionary by reading, reference files for filter functions (files specified in `"database_path"` key of `policy_details.json` file)
* File `database_operator.py`: Contain Postgres database functions for opening and closing database connections, creating initial table, and inserting events
* Folder  `detector_modules`: Contains detection filters used by SlackGuard
* Folder `known_databases`: Contains reference files for filters created in `detector_modules` folder


## Deployment

Natively, the project runs using Flask development server. To use it in production:

* Get a server with public IP address and a domain name.
* Get a SSL certificate for your domain name
* Use a production web server such as `nginx` and configure it to redirect slack events to your endpoint
* Use a Web Server Gateway Interface such as `gunicorn` to call your Application
* Use a data visualization program such as `Tableau` to create dashboards from data being stored in postgres database

