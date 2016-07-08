.PHONY: deps test-deps test install clean git-clean, all, pickle

all: test

license_identifier/licenses.py: update_licenses.py
	python update_licenses.py

deps: requirements.txt
	pip install -r $<

test-deps: test-requirements.txt
	pip install -r $<

test: deps test-deps
	cd license_identifier && python -B -m pytest --cov-config=.coveragerc --cov=. --cov-report=term-missing *_test.py

install: deps license_identifier/licenses.py
	python setup.py install

clean:
	cd license_identifier && rm -f *.pyc && rm -f licenses.py

pickle: deps license_identifier/licenses.py
	python -m license_identifier.license_identifier -L license_identifier/data/license_dir/ -P license_identifier/data/license_n_gram_lib.pickle

git-clean:
	git clean -Xdf
