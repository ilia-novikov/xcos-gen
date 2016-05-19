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

from block import Block


class HdlBlock:
    def __init__(self, block: Block, hdl_type: str):
        self.block_type = hdl_type
        self.block_id = block.block_id
        self.gain = block.gain
        self.inputs = block.inputs
        self.outputs = block.outputs
        self.in_wire = None
        self.out_wire = None

    def __str__(self):
        if not self.gain:
            return "{0}: {1}, {2} -> {3}".format(self.block_type, self.block_id, self.in_wire, self.out_wire)
        else:
            return "{0}: {1}, k = {2}, {3} -> {4}".format(
                self.block_type,
                self.block_id,
                self.gain,
                self.in_wire,
                self.out_wire
            )
