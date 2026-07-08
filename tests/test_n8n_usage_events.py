from gateway import _build_n8n_usage_event


def test_n8n_usage_event_normalizes_deepseek_tokens_without_payload_text():
    event = _build_n8n_usage_event(
        {
            "workflow": "Mengniu",
            "source_node": "automation-n8n",
            "node_name": "DeepSeek Chat Model",
            "provider": "deepseek",
            "model": "deepseek-chat",
            "execution_id": "123",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            "prompt": "do not store this",
            "response": "do not store this either",
            "command": "curl with secret",
            "headers": {"Authorization": "secret"},
        }
    )

    assert event["agent"] == "n8n"
    assert event["source_node"] == "automation-n8n"
    assert event["project"] == "Mengniu"
    assert event["provider"] == "deepseek"
    assert event["model"] == "deepseek-chat"
    assert event["input_tokens"] == 100
    assert event["output_tokens"] == 50
    assert event["total_tokens"] == 150
    assert event["token_status"] == "n8n_reported"
    assert "prompt" not in event
    assert "response" not in event
    assert "command" not in event
    assert "headers" not in event


def test_n8n_usage_event_supports_media_accounting_without_tokens():
    event = _build_n8n_usage_event(
        {
            "workflow": "07V_V2_Seedance直出视频",
            "source_node": "automation-n8n",
            "provider": "volcengine",
            "model": "seedance",
            "task_id": "video-task-1",
            "status": "success",
            "media_units": 1,
            "video_seconds": 8,
            "estimated_cost_usd": 0.12,
            "cost_status": "n8n_media_estimate",
        }
    )

    assert event["agent"] == "n8n"
    assert event["provider"] == "volcengine"
    assert event["model"] == "seedance"
    assert event["total_tokens"] == 0
    assert event["token_status"] == "not_available"
    assert event["media_units"] == 1
    assert event["video_seconds"] == 8.0
    assert event["estimated_cost_usd"] == 0.12
    assert event["cost_status"] == "n8n_media_estimate"
