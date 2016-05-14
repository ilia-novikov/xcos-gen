class Block:
    def __init__(self, block_type: str, block_id: str):
        self.block_type = block_type
        self.block_id = block_id
        self.inputs = []
        self.outputs = []
        self.gain = None

    def connect(self, block):
        block.inputs.append(self.block_id)
        self.outputs.append(block.block_id)

    def __str__(self):
        return "{0}: {1}".format(self.block_type, self.block_id)