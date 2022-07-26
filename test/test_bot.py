from isi_darma.bots import BasicBot

bot = BasicBot(test=True, db = "/Users/darpanjain/Data/USC/RA - ISI/isi_darma/src/isi_darma/data/optout/optout_db.json")
dialogue = ["Hello", "I hate you", "You're such a jerk", "I will beat you up!", "Hey asshole!", "opt-out please"]

for diag in dialogue:
	print(f'*** Final Response to "{diag}" from the bot --> {bot.moderate(dialogue_str=diag)}\n')
