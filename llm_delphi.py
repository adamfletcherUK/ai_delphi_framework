# from langchain.llms import OpenAI
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema.messages import SystemMessage
import yaml
import os
import json
import pandas as pd
import glob


def llm_config():
    # Load LLM Config Information from config.yaml
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    if config['llm_framework'] == 'OpenAI':
        os.environ['OPENAI_API_KEY'] = config['OpenAI']['api_key']
        # DEFINE DEFAULT LLM
        llm = ChatOpenAI(model=config['OpenAI']['default_model'])
        # TODO: Determine if there is a need for multiple LLM definitions
    if config['llm_framework'] == 'Ollama':
        llm = ChatOllama(model=config['Ollama']['default_model'])

    return llm


def pipeline():
    # Configure LLM
    print('\nLoading LLM Config')
    llm = llm_config()

    # Read the User input for a project to investigate
    with open('outputs/1_question.md') as f:
        question = f.read()

    # Determine Key Themes From Input
    print('Determining Key Themes')
    key_themes = llm.invoke(
        ChatPromptTemplate.from_messages(
            [SystemMessage(
                content=(open('./persona_descriptions/determine_key_themes.txt').read())),
             HumanMessagePromptTemplate.from_template(
                """can you provide key themes around the question or subject of '{question}'""")])
        .format_messages(question=question))\
        .content

    # Write Key Themes To File
    with open("outputs/2_key_themes.md", "w") as text_file:
        text_file.write(key_themes)

    # Design Questionnaire From Themes
    print('Designing Questionnaire')
    questionnaire = llm.invoke(
        ChatPromptTemplate.from_messages(
            [SystemMessage(
                content=(open('./persona_descriptions/create_the_initial_questionnaire.txt').read())),
             HumanMessagePromptTemplate.from_template(
                """can you questionnaire to gather information around the question or subject of '{question}' making sure to take into account the key themes from Dr. Renn, here are his findings: {themes}""")])
        .format_messages(question=question, themes=key_themes))\
        .content

    # Write Questionnaire To File
    with open("outputs/3_questionnaire.md", "w") as text_file:
        text_file.write(questionnaire)

    # Convert Questionnaire to JSON
    print('  - Converting Questionnaire to JSON')

    for attempt in range(5):
        try:
            questionnaire_json = llm.invoke(
                ChatPromptTemplate.from_messages(
                    [SystemMessage(
                        content=(open('./persona_descriptions/turn_initial_questionnaire_to_JSON.txt').read())),
                     HumanMessagePromptTemplate.from_template(
                        """Can you convert the following into a JSON object: {questionnaire}""")])
                .format_messages(questionnaire=questionnaire))\
                .content
            questionnaire_json = json.loads(questionnaire_json)
            break
        except:
            print(
                f"  - Attempt {attempt + 1}: LLM Failed to Make JSON. Retrying...")
            continue

    # Write to File
    with open("outputs/3_questionnaire.json", "w") as f:
        json.dump(questionnaire_json, f)

    # Make Overview of Types of Experts Needed
    print("Defining Experts")
    expert_personas_overview_md = llm.invoke(
        ChatPromptTemplate.from_messages(
            [SystemMessage(
                content=(open('./persona_descriptions/make_initial_overview_of_expert_types.txt').read())),
             HumanMessagePromptTemplate.from_template(
                """can you craft descriptions of the different type of experts which would make up a diverse panel of experts on the subject of '{question}', with the key themes being '{key_themes}' where the questions being answered are '{questionnaire}'""")])
        .format_messages(question=question,
                         key_themes=key_themes,
                         questionnaire=questionnaire))\
        .content

    with open("outputs/4_expert_personas_overview.md", "w") as text_file:
        text_file.write(expert_personas_overview_md)

    # Convert Expert Overviews to JSON
    print('  - Converting Expert Overviews to JSON')

    for attempt in range(3):
        try:
            expert_personas_overview_json = llm.invoke(
                ChatPromptTemplate.from_messages(
                    [SystemMessage(
                        content=(open('./persona_descriptions/convert_initial_overview_to_JSON.txt').read())),
                     HumanMessagePromptTemplate.from_template(
                        """Can you convert the following into a JSON object: {expert_personas_overview_md}""")])
                .format_messages(expert_personas_overview_md=expert_personas_overview_md))\
                .content
            persona_overview_json = json.loads(expert_personas_overview_json)
            break
        except:
            print(
                f"    - Attempt {attempt + 1}: LLM Failed to Make JSON.  Retrying...")
            continue

    # Cleanup files if they exist
    files = glob.glob('outputs/5_custom_personas/*')
    for f in files:
        os.remove(f)

    # Craft Persona Descriptions from JSON
    print("Crafting Expert Persona Descriptions")
    for i in persona_overview_json['Expert Personas']:
        print(f"  - {i['Role']}")
        specific_personas = llm.invoke(
            ChatPromptTemplate.from_messages([
                SystemMessage(
                    content=(open('./persona_descriptions/craft_persona_from_overview_persona.txt').read())),
                HumanMessagePromptTemplate.from_template(
                    """Can you convert craft various LLM personas for the role of {role}, with the characteristics of {characteristics}. Which could suitably answer the question of '{question}', where the key themes are '{key_themes}' and the questions being asked are '{questionnaire}'""")])
            .format_messages(
                role=i['Role'],
                characteristics=i['characteristics'],
                question=question,
                key_themes=key_themes,
                questionnaire=questionnaire))\
            .content

        with open(f"outputs/5_custom_personas/{i['Role']}.txt", "w") as text_file:
            text_file.write(specific_personas)

    # Convert Persona Descriptions to JSON
    print('  - Converting to JSON')
    files = glob.glob('outputs/5_custom_personas/*.txt')
    for file in files:
        # print(os.path.basename(file).replace('.txt', ''))
        with open(file, 'r') as text_file:
            specific_personas = text_file.read()

        for attempt in range(3):
            try:
                specific_personas_json = llm.invoke(
                    ChatPromptTemplate.from_messages([
                        SystemMessage(
                            content=(open('./persona_descriptions/convert_expert_persona_descriptions_to_JSON.txt').read())),
                        HumanMessagePromptTemplate.from_template(
                            """Can you convert the following into a JSON object: {specific_personas}""")])
                    .format_messages(specific_personas=specific_personas))\
                    .content
                specific_personas_json = json.loads(specific_personas_json)
                break

            except:
                print(
                    f"    - Attempt {attempt + 1}: LLM Failed to Make JSON. Retrying...")
            continue

        with open(f"outputs/5_custom_personas/{os.path.basename(file).replace('.txt','')}.json", 'w') as f:
            json.dump(specific_personas_json, f)

    # Remove Files If They Exist
    files = glob.glob('outputs/6_final_personas/*.md')
    for f in files:
        os.remove(f)

    # Flesh Out Personas With Viewpoints
    print("Making Multiple Expert Personas with different viewpoints:")
    files = glob.glob('outputs/5_custom_personas/*.json')
    for file in files:
        print(f"  {os.path.basename(file).replace('.json', '')}")
        with open(file, 'r') as j:
            specific_personas_json = json.loads(j.read())

        for i in specific_personas_json['Expert Personas']:
            print(f"    - {i['Role']}")
            detailed_persona = llm.invoke(
                ChatPromptTemplate.from_messages([
                    SystemMessage(
                        content=(open('./persona_descriptions/flesh_out_expert_personas_with_viewpoints.txt').read())),
                    HumanMessagePromptTemplate.from_template(
                        """Can you convert craft a detailed personas for the role of {role}, with the characteristics of {characteristics}. Which could suitably answer questions where the key themes are '{key_themes}'""")])
                .format_messages(
                    role=i['Role'],
                    characteristics=i['characteristics'],
                    question=question,
                    key_themes=key_themes,
                    questionnaire=questionnaire))\
                .content

            with open(f"outputs/6_final_personas/{os.path.basename(file).replace('.json','')} {i['Role'].replace(':', '')}.md", "w") as text_file:
                text_file.write(detailed_persona)

    # Get the Experts To Answer Questionnaires
    print('Answering Questionnaires')
    files = glob.glob('outputs/6_final_personas/*.md')
    for file in files:
        with open(file) as f:
            persona_content = f.read()

        print(f"  - {os.path.basename(file).replace('.md','')}")
        answered_questionaire = llm.invoke(
            ChatPromptTemplate.from_messages(
                [SystemMessage(
                    content=(f"""{persona_content}  {open('./persona_descriptions/have_each_persona_answer_the_initial_questionnaire.txt').read()}""")),
                 HumanMessagePromptTemplate.from_template(
                    """Can you to the best of your ability answer this questionare giving very detailed responses: {questionnaire}""")])
            .format_messages(questionnaire=questionnaire))\
            .content

        with open(f"outputs/7_answered_questionares/{os.path.basename(file).replace('.md','')}.md", "w") as text_file:
            text_file.write(answered_questionaire)

    # Convert Answered Questionnaire to JSON
    print('Converting Answered Questionnaires to JSON')
    files = glob.glob('outputs/7_answered_questionares/*.md')
    for file in files:
        print(f"  - {os.path.basename(file).replace('.md', '')}")
        with open(file, 'r') as text_file:
            answered_questionnaire = text_file.read()

        for attempt in range(3):
            try:
                answered_questionnaire_json = llm.invoke(
                    ChatPromptTemplate.from_messages(
                        [SystemMessage(
                            content=(open('./persona_descriptions/convert_initial_questionnaire_responses_to_JSON.txt').read())),
                         HumanMessagePromptTemplate.from_template(
                            """Can you convert the following into a JSON object: {answered_questionnaire}""")])
                    .format_messages(answered_questionnaire=answered_questionnaire))\
                    .content

                answered_questionnaire_json = json.loads(
                    answered_questionnaire_json)
                with open(f"outputs/7_answered_questionares/{os.path.basename(file).replace('.md','')}.json", 'w') as f:
                    json.dump(answered_questionnaire_json, f)
                break
            except:
                print(
                    f"    - Attempt {attempt + 1}: LLM Failed to Make JSON. Retrying...")
            continue

    # Reformat Question JSON to Bundle by Questions
    print('Reformatting Questions')
    responses_df = pd.DataFrame()
    files = glob.glob('outputs/7_answered_questionares/*.json')
    for file in files:
        expert = os.path.basename(file).replace('.json', '')
        print(f"  - {expert}")
        with open(file, 'r') as j:
            response = json.loads(j.read())
        tmp_df = pd.DataFrame.from_dict(response['Answers'])
        tmp_df['Expert'] = expert
        responses_df = pd.concat([responses_df, tmp_df])

    def dataframe_to_text(df, question):
        text_lines = []
        line = f"""# {question}\n"""
        text_lines.append(line)

        for index, row in df.iterrows():
            line = f"""\n## {row['Expert']}:\n{row['Response']}\n"""
            text_lines.append(line.replace("['", "").replace(
                "']", "").replace('["', '').replace('"]', ''))
        return " ".join(text_lines)

    questionare_df = pd.DataFrame.from_dict(
        questionnaire_json['Questionare'])  # todo: fix this spelling error

    for i in questionare_df['Number'].unique():
        question = questionare_df.loc[questionare_df['Number']
                                      == i]['Question'].values[0]
        formatted_question = dataframe_to_text(responses_df.loc[responses_df['Question'] == i],
                                               question)

        with open(f"outputs/8_formatted_questions/{question}.md", "w") as text_file:
            text_file.write(formatted_question)


if __name__ == '__main__':
    pipeline()
