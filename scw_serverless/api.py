import requests

API_BASE = "https://api.scaleway.com/functions/v1beta1"


class Api:
    def __init__(self, region: str, secret_key: str):
        self.secret_key = secret_key
        self.region = region

    def list_namespaces(self, project_id):
        req = requests.get(
            f"{API_BASE}/regions/{self.region}/namespaces?project_id={project_id}",
            headers={"X-Auth-Token": self.secret_key},
        )

        if req.status_code != 200:
            return []

        return req.json()["namespaces"]

    def get_namespace(self, namespace_id):
        req = requests.get(
            f"{API_BASE}/regions/{self.region}/namespaces/{namespace_id}",
            headers={"X-Auth-Token": self.secret_key},
        )

        if req.status_code != 200:
            return None

        return req.json()

    def create_namespace(
        self,
        name: str,
        project_id: str,
        env: dict = None,
        description: str = None,
        secrets: dict = None,
    ):
        req = requests.post(
            f"{API_BASE}/regions/{self.region}/namespaces",
            headers={"X-Auth-Token": self.secret_key},
            json={
                "name": name,
                "environment_variables": env,
                "project_id": project_id,
                "description": description,
                "secret_environment_variables": self.to_secret_list(secrets),
            },
        )

        if req.status_code != 200:
            return None

        return req.json()

    def update_namespace(
        self,
        env: dict = None,
        description: str = None,
        secrets: dict = None,
    ):
        req = requests.patch(
            f"{API_BASE}/regions/{self.region}/namespaces",
            headers={"X-Auth-Token": self.secret_key},
            json={
                "environment_variables": env,
                "description": description,
                "secret_environment_variables": self.to_secret_list(secrets),
            },
        )

        if req.status_code != 200:
            return None

        return req.json()

    def to_secret_list(self, secrets: dict) -> list:
        secrets_list = []

        if secrets is not None:
            for k, v in secrets.items():
                secrets_list.append({"key": k, "value": v})

        return secrets_list

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
    ):
        req = requests.post(
            f"{API_BASE}/regions/{self.region}/functions",
            headers={"X-Auth-Token": self.secret_key},
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
                "secret_environment_variables": self.to_secret_list(secrets),
            },
        )

        if req.status_code != 200:
            return None

        return req.json()

    def list_functions(self, namespace_id: str):
        req = requests.get(
            f"{API_BASE}/regions/{self.region}/functions?namespace_id={namespace_id}",
            headers={"X-Auth-Token": self.secret_key},
        )

        if req.status_code != 200:
            return []

        return req.json()["functions"]

    def upload_function(self, function_id: str, content_length: int):
        req = requests.get(
            f"{API_BASE}/regions/{self.region}/functions/{function_id}/upload-url?content_length={str(content_length)}",
            headers={"X-Auth-Token": self.secret_key},
        )

        if req.status_code != 200:
            return None

        return req.json()["url"]

    def deploy_function(self, function_id: str):
        req = requests.post(
            f"{API_BASE}/regions/{self.region}/functions/{function_id}/deploy",
            headers={"X-Auth-Token": self.secret_key},
            json={},
        )

        return req.status_code == 200

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
    ):
        req = requests.patch(
            f"{API_BASE}/regions/{self.region}/functions/{function_id}",
            headers={"X-Auth-Token": self.secret_key},
            json={
                "min_scale": min_scale,
                "max_scale": max_scale,
                "runtime": runtime,
                "memory_limit": memory_limit,
                "timeout": timeout,
                "handler": handler,
                "privacy": privacy,
                "description": description,
                "secret_environment_variables": self.to_secret_list(secrets),
                "environment_variables": env,
            },
        )

        if req.status_code != 200:
            return None

        return req.json()

    def get_function(self, function_id: str):
        req = requests.get(
            f"{API_BASE}/regions/{self.region}/functions/{function_id}",
            headers={"X-Auth-Token": self.secret_key},
        )

        if req.status_code != 200:
            return None

        return req.json()

    def delete_function(self, function_id: str):
        req = requests.delete(
            f"{API_BASE}/regions/{self.region}/functions/{function_id}",
            headers={"X-Auth-Token": self.secret_key},
        )

        return req.status_code == 200
