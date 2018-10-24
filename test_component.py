import pytest
import hashlib
import random
from functools import partial
from Component import *

class Base:
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
class Strict:
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
class Complex:
    msg_key = lambda x: - x.metadata["timestamp"].timestamp().hex()
    conn_crit = lambda s, y: hashlib.md5(s) > y.hash
    disc_crit = lambda s, y: hashlib.md5(s) > y.hash
    is_conn_crit_mut = True
    is_disc_crit_mut = True
    api_accessibility = {
        func: (lambda x: x.truth) for
        func in
        inspect.getmembers(Component, inspect.ismethod)}
    api_mutable = True
class Partial:
    api_accessibility = {
        func: (lambda x: x.truth) for
        func
    in inspect.getmembers(Component, inspect.ismethod)}

def default_api():
    return Component(Base.msg_key).exec_list.keys()

def partial_generator(api_list, seed = datetime.now().microsecond):
    random_gen = random.Random()
    random_gen.seed(seed)
    return {func: (lambda x: True) for
            func in api_list if
            random_gen.random() > 0.5}

def generate_component(type, api_override = None):
    if api_override is None:
        api_override = type.api_accessibility
    return Component(type.msg_key,
                     type.conn_crit,
                     type.disc_crit,
                     type.is_conn_crit_mut,
                     type.is_disc_crit_mut,
                     api_override,
                     type.api_mutable)

def

@pytest.fixture()
def base_component():
    return generate_component(Base)

@pytest.fixture()
def strict_component():
    return generate_component(Strict)

@pytest.fixture()
def complex_component(api):
    return generate_component(Complex)

@pytest.fixture(scope="module")
def register_contents():
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
    }

class TestComponent:

    def test_get(self, base_component):
        component = generate_component(Base, )

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
