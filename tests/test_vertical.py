#pylint: disable=wrong-import-position
import os, sys
from io import StringIO
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import patch, Mock
import pytest
from album_rsync.__main__ import main

@patch('time.sleep', Mock())
@patch('time.time', Mock(return_value=0.0))
@patch('sys.stderr', new_callable=StringIO)
@patch('sys.stdout', new_callable=StringIO)
class TestVertical:

    def test_should_list_files_as_tree(self, mock_stdout, mock_stderr):
        testargs = ["album-rsync", "fake", "--list-only"]
        with patch.object(sys, 'argv', testargs):
            main()
            assert mock_stderr.getvalue() == "3 directories, 5 files read in 0.0 sec\n"
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

    def test_should_list_files_as_csv(self, mock_stdout, mock_stderr):
        testargs = ["album-rsync", "fake", "--list-only", "--list-format=csv"]
        with patch.object(sys, 'argv', testargs):
            main()
            assert mock_stderr.getvalue() == "\ndone in 0.0 sec\n"
            assert mock_stdout.getvalue() == """\
Folder,Filename,Checksum
A Folder,A File,
B Folder,A File,
B Folder,B File,
C Folder,A File,
C Folder,B File,
"""

    def test_should_sync(self, mock_stdout, mock_stderr):
        testargs = ["album-rsync", "fake", "fake"]
        with patch.object(sys, 'argv', testargs):
            main()
            assert mock_stderr.getvalue() == """\
building folder list...

transferred 3 file(s), skipped 2 files(s) that already exist in 0.0 sec
"""

            assert mock_stdout.getvalue() == """\
A Folder/
B Folder/
B Folder/A File
B Folder/B File
C Folder/
C Folder/A File
"""

    def test_should_mirror(self, mock_stdout, mock_stderr):
        testargs = ["album-rsync", "fake", "fake", "--delete", "-n"]
        with patch.object(sys, 'argv', testargs):
            main()
            assert mock_stderr.getvalue() == """\
dry run enabled, no files will be copied
building folder list...

transferred 3 file(s), skipped 2 files(s) that already exist, deleted 1 additional files(s) in 0.0 sec
"""

            assert mock_stdout.getvalue() == """\
A Folder/
B Folder/
B Folder/A File
B Folder/B File
C Folder/
C Folder/A File
deleting D Folder/A File
deleting D Folder/
"""
