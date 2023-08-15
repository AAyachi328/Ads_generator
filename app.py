# Bring in deps
import os
import json
import streamlit as st
from typing import List
from pydantic import BaseModel, Field
from apikey import apikey
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

os.environ['OPENAI_API_KEY'] = apikey

model_name = "gpt-3.5-turbo-0301"
temperature = 0.4
model = OpenAI(model_name=model_name, temperature=temperature)

# App framework
st.title('📰💰 Aide à la création d'annonce')
prompt_input = st.text_input('Que souhaites tu vendres?')


@st.cache_data
def chatgpt(prompt_input):
    # if prompt_input:
    #     # Prompt templates
    #     # Le prompt mis à jour avec le nouveau texte
    class QA(BaseModel):
        question: str = Field(description="question")
        response: List[str] = Field(description="liste de responses")

    object_query = "exemple de format de réponse comme un json:\n{'question': 'Quelle est la superficie du terrain?', 'response': ['Petit', 'Moyen', 'Grand']}\n{'question': 'Quelle est la forme du terrain?', 'response': ['Rectangulaire', 'Irregulier', 'Ovale']}\n{'question': 'Quelle est la topographie du terrain?', 'response': ['Plat', 'Vallonné', 'Montagneux']} je voudrai vendre {object} je voudrai donc ecrire une annonce le plus détaillées possibles , poses moi les questions sur les principales caracteristiques ainsi que l'état et pour chacune donne moi les 3 ou 4 reponses les plus frequentes résumé par un mot, ajoute  dans les propositions de reponses 'je ne sais pas' et met 'autre' en dernier et ne poses pas de question sur le prix"
    parser = PydanticOutputParser(pydantic_object=QA)

    prompt = PromptTemplate(
        template="Fournir des informations sur {object}.\n{format_instructions}\n{query}\n",
        input_variables=["object", "query"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()},
    )

    # Formater le prompt avec l'objet spécifié dans la requête
    _input = prompt.format_prompt(object=prompt_input, query=object_query)

    # Soumission de la requête au modèle GPT-3.5
    output = model(_input.to_string())

    output = output.replace('\nOutput', '').replace(
        '}\n{', '},{').replace(':\n', '').replace('\n', '')

    output = "[" + output + "]"
    # st.write(output)
    output_list = json.loads(output)

    return output_list


# Ceci est un modèle Pydantic appelé QA pour question réponse qui définit la structure des données
# que nous attendons comme réponse.
# Le modèle a deux champs : question qui est une chaîne de caractères représentant la question
# et response qui est une liste de chaînes de caractères représentant les reponses fréqeuntes.
list_choix = []

if prompt_input:
    output_list = chatgpt(prompt_input)

    for i in range(len(output_list)):
        option = []
        list_rep = []
        for j in range(len(output_list[i]['response'])):
            list_rep.append(output_list[i]["response"][j])
        option = st.radio(output_list[i]["question"],
                          list_rep, horizontal=True)
        input_id = f"input_id{i}"
        details = output_list[i]["question"]
        details = details.split()[2:]
        details = " ".join(details)
        if option == 'Autre':
            input_id = st.text_input(
                "Précision ou détails sur " + details, key=input_id)
            list_choix.append(input_id)
        else: 
            list_choix.append(option)


    ann=[]
    for i in range(len(output_list)):
        details = output_list[i]["question"][:-1]
        details = details.split()[2:]
        details = " ".join(details)
        ann.append(details + " : " + list_choix[i])
    ann = ', '.join(ann)
    
if prompt_input and st.button('Créer mon annonce'):

    prompt = PromptTemplate.from_template(
        "Peux-tu m'ecrire une annonce pour vendre {object} dont les informations sont: {ann}, n'oubli pas de finir en disant que le prix est à négocier dans la limite du raisonnable")
    _input = prompt.format_prompt(object=object, ann=ann)

    annonce = model(_input.to_string())

    st.write(annonce)
    
