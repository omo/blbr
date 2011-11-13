

SDK_DIR       = ./third_party/google_appengine
BOOTSTRAP_DIR = ./third_party/bootstrap

APP_DIR    = ./app
PUBLIC_DIR = ${APP_DIR}/public

STYLESHEETS_DIR = ${PUBLIC_DIR}/stylesheets
STYLESHEETS_BIN = ${STYLESHEETS_DIR}/bootstrap.css

CO_SRC_DIR = ${APP_DIR}/coffee
CO_BIN_DIR = ${PUBLIC_DIR}/js/app
CO_SRC := ${wildcard ${CO_SRC_DIR}/*.coffee}
CO_BIN := ${patsubst ${CO_SRC_DIR}/%.coffee,${CO_BIN_DIR}/%.js,${CO_SRC}}


prerun: pytest compile

pytest:
	python ./app/py/runtest.py ${SDK_DIR}

run: compile
	${SDK_DIR}/dev_appserver.py app/

upload: compile
	${SDK_DIR}/appcfg.py update app/

compile: css js

css: ${STYLESHEETS_BIN}

js: ${CO_BIN}

${CO_BIN_DIR}/%.js: ${CO_SRC_DIR}/%.coffee
	coffee -o ${CO_BIN_DIR} $<

${STYLESHEETS_DIR}/bootstrap.css: ${BOOTSTRAP_DIR}/bootstrap.css
	cp $< $@
${CO_BIN_DIR}/%.js: ${CO_SRC_DIR}/%.coffee
	coffee -o ${CO_BIN_DIR} $<

clean:
	-rm ${STYLESHEETS_DIR}/*.css

# XXX: checkout bootstrap
setup:
	cd ${BOOTSTRAP_DIR}; make DATE=date
	ender add ${JS_LIB_PACKAGES}

.PHONY: clean