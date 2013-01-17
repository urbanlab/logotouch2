__version__ = '0.1'

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.modalview import ModalView
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, \
        ObjectProperty
from kivy.clock import Clock
from logotouch.client import ThreadedRpcClient
from logotouch.game import GameScreen
from logotouch.translations import _
from logotouch.baseenc import basedec

class AppButton(Button):
    pass

class WelcomeScreen(Screen):
    pass


class JoinSessionScreen(Screen):
    textinput = ObjectProperty()
    error = StringProperty()

    def on_enter(self, *args):
        self.textinput.select_all()
        self.textinput.focus = True

    def on_pre_leave(self, *args):
        self.textinput.focus = False


class CreateSessionScreen(Screen):
    pass


class DownloadScreen(Screen):
    title = StringProperty()
    action = StringProperty()
    progression = NumericProperty()


class HelpGesturePopup(ModalView):
    pass


class Logotouch(App):

    connected = BooleanProperty(False)

    def build_config(self, config):
        config.setdefaults('server', {
            'host': 'localhost',
            'db': '0' })

    def build(self):
        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_window_keyboard)

        self.rpc = None
        self.game_screen = None
        self.sm = ScreenManager(transition=SlideTransition())
        self.screen_welcome = WelcomeScreen(name='welcome')
        self.sm.add_widget(self.screen_welcome)
        self.connect()
        #self.create_session_with_corpus(0)
        return self.sm

    def create_session(self):
        if not hasattr(self, 'screen_create_session'):
            self.screen_create_session = CreateSessionScreen(name='create')
            self.sm.add_widget(self.screen_create_session)
        self.sm.current = 'create'

    def join_session(self):
        if not hasattr(self, 'screen_join_session'):
            self.screen_join_session = JoinSessionScreen(name='join')
            self.sm.add_widget(self.screen_join_session)
        self.sm.current = 'join'

    def create_session_with_corpus(self, corpus_id):
        if not hasattr(self, 'screen_download_corpus'):
            self.screen_download_corpus = DownloadScreen(name='download',
                    title=_('Game is starting'),
                    action=_('Creating session'),
                    progression=33)
            self.sm.add_widget(self.screen_download_corpus)
        self.sm.current = 'download'
        self.g_corpus_id = corpus_id
        self.rpc.new_session(corpus_id, callback=self._on_create_session)

    def join_session_from_enc(self, enc):
        try:
            sessid = basedec(enc)
            if not hasattr(self, 'screen_download_corpus2'):
                self.screen_download_corpus2 = \
                        DownloadScreen(name='download2',
                        title=_('Game is starting'),
                        action=_('Joining session'),
                        progression=33)
                self.sm.add_widget(self.screen_download_corpus2)
            self.sm.current = 'download2'
            self.rpc.join_session(sessid, callback=self._on_join_session)
        except:
            self.screen_join_session.error = _('Invalid session code')
            self.sm.current = 'join'
            self.screen_join_session.disptach('on_enter')

    def add_sentence(self, data):
        self.rpc.add_sentence(self.g_sessid, data)

    def _on_join_session(self, result, error=None):
        if error is not None:
            self.screen_join_session.error = _('Error while joining the session: {}').format(error)
            self.sm.current = 'join'
            return
        if result is None:
            self.screen_join_session.error = _('Unknow session code')
            self.sm.current = 'join'
            return
        self.g_sessid = result['sessid']
        self.g_corpus_id = result['corpusid']
        self.g_sentences_count = result['sentences_count']
        self.rpc.bind_session(self.g_sessid)
        self.sm.current_screen.action = _('Downloading Corpus')
        self.sm.current_screen.progression = 66
        self.rpc.get_corpus(self.g_corpus_id, callback=self._on_corpus)

    def _on_create_session(self, result, error=None):
        if error is not None:
            return
        self.g_sessid = result
        self.g_sentences_count = 0
        self.sm.current_screen.action = _('Downloading Corpus')
        self.sm.current_screen.progression = 66
        self.rpc.get_corpus(self.g_corpus_id, callback=self._on_corpus)

    def _on_corpus(self, result, error=None):
        if error is not None:
            # TODO
            return
        self.g_corpus = result
        self.sm.current_screen.progression = 100
        Clock.schedule_once(self._start_game, 0.1)

    def _start_game(self, *args):
        self.game_screen = GameScreen(name='game',
            sessid=self.g_sessid, corpus=self.g_corpus,
            sentences_count=self.g_sentences_count)
        if self.sm.has_screen('game'):
            self.sm.remove_widget(self.sm.get_screen('game'))
        self.sm.add_widget(self.game_screen)
        self.sm.current = 'game'

    def connect(self):
        self.rpc = ThreadedRpcClient(
                host=self.config.get('server', 'host'),
                on_session_broadcast=self._on_session_broadcast)

    def disconnect(self):
        pass

    def help_gesture(self):
        popup = HelpGesturePopup()
        popup.open()

    def _on_window_keyboard(self, window, *largs):
        key = largs[0]
        if key != 27:
            return
        # if there is a modal view in the window, avoid to check it
        from kivy.core.window import Window
        if any([isinstance(x, ModalView) for x in Window.children]):
            return
        if self.sm.current != 'welcome':
            self.sm.current = 'welcome'
            return True

    def _on_session_broadcast(self, sessid, message):
        if str(self.g_sessid) != str(sessid):
            print 'Dropped message, invalid sessid {} (we accept {})'.format(
                    sessid, self.g_sessid)
            return
        if self.game_screen:
            self.game_screen.on_broadcast(message)

if __name__ == '__main__':
    Logotouch().run()
