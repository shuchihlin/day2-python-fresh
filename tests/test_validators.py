import pytest
import math
from src.validators import (
    is_email,
    is_strong_password,
    clamp,
    normalize_email,
    is_valid_username,
)


class TestIsEmail:
    def test_valid_email_simple(self):
        assert is_email("user@example.com") is True

    def test_valid_email_with_dots(self):
        assert is_email("john.doe@example.co.uk") is True

    def test_valid_email_with_plus(self):
        assert is_email("user+tag@example.com") is True

    def test_invalid_email_no_at(self):
        assert is_email("userexample.com") is False

    def test_invalid_email_no_domain(self):
        assert is_email("user@") is False

    def test_invalid_email_no_tld(self):
        assert is_email("user@example") is False

    def test_invalid_email_spaces(self):
        assert is_email("user @example.com") is False

    def test_invalid_email_empty_string(self):
        assert is_email("") is False

    def test_invalid_email_not_string(self):
        assert is_email(123) is False

    def test_invalid_email_none(self):
        assert is_email(None) is False


class TestIsStrongPassword:
    def test_strong_password_all_requirements(self):
        assert is_strong_password("SecurePass123!") is True

    def test_strong_password_long(self):
        assert is_strong_password("VeryLongPassword123!WithSpecialChars@") is True

    def test_weak_password_no_uppercase(self):
        assert is_strong_password("lowercasepass123!") is False

    def test_weak_password_no_lowercase(self):
        assert is_strong_password("UPPERCASEPASS123!") is False

    def test_weak_password_no_digit(self):
        assert is_strong_password("NoDigitsHere!") is False

    def test_weak_password_no_special(self):
        assert is_strong_password("NoSpecialChars123") is False

    def test_weak_password_too_short(self):
        assert is_strong_password("Short1!") is False

    def test_weak_password_empty(self):
        assert is_strong_password("") is False

    def test_invalid_password_not_string(self):
        assert is_strong_password(123) is False

    def test_invalid_password_none(self):
        assert is_strong_password(None) is False

    def test_strong_password_exactly_8_chars(self):
        assert is_strong_password("Pass123!") is True

    # TODO: is_strong_password('пароль1Пароль') - non-Latin scripts rejected by ASCII-only regex
    def test_strong_password_cyrillic(self):
        result = is_strong_password("пароль1Пароль!")
        # Current behavior: returns False because regex only matches [A-Z] and [a-z]
        assert result is False


class TestClamp:
    def test_clamp_value_in_range(self):
        assert clamp(5, 1, 10) == 5

    def test_clamp_value_below_range(self):
        assert clamp(0, 1, 10) == 1

    def test_clamp_value_above_range(self):
        assert clamp(15, 1, 10) == 10

    def test_clamp_min_boundary(self):
        assert clamp(1, 1, 10) == 1

    def test_clamp_max_boundary(self):
        assert clamp(10, 1, 10) == 10

    def test_clamp_negative_range(self):
        assert clamp(-5, -10, -1) == -5

    def test_clamp_negative_value_in_range(self):
        assert clamp(-5, -10, 0) == -5

    def test_clamp_zero_in_range(self):
        assert clamp(0, -10, 10) == 0

    def test_clamp_float_values(self):
        assert clamp(5.5, 1.0, 10.0) == 5.5

    # TODO: clamp(5, 10, 1) - inverted range doesn't error, just returns 10
    def test_clamp_inverted_range(self):
        result = clamp(5, 10, 1)
        # Current behavior: returns 10 (max_val) because value < min_val
        assert result == 10

    # TODO: clamp(NaN, 1, 10) - NaN comparisons have undefined behavior
    def test_clamp_with_nan(self):
        result = clamp(float('nan'), 1, 10)
        # Current behavior: NaN < 1 is False, NaN > 10 is False, so returns NaN
        assert math.isnan(result)


class TestNormalizeEmail:
    def test_normalize_uppercase(self):
        assert normalize_email("USER@EXAMPLE.COM") == "user@example.com"

    def test_normalize_mixed_case(self):
        assert normalize_email("John.Doe@Example.Com") == "john.doe@example.com"

    def test_normalize_already_lowercase(self):
        assert normalize_email("user@example.com") == "user@example.com"

    def test_normalize_empty_string(self):
        assert normalize_email("") == ""

    def test_normalize_with_spaces(self):
        assert normalize_email("USER WITH SPACE@EXAMPLE.COM") == "user with space@example.com"

    def test_normalize_not_string(self):
        assert normalize_email(123) is None

    def test_normalize_none(self):
        assert normalize_email(None) is None


class TestIsValidUsername:
    def test_valid_username_simple(self):
        assert is_valid_username("john_doe") is True

    def test_valid_username_with_numbers(self):
        assert is_valid_username("user123") is True

    def test_valid_username_all_underscore(self):
        assert is_valid_username("___") is True

    def test_valid_username_min_length(self):
        assert is_valid_username("abc") is True

    def test_valid_username_max_length(self):
        assert is_valid_username("a" * 20) is True

    def test_invalid_username_too_short(self):
        assert is_valid_username("ab") is False

    def test_invalid_username_too_long(self):
        assert is_valid_username("a" * 21) is False

    def test_invalid_username_empty(self):
        assert is_valid_username("") is False

    def test_invalid_username_with_space(self):
        assert is_valid_username("user name") is False

    def test_invalid_username_with_dash(self):
        assert is_valid_username("user-name") is False

    def test_invalid_username_with_special_chars(self):
        assert is_valid_username("user@name") is False

    def test_invalid_username_not_string(self):
        assert is_valid_username(123) is False

    def test_invalid_username_none(self):
        assert is_valid_username(None) is False

    def test_invalid_username_uppercase(self):
        assert is_valid_username("UserName") is True  # Actually valid - [a-zA-Z0-9_]+
