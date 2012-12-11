__all__ = ('CorpusSelector', )

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.listview import ListView
from kivy.properties import StringProperty


class CorpusSelector(GridLayout):
    corpus_id = StringProperty()

    def __init__(self, **kwargs):
        super(CorpusSelector, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.rpc = self.app.rpc
        self.rpc.get_available_corpus(callback=self._on_available_corpus)

    def _on_available_corpus(self, result, error=None):
        print 'on_available_corpus', result, error
        if error is not None:
            # TODO
            return

        args_converter = lambda index, rec: {'rec': rec}
        adapter = DictAdapter(
                data=result,
                args_converter=args_converter,
                template='CorpusItemButton',
                selection_mode='none')
        self.add_widget(ListView(adapter=adapter))
