

SDK_DIR=./third_party/google_appengine
BOOTSTRAP_DIR=./third_party/bootstrap
PUBLIC_DIR=./app/public
STYLESHEETS_DIR=${PUBLIC_DIR}/stylesheets

pytest:
	python ./app/py/runtest.py ${SDK_DIR}

run: css
	${SDK_DIR}/dev_appserver.py app/

upload:
	${SDK_DIR}/appcfg.py update app/

css: ${STYLESHEETS_DIR}/bootstrap.css

clean:
	-rm ${STYLESHEETS_DIR}/*.css

${STYLESHEETS_DIR}/bootstrap.css:
	cp ${BOOTSTRAP_DIR}/bootstrap.css $@

# XXX: checkout bootstrap
setup:
	cd ${BOOTSTRAP_DIR}; make DATE=date

.PHONY: clean