__version__ = '0.1'

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivy.clock import Clock
from logotouch.client import ThreadedRpcClient
from logotouch.game import GameScreen
from logotouch.translations import _

class AppButton(Button):
    pass

class WelcomeScreen(Screen):
    pass


class JoinSessionScreen(Screen):
    pass


class CreateSessionScreen(Screen):
    pass


class DownloadScreen(Screen):
    title = StringProperty()
    action = StringProperty()
    progression = NumericProperty()


class Logotouch(App):

    connected = BooleanProperty(False)

    def build_config(self, config):
        config.setdefaults('server', {
            'host': 'localhost',
            'db': '0' })

    def build(self):
        self.rpc = None
        self.sm = ScreenManager(transition=SlideTransition())
        self.screen_welcome = WelcomeScreen()
        self.sm.add_widget(self.screen_welcome)
        self.connect()
        self.create_session_with_corpus(0)
        return self.sm

    def create_session(self):
        self.screen_create_session = CreateSessionScreen(name='create')
        self.sm.add_widget(self.screen_create_session)
        self.sm.current = 'create'

    def join_session(self):
        self.screen_join_session = JoinSessionScreen(name='join')
        self.sm.add_widget(self.screen_join_session)
        self.sm.current = 'join'

    def create_session_with_corpus(self, corpus_id):
        download = DownloadScreen(name='download',
                title=_('Game is starting'),
                action=_('Creating session'),
                progression=33)
        self.sm.add_widget(download)
        self.sm.current = 'download'
        self.g_corpus_id = corpus_id
        self.rpc.new_session(corpus_id, callback=self._on_session)

    def _on_session(self, result, error=None):
        if error is not None:
            # TODO
            return
        self.g_sessid = result
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
        self.sm.add_widget(GameScreen(
            name='game',
            sessid=self.g_sessid,
            corpus=self.g_corpus))
        self.sm.current = 'game'

    def connect(self):
        self.rpc = ThreadedRpcClient()

    def disconnect(self):
        pass





if __name__ == '__main__':
    Logotouch().run()
