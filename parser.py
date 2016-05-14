import logging.handlers
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import shutil
import subprocess

from block import Block

DEBUG = True
SCILAB_ROOT = '/home/ilia/scilab-5.5.2/'
JAVA = '/usr/lib/jvm/jdk1.8.0_72/bin/java'


class Parser:
    content_file = 'content.xml'
    source_data_file = 'dictionary/dictionary.ser'
    destination_data_file = 'data.bin'

    def __init__(self, model_file):
        self.logger = self.initialize_logger()
        self.model = self.load_model(model_file)
        self.get_basic_blocks()

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
                content_tree = ET.fromstring(file.read())
            archive.extract(self.source_data_file, './')
            shutil.move(self.source_data_file, self.destination_data_file)
            shutil.rmtree(self.source_data_file.split('/')[0])

        model = content_tree[0][0]
        self.logger.info("Модель успешно загружена: {0}".format(content_tree.attrib['title']))
        self.logger.info("Компонентов модели: {0}".format(len(model)))
        return model

    def get_basic_blocks(self):
        blocks = []
        for item in self.model.iter('BasicBlock'):
            block_type = item.attrib['interfaceFunctionName']
            block_id = item.attrib['id']
            if block_type not in ['INTEGRAL_f', 'DIFF_f', 'GAIN_f']:
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
                self.logger.info("Тип блока: {0}, ID блока: {1}, коэффициент: {2}".format(block_type, block_id, block.gain))
            blocks.append(block)
        return blocks

    def finalize(self):
        os.remove(self.destination_data_file)
        if not DEBUG:
            os.remove(self.content_file)

p = Parser('./model.zcos')
p.finalize()
