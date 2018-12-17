from slearner_helpers import get_sl_tokens


class PostProcessorInterface:
    pass


class AsIsPP(PostProcessorInterface):
    """
    Returns object as-is, instead of converting to string
    """
    def go(self, entry):
        return entry


class InterleavedSystemPP(PostProcessorInterface):
    def get_block_name(self, block):
        for x in block.outputs:
            x = x.strip()
            tokens = get_sl_tokens(x)
            if tokens[0] == 'Name':
                return tokens[1]

        raise Exception('Unexpected - no name found for block')

    def get_block_names_for_line(self, line):
        src_blk = None
        dst_blks = []

        for x in line.outputs:
            x = x.strip()
            tokens = get_sl_tokens(x)
            if tokens[0] == 'SrcBlock':
                src_blk = tokens[1]
            elif tokens[0] == 'DstBlock':
                dst_blks.append(tokens[1])

        # if src_blk is None:
        #     assert False
        # if len(dst_blks) == 0:
        #     assert False

        return src_blk, dst_blks

    def get_plain_output(self, entries):
        return ''.join(entries)

    def go(self, entry):
        entries = entry.outputs
        final_output = [entries[0]]

        plain_strings = []
        blocks = {}
        lines = []

        for i in entries[2:len(entries) - 1]:
            if type(i) == str:
                plain_strings.append(i)
            elif i.kw == 'Block':
                blocks[self.get_block_name(i)] = i
            elif i.kw == 'Line':
                lines.append(i)

        added_blocks = set()

        for line in lines:
            src_blk, dst_blks = self.get_block_names_for_line(line)

            # if src_blk not in blocks:
            #     assert False

            if src_blk in blocks and src_blk not in added_blocks:
                final_output.append(self.get_plain_output(blocks[src_blk].outputs))
                added_blocks.add(src_blk)

            for dst_blk in dst_blks:
                assert dst_blk in blocks
                if dst_blk not in blocks or dst_blk in added_blocks:
                    continue

                final_output.append(self.get_plain_output(blocks[dst_blk].outputs))
                added_blocks.add(dst_blk)

            final_output.append(self.get_plain_output(line.outputs))

        final_output.append(entries[-1])

        return self.get_plain_output(final_output)
