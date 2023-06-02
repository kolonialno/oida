import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List
from oida.component import Component

from oida.discovery import find_apps, find_components


class Statistics:

    def __init__(self, components: List[Component], uncomponentized_apps: List[Path]) -> None:
        self.components = components
        self.uncomponentized_apps = uncomponentized_apps
        self.componentized_apps = list()
        for component in self.components:
            self.componentized_apps = self.componentized_apps + component.apps
    

    def get_number_of_components(self):
        return len(self.components)
    
    
    def get_total_number_of_apps(self):
        return len(self.componentized_apps) + len(self.uncomponentized_apps)
    

    def get_number_of_componentized_apps(self):
        return len(self.componentized_apps)
    

    def get_componentized_apps_fraction(self):
        return self.get_number_of_componentized_apps() / self.get_total_number_of_apps()
    
    
    def get_components_with_public_API(self):
        return list(filter(lambda component: component.has_public_API, self.components))
    

    def get_number_of_components_with_public_API(self):
        return len(self.get_components_with_public_API())
    

    def get_components_with_public_API_fraction(self):
        return self.get_number_of_components_with_public_API() / self.get_number_of_components()


    def list_componentized_apps(self):
        return map(lambda component: component.name, self.componentized_apps)


    def list_uncomponentized_apps(self):
        return map(lambda component: component.name, self.uncomponentized_apps)
    

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
            % of Apps in Compoments:                 {"{:>4.0f}".format(self.get_componentized_apps_fraction()*100) }%
            --------------------------------------------------
            """


def generate_statistics(path: Path) -> Statistics:
    components = list(find_components(path=path))
    uncomponentized_apps = list(find_apps(path=path))
    return Statistics(components=components, uncomponentized_apps=uncomponentized_apps)