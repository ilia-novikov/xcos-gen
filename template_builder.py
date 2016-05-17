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
import datetime
import os
import shlex
import sys

import utils
from parser import Parser
from safe_dict import SafeDict

CORES_DIR = '/home/ilia/src/sc_cores'


class TemplateBuilder:
    def __init__(self, filename):
        self.logger = utils.get_logger(__name__)
        self.assoc = {}
        self.template = ''
        self.module_params = []
        self.connection_type = {
            'input': 'sigma-delta',
            'output': 'sigma-delta'
        }
        self.creation_date = datetime.datetime.now()
        self.preprocess(filename)
        self.fill_module_info()

    def preprocess(self, filename):
        self.logger.info(utils.separator)
        self.logger.info("Запускаю обработку шаблона...")
        if not os.path.exists(filename):
            self.logger.error("Файл шаблона не найден: {0}".format(filename))
            sys.exit(1)
        with open(filename) as file:
            for line in file.readlines():
                self.parse(line)
        self.template += '\n'

    def parse(self, line):
        line = line.strip()
        if line.startswith(';') or not line:
            return
        if not line.startswith(':'):
            self.logger.error("Некорректный синтаксис в шаблоне: {0}".format(line))
            sys.exit(1)
        split = shlex.split(line)
        commands = {
            'include': lambda: self.include(split[1]),
            'block': lambda: self.create_block(split[1]),
            'info': lambda: self.logger.info(split[1]),
            'warning': lambda: self.logger.warning(split[1]),
            'assoc': lambda: self.create_association(split[1], split[2]),
            'param': lambda: self.create_param(split[1], split[2]),
            'input': lambda: self.set_connection_type(command, split[1]),
            'output': lambda: self.set_connection_type(command, split[1])
        }
        command = split[0][1:]
        if command not in commands:
            self.logger.error("Некорректный синтаксис в шаблоне: {0}".format(line))
            sys.exit(1)
        commands[command]()

    def include(self, part):
        self.logger.info("Выполняю импорт {0}...".format(part))
        filename = '{0}.part'.format(part)
        if not os.path.exists(filename):
            self.logger.error("Файл для импорта не найден: {0}".format(filename))
            sys.exit(1)
        with open(filename) as file:
            self.template += file.read()

    def create_association(self, source, target):
        self.logger.info("Создаю ассоциацию {0} -> {1}".format(source, target))
        filename = '{0}/{1}/hdl/{1}.v'.format(CORES_DIR, target)
        if not filename:
            self.logger.error("Не могу найти модуль HDL: {0}".format(filename))
            sys.exit(1)
        self.assoc[source] = {
            'name': target,
            'path': filename
        }

    def build(self, parser: Parser):
        self.logger.info(utils.separator)
        self.logger.info("Запускаю сборку шаблона...")
        blocks = parser.blocks
        for block in blocks:
            if block.block_type not in self.assoc:
                self.logger.error("Не найдена ассоциация для блока: {0}".format(block.block_type))
                sys.exit(1)

    def create_block(self, name):
        self.template += '{{{0}}}\n'.format(name)

    def create_param(self, name, value):
        self.logger.info("Добавляю параметр '{0}' со значением {1}".format(name, value))
        self.module_params.append({name: int(value)})

    def set_connection_type(self, name, value):
        printable = {
            'input': "вход",
            'output': "выход",
            'sigma-delta': "сигма-дельта",
            'normal': "обычный"
        }
        if value not in ['sigma-delta', 'normal']:
            self.logger.error("Неверный тип сигнала '{0}': {1}".format(name, value))
            sys.exit(1)
        self.logger.info("Задаю тип сигнала на {0}е модуля: {1}".format(printable[name], printable[value]))
        self.connection_type[name] = value

    def fill_module_info(self):
        self.template = self.template.format(**SafeDict({
            'creation_date': self.creation_date.strftime('%d.%m.%Y / %H:%M:%S'),
            'time_spent': (datetime.datetime.now() - self.creation_date).microseconds,
            'used_cores': ', '.join([x['name'] for x in self.assoc.values()])
        }))
