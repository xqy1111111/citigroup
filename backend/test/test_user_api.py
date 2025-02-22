import pytest
from fastapi.testclient import TestClient
from backend.main import app  # 确保 `app` 是你的 FastAPI 实例


client = TestClient(app)  # 使用 TestClient 进行 API 测试

# 测试用户数据
test_user_data = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword",
    "profile_picture": "http://example.com/avatar.jpg"
}

# 测试创建用户
def test_create_user():
    response = client.post("/users/", json=test_user_data)
    assert response.status_code == 200  # 确保请求成功
    data = response.json()
    assert "id" in data  # 确保返回了用户 ID
    global test_user_id  # 记录用户 ID 以供后续测试
    test_user_id = data["id"]

# 测试用户认证
def test_authenticate_user():
    login_data = {"username_or_email": test_user_data["email"], "password": test_user_data["password"]}
    response = client.post("/users/authenticate/", json=login_data)
    assert response.status_code == 200  # 确保登录成功
    data = response.json()
    assert "user_id" in data  # 确保返回了用户 ID
    assert data["user_id"] == test_user_id

# 测试获取用户信息
def test_get_user():
    response = client.get(f"/users/{test_user_id}")
    assert response.status_code == 200  # 确保请求成功
    data = response.json()
    assert data["id"] == test_user_id
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]

# 测试认证失败（错误密码）
def test_authenticate_user_wrong_password():
    wrong_login_data = {"username_or_email": test_user_data["email"], "password": "wrongpassword"}
    response = client.post("/users/authenticate/", json=wrong_login_data)
    assert response.status_code == 401  # 确保返回 401
    assert response.json()["detail"] == "Invalid credentials"

# 测试获取不存在的用户
def test_get_nonexistent_user():
    response = client.get("/users/invalid_user_id")
    assert response.status_code == 404  # 确保返回 404
    assert response.json()["detail"] == "User not found"
