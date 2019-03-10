#pylint: disable=wrong-import-position
import os, sys
from io import StringIO
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock, patch
import pytest
from album_rsync.__main__ import main

class TestVertical:

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    @pytest.mark.focus
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_expected_results_when_syncing(self, mock_stdout, mock_stderr):
        testargs = ["album-rsync", "fake", "--list-only"]
        with patch.object(sys, 'argv', testargs):
            with patch('time.sleep'):
                main()
                assert mock_stderr.getvalue().startswith("3 directories, 5 files read in")
                assert mock_stdout.getvalue() == """\
├─── A Folder
│   └─── A File
│   
├─── B Folder
│   ├─── A File
│   └─── B File
│   
└─── C Folder
    ├─── A File
    └─── B File
"""
