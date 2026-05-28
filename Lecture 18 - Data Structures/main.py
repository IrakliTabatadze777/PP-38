################################################################################
# Linked Lists
################################################################################


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

    def __repr__(self):
        return f'Node({self.data})'



class SinglyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def append(self, data):
        new_node = Node(data)

        if self.is_empty():
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

        self._size += 1


    def __repr__(self):
        nodes = []
        current = self.head
        while current:
            nodes.append(str(current.data))
            current = current.next

        return ' -> '.join(nodes)



# head              tail
# Node(10)   ->    Node(20)

node1 = Node(1)
node2 = Node(2)
node3 = Node(3)


linked_list = SinglyLinkedList()

linked_list.append(node1)
linked_list.append(node3)
linked_list.append(node2)

print(linked_list)
print(len(linked_list))

# node1.next = node2
# node2.next = node3


# Node(1) -> Node(2) -> Node(3)



################################################################################
# Stack LIFO(Last In First Out)
################################################################################


lst = []


lst.append(10)
lst.append(20)
lst.append(30)

print(lst.pop())

while True:
    try:
        print(lst.pop())
    except IndexError:
        break

print(lst[-1])




################################################################################
# Queue FIFO(First In First Out)
################################################################################

from queue import Queue

q = Queue(maxsize=3)

q.put(10)
q.put(20)
q.put(30)
q.put_nowait(40)

print(q.empty())
print(q.full())

print(q.get())
print(q.get())
print(q.get())
print(q.get_nowait())




################################################################################
# deque - Double-Ended Queue
################################################################################
# [1, 2, 3, 4 , 5]

from collections import deque

q = deque()

# [4, 1, 2, 3]
q.append(1)
q.append(2)
q.append(3)

q.appendleft(4)
print(q.popleft())


