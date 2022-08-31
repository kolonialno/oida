<h1 align="center">
  💅<br>
  Oida
</h1>

<p align="center">
  Oida is Oda's linter that enforces code style and modularization in our
  Django projects.
</p>

> **Warning**
> This project is still in early development. Expect breaking changes.

## Installation

Oida requires Python 3.10 or newer and can be installed from
[PyPI](https://pypi.org/project/oida):

`pip install oida`

## Usage

Oida is mainly intended to be used as a [flake8](https://flake8.pycqa.org/)
plugin. Once you have installed Oida and flake8 you can enable the linting
rules in the flake8 config:

```ini
[flake8]
extend-select = ODA
```

This will enable all our linting rules. You can also enable them one by one,
for a complete list of the various violations we report on see the
[oida/checkers/base.py](oida/checkers/base.py) file.

Oida also provides its own command line tool. This can also be used to run the
linting rules, but its main purpose is to provide tools to help transitioning
an existing codebase into one that's modularized. For details see `oida
--help`, but below is a quick summary of the provided commands:

### `oida lint`

This command is just another way of running the same checks that can be run
through `flake8`. Note that this does not support `# noqa` comments.

### `oida config`

This command will generate configuration files for components, which will be
automatically pre-filled with ignore rules for isolation violations. See below
for details on the configuration files.

### `oida componentize`

This command moves or renames a Django app, for example for moving an app into
a component. In addition to moving the files in the app it also updates (or
adds if needed) the app config and updates imports elsewhere in the project.


## Concepts

Oida is a static code analyzer, that also looks at the project structure. The
codebase is expected to be structured with a project as the top package and
then Django apps or _components_ as submodules below this, something like this:

    project/
    ├── pyproject.toml
    ├── setup.cfg
    └── project/
        ├── __init__.py
        ├── my_component/
        │   ├── __init__.py
        │   ├── first_app/
        │   │   ├── __init__.py
        │   │   ├── models.py
        │   │   └── ...
        │   ├── second_app/
        │   │   ├── __init__.py
        │   │   └── ....
        │   └── ...
        ├── third_app/
        │   ├── __init__.py
        │   └── ...
        └── ...

A component is basically a collection of Django apps. Oida will enforce
isolation of the apps inside the component, meaning that no code elsewhere in
the project will be allowed to import from the apps inside a component. Instead
a component should expose a public interface at the top level.

Because Oida is intended to be introduced in mature projects it's also possible
to grandfather in existing violations. That's done through a `confcomponent.py`
file placed at the root of the component. The only allowed statement in this
file is assigning a list of string literals to `ALLOWED_IMPORTS`:

```python
ALLOWED_IMPORTS = ["my_component.app.models.MyModel"]
```

This will silence any warnings when importing `my_component.app.models.MyModel`
in the current app/component.


## Checks

These are the checks currently implemented in Oida:

 * **component-isolation:** Checks that relative imports do not cross app boundaries.
 * **config:** Checks that component configuration files are valid
 * **relative-imports:** Checks that no imports are done across components.
