from openai import OpenAI
from typing import List, Dict


client = OpenAI(
    base_url='http://10.15.88.73:your_group_number/v1',
    api_key='ollama',  # required but ignored
)

messages : List[Dict] = [
    {"role": "system", "content": "We are going to play a game now, and I have an integer in my mind. You can ask me an integer each time, and I will tell you whether the answer will be larger or smaller than the number asked. You need to use the minimum number of questions to answer what the answer is. For example, when the answer in my mind is 200, you can ask 100 and I will tell you that the answer is greater than 100."}
]

while True:
    user_input = input("User input: ")
    if user_input.lower() in [ "exit", "quit"]:
        print("chat ends.")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama3.2",      
        messages=messages,    # a list of dictionary contains all chat dictionary
    )

    # 提取模型回复
    assistant_reply = response.choices[0].message.content
    print(f"Llama: {assistant_reply}")

    # 将助手回复添加到对话历史
    messages.append({"role": "assistant", "content": assistant_reply})






'''
messages : List[Dict] = [
    {"role": "system", "content": 'You are a helpful teaching assitant of computer science lessons, \
                you should help CS freshman with teaching \
                how to use LLM to design and create games better.'}
]


messages : List[Dict] = [
    {"role": "system", "content": "You are a game player and are playing tic-tac-ton with users.\
Tic-Tac-Toe is a simple two-player game played on a 3x3 grid. Players take turns marking the grid with their respective symbols ('X' or 'O').\
 The objective is to be the first to form a line of three symbols either horizontally, vertically, or diagonally.\
For example, At the start, the grid is empty: \
_ _ _\n\
_ _ _\n\
_ _ _\n\
Player 1 places 'X' in the center:\
_ _ _\n\
_ X _\n\
_ _ _\n"}
]

messages : List[Dict] = [
    {"role": "system", "content": "We are going to play a game now, and I have an integer in my mind. You can ask me an integer each time, and I will tell you whether the answer will be larger or smaller than the number asked. You need to use the minimum number of questions to answer what the answer is. For example, when the answer in my mind is 200, you can ask 100 and I will tell you that the answer is greater than 100."}
]

"We are going to play a game now, and I have a number in my mind. You can ask me a number each time, and I will tell you whether the answer will be larger or smaller than the number asked. You need to use the minimum number of questions to answer what the answer is. For example, when the answer in my mind is 200, you can ask 100 and I will tell you that the answer is greater than 100."


"You are a game player and are playing tic-tac-ton with users. \
Tic-Tac-Toe is a simple two-player game played on a 3x3 grid. Players take turns marking the grid with their respective symbols ("X" or "O"). \
 The objective is to be the first to form a line of three symbols either horizontally, vertically, or diagonally.
For example, At the start, the grid is empty: \
_ _ _\n\
_ _ _\n\
_ _ _\n\
Player 1 places "X" in the center:\
_ _ _\n\
_ X _\n\
_ _ _\n"

'''
