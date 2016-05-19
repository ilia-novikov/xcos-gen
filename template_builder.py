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
from hdl_block import HdlBlock
from parser import Parser
from safe_dict import SafeDict

CORES_DIR = '/home/ilia/src/sc_cores'


class TemplateBuilder:
    def __init__(self, filename: str):
        self.logger = utils.get_logger(__name__)
        self.assoc = {}
        self.module_name = 'regulator'
        self.template = ''
        self.body = ''
        self.block_ids = {}
        self.wire_id = 0
        self.module_params = []
        self.module_ports = {
            'module_input': {
                'type': 'sigma-delta',
                'width': 2
            },
            'module_output': {
                'type': 'sigma-delta',
                'width': 2
            }
        }
        self.hdl_blocks = []
        self.creation_date = datetime.datetime.now()
        self.preprocess(filename)
        self.fill_module_info()

    def preprocess(self, filename: str):
        self.logger.info(utils.separator)
        self.logger.info("Запускаю обработку шаблона...")
        if not os.path.exists(filename):
            self.logger.error("Файл шаблона не найден: {0}".format(filename))
            sys.exit(1)
        with open(filename) as file:
            for line in file.readlines():
                self.parse(line)
        self.template += '\n'

    def parse(self, line: str):
        line = line.strip()
        if line.startswith(';') or not line:
            return
        if not line.startswith(':'):
            self.logger.error("Некорректный синтаксис в шаблоне: {0}".format(line))
            sys.exit(1)
        split = shlex.split(line)
        commands = {
            'include': lambda: self.include(split[1]),
            'body': lambda: self.place_body(),
            'info': lambda: self.logger.info(split[1]),
            'warning': lambda: self.logger.warning(split[1]),
            'assoc': lambda: self.create_association(split[1], split[2]),
            'param': lambda: self.create_param(split[1], split[2]),
            'module_input': lambda: self.set_module_port(command, split),
            'module_output': lambda: self.set_module_port(command, split),
            'name': lambda: self.set_module_name(split[1])
        }
        command = split[0][1:]
        if command not in commands:
            self.logger.error("Некорректный синтаксис в шаблоне: {0}".format(line))
            sys.exit(1)
        commands[command]()

    def include(self, part: str):
        self.logger.info("Выполняю импорт {0}".format(part))
        filename = '{0}.part'.format(part)
        if not os.path.exists(filename):
            self.logger.error("Файл для импорта не найден: {0}".format(filename))
            sys.exit(1)
        with open(filename) as file:
            self.template += file.read()

    def create_association(self, source: str, target: str):
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
        self.template = self.template.format(**SafeDict({
            'module_name': self.module_name,
            'module_params': self.get_module_params(),
            'module_ports': self.get_module_ports()
        }))
        blocks = parser.blocks
        entrance_count = 0
        for block in blocks:
            if block.block_type not in self.assoc:
                self.logger.error("Не найдена ассоциация для блока: {0}".format(block.block_type))
                sys.exit(1)
            if len(block.inputs) == 0:
                entrance_count += 1
        if entrance_count > 1:
            self.logger.error("В модели более 1 блока без входов. Невозможно выбрать начальный блок")
            sys.exit(1)
        initial_wire = 'in'
        if self.module_ports['module_input']['type'] == 'normal':
            self.logger.info("Добавляю сигма-дельта модулятор")
            initial_wire = self.place_wire(2)
            params = {
                'N': self.module_ports['module_input']['width'],
                'k': 1,
                'ext_feedback': 0,
                'bin': 1
            }
            ports = {
                'x': 'in',
                'y_feedback': 0,
                'y': initial_wire
            }
            self.place_hdl_block('sd_modulator', params, ports)
            self.body += '\n'
        for block in parser.blocks:
            self.hdl_blocks.append(HdlBlock(block, self.assoc[block.block_type]['name']))
        self.reconnect_hdl_blocks()
        self.find_input_wire(initial_wire, initial_wire != 'in')
        self.body += '\n\n'
        self.logger.info(utils.separator)
        self.logger.info("Запускаю генерацию блоков HDL")
        for hdl_block in self.hdl_blocks:
            self.create_hdl_block(hdl_block)
        self.template = self.template.format(**SafeDict({'body': self.body}))

    def place_body(self):
        self.template += '{body}\n'

    def create_param(self, name: str, value: str):
        self.logger.info("Добавляю параметр {0} со значением {1}".format(name, value))
        self.module_params.append({
            'name': name,
            'value': int(value)
        })

    def set_module_port(self, name: str, value: str):
        printable = {
            'module_input': "вход",
            'module_output': "выход",
            'sigma-delta': "сигма-дельта",
            'normal': "обычный"
        }
        port_type = value[1]
        if port_type not in ['sigma-delta', 'normal']:
            self.logger.error("Неверный тип сигнала '{0}': {1}".format(name, port_type))
            sys.exit(1)
        port_width = 2 if port_type == 'sigma-delta' else int(value[2])
        self.logger.info("Задаю тип сигнала на {0}е модуля: {1} шириной {2} бит".format(
            printable[name],
            printable[port_type],
            port_width
        ))
        self.module_ports[name] = {
            'type': port_type,
            'width': port_width
        }

    def fill_module_info(self):
        self.template = self.template.format(**SafeDict({
            'creation_date': self.creation_date.strftime('%d.%m.%Y / %H:%M:%S'),
            'time_spent': (datetime.datetime.now() - self.creation_date).microseconds,
            'used_cores': ', '.join([x['name'] for x in self.assoc.values()])
        }))

    def set_module_name(self, name: str):
        self.logger.info("Задаю имя модуля HDL как {0}".format(name))
        self.module_name = name

    def get_module_params(self) -> str:
        self.logger.info("Создаю параметры модуля")
        if not self.module_params:
            return ''
        template = '    {0} = {1}'
        printable_params = ',\n'.join(template.format(param['name'], param['value']) for param in self.module_params)
        return '#(\n    parameter\n{0}\n)'.format(printable_params)

    @staticmethod
    def get_printable_port(port: dict) -> str:
        if 'width' in port:
            return '    {0} [{1}:0] {2}'.format(port['type'], port['width'] - 1, port['name'])
        else:
            return '    {0} {1}'.format(port['type'], port['name'])

    def get_module_ports(self) -> str:
        self.logger.info("Создаю порты модуля")
        ports = [
            {
                'type': 'input',
                'name': 'clk'
            },
            {
                'type': 'input',
                'name': 'reset'
            },
            {
                'type': 'input',
                'name': 'in',
                'width': self.module_ports['module_input']['width']
            },
            {
                'type': 'output',
                'name': 'out',
                'width': self.module_ports['module_output']['width']
            }
        ]
        printable_ports = '\n'
        printable_ports += ',\n'.join(self.get_printable_port(port) for port in ports)
        printable_ports += '\n'
        return printable_ports

    def create_hdl_block(self, hdl_block: HdlBlock):
        hdl_block_types = {
            'sd_adder': lambda: self.create_adder(hdl_block),
            'sd_mult_2in': lambda: self.create_multiplier(hdl_block),
            'sd_diff': lambda: self.create_differentiator(hdl_block),
            'sd_integrator': lambda: self.create_integrator(hdl_block)
        }
        if hdl_block.block_type in hdl_block_types:
            hdl_block_types[hdl_block.block_type]()
        else:
            self.logger.error("Неизвестен рецепт для генерации: {0}".format(hdl_block.block_type))
            sys.exit(1)

    def place_hdl_block(self, name: str, params: dict, ports: dict):
        ports['clk'] = 'clk'
        ports['rst'] = 'rst'
        if name in self.block_ids:
            self.block_ids[name] += 1
        else:
            self.block_ids[name] = 0
        instance_name = '{0}_{1}'.format(name, self.block_ids[name])
        self.logger.info("Создаю блок {0}".format(name))
        printable = '    ' + name
        template = '        .{0}({1})'
        if params:
            printable_params = ',\n'.join(template.format(key, params[key]) for key in params.keys())
            printable += ' #(\n{0}\n    )'.format(printable_params)
        printable_ports = ',\n'.join(template.format(key, ports[key]) for key in ports.keys())
        printable += ' {0} (\n{1}\n    )'.format(instance_name, printable_ports)
        self.body += printable + '\n\n'

    def place_wire(self, width=2):
        name = 'wire_{0}'.format(self.wire_id)
        self.wire_id += 1
        self.logger.info("Добавляю провод: {0}".format(name))
        self.body += '    wire [{0}:0] {1};\n'.format(width - 1, name)
        return name

    def find_hdl_block(self, block_id: str) -> HdlBlock:
        for block in self.hdl_blocks:
            if block.block_id == block_id:
                return block
        return None

    def find_input_wire(self, replace_wire: str, ignore_first=False):
        self.logger.info(utils.separator)
        self.logger.info("Выполняю переподключение входного сигнала...")
        start_index = 1 if ignore_first else 0
        wires = ['wire_{0}'.format(x) for x in range(start_index, self.wire_id)]
        for hdl_block in self.hdl_blocks:
            if hdl_block.out_wire in wires:
                wires.remove(hdl_block.out_wire)
        if not wires or len(wires) > 1:
            self.logger.error("Невозможно выбрать входной сигнал")
            sys.exit(1)
        model_input_wire = wires[0]
        self.logger.info("Входной сигнал модели: {0}".format(model_input_wire))
        for hdl_block in self.hdl_blocks:
            if hdl_block.in_wire == model_input_wire:
                self.logger.info("Замена входного сигнала для {0} на {1}".format(hdl_block.block_type, replace_wire))
                hdl_block.in_wire = replace_wire
                break
        lines = self.body.splitlines()
        for i in range(0, len(lines)):
            if model_input_wire in lines[i]:
                self.logger.info("Сигнал {0} был удален".format(model_input_wire))
                lines.remove(lines[i])
                self.body = '\n'.join(lines)
                break

    def reconnect_hdl_blocks(self):
        self.logger.info(utils.separator)
        self.logger.info("Выполняю создание соединений...")
        for hdl_block in self.hdl_blocks:
            for source in hdl_block.inputs:
                source_block = self.find_hdl_block(source)
                if source_block.out_wire:
                    if hdl_block.block_type != 'sd_adder':
                        hdl_block.in_wire = source_block.out_wire
                        break
                    else:
                        if not hdl_block.in_wire:
                            hdl_block.in_wire = []
                            hdl_block.in_wire.append(source_block.out_wire)
            if not hdl_block.in_wire:
                hdl_block.in_wire = self.place_wire()
                for source in hdl_block.inputs:
                    source_block = self.find_hdl_block(source)
                    source_block.out_wire = hdl_block.in_wire
            for target in hdl_block.outputs:
                target_block = self.find_hdl_block(target)
                if target_block.in_wire and target_block.block_type != 'sd_adder':
                    hdl_block.out_wire = target_block.in_wire
                    break
            if not hdl_block.out_wire:
                hdl_block.out_wire = self.place_wire()
                for target in hdl_block.outputs:
                    target_block = self.find_hdl_block(target)
                    if target_block.block_type != 'sd_adder':
                        target_block.in_wire = hdl_block.out_wire
                    else:
                        if not target_block.in_wire:
                            target_block.in_wire = []
                        target_block.in_wire.append(hdl_block.out_wire)

    def create_adder(self, hdl_block: HdlBlock):
        if len(hdl_block.inputs) > 2:
            self.logger.error("В данной версии не поддерживаются сумматоры с числом входов > 2")
            sys.exit(1)
        params = {
            'bin': 0,
            'N': 3
        }
        ports = {
            'x': hdl_block.in_wire[0],
            'y': hdl_block.in_wire[1],
            's': hdl_block.out_wire
        }
        self.place_hdl_block(hdl_block.block_type, params, ports)

    def create_multiplier(self, hdl_block: HdlBlock):
        params = {
            'N': 16,
            'outN': 2,
            'intN': 0,
            'bin': 0
        }
        ports = {
            'x': hdl_block.in_wire,
            'kp': hdl_block.gain,
            'kn': -hdl_block.gain,
            'y': hdl_block.out_wire
        }
        self.place_hdl_block(hdl_block.block_type, params, ports)

    def create_differentiator(self, hdl_block: HdlBlock):
        params = {
            'N': 15,
            'k': 5,
            'bin': 0
        }
        ports = {
            'x': hdl_block.in_wire,
            'y': hdl_block.out_wire,
            'y_pcm': 0
        }
        self.place_hdl_block(hdl_block.block_type, params, ports)

    def create_integrator(self, hdl_block: HdlBlock):
        params = {
            'N': 31,
            'Nmod': 'N + 1',
            'bin': 1,
            'doWin': 0,
            'doSrst': 0,
            'doRVin': 0,
            'doEn': 0
        }
        ports = {
            'w': 0,
            'x': hdl_block.in_wire,
            'k': 1,
            'rst_value': 0,
            'sync_rst': 0,
            'enable': 0,
            'y': hdl_block.out_wire,
            'pcm_y': 0
        }
        self.place_hdl_block(hdl_block.block_type, params, ports)
