import logging
import os
import os.path
import shutil

from .exceptions import UnsupportedActivityException


class LernplattformListerAcceptor:
    def __init__(self):
        self.res = {}

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        name = activity.get_name()

        if subcourse is None:
            self.res \
                .setdefault(course, {}) \
                .setdefault(subj, []).append(name)
        else:
            self.res \
                .setdefault(course, {}) \
                .setdefault(subcourse, {}) \
                .setdefault(subj, []).append(name)


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

        if not os.path.exists(target_file):
            try:
                res = activity.download(driver, auth)
            except UnsupportedActivityException:
                logging.warning(f'Cannot download activity {activity_name}: '
                                f'its type ({activity_type}) '
                                'is unsupported.')
                return

            os.makedirs(os.path.dirname(target_file))

            if res is None:
                download_file = os.listdir(self.dl_dir)[0]
                shutil.move(download_file, target_file)
            else:
                with open(target_file, 'w') as out:
                    out.write(res)

            logging.info(f'Downloaded activity \'{activity_name}\''
                         '({activity_type})')


class LernplattformCompositeAcceptor:
    def __init__(self, acceptors=[]):
        self.acceptors = acceptors

    def add_acceptor(self, acceptor):
        self.acceptors.append(acceptor)

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        for acceptor in self.acceptors:
            acceptor.accept_activity(course, subcourse, subj,
                                     activity, auth, driver)
