import json
import logging
import os
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Tuple

import boto3
from dataclass_wizard import JSONWizard
from slack_sdk import WebClient
from slack_sdk.models import blocks as blks

from scw_serverless.app import Serverless

SCW_ACCESS_KEY = os.environ["SCW_ACCESS_KEY"]
SCW_SECRET_KEY = os.environ["SCW_SECRET_KEY"]
S3_BUCKET = os.environ["S3_BUCKET"]
SLACK_TOKEN = os.environ["SLACK_TOKEN"]
SLACK_CHANNEL = os.environ["SLACK_CHANNEL"]
SLACK_INSTANCE = os.getenv(
    "SLACK_INSTANCE", ""
)  # used to generate archive links to slack messages
REMINDER_SCHEDULE = os.getenv("REMINDER_SCHEDULE", "0 * * * *")

app = Serverless(
    "slack-bots",
    env={
        "S3_BUCKET": S3_BUCKET,
        "SLACK_CHANNEL": SLACK_CHANNEL,
    },
    secret={
        "SLACK_TOKEN": SLACK_TOKEN,
        "SCW_ACCESS_KEY": SCW_ACCESS_KEY,
        "SCW_SECRET_KEY": SCW_SECRET_KEY,
    },
)

s3 = boto3.resource(
    "s3",
    region_name="fr-par",
    use_ssl=True,
    endpoint_url="http://s3.fr-par.scw.cloud",
    aws_access_key_id=SCW_ACCESS_KEY,
    aws_secret_access_key=SCW_SECRET_KEY,
)

# Enable info logging
logging.basicConfig(level=logging.INFO)
client = WebClient(token=SLACK_TOKEN)


@dataclass
class Developer(JSONWizard):
    """Generic representation of a user from GitHub/GitLab"""

    name: str
    avatar_url: str | None

    @staticmethod
    def from_github(user: dict[str, Any]):
        """Creates from a GitHub user"""
        return Developer(name=user["login"], avatar_url=user["avatar_url"])

    @staticmethod
    def from_gitlab(user: dict[str, Any]):
        """Creates from a GitLab user"""
        return Developer(name=user["username"], avatar_url=user["avatar_url"])


@dataclass
class Review(JSONWizard):
    """Generic representation of a review from GitHub/GitLab"""

    state: str
    _slack_emojis: ClassVar[dict[str, str]] = {
        "approved": ":heavy_check_mark:",
        "dismissed": ":put_litter_in_its_place:",
        "changes_requested": ":x:",
    }

    @staticmethod
    def from_github(review: dict[str, Any]):
        """Creates from a GitHub review"""
        return Review(state=review["state"].lower())

    @staticmethod
    def from_gitlab_action(
        action: Literal["approval", "approved", "unapproval", "unapproved"]
    ):
        """Creates from a GitLab action"""
        return Review(
            state="approved" if action.startswith("approv") else "changes_requested"
        )

    def get_slack_emoji(self) -> str:
        """Gets the corresponding slack emoji"""
        return self._slack_emojis.get(self.state, "")


@dataclass
class Repository(JSONWizard):
    """Generic representation of a GitHub/GitLab repository"""

    name: str
    full_name: str

    @staticmethod
    def from_github(repository: dict[str, Any]):
        """Creates from a GitHub repository"""
        return Repository(name=repository["name"], full_name=repository["full_name"])

    @staticmethod
    def from_gitlab(repository: dict[str, Any]):
        """Creates from a GitLab project"""
        return Repository(
            name=repository["name"], full_name=repository["path_with_namespace"]
        )


