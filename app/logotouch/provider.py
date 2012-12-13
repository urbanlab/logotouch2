from json import loads
from kivy.event import EventDispatcher

class WordProvider(EventDispatcher):

    def __init__(self, data):
        super(WordProvider, self).__init__()
        self.data = data
        self.itype = int(data['type'])
        self.wtype = ['verbe', 'mot', 'adverbe'][self.itype]
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

        if self.wtype == 'verbe':
            title = 'present_1'
        else:
            title = 'name'
        self.maxzoom = len(loads(data[title]['zoomin']))
        self.minzoom = -len(loads(data[title]['zoomout']))
        self.maxsynonym = len(loads(data[title]['shake']))


    #def __str__(self):
    #    return self.pronouns[self.person] + ' ' + str(self.tense)

    @property
    def use_pronouns(self):
        return self.wtype in ('verbe', 'mot')

    @property
    def use_time(self):
        return self.wtype in ('verbe', )

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

    def get(self):
        title = 'normal'
        index = 0
        if self.antonym:
            title = 'opposite'
        else:
            # zoom in
            if self.zoom > 0:
                index = self.zoom - 1
                title = 'zoomin'
            # zoom out
            elif self.zoom < 0:
                index = abs(self.zoom) - 1
                title = 'zoomout'
            # synonym
            elif self.synonym != 0:
                index = self.synonym - 1
                title = 'shake'

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

        print 'GET WORD', (tense, title, index)
        word = loads(self.data[tense][title])[index]

        if self.show_person and self.use_pronouns:
            if self.wtype == 'verbe':
                return self.pronouns[self.person] + u' ' + word
            else:
                return self.pronouns_word[self.person] + u' ' + word
        else:
            return word

