# -*- coding: utf-8 -*-
#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import tests.helpers    #pylint: disable=unused-import
from album_rsync.enumerate_peek import enumerate_peek

class TestEnumeratePeek:

    def test_should_return_empty_iterator_given_empty_iterator(self):
        mock_generator = iter(())
        was_called = False
        for _, _ in enumerate_peek(mock_generator):
            was_called = True
        assert not was_called, "Expected no enumeration of empty iterator"

    def test_has_next_should_return_true_given_more_items_exist(self):
        mock_generator = iter(range(2))
        _, has_next = next(enumerate_peek(mock_generator))
        assert has_next

    def test_has_next_should_return_false_given_no_more_items_exist(self):
        mock_generator = iter(range(1))
        _, has_next = next(enumerate_peek(mock_generator))
        assert not has_next

    def test_should_iterate_over_all_items_given_iterator(self):
        mock_generator = iter(range(3))
        call_count = 0
        for _, _ in enumerate_peek(mock_generator):
            call_count += 1
        assert call_count == 3

    def test_should_iterate_over_all_items_given_list(self):
        my_list = [1, 2, 3]
        call_count = 0
        for _, _ in enumerate_peek(my_list):
            call_count += 1
        assert call_count == 3
