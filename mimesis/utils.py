# utils.py

import collections
import functools
import json
import os.path as path
import urllib.request as request
from random import choice

from mimesis.exceptions import (
    UnexpectedGender,
    UnsupportedLocale,
)
import mimesis.settings as settings
import mimesis.typing as types

__all__ = ['pull', 'download_image', 'locale_info', 'check_gender']

PATH = path.abspath(path.join(path.dirname(__file__), 'data'))


def locale_info(locale: str) -> str:
    """Return name (in english) or local name of the locale

    :param locale: Locale abbreviation.
    :type locale: str
    :returns: Locale name.
    """
    locale = locale.lower()
    supported = settings.SUPPORTED_LOCALES

    if locale not in supported:
        raise UnsupportedLocale('Locale %s is not supported' % locale)

    return supported[locale]['name']


def luhn_checksum(num: str) -> str:
    """Calculate a checksum for num using the Luhn algorithm.

    :param num: The number to calculate a checksum for as a string.
    :returns: Checksum for number.
    """
    check = 0
    for i, s in enumerate(reversed([x for x in num])):
        sx = int(s)
        sx = sx * 2 if i % 2 == 0 else sx
        sx = sx - 9 if sx > 9 else sx
        check += sx
    return str(check * 9 % 10)


def update_dict(initial: types.JSON, other: types.Mapping) -> types.JSON:
    """Recursively update a dictionary.

    .. note:: update_dict - is internal function of `mimesis`.

    :param initial: Dict to update.
    :param other: Dict to update from.
    :return: Updated dict.
    """
    for key, value in other.items():
        if isinstance(value, collections.Mapping):
            r = update_dict(initial.get(key, {}), value)
            initial[key] = r
        else:
            initial[key] = other[key]
    return initial


@functools.lru_cache(maxsize=None)
def pull(file: str, locale: str = 'en') -> types.JSON:
    """Open json file file and get content from file and memorize result using
     lru_cache.

    .. note:: pull - is internal function, please do not use this function
    outside the module 'mimesis'.

    :param file: The name of file.
    :param locale: Locale.
    :returns: The content of the file.

    :Example:

        >>> from mimesis.utils import pull
        >>> en = pull(file='datetime.json', locale='en')
        >>> isinstance(en, dict)
        True
        >>> en['day']['abbr'][0]
        'Mon.'
    """

    def get_data(locale_name: str) -> types.JSON:
        """Pull JSON data from file.

        :param locale_name: Name of locale to pull.
        :return: Dict of data from file
        """
        file_path = path.join(PATH + '/' + locale_name, file)
        # Needs explicit encoding for Windows
        with open(file_path, 'r', encoding='utf8') as f:
            return json.load(f)

    locale = locale.lower()

    if locale not in settings.SUPPORTED_LOCALES:
        raise UnsupportedLocale('Locale %s is not supported' % locale)

    master_locale = locale.split('-')[0]
    data = get_data(master_locale)

    # Handle sub-locales
    if '-' in locale:
        data = update_dict(data, get_data(locale))

    return data


def download_image(url: str = '', save_path: str = '',
                   unverified_ctx: bool = False) -> types.Union[None, str]:
    """Download image and save in current directory on local machine.

    :param url: URL to image.
    :param save_path: Saving path.
    :param unverified_ctx: Create unverified context.
    :return: Image name.
    """
    if unverified_ctx:
        import ssl
        ssl._create_default_https_context = ssl._create_stdlib_context

    if url is not None:
        image_name = url.rsplit('/')[-1]
        request.urlretrieve(url, save_path + image_name)
        return image_name
    return None


def check_gender(gender: types.Gender = 0) -> str:
    """Checking of the correctness of gender.

    :param gender: Gender.
    :return: Gender.
    """
    f, m = ('female', 'male')
    # When gender is None or 0, 9
    o = choice([f, m])

    options = {
        '0': o, '9': o,
        '1': m, '2': f,
        'f': f, 'm': m,
        f: f, m: m,
    }

    if gender is None:
        return o

    supported = sorted(options)
    gender = str(gender).lower()

    if gender not in supported:
        raise UnexpectedGender(
            'Gender must be {}.'.format(', '.join(supported)))

    return options[gender]
