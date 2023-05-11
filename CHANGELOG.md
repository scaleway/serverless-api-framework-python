# Changelog

All notable changes to this project will be documented in this file.

<!-- The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## [0.0.4] - 2023-02-27

### Fixed

- Fixed a bug which prevented the use of multiple modules
- Fixed env vars were being overwritten by config file

## [1.0.0] - 2023-04-11

### Feature

- Add support for self hosted serverless gateway

## [1.0.2] - 2023-05-05

### Fixed

- Fixed decorator nesting that breaks compatibility with local testing framework

## [1.1.0] - 2023-05-11

### Feature

- Added dev command to test functions locally
- Added `--verbose` and `--log-level` flags for a better feedback when deploying

### Fixed

- Setting `http_option=enabled` will now correctly apply HTTPs-only when deploying with the API

### Removed

- Removed generating Terraform and Serverless Framework configuration files as those features were mostly unused. This does not break the `scw-serverless` library but it removes a command from the CLI. We think those changes will help improve the overall quality of the tool.
