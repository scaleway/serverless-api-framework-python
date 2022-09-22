import requests

API_BASE = "https://api.scaleway.com/functions/v1beta1"


class Api:
    def __init__(self, region: str, secret_key: str):
        self.secret_key = secret_key
        self.region = region
        self.headers = {"X-Auth-Token": self.secret_key}
        self.base_url = f"{API_BASE}/regions/{self.region}"

    def list_namespaces(self, project_id):
        resp = requests.get(
            f"{self.base_url}/namespaces?project_id={project_id}",
            headers=self.headers,
        )

        if resp.status_code != 200:
            return []

        return resp.json()["namespaces"]

    def get_namespace(self, namespace_id):
        resp = requests.get(
            f"{self.base_url}/namespaces/{namespace_id}",
            headers=self.headers,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def create_namespace(
        self,
        name: str,
        project_id: str,
        env: dict = None,
        description: str = None,
        secrets: dict = None,
    ):
        resp = requests.post(
            f"{self.base_url}/namespaces",
            headers=self.headers,
            json={
                "name": name,
                "environment_variables": env,
                "project_id": project_id,
                "description": description,
                "secret_environment_variables": self.to_secret_list(secrets),
            },
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
    ):
        resp = requests.patch(
            f"{self.base_url}/namespaces/{namespace_id}",
            headers=self.headers,
            json={
                "environment_variables": env,
                "description": description,
                "secret_environment_variables": self.to_secret_list(secrets),
            },
        )

        if resp.status_code != 200:
            return None

        return resp.json()

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
                "secret_environment_variables": self.to_secret_list(secrets),
            },
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def list_functions(self, namespace_id: str):
        resp = requests.get(
            f"{self.base_url}/functions?namespace_id={namespace_id}",
            headers=self.headers,
        )

        if resp.status_code != 200:
            return []

        return resp.json()["functions"]

    def upload_function(self, function_id: str, content_length: int):
        resp = requests.get(
            f"{self.base_url}/functions/{function_id}/upload-url?content_length={str(content_length)}",
            headers=self.headers,
        )

        if resp.status_code != 200:
            return None

        return resp.json()["url"]

    def deploy_function(self, function_id: str):
        resp = requests.post(
            f"{self.base_url}/functions/{function_id}/deploy",
            headers=self.headers,
            json={},
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
    ):
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
                "secret_environment_variables": self.to_secret_list(secrets),
                "environment_variables": env,
            },
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def get_function(self, function_id: str):
        resp = requests.get(
            f"{self.base_url}/functions/{function_id}",
            headers=self.headers,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    def delete_function(self, function_id: str):
        resp = requests.delete(
            f"{self.base_url}/functions/{function_id}",
            headers=self.headers,
        )

        return resp.status_code == 200
