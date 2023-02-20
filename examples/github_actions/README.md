# [Deploying using Github Actions](https://github.com/scaleway/serverless-api-project/tree/main/examples/github_actions)

This example provides a simple Github Action configuration file to get you started on deploying with `scw_serverless` in your CI/CD pipelines.

To do so, simply copy the `deploy.yml` file in `.github/workflows`.

Then set the following variables on your [Github Action Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets):

- `SCW_SECRET_KEY`: your user secret key
- `SCW_ACCESS_KEY`: your user access key
- `SCW_DEFAULT_PROJECT_ID`: your default project ID


This example will automatically run `scw-serverless deploy` in the project root to deploy your function on each git tag.

You can specify another deployment region (fr-par is the by-default deployment region) using for example:
```
scw-serverless deploy --region pl-waw app.py
```
