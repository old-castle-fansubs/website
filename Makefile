include ~/.config/oc-tools.env
export

dev:
	FLASK_APP=oc_website.app FLASK_ENV=development python3 -m flask run

release-anime:
ifdef path:
	@echo python3.9 -m oc_website.release "$(path)"
else
	$(error 'path required')
endif

publish-website:
	sh -c "\
		git ls-files -mo --directory --exclude-standard | grep -v __pycache__ && echo 'there are untracked files, aborting.' && exit 1; \
		git push --force-with-lease; \
		python3 -m oc_website.publish"

.PHONY: dev release-anime publish-website
