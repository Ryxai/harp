import pytest
from Component import *

def setup_module(module):
    msg_key = lambda x: - x.metadata["timestamp"].timestamp().hex()
    base_conn_crit = lambda s, y: True
    base_disc_crit = lambda s, y: True
    base_is_conn_crit_mut = True
    base_is_disc_crit_mut =


class TestComponent:
    def setup(self):
        component = Component

    def test_get(self):

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
