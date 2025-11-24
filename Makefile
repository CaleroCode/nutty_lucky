run:
	.venv/Scripts/python src/main.py

watch:
	nodemon --exec ".venv/Scripts/python src/main.py" --ext py --watch src