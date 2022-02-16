from isi_darma.bots import BasicBot

bot = BasicBot()
dialogue = ["Hello", "I hate you"]

print(bot.moderate(dialogue_str=dialogue))