#!/usr/bin/env python3
import argparse
import os.path
import sys

from post_processors import InterleavedSystemPP, AsIsPP
from slearner_helpers import get_sl_tokens

SYS_EXT = '.mdl'
OUTPUT_PREFIX = '_PPD'

DUMMY_MODEL_ROOT = 'SLearnerDummyRoot'

UNIQUE_KW_WRAPPER = '      tokens: "{0}"'

# Post-processors
POST_PROCESSOR_REGISTRY = {
    'System': InterleavedSystemPP,
    'Block': AsIsPP,
    'Line': AsIsPP
}


def pre_keywords():
    """Add these keywords"""
    return {'{', '}', }


class CollectedToken:

    @property
    def output(self):
        if self._is_post_process_on and self.kw in POST_PROCESSOR_REGISTRY:
            return POST_PROCESSOR_REGISTRY[self.kw]().go(self)
        else:
            return ''.join(self.outputs)

    def __init__(self, kw, init_line='', is_post_process_on=False):
        self._is_post_process_on = is_post_process_on
        self.kw = kw  # The keyword
        self.outputs = [init_line]
        self.brace_count = 1

    def add_line(self, line):
        # Line may not be string in case of post-processors present
        self.outputs.append(line)


class ModelPreprocessor:
    """docstring for ModelPreprocessor"""

    @property
    def unique_kws(self):
        return self._unique_kws

    def __init__(self, model_name, outdir, unique_kws=None, postprocess=False):
        self._sys = model_name
        self._outdir = outdir

        self._outsys = None  # Output file

        # self._outputs = []  # Output lines

        self._unique_kws = unique_kws if unique_kws is not None else set()  # Unique keywords

        self._postprocess = postprocess

        # What to items to collect from this document?

        self._collectibles = [{
            DUMMY_MODEL_ROOT: {'Model': {
                'Name': None,  # None means capture the whole element
                'System': {
                    'Block': None,
                    'Line': None,
                    None: None  # Also collect others type of children
                }
            }}
        }, ]  # Stack

        self._collections = [CollectedToken(DUMMY_MODEL_ROOT, is_post_process_on=self._postprocess)]  # Stack containing collected tokens.

    def go(self, write_in_disc):
        print('Input: {} Output: {}'.format(self._sys, self._outdir))
        assert os.path.exists(self._sys)
        assert (os.path.exists(self._outdir))

        self._get_out_files()
        self._parse()

        output = self._collections[-1].output

        if write_in_disc:
            self._write_output(output)
            return None
        else:
            return output

    def _parse(self):

        # self._outputs.append(self._get_prefix())

        with open(self._sys, 'r') as infile:
            for l in infile:
                line = l.strip()
                tokens = get_sl_tokens(line)

                top = self._collections[-1]
                lookup = self._collectibles[-1] # Top of collectibles

                if lookup is not None and (lookup[top.kw] is None or tokens[0] in lookup[top.kw] or None in lookup[top.kw]):
                    self._include_line(line, l, tokens, top)  # This may change top by pushing new
                else:
                    self._skip_line(line, l, tokens, top)

    def _skip_line(self, line, original_line, tokens, top):
        """ This keyword is not interesting.
        Just do brace count to know when to return from scope."""

        if line == '}':
            top.brace_count -= 1

            if top.brace_count == 0:
                top.add_line(original_line)
                self._decrement_scope(top)
            else:  # Still non-interesting
                self._collectibles.pop()

        elif '{' in tokens:
            top.brace_count += 1
            self._collectibles.append(None)  # Dummy

    def _decrement_scope(self, top):
        """Pop Elements from various stacks due to decrementing scope"""
        self._collectibles.pop()
        self._collections.pop()
        self._collections[-1].add_line(top.output)

    def _include_line(self, line, original_line, tokens, top):
        # Return: whether to add token in unique keywords

        if line == "}":
            top.add_line(original_line)
            top.brace_count -= 1

            if top.brace_count == 0:
                self._decrement_scope(top)

            return

        has_open_brace = "{" in tokens

        if not has_open_brace:
            # Single liners -- no need to start new scope.
            top.add_line(original_line)

        elif self._collectibles[-1][top.kw] is None:
            # Parent wants every child. No need to start scope, instead use brace counting
            top.add_line(original_line)
            top.brace_count += 1
        else:
            # Parent wants selected children. Start new scope
            self._collectibles.append(self._collectibles[-1][top.kw])
            self._collections.append(CollectedToken(tokens[0], original_line, is_post_process_on=self._postprocess))

        self._unique_kws.add(tokens[0])

    def _write_output(self, output):
        with open(self._outsys, 'w') as outfile:
            outfile.write(output)

    def _get_out_files(self):
        self._sysdir, sys = os.path.split(self._sys)

        self._outsys = os.path.join(self._outdir, sys)


class BulkModelProcessor:
    def __init__(self, input_dir, output_dir, postprocess):
        self._input_dir = input_dir
        self._output_dir = output_dir
        self._unique_kw = set()  # Unique Keywords
        self._postprocess = postprocess

    def _process_dir(self, *args):
        num_success = 0
        num_error = 0

        for file in os.listdir(self._input_dir):
            if os.path.isdir(file) or not file.endswith(SYS_EXT):
                continue

            try:
                mp = ModelPreprocessor(os.path.join(self._input_dir, file), self._output_dir, self._unique_kw,
                                       self._postprocess)
                mp.go(*args)

                num_success += 1
            except e:
                num_error += 1
                print('Error: {}'.format(e))

        print('Success: {}; Error: {}'.format(num_success, num_error))

    def _write_unique_kws(self):
        kw_file_name = 'unique_keywords.txt'
        kw_file_path = os.path.join(self._output_dir, kw_file_name)

        with open(kw_file_path, 'w') as outfile:
            outfile.write('\n'.join([UNIQUE_KW_WRAPPER.format(i) for i in (self._unique_kw | pre_keywords())
                                     if not i.startswith('"')]))

    def go(self, *args):
        if os.path.isfile(self._input_dir):
            mp = ModelPreprocessor(self._input_dir, self._output_dir, self._unique_kw)
            mp.go(*args)
        else:
            self._process_dir(*args)

        if '}' in self._unique_kw:  # might be unnecessary
            self._unique_kw.remove('}')

        self._write_unique_kws()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--sys", help='Full path of the Simulink Model')
    parser.add_argument('--outdir', help='output location')
    parser.add_argument('--postprocess', help='Post process e.g. interleave blocks and lines',
                        nargs='?', const=False, type=bool)

    cmd_args = parser.parse_args()

    try:
        BulkModelProcessor(cmd_args.sys, cmd_args.outdir, cmd_args.postprocess).go(True)
        print('-------- RETURNING FROM model_preprocessor --------')
        sys.exit(0)
    except Exception as e:
        print('Exception in model_preprocessor.py: {}'.format(e))
        sys.exit(-1)
