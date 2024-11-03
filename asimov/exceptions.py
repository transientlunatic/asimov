class DescriptionException(Exception):
    """Exception for event description problems."""

    def __init__(self, message, production=None):
        super(DescriptionException, self).__init__(message)
        self.message = message
        self.production = production
