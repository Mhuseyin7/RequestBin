from app.services.transforms import apply, matches

def test_header_condition_and_safe_transform():
    assert matches({"source":"header","path":"x-event","equals":"payment.completed"}, {"x-event":"payment.completed"}, {})
    body, headers = apply({"event":{"id":1}}, {"authorization":"secret"}, [{"op":"set_field","path":"meta.source","value":"requestbinx"},{"op":"remove_header","name":"authorization"}])
    assert body["meta"]["source"] == "requestbinx"
    assert "authorization" not in headers
