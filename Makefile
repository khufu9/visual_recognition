profile:
	python2.7 -m cProfile -s time static_test.py | less

realtime:
	python2.7 realtime.py

static_test:
	python2.7 static_test.py
