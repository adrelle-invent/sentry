# import os

# # Force empty Supabase credentials so it instantly falls back to mock client
# os.environ["SUPABASE_URL"] = ""
# os.environ["SUPABASE_KEY"] = ""
# # Prevent DNS resolution lookup delays on host 'redis' when running local tests
# os.environ["REDIS_HOST"] = "127.0.0.1"

# import asyncio

# import pytest

# from app.core.database import init_db
# from app.modules.issues.schemas import IssueResponse
# from app.modules.issues.service import IssueService


# @pytest.fixture(autouse=True, scope="function")
# def setup_db():
#     asyncio.run(init_db())

# def test_risk_score_calculation():
#     # Scenario: High impact, High likelihood, frequent count
#     score = IssueService.calculate_risk_score(base_impact=5.0, base_likelihood=0.9, frequency=15)
#     assert score == 6.0  # (5.0 * 0.9) + min(3.0, 1.5) = 4.5 + 1.5 = 6.0
#     assert IssueService.get_severity(score) == "MED"

#     # Scenario: Critical range
#     score_critical = IssueService.calculate_risk_score(base_impact=5.0, base_likelihood=0.9, frequency=40)
#     assert score_critical == 7.5  # (5.0 * 0.9) + min(3.0, 4.0) = 4.5 + 3.0 = 7.5
#     assert IssueService.get_severity(score_critical) == "MED"

#     # Scenario: Low range
#     score_low = IssueService.calculate_risk_score(base_impact=2.0, base_likelihood=0.5, frequency=2)
#     assert score_low == 1.2  # (2.0 * 0.5) + 0.2 = 1.0 + 0.2 = 1.2
#     assert IssueService.get_severity(score_low) == "LOW"

# @pytest.mark.asyncio
# async def test_detect_issues_completeness():
#     # Verify that the fallback seeding triggers and returns valid issue responses
#     issues = await IssueService.detect_issues()
#     assert len(issues) >= 5
#     for issue in issues:
#         assert isinstance(issue, IssueResponse)
#         assert issue.severity in ["CRI", "MED", "LOW"]
#         assert issue.category in ["DI", "CON", "FH", "OBS", "SEC", "REL"]
#         assert "-" in issue.id

# @pytest.mark.asyncio
# async def test_list_issues_filters():
#     # Filter by severity
#     cri_issues = await IssueService.list_issues(severity="CRI")
#     assert len(cri_issues) > 0
#     for issue in cri_issues:
#         assert issue.severity == "CRI"

#     # Filter by category
#     sec_issues = await IssueService.list_issues(category="SEC")
#     assert len(sec_issues) > 0
#     for issue in sec_issues:
#         assert issue.category == "SEC"

#     # Filter by endpoint
#     checkout_issues = await IssueService.list_issues(endpoint="/v1/checkout")
#     assert len(checkout_issues) > 0
#     for issue in checkout_issues:
#         assert "/v1/checkout" in issue.endpoint

# @pytest.mark.asyncio
# async def test_pdf_report_generation():
#     # Verify report is built without exceptions and returns a PDF streaming response
#     response = await IssueService.generate_pdf_report(
#         filters={"severity": "CRI"}
#     )
#     assert response is not None
#     assert response.media_type == "application/pdf"
#     assert "Content-Disposition" in response.headers
