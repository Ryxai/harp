import inspect
from datetime import datetime
from heapqueue import *


class Message:
    """
    A message passed between two components

    :param: source, A Component, from which the message was sent
    :param func: A string, the api function of the target to be run
    component is required
    :param func_context: A Generic, the api function call context
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
    :param entity: An optional string, representing a named component in the
    construct wide index
    """

    def __init__(self,
                 source: 'Component',
                 func: str,
                 func_context: Generic,
                 metadata: Dict[str, Generic],
                 key: Union[str, None] = None,
                 value: Union[Generic, Callable[Generic, bool]] = None,
                 accessor: Union[Callable[Generic, bool], None] = None,
                 mutator: Union[Callable[Generic, bool], None] = None,
                 context: Union[Generic, None] = None,
                 criteria: Union[Callable[str, Generic, bool], None] = None,
                 entity: Union[str, None] = None):
        if metadata is None:
            metadata = {"timestamp": datetime.now()}
        self.source = source
        self.func = func
        self.func_context = func_context
        self.metadata = metadata
        self.key = key
        self.value = value
        self.accessor = accessor
        self.mutator = mutator
        self.context = context
        self.criteria = criteria
        self.entity = entity


class BlockedComponentError(Exception):
    """
    Error indicating that a component is blocked (i.e. its message queue is
    emtpty)
    """

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class Component:
    """
    A representation of a computational unit of some variety. Designed to be sub
    -classed.

    :param message_key_func: A Callable(Generic) -> int, a key function used for
    message priority
    :param connection_criteria: A Callable(str, Generic) -> bool, represents
    the criteria requirements for connecting another entity to the
     current entity (unidirectionally)
    :param disconnection_criteria: A Callable(str, Generic) -> bool, represents
    the criteria requirements for disconnecting another entity from the current
    entity(unidirectionally)
    :param is_connection_criteria_mutable: A boolean, can the
    connection_criteria be updated later
    :param is_disconnection)criteria_mutable: A boolean, can the
    disconnection_criteria_mutable can be updated later
    :param api_accessibility: A dictionary of string -> Callable[Generic, bool],
    represents availability of certain api functions
    :param api_mutable: A Callable[Generic, bool], representing if the api
    availabilty can be modified
    """

    entities: Dict[str, 'Component'] = dict()

    def __init__(self,
                 message_key_func: Callable[Generic, int],
                 connection_criteria: Callable[str, Generic, bool] =
                 lambda s, context: True,
                 disconnection_criteria: Callable[str, Generic, bool] =
                 lambda s, context: True,
                 is_connection_criteria_mutable: bool = True,
                 is_disconnection_criteria_mutable: bool = True,
                 api_accessibility: Dict[str, Callable[Generic, bool]] = None,
                 api_mutable: Callable[Generic, bool] = lambda context: False
                 ):
        if api_accessibility is None:
            api_accessibility = dict()
        self.registers: Dict[str, Any] = dict()
        self.accessors: Dict[str, Callable[Generic, bool]] = dict()
        self.mutators: Dict[str, Callable[Generic, bool]] = dict()
        self.immutables: Dict[str, bool] = dict()
        self.messages: List[Generic] = []
        self.message_prioritizer: HeapQueue = HeapQueue(message_key_func)
        self.exec_list: Dict[str, Callable] = {func_name: bound_method for
                                               func_name, bound_method in
                                               inspect.getmembers(self,
                                                              inspect.ismethod)}
        self.connection_criteria = connection_criteria
        self.disconnection_criteria = disconnection_criteria
        self.connected_entities: List[str] = []
        self.is_connection_criteria_mutable = is_connection_criteria_mutable
        self.is_disconnection_criteria_mutable = \
            is_disconnection_criteria_mutable
        self.entities[self.__name__] = self
        self.api_mutable = api_mutable
        if not api_accessibility:
            # Default all values are true
            self.api_permissions = {key: (lambda context: True) for
                                    key in
                                    self.exec_list.keys()}
        elif api_accessibility.keys() != self.exec_list.keys():
            # Get keys where we have values set other values to True
            self.api_permissions = {func: (api_accessibility[func]
                                           if func in api_accessibility.keys()
                                           else True)
                                    for func in self.exec_list.keys()}
        else:
            # If user covers all inputs set permissions
            self.api_permissions = api_accessibility

    def get(self, key: str, context: Generic) -> \
            Union[KeyError, PermissionError, Generic]:
        """
        Gets the contents of a register, will return (not raise an error) if
        it fails. This
        :param key: A string, the register index/label
        :param context: A generic, used to confirm that the register is
        accessible
        :return: Either a KeyError, PermissionError, or Generic depending on the
         stored value. Returns a key error if the key does not exist in the
         registers or accessors. It will return a PermissionError if the
         register cannot be access due to failed permission granted by the
         accessor modifier. Otherwise will return the contents of the register.
        """
        if key not in self.registers or key not in self.accessors:
            return KeyError("Register does not exist", self, key, context)
        return self.registers[key] if self.accessors[key](context) \
            else PermissionError("Cannot access register")

    def eval(self, key: str, context: Generic, content: Generic) -> \
            Union[KeyError, TypeError, PermissionError, Any]:
        """
        If the contents of a register is a Callable, will execute the register
        and return its contents. Otherwise will return an error (not raise).
        :param key: A string, the register index/label.
        :param context: A generic, used to confirm that the register is
        accessible.
        :param content: A generic, parameters to the evaluated function (usually
        stored as a dict [kwargs] if multiple params).
        :return: Will return a KeyError if the register does not exist. Will
        return a TypeError if the register is not callable. Will return a
        PermissionError if the register is not accessible by the accessor.
        Otherwise returns the result of the function.
        """
        if key not in self.registers or key not in self.accessors:
            return KeyError("Register does not exist",
                            self,
                            key,
                            context,
                            content)
        elif callable(self.registers[key]):
            return TypeError("Cannot call uncallable register",
                             self,
                             key,
                             context,
                             content)
        elif not self.accessors[key](context):
            return PermissionError("Cannot access register",
                                   self,
                                   key,
                                   context,
                                   content)
        else:
            return self.registers[key](content)

    def update(self, key: str, value: Generic, context: Generic) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Changes the value stored in a register, assuming the register is
        accessible. Otherwise will return a KeyError or PermissionError.
        :param key: A string, the register label/index
        :param value: A Generic, the value for the register to be updated to
        :param context: A Generic, used to evaluate whether the register is
        mutable
        :return: Will return a KeyError if the register does not exist. Will
        return a PermissionError is the register is not mutable. Otherwise does
        not return anything.
        """
        if key not in self.registers or key not in self.mutators:
            return KeyError("Register does not exist",
                            self,
                            key,
                            value,
                            context)
        elif not self.mutators[key](context):
            return PermissionError("Cannot update register contents",
                                   self,
                                   key,
                                   value,
                                   context)
        else:
            self.registers[key] = value

    def delete(self, key: str, context: Generic) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Deletes/removes a register. Will return a KeyError or PermissionError
        otherwise.
        :param key: A string, the register label/index
        :param context: A generic, used to evaluate whether the register can be
        deleted or not.
        :return: Will return a KeyError if the key does not exist. Will return
        a PermissionError if the register cannot be deleted. Otherwise does not
        return anything.
        """
        if key not in self.registers or key not in self.accessors or \
                key not in self.mutators or \
                key not in self.immutables:
            return KeyError("Register cannot be removed",
                            self,
                            key,
                            context)
        if self.immutables[key] and self.mutators[key](context):
            return PermissionError("Register cannot be deleted",
                                   self,
                                   key,
                                   context)
        del self.registers[key]
        del self.accessors[key]
        del self.mutators[key]
        del self.immutables[key]

    def add(self,
            key: str,
            accessor: Callable[Generic, bool],
            mutator: Callable[Generic, bool],
            immutability: bool,
            value: Any) -> Union[KeyError, NoReturn]:
        """
        Adds the register with default contents along with the given permissions
        and values. Returns errors if the add fails.
        :param key: A string, the register label/identifier
        :param accessor: A Callable[Generic, bool], evaluates whether the
        register can be accessed under the current context.
        :param mutator: A Callable[Generic, bool], evaluates whether the
        register can be modified under the current context.
        :param immutability: A boolean, can the accessor/mutator be modified in
        the future
        :param value: A generic, the initial value contained within the register
        :return: Will return a KeyError if the key exists in any context.
        Otherwise will not return anything.
        """
        if key in self.registers or \
                key in self.accessors or \
                key in self.mutators or \
                key in self.immutables:
            return KeyError("Register already exists",
                            self,
                            key,
                            accessor,
                            mutator,
                            immutability)
        self.registers[key] = value
        self.accessors[key] = accessor
        self.mutators[key] = mutator
        self.immutables[key] = immutability

    def modify_mutator(self, key: str, value: Callable[Generic, bool]) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Modifies the mutator permission if the modification is allowed. It will
        return a KeyError or PermissionError on failure.
        :param key: A string, the register index/label
        :param value: A Callable[Generic, bool], the updated mutator permission
        function.
        :return: Will return a KeyError if the label/identifier does not exist.
        If the register mutator is immutable, it will return a PermissionError.
        if the mutator is successfully updated, there is no return value.
        """
        if key not in self.registers or \
                key not in self.mutators or \
                key not in self.immutables:
            return KeyError("Register does not exist")
        if self.immutables[key]:
            return PermissionError("Register is immutable cannot modify "
                                   "mutators")
        else:
            self.mutators[key] = value

    def modify_accessor(self, key: str, value: Callable[Generic, bool]) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Modifies the accessor permission if the modification is allowed. It will
        return a KeyError or PermissionError on failure.
        :param key: A string, the register label/index
        :param value: A Callable[Generic, bool], the updated accessor permission
        function.
        :return: Will return a KeyError if the label/identifier does not exist.
        If the register accessor is immutable, it will return a PermissionError.
        Otherwise it will return nothing.
        """
        if key not in self.registers or \
                key not in self.accessors or \
                key not in self.immutables:
            return KeyError("Register does not exist")
        if self.immutables[key]:
            return PermissionError("Register is immutable cannot modify "
                                   "accessor",
                                   self,
                                   key,
                                   value)
        else:
            self.accessors[key] = value

    def push_message(self, message: Message) -> NoReturn:
        """
        Add a message to the message queue for the entity.
        :param message: A message, to be added to the message queue.
        :return: There is no return value
        """
        self.message_prioritizer.push(self.messages, message)

    def get_next_message(self) -> Union[Message, None]:
        """
        Gets the current message from the top of the heapqueue of messages.
        :return: Returns the next message if there is one, otherwise returns
        None.
        """
        return self.message_prioritizer.pop(self.messages)

    def execute_message_contents(self, message: Message) -> \
            Union[KeyError, PermissionError, SyntaxError, Generic]:
        """
        Given a message, executes thr requested function with the given function
        body. Depending on the nature of the failure (if there is any) can
        return a KeyError, PermissionError, or SyntaxError.

        :param message: A message, whose contents contain the function to be
        executed.
        :return: If message.func is not in the API list, it will return a
        KeyError. If the API call is unavailable, it will return a
        PermissionError. If the function parameters are incorrect and cannot be
        matched then it will throw a SyntaxError. Otherwise it will return
        the result of the function call.
        """
        if message.func not in self.exec_list:
            return KeyError("Function not available", self, message)
        elif not self.api_permissions[message.func](message.func_context):
            return PermissionError("Function not executable", self, message)
        # Use inspection to get argnames
        func: Callable = self.exec_list[message.func]
        arg_names: List[str] = inspect.signature(func).parameters.keys()
        # Construct dict with argnames for kwargs throw error if fail
        arg_map: Dict[str, Any] = dict()
        for arg_name in arg_names:
            arg: Any = getattr(message, arg_name, None)
            if not arg:
                return SyntaxError("Failure to match arguments properly",
                                   self,
                                   arg_name,
                                   message)
            else:
                arg_map[arg_name]: Any = arg
        return func(**arg_map)

    def modify_connection_criteria(self,
                                   criteria: Callable[str, Generic, bool]) -> \
            Union[PermissionError, NoReturn]:
        """
        Modifies the connection criteria if connection critera is not immutable.
        :param criteria: A Callable[str, Generic, bool], returns a boolean if a
        connection is allowed
        :return: Will return a PermissionError if the criteria is immutable and
        cannot be changed. If the criteria is changed then there is no return
        value.
        """
        if not self.is_connection_criteria_mutable:
            return PermissionError("Criteria is immutable and cannot be "
                                   "modified", self, criteria)
        self.connection_criteria = criteria

    def modify_disconnection_criteria(self,
                                      criteria: Callable[str, Generic, bool]) -> \
            Union[PermissionError, NoReturn]:
        """
        Modifies the disconnection criteria if the disconnection criteria is not
        immutable.
        :param criteria: A Callable[str, Generic, bool], returns a boolean if a
        disconnection is allowed
        :return:Will return a PermissionError if the criteria is immutable and
        cannot be changed. If the criteria is changed there is no return value.
        """
        if not self.is_disconnection_criteria_mutable:
            return PermissionError("Criteria is immutable and cannot be "
                                   "modified",
                                   self,
                                   criteria)
        self.disconnection_criteria = criteria

    def connect_entity(self, entity: str, context: Generic) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Connects the prescribed entity. If the connection is not allowed or not
        possible then a PermissionError or KeyError is thrown respectively.
        :param entity: A string, the label/index of the entity to connect to
        :param context: A Generic, used to evaluate whether the entity can
        be connected or not.
        :return: Will return a PermissionError if the connection is not
        permitted. Will return a KeyError if the entity label is not found.
        Otherwise the entity is added to the connected entities and no return
        value is returned.
        """
        if not self.connection_criteria(entity, context):
            return PermissionError("Criteria is not satisfied",
                                   self,
                                   entity,
                                   context)
        if str not in self.entities.keys:
            return KeyError("Entity does not exist", self, entity, context)
        self.connected_entities.append(entity)

    def disconnect_entity(self, entity: str, context: Generic) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Disconnects a prescribed entity should it be present in the connected
        entities. Otherwise will return a KeyError or PermissionError if the
        entity is not connected, does not exist or cannot be disconnected.
        :param entity: A string, the the label/index of the entity to be
        disconnected
        :param context A generic, used to  evaluate whether the enitty can
        be disconnected or not.
        :return: Will return a KeyError if the entity label is not found or
        is not connected. Will return a PermissionError if the entity cannot
        be disconnected. Otherwise the entity is disconnected and None is
        returned.
        """
        if not self.disconnection_criteria(entity, context):
            return PermissionError("Criteria is not satisfied",
                                   self,
                                   entity,
                                   context)
        if str not in self.entities.keys:
            return KeyError("Entity does not exist", self, entity, context)
        if str not in self.connected_entities:
            return KeyError("Entity is not connected", self, entity, context)
        self.connected_entities.remove(entity)

    def message_entity(self, entity: str, message: Message) -> \
            Union[ConnectionError, NoReturn]:
        """
        If a entity is connected to the current entity a message is pushed to
        its message queue.
        :param entity: A string, the label/identifier for the given entity
        :param message: A Message, to be pushed to the specified entity.
        :return: Will return a ConnectionError if the targeted entity does not
        exist or is not connected. Otherwise will return None and the Message is
        pushed to the connected entity.
        """
        if entity not in self.entities.keys:
            return ConnectionError("Entity does not exist",
                                   self,
                                   entity,
                                   message)
        elif entity not in self.connected_entities:
            return ConnectionError("Entity is not connected",
                                   self,
                                   entity,
                                   message)
        else:
            self.entities[entity].push_message(message)

    def modify_api_permission(self,
                              key: str,
                              value: Callable[Generic, bool],
                              context: Generic) -> \
            Union[KeyError, PermissionError, NoReturn]:
        """
        Modify API function by updating it with a new evaluation function. Will
        return a KeyError or PermissionError if the API cannot be modified.
        :param key: A string, the name of api function to modify
        :param value: A Callable[Generic, bool], will update the current API
        access function.
        :param context: A Generic, used to evaluate if the API accessor can be
        updated.
        :return: Will return a KeyError if the API function name does not exist.
        Otherwise if the API function cannot be modified will return a
        PermissionError. If no restrictions are in place, the API accessor
        will be modified and updated with a return value of None.
        """
        if key not in self.api_permissions:
            return KeyError("Api function is not available",
                            self,
                            key,
                            value,
                            context)
        elif not self.api_mutable(context):
            return PermissionError("Api accessibility cannot be modified with "
                                   "this context",
                                   self,
                                   key,
                                   value,
                                   context)
        else:
            self.api_permissions[key] = value

    def run(self) -> \
            Union[KeyError,
                  SyntaxError,
                  PermissionError,
                  BlockedComponentError,
                  Generic,
                  NoReturn]:
        """
        Retrieves a message from the components message queue and processes it,
        if the message queue is empty indicates the component is blocked waiting
        for new messages.
        :return: Return a BlockedComponentMessage if the queue of the component
        is empty. Othwise will return the result of the processed message.
        """
        message = self.get_next_message()
        if not Message:
            return BlockedComponentError("Component queue is empty", self)
        else:
            return self.execute_message_contents(message)
