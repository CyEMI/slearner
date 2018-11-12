import unittest
import os
import filecmp

from model_preprocess import ModelPreprocessor, BulkModelProcessor


class TestModelPreprocessor(unittest.TestCase):

    my_dir = os.path.dirname(os.path.realpath(__file__))

    def test_sampleModel(self):
        sys_loc = os.path.join(self.my_dir, 'testdata', 'sampleModel20.mdl')
        out_loc = os.path.join(self.my_dir, 'output')

        mp = ModelPreprocessor(sys_loc, out_loc)
        result = mp.go(True)
        self.assertIsNone(result)

    def test_smoke1(self):
        sys_loc = os.path.join(self.my_dir, 'testdata', 'sampleModel1.mdl')
        out_loc = os.path.join(self.my_dir, 'output')

        mp = ModelPreprocessor(sys_loc, out_loc)
        result = mp.go(True)
        self.assertIsNone(result)


class TestBulkModelPreprocessor(unittest.TestCase):

    my_dir = os.path.dirname(os.path.realpath(__file__))

    def test_smoke(self):
        """
        Converts all three model files from testdata folder and compare
        """
        sys_loc = os.path.join(self.my_dir, 'testdata')
        out_loc = os.path.join(self.my_dir, 'output')

        mp = BulkModelProcessor(sys_loc, out_loc)
        mp.go(True)

        for i in (20, 21, 22,):
            o_loc = os.path.join(self.my_dir, 'output', 'sampleModel{}.mdl'.format(i))
            base_loc = os.path.join(self.my_dir, 'testdata', '{}ni.txt'.format(i))
            self.assertTrue(filecmp.cmp(o_loc, base_loc, shallow=False), 'Model sampleModel{} mismatched'.format(i))

        # does not work.. set order not reliable? #TODO construct set and compare
        self.assertTrue(filecmp.cmp(os.path.join(self.my_dir, 'output', 'unique_keywords.txt'),
                        os.path.join(self.my_dir, 'testdata', '202122_uk.txt'), shallow=False),
                        'Unique Keywords text file mismatched')

    def test_corpus(self):
        sys_loc = '/home/cyfuzz/workspace/explore/success'
        out_loc = '/home/cyfuzz/workspace/explore/processed'

        mp = BulkModelProcessor(sys_loc, out_loc)
        mp.go(True)
