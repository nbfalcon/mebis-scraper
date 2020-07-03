import tempfile

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

def make_firefox_profile():
    AUTODOWNLOAD_MIMETYPES = [
        "audio/aac",
        "application/x-abiword",
        "application/x-freearc",
        "video/x-msvideo",
        "application/vnd.amazon.ebook",
        "application/octet-stream",
        "image/bmp",
        "application/x-bzip",
        "application/x-bzip2",
        "application/x-csh",
        "text/css",
        "text/csv",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # noqa: E501
        "application/vnd.ms-fontobject",
        "application/epub+zip",
        "application/gzip",
        "image/gif",
        "image/vnd.microsoft.icon",
        "text/calendar",
        "application/java-archive",
        "image/jpeg",
        "application/json",
        "application/ld+json",
        "text/javascript",
        "audio/mpeg",
        "video/mpeg",
        "application/vnd.apple.installer+xml",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.text",
        "audio/ogg",
        "video/ogg",
        "application/ogg",
        "audio/opus",
        "font/otf",
        "image/png",
        "application/pdf",
        "application/x-httpd-php",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # noqa: E501
        "application/vnd.rar",
        "application/rtf",
        "application/x-sh",
        "image/svg+xml",
        "application/x-shockwave-flash",
        "application/x-tar",
        "image/tiff",
        "video/mp2t",
        "font/ttf",
        "text/plain",
        "application/vnd.visio",
        "audio/wav",
        "audio/webm",
        "video/webm",
        "image/webp",
        "font/woff",
        "font/woff2",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.mozilla.xul+xml",
        "application/zip",
        "application/x-7z-compressed"
    ]
    AUTODOWNLOAD_MIMETYPES_CSV = ','.join(AUTODOWNLOAD_MIMETYPES)
    USERAGENT = ("Mozilla/5.0"
                 " (Windows NT 10.0; Win64; x64; rv:77.0)"
                 " Gecko/20100101 Firefox/77.0")

    dl_dir = tempfile.mkdtemp()

    prefs = {
        'general.useragent.override': USERAGENT,

        'browser.download.folderList': 2,
        'browser.download.manager.showWhenStarting': False,
        'browser.helperApps.alwaysAsk.force': False,
        'browser.helperApps.neverAsk.saveToDisk': AUTODOWNLOAD_MIMETYPES_CSV,

        'browser.download.manager.closeWhenDone': False,
        'browser.download.manager.focusWhenStarting': False,

        'browser.download.dir': dl_dir,
    }

    profile = webdriver.FirefoxProfile()
    for (pref, value) in prefs.items():
        profile.set_preference(pref, value)

    options = FirefoxOptions()
    options.headless = True

    return (dl_dir, webdriver.Firefox(firefox_profile=profile,
                                      firefox_options=options))
