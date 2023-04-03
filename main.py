import streamlit as st
import pymongo
from pathlib import Path
import re
import os
import openai
from streamlit.components.v1 import html
# dotenv is usuful for local development,
# for deployment you can set the environment variables directly
# in the deployment environment
from dotenv import load_dotenv
load_dotenv()

@st.cache_resource()
def load_db():
    # requires a connection to a mongodb database, but you can
    # remove the database (and all lines using it) if no websites are stored.
    client = pymongo.MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
    db = client.streamlit_html_generator
    return db

@st.cache_data(ttl=60*10)
def load_existing_sites(_db):
    return list(_db.sites.find({ "accepted": True }))

st.set_page_config(page_title="Streamlit Site Generator", layout="wide")
openai.api_key = os.getenv("OPENAI_API_KEY")
db = load_db()
websites = load_existing_sites(db)

def get_starting_convo():
    return [
        {
            "role": "system", 
            "content": "You are an assistant that helps the user create and improve a web page in HTML, CSS, and JavaScript."
        }
    ]

@st.cache_data(ttl=10, show_spinner=False)
def call_openai_api(conversation):
    st.spinner("The code is being generated...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        temperature=0.1
    )
    return response["choices"][0]["message"]["content"].strip()

def main():
    # initialize session state
    if "show_code" not in st.session_state:
        st.session_state.show_code = False
    if "messages" not in st.session_state:
        st.session_state.messages = get_starting_convo()

    st.title("Interactive Website Generator")
    st.write(
        "Enter your desired website and let the AI generate it for you! If you would like to see the code, see [this article](https://medium.com/@dreamferus/i-built-a-streamlit-app-to-generate-websites-in-seconds-try-it-6cf13eb86192)."
    )

    user_input = st.text_area("Type your content:", height=200)
    
    has_previously_generated = len(st.session_state.messages) > 1
    reset = not has_previously_generated or st.checkbox("Reset", value=False)
    
    # change text depending on whether the user has previously generated code
    if st.button("Generate website" if reset else "Ask AI to modify the generated website"):
        # set to starting conversation if reset
        messages = get_starting_convo() if reset else st.session_state.messages.copy()
        # decide prompt depending on whether the user has previously generated code
        if reset:
            messages.append({
                "role": "user", 
                "content": f"Create an HTML web page with accompanying CSS and JavaScript in a single HTML-file based on the following description: {user_input}"
            })
        else:
            messages.append({
                "role": "user", 
                "content": f"Modify the previous website to accomodate the following:\n\n{user_input}\n\n Note that you should recreate the HTML, CSS, and JavaScript code from scratch in its entirety. The new code should be self-contained in a single HTML-file."
            })
        # get the AI's response
        try:
            output = call_openai_api(messages)
        except Exception as e:
            st.error(f"Error while generating code. {str(e)}")
            return

        # extract the code block
        pattern = r"```(\w*)\n([\s\S]*?)\n```"
        code_blocks = re.findall(pattern, output)

        # should be in a single file
        if len(code_blocks) != 1:
            st.error("Something went wrong. Please try again or change the instructions.")
            return
        
        # append the assistant's response to the conversation
        messages.append({"role": "assistant", "content": output})

        # two groups are captured, the language and the code,
        # but only the code is needed
        st.session_state.code = code_blocks[0][1]
        st.session_state.output = output
        st.session_state.messages = messages

        # go from the beginning
        st.experimental_rerun()

    # display the generated html/css/javascript
    if "code" in st.session_state and st.session_state.code is not None:
        st.header("Generated website")
        html(st.session_state.code, height=600, scrolling=True)
            
    # display the code and explanations
    if has_previously_generated and st.session_state.code is not None:
        # toggle between show and hide,
        # a placeholder (st.empty) is used to replace the
        # text of the button after it has been clicked
        show_hide_button = st.empty()
        get_show_code_text = lambda: "Show code and explanations" if not st.session_state.show_code else "Hide code and explanations"
        clicked = show_hide_button.button(get_show_code_text())
        if clicked:
            st.session_state.show_code = not st.session_state.show_code
            show_hide_button.button(get_show_code_text())
        if st.session_state.show_code:
            st.header("Code and explanations")
            st.markdown(st.session_state.output)

        # form to submit/publish the website
        st.header("Publish website")
        st.write("""
            If you publish the app and it is approved it will be displayed below for everyone to try out. By submitting
            you give me the full permission to do so.
        """)
        name = st.text_input("Add a name for the website")
        submit = st.button("Submit")

        if submit:
            if name == "":
                st.error("You need to add a name")
            else:
                db.sites.insert_one({ "name": name, "code": st.session_state.code, "accepted": False })
                st.success("Your website has been submitted for review.")

    # display previously generated websites that can be opened
    if websites:
        st.header("Try previously generated websites")
        for website in websites:
            click = st.button(website['name'], key=website["_id"])
            if click:
                db.sites.update_one({ "_id": website["_id"] }, { "$set": { "views": website.get("views", 0) + 1 } })
                html(website["code"], height=600, scrolling=True)

if __name__ == "__main__":
    main()