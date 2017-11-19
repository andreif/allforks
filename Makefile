.DEFAULT_GOAL := server

server:
	source .env && python app.py
