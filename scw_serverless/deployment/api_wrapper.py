import logging
from typing import Optional

from scaleway import ScalewayException, WaitForOptions
from scaleway.function import v1beta1 as sdk

from scw_serverless.app import Serverless
from scw_serverless.config import Function
from scw_serverless.config.triggers import CronTrigger

DEPLOY_TIMEOUT = 600


class FunctionAPIWrapper:
    """Wraps the Scaleway Python SDK with the Framework types."""

    def __init__(self, api: sdk.FunctionV1Beta1API) -> None:
        self.api = api

    def find_deployed_namespace(
        self, app_instance: Serverless
    ) -> Optional[sdk.Namespace]:
        """Find a deployed namespace given its name."""
        candidates = self.api.list_namespaces_all(name=app_instance.service_name)
        return candidates[0] if candidates else None

    def find_deployed_function(
        self, namespace_id: str, function: Function
    ) -> Optional[sdk.Function]:
        """Find a deployed function given its name."""
        candidates = self.api.list_functions_all(
            namespace_id=namespace_id, name=function.name
        )
        return candidates[0] if candidates else None

    def find_deployed_cron_trigger(
        self, function_id: str, trigger: CronTrigger
    ) -> Optional[sdk.Cron]:
        """Find a deployed trigger given its name."""
        deployed_trigger = None
        for cron in self.api.list_crons_all(function_id=function_id):
            if cron.name == trigger.name:
                deployed_trigger = cron
        return deployed_trigger

    def _get_secrets_from_dict(
        self, secrets: Optional[dict[str, str]]
    ) -> Optional[list[sdk.Secret]]:
        if not secrets:
            return None
        return [sdk.Secret(key=key, value=val) for key, val in secrets.items()]

    def create_namespace(self, app_instance: Serverless) -> sdk.Namespace:
        """Create a namespace."""
        namespace = self.api.create_namespace(
            name=app_instance.service_name,
            environment_variables=app_instance.env,
            secret_environment_variables=self._get_secrets_from_dict(
                app_instance.secret
            ),
        )
        return self.api.wait_for_namespace(namespace_id=namespace.id)

    def update_namespace(
        self, namespace_id: str, app_instance: Serverless
    ) -> sdk.Namespace:
        """Update a namespace."""
        namespace = self.api.update_namespace(
            namespace_id=namespace_id,
            environment_variables=app_instance.env,
            secret_environment_variables=self._get_secrets_from_dict(
                app_instance.secret
            ),
        )
        return self.api.wait_for_namespace(namespace_id=namespace.id)

    def create_function(
        self, namespace_id: str, function: Function, runtime: sdk.FunctionRuntime
    ) -> sdk.Function:
        """Create a function."""
        return self.api.create_function(
            namespace_id=namespace_id,
            runtime=runtime,
            privacy=sdk.FunctionPrivacy(function.privacy),
            http_option=sdk.FunctionHttpOption(function.http_option),
            name=function.name,
            environment_variables=function.environment_variables,
            min_scale=function.min_scale,
            max_scale=function.max_scale,
            memory_limit=function.memory_limit,
            timeout=function.timeout,
            handler=function.handler_path,
            description=function.description,
            secret_environment_variables=self._get_secrets_from_dict(
                function.secret_environment_variables
            ),
        )

    def update_function(
        self, function_id: str, function: Function, runtime: sdk.FunctionRuntime
    ) -> sdk.Function:
        """Update a function."""
        return self.api.update_function(
            function_id=function_id,
            runtime=runtime,
            privacy=sdk.FunctionPrivacy(function.privacy),
            http_option=sdk.FunctionHttpOption(function.http_option),
            environment_variables=function.environment_variables,
            min_scale=function.min_scale,
            max_scale=function.max_scale,
            memory_limit=function.memory_limit,
            timeout=function.timeout,
            handler=function.handler_path,
            description=function.description,
            secret_environment_variables=self._get_secrets_from_dict(
                function.secret_environment_variables
            ),
        )

    def get_upload_url(self, function_id: str, zip_size: int) -> str:
        """Get the upload url for a function."""
        return self.api.get_function_upload_url(
            function_id=function_id, content_length=zip_size
        ).url

    def deploy_function(self, function_id: str) -> sdk.Function:
        """Deploy a function."""
        self.api.deploy_function(function_id=function_id)
        return self.api.wait_for_function(
            function_id=function_id,
            options=WaitForOptions(timeout=DEPLOY_TIMEOUT),
        )

    def create_cron_trigger(self, function_id: str, trigger: CronTrigger) -> sdk.Cron:
        """Create a Cron."""
        cron = self.api.create_cron(
            function_id=function_id,
            schedule=trigger.schedule,
            name=trigger.name,
            args=trigger.args,
        )
        return self.api.wait_for_cron(cron_id=cron.id)

    def update_cron_trigger(self, function_id: str, trigger: CronTrigger) -> sdk.Cron:
        """Update a Cron."""
        cron = self.api.create_cron(
            function_id=function_id,
            schedule=trigger.schedule,
            name=trigger.name,
            args=trigger.args,
        )
        return self.api.wait_for_cron(cron_id=cron.id)

    def delete_all_functions_from_ns_except(
        self, namespace_id: str, function_ids: list[str]
    ) -> None:
        """Delete all functions from a namespace expect function_ids."""
        for function in self.api.list_functions_all(namespace_id=namespace_id):
            if function.id in function_ids:
                continue

            logging.info("Deleting function %s...", function.name)

            try:
                self.api.delete_function(function_id=function.id)
            except ScalewayException as e:
                if e.status_code == 404:
                    return
                raise e

    def delete_all_crons_from_ns_except(
        self, namespace_id: str, cron_ids: list[str]
    ) -> None:
        """Delete all crons from a namespace expect cron_ids."""
        for function in self.api.list_functions_all(namespace_id=namespace_id):
            to_be_removed = [
                cron
                for cron in self.api.list_crons_all(function_id=function.id)
                if cron.id not in cron_ids
            ]
            for cron in to_be_removed:
                logging.info("Deleting cron %s...", cron.name)
                try:
                    self.api.delete_cron(cron_id=cron.id)
                except ScalewayException as e:
                    if e.status_code == 404:
                        return
                    raise e
