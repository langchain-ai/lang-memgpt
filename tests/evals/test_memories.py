import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from langsmith import get_current_run_tree, test

from lang_memgpt._constants import PATCH_PATH
from lang_memgpt._schemas import GraphConfig
from lang_memgpt.graph import memgraph


@test(output_keys=["num_mems_expected"])
@pytest.mark.parametrize(
    "messages, existing, num_mems_expected",
    [
        ([("user", "hi")], {}, 0),
        (
            [
                (
                    "user",
                    "When I was young, I had a dog named spot. He was my favorite pup. It's really one of my core memories.",
                )
            ],
            {},
            1,
        ),
        (
            [
                (
                    "user",
                    "When I was young, I had a dog named spot. It's really one of my core memories.",
                )
            ],
            {"memories": ["I am afraid of spiders."]},
            2,
        ),
    ],
)
async def test_patch_memory(
    messages: List[str],
    num_mems_expected: int,
    existing: dict,
):
    # patch lang_memgpt.graph.index with a mock
    user_id = "4fddb3ef-fcc9-4ef7-91b6-89e4a3efd112"
    thread_id = "e1d0b7f7-0a8b-4c5f-8c4b-8a6c9f6e5c7a"
    function_name = "CoreMemories"
    with patch("lang_memgpt._utils.get_index") as get_index:
        index = MagicMock()
        get_index.return_value = index
        # No existing memories
        if existing:
            path = PATCH_PATH.format(
                user_id=user_id,
                function_name=function_name,
            )
            index.fetch.return_value = {
                "vectors": {path: {"metadata": {"content": json.dumps(existing)}}}
            }
        else:
            index.fetch.return_value = {}

        # When the memories are patched
        await memgraph.ainvoke(
            {
                "messages": messages,
            },
            {
                "configurable": GraphConfig(
                    delay=0.1,
                    user_id=user_id,
                    thread_id=thread_id,
                ),
            },
        )
        if num_mems_expected:
            # Check if index.upsert was called
            index.upsert.assert_called_once()
            # Get named call args
            vectors = index.upsert.call_args.kwargs["vectors"]
            rt = get_current_run_tree()
            rt.outputs = {"upserted": [v["metadata"]["content"] for v in vectors]}
            assert len(vectors) == 1
            # Check if the memory was added
            mem = vectors[0]["metadata"]["content"]
            assert mem


@test(output_keys=["num_events_expected"])
@pytest.mark.parametrize(
    "messages, num_events_expected",
    [
        ([("user", "hi")], 0),
        (
            [
                ("user", "I went to the beach with my friends today."),
                ("assistant", "That sounds like a fun day."),
                ("user", "You speak the truth."),
            ],
            1,
        ),
        (
            [
                ("user", "I went to the beach with my friends."),
                ("assistant", "That sounds like a fun day."),
                ("user", "I also went to the park with my family - I like the park."),
            ],
            1,
        ),
    ],
)
async def test_insert_memory(
    messages: List[str],
    num_events_expected: int,
):
    # patch lang_memgpt.graph.index with a mock
    user_id = "4fddb3ef-fcc9-4ef7-91b6-89e4a3efd112"
    thread_id = "e1d0b7f7-0a8b-4c5f-8c4b-8a6c9f6e5c7a"
    with patch("lang_memgpt._utils.get_index") as get_index:
        index = MagicMock()
        get_index.return_value = index
        index.fetch.return_value = {}
        # When the events are inserted
        await memgraph.ainvoke(
            {
                "messages": messages,
            },
            {
                "configurable": GraphConfig(
                    delay=0.1,
                    user_id=user_id,
                    thread_id=thread_id,
                ),
            },
        )
        if num_events_expected:
            # Get named call args
            assert len(index.upsert.call_args_list) >= num_events_expected
