"""

    This file is part of xcos-gen.

    xcos-gen is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    xcos-gen is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with xcos-gen. If not, see <http://www.gnu.org/licenses/>.

    Author: Ilia Novikov <ilia.novikov@live.ru>

"""

from parser import Parser
from template_builder import TemplateBuilder
import utils

logger = utils.get_logger('main')
logger.info("xcos-gen, версия {0}, разработчик {1}".format(
    utils.__version__,
    utils.__author__
))

parser = Parser('./model.zcos', False)
builder = TemplateBuilder('default.template')
builder.build(parser)

with open('output.v', 'w') as file:
    file.write(builder.template)
