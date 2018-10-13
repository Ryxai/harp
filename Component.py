import inspect
from heapqueue import *


class Message:
    """
    A message passed between two components

    :param: source, A Component, from which the message was sent
    :param func: A string, the api function of the target to be run
    :param return_req: A bool, representing whether a return message to source
    component is required
    :param key: An optional string, an index into one of the component's
    dictionaries
    :param value: An optional (Generic or Callable(Generic) -> bool), the value
    to be stored/updated
    :param accessor: An optional Callable(Generic) -> bool, used to validate
    access to the contents of one of the registers
    :param mutator: An optional Callable(Generic) -> bool, used to validate the
     update of one of the registers
    :param context: An optional generic, a container for additional information
    relevant to the function call
    :param criteria: An optional Callable(str, Generic) -> bool, used to
    evaluate entity linkage manipulation
    :param entity: An optional string, representing a named component in the construct
    wide index
    """
    def __init__(self,
                 source: 'Component',
                 func: str,
                 return_req: bool = False,
                 key: Union[str, None] = None,
                 value: Union[Generic, Callable[Generic, bool]] = None,
                 accessor: Union[Callable[Generic, bool], None] = None,
                 mutator: Union[Callable[Generic, bool], None] = None,
                 context: Union[Generic, None] = None,
                 criteria: Union[Callable[str, Generic, bool], None] = None,
                 entity: Union[str, None] = None):
        self.source = source
        self.func = func
        self.return_req = return_req
        self.key = key
        self.value = value
        self.accessor = accessor
        self.mutator = mutator
        self.context = context
        self.criteria = criteria
        self.entity = entity


