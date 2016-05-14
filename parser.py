import logging.handlers
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import shutil
import subprocess

from block import Block

DEBUG = False
SCILAB_ROOT = '/home/ilia/scilab-5.5.2/'
JAVA = '/usr/lib/jvm/jdk1.8.0_72/bin/java'


class Parser:
    content_file = 'content.xml'
    source_data_file = 'dictionary/dictionary.ser'
    destination_data_file = 'data.bin'

    def __init__(self, model_file):
        self.logger = self.initialize_logger()
        self.model = self.load_model(model_file)
        self.blocks = self.get_basic_blocks()
        self.get_links()
        self.simplify()

    @staticmethod
    def initialize_logger():
        formatter = logging.Formatter(
            fmt='xcos-gen :: %(levelname)s @ [%(asctime)s] %(message)s',
            datefmt='%d-%m-%Y / %H:%M:%S'
        )
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        return logger

    def load_model(self, model_file):
        self.logger.info('-------------------------------')
        self.logger.info("Загрузка модели...")
        if not os.path.exists(model_file) or not os.path.isfile(model_file):
            self.logger.error("Файл модели не найден: {0}".format(model_file))
            sys.exit(1)
        if not zipfile.is_zipfile(model_file):
            self.logger.error("Файл не является xcos архивом: {0}".format(model_file))
            sys.exit(1)
        with zipfile.ZipFile(model_file) as archive:
            if self.content_file not in archive.namelist() or self.source_data_file not in archive.namelist():
                self.logger.error("В файле не найдено описание модели: {0}".format(model_file))
                sys.exit(1)
            if DEBUG:
                archive.extract(self.content_file)
            with archive.open(self.content_file) as file:
                content_tree = ET.fromstring(file.read().decode().replace('RoundBlock', 'BasicBlock'))
            archive.extract(self.source_data_file, './')
            shutil.move(self.source_data_file, self.destination_data_file)
            shutil.rmtree(self.source_data_file.split('/')[0])

        model = content_tree[0][0]
        self.logger.info("Модель успешно загружена: {0}".format(content_tree.attrib['title']))
        self.logger.info("Загружено компонентов модели: {0}".format(len(model)))
        return model

    def get_basic_blocks(self):
        self.logger.info('-------------------------------')
        self.logger.info("Поиск базовых блоков...")
        blocks = []
        for item in self.model.iter('BasicBlock'):
            block_type = item.attrib['interfaceFunctionName']
            block_id = item.attrib['id']
            if block_type not in ['INTEGRAL_f', 'DIFF_f', 'GAIN_f', 'DEMUX', 'SUM_f']:
                self.logger.error("Неивестный тип блока: {0}".format(block_type))
                exit(1)
            block = Block(block_type, block_id)
            if block_type == 'GAIN_f':
                for child in item.iter('ScilabDouble'):
                    if child.attrib['as'] == 'realParameters':
                        command = '{0} -classpath {1}:{2} Extractor {3} {4}'.format(
                            JAVA,
                            os.path.dirname(__file__),
                            SCILAB_ROOT + 'share/scilab/modules/types/jar/org.scilab.modules.types.jar',
                            os.path.dirname(__file__) + '/' + self.destination_data_file,
                            child.attrib['position']
                        )
                        p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                        result, _ = p.communicate()
                        gain = float(result.decode().strip()[1:-1])
                        block.gain = gain
            if not block.gain:
                self.logger.info("Тип блока: {0}, ID блока: {1}".format(block_type, block_id))
            else:
                self.logger.info("Тип блока: {0}, ID блока: {1}, коэффициент: {2}".format(
                    block_type,
                    block_id,
                    block.gain
                ))
            blocks.append(block)
        self.logger.info("Найдено базовых блоков: {0}".format(len(blocks)))
        return blocks

    def find_item(self, item_id):
        for item in self.model:
            if item.attrib['id'] == item_id:
                return item

    def find_block(self, block_id) -> Block:
        for item in self.blocks:
            if item.block_id == block_id:
                return item

    def find_endpoints(self, link):
        source_port = self.find_item(link.attrib['source'])
        source = self.find_item(source_port.attrib['parent'])
        target_port = self.find_item(link.attrib['target'])
        target = self.find_item(target_port.attrib['parent'])
        return source, target

    def simplify(self):
        self.logger.info('-------------------------------')
        self.logger.info("Упрощение модели...")
        to_remove = set()
        for block in self.blocks:
            if block.block_type == 'DEMUX':
                source = self.find_block(list(block.inputs)[0])
                source.outputs.remove(block.block_id)
                for output in block.outputs:
                    target = self.find_block(output)
                    target.inputs.remove(block.block_id)
                    source.connect(target)
                to_remove.add(block)
            if block.block_type == 'SUM_f':
                for item in list(block.inputs):
                    neighbour = self.find_block(item)
                    if neighbour.block_type == 'SUM_f':
                        block.inputs.remove(neighbour.block_id)
                        for port in neighbour.inputs:
                            source = self.find_block(port)
                            source.outputs.remove(neighbour.block_id)
                            source.connect(block)
                        to_remove.add(neighbour)
        for block in to_remove:
            self.logger.info("Блок {0} удален: {1}".format(block.block_type, block.block_id))
            self.blocks.remove(block)

    def get_links(self):
        self.logger.info('-------------------------------')
        self.logger.info("Поиск связей...")
        links = list([x for x in self.model.iter('ExplicitLink')])
        for item in links:
            source, target = self.find_endpoints(item)
            self.logger.info("Связь {0}: {1} -> {2}".format(
                item.attrib['id'],
                source.tag,
                target.tag
            ))
        self.logger.info('-------------------------------')
        self.logger.info("Обработка связей типа блок -> блок")
        for item in links:
            source, target = self.find_endpoints(item)
            if source.tag == 'BasicBlock' and target.tag == 'BasicBlock':
                self.connect_basic_blocks(source, target)

    def connect_basic_blocks(self, source, target):
        source_block = self.find_block(source.attrib['id'])
        target_block = self.find_block(target.attrib['id'])
        self.logger.info("Создаю соединение: {0} -> {1}".format(
            source_block.block_type,
            target_block.block_type
        ))
        source_block.connect(target_block)

    def finalize(self):
        os.remove(self.destination_data_file)

parser = Parser('./model.zcos')
parser.finalize()
