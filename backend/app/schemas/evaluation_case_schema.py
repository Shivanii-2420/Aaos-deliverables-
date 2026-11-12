from pydantic import AliasChoices, BaseModel, Field


class EvaluationCaseCreate(BaseModel):

    name: str

    prompt: str

    expected_response: str

    category: str

    test_run_id: int | None = None

    tags: list[str] = Field(default_factory=list)

    metadata: dict = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata_json", "metadata"),
    )

    dataset_id: int | None = None


class EvaluationCaseResponse(
    EvaluationCaseCreate
):

    id: int

    class Config:
        from_attributes = True