class Component:
    """
    A representation of a computational unit of some variety. Designed to be sub-classed.

    :param message_key_func: A Callable(Generic) -> int, a key function used for
    message priority
    :param connection_criteria: A Callable(str, Generic) -> bool, represents the criteria requirements for
    connecting another entity to the current entity (unidirectionally)
    :param disconnection_criteria: A Callable(str, Generic) -> bool, represents the criteria requirements for
    disconnecting another entity from the current entity (unidirectionally)
    """

    entities: Dict[str, 'Component'] = dict()

    def __init__(self,
                 message_key_func: Callable[Generic, int],
                 connection_criteria: Callable[str, Generic, bool] = lambda s, context: True,
                 disconnection_criteria: Callable[str, Generic, bool] = lambda s, context: True,
                 is_connection_criteria_mutable: bool = True,
                 is_disconnection_criteria_mutable: bool = True
                 ):
        self.registers: Dict[str, Any] = dict()
        self.accessors: Dict[str, Callable[Generic, bool]] = dict()
        self.mutators: Dict[str, Callable[Generic, bool]] = dict()
        self.immutables: Dict[str, bool] = dict()
        self.messages: List[Generic] = []
        self.message_prioritizer: HeapQueue = HeapQueue(message_key_func)
        self.exec_list: Dict[str, Callable] = {func_name: bound_method for func_name, bound_method in
                                               inspect.getmembers(self, inspect.ismethod)}
        self.connection_criteria = connection_criteria
        self.disconnection_criteria = disconnection_criteria
        self.connected_entities: List[str] = []
        self.is_connection_criteria_mutable = is_connection_criteria_mutable
        self.is_disconnection_criteria_mutable = is_disconnection_criteria_mutable
        self.entities[self.__name__] = self

    def get(self, key: str, context: Generic) -> Union[KeyError, Generic, None]:
        if key not in self.registers or key not in self.accessors:
            return KeyError("Register does not exist", self, key, context)
        return self.registers[key] if self.mutators[key](context) else None

    def eval(self, key: str, context: Generic, content: Generic) -> Union[KeyError, Any]:
        if key not in self.registers or key not in self.accessors:
            return KeyError("Register does not exist", self, key, context, content)
        return self.registers[key](content) if self.mutators[key][context] else None

    def update(self, key: str, value: Generic, context: Generic) -> Union[KeyError, NoReturn]:
        if key not in self.registers or key not in self.mutators:
            return KeyError("Register does not exist", self, key, value, context)
        if self.mutators[key](context):
            self.registers[key] = value

    def delete(self, key: str, context: Generic) -> Union[KeyError, PermissionError, NoReturn]:
        if key not in self.registers or key not in self.accessors or key not in self.mutators or \
                key not in self.immutables:
            return PermissionError("Register cannot be removed", self, key, context)
        if self.immutables[key] and self.mutators[key](context):
            return PermissionError("Register cannot be deleted", self, key, context)
        del self.registers[key]
        del self.accessors[key]
        del self.mutators[key]
        del self.immutables[key]

    def add(self, key: str, accessor: Callable[Generic, bool], mutator: Callable[Generic, bool], immutability: bool,
            value: Any) -> Union[KeyError, NoReturn]:
        if key in self.registers or key in self.accessors or key in self.mutators or key in self.immutables:
            return KeyError("Register already exists", self, key, accessor, mutator, immutability)
        self.registers[key] = value
        self.accessors[key] = accessor
        self.mutators[key] = mutator
        self.immutables[key] = immutability

    def modify_mutator(self, key: str, value: Callable[Generic, bool]) -> Union[KeyError, PermissionError, NoReturn]:
        if key not in self.registers or key not in self.mutators or key not in self.immutables:
            return KeyError("Register does not exist")
        if self.immutables[key]:
            return PermissionError("Register is immutable cannot modify mutators")
        else:
            self.mutators[key] = value

    def modify_accessor(self, key: str, value: Callable[Generic, bool]) -> Union[KeyError, PermissionError, NoReturn]:
        if key not in self.registers or key not in self.accessors or key not in self.immutables:
            return KeyError("Register does not exist")
        if self.immutables[key]:
            return PermissionError("Register is immutable cannot modify accessor", self, key, value)
        else:
            self.accessors[key] = value

    def push_message(self, message: Message) -> NoReturn:
        self.message_prioritizer.push(self.messages, message)

    def get_next_message(self) -> Union[Message, None]:
        return self.message_prioritizer.pop(self.messages)

    def execute_message_contents(self, message: Message) -> Union[KeyError, PermissionError, Generic]:
        if message.func not in self.exec_list:
            return KeyError("Function not available")
        # Use inspection to get argnames
        func: Callable = self.exec_list[message.func]
        arg_names: List[str] = inspect.signature(func).parameters.keys()
        # Construct dict with argnames for kwargs throw error if fail
        arg_map: Dict[str, Any] = dict()
        for arg_name in arg_names:
            arg: Any = getattr(message, arg_name, None)
            if not arg:
                raise SyntaxError("Failure to match arguments properly",
                                  arg_name,
                                  message,
                                  self)
            else:
                arg_map[arg_name]: Any = arg
        return func(**arg_map)

    def modify_connection_criteria(self, criteria: Callable[str, Generic, bool]) -> Union[PermissionError, NoReturn]:
        if not self.is_connection_criteria_mutable:
            return PermissionError("Criteria is immutable and cannot be modified", self, criteria)
        self.connection_criteria = criteria

    def modify_disconnection_criteria(self, criteria: Callable[str, Generic, bool]) -> Union[PermissionError, NoReturn]:
        if not self.is_disconnection_criteria_mutable:
            return PermissionError("Criteria is immutable and cannot be modified", self, criteria)
        self.disconnection_criteria = criteria

    def connect_entity(self, entity: str, context: Generic) -> Union[KeyError, PermissionError, NoReturn]:
        if not self.connection_criteria(entity, context):
            return PermissionError("Criteria is not sastisfied", self, entity, context)
        if str not in self.entities.keys:
            return KeyError("Entity does not exist", self, entity, context)
        self.connected_entities.append(entity)

    def disconnect_entity(self, entity: str, context: Generic) -> Union[KeyError, PermissionError, NoReturn]:
        if not self.disconnection_criteria(entity, context):
            return PermissionError("Criteria is not sastisfied", self, entity, context)
        if str not in self.entities.keys:
            return KeyError("Entity does not exist", self, entity, context)
        if str not in self.connected_entities:
            return KeyError("Entity is not connected", self, entity, context)
        self.connected_entities.remove(entity)

    def message_entity(self, entity: str, message: Message) -> Union[ConnectionError, NoReturn]:
        if entity not in self.entities.keys:
            return ConnectionError("Entity does not exist", self, entity, message)
        elif entity not in self.connected_entities:
            return ConnectionError("Entity is not connected", self, entity, message)
        else:
            self.entities[entity].push_message(message)

