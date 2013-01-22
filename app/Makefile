.PHONY: gestures

gestures:
	python -m kivy.atlas data/gestures 512 tools/gesture-images/*.png

xgettext:
	xgettext.pl logotouch.kv logotouch/* main.py
	mv messages.po po/en.po

