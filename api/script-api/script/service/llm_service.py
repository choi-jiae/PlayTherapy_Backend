from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from typing import TypeVar, Type
T = TypeVar("T")


class LLMService:

    def __init__(self, model_name: str, token: str, temperature: float = 0.5):
        self.model_name = model_name
        self.model = ChatOpenAI(openai_api_key=token)
        self.model.model_name = self.model_name
        self.temperature = temperature

    def run(
            self, system_prompt: str, prompt: str, variables: dict, class_type: Type[T]
    ):
        parser = PydanticOutputParser(pydantic_object=class_type)
        prompt_template = PromptTemplate(
            template=system_prompt + prompt + "\n{format_instructions}\n",
            input_variables=list(variables.keys()),
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # And a query intended to prompt a language model to populate the data structure.
        prompt_and_model = prompt_template | self.model
        output = prompt_and_model.invoke(variables)
        return parser.invoke(output)