if __name__ == '__main__':
    data = {
            u'type': u'0',
            u'future_1': {
                u'normal': u'["vivrai"]',
                u'opposite': u'["mourrai"]',
                u'shake': u'["serai", "logerai", "camperai"]',
                u'zoomin': u'["existerai", "respirerai", "subsisterai"]',
                u'zoomout': u'["habiterai", "occuperai", "peuplerai"]'},
            u'future_2': {
                u'normal': u'["vivras"]',
                u'opposite': u'["mourras"]',
                u'shake': u'["seras", "logeras", "camperas"]',
                u'zoomin': u'["existeras", "respireras", "subsisteras"]',
                u'zoomout': u'["habiteras", "occuperas", "peupleras"]'},
            u'future_3': {
                u'normal': u'["vivra"]',
                u'opposite': u'["mourra"]',
                u'shake': u'["sera", "logera", "campera"]',
                u'zoomin': u'["existera", "respirera", "subsistera"]',
                u'zoomout': u'["habitera", "occupera", "peuplera"]'},
            u'future_4': {
                u'normal': u'["vivrons"]',
                u'opposite': u'["mourrons"]',
                u'shake': u'["serons", "logerons", "camperons"]',
                u'zoomin': u'["existerons", "respirerons", "subsisterons"]',
                u'zoomout': u'["habiterons", "occuperons", "peuplerons"]'},
            u'future_5': {
                u'normal': u'["vivrez"]',
                u'opposite': u'["mourrez"]',
                u'shake': u'["serez", "logerez", "camperez"]',
                u'zoomin': u'["existerez", "respirerez", "subsisterez"]',
                u'zoomout': u'["habiterez", "occuperez", "peuplerez"]'},
            u'future_6': {
                u'normal': u'["vivront"]',
                u'opposite': u'["mourront"]',
                u'shake': u'["seront", "logeront", "camperont"]',
                u'zoomin': u'["existeront", "respireront", "subsisteront"]',
                u'zoomout': u'["habiteront", "occuperont", "peupleront"]'},
            u'infinitif_0': {
                u'normal': u'["vivre"]',
                u'opposite': u'["mourir"]',
                u'shake': u'["\\u00eatre", "loger", "camper"]',
                u'zoomin': u'["exister", "respirer", "subsister"]',
                u'zoomout': u'["habiter", "occuper", "peupler"]'},
            u'past_1': {
                u'normal': u'["vivais"]',
                u'opposite': u'["mourais"]',
                u'shake': u'["\\u00e9tais", "logeais", "campais"]',
                u'zoomin': u'["existais", "respirais", "subsistais"]',
                u'zoomout': u'["habitais", "occupais", "peuplais"]'},
            u'past_2': {
                u'normal': u'["vivais"]',
                u'opposite': u'["mourais"]',
                u'shake': u'["\\u00e9tais", "logeais", "campais"]',
                u'zoomin': u'["existais", "respirais", "subsistais"]',
                u'zoomout': u'["habitais", "occupais", "peuplais"]'},
            u'past_3': {
                    u'normal': u'["vivait"]',
                u'opposite': u'["mourait"]',
                u'shake': u'["\\u00e9tait", "logeait", "campait"]',
                u'zoomin': u'["existait", "respirait", "subsistait"]',
                u'zoomout': u'["habitait", "occupait", "peuplait"]'},
            u'past_4': {
                    u'normal': u'["vivions"]',
                    u'opposite': u'["mourions"]',
                    u'shake': u'["\\u00e9tions", "logions", "campions"]',
                    u'zoomin': u'["existions", "respirions", "subsistions"]',
                    u'zoomout': u'["habitions", "occupions", "peuplions"]'},
            u'past_5': {
                    u'normal': u'["viviez"]',
                    u'opposite': u'["mouriez"]',
                    u'shake': u'["\\u00e9tiez", "logiez", "campiez"]',
                    u'zoomin': u'["existiez", "respiriez", "subsistiez"]',
                    u'zoomout': u'["habitiez", "occupiez", "peupliez"]'},
            u'past_6': {
                    u'normal': u'["vivaient"]',
                    u'opposite': u'["mouraient"]',
                    u'shake': u'["\\u00e9taient", "logeaient", "campaient"]',
                    u'zoomin': u'["existaient", "respiraient", "subsistaient"]',
                    u'zoomout': u'["habitaient", "occupaient", "peuplaient"]'},
            u'present_1': {u'normal': u'["vis"]',
                    u'opposite': u'["meurs"]',
                    u'shake': u'["suis", "loge", "campe"]',
                    u'zoomin': u'["existe", "respire", "subsiste"]',
                    u'zoomout': u'["habite", "occupe", "peuple"]'},
            u'present_2': {u'normal': u'["vis"]',
                    u'opposite': u'["meurs"]',
                    u'shake': u'["es", "loges", "campes"]',
                    u'zoomin': u'["existes", "respires", "subsistes"]',
                    u'zoomout': u'["habites", "occupes", "peuples"]'},
            u'present_3': {u'normal': u'["vit"]',
                    u'opposite': u'["meurt"]',
                    u'shake': u'["est", "loge", "campe"]',
                    u'zoomin': u'["existe", "respire", "subsiste"]',
                    u'zoomout': u'["habite", "occupe", "peuple"]'},
            u'present_4': {u'normal': u'["vivons"]',
                    u'opposite': u'["mourons"]',
                    u'shake': u'["sommes", "logeons", "campons"]',
                    u'zoomin': u'["existons", "respirons", "subsistons"]',
                    u'zoomout': u'["habitons", "occupons", "peuplons"]'},
            u'present_5': {u'normal': u'["vivez"]',
                    u'opposite': u'["mourez"]',
                    u'shake': u'["\\u00eates", "logez", "campez"]',
                    u'zoomin': u'["existez", "respirez", "subsistez"]',
                    u'zoomout': u'["habitez", "occupez", "peuplez"]'},
            u'present_6': {u'normal': u'["vivent"]',
                    u'opposite': u'["meurent"]',
                    u'shake': u'["sont", "logent", "campent"]',
                    u'zoomin': u'["existent", "respirent", "subsistent"]',
                    u'zoomout': u'["habitent", "occupent", "peuplent"]'}}

    word = WordProvider(data)
    print word.get()
    word.do_synonym()
    print word.get()
