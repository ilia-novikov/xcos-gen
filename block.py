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
