from unittest import TestCase
from hexachromix.core import HexachromixState

class TestCore(TestCase):
    def setUp(self):
        self.longMessage = True

    def test_hfen(self):
        self.assertEqual(HexachromixState().hfen, '3/4/5/4/3 R MRY')

        self.assertEqual(HexachromixState([0]*19, 0, 'MRY').hfen, '3/4/5/4/3 R MRY')
        self.assertEqual(HexachromixState([1]+[0]*17+[2], 2, 'MR').hfen, 'R2/4/5/4/2Y G MR')

        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 R MRY').hfen, '3/4/5/4/3 R MRY')
        self.assertEqual(HexachromixState(hfen='GC1/BMRC/2R1c/MMYY/1BY C MRY').hfen, 'GC1/BMRC/2R1c/MMYY/1BY C MRY')

    def test_get_current_team(self):
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 R MRY').get_current_team(), 'MRY')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 Y MRY').get_current_team(), 'MRY')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 G MRY').get_current_team(), 'GCB')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 C MRY').get_current_team(), 'GCB')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 B MRY').get_current_team(), 'GCB')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 M MRY').get_current_team(), 'MRY')

        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 R MR').get_current_team(), 'MR')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 Y MR').get_current_team(), 'YG')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 G MR').get_current_team(), 'YG')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 C MR').get_current_team(), 'CB')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 B MR').get_current_team(), 'CB')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 M MR').get_current_team(), 'MR')

        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 R R').get_current_team(), 'R')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 Y R').get_current_team(), 'Y')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 G R').get_current_team(), 'G')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 C R').get_current_team(), 'C')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 B R').get_current_team(), 'B')
        self.assertEqual(HexachromixState(hfen='3/4/5/4/3 M R').get_current_team(), 'M')

    def test_get_legal_moves(self):
        self.assertEqual(len(HexachromixState(hfen='3/4/5/4/3 R MRY').get_legal_moves()), 19)
        self.assertEqual(len(HexachromixState(hfen='R2/4/5/4/3 Y MRY').get_legal_moves()), 18)
        self.assertEqual(len(HexachromixState(hfen='RY1/4/5/4/3 G MRY').get_legal_moves()), 18)
        self.assertEqual(len(HexachromixState(hfen='yY1/4/5/4/3 C MRY').get_legal_moves()), 18)
        self.assertEqual(len(HexachromixState(hfen='yg1/4/5/4/3 B MRY').get_legal_moves()), 17)
        self.assertEqual(len(HexachromixState(hfen='ygB/4/5/4/3 M MRY').get_legal_moves()), 16)
        self.assertEqual(len(HexachromixState(hfen='ygB/M3/5/4/3 R MRY').get_legal_moves()), 16)
        self.assertEqual(len(HexachromixState(hfen='ygm/M3/5/4/3 Y MRY').get_legal_moves()), 17)
        self.assertEqual(len(HexachromixState(hfen='Ygm/M3/5/4/3 G MRY').get_legal_moves()), 16)

    def test_make_move(self):
        state = HexachromixState(hfen='3/4/5/4/3 R R')
        for _ in range(8): state = state.make_move(state.get_legal_moves()[0])
        self.assertEqual(state.hfen, 'Ygm/M3/5/4/3 G R')

    def test_is_terminal(self):
        self.assertTrue(HexachromixState(hfen='R2/R3/m4/R3/y2 Y MRY').is_terminal())
        self.assertTrue(HexachromixState(hfen='3/4/yGcyG/4/3 C MR').is_terminal())
        self.assertTrue(HexachromixState(hfen='3/4/Bcmmm/4/3 M MR').is_terminal())
        self.assertTrue(HexachromixState(hfen='1bR/Yb1y/mYCrM/Bygy/YC1 B MRY').is_terminal())
        self.assertTrue(HexachromixState(hfen='RRR/RRRR/RRRRR/RRRR/RRR Y MRY').is_terminal())

        self.assertFalse(HexachromixState(hfen='3/4/5/4/3 R MRY').is_terminal())
        self.assertFalse(HexachromixState(hfen='3/4/5/4/3 R MR').is_terminal())
        self.assertFalse(HexachromixState(hfen='GC1/BMRC/2R1c/MMYY/1BY C MRY').is_terminal()) # This one used to fail for some implementations of C, due to differing default char type signedness.
        self.assertFalse(HexachromixState(hfen='R2/R3/m4/R3/y2 R MRY').is_terminal())

    def test_get_reward(self):
        win = HexachromixState(hfen='RRR/RRRR/RRRRR/RRRR/RRR Y MRY').get_reward()
        draw = HexachromixState(hfen='RRR/RRRR/RRRRR/RRRR/RRR R MRY').get_reward()
        self.assertGreater(win, draw)

    def test_has_path(self):
        self.assertTrue(HexachromixState(hfen='RRR/RRRR/RRRRR/RRRR/RRR Y MRY').has_path())
        self.assertFalse(HexachromixState(hfen='RRR/RRRR/RRRRR/RRRR/RRR R MRY').has_path())
