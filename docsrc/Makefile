# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = ./_build/
AUTODOCDIR    = api
AUTODOCBUILD  = sphinx-apidoc
PROJECT       = oceanpack
MODULEDIR     = ../src/oceanpack

# User-friendly check for sphinx-build
#ifeq ($(shell which $(SPHINXBUILD) >/dev/null 2>&1; echo $?), 1)
#$(error The '$(SPHINXBUILD)' command was not found. Make sure you have Sphinx installed, then set the SPHINXBUILD environment variable to point to the full path of the '$(SPHINXBUILD)' executable. Alternatively you can add the directory with the executable to your PATH. If you don't have Sphinx installed, grab it from http://sphinx-doc.org/)
#endif

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help github clean doc-requirements Makefile

github:
	@make html
	@mkdir -p ../docs
	@cp -a $(BUILDDIR)/html/. ../docs

clean:
	rm -rf $(BUILDDIR)/* $(AUTODOCDIR)

$(AUTODOCDIR): $(MODULEDIR)
	mkdir -p $@
	$(AUTODOCBUILD) -f -o $@ $^

doc-requirements: $(AUTODOCDIR)


# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: doc-requirements
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
