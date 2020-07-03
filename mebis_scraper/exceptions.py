class MebisException(Exception):
    def __init__(self, message='''MebisScraper has encountered an error.'''):
        self.message = message

    def __str__(self):
        return self.message


class LernplattformException(MebisException):
    pass


class UnsupportedActivityException(LernplattformException):
    def __init__(self, activity_type):
        super().__init__(f'Activities of type {activity_type} can\'t'
              'currently be downloaded.')
        self.activity_type = activity_type
