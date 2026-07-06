

class NotificationServiceError(Exception):
    pass


class NotificationNotFoundError(NotificationServiceError):
    pass


class NotificationRetryNotAllowedError(NotificationServiceError):
    pass