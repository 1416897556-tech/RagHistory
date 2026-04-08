from auth import hash_password

# 替换为你想要的管理员密码
raw_password = "12345"
print(f"你的加密哈希值是: {hash_password(raw_password)}")