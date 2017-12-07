.PHONY: deps test install clean git-clean, all, pickle

all: test

update-licenses: deps update_licenses.py
	python update_licenses.py

deps: requirements.txt
	pip install -r $<

test: tox

install: deps
	python setup.py install

clean:
	cd license_identifier && rm -f *.pyc && rm -f licenses.py

pickle: deps
	python -m license_identifier.cli -L license_identifier/data/license_dir/ -P license_identifier/data/license_n_gram_lib.pickle

git-clean:
	git clean -Xdf
