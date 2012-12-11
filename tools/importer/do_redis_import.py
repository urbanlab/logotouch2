import redis
import sys
import json
from wordprovider import CSVWordProvider

r = redis.StrictRedis()

cid = 'corpus.0'
r.set(cid + '.name', 'Francais')
r.set(cid + '.author', 'Erasme')
r.set(cid + '.email', 'logotouch@erasme.org')
r.set(cid + '.count', 0)

def get_words(wp, tense, action):
    wpaction = tr_actions.get(action, action)
    return [wp.data[tense][wp.titles.index(key) - 1] for key in wp.titles if key.startswith(wpaction)]

types = ['verbe', 'mot', 'adverbe']
tr_actions = {'normal': 'mot', 'shake': 'secouer', 'opposite': 'contraire'}
for fn in sys.argv[1:]:
    wp = CSVWordProvider(fn)
    print '-- add', wp.wtype

    data = []
    for action in ('normal', 'zoomin', 'zoomout', 'shake', 'opposite'):
        tenses = ('name', )
        if wp.wtype == 'verbe':
            tenses = ['infinitif_0']
            for tense in ('present', 'past', 'future'):
                for x in xrange(1, 7):
                    tenses.append(tense + '_' + str(x))
        for tense in tenses:
            data.append(((tense, action), get_words(wp, tense, action)))

    # all ok, create the word!
    vid = r.incr(cid + '.count')
    vid = cid + '.' + str(vid)
    pipe = r.pipeline()
    pipe.set(vid + '.type', types.index(wp.wtype))
    for keys, words in data:
        key = vid + '.' + '.'.join(keys)
        pipe.set(key, json.dumps(words))
    pipe.execute()
