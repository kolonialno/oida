<h1 align="center">
  💅<br>
  Oida
</h1>

<p align="center">
  Oida is Oda's internal linter that enforces code style and modularization in
  our Django projects.
</p>

## Usage

    oida <path>


## Concepts

Oida expects the code to be structured with a project as the top package and
then apps as submodules below this

Here's an example project structure:

    project/
        __init__.py
        first_app/
            __init__.py
            ...
        second_app/
            __init__.py
            ....
        third_app/
            __init__.py
            ...
        ...


## Checks

 * **Apps:** This check validates that no imports are done across sub-modules.
 * **Imports:**: This module checks that relative imports to not cross app
   boundaries.
