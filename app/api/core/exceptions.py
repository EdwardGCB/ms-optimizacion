class DocumentReprocessStatusNotValidException(Exception):

    def __init__(self, uuid: str, current_status: str):
        super().__init__(
            f"The document '{uuid}' don't have a valid status to be processed (current status: '{current_status}')")


class NotFound(Exception):

    def __init__(self, message: str):
        super().__init__(message)
