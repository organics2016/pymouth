from dtw import dtw

V_A = [[145.02333, 26.781],]
V_T = [[54.447308, -5.225743], [65.70888, -24.43354], [65.70888, -24.43354], [65.70888, -24.43354]]

res = dtw(V_A, V_T, distance_only=True).normalizedDistance
print(res)
