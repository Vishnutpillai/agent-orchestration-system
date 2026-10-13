
import unittest
from unittest.mock import Mock, patch

from openai import RateLimitError

from app.core import llm


def make_rate_limit_error():
    """Build a RateLimitError without making an actual API request."""
    response = Mock()
    response.status_code = 429
    response.headers = {}
    response.request = Mock()
    return RateLimitError(
        "Rate limit exceeded",
        response=response,
        body={"error": {"message": "Rate limit exceeded"}},
    )


class TestLLMReliability(unittest.TestCase):
    @patch("app.core.llm.time.sleep")
    @patch("app.core.llm.random.randint", return_value=0)
    @patch("app.core.llm.client.chat.completions.create")
    def test_retries_rate_limit_then_succeeds(
        self, mock_create, mock_jitter, mock_sleep
    ):
        expected_response = Mock()
        mock_create.side_effect = [
            make_rate_limit_error(),
            expected_response,
        ]

        result = llm._create_with_retry(
            model="test-model",
            messages=[{"role": "user", "content": "hello"}],
        )

        self.assertIs(result, expected_response)
        self.assertEqual(mock_create.call_count, 2)
        mock_sleep.assert_called_once_with(20)

    @patch("app.core.llm.time.sleep")
    @patch("app.core.llm.random.randint", return_value=0)
    @patch("app.core.llm.client.chat.completions.create")
    def test_stops_after_maximum_rate_limit_attempts(
        self, mock_create, mock_jitter, mock_sleep
    ):
        mock_create.side_effect = make_rate_limit_error()

        with self.assertRaises(RateLimitError):
            llm._create_with_retry(
                model="test-model",
                messages=[{"role": "user", "content": "hello"}],
            )

        self.assertEqual(mock_create.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("app.core.llm.time.sleep")
    @patch("app.core.llm.client.chat.completions.create")
    def test_does_not_retry_unrelated_errors(self, mock_create, mock_sleep):
        mock_create.side_effect = ValueError("Invalid request")

        with self.assertRaisesRegex(ValueError, "Invalid request"):
            llm._create_with_retry(
                model="test-model",
                messages=[{"role": "user", "content": "hello"}],
            )

        mock_create.assert_called_once()
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
