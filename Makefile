MODULES = api/auth-api api/contents-api api/script-api package/core-package package/object-package

.PHONY: test
test:
	for module in $(MODULES); do \
		cd $$module; \
		poetry install --sync; \
		poetry run python -m unittest discover -s tests; \
		cd -; \
	done