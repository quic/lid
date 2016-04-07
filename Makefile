.PHONY: deps test-deps test install clean git-clean, all

all: test

license_identifier/licenses.py: update_licenses.py
	python update_licenses.py

deps: requirements.txt
	pip install -r $<

test-deps: test-requirements.txt
	pip install -r $<

test: deps license_identifier/licenses.py
	cd license_identifier && python -B -m pytest --cov=. --cov-report=term-missing --pdb *_test.py

install: deps license_identifier/licenses.py
	python setup.py install

clean:
	cd license_identifier && rm -f *.pyc && rm -f licenses.py

git-clean:
	git clean -Xdf
