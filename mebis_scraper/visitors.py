class LernplattformFilterVisitor:
    def __init__(self, acceptor, filter_dict):
        self.acceptor = acceptor
        self.filter = filter_dict
        self.current_course = None
        self.current_subcourse = None
        self.current_subject = None

        self.current_subject_filter = None

    def enter_course(self, name):
        # print(name)
        if name in self.filter:
            self.current_course = name
            return True

        return False

    def exit_course(self):
        self.current_course = None

    def enter_subcourse(self, name):
        # print(f'enter sc: {name}')
        if name in self.filter[self.current_course]['subcourses']:
            self.current_subcourse = name
            return True

        return False

    def exit_subcourse(self):
        # print(f'exit sc: {self.current_subcourse}')
        self.current_subcourse = None

    def enter_subject(self, name):
        # print(self.filter[self.current_course])
        # print(self.current_subcourse)
        nfilter = None
        if self.current_subcourse is not None:
            nfilter = (self.filter[self.current_course]
                       ['subcourses'][self.current_subcourse]
                       ['subjects'])
        else:
            nfilter = self.filter[self.current_course]['subjects']

        if name in nfilter:
            self.current_subject = name
            return True

        return False

    def exit_subject(self):
        self.current_subject = None

    def accept_activity(self, activity, auth, driver):
        self.acceptor.accept_activity(
            self.current_course, self.current_subcourse,
            self.current_subject,
            activity, auth, driver)
