from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSetting(BaseSettings):
    model_name: str = Field(default='hermes3:latest', description='The name of the LLM model to use.')
    model_prompt: str = Field(default='karma_prompt', description='The system prompt to use.')
    temperature: float = Field(default=0.6, gt=0.0, lt=1.0, description='The LLM temperature')
    top_p: float = Field(default=0.2, gt=0.0, lt=1.0, description='The LLM top probability')
    top_k: int = Field(default=10, gt=0, description='The LLM top-k')

class ChatSettings(BaseSettings):
    player_prefix: str = Field(default='[bold]localhost[/bold]> ', description='The player prefix on the chat')
    karma_prefix: str = Field(default='[bold]KARMA[/bold]> ', description='KARMA prefix on the chat')

class Settings(BaseSettings):
    assets_dir: str = Field(default='./assets', description='The location of the assets directory.')
    title: str = Field(default='title.txt', description='The location of the title ASCII art.')
    rng_seed: int = Field(default=1234, description='The RNG seed.')
    karma: LLMSetting = LLMSetting()
    neuralsys: LLMSetting = LLMSetting(model_name='llama3.1:latest', model_prompt='neuralsys_prompt', temperature=0.01)
    chat: ChatSettings = ChatSettings()

settings = Settings()