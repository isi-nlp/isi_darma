from isi_darma.bots import BasicBot

bot = BasicBot(test=True)
dialogue = ["Hello", "I hate you", "You're such a jerk", "I will beat you up!", "Hey asshole!", "opt-out please"]

for diag in dialogue:
	final_response = bot.moderate(dialogue_str=diag)
	print(f'*** Final Response to "{diag}" from the bot -->\n{final_response if final_response else " -> No Response <-"}\n')
