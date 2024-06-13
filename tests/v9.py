import numpy as np

# 假设数组为 data
data = np.array([1, 2, 3, 4, 5])

# 计算数组标准差
data_std = np.std(data)

# 标准化标准差
std_normalized = (data_std - (data_std / len(data))) / np.std([np.std(x) for x in [data]])

# 输出标准化后的标准差
print(std_normalized)
