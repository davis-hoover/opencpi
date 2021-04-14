include $(OCPI_CDK_DIR)/include/util.mk
SRC_PAGES=$(wildcard src/*.1.txt)
MAN_PAGES=$(SRC_PAGES:src/%.1.txt=gen/man1/%.1)
HTML_PAGES=$(SRC_PAGES:src/%.1.txt=gen/html/%.1.html)
INDEX=gen/html/index.html
TOOL=$(OCPI_PREREQUISITES_DIR)/asciidoc3/ad3/a2x3.py -L
LOG:=$(shell echo `pwd`/"gen/build-man-pages.`date +%y%m%d%H%M%S`.log")
PRINTLOG=$(if $(printedlog),,\
           $(eval printedlog:=1)$(info Log for all man page generation is in: $(LOG)))
all: man html
man: $(MAN_PAGES)
html: $(HTML_PAGES) $(INDEX)
gen/man1 gen/html:
	$(AT)mkdir -p $@

$(MAN_PAGES): gen/man1/%.1 : src/%.1.txt | gen/man1
	$(AT)echo Generating $@ from $<$(PRINTLOG)
	$(AT)set -o pipefail && \
	     ($(TOOL) --doctype manpage --format manpage -D gen/man1 -v $<  >> $(LOG)) 2>&1 | \
	     sed '/--destination-dir option is only applicable/d'

$(HTML_PAGES): gen/html/%.1.html : src/%.1.txt | gen/html
	$(AT)echo Generating $@ from $<$(PRINTLOG)
	$(AT)$(TOOL) --doctype manpage --format xhtml -D gen/html -v $<  >> $(LOG)

$(INDEX): | gen/html
	$(AT)ln -s opencpi.1.html $@
clean:
	$(AT) rm -r -f gen
