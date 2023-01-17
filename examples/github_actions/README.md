# [Deploying using Github Actions](https://github.com/scaleway/serverless-api-project/tree/main/examples/github_actions)

This example provides a simple Github Action configuration file to get you started on deploying with `scw_serverless` in your CI/CD pipelines.

To do so, simply copy the `deploy.yml` file in `.github/workflows`.

This example will automatically run `scw-serverless deploy` in the project root to deploy your on each git tag.
