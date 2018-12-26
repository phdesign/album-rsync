# -*- coding: utf-8 -*-
#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock, patch, call
from urllib.error import URLError
import pytest
import tests.helpers    #pylint: disable=unused-import
from album_rsync.resiliently import Resiliently

class TestResiliently:

    def setup_method(self):
        self.sleep_patch = patch('album_rsync.throttle.time.sleep', create=True)
        self.mock_sleep = self.sleep_patch.start()

        self.config = MagicMock()
        self.config.verbose = False
        self.config.throttling = 0
        self.callback = MagicMock()
        self.callback.__name__ = 'foo'

    def teardown_method(self):
        self.sleep_patch.stop()

    def test_should_make_remote_call(self):
        resiliently = Resiliently(self.config)
        resiliently.call(self.callback, 'a', b='b')

        self.callback.assert_called_once_with('a', b='b')

    def test_should_retry_once_with_backoff(self):
        self.config.retry = 1
        self.callback.side_effect = self.throw_errors(1)
        resiliently = Resiliently(self.config)
        resiliently.call(self.callback, 'a', b='b')

        self.callback.assert_has_calls_exactly([
            call('a', b='b'),
            call('a', b='b')
        ])

    def test_should_retry_specified_times(self):
        self.config.retry = 3
        self.callback.side_effect = self.throw_errors(3)
        resiliently = Resiliently(self.config)
        resiliently.call(self.callback, 'a', b='b')

        self.callback.assert_has_calls_exactly([
            call('a', b='b'),
            call('a', b='b'),
            call('a', b='b'),
            call('a', b='b')
        ])
        assert self.mock_sleep.call_count == 3, \
            f"Expected call_count of 3, was {self.mock_sleep.call_count}. Recieved {self.mock_sleep.call_args_list}"

    def test_should_fail_once_retry_exceeded(self):
        self.config.retry = 2
        self.callback.side_effect = self.throw_errors(3)
        resiliently = Resiliently(self.config)

        with pytest.raises(URLError):
            resiliently.call(self.callback, 'a', b='b')

        self.callback.assert_has_calls_exactly([
            call('a', b='b'),
            call('a', b='b'),
            call('a', b='b')
        ])

    def test_should_throttle_consecutive_calls(self):
        time_patch = patch('album_rsync.throttle.time.time', create=True)
        mock_time = time_patch.start()
        self.config.throttling = 10
        resiliently = Resiliently(self.config)

        mock_time.return_value = 0
        resiliently.call(self.callback, 'a', b='b')
        mock_time.return_value = 1
        resiliently.call(self.callback, 'a', b='b')
        mock_time.return_value = 6
        resiliently.call(self.callback, 'a', b='b')

        self.mock_sleep.assert_has_calls_exactly([
            call(9),
            call(5)
        ])
        time_patch.stop()

    def test_should_throttle_consecutive_calls_across_multiple_functions(self):
        time_patch = patch('album_rsync.throttle.time.time', create=True)
        mock_time = time_patch.start()
        self.config.throttling = 10
        callback2 = MagicMock()
        callback2.__name__ = 'bar'
        resiliently = Resiliently(self.config)

        mock_time.return_value = 0
        resiliently.call(self.callback, 'a', b='b')
        mock_time.return_value = 1
        resiliently.call(callback2, 'a', b='b')
        mock_time.return_value = 6
        resiliently.call(self.callback, 'a', b='b')

        self.mock_sleep.assert_has_calls_exactly([
            call(9),
            call(5)
        ])
        time_patch.stop()

    def test_should_not_throttle_if_timeout_passed(self):
        time_patch = patch('album_rsync.throttle.time.time', create=True)
        mock_time = time_patch.start()
        self.config.throttling = 10
        resiliently = Resiliently(self.config)

        mock_time.return_value = 0
        resiliently.call(self.callback, 'a', b='b')
        mock_time.return_value = 11
        resiliently.call(self.callback, 'a', b='b')

        self.mock_sleep.assert_not_called()
        time_patch.stop()

    def throw_errors(self, num):
        for _ in range(num):
            yield URLError('Bang!')
        yield True
