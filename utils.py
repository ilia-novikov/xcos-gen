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

import logging

__version__ = '0.2'
__author__ = 'Ilia Novikov <ilia.novikov@live.ru>'

separator = '-------------------------------'


def get_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter(
        fmt='xcos-gen::{0} %(levelname)s @ [%(asctime)s] %(message)s'.format(name),
        datefmt='%d-%m-%Y / %H:%M:%S'
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
