import inspect
from typing import Dict

from di.dependencies import (ConstructorDependency,
                             DependencyRegistration)


class ServiceCollection:
    def __init__(self):
        self.__container = dict()

    def get_type_dependencies(self, _type):
        params = inspect.signature(_type).parameters

        types = []
        for name, param in params.items():
            if param.annotation == inspect._empty:
                raise Exception(
                    f"Encountered parameter with no annotation in type {_type.__name__}: {name}")

            constructor_dependency = ConstructorDependency(
                name=name,
                _type=param.annotation)
            types.append(constructor_dependency)
        return types

    def add_singleton(self, dependency_type, implementation_type=None, instance=None, factory=None):
        self.__register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='singleton',
            instance=instance,
            factory=factory)

    def add_transient(self, dependency_type, implementation_type=None):
        self.__register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='transient')

    def __register_dependency(self, implementation_type, dependency_type, **kwargs):
        if implementation_type is None:
            implementation_type = dependency_type

        factory = kwargs.get('factory')

        if factory is None:
            constructor_params = self.get_type_dependencies(
                _type=implementation_type)
        else:
            constructor_params = []

        dependency = DependencyRegistration(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            constructor_params=constructor_params,
            **kwargs)

        self.__container[dependency_type] = dependency

    def get_container(self) -> Dict[type, DependencyRegistration]:
        return self.__container
