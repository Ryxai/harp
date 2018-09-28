from typing import *
from math import floor


class HeapQueue:
    """
    Derived from Skeina's heapqueue implementation provides a heapq like interface with the a key function
    (and type annotations!), does not require mappings to reorder a priority queue. Note that implicitly this is a
    minheap and can be turned into a max heap queue with the use of the multiplicative inverse.
    """

    def __init__(self, key: Callable[Any, int] = None):
        """
        Initializes the heapqueue class, can use the default heapqueue sorting method or provide a key function

        :param key:
        """
        if not key:
            self.__key__ = lambda x: x
        else:
            self.__key__ = key

    @staticmethod
    def __parent__(index: int) -> int:
        """
        Returns the index of the parent element of the priority queue. If the current element is the root returns -1
        :param index: The index of the element in the binary heap to get the parent of
        :return: The index of the parent element or -1 if the index is already the root
        """
        if index < 1:
            return -1
        else:
            return int(floor(index / 2))

    @staticmethod
    def __young_child__(index: int) -> int:
        """
        Gets the left-most child of the current node at the given index
        :param index:  An integer representing the index of the current node in the heap
        :return: An integer representing the index of the left-most child node
        """
        return 2 * index

    @staticmethod
    def __swap__(heap: List[Any], first_index: int, second_index: int) -> List[Any]:
        """
        Trades the values of the nodes
        :param heap: A heap implemented as a List of a given type
        :param first_index: The index of the first element to be swapped
        :param second_index:The index of the second element to be swapped
        :return: The heap with the elements at first_index and second_index swapped
        """
        temp = heap[first_index]
        heap[first_index] = heap[second_index]
        heap[second_index] = temp
        return heap

    def __bubble_down__(self, heap: List[Any], index: int) -> List[Any]:
        """
        Swaps and transfers values down the heap maintaining the minheap invariant
        :param heap: The heap
        :param index: The index of the current element to perform a bubble_down on, can be called from
        within a __bubble_down__ call
        :return The heap with the target value having been bubbled down the heap
        """
        child_index = self.__young_child__(index)
        min_index = index
        i = 0
        while i <= 1:
            if child_index + i <= len(heap) and self.__key__(heap[min_index]) > self.__key__(heap[child_index + i]):
                min_index = child_index + i
            i = i + 1
        if min_index != index:
            heap = self.__swap__(heap, index, min_index)
            heap = self.__bubble_down__(heap, min_index)
        return heap

    def __bubble_up__(self, heap: List[Any], index: int) -> List[Any]:
        """
        Bubbles a value up the heap as per the minheap invariant
        :param heap: The heap
        :param index: The index of the current value to bubble up
        :return:
        """
        if self.__parent__(index) == -1:
            return heap
        parent_index = self.__parent__(index)
        if self.__key__(heap[parent_index]) > self.__key__(heap[index]):
            heap = self.__swap__(heap, index, parent_index)
            return self.__bubble_up__(heap, parent_index)

    def pop(self, heap: List[Any]) -> Union[IndexError, [Any, List[Any]]]:
        """
        Removes the top element from the heap and then replaces it with the next minimal element while maintaining the
        heap invariant.
        :param heap: The heap to retrieve an element from
        :return:A tuple containing the removed element and the remaining heap
        """
        if len(heap) == 0:
            raise IndexError("Heap length cannot be zero.")
        ret = heap[0]
        heap = heap[1:]
        return ret, self.__bubble_down__(heap, 1)

    def push(self, heap: List[Any], item: Any) -> List[Any]:
        """
        Pushes a new value onto the heap and then correctly locates it according to the invariant
        :param heap: The heap to push an element to
        :param item:  The item to push into the heap
        :return: The heap with the item inserted into a correction according to the invariant
        """
        heap.append(item)
        return self.__bubble_up__(heap, len(heap) - 1)

    @staticmethod
    def peek(heap: List[Any]) -> Any:
        return heap[0]

    def pushpop(self, heap: List[Any], item: Any) -> Union[IndexError, [Any, List[Any]]]:
        """
        Pushes a new item onto the heap and then retrieves the minimal item from the heap. Is faster then a separate
        push & pop.
        :param heap: The heap from which to obtain a min item and to push one too
        :param item: The item to push onto the heap
        :return: A tuple containing the popped item and the updated heap
        """
        if self.__key__(heap[0]) > self.__key__(item):
            return item, heap
        else:
            item, heap[0] = heap[0], item
            return item, self.__bubble_up__(heap, 0)

    def heapreplace(self, heap: List[Any], item: Any) -> Union[IndexError, [Any, List[Any]]]:
        """
        Pops an item from the heap and then pushes a new item to it. Is faster then a pop & push.
        :param heap: THe heap tp pop and item from and then push one to
        :param item:The item to push to the heap
        :return: A tuple containing the popped item and the updated heap
        """
        ret = heap[0]
        heap[0] = item
        return ret, self.__bubble_down__(heap, 0)

    def heapify(self, heap: List[Any]) -> List[Any]:
        """
        Transforms a list into a heap, in O(len(x)) time
        :param heap: The input list of items to be transformed into a heap
        :return: The list transformed into a heap
        """
        for i in range(0, len(heap) - 1):
            heap = self.__bubble_down__(heap, i)
        return heap
