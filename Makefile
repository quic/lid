all: test

deps: requirements.txt
	pip install -r $<

test: deps
	cd license_identifier && python -B -m pytest --cov=. --cov-report=term-missing --pdb *_test.py

install: deps
	python setup.py install

clean:
	cd license_identifier && rm -f *.pyc

git-clean:
	git clean -Xdf
