from typing import Any, Optional

import requests

API_BASE = "https://api.scaleway.com/functions/v1beta1"
TIMEOUT = 3


class Api:
    """Wrapper around Scaleway's API."""

    def __init__(self, region: str, secret_key: str):
        self.secret_key = secret_key
        self.region = region
        self.headers = {"X-Auth-Token": self.secret_key}
        self.base_url = f"{API_BASE}/regions/{self.region}"

    def list_namespaces(self, project_id: str) -> list[dict[str, Any]]:
        """List the functions namespaces in the specified project."""
        resp = requests.get(
            f"{self.base_url}/namespaces?project_id={project_id}",
            headers=self.headers,
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return []

        return resp.json().get("namespaces", [])

    def get_namespace(self, namespace_id: str) -> Optional[dict[str, Any]]:
        """Get details about the function namespace."""
        resp = requests.get(
            f"{self.base_url}/namespaces/{namespace_id}",
            headers=self.headers,
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    # pylint: disable=too-many-arguments
    def create_namespace(
        self,
        name: str,
        project_id: str,
        env: dict = None,
        description: str = None,
        secrets: dict = None,
    ) -> Optional[dict[str, Any]]:
        """Create a function namespace."""
        resp = requests.post(
            f"{self.base_url}/namespaces",
            headers=self.headers,
            json={
                "name": name,
                "environment_variables": env,
                "project_id": project_id,
                "description": description,
                "secret_environment_variables": self._to_secret_list(secrets),
            },
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def update_namespace(
        self,
        namespace_id: str,
        env: dict = None,
        description: str = None,
        secrets: dict = None,
    ) -> Optional[dict[str, Any]]:
        """Update the function namespace."""
        resp = requests.patch(
            f"{self.base_url}/namespaces/{namespace_id}",
            headers=self.headers,
            json={
                "environment_variables": env,
                "description": description,
                "secret_environment_variables": self._to_secret_list(secrets),
            },
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def get_namespace_id(self, project_id: str, namespace_name: str) -> str:
        """Get the first namespace which name's matches namespace_name in project_id"""
        for namespace in self.list_namespaces(project_id):
            if namespace["name"] == namespace_name:
                return namespace["id"]
        raise RuntimeError(f"could not find namespace {namespace_name}")

    def _to_secret_list(self, secrets: dict) -> list:
        secrets_list = []

        if secrets is not None:
            for k, value in secrets.items():
                secrets_list.append({"key": k, "value": value})

        return secrets_list

    # pylint: disable=too-many-arguments
    def create_function(
        self,
        name: str,
        namespace_id: str,
        runtime: str,
        handler: str,
        privacy: str = "unknown_privacy",
        env: dict = None,
        min_scale: int = None,
        max_scale: int = None,
        memory_limit: int = None,
        timeout: str = None,
        description: str = None,
        secrets: dict = None,
    ) -> Optional[dict[str, Any]]:
        """Create a function."""

        resp = requests.post(
            f"{self.base_url}/functions",
            headers=self.headers,
            json={
                "name": name,
                "namespace_id": namespace_id,
                "environment_variables": env,
                "min_scale": min_scale,
                "max_scale": max_scale,
                "runtime": runtime,
                "memory_limit": memory_limit,
                "timeout": timeout,
                "handler": handler,
                "privacy": privacy,
                "description": description,
                "secret_environment_variables": self._to_secret_list(secrets),
            },
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def list_functions(self, namespace_id: str) -> list[dict[str, Any]]:
        """List deployed function in namespace."""

        resp = requests.get(
            f"{self.base_url}/functions?namespace_id={namespace_id}",
            headers=self.headers,
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return []

        return resp.json().get("functions", [])

    def upload_function(self, function_id: str, content_length: int) -> Optional[str]:
        """Get the upload url of a function."""
        resp = requests.get(
            f"{self.base_url}/functions/{function_id}"
            + f"/upload-url?content_length={str(content_length)}",
            headers=self.headers,
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json().get("url", None)

    def deploy_function(self, function_id: str) -> bool:
        """Deploy a function."""
        resp = requests.post(
            f"{self.base_url}/functions/{function_id}/deploy",
            headers=self.headers,
            json={},
            timeout=TIMEOUT,
        )

        return resp.status_code == 200

    def update_function(
        self,
        function_id: str,
        runtime: str,
        handler: str,
        privacy: str = "unknown_privacy",
        env: dict = None,
        min_scale: int = None,
        max_scale: int = None,
        memory_limit: int = None,
        timeout: str = None,
        description: str = None,
        secrets: dict = None,
    ) -> Optional[dict[str, Any]]:
        """Update the function."""

        resp = requests.patch(
            f"{self.base_url}/functions/{function_id}",
            headers=self.headers,
            json={
                "min_scale": min_scale,
                "max_scale": max_scale,
                "runtime": runtime,
                "memory_limit": memory_limit,
                "timeout": timeout,
                "handler": handler,
                "privacy": privacy,
                "description": description,
                "secret_environment_variables": self._to_secret_list(secrets),
                "environment_variables": env,
            },
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def get_function(self, function_id: str) -> Optional[dict[str, Any]]:
        """Get details on a function."""
        resp = requests.get(
            f"{self.base_url}/functions/{function_id}",
            headers=self.headers,
            timeout=TIMEOUT,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def delete_function(self, function_id: str) -> bool:
        """Delete the function."""
        resp = requests.delete(
            f"{self.base_url}/functions/{function_id}",
            headers=self.headers,
            timeout=TIMEOUT,
        )

        return resp.status_code == 200
