
import time
from datetime import datetime

# start = time.time()
start = datetime.now()

a = list(range(10))
b = list(range(10))
result = [a[i] + b[i] for i in range(len(a))]
print(result)
# print(time.time() - start)
print(datetime.now() - start)


import numpy as np

# start = time.time()
start = datetime.now()
a = np.arange(10)
b = np.arange(10)
result = a + b
print(result)

# 1 1 1 1 1 1 1 1  - int8
# 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1  - int16
a = np.array([[1,2,3], [4,5,6], [7,8,9]], dtype=np.int8)
mask = a % 2 != 0

print(a)
print(mask)
a[mask] = -1
print(a)

print(a)
print(a.strides)
# [1, 2, 3]
# [4, 5, 6]
# [7, 8, 9]

# print(time.time() - start)
# print(datetime.now() - start)


arr = np.zeros((3,4))
print(arr)


arr = np.ones((2, 2, 2))
print(arr)