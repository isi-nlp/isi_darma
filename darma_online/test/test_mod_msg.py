from darma_online.bots import BasicBot
from darma_online.utils import build_logger, load_reddit_client

sub_name = "darma_test"

logger = build_logger(sub_name, test=True)
reddit_client = load_reddit_client(logger)

bot = BasicBot(reddit_client=reddit_client,
               sub_name=sub_name,
               sub_obj = reddit_client.subreddit(sub_name),
               lang="english",
               mod_assist=True,
               logger=logger)

# bot.msg_mods("test-toxic-user", "100", "text_tox", "no-one", "Hey, no being toxic here.", "Being so toxic!", "123abc")
bot.msg_mods("test-toxic-user", "100", "text_tox", "no-one", "Hey, no being toxic here.", "You're a real shit!!!", "123abc")
print('Test complete. Check your inbox and logs.')