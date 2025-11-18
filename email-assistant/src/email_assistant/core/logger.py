import logging

class Logger:
    _is_configured = False     # Prevent double configuration

    @staticmethod
    def get_logger(name: str = None):
        if not Logger._is_configured:
            Logger._configure()
            Logger._is_configured = True

        return logging.getLogger(name)

    @staticmethod
    def _configure():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
