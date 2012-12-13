from kivy.vector import Vector
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.layout import Layout
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
from kivy.metrics import sp, dp
from kivy.properties import DictProperty, NumericProperty, StringProperty, \
        AliasProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.animation import Animation
from logotouch.provider import WordProvider


WORD_FONTSIZE = 44


class TypeButton(ToggleButton):
    wordtype = NumericProperty()


class Word(Button):
    padding = NumericProperty('20dp')
    wordid = StringProperty()
    screen = ObjectProperty()
    word = ObjectProperty()

    antonym = BooleanProperty(False)
    zoom = NumericProperty(0)

    fontzoom = NumericProperty(0)
    direction = NumericProperty(0)

    provider = ObjectProperty()
    wordtype = NumericProperty(0)
    text = StringProperty()

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(WORD_FONTSIZE))
        super(Word, self).__init__(**kwargs)
        self.provider = WordProvider(kwargs['word'])
        self.reload()

    def reload(self, *args):
        provider = self.provider
        self.text = provider.get()
        self.wordtype = provider.itype
        self.antonym = provider.antonym
        self.zoom = provider.zoom

        Animation(
                fontzoom=self.zoom * sp(5),
                padding=max(dp(20), dp(20) - self.zoom * dp(10)),
                direction=(provider.tense - 1) * dp(5),
                d=0.3, t='out_quart').start(self)


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

    def on_release(self, *args):
        if self.__class__ is not Word:
            return
        t = self._last_touch
        d = Vector(t.pos).distance(t.opos)
        if d > 20:
            return
        self.screen.open_gesture_selection(self)


    


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

        return super(DroppableWord, self).on_touch_up(touch)


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
        self._view = None
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

    def open_gesture_selection(self, word):
        # modal popup?
        self._view = view = GestureWordSelector(screen=self, word=word)
        view.open()



from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from time import time

class GestureWord(Word):
    pass

class GestureWordSelector(ModalView):
    word = ObjectProperty()
    screen = ObjectProperty()
    container = ObjectProperty()

    def on_container(self, instance, value):
        oword = self.word
        self.container.clear_widgets()
        word = GestureWord(word=oword.word,
            wordid=oword.wordid, screen=self.screen)
        self.container.set_word(word)

