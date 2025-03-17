## Setup
1. Clone the repository
2. Duplicate the `.env.example` file and rename it to `.env`
3. Populate the `.env` file with your own values
4. Follow the following steps based on your preference:
    - For docker users, run `docker-compose up --build`
    - For non-docker users
       - Setup python virtual environment by running `python3 -m venv venv`
       - Switch to the virtual environment by running `source venv/bin/activate`
       - Run `pip install -r requirements.txt`
       - Run `fastapi dev ./main.py`
