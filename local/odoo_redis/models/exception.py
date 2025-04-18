class RateLimitException(Exception):

    def __init__(self, message, period_remaining):
        super(RateLimitException, self).__init__(message)
        self.period_remaining = period_remaining
