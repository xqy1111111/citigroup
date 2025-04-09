# ========================= user part =======================================
# 创建一个新的用户
curl -X POST http://localhost:8000/users/ -d '{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "profile_picture": "http://example.com/profile.jpg"
}' -H "Content-Type: application/json"

# 验证用户登陆
curl -X POST http://localhost:8000/users/authenticate/ -d '{
  "username_or_email": "newuser@example.com",
  "password": "password123"
}' -H "Content-Type: application/json"

# 获得某个用户的用户信息，注意将userid替换为对应的userid
curl -X 'GET' 'http://localhost:8000/users/{userid}'

