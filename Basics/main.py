def f(x):
    if x == 1:
        return 1
    else:
        return x * f(x - 1)


result = f(4)
print(result)


#######################
def multiply_times(n):

    def multiplier(x):
        return x * n

    return multiplier


times3 = multiply_times(3)
times5 = multiply_times(5)

# print(times3(9))
# print(times5(3))
# print(times5(times3(2)))
