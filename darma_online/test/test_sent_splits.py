from spacy.lang.en import English
from spacy.lang.fr import French

raw_text = 'Hello, world. Here are two sentences.'
french_text = "Ce post a été supprimé. Merci de ne pas mettre le lien en self.post, mais de cliquer sur le bouton 'partager un lien/submit a new link' dans la barrecôté. *I am a bot, and this action was performed automatically. " \
              "Please [contact the moderators of this subreddit](/message/compose/?to=/r/france) if you have any questions or concerns.*"
nlp = English()
nlp.add_pipe('sentencizer') # updated
doc = nlp(raw_text)
sentences = [sent.text.strip() for sent in doc.sents]
print(sentences)

nlp = French()
nlp.add_pipe('sentencizer') # updated
doc = nlp(french_text)
sentences = [sent.text.strip() for sent in doc.sents]
print(sentences)