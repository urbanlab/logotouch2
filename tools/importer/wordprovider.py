import csv
import os

class AbstractWordProvider(object):

    def __init__(self):
        #TODO:  nedd type..like verb, adjective, noun etc?!
        self.data = {}
        self.is_verb = False
        self.wtype = 'verbe' # verbe, mot, adverbe
        self.word = 'walk'
        self.tense = 1 # 0=past, 1=present, 2=future
        self.show_person = True
        self.person = 1
        self.pronouns = [u'', u'Je', u'Tu', u'Il', u'Nous', u'Vous', u'Ils']
        self.pronouns_word = [u'un', u'le', u'ce', u'une', u'la', u'cette',
                              u'des', u'les', u'ces', u'ma', u'sa', u'ta',
                              u'nos', u'notre', u'leurs', u'leur']
        self.zoom = 0
        self.maxzoom = 0
        self.minzoom = 0
        self.maxsynonym = 0
        self.synonym = 0
        self.antonym = False

    def __str__(self):
        return self.pronouns[self.person] + self.conjugate() + ' ' + str(self.tense)

    @property
    def use_pronouns(self):
        return self.wtype in ('verbe', 'mot')

    @property
    def use_time(self):
        return self.wtype in ('verbe', )

    def conjugate(self):
        #TODO: return right word form root with time and person
        return self.word

    def get_synonym(self):
        return 'wander'

    def get_antonym(self):
        return 'stand'

    def do_zoomin(self):
        zoom = min(self.zoom + 1, self.maxzoom)
        if self.zoom == zoom:
            return
        self.zoom = zoom
        return True

    def do_zoomout(self):
        zoom = max(self.zoom - 1, self.minzoom)
        if self.zoom == zoom:
            return
        self.zoom = zoom
        return True

    def do_synonym(self):
        synonym = (self.synonym + 1) % self.maxsynonym
        if self.synonym == synonym:
            return
        self.synonym = synonym
        return True

    def do_antonym(self):
        self.antonym = not self.antonym
        return True

    def do_time_next(self):
        if not self.use_time:
            return
        tense = min(2, self.tense + 1)
        if tense == self.tense:
            return
        self.tense = tense
        return True

    def do_time_previous(self):
        if not self.use_time:
            return
        tense = max(0, self.tense - 1)
        if tense == self.tense:
            return
        self.tense = tense
        return True

    def toggle_person(self):
        self.show_person = not self.show_person

    def do_person_next(self):
        if not self.use_pronouns:
            return
        pronouns = self.pronouns if self.wtype == 'verbe' else self.pronouns_word
        person = min(len(pronouns) - 1, self.person + 1)
        if person == self.person:
            return
        self.person = person
        return True

    def do_person_previous(self):
        if not self.use_pronouns:
            return
        person = max(0, self.person - 1)
        if person == self.person:
            return
        self.person = person
        return True


class CSVWordProvider(AbstractWordProvider):
    def __init__(self, filename):
        super(CSVWordProvider, self).__init__()
        self.filename = filename
        self.load()
        ext = os.path.basename(filename).split('-')[0]
        self.wtype = ext

    def load(self):
        def norm(title):
            title = title.lower()
            c = title.split()
            if len(c) == 0:
                return title
            if len(c) != 2:
                if c[0] != 'infinitif':
                    title = title.replace('nom', 'name')
                    title = title.replace('adverbe', 'name')
                    return title
            if c[0] == 'infinitif':
                a = c[0]
                b = ''
            else:
                a, b = c
                a = a.replace('pr\xc3\xa9sent', 'present')
                a = a.replace('futur', 'future')
                a = a.replace('imparfait', 'past')
                a = a.replace('imparfai', 'past')
            d = {'': 0, 'je': 1, 'tu': 2, 'il': 3, 'nous': 4, 'vous': 5, 'ils': 6}
            return '%s_%s' % (a, d[b.lower()])
        rows = []
        titles = None
        with open(self.filename, 'rb') as fd:
            data = csv.reader(fd)
            for row in data:
                if titles is None:
                    titles = row
                else:
                    rows.append(row)

        for i in xrange(len(titles)):
            titles[i] = titles[i].lower().replace('-', '')

        self.titles = titles
        for row in rows:
            self.data[norm(row[0])] = row[1:]

        # count zoomin
        for t in titles:
            if t.startswith('zoomin'):
                self.maxzoom += 1
            if t.startswith('zoomout'):
                self.minzoom -= 1
            if t.startswith('secouer'):
                self.maxsynonym += 1

    def get(self):
        title = 'mot'
        if self.antonym:
            title = 'contraire'
        else:
            # zoom in
            if self.zoom > 0:
                z = self.zoom - 1
                if z == 0:
                    title = 'zoomin'
                else:
                    title = 'zoomin%d' % z
            # zoom out
            elif self.zoom < 0:
                z = abs(self.zoom) - 1
                if z == 0:
                    title = 'zoomout'
                else:
                    title = 'zoomout%d' % z
            # synonym
            elif self.synonym != 0:
                title = 'secouer%d' % self.synonym

        # tense ?
        if self.wtype == 'verbe':
            a = {0: 'past', 1: 'present', 2: 'future'}
            if self.tense != 1: # other than present
                self.person = max(1, self.person)
                tense = '%s_%d' % (a[self.tense], self.person)
            elif self.person > 0:
                tense = 'present_%d' % self.person
            else:
                tense = 'infinitif_0'
        else:
            tense = 'name'

        tidx = self.titles.index(title) - 1
        word = self.data[tense][tidx]
        word = word.decode('utf8')

        if self.show_person and self.use_pronouns:
            if self.wtype == 'verbe':
                return self.pronouns[self.person] + u' ' + word
            else:
                return self.pronouns_word[self.person] + u' ' + word
        else:
            return word
