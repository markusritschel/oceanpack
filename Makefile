# This is a self-documenting Makefile.
# For details, check out the following resources:
# https://gist.github.com/klmr/575726c7e05d8780505a
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html

# ======= Put your targets etc. between here and the line which is starting with ".DEFAULT_GOAL" =======
# Document any rules by adding a single line starting with ## right before the rule (see examples below)
# ======================================================================================================

# If you have an .env file
# include .env



.PHONY: cleanup clean-jupyter-book clean-pyc, clean-logs, documentation, book, save-requirements, requirements, src-available, conda-env, test-requirements, tests, clear-images, convert-images, figures, crop-pdf, crop-png, show-help

## Clean-up python artifacts, logs and jupyter-book built
cleanup: clean-pyc clean-logs clean-docs clean-test-cov

## Cleanup documentation built
clean-docs:
	rm -rf doc/_build/*
	jb clean --all docs/

# Remove Python file artifacts
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +


## Remove all log files
clean-logs:
	find ./logs -iname '*.log' -type f -exec rm {} +


## Remove coverage files
clean-test-cov:
	find . -name 'htmlcov' -exec rm -fr {} +

## Build the code documentation with Jupyter-Book
documentation:
	jb build docs/ -v



## Run flake8 linter
lint:
	uv run ruff check


## Synchronize Jupyter notebooks according to the rules in pyproject.toml
sync-notebooks:
	jupytext --sync notebooks/**/*.ipynb


## Update dependencies lock file
save-requirements:
	uv lock


## Create a conda environment.yml file
save-conda-env:
	@pip_packages=$$(conda env export | grep -A9999 ".*- pip:" | grep -v "^prefix: ") ;\
	 conda env export --from-history | grep -v "^prefix: " > environment.yml;\
	 echo "$$pip_packages" >> environment.yml ;\
	 sed -i 's/name: base/name: $(CONDA_DEFAULT_ENV)/g' environment.yml
	@echo exported \"$$CONDA_DEFAULT_ENV\" environment to environment.yml


## Create a conda environment named 'oceanpack', install packages, and activate it
conda-env:
	@echo "Create conda environment 'oceanpack"
	conda create --name oceanpack python=3.10 --no-default-packages 
	@echo "Activate conda environment 'oceanpack'"
	conda activate oceanpack


## Set up a virtual environment with uv
virtual-env:
	@echo "Set up a virtual environment with uv"
	uv sync --dev
	uv lock


## Install Python Dependencies
install-requirements:
	@echo "Install required packages into current environment"
	uv sync --all-extras

## Install requirements for building the docs
install-doc-requirements:
	uv sync --groups docs


## Make the source code as package available
src-available:
	pip install -e .


## Check if all packages listed in pyproject.toml are installed in the current environment
test-requirements:
	@echo "Check if all packages listed in pyproject.toml are installed in the current environment:"
	uv sync --all-extras --dry-run


## Run pytest for the source code
tests: test-requirements
	uv run pytest -v


## Test github actions locally
test-gh-actions:
	mkdir -p /tmp/artifacts
	act push --artifact-server-path /tmp/artifacts --container-options "--userns host" --action-offline-mode





# ==================== Don't put anything below this line ====================
# https://www.digitalocean.com/community/tutorials/how-to-use-makefiles-to-automate-repetitive-tasks-on-an-ubuntu-vps
.DEFAULT_GOAL := show-help
show-help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)";echo;sed -ne"/^## /{h;s/.*//;:d" -e"H;n;s/^## //;td" -e"s/:.*//;G;s/\\n## /---/;s/\\n/ /g;p;}" ${MAKEFILE_LIST}|LC_ALL='C' sort -f|awk -F --- -v n=$$(tput cols) -v i=21 -v a="$$(tput setaf 6)" -v z="$$(tput sgr0)" '{printf"%s%*s%s ",a,-i,$$1,z;m=split($$2,w," ");l=n-i;for(j=1;j<=m;j++){l-=length(w[j])+1;if(l<= 0){l=n-i-length(w[j])-1;printf"\n%*s ",-i," ";}printf"%s ",w[j];}printf"\n";}'|more
