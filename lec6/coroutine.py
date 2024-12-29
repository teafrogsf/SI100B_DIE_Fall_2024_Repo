# Two simple generator functions
from typing import Generator, Set

Homework_list : Set[str] = set()

# Teacher produces homework
def producer(name : str) -> Generator:
    id = 0
    print(f"I am the {name} teacher")
    while True:
        id += 1
        assignment = name + str(id)
        print(f'One more piece of homework {assignment}')
        Homework_list.add(assignment)
        yield 

# Student does homework
def consumer() -> Generator:
    while True:
        x = None
        if len(Homework_list)>0:
            x = Homework_list.pop()
            print(f"finished homework {x}")
        send_parameter = yield x
        print(f"successfully send {send_parameter}")


# Example use
MathTeacher = producer("math")
EnglishTeacher = producer("English")
Student = consumer()

print("Starting coroutine")
next(MathTeacher)
next(EnglishTeacher)

MathTeacher.send(0)
EnglishTeacher.send(998244353)
next(Student)
Student.send(998244353)
Student.send(998244353)
Student.send(998244353)

print(Homework_list)
next(Student)
# for x in Student:
#     if x is not None:
#         print(f"Student has uploaded homework {x}")
# sched = TaskScheduler()
# sched.new_task(countdown(2))
# sched.new_task(countup(5))
# sched.run()