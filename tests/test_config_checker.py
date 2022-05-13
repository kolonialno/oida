from unittest import mock

import pytest

from oida.checkers import SubserviceConfigChecker
from oida.reporter import Violation

pytestmark = pytest.mark.module(name="confservice", package="project")


@pytest.mark.module("SUBSERVICES = {}")
def test_empty_subservice_config(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module("SUBSERVICES: dict = {}")
def test_empty_subservice_config_with_type_annotation(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module("SUBSERVICES: dict")
def test_subservice_config_with_type_annotation_no_value(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module("SUBSERVICES = None")
def test_none_subservice_config(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=14,
        message="Invalid sub-service config, should be a dict literal",
    )


@pytest.mark.module("SUBSERVICES: dict = None")
def test_none_subservice_config_with_type_annotation(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=20,
        message="Invalid sub-service config, should be a dict literal",
    )


@pytest.mark.module('SUBSERVICES = {"foo": None}')
def test_subservice_config_app_none(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY, line=1, column=22, message="Invalid sub-service config"
    )


@pytest.mark.module('SUBSERVICES = {"foo": {}}')
def test_subservice_config_one_empty(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('SUBSERVICES = {"foo": {}, "bar": {}}')
def test_subservice_config_two_empty(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('SUBSERVICES = {"foo": {"database": "test"}}')
def test_subservice_config_database(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('SUBSERVICES = {"foo": {"database": None}}')
def test_subservice_config_database_invalid_value(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=23,
        message='Invalid value for "database", should be a string literal',
    )


@pytest.mark.module('SUBSERVICES = {"foo": {"apps": []}}')
def test_subservice_config_apps_empty_list(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('SUBSERVICES = {"foo": {"apps": ["test"]}}')
def test_subservice_config_apps_one(
    checker: SubserviceConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('SUBSERVICES = {"foo": {"apps": None}}')
def test_subservice_config_apps_invalid_value(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=23,
        message='Invalid value for "apps", should be a list of string literals',
    )


@pytest.mark.module('SUBSERVICES = {"foo": {"apps": [None]}}')
def test_subservice_config_apps_invalid_value_in_list(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=32,
        message='Invalid value for "apps", should be a list of string literals',
    )


@pytest.mark.module('SUBSERVICES = {"foo": {"bar": ...}}')
def test_subservice_config_unknown_key(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=23,
        message='Unknown config key "bar", choices are "database" or "apps"',
    )


@pytest.mark.module('SUBSERVICES = {"foo": {1: ...}}')
def test_subservice_config_invalid_key(
    checker: SubserviceConfigChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=23,
        message='Invalid config key, choices are "database" or "apps"',
    )
