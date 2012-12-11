from json import loads
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.layout import Layout
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
from kivy.metrics import sp
from kivy.properties import DictProperty, NumericProperty, StringProperty, \
        AliasProperty, ObjectProperty, ListProperty
from kivy.animation import Animation


WORD_FONTSIZE = 44

class TypeButton(ToggleButton):
    wordtype = NumericProperty()


class Word(Button):
    padding = NumericProperty('20dp')
    wordid = StringProperty()
    word = DictProperty()
    screen = ObjectProperty()

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(WORD_FONTSIZE))
        super(Word, self).__init__(**kwargs)

    def _get_text(self):
        tp = self.word.get('type')
        if tp is None:
            return ''
        key = 'name'
        if tp == '0': #verbe
            key = 'present_1'

        word = loads(self.word[key]['normal'])[0]
        return word

    text = AliasProperty(_get_text, None, bind=('word', ))

    def _get_type(self):
        return int(self.word['type'])
    wordtype = AliasProperty(_get_type, None, bind=('word', ))

    def on_touch_down(self, touch):
        self._last_touch = touch
        return super(Word, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        return super(Word, self).on_touch_move(touch)

    def on_press(self, *args):
        if self.__class__ is not Word:
            return
        touch = self._last_touch
        x, y = self.to_window(touch.x, touch.y)
        dw = DroppableWord(word=self.word,
            wordid=self.wordid, screen=self.screen, center=(x, y),
            last_touch=self._last_touch)
        touch.grab(dw)
        self._dw = dw
        self.screen.root_layout.add_widget(dw)

class DroppableWord(Word):
    tdelta = ListProperty([0, 0])
    last_touch = ObjectProperty()

    def __init__(self, **kwargs):
        super(DroppableWord, self).__init__(**kwargs)
        self.testwidget = Widget(size_hint=(None, None))
        self.testwidget.ref = self
        self.bind(size=self._update_word_pos)

    def _update_word_pos(self, instance, size):
        touch = self.last_touch
        x, y = self.to_window(touch.x, touch.y)
        self.center = x, y

    def on_touch_down(self, touch):
        if self.testwidget.parent:
            return False
        if self.collide_point(*touch.pos):
            self.testwidget.size = self.size
            self.parent.add_widget_at(self.testwidget, self.pos)
            self.parent.remove_widget(self)
            self.screen.root_layout.add_widget(self)
        self.tdelta = self.center_x - touch.x, self.center_y - touch.y
        return super(DroppableWord, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            x, y = self.to_window(touch.x, touch.y)
            tx, ty = self.tdelta
            self.center = x + tx, y + ty

            self.testwidget.size = self.size
            sc = self.screen.sentence_container
            if self.testwidget in sc.children:
                sc.remove_widget(self.testwidget)
            if sc.collide_point(*touch.pos):
                sc.add_widget_at(self.testwidget, touch.pos)

        return super(DroppableWord, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.unbind(size=self._update_word_pos)
            self.state = 'normal'
            self.parent.remove_widget(self)
            sc = self.screen.sentence_container
            if sc.collide_point(*touch.pos):
                sc.add_widget_at(self, touch.pos)
            if self.testwidget in sc.children:
                sc.remove_widget(self.testwidget)
            return True
        return


class GameLayout(Layout):
    spacing = NumericProperty('10dp')
    minimum_width = NumericProperty(0)

    def __init__(self, **kwargs):
        super(GameLayout, self).__init__(**kwargs)
        self.bind(
            children=self._trigger_layout,
            parent=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def add_widget(self, widget, index=0):
        widget.bind(size=self._trigger_layout)
        return super(Layout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(size=self._trigger_layout)
        return super(Layout, self).remove_widget(widget)

    def do_layout(self, *args):
        reposition_child = self.reposition_child
        spacing = self.spacing
        if not self.children:
            return
        wh = self.children[0].height
        linescount = int((self.height - spacing) / (wh + spacing))
        if linescount <= 0:
            return
        lines = [0] * linescount
        clines = [[] for x in lines]
        for child in self.children:
            # lowest available column
            index = lines.index(min(lines))
            x = lines[index]
            lines[index] = x + child.width + spacing
            clines[index].append(child)

        minimum_height = ((linescount * (wh + spacing)) - spacing)
        sy = self.y + (self.height - minimum_height) / 2.

        self.minimum_width = max(lines)
        ww = self.get_parent_window().width
        if self.minimum_width < ww:
            # center ?
            lines = [(ww - x) / 2 for x in lines]
            for index, line in enumerate(clines):
                x = self.x + lines[index]
                y = sy + index * (wh + spacing)
                for child in line:
                    reposition_child(child, x, y)
                    x += child.width + spacing
        else:
            lines = [0] * linescount
            for index, line in enumerate(clines):
                x = self.x + lines[index]
                y = sy + index * (wh + spacing)
                for child in line:
                    reposition_child(child, x, y)
                    x += child.width + spacing

    def reposition_child(self, child, x, y):
        Animation(pos=(x, y), d=.5, t='out_quart').start(child)


class SentenceLayout(Layout):
    spacing = NumericProperty('10dp')

    def __init__(self, **kwargs):
        super(SentenceLayout, self).__init__(**kwargs)
        self.bind(
            children=self._trigger_layout,
            parent=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def add_widget_at(self, widget, pos):
        x, y = pos
        children = reversed(self.children[:])
        added = False
        self.clear_widgets()
        for child in children:
            if x > child.center_x and not added:
                self.add_widget(widget)
                added = True
            self.add_widget(child)
        if not added:
            self.add_widget(widget)

    def reposition_child(self, child, x, y):
        Animation(pos=(x, y), d=.5, t='out_quart').start(child)

    def _iterate_words(self):
        for child in self.children:
            if child.__class__ is Widget:
                yield child.ref
            else:
                yield child

    def _calculate_widths(self):
        return sum([(x.ref.width if x.__class__ is Widget else x.width) for x in self.children])

    def _calculate_optimum_font_size(self):
        #cw = self._calculate_widths()
        words = list(self._iterate_words())
        text = ' '.join([x.text for x in words])
        font_size = WORD_FONTSIZE
        corelabel = CoreLabel(text=text, font_name=words[0].font_name)
        padding = words[0].padding * len(words)

        # too many words ?
        if padding > self.width / 2:
            padding = int(self.width / 2 / len(words))
            for word in words:
                word.padding = padding
        else:
            for word in words:
                word.padding = Word.padding.defaultvalue

        while True:
            corelabel.options['font_size'] = sp(font_size)
            w, h = corelabel.render()
            if w < self.width - padding:
                break
            font_size -= 1

        font_size = sp(font_size)
        if font_size != words[0].font_size:
            for word in words:
                word.font_size = font_size
                word.texture_update()


    def do_layout(self, *args):
        if not self.children:
            return
        wh = self.children[0].height
        y = self.y + (self.height - wh) / 2

        # automatically adjust
        self._calculate_optimum_font_size()

        x = self.x + self.spacing
        reposition_child = self.reposition_child
        for child in self.children:
            reposition_child(child, x, y)
            x += child.width



class GameScreen(Screen):
    corpus = DictProperty()
    sessid = NumericProperty()
    word_container = ObjectProperty()
    sentence_container = ObjectProperty()
    words = ListProperty([])
    show_types = ListProperty([True, True, True])

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        for wordid, word in self.corpus['words'].iteritems():
            self.create_word(wordid, word)

    def create_word(self, wordid, word):
        widget_word = Word(wordid=wordid, word=word, screen=self)
        self.words.append(widget_word)
        self.word_container.add_widget(widget_word)

    def on_show_types(self, instance, value):
        available_types = [index for index, value in enumerate(self.show_types)
                if value]
        for word in self.words:
            if word.wordtype not in available_types:
                self.word_container.remove_widget(word)
                continue
            if word not in self.word_container.children:
                word.center = self.center
                self.word_container.add_widget(word)

    def toggle_type(self, index):
        self.show_types[index] = not self.show_types[index]
