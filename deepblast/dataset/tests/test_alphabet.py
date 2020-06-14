import numpy as np
import torch
import unittest
from deepblast.dataset.alphabet import UniprotTokenizer
import numpy.testing as npt


class TestAlphabet(unittest.TestCase):

    def test_tokenizer(self):
        tokenizer = UniprotTokenizer()
        res = tokenizer(b'ARNDCQEGHILKMFPSTWYVXOUBZ')
        # Need to account for padding and offset
        exp = np.array([0] + list(range(1, 22)) + [12,5,21,21] + [0])
        npt.assert_allclose(res, exp)

    def test_tokenizer_encode(self):
        tokenizer = UniprotTokenizer()
        x = 'ARNDCQEGHILKMFPSTWYVXOUBZ'
        x = str.encode(x)
        res = tokenizer(x)
        self.assertEqual(len(x) + 2, len(res))


if __name__ == '__main__':
    unittest.main()