# importing these modules will invoke register() calls
import site, os
site.addsitedir(os.path.dirname(__file__))

from .bots import GPTBot
from .transforms import RtgApiTranslator, NLLBApiTranslator