# pylint: disable=too-many-instance-attributes # unecessary work to split the attributes
@dataclass
class PullRequest(JSONWizard):
    """Generic representation of a GitHub PR/Gitlab MR"""

    number: int
    repository: Repository
    title: str
    url: str
    is_draft: bool
    is_merged: bool
    owner: Developer
    reviewers: dict[str, Developer]  # key is the Developer name property
    reviews: dict[str, Review]
    target_branch: str
    mergeable: bool | None
    additions: int | None
    deletions: int | None

    @property
    def bucket_path(self) -> str:
        """Get the path to store this PR in"""
        return f"pull_requests/{self.repository.full_name}/{self.number}.json"

    # pylint: disable=line-too-long # disabled to include links to documentation
    @staticmethod
    def from_github(repository: dict[str, Any], pull_request: dict[str, Any]):
        """Creates from a GitHub PR
        See: https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request
        """
        return PullRequest(
            number=pull_request["number"],
            repository=Repository.from_github(repository),
            title=pull_request["title"],
            url=pull_request["html_url"],
            is_draft=pull_request["draft"],
            is_merged=pull_request["merged"],
            owner=Developer.from_github(pull_request["user"]),
            reviewers={
                d["login"]: Developer.from_github(d)
                for d in pull_request["requested_reviewers"]
            },
            reviews={},
            target_branch=pull_request["base"]["ref"],
            mergeable=pull_request.get("mergeable"),
            additions=pull_request.get("additions"),
            deletions=pull_request.get("deletions"),
        )

    @staticmethod
    def from_gitlab(
        project: dict[str, Any],
        pull_request: dict[str, Any],
        user: dict[str, Any],
        reviewers: list[dict[str, Any]],
    ):
        """Creates from a GitLab MR event"""
        return PullRequest(
            number=pull_request["id"],
            repository=Repository.from_gitlab(project),
            title=pull_request["title"],
            url=pull_request["url"],
            is_draft=pull_request["work_in_progress"],
            is_merged=(pull_request["action"] == "merge"),
            owner=Developer.from_gitlab(user),  # only true when action is create
            reviewers={d["username"]: Developer.from_gitlab(d) for d in reviewers},
            reviews={},
            target_branch=pull_request["target_branch"],
            mergeable=(pull_request.get("detailed_merge_status") == "mergeable"),
            additions=None,
            deletions=None,
        )

    def on_draft(self):
        """Saves a PR marked as a draft to notify when it's ready"""
        save_pr_to_bucket(self, "")

    def on_created(self):
        """Sends a notification for a newly created PR"""
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL, blocks=self._as_slack_notification()
        )
        if not response["ok"]:
            logging.warning(response["error"])
            return
        timestamp = str(response["ts"])
        save_pr_to_bucket(self, timestamp)

    def on_updated(self):
        """Performs the necessary changes when a PR is updated"""
        _timestamp, pull = load_pr_from_bucket(self.bucket_path)
        if pull.is_draft and not self.is_draft:
            self.on_created()

    def on_reviewed(self, review: Review, reviewer: Developer):
        """Updates the notification when a new review is made"""
        timestamp, pull = load_pr_from_bucket(self.bucket_path)
        self.reviews = pull.reviews.copy()
        self.reviews[reviewer.name] = review
        self.owner = pull.owner
        save_pr_to_bucket(self, timestamp)
        response = client.chat_update(
            channel=SLACK_CHANNEL, ts=timestamp, blocks=self._as_slack_notification()
        )
        if not response["ok"]:
            logging.warning(response["error"])
            return
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            thread_ts=timestamp,
            text=f"{reviewer.name} left a review: {review.state}",
        )
        if not response["ok"]:
            logging.warning(response["error"])

    def on_closed(self):
        """Sends a message in the thread when the PR is merged"""
        if self.is_merged:
            timestamp, _pull = load_pr_from_bucket(self.bucket_path)
            response = client.chat_postMessage(
                channel=SLACK_CHANNEL,
                thread_ts=timestamp,
                text="Pull request was merged! :tada:",
            )
            if not response["ok"]:
                logging.warning(response["error"])
        delete_pr_from_bucket(self.bucket_path)

    def _as_slack_notification(self) -> list[blks.Block]:
        return [
            blks.HeaderBlock(text=f"New MR on {self.repository.name}: {self.title}"),
            blks.DividerBlock(),
            blks.ContextBlock(
                elements=[
                    blks.MarkdownTextObject(text="Submitted by"),
                    blks.ImageElement(
                        image_url=self.owner.avatar_url,
                        alt_text=f"avatar of {self.owner.name}",
                    ),
                    blks.MarkdownTextObject(text=f"*{self.owner.name}*"),
                ]
            ),
            blks.SectionBlock(
                fields=[self._get_details_slack_blk(), self._get_reviews_slack_blk()],
                accessory=blks.ButtonElement(text="Review", url=self.url),
            ),
        ]

    def _get_details_slack_blk(self) -> blks.MarkdownTextObject:
        txt = "*Details*\n"
        txt += f"Target: *{self.target_branch}*\n"
        txt += "Mergeable: "
        txt += ":ok_hand:\n" if self.mergeable else ":no_good:\n"
        if self.additions:
            txt += f"Additions: *{self.additions}*\n"
        if self.deletions:
            txt += f"Deletions: *{self.deletions}*\n"
        return blks.MarkdownTextObject(text=txt)

    def _get_reviews_slack_blk(self) -> blks.MarkdownTextObject:
        txt = "*Reviews*\n"
        for name, _reviewer in self.reviewers.items():
            txt += f"{name}"
            if review := self.reviews.get(name):
                txt += ": " + review.get_slack_emoji()
            txt += "\n"
        for name, review in self.reviews.items():
            if name not in self.reviewers:
                txt += f"{name}: " + review.get_slack_emoji() + "\n"
        return blks.MarkdownTextObject(text=txt)

    def should_be_reminded(self) -> bool:
        """Defines the rules to appear in the reminder"""
        return not self.is_draft and not self.mergeable

    def get_reminder_slack_blk(self, timestamp: str) -> blks.SectionBlock:
        """Gets the message to be added to the reminder"""
        reminder = f"*{self.title}*"
        if SLACK_INSTANCE:
            msg_url = f"https://{ SLACK_INSTANCE }.slack.com/archives/{ SLACK_CHANNEL }/p{ timestamp }"
            reminder = f"*<{msg_url}|{self.title}>*"
        return blks.SectionBlock(
            text=blks.MarkdownTextObject(text=reminder, verbatim=True),
        )


def delete_pr_from_bucket(bucket_path: str):
    """Deletes a PR"""
    s3.Object(S3_BUCKET, bucket_path).delete()


