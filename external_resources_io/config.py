from pydantic import field_validator
from pydantic_settings import BaseSettings, EnvSettingsSource


class Config(BaseSettings):
    """Environment Variables."""

    # general settings
    action: str = "Apply"
    dry_run: bool = True
    log_level: str = "INFO"

    # app-interface input related
    input_file: str = "/inputs/input.json"

    backend_tf_file: str = "module/backend.tf"
    outputs_file: str = "tmp/outputs.json"
    plan_file_json: str = "tmp/plan.json"
    terraform_cmd: str = "terraform"
    tf_vars_file: str = "module/tfvars.json"
    variables_tf_file: str = "module/variables.tf"

    @field_validator("action", mode="before")
    @classmethod
    def lower_action(cls, v: str) -> str:
        """Transform the action to lowercase."""
        return v.lower()


_env_settings = EnvSettingsSource(
    Config,
    case_sensitive=False,  # we want to user UPPERCASE env variable names only
    env_prefix=Config.model_config["env_prefix"],
    env_nested_delimiter=Config.model_config["env_nested_delimiter"],
)


def get_env_var_name(field_name: str) -> str:
    return _env_settings._extract_field_info(  # noqa: SLF001
        Config.model_fields[field_name], field_name
    )[0][1].upper()  # we want to user UPPERCASE env variable names only
