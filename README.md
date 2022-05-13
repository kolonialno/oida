<h1 align="center">
  💅<br>
  Oida
</h1>

<p align="center">
  Oda's very own linter
</p>

Oida is Oda's internal linter that enforces code style and modularization in
our Django projects.

## Usage

    oida <path>


## Concepts

Oida expects the code to be structured with a project as the top package and
then apps as submodules below this. Sub-services are a group of apps that are
freely allowed to import from each other.Sub-services are defined in a
`confservices.py` file.

Here's an example project structure:

    project/
        __init__.py
        confservice.py
        first_app/
            __init__.py
            ...
        second_app/
            __init__.py
            ....
        ...


## Checks

 * **Apps:** This check validates that no imports are done across sub-modules.
 * **Config:** This check validates sub-services configs found in
   confservice.py files.
 * **Imports:**: This module checks that relative imports to not cross app
   boundaries.
