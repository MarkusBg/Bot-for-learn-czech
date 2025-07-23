import pytest
from states.base_state import BaseState
from states.writing_state import WritingState
from states.learning_state import LearningState
from states.waiting_state import WaitingState

def test_base_state_not_implemented():
    base = BaseState()
    with pytest.raises(NotImplementedError):
        base.handle(None, None, None, None)

def test_inherited_states():
    for StateClass in [WritingState, LearningState, WaitingState]:
        state = StateClass()
        assert hasattr(state, 'handle')