def save_pr_to_bucket(pull: PullRequest, timestamp: str):
    """Saves a PR associated with a Slack timestamp"""
    s3.Object(S3_BUCKET, pull.bucket_path).put(
        Body=json.dumps({"ts": timestamp, "pull_request": pull.to_dict()})
    )


def load_pr_from_bucket(bucket_path: str) -> Tuple[str, PullRequest]:
    """Loads a PR and the Slack timestamp of its notification"""
    saved = json.loads(
        s3.Object(S3_BUCKET, bucket_path).get()["Body"].read().decode("utf-8")
    )
    return (saved["ts"], PullRequest.from_dict(saved["pull_request"]))


def _handle_github_events(body: dict[str, Any]):
    match body:
        case {
            "action": "opened" | "reopened",
            "pull_request": pull_request,
            "repository": repository,
        }:
            pull = PullRequest.from_github(repository, pull_request)
            if pull.is_draft:
                pull.on_draft()
            else:
                pull.on_created()
        case {
            "review": review,
            "sender": reviewer,
            "pull_request": pull_request,
            "repository": repository,
        }:
            pull = PullRequest.from_github(repository, pull_request)
            review = Review.from_github(review)
            reviewer = Developer.from_github(reviewer)
            pull.on_reviewed(review, reviewer)
        case {
            "action": "closed",
            "pull_request": pull_request,
            "repository": repository,
        }:
            pull = PullRequest.from_github(repository, pull_request)
            pull.on_closed()
        case _:
            logging.info("could not match body")
            return {"statusCode": 400}
    return {"statusCode": 200}


# pylint: disable=broad-except,line-too-long # disabled for convenience
@app.func()
def handle_github(event, _content):
    """Handles GitHub webhook request
    See: https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#pull_request
    """
    response = {"statusCode": 200}
    try:
        response = _handle_github_events(json.loads(event[0]["body"]))
    except Exception as exception:
        logging.error(exception)
        return {"statusCode": 500}
    return response


def _handle_gitlab_events(body: dict[str, Any]):
    match body:
        case {
            "event_type": "merge_request",
            "user": user,
            "project": project,
            "object_attributes": {"action": "open" | "reopen" | "update"},
        }:
            pull_request = body["object_attributes"]
            reviewers = body.get("reviewers", [])
            pull = PullRequest.from_gitlab(project, pull_request, user, reviewers)
            if pull_request["action"] == "update":
                pull.on_updated()
            elif pull.is_draft:
                pull.on_draft()
            else:
                pull.on_created()
        case {
            "event_type": "merge_request",
            "user": user,
            "project": project,
            "object_attributes": {
                "action": "approval" | "approved" | "unapproval" | "unapproved"
            },
        }:
            pull_request = body["object_attributes"]
            reviewers = body.get("reviewers", [])
            pull = PullRequest.from_gitlab(project, pull_request, user, reviewers)
            pull.on_reviewed(
                Review.from_gitlab_action(pull_request["action"]), pull.owner
            )
        case {
            "event_type": "merge_request",
            "user": user,
            "project": project,
            "object_attributes": {"action": "merge" | "close"},
        }:
            pull_request = body["object_attributes"]
            pull = PullRequest.from_gitlab(project, pull_request, user, [])
            pull.on_closed()
        case _:
            logging.info("could not match body")
            return {"statusCode": 400}
    return {"statusCode": 200}


@app.func(min_scale=1, memory_limit=1024)
def handle_gitlab(event, _content):
    """Handles GitLab webhook request
    See: https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html#merge-request-events
    """
    response = {"statusCode": 200}
    try:
        response = _handle_gitlab_events(json.loads(event[0]["body"]))
    except Exception as exception:
        logging.error(exception)
        return {"statusCode": 500}
    return response


@app.schedule(REMINDER_SCHEDULE)
def pull_request_reminder(_event, _content):
    """Daily reminder to review opened pull-requests"""
    bucket = s3.Bucket(S3_BUCKET)
    opened_prs = (
        bucket.objects.all()
    )  # not worth using list_objects_v2 since there shouldn't be a lot of active MRs
    if len(opened_prs) == 0:
        logging.info("No PRs were found")
        return {"statusCode": 200}
    blocks = [blks.HeaderBlock(text="PRs awaiting for review: "), blks.DividerBlock()]
    try:
        for opened_pr in opened_prs:
            timestamp, pull = load_pr_from_bucket(opened_pr.key)
            if pull.should_be_reminded:
                logging.info(
                    "PR %s on %s is waiting for review",
                    pull.title,
                    pull.repository.full_name,
                )
                blocks.append(pull.get_reminder_slack_blk(timestamp))
            else:
                logging.info(
                    "PR %s on %s was not included in the reminder",
                    pull.title,
                    pull.repository.full_name,
                )
        response = client.chat_postMessage(channel=SLACK_CHANNEL, blocks=blocks)
        if not response["ok"]:
            logging.error(response["error"])
            return {"statusCode": 500}
        return {"statusCode": 200}
    except Exception as exception:
        logging.error(exception)
        return {"statusCode": 500}
