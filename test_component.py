import pytest
import hashlib
import random
from functools import partial
from Component import *
from uuid import UUID

# Test utilities to examine security levels in method access and use
class Base:
    """A simple class containing settings for a completely mutable component"""
    msg_key = lambda x: - x.metadata["timestamp"].timestamp().hex()
    conn_crit = lambda s, y: True
    disc_crit = lambda s, y: True
    is_conn_crit_mut = True
    is_disc_crit_mut = True
    api_accessibility = {
        func: (lambda x: True) for
        func in
        inspect.getmembers(Component, inspect.ismethod)}
    api_mutable = True
    register_accessor = lambda x: True
    register_mutator = lambda x: True
    register_immutability: False

class Strict:
    """A simple class containing settings for a strictly immutable component"""
    msg_key = lambda x: - x.metadata["timestamp"].timestamp().hex()
    conn_crit = lambda s, y: False
    disc_crit = lambda s, y: False
    is_conn_crit_mut = False
    is_disc_crit_mut = False
    api_accessibility = {
        func: (lambda x: False) for
        func in
        inspect.getmembers(Component, inspect.ismethod)}
    api_mutable = False
    register_accessor: lambda x: False
    register_mutator = lambda x: False
    register_immutability: True

class Complex:
    """A simple class containing settings for a component whose api modifiability can be adjusted.
    Specifically registers access can be modified but registers cannot be removed"""
    msg_key = lambda x: - x.metadata["timestamp"].timestamp().hex()
    conn_crit = lambda s, y: hashlib.md5(s) > y.hash
    disc_crit = lambda s, y: hashlib.md5(s) > y.hash
    is_conn_crit_mut = True
    is_disc_crit_mut = True
    api_accessibility = {
        func: (lambda x: x.status) for
        func in
        inspect.getmembers(Component, inspect.ismethod)}
    api_mutable = True
    register_accessor = lambda x: x.status
    register_mutator = lambda x: x.status
    register_immutability = True

#Functions used for creating test components
def generate_name(seed=datetime.now().microsecond) -> str:
    """
    Generates a guid-based name
    :param seed An integer used to seed the random name generation
    :returns A string containing the hex characters of GUID
    """
    rand = random.Random()
    rand.seed(seed)
    return UUID(bytes=rand.getrandbits(128).to_bytes(128,"big")).hex

def default_api() -> List[str]:
    """
    Gets the default api of a component
    :return:  A list of strings containing the API function names
    """
    return [key for key in Component(Base.msg_key).exec_list.keys()]

def generate_prob_api_denial(api_list: List[str], seed : int = datetime.now().microsecond) -> \
        Dict[str, Callable[Generic, bool]]:
    """
    Randomly denies access to certain API functions
    :param api_list: The list of functions in the api
    :param seed: An int, allows for seeding the tests with a certain seed to create predictable results
    :return: Returns an api where roughly 1/2 the functions are denied access
    """
    random_gen = random.Random()
    random_gen.seed(seed)
    return {func: (lambda x: False) for
            func in api_list if
            random_gen.random() > 0.5}

def generate_registers(register_types):
    """
    Generates registers and types given a library of potential types
    """


def generate_component(component_type: Literal[Base, Strict, Complex],
                       api_override: Dict[str, Callable[Generic, bool]] = None) -> Component:
    """
    Factory method, generates a component of component_type, if the api is overridden then the api_will include the
    specified modifications
    :param component_type: A component of the Base, Strict, Complex variety
    :param api_override: A dict containing the permission overrides for
    api access
    :return: Returns a constructed component with the specified parameters
    """
    if api_override is None or component_type is Base or component_type is Strict:
        api_override = component_type.api_accessibility
    return Component(component_type.msg_key,
                     component_type.conn_crit,
                     component_type.disc_crit,
                     component_type.is_conn_crit_mut,
                     component_type.is_disc_crit_mut,
                     api_override,
                     component_type.api_mutable)

def add_contents_to_registers(component, register_contents):
    component

def generate_component_with_registers(component_type,api_override = None, registers=None):
    component = generate_component(component_type, api_override)
    if registers is not None:
        for k,v in registers:
            component.add(k,
                          component_type.register_accessor,
                          component_type.register_mutator,
                          component_type.register_immutability,
                          v)
    return component


@pytest.fixture(scope="module")
def base_component() -> Component:
    """Generates a component with complete mutability
    :returns a fully mutable component"""
    return generate_component(Base)

@pytest.fixture(scope="module")
def strict_component() -> Component:
    """Generates a component with no mutability
    :returns a fully immutable component"""
    return generate_component(Strict)

@pytest.fixture(scope="module")
def complex_component(api) -> Component:
    """Generates a component with a complex api. Mutability is determined
    by the caller.
    :param api: An api"""
    return generate_component(Complex, api)

@pytest.fixture(scope="module")
def register_contents() -> Dict[str, Any]:
    return {
        "zero":  lambda: 0,
        "one": lambda: 1,
        "random_int": lambda: random.randint(0,10000000),
        "random_float": lambda: random.randrange(0,10000000),
        "boolean_val": lambda: random.random() > 0.5,
        "random_addition_func": lambda: partial((lambda x,y: x + y),
                                                random.randint(0,1000)),
        "random_mult_func": lambda: partial((lambda x,y: x * y),
                                                random.randint(0,1000)),
        "single_arg_func": lambda seed: partial(lambda x,y: x(y), seed),
        "class": lambda seed: type("test_class", (object, object), seed)
    }


class TestComponent:

    def test_get(self, base_component, strict_component, complex_component, register_contents):
        def

    def test_eval(self):

    def test_update(self):

    def test_delete(self):

    def test_add(self):

    def test_modify_mutator(self):

    def test_modify_accessor(self):

    def test_push_message(self):

    def test_get_next_message(self):

    def test_execute_message_contents(self):

    def test_modify_connection_criteria(self):

    def test_modify_disconnection_criteria(self):

    def test_connect_entity(self):

    def test_disconnect_entity(self):

    def test_message_entity(self):

    def test_modify_api_permission(self):

    def test_run(self):
