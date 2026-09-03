import ast

import pytest

from oida.checkers import Code, RecordBuildQueryChecker, Violation
from oida.config import ProjectConfig

# Default to testing in a records.py file
pytestmark = pytest.mark.module(name="records", module="project.app")


def message(trigger: str) -> str:
    return (
        "Database queries are not allowed in build methods, "
        f"fetch the data first (found '{trigger}')"
    )


# Tests for violations


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = Item.objects.filter(obj=obj)
            return cls()
    """
)
def test_objects_manager_in_build(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".objects"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.order_by("name")
            return cls()
    """
)
def test_queryset_method_on_related_manager_in_build(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".order_by()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """
)
def test_all_on_related_manager_in_build(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            names = [item.name for item in obj.items.all()]
            return cls(names=names)
    """
)
def test_query_in_comprehension_in_build(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=39, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            def inner():
                return Item.objects.filter(obj=obj)

            return cls(items=inner())
    """
)
def test_query_in_nested_function_in_build(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=5, column=19, code=Code.ODA008, message=message(".objects"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build_pickup(cls, obj):
            qs = obj.items.all()
            return cls()
    """
)
def test_query_in_build_prefixed_method(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        async def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """
)
def test_query_in_async_build(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = (
                Item.objects.filter(obj=obj)
                .select_related("thing")
                .order_by("name")
            )
            return cls()
    """
)
def test_chained_query_reported_once_at_first_line(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=5, column=12, code=Code.ODA008, message=message(".objects"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.a.all() or obj.b.all()
            return cls()
    """
)
def test_two_queries_on_one_line_reported_once(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="day_routes",
    module="project.app.records",
)
def test_query_in_records_package_module(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


def test_query_in_records_package_init() -> None:
    """The name is empty for __init__.py, so the module name has to match."""

    source = (
        "class FooRecord(CamelModel):\n"
        "    @classmethod\n"
        "    def build(cls, obj):\n"
        "        qs = obj.items.all()\n"
        "        return cls()\n"
    )
    checker = RecordBuildQueryChecker(
        module="project.app.records",
        name="",
        component_config=None,
        project_config=ProjectConfig(),
        source_lines=source.splitlines(),
    )
    checker.visit(ast.parse(source))

    assert checker.violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


# Tests for non-violations


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, rule):
            return cls(
                weekday=rule.weekday,
                group_id=rule.route_group.fulfillment_group_id,
                name=rule.display_name(),
            )
    """
)
def test_attribute_traversal_and_method_calls_are_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, lookup, values):
            name = lookup.get("name")
            keys = lookup.keys()
            pairs = lookup.items()
            totals = lookup.values()
            copied = lookup.copy()
            lookup.update(values)
            hits = values.count(1)
            values.reverse()
            return cls(name=name)
    """
)
def test_dict_and_list_methods_are_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, qs):
            return cls(a=qs.get(), b=qs.first(), c=qs.last())
    """
)
def test_get_first_and_last_are_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            return cls()

        @classmethod
        def empty(cls):
            return cls(items=Item.objects.all())
    """
)
def test_query_in_non_build_method_is_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="services",
)
def test_query_outside_a_records_module_is_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="test_records",
)
def test_query_in_test_file_is_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    module="project.app.tests.records",
)
def test_query_in_test_module_is_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    def build(obj):
        return obj.items.all()
    """
)
def test_module_level_build_function_is_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module("QUERYSET = Item.objects.all()")
def test_module_level_query_is_allowed(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class Status(Enum):
        @classmethod
        def build(cls, obj):
            return obj.items.all()
    """
)
def test_enum_class_is_not_a_record(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(NamedTuple):
        @classmethod
        def build(cls, obj):
            return obj.items.all()
    """
)
def test_named_tuple_class_is_not_a_record(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()  # noida: ODA008
            return cls()
    """
)
def test_noida_comment_ignores_violation(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


# Tests for configuration


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_modules = ["schemas"]
    """
)
@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="schemas",
)
def test_custom_record_modules(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_modules = ["schemas"]
    """
)
@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """
)
def test_custom_record_modules_replaces_the_default(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_base_classes = ["BaseModel"]
    """
)
@pytest.mark.module(
    """\
    class FooRecord(BaseModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="fields",
)
def test_record_base_class_outside_a_records_module(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.module(
    """\
    class FooRecord(BaseModel):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="fields",
)
def test_base_classes_are_not_matched_by_default(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_base_classes = ["CamelModel"]
    """
)
@pytest.mark.module(
    """\
    class BaseFooRecord(CamelModel):
        pass


    class FooRecord(BaseFooRecord):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="fields",
)
def test_base_class_chain_within_the_same_file(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=8, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_base_classes = ["CamelModel"]
    """
)
@pytest.mark.module(
    """\
    class AuditRecord(CamelModel):
        pass


    class FooRecord(AuditRecord[list[str]]):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="fields",
)
def test_generic_base_class_is_unwrapped(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=8, column=13, code=Code.ODA008, message=message(".all()"))
    ]


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_base_classes = ["CamelModel"]
    """
)
@pytest.mark.module(
    """\
    class FooRecord(FooRecord):
        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """,
    name="fields",
)
def test_self_referencing_base_class_does_not_recurse_forever(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_build_methods = ["serialize"]
    """
)
@pytest.mark.module(
    """\
    class FooRecord(CamelModel):
        @classmethod
        def serialize(cls, obj):
            qs = obj.items.all()
            return cls()

        @classmethod
        def build(cls, obj):
            qs = obj.items.all()
            return cls()
    """
)
def test_custom_record_build_methods(
    checker: RecordBuildQueryChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(line=4, column=13, code=Code.ODA008, message=message(".all()"))
    ]
