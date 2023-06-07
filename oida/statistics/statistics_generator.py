import importlib.util
import json
import sys
from pathlib import Path
from typing import List
from oida.component import Component

from oida.discovery import find_apps, find_components


class Statistics:

    def __init__(self, components: List[Component], uncomponentized_apps: List[Path]) -> None:
        """
        Creates a new Statistics object containing statistics information about the 
        componentization and modularization process for the project Oida was run on.
        It takes a list of components and a list of the apps that are not part of a
        component as input.
        """
        
        self.components = components
        self.uncomponentized_apps = uncomponentized_apps
        self.componentized_apps = list()
        for component in self.components:
            self.componentized_apps = self.componentized_apps + component.apps
    

    def get_number_of_components(self) -> int:
        """
        Returns the number of components in the project.
        """

        return len(self.components)
    
    
    def get_total_number_of_apps(self) -> int:
        """
        Returns the total number of apss in the project.
        """

        return len(self.componentized_apps) + len(self.uncomponentized_apps)
    

    def get_number_of_componentized_apps(self) -> int:
        """
        Returns the number of apps that are contained in components.
        """
        return len(self.componentized_apps)
    

    def get_componentized_apps_fraction(self) -> float:
        """
        Returns the fraction of apps that are contained in a component.
        This is equal to the number of componentized apps divided by the 
        total number of apps in the project.
        """
        return self.get_number_of_componentized_apps() / self.get_total_number_of_apps()
    
    
    def get_components_with_public_API(self) -> List[Component]:
        """
        Returns the components that have a public API defined (in selectors.py
        and services.py).
        """
        return list(filter(lambda component: component.has_public_API, self.components))
    

    def get_number_of_components_with_public_API(self) -> int:
        """
        Returns the number of components that have a public API defined
        (in selectors.py and services.py).
        """
        return len(self.get_components_with_public_API())
    

    def get_components_with_public_API_fraction(self) -> float:
        """
        Returns the fraction of components that have a public API defined
        (in selectors.py and services.py). This is equal to the number of
        components with a public API divided by the total number of components.
        """
        return self.get_number_of_components_with_public_API() / self.get_number_of_components()


    def list_componentized_apps(self) -> List[str]:
        """
        Returns a list containing the names of componentized apps. 
        """
        return list(map(lambda app_path: app_path.name, self.componentized_apps))


    def list_uncomponentized_apps(self) -> List[str]:
        """
        Returns a list containing the names of apps that are not part of a component. 
        """
        return list(map(lambda app_path: app_path.name, self.uncomponentized_apps))
    
    def json(self) -> str:
        """
        Returns a json representation of the Statistics object.
        """
        percentage_of_components_with_public_API = self.get_components_with_public_API_fraction() * 100.0
        percentage_of_apps_in_components = self.get_componentized_apps_fraction() * 100.0
        dict = {
            "components": {
                "number_of_components": self.get_number_of_components(),
                "number_of_components_with_public_API": self.get_number_of_components_with_public_API(),
                "percentage_of_components_with_public_API": percentage_of_components_with_public_API,
                "components": list(map(lambda component: component.name, self.components)),
                "components_with_public_API": list(map(lambda component: component.name, self.get_components_with_public_API())),
            },
            "apps": {
                "number_of_apps": self.get_total_number_of_apps(),
                "number_of_apps_in_components": self.get_number_of_componentized_apps(),
                "percentage_of_apps_in_components": percentage_of_apps_in_components,
                "componentized_apps": self.list_componentized_apps(),
                "uncomponentized_apps": self.list_uncomponentized_apps(),
            }
        }
        return json.dumps(dict, indent=4)

    def __str__(self):
        return f"""
            Statistics
            ==================================================
            Number of Components:                    {"{:>4}".format(self.get_number_of_components())}
            Number of Components with Public API:    {"{:>4}".format(self.get_number_of_components_with_public_API())}
            % of Components with Public API:         {"{:>4.0f}".format(self.get_components_with_public_API_fraction()*100)} %
            --------------------------------------------------
            Number of Apps:                          {"{:>4}".format(self.get_total_number_of_apps())}
            Number of Apps in Components:            {"{:>4}".format(self.get_number_of_componentized_apps())}
            % of Apps in Compoments:                 {"{:>4.0f}".format(self.get_componentized_apps_fraction()*100) } %
            --------------------------------------------------
            """


def generate_statistics(path: Path) -> Statistics:
    """
    Generates a Statistics object containing information about the modularization
    and componentization of the project at the specified path.
    """
    components = list(find_components(path=path))
    uncomponentized_apps = list(find_apps(path=path))
    return Statistics(components=components, uncomponentized_apps=uncomponentized_apps)