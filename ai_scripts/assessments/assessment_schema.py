from typing import List
from pydantic import BaseModel, field_validator

class MCQ(BaseModel):
    """
    Pydantic model for a single, validated Multiple Choice Question.
    """
    question_text: str
    options: List[str]
    correct_answer: str

    @field_validator('options')
    def check_options_count(cls, v):
        """Validates that there are exactly 4 options."""
        if len(v) != 4:
            raise ValueError('must provide exactly 4 options')
        return v

    @field_validator('correct_answer')
    def check_correct_answer_in_options(cls, v, values):
        """Validates that the correct answer is one of the provided options."""
        if 'options' in values.data and v not in values.data['options']:
            raise ValueError('correct answer must be one of the strings in the options list')
        return v
