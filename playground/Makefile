build:
	go build -o dist/linux.so -buildmode=c-shared main.go

rerun: 
	python main.py


run: build rerun
