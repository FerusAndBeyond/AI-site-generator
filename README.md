## Streamlit-Site-Generator

Click [here](https://site-generator.streamlit.app/) to try it out. There is also an article explaining the code [here](https://itnext.io/i-built-a-streamlit-app-to-generate-websites-in-seconds-try-it-6cf13eb86192?sk=a0d357d4aa1831d72ad0c7ef21f832fe).

#### Setup

Install all packages in requirements.txt: `pip install -r requirements.txt`. 

Add environment variables to a `.env`, that is `OPENAI_API_KEY` and the `MONGODB_CONNECTION_STRING` (if you want to use the database, otherwise you can remove all code that utilizes the db). 

Thereafter, run `streamlit run main.py` to start the app.