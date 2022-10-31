from typing import Dict, List


class ConstructorDependency:
    @property
    def type_name(self):
        self.dependency_type.__name__

    def __init__(self, name, _type):
        self.name = name
        self.dependency_type = _type

    def __repr__(self) -> str:
        return self.dependency_type.__name__


class DependencyRegistration:
    @property
    def type_name(self):
        return self.__type_name

    @property
    def is_factory(self):
        return self.factory is not None

    @property
    def required_types(self):
        return self.__required_types

    @property
    def built(self):
        return self.instance is not None

    def __init__(
        self,
        dependency_type,
        lifetime,
        implementation_type=None,
        instance=None,
        factory=None,
        constructor_params: List[ConstructorDependency] = None
    ):
        self.dependency_type = dependency_type
        self.lifetime = lifetime
        self.implementation_type = implementation_type or dependency_type
        self.instance = instance
        self.factory = factory
        self.constructor_params = constructor_params

        self.configure_dependency()

    def configure_dependency(self):
        self.__required_types = [
            x.dependency_type for x in self.constructor_params]
        self.__type_name = self.implementation_type.__name__

    def get_activate_constructor_params(self, dependency_lookup: Dict[str, 'DependencyRegistration']):
        constructor_params = dict()

        for param in self.constructor_params:
            param_dependency = dependency_lookup.get(param.dependency_type)

            constructor_params[param.name] = param_dependency.activate(
                dependency_lookup=dependency_lookup)

        return constructor_params

    def activate(self, dependency_lookup):
        if self.lifetime == 'singleton' and self.built:
            return self.instance

        if self.lifetime == 'singleton' and len(self.constructor_params) == 0:
            self.instance = self.implementation_type()
            return self.instance

        constructor_params = self.get_activate_constructor_params(
            dependency_lookup=dependency_lookup)

        if self.lifetime == 'singleton':
            self.instance = self.implementation_type(**constructor_params)
            return self.instance

        if self.lifetime == 'transient':
            return self.implementation_type(**constructor_params)
