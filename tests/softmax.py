import numpy as np


def softmax_with_temperature(x, temperature=1.0):
    """
    带温度参数的softmax函数

    参数:
    x -- 输入向量或矩阵(numpy数组)
    temperature -- 温度参数(正数，默认为1.0)

    返回:
    s -- softmax计算结果(与x形状相同)

    异常:
    ValueError -- 如果温度<=0
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive")

    # 防止数值溢出，减去最大值
    x = x / temperature
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0, keepdims=True)


# 示例使用
if __name__ == "__main__":
    # 示例1: 不同温度下的结果比较
    scores = np.array([-1.0, 0, 1.0])

    print("高温(tau=2.0):", softmax_with_temperature(scores, temperature=2.0))
    print("标准(tau=1.0):", softmax_with_temperature(scores, temperature=1.0))
    print("低温(tau=0.5):", softmax_with_temperature(scores, temperature=0.5))

    # 示例2: 矩阵输入
    scores_matrix = np.array([[1, 2, 3],
                              [4, 5, 6]])
    print("\n矩阵输入(tau=0.5):")
    print(softmax_with_temperature(scores_matrix, temperature=0.5))

    # 示例3: 错误温度参数
    try:
        print(softmax_with_temperature(scores, temperature=0))
    except ValueError as e:
        print("\n错误捕获:", e)
