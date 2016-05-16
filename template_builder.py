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

import os
import shlex
import sys

import utils


class TemplateBuilder:
    def __init__(self, filename):
        self.logger = utils.get_logger(__name__)
        self.template = ''
        self.preprocess(filename)

    def preprocess(self, filename):
        self.logger.info(utils.separator)
        self.logger.info("Запускаю обработку шаблона...")
        if not os.path.exists(filename):
            self.logger.error("Файл шаблона не найден: {0}".format(filename))
            sys.exit(1)
        with open(filename) as file:
            for line in file.readlines():
                line = line.strip()
                if line.startswith(';') or not line:
                    continue
                if not line.startswith(':'):
                    self.logger.error("Некорректный синтаксис в шаблоне: {0}".format(line))
                    sys.exit(1)
                split = shlex.split(line)
                command = split[0][1:]
                if command not in ['include', 'block', 'warning', 'info']:
                    self.logger.error("Некорректный синтаксис в шаблоне: {0}".format(line))
                    sys.exit(1)
                if command == 'include':
                    self.include(split[1])
                if command == 'block':
                    self.template += '{' + split[1] + '}'
                    self.template += '\n'
                if command == 'info':
                    self.logger.info('{0}: {1}'.format(filename, split[1]))
                if command == 'warning':
                    self.logger.warning('{0}: {1}'.format(filename, split[1]))
        self.template += '\n'

    def include(self, part):
        self.logger.info("Выполняю импорт {0}...".format(part))
        filename = '{0}.part'.format(part)
        if not os.path.exists(filename):
            self.logger.error("Файл для импорта не найден: {0}".format(filename))
            sys.exit(1)
        with open(filename) as file:
            self.template += file.read()
