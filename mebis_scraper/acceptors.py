import logging
import os.path
import shutil

from .exceptions import (UncompletableActivityException,
                         UnsupportedActivityException)
from selenium_scraping.download import await_download


class LernplattformCompletionFilterAcceptor:
    def __init__(self, acceptor, desired_completion_state=False):
        self.acceptor = acceptor
        self.complete_filter = desired_completion_state

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        if activity.get_complete_button_state_false() == self.complete_filter:
            self.acceptor.accept_activity(course, subcourse, subj, activity,
                                          auth, driver)


class LernplattformCompletionSyncAcceptor:
    def __init__(self, completion_dict):
        self.completion_dict = completion_dict

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        state = None
        activity_name = activity.get_name()
        try:
            if subcourse is None:
                state = self.completion_dict[course][subj][activity_name]
            else:
                state = (self.completion_dict[course][subcourse][subj]
                         [activity_name])
        except KeyError:
            return  # an unknown activity is normal and shouldn't be changed

        try:
            activity.set_complete_button_state(state)
        except UncompletableActivityException:
            logging.warning(f'{activity_name} cannot be completed')


class LernplattformDownloadAcceptor:
    def __init__(self, path, driver_download_dir):
        self.path = path
        self.dl_dir = driver_download_dir

    def make_path(self, *args):
        def escape_filename(filename):
            return filename.replace('/', '_')

        newpath = self.path

        for filename in args:
            if filename is not None:
                newpath = os.path.join(newpath, escape_filename(filename))

        return newpath

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        activity_name = activity.get_name()
        activity_type = activity.get_type()
        target_file = self.make_path(course, subcourse, subj, activity_name)

        logging.info(f'Download activity \'{activity_name}\''
                     '({activity_type})')

        if not os.path.exists(target_file):
            try:
                res = activity.download(driver, auth)
            except UnsupportedActivityException:
                logging.warning(f'Cannot download activity {activity_name}: '
                                f'its type ({activity_type}) '
                                'is unsupported.')
                return

            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            if res is None:
                await_download(self.dl_dir)

                download_file = os.listdir(self.dl_dir)[0]
                src_file = os.path.join(self.dl_dir, download_file)

                shutil.move(src_file, target_file)
            else:
                with open(target_file, 'w') as out:
                    out.write(res)


class LernplattformListerAcceptor:
    def __init__(self):
        self.result = {}

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        res = {
            'name': activity.get_name(),
            'type': activity.get_type(),
            'complete': activity.get_complete_button_state_none(),
            'subtext': activity.get_subtext()
        }

        if subcourse is None:
            self.result \
                .setdefault(course, {}) \
                .setdefault(subj, []).append(res)
        else:
            self.result \
                .setdefault(course, {}) \
                .setdefault(subcourse, {}) \
                .setdefault(subj, []).append(res)


class LernplattformFlatListerAcceptor:
    def __init__(self):
        self.result = []

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        self.result.append({
            'name': activity.get_name(),
            'type': activity.get_type(),
            'complete': activity.get_complete_button_state_none(),
            'subtext': activity.get_subtext(),

            'course': course.get_name(),
            'subcourse': subcourse.get_name(),
            'subject': subj.get_name()
        })


class LernplattformCompositeAcceptor:
    def __init__(self, acceptors=[]):
        self.acceptors = acceptors

    def add_acceptor(self, acceptor):
        self.acceptors.append(acceptor)

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        for acceptor in self.acceptors:
            acceptor.accept_activity(course, subcourse, subj,
                                     activity, auth, driver)
