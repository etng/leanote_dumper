all: clean dump
clean:
	rm data/*.md || true
	rm data/*.htm || true
dump:
	python dump_leannotes.py
.PHONY: clean dump
help:
	@echo "	clean"
	@echo "	Remove old dumps but keep images and attachs"
	@echo "	dump"
	@echo "	dump data"
