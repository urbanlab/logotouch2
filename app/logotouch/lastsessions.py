__all__ = ('LastSessions', )

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView


class LastSessions(GridLayout):
    def __init__(self, **kwargs):
        super(LastSessions, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.rpc = self.app.rpc
        self.rpc.get_last_sessions(self.app.user_email,
                callback=self._on_available_sessions)

    def _on_available_sessions(self, result, error=None):
        if error is not None:
            # TODO
            return

        print result
        from logotouch.baseenc import baseenc
        for x in result:
            print '-->', x
            print baseenc(int(x.get('sessid')))


        args_converter = lambda index, rec: {'rec': rec}
        adapter = ListAdapter(
                data=result,
                args_converter=args_converter,
                template='LastSessionItemButton',
                selection_mode='none')
        self.add_widget(ListView(adapter=adapter))
