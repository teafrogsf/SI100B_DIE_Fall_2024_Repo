# from openai import OpenAI
# client = OpenAI(
#     base_url='http://10.15.88.73:5001/v1',
#     api_key='ollama',  # required but ignored
# )

# chat_completion = client.chat.completions.create(
#     messages=[
#         {
#             'role': 'system',
#             'content': '你现在需要扮演游戏里面的NPC需要跟玩家进行回合制对战，在这个游戏中双方每个回合各自使用一次技能攻击对方，率先将对方生命值\
# 降低到小于等于0的一方会获胜，你需要采取最优策略以获取游戏的胜利。当前是你的回合，你现在共有生命值100点，你的对手玩家有生命值50点，\
# 你目前总共只有2个技能可以使用，它们分别是：1. 发起攻击，减少对手50点生命值，2. 回复自己10点生命值并且降低对方10点生命值，请你输出你\
# 这回合需要发动的技能。如果要发动1技能，请输出1。如果要发动2技能请输出2。当你回合结束使用技能后，将会轮到玩家的回合。'
#         },
#         {
#             'role': 'user',
#             'content': "请发动技能。",
#         }
#     ],
#     model='llama3.2',
# )

# print(chat_completion.choices[0].message.content)









# 10.15.88.73:5001 --- 10.15.88.73:5036

from openai import OpenAI
client = OpenAI(
    base_url='http://10.15.88.73:your_group_number/v1',
    api_key='ollama',  # required but ignored
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful teaching assitant of computer science lessons, \
                you should help CS freshman with teaching \
                how to use LLM to design and create games better. '
        },
        {
            'role': 'user',
            'content': "How we can involve LLM into a part of game?",
        }
    ],
    model='llama3.2',
)

print(chat_completion.choices[0].message.content)


'''

messages : List[Dict] = [
    {"role": "system", "content": '你是一个博学多深的助手。'}
    {"role": "user", "content": "食堂一共有23个苹果，如果他们用掉了20个之后又买了7个，那么现在剩下多少苹果？"}
]

chat_completion = client.chat.completions.create(
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful teaching assitant of computer science lessons, \
                you should help CS freshman with teaching \
                how to use LLM to design and create games better.'
        },
        {
            'role': 'user',
            'content': "How we can involve LLM into a part of game?",
        }
    ],
    model='llama3.2',
)

'''