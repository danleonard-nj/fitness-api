from time import time
from di.dependencies import DependencyRegistration
from di.service_collection import ServiceCollection
from framework.logger import get_logger

logger = get_logger(__name__)


class ServiceProvider:
    @property
    def built_types(self):
        return self.__built_types

    @property
    def built_type_lookup(self):
        return self.__built_type_lookup

    @property
    def built_dependencies(self):
        return self.__built_dependencies

    @property
    def singleton_registrations(self):
        return self.__singletons

    @property
    def factory_registrations(self):
        return self.__factories

    @property
    def transient_registrations(self):
        return self.__transients

    @property
    def transient_types(self):
        return self.__transient_types

    @property
    def to_instantiate(self):
        return len(self.singleton_registrations) + len(self.factory_registrations)

    def __init__(self, service_collection: ServiceCollection):
        container = service_collection.get_container()

        self.__dependency_lookup = container
        self.__dependencies = list(container.values())

        self.__built_dependencies = []
        self.__built_types = []
        self.__built_type_lookup = dict()

        self.__initialize_provider()

    def __initialize_provider(self):
        self.__transients = [
            x for x in self.__dependencies if x.lifetime == 'transient']
        self.__transient_types = [
            x.implementation_type for x in self.__transients]
        self.__factories = [
            x for x in self.__dependencies if x.lifetime == 'singleton' and x.is_factory]
        self.__singletons = [
            x for x in self.__dependencies if x.lifetime == 'singleton' and not x.is_factory]

    def __set_built_dependency(self, registration: DependencyRegistration):
        self.__built_type_lookup[registration.implementation_type] = registration
        self.__built_types.append(registration.implementation_type)
        self.__built_dependencies.append(registration)

    def resolve(self, _type):
        start_time = time()
        logger.info(f"Resolving service for type: {_type.__name__}")
        registration = self.__get_registered_dependency(
            implementation_type=_type)
        logger.info(f"Service type: {registration.lifetime}")

        if registration.lifetime == 'transient':
            # Activate an instance of the transient dependency using the
            # available built types
            instance = registration.activate(self.__dependency_lookup)
            end_time = time()
            logger.info(f'Dependency resolved in: {end_time - start_time}')
            return instance
        elif registration.lifetime == 'singleton':
            end_time = time()
            logger.info(f'Dependency resolved in: {end_time - start_time}')
            return registration.instance

    def __verify_singleton(self, registration: DependencyRegistration):
        for required_type in registration.required_types:
            required_type_registration = self.__get_registered_dependency(
                implementation_type=required_type,
                requesting_type=registration)

            if required_type_registration.lifetime == 'transient':
                raise Exception(
                    f"Cannot inject dependency '{required_type.__name__}' with transient lifetime into singleton '{registration.type_name}'")

    def __can_build_type(self, registration: DependencyRegistration):
        # Verify no singleton constructor param dependencies are
        # transients, these cannot be injected into a singleton
        if registration.lifetime == 'singleton':
            return self.__can_build_singleton_type(
                registration=registration)

    def __can_build_singleton_type(self, registration: DependencyRegistration):
        self.__verify_singleton(registration=registration)

        for required_type in registration.required_types:
            if required_type not in self.built_types:
                return False

        return True

    def __get_registered_dependency(
        self,
        implementation_type: type,
        requesting_type: DependencyRegistration = None
    ):
        # for dependency in self.__dependencies:
        #     if dependency.implementation_type == implementation_type:
        #         return dependency
        registration = self.__dependency_lookup.get(implementation_type)

        if registration is not None:
            return registration

        if requesting_type is not None:
            raise Exception(
                f"Failed to locate registration for type '{implementation_type.__name__}' when instantiating type '{requesting_type.type_name}'")
        else:
            raise Exception(
                f"Failed to locate registration for type '{implementation_type.__name__}'")

    def build(self):
        # To call the provider built, we have to have created an
        # instance of all dependencies registered as singleton
        # or factories
        while len(self.built_dependencies) < self.to_instantiate:
            cycle_start = len(self.built_dependencies)
            self.__build_singletons()
            self.__build_factories()
            cycle_end = len(self.built_dependencies)

            # If we haven't managed to create any depdencies in
            # a cycle, and we also haven't met the total number
            # of built depenencies to call the container built,
            # we're in a loop and there is no valid dependency
            # chain
            if cycle_start == cycle_end:
                raise Exception(
                    f'Dependency chain is not valid, check your registration types')

        logger.info('Built the provider!')

    def __build_singletons(self):
        for registration in [x for x in self.singleton_registrations if not x.built]:
            if len(registration.constructor_params) == 0:
                logger.info(f"Building type: {registration.type_name}")

                registration.activate(self.__dependency_lookup)
                self.__set_built_dependency(registration=registration)

            elif self.__can_build_type(registration=registration):
                logger.info(f"Building type: {registration.type_name}")

                registration.activate(self.__dependency_lookup)
                self.__set_built_dependency(registration=registration)

    def __build_factories(self):
        for registration in [x for x in self.factory_registrations if not x.built]:
            registration.instance = registration.factory(self)
            self.__set_built_dependency(registration=registration)
