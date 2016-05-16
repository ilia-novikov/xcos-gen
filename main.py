from parser import Parser
import utils

logger = utils.get_logger('main')
logger.info("xcos-gen, версия {0}, разработчик {1}".format(
    utils.__version__,
    utils.__author__
))

parser = Parser('./model.zcos')
parser.finalize()
