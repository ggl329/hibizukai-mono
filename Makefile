NAME=HibizukaiMono
VERSION=1.1
# BIZ UD Gothic 1.051
# JetBrains Mono NL 2.304
# Nerd Fonts 3.4.0

.PHONY: all
all: regular bold italic bold-italic

.PHONY: regular bold italic bold-italic
regular bold italic bold-italic:
	python3 generate-hibizukai-mono.py $@ $(VERSION)

.PHONY: package
package:
	cp LICENSE $(NAME)/
	rm -f $(NAME)-$(VERSION).7z
	7za a -mx9 $(NAME)-$(VERSION).7z $(NAME)

.PHONY: clean
clean:
	rm -rf $(NAME)/

.PHONY: distclean
distclean:
	rm -f *~ *.7z
	rm -rf $(NAME)/ __pycache__/
