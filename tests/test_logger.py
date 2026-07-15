from garlicsmtp.logger import Logger


def test_logger_info(capsys):

    logger = Logger()

    logger.info("hello")

    captured = capsys.readouterr()

    assert captured.out == "hello\n"