import ast
from fnmatch import fnmatchcase

from ..config import ComponentConfig, ProjectConfig
from .base import Checker, Code

# Queryset and manager methods that hit, or build a query against, the
# database. Names that collide with common builtin types are left out on
# purpose: 'get', 'values', 'update', 'count', 'reverse', 'union',
# 'intersection' and 'difference' are all far more likely to be a dict, list
# or set method inside a build method. Queries using those still get caught
# through the '.objects' manager or an earlier method in the same chain.
QUERY_METHODS = frozenset(
    {
        "aggregate",
        "all",
        "annotate",
        "bulk_create",
        "bulk_update",
        "create",
        "defer",
        "delete",
        "distinct",
        "earliest",
        "exclude",
        "exists",
        "filter",
        "get_or_create",
        "in_bulk",
        "iterator",
        "latest",
        "none",
        "only",
        "order_by",
        "prefetch_related",
        "raw",
        "refresh_from_db",
        "save",
        "select_for_update",
        "select_related",
        "update_or_create",
        "values_list",
    }
)

# Base classes that rule a class out as a record, even in a records module
NON_RECORD_BASES = frozenset(
    {
        "Enum",
        "Flag",
        "IntEnum",
        "IntFlag",
        "NamedTuple",
        "Protocol",
        "StrEnum",
        "TypedDict",
    }
)


class RecordBuildQueryChecker(Checker):
    """
    Check that record build methods don't query the database.

    Records are the request and response types of a web API. Fetching data
    belongs outside them, so a build method may only massage what it is
    given.

    Records are found either by module, through the 'record_modules'
    setting, which defaults to files named records.py and modules under a
    records/ directory, or by base class, through the 'record_base_classes'
    setting, which is empty by default. Base classes are matched by name and
    followed through bases defined in the same file. Which methods to check
    is set by 'record_build_methods', which defaults to 'build' and
    'build_*'.

    Example violations:
        class FooRecord(CamelModel):
            @classmethod
            def build(cls, obj):
                items = Item.objects.filter(obj=obj)  # <-- Not allowed
                stops = obj.stops.order_by("name")  # <-- Not allowed
                return cls(items=items, stops=stops)

    Valid usage:
        class FooRecord(CamelModel):
            @classmethod
            def build(cls, obj, items):
                return cls(name=obj.name, group=obj.group.name, items=items)
    """

    slug = "record-build-no-queries"

    def __init__(
        self,
        module: str | None,
        name: str,
        component_config: ComponentConfig | None,
        project_config: ProjectConfig,
        source_lines: list[str] | None = None,
    ) -> None:
        super().__init__(module, name, component_config, project_config, source_lines)
        self._is_record_module = self._check_if_record_module()
        self._local_bases: dict[str, list[str]] = {}
        self._reported_lines: set[int] = set()

    def _check_if_record_module(self) -> bool:
        """
        Check if the current file holds records, as configured by the
        'record_modules' setting.
        """

        # Don't check test files
        if self.name.startswith("test_"):
            return False
        if self.module and (".tests." in self.module or ".test." in self.module):
            return False

        for candidate in self.project_config.record_modules:
            if self.name == candidate:
                return True
            if self.module and (
                self.module == candidate
                or self.module.endswith(f".{candidate}")
                or f".{candidate}." in self.module
            ):
                return True

        return False

    @staticmethod
    def _base_names(node: ast.ClassDef) -> list[str]:
        """Get the name of each base class, ignoring anything we can't name."""

        names: list[str] = []
        for base in node.bases:
            # Unwrap generic bases, eg. AuditLogRecord[list[str]]
            if isinstance(base, ast.Subscript):
                base = base.value
            if isinstance(base, ast.Attribute):
                names.append(base.attr)
            elif isinstance(base, ast.Name):
                names.append(base.id)
        return names

    def _has_record_base(self, bases: list[str]) -> bool:
        """
        Check if any base class is configured as a record base, following
        bases that are defined in this file.
        """

        configured = set(self.project_config.record_base_classes)
        if not configured:
            return False

        seen: set[str] = set()
        queue = list(bases)
        while queue:
            base = queue.pop()
            if base in configured:
                return True
            if base in seen:
                continue
            seen.add(base)
            queue.extend(self._local_bases.get(base, ()))

        return False

    def _is_record(self, node: ast.ClassDef) -> bool:
        bases = self._base_names(node)
        if NON_RECORD_BASES.intersection(bases):
            return False
        return self._is_record_module or self._has_record_base(bases)

    def _is_build_method(self, name: str) -> bool:
        return any(
            fnmatchcase(name, pattern)
            for pattern in self.project_config.record_build_methods
        )

    @staticmethod
    def _query_trigger(node: ast.Attribute | ast.Call) -> str | None:
        if isinstance(node, ast.Attribute):
            return ".objects" if node.attr == "objects" else None
        if isinstance(node.func, ast.Attribute) and node.func.attr in QUERY_METHODS:
            return f".{node.func.attr}()"
        return None

    def _check_build_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """
        Report one violation per line of the build method that queries.

        Every node in a chained call shares the position of the leftmost
        token, so a call spanning several lines is reported once, on the
        line the expression starts on. That is also the line a
        '# noida: ODA008' comment has to go on.
        """

        found: dict[int, tuple[ast.Attribute | ast.Call, str]] = {}
        for child in ast.walk(node):
            if not isinstance(child, (ast.Attribute, ast.Call)):
                continue
            trigger = self._query_trigger(child)
            if trigger is None:
                continue
            # '.objects' says the most when a chain matches several times
            # on the same line
            if child.lineno not in found or trigger == ".objects":
                found[child.lineno] = (child, trigger)

        for line in sorted(found):
            if line in self._reported_lines:
                continue
            self._reported_lines.add(line)
            child, trigger = found[line]
            self.report_violation(
                child,
                Code.ODA008,
                "Database queries are not allowed in build methods, "
                f"fetch the data first (found '{trigger}')",
            )

    def visit_Module(self, node: ast.Module) -> None:
        """Map every class in the file to its bases, then walk the file."""

        self._local_bases = {
            child.name: self._base_names(child)
            for child in ast.walk(node)
            if isinstance(child, ast.ClassDef)
        }
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self._is_record(node):
            for child in node.body:
                if isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and self._is_build_method(child.name):
                    self._check_build_method(child)

        self.generic_visit(node)
