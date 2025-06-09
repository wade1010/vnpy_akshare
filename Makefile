.PHONY: clean build upload publish

clean:
	rm -rf dist build *.egg-info

build: clean
	python -m build

upload:
	python -m twine upload dist/*

# 一次性执行清理、构建和上传
publish: clean build upload


