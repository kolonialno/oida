# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Global allowed_imports project config option

### Fixed

- Fix crash when using ignored_modules project config option

## [0.1.5] - 2023-04-20

### Fixed

- Fix explicit naming of Celery tasks using @coalesced_task instead of @app.task.

## [0.1.4] - 2023-03-22

### Fixed

- Fix crash in flake8 plugin on Python 3.11

## [0.1.3] - 2023-03-13

### Added

- The `componentize` command now adds explicit names for Celery tasks.

## [0.1.2] - 2023-02-09

### Changed

- Set `LIBCST_PARSER_TYPE` to `native` such that the `config` and `componentize` commands can parse Python 3.10 syntax

## [0.1.1] - 2022-08-31

## [0.1.0] - 2022-08-31

## [0.1.0-rc.1] - 2022-08-31

### Added

- The `componentize` command will now also update references in string literals

### Fixed

- Ignore module imports from the same app

## [0.1.0-alpha.1] - 2022-07-06

### Added

- Initial release

[Unreleased]: https://github.com/kolonialno/oida/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/kolonialno/oida/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/kolonialno/oida/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/kolonialno/oida/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/kolonialno/oida/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/kolonialno/oida/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/kolonialno/oida/compare/v0.1.0-rc.1-rc.1...v0.1.0
[0.1.0-rc.1]: https://github.com/kolonialno/oida/compare/v0.1.0-alpha.1...v0.1.0-rc.1
[0.1.0-alpha.1]: https://github.com/kolonialno/oida/releases/tag/v0.1.0-alpha.1
