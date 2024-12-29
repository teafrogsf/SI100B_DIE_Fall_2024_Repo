

class MyNumberIter:
    def __init__(self) -> None:
        pass

    def __iter__(self): # iterator
        for prime in [2,3,5,7,11,13,17,19]:
            print(f"yield {prime}")
            yield prime
            print(f"recover from prime {prime}")


IterClass = iter(MyNumberIter())

for i in IterClass:
    print(f"get number {i}------------")

A = iter(range(100))
while True:
    try:
        i = next(A)
    except StopIteration:
        break
    print(i)
