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
then apps or components as submodules below this.

Here's an example project structure:

    project/
        __init__.py
        my_component/
            __init__.py
            first_app/
                __init__.py
                ...
            second_app/
                __init__.py
                ....
            ...
        third_app/
            __init__.py
            ...
        ...


## Checks

 * **Apps:** Checks that no imports are done across sub-modules.
 * **Imports:** Checks that relative imports to not cross app boundaries.
 * **Config:** Checks that component configuration files are valid
