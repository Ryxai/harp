import inspect
from heapqueue import *


class Message:
    def __init__(self,
                 func: str,
                 key: str,
                 value: Union[Generic, Callable[Generic, bool]],
                 accessor: Union[Callable[Generic, bool], None],
                 mutator: Union[Callable[Generic, bool], None],
                 context: Union[Generic, None],
                 contents: Any):
        self.func = func
        self.key = key
        self.value = value
        self.accessor = accessor
        self.mutator = mutator
        self.context = context
        self.contents = contents


class Frame:
    def __init__(self, header: Generic, content: Any):
        self.header = header
        self.content = content


class Component:

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
        self.input_buffer: List[Frame] = []
        self.output_buffer: List[Frame] = []
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

    def modify_connection_criteria(self, value: Callable[str, Generic, bool]) -> Union[PermissionError, NoReturn]:
        if not self.is_connection_criteria_mutable:
            return PermissionError("Criteria is immutable and cannot be modified", self, value)
        self.connection_criteria = value

    def modify_disconnection_criteria(self, value: Callable[str, Generic, bool]) -> Union[PermissionError, NoReturn]:
        if not self.is_disconnection_criteria_mutable:
            return PermissionError("Criteria is immutable and cannot be modified", self, value)
        self.disconnection_criteria = value

    def connect_entity(self, value: str, context: Generic) -> Union[KeyError, PermissionError, NoReturn]:
        if not self.connection_criteria(value, context):
            return PermissionError("Criteria is not sastisfied")
        if str not in self.entities.keys:
            return KeyError("Entity does not exist")
        self.connected_entities.append(value)

    def disconnect_entity(self, value: str, context: Generic) -> Union[KeyError, PermissionError, NoReturn]:
        if not self.disconnection_criteria(value, context):
            return PermissionError("Criteria is not sastisfied")
        if str not in self.entities.keys:
            return KeyError("Entity does not exist")
        if str not in self.connected_entities:
            return KeyError("Entity is not connected")
        self.connected_entities.remove(value)

    def message_entity(self, value: str, message: Message) -> Union[ConnectionError,NoReturn]:
        pass

