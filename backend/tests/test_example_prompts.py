from app.services.agent_brief_service import clean_example_prompts, example_prompts_request


def test_keeps_three_distinct_trimmed_prompts():
    raw = ["  Dental clinics in Sydney ", "dental clinics in sydney", "", "Clinics open on Sundays",
           "Melbourne dental clinics with more than one dentist", "One too many"]
    assert clean_example_prompts(raw) == [
        "Dental clinics in Sydney",
        "Clinics open on Sundays",
        "Melbourne dental clinics with more than one dentist",
    ]


def test_drops_questions_about_companies_already_found():
    raw = ["Chinese restaurants in Sydney", "Does each restaurant offer online ordering?",
           "Chinese restaurants in Brisbane offering delivery"]
    assert clean_example_prompts(raw) == [
        "Chinese restaurants in Sydney",
        "Chinese restaurants in Brisbane offering delivery",
    ]


def test_drops_prompts_too_long_to_read_as_an_example():
    assert clean_example_prompts(["x" * 200, "Gyms in Brisbane"]) == ["Gyms in Brisbane"]


def test_request_is_built_from_the_title_and_description():
    text = example_prompts_request("Sydney dental clinics", "Private practices for a dental supply rep")
    assert "Sydney dental clinics" in text and "Private practices for a dental supply rep" in text


def test_request_without_a_description_says_so():
    text = example_prompts_request("Gym leads", None)
    assert "Gym leads" in text and "(no description)" in text
