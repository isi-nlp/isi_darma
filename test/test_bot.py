from isi_darma.bots import BasicBot

bot = BasicBot(test=True)
dialogue = ["Hello", "I hate you", "You're such a jerk", "I will beat you up!"]

for diag in dialogue:
	print(f'*** Final Response to "{diag}" from the bot --> ', bot.moderate(dialogue_str=dialogue))
