import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# @pytest_asyncio.fixture(autouse=True)
# async def clear_redis(client: AsyncClient):
#     await client.get("/clear-redis")
#     yield


# # Test POST /v1/logs rate limit (5 requests per minute)
# @pytest.mark.asyncio
# async def test_post_logs_rate_limit(client: AsyncClient):
#     # Within limit
#     for i in range(5):
#         response = await client.post(
#             "/v1/logs",
#             json={
#                 "service": "test-service",
#                 "environment": "test",
#                 "level": "INFO",
#                 "log_message": f"Test log {i}",
#             },
#         )
#         assert response.status_code == 200, f"Request {i} failed: {response.text}"

#     # Exceed limit
#     for i in range(2):
#         response = await client.post(
#             "/v1/logs",
#             json={
#                 "service": "test-service",
#                 "environment": "test",
#                 "level": "INFO",
#                 "log_message": f"Exceed log {i}",
#             },
#         )
#         assert response.status_code == 429, f"Request {i} should be rate-limited"


# # Test GET /v1/logs rate limit (20 requests per minute)
# @pytest.mark.asyncio
# async def test_get_logs_rate_limit(client: AsyncClient):
#     # Within limit
#     for i in range(20):
#         response = await client.get("/v1/logs")
#         assert response.status_code == 200, f"Request {i} failed: {response.text}"

#     # Exceed limit
#     response = await client.get("/v1/logs")
#     assert response.status_code == 429, f"Request {i} should be rate-limited"


# # Test GET /v1/logs/{log_id} rate limit (20 requests per minute)
# @pytest.mark.asyncio
# async def test_get_log_by_id_rate_limit(client: AsyncClient):
#     # First, create a log to have an ID
#     create_response = await client.post(
#         "/v1/logs",
#         json={
#             "service": "test-service-get",
#             "environment": "test",
#             "level": "INFO",
#             "log_message": "Log for get by ID test",
#         },
#     )
#     assert create_response.status_code == 200
#     log_id = create_response.json()["id"]

#     # Within limit
#     for i in range(20):
#         response = await client.get(f"/v1/logs/{log_id}")
#         assert response.status_code == 200, f"Request {i} failed: {response.text}"

#     # Exceed limit
#     response = await client.get(f"/v1/logs/{log_id}")
#     assert response.status_code == 429, f"Request {i} should be rate-limited"


# # Test DELETE /v1/logs/{log_id} rate limit (2 requests per minute)
# @pytest.mark.asyncio
# async def test_delete_log_rate_limit(client: AsyncClient):
#     # Create two logs for deletion
#     log_ids = []
#     for _ in range(2):
#         create_response = await client.post(
#             "/v1/logs",
#             json={
#                 "service": "test-service-delete",
#                 "environment": "test",
#                 "level": "INFO",
#                 "log_message": "Log for delete test",
#             },
#         )
#         assert create_response.status_code == 200
#         log_ids.append(create_response.json()["id"])

#     # Within limit
#     response = await client.delete(f"/v1/logs/{log_ids[0]}")
#     assert response.status_code == 200

#     # Exceed limit
#     response = await client.delete(f"/v1/logs/{log_ids[1]}")
#     assert response.status_code == 200

#     # Create a third log to attempt deletion and hit limit
#     create_response = await client.post(
#         "/v1/logs",
#         json={
#             "service": "test-service-delete-exceed",
#             "environment": "test",
#             "level": "INFO",
#             "log_message": "Log to hit delete limit",
#         },
#     )
#     assert create_response.status_code == 200
#     log_id_exceed = create_response.json()["id"]

#     # Attempt to delete third log (exceeds limit)
#     response = await client.delete(f"/v1/logs/{log_id_exceed}")
#     assert response.status_code == 429, "Request should be rate-limited"


# Test /health endpoint is not rate limited
@pytest.mark.asyncio
async def test_health_not_rate_limited(client: AsyncClient):
    # Make many requests to ensure it's not rate-limited
    for i in range(50):  # Arbitrarily large number
        response = await client.get("/healthz")
        assert response.status_code == 200, (
            f"Health check failed on request {i}: {response.text}"
        )
        assert response.json() == {"status": "ok"}
