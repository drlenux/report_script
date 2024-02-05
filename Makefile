run:
	uvicorn main:app
dev:
	uvicorn main:app --reload
build:
	pyinstaller --onefile main.py