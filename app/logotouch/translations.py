from os.path import join, dirname
import gettext

locale_dir = join(dirname(__file__), '..', 'data', 'locales')
fr = gettext.translation('logotouch', locale_dir,
    languages=['fr'])
en = gettext.translation('logotouch', locale_dir,
    languages=['en'])

_ = fr.ugettext
