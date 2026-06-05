import os 
import streamlit as st
import requests 
import time
import uuid
import logfire
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))

load_dotenv(env_path)

try:
    token = os.getenv("LOGFIRE_TOKEN")
    if not token:
        print('ERROR: Token not found')
    
    logfire.configure(token)
    LOGFIRE_STATUS = "Connected & Tracing"

except Exception as e:
    print(f"Logfire Init Error in UI: {e}")
    LOGFIRE_STATUS = f"Error: {str(e)}"

    