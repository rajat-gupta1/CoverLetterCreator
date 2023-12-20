import streamlit as st
import requests
from bs4 import BeautifulSoup
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
import shutil

from dotenv import load_dotenv

load_dotenv()

import os

def scrape_website(url):
    """
    Scrapes text content on a given website.

    Args:
        url (str): The URL of the website to scrape.

    Returns:
        str: Concatenated string containing text from all paragraphs on the webpage.
             Returns None if the HTTP request is not successful.
    """
    response = requests.get(url)

    # For successful responses
    if response.status_code == 200:

        # Parse the HTML content of the webpage using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text content from all <p> (paragraph) tags
        paragraphs = [p.text.strip() for p in soup.find_all("p")]

        web_str = ""
        for para in paragraphs:
            web_str += para
        return web_str
    
    else:
        print("Failed to retrieve the web page. Status code:", response.status_code)
        st.write("Failed to retrieve the web page.")

def get_loader(uploaded_file):
    """
    Saves an uploaded PDF file to the "Docs" directory, converts it to 
    Langchain Document, and returns it

    Args:
        uploaded_file (UploadedFile): The uploaded PDF file.

    Returns:
        Langchain Document: The content of the file as a Langchain Document
    """
    if uploaded_file is not None:
        if os.path.exists("Docs"):
             # If it exists, remove the directory and its contents
            directory_path = os.path.join(os.getcwd(), "Docs")
            shutil.rmtree(directory_path)

        os.mkdir("Docs")

         # Write the uploaded PDF file to the "Docs" directory
        with open(os.path.join("Docs",uploaded_file.name),"wb") as f: 
            f.write(uploaded_file.getbuffer()) 

        # Load all PDF files from current directory as a Langchain Document
        loader = DirectoryLoader(f"docs", glob="./*.pdf", loader_cls=PyPDFLoader)
        docs = loader.load()

        # Return it as a Langchain Document instead of an array
        return docs[0]

def main():     

    # Set the title of the Streamlit app
    st.title("Cover Letter Creator")
    
    # Create a form for user input
    with st.form("my_form"):
        JD_option = st.selectbox("How do you want to submit the JD?",("PDF", "Provide URL"), index=None)
        Resume_option = st.selectbox("How do you want to submit your Resume?",("PDF", "Paste as Text"), index=None)
        submitted = st.form_submit_button("Submit")

    JD = None
    Resume = None

    # Process user input based on JD option
    if JD_option == "PDF":
        JD = st.file_uploader("Upload the JD", type="pdf")
        JD = get_loader(JD)
        
    elif JD_option == "Provide URL":
        JD = st.text_input("JD_URL", None, placeholder="Paste the URL for the given JD")
        if JD is not None:
            JD = scrape_website(JD)
            # Convert JD to Langchain Document
            JD =  Document(page_content=JD, metadata={"source": "local"})

    # Process user input based on Resume option
    if Resume_option == "PDF":
        Resume = st.file_uploader("Upload the Resume", type="pdf")
        Resume = get_loader(Resume)

    elif Resume_option == "Paste as Text":
        Resume = st.text_input("Resume", None, placeholder="Type your Resume here")
        if Resume is not None:
            Resume =  Document(page_content=Resume, metadata={"source": "local"})

    # The default Prompt
    prompt_template2 = """The first document here is the job description along with company details. The second document is the resume. 
    Create a cover letter from the resume using job description and company details from the text:
    {text}
    COVER LETTER:"""

    # The modified Prompt
    prompt_template = ""

    with st.form("my_form2"):
        prompt_template = st.text_input("Prompt Template (Do not change if you are unsure)", prompt_template2)
        submitted2 = st.form_submit_button("Submit")

    # If the prompt has been submitted
    if submitted2:
        st.write("Creating Cover Letter...")
        
        prompt = PromptTemplate.from_template(prompt_template)

        # Initialize ChatOpenAI and LLMChain objects
        llm = ChatOpenAI(temperature=0.1, model_name="gpt-3.5-turbo-16k")
        llm_chain = LLMChain(llm=llm, prompt=prompt)

        # Initialize StuffDocumentsChain object
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")

        # Run the StuffDocumentsChain on the provided documents (JD and Resume)
        final_text = [JD, Resume]
        Cover_Letter = stuff_chain.run(final_text)

        # Display the generated Cover Letter
        st.write(Cover_Letter)

        # Add a download button for the generated Cover Letter
        st.download_button("Download Cover Letter", Cover_Letter, file_name="CoverLetter.txt")
        
if __name__ == "__main__":
    main()