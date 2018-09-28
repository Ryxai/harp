from typing import *
import heapqueue


class Message:
    def __init__(self, key: str, contents: Any):
        self.key = key
        self.contents = contents


class Component:
    def __init__(self, message_key_func: Callable[[str, Generic], bool]):
        self.registers: Dict[str, Any] = dict()
        self.accessors: Dict[str, Callable[Generic, bool]] = dict()
        self.mutators: Dict[str, Callable[Generic, bool]] = dict()
        self.immutables: Dict[str, bool] = dict()
        self.messages: List[Generic] = []
        self.messageKeyFunc: Callable[[str, Any], bool] = message_key_func

    def get(self, key: str, context: Generic) -> Union[KeyError, Generic, None]:
        if key not in self.registers or key not in self.accessors:
            return KeyError("Register does not exist")
        return self.registers[key] if self.mutators[key](context) else None

    def eval(self, key: str, context, Generic, content: Generic) -> Union[KeyError, Any]:
        if key not in self.registers or key not in self.accessors:
            return KeyError("Register does not exist")
        return self.registers[key](content) if self.mutators[key][context] else None

    def update(self, key: str, value: Generic, context: Generic) -> Union[KeyError, NoReturn]:
        if key not in self.registers or key not in self.mutators:
            return KeyError("Register does not exist")
        if self.mutators[key](context):
            self.registers[key] = value

    def delete(self, key: str, context: Generic) -> Union[KeyError, PermissionError, NoReturn]:
        if key not in self.registers or key not in self.accessors or key not in self.mutators or key not in self.immutables:
            return PermissionError("Register cannot be removed")
        if self.immutables[key] and self.mutators[key](context):
            return PermissionError("Register cannot be deleted")
        del self.registers[key]
        del self.accessors[key]
        del self.mutators[key]
        del self.immutables[key]

    def add(self, key: str, accessor: Callable[[Generic], bool], mutator: Callable[[Generic], bool], immutability,
            value: Any) -> Union[KeyError, NoReturn]:
        if key in self.registers or key in self.accessors or key in self.mutators or key in self.immutables:
            return KeyError("Register already exists")
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
            return PermissionError("Register is immutable cannot modify accessor")
        else:
            self.accessors[key] = value

    def push_message(self, message: Message) -> NoReturn:
        heapqueue.heappush(self.messages, message, )
