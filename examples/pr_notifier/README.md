# Pull Requests Notifier

A simple Slack bot to notify on new pull requests using `scw_serverless` for deployment. Compatible with Github and Gitlab.

The bot will send a notification whenever a new pull request is ready to be reviewed. This notification will get updated as contributors leave their reviews.

In addition, it will send a daily recap with all merge requests which require attention from reviewers.

## Deploying

Deployment can be done with `scw_serverless`:

```console
pip install scw_serverless
srvless deploy notifier.py
```

Once you have deployed the functions, they can be setup as webhooks on your repositories:

### Gitlab

> In Settings -> Webhooks

1. Add the url to the `handle_gitlab` function in the *URL* field.
2. Select under *Trigger*:
   * Comments
   * Merge request events

### GitHub

> In Project Settings -> Webhooks -> Add Webhook

1. Add the url to the `handle_github` function in the *Payload URL* field.
2. Select the *Content type*: `application/json`.
3. Choose *Let me select individual events* and select the triggers:
   * Pull requests
   * Pull request reviews

## Configuration

Here's all the environments variables that needs to be passed when deploying:

| Variable | Description  | Required |
| :---:   | :---: | :---: |
| `SCW_ACCESS_KEY` | Access key to use for S3 operations |  :heavy_check_mark: |
| `SCW_SECRET_KEY` | Secret key to use for S3 operations |  :heavy_check_mark: |
| `S3_BUCKET` | Name of the bucket to store opened PRs into. |  :heavy_check_mark: |
| `SLACK_TOKEN` | Slack token. See below for details on scope. |  :heavy_check_mark: |
| `SLACK_CHANNEL` | Channel ID of the Slack channel to send messages to |  :heavy_check_mark: |
| `SLACK_INSTANCE` | Name of your Slack workspace to link previous messages in the recap |   |
| `REMINDER_SCHEDULE` | CRON schedule to trigger the reminder |   |

### Creating the Slack application

To generate your Slack token, we recommend to create a dedicated Slack application:

1. Go to <https://api.slack.com/apps?new_app=1>
2. In OAuth & Permissions, give it the following *Scopes*:
   * chat:write
3. Install the app in your slack workspace and invite it in a dedicated channel!
