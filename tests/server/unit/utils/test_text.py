from app.utils.text import check_email


def test_check_email() -> None:
    valid_email = "test@test.com"
    valid_email_upper = "TEST@TEST.COM"

    assert check_email(valid_email) == valid_email
    assert check_email(valid_email_upper) == valid_email
