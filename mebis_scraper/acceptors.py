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
                state = (self.completion_dict[course][subj][activity_name]
                         ['complete'])
            else:
                state = (self.completion_dict[course][subcourse][subj]
                         [activity_name]['complete'])
        except KeyError:
            return  # an unknown activity is normal and shouldn't be changed

        if state is not None:
            try:
                activity.set_complete_button_state(state)
            except UncompletableActivityException:
                logging.getLogger('activity_sync') \
                       .warning(f'{activity_name} cannot be completed')


class LernplattformDownloadAcceptor:
    def __init__(self, path, driver_download_dir):
        self.out_dir = path
        self.src_dir = driver_download_dir

    def make_path(basedir, *args):
        def escape_filename(filename):
            return filename.replace('/', '_')

        paths = filter(lambda f: f is not None, args)
        return os.path.join(basedir, *map(escape_filename, paths))

    def find_activity(target_file):
        activity_path = os.path.dirname(target_file)
        activity_name = os.path.basename(target_file)

        try:
            for activity_file in os.listdir(activity_path):
                (name, ext) = os.path.splitext(activity_file)

                if name == activity_name:
                    return os.path.join(activity_path, activity_file)
        except FileNotFoundError:
            # if its directory doesn't exist, the activity file can't either,
            # so return None (below)
            pass

        return None

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        activity_name = activity.get_name()
        activity_type = activity.get_type()

        target_file = self.__class__.make_path(
            self.out_dir, course, subcourse, subj, activity_name)

        if self.__class__.find_activity(target_file) is None:
            logging.getLogger('download').info(
                f'Download activity \'{activity_name}\' ({activity_type})')

            try:
                res = activity.download(driver, auth)
            except UnsupportedActivityException:
                logging.getLogger('download').warning(
                    f'Cannot download activity \'{activity_name}\': '
                    f'its type ({activity_type}) is unsupported.')
                return

            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            if res is None:
                await_download(self.src_dir)

                download_file = os.listdir(self.src_dir)[0]
                src_file = os.path.join(self.src_dir, download_file)

                ext = os.path.splitext(download_file)[1]
                shutil.move(src_file, target_file + ext)
            else:
                TYPE_EXT_MAPPING = {
                    'modtype_page': '.page',
                    'modtype_label': '.label',
                    'modtype_url': '.url'
                }
                ext = TYPE_EXT_MAPPING[activity_type]

                with open(target_file + ext, 'w') as out:
                    out.write(res)
        else:
            logging.getLogger('download').info(
                f'Skip download of \'{activity_name}\': already downloaded')


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

            'course': course,
            'subcourse': subcourse,
            'subject': subj
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
