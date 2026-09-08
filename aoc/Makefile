build:
	go build -o dist/lib.so -buildmode=c-shared main.go

rerun: 
	python main.py


run: build rerun
