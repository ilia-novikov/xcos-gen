import logging.handlers
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

import shutil

import subprocess

from block import Block

scilab_path = '/home/ilia/scilab-5.5.2/'
java = '/usr/lib/jvm/jdk1.8.0_72/bin/java'

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

if len(sys.argv) != 2:
    logger.error("Недостаточно аргументов")
    sys.exit(1)

debug = True

model_file = sys.argv[1]
if not os.path.exists(model_file) or not os.path.isfile(model_file):
    logger.error("Файл модели не найден: {0}".format(model_file))
    sys.exit(1)
if not zipfile.is_zipfile(model_file):
    logger.error("Файл не является xcos архивом: {0}".format(model_file))
    sys.exit(1)
with zipfile.ZipFile(model_file) as archive:
    if 'content.xml' not in archive.namelist() or 'dictionary/dictionary.ser' not in archive.namelist():
        logger.error("В файле не найдено описание модели: {0}".format(model_file))
        sys.exit(1)
    if debug:
        archive.extract('content.xml')
    with archive.open('content.xml') as file:
        content_tree = ET.fromstring(file.read())
    archive.extract('dictionary/dictionary.ser', './')
    shutil.move('dictionary/dictionary.ser', 'data.bin')
    shutil.rmtree('dictionary')

model = content_tree[0][0]
logger.info("Модель успешно загружена: {0}".format(content_tree.attrib['title']))
logger.info("Компонентов модели: {0}".format(len(model)))

known_blocks = ['INTEGRAL_f', 'DIFF_f', 'GAIN_f']

blocks = []

for item in model.iter('BasicBlock'):
    block_type = item.attrib['interfaceFunctionName']
    block_id = item.attrib['id']
    if block_type not in known_blocks:
        logger.error("Неивестный тип блока: {0}".format(block_type))
        exit(1)
    block = Block(block_type, block_id)
    if block_type == 'GAIN_f':
        for child in item.iter('ScilabDouble'):
            if child.attrib['as'] == 'realParameters':
                command = '{0} -classpath {1}:{2} Extractor {3} {4}'.format(
                    java,
                    os.path.dirname(__file__),
                    scilab_path + 'share/scilab/modules/types/jar/org.scilab.modules.types.jar',
                    os.path.dirname(__file__) + '/data.bin',
                    child.attrib['position']
                )
                p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                result, _ = p.communicate()
                gain = float(result.decode().strip()[1:-1])
                block.gain = gain
    if not block.gain:
        logger.info("Тип блока: {0}, ID блока: {1}".format(block_type, block_id))
    else:
        logger.info("Тип блока: {0}, ID блока: {1}, коэффициент: {2}".format(block_type, block_id, block.gain))
    blocks.append(block)
