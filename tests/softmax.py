import numpy as np


def softmax(x):
    """
    计算softmax函数

    参数:
    x -- 输入向量或矩阵(numpy数组)

    返回:
    s -- softmax计算结果(与x形状相同)
    """
    # 防止数值溢出，减去最大值
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


# 示例使用
if __name__ == "__main__":
    # 示例1: 一维向量
    scores = np.array([1.0, 2.0, 3.0])
    print("一维向量softmax结果:", softmax(scores))

    # 示例2: 二维矩阵(按行计算softmax)
    scores_matrix = np.array([[1, 2, 3, 6],
                              [2, 4, 5, 6],
                              [3, 8, 7, 6]])
    print("\n二维矩阵softmax结果(按行):")
    print(softmax(scores_matrix))

    # 示例3: 数值稳定性测试(大数)
    large_scores = np.array([1000, 2000, 3000])
    print("\n大数输入softmax结果:", softmax(large_scores))