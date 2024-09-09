# Langgraph Chatbot With WIKITOOL

This project demonstrates how to build a chatbot using Langgraph and Langsmith, with integration of tools like Arxiv and Wikipedia for fetching real-time information.

## Overview

This chatbot leverages the **Langgraph** and **Langsmith** libraries to create an interactive conversational agent. The chatbot is powered by the **ChatGroq** model, which is based on LLaMA 3-8b-8192, and integrates **Arxiv** and **Wikipedia** tools to answer user queries with real-time data.

## Installation

To set up the project, you need to install the following dependencies:

```bash
pip install langgraph langsmith langchain langchain_groq langchain_community
pip install arxiv wikipedia
