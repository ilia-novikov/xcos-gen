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


class Block:
    def __init__(self, block_type: str, block_id: str):
        self.block_type = block_type
        self.block_id = block_id
        self.inputs = set()
        self.outputs = set()
        self.gain = None

    def connect(self, block):
        block.inputs.add(self.block_id)
        self.outputs.add(block.block_id)

    def __str__(self):
        if not self.gain:
            return "{0}: {1}".format(self.block_type, self.block_id)
        else:
            return "{0}: {1}, k = {2}".format(self.block_type, self.block_id, self.gain)