class GestureContainerSelector(FloatLayout):
    def __init__(self, **kwargs):
        self.word = None
        super(GestureContainerSelector, self).__init__(**kwargs)
        self.touches = []
        self.touch = None
        self.action_exclusive = None
        self.angle = None
        self.shake_counter = 0
        self.shake_direction = 0

        # configure trigger
        self.action_scale_trigger = kwargs.get('scale_trigger', 30)
        self.action_scale_padding = kwargs.get('scale_padding', 10)
        self.action_scale_fontsize = kwargs.get('scale_fontsize', 1)
        self.action_rotation_trigger = kwargs.get('rotation_trigger', 45)
        self.action_time_trigger = kwargs.get('time_trigger', 25)
        self.action_person_trigger = kwargs.get('person_trigger', 25)
        self.action_shake_trigger = kwargs.get('shake_trigger', 15)

    def set_word(self, word):
        self.add_widget(word)
        self.word = word
        self.provider = word.provider
        self.word.center = self.center

    def on_center(self, instance, value):
        if self.word:
            self.word.center = self.center

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        touch.grab(self)
        self.touches.append(touch)
        touch.ud['origin'] = touch.opos
        touch.ud['delta'] = Vector(touch.pos) - Vector(self.pos)
        touch.ud['time'] = time()
        if self.touch is None:
            self.touch = touch
            self.detect_action(touch)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return True
        if not touch in self.touches:
            return False
        self.detect_action(touch)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return True
        if touch not in self.touches:
            return
        self.touches.remove(touch)
        if touch is self.touch:
            self.touch = None
        self.reset_detection()
        return True

    def is_controled(self):
        return bool(len(self.touches))

    def is_action_allowed(self, action):
        return not self.action_exclusive or self.action_exclusive == action

    def detect_action(self, touch):
        num = len(self.touches)
        action = None
        if num == 1:
            action = self.detect_action_1(touch)
        elif num == 2:
            action = self.detect_action_2(touch)
        elif num == 3:
            action = self.detect_action_3(touch)
        if action:
            self.apply_action(action, touch)
            self.word.reload()

    def detect_action_1(self, touch):
        # double tap ?
        if self.is_action_allowed('toggleperson'):
            if touch.is_double_tap:
                return 'toggleperson'

        # only one action possible.. move :=)
        if self.is_action_allowed('shake'):
            distance = Vector(touch.ud['origin']).distance(touch.pos)
            direction = (touch.x - touch.ud['origin'][0] > 0)
            if distance > self.action_shake_trigger:
                # no shake yet, initialize.
                if self.shake_counter == 0:
                    self.shake_counter = 1
                    self.shake_direction = not direction
                elif self.shake_direction == direction:
                    self.shake_direction = not direction
                    self.shake_counter += 1
                if self.shake_counter >= 3:
                    return 'shake'

        # drag ?
        if self.is_action_allowed('drag'):
            pass

        # no shake... allow move :)
        if self.is_action_allowed('move'):
            return 'move'

    def detect_action_2(self, touch):
        touch1, touch2 = self.touches
        # 2 fingers, detect scale
        if self.is_action_allowed('scale'):
            distance = Vector(touch1.pos).distance(touch2.pos) - \
                       Vector(touch1.ud['origin']).distance(touch2.ud['origin'])
            if abs(distance) >= self.action_scale_trigger:
                touch.ud['scale'] = distance
                return 'scale'

        # no scale, detect a rotation
        if self.is_action_allowed('rotate'):
            angle = Vector(0, 1).angle(Vector(touch1.pos) - Vector(touch2.pos))
            Logger.debug('calculated angle is %f' % angle)
            if self.angle is None:
                self.angle = angle
            else:
                Logger.debug('current angle is %f' % self.angle)
                angle = abs(angle - self.angle) % 360
                if angle > 180:
                    angle = 360 - angle
                # trigger
                Logger.debug('result angle is %f' % angle)
                if angle > self.action_rotation_trigger:
                    return 'rotate'

    def detect_action_3(self, touch):
        touch1, touch2, touch3 = self.touches
        if touch is not touch3:
            return

        # do the movement detection only on the third finger
        dx = touch.x - touch.ud['origin'][0]
        dy = touch.y - touch.ud['origin'][1]
        if self.is_action_allowed('time'):
            if abs(dx) > self.action_time_trigger:
                touch.ud['time'] = dx
                return 'time'
        if self.is_action_allowed('person'):
            if abs(dy) > self.action_person_trigger:
                touch.ud['person'] = dy
                return 'person'

    def apply_action(self, action, touch):
        Logger.debug('apply action %s' % action)
        # just move the word
        if action == 'move':
            x, y = map(int, Vector(touch.pos) - touch.ud['delta'])
            y -= self.y
            x -= self.x
            self.word.center = x + self.center_x, y + self.center_y
            return

        # do synonym
        elif action == 'shake':
            Logger.debug('do shake')
            self.cancel_action_scale()
            self.cancel_action_antonym()
            self.provider.do_synonym()
            self.shake_counter = 0
            self.shake_direction = 0

        else:
            self.cancel_action_shake()

        if action == 'toggleperson':
            if not self.action_exclusive == 'toggleperson':
                self.action_exclusive = 'toggleperson'
                Logger.debug('toggle person')
                self.provider.toggle_person()

        # bigger / smaller word
        if action == 'scale':
            self.action_exclusive = 'scale'
            if touch.ud['scale'] > 0:
                if self.provider.do_zoomout():
                    #self.padding += self.action_scale_padding
                    #self.textopt['font_size'] += self.action_scale_fontsize
                    #Logger.debug('do scale + %d' % self.padding)
                    pass
            else:
                if self.provider.do_zoomin():
                    #self.padding -= self.action_scale_padding
                    #self.textopt['font_size'] -= self.action_scale_fontsize
                    #Logger.debug('do scale - %d' % self.padding)
                    pass

        # rotation do the antonym
        elif action == 'rotate':
            if self.action_exclusive != 'rotate':
                self.action_exclusive = 'rotate'
                self.provider.do_antonym()
                #s = self.style.get
                #color = s('color')
                #if self.provider.antonym:
                #    color = s('antonym-color')
                #self.textopt['color'] = color

        # prev/next time
        elif action == 'time':
            Logger.debug('do time %d' % touch.ud['time'])
            self.action_exclusive = 'time'
            if touch.ud['time'] > 0:
                self.provider.do_time_next()
            else:
                self.provider.do_time_previous()
            self.ldirection = (self.provider.tense - 1) * 10

        # prev/next pronoun
        elif action == 'person':
            Logger.debug('do person')
            self.action_exclusive = 'person'
            if touch.ud['person'] < 0:
                self.provider.do_person_next()
            else:
                self.provider.do_person_previous()

        self.reset_action()

    def cancel_action_scale(self):
        #self.padding = 10
        #self.textopt['font_size'] = self.style.get('font-size')
        self.provider.zoom = 0

    def cancel_action_antonym(self):
        #self.textopt['color'] = self.style.get('color')
        if self.provider.antonym:
            self.provider.do_antonym()

    def cancel_action_shake(self):
        self.shake_counter = 0
        self.shake_direction = 0

    def reset_action(self):
        #pymt_logger.debug('reset')
        # reset origin of all touches.
        for touch in self.touches:
            touch.ud['origin'] = touch.pos
        self.angle = None

    def reset_detection(self):
        # reset exclusive action
        self.reset_action()
        self.action_exclusive = None
        self.cancel_action_shake()
        Animation(center=self.center, d=0.3, t='out_quart').start(self.word)


