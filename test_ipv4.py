import socket
import httpx

print("Đang kiểm tra kết nối IPv4...")

old_getaddrinfo = socket.getaddrinfo

def getaddrinfo_ipv4(host, port, *args, **kwargs):
    return old_getaddrinfo(
        host,
        port,
        socket.AF_INET,
        *args[1:],
        **kwargs
    )

socket.getaddrinfo = getaddrinfo_ipv4

print("Đã ép Python ưu tiên IPv4.")

try:
    response = httpx.get(
        "https://generativelanguage.googleapis.com",
        timeout=10
    )

    print("Kết nối thành công!")
    print("HTTP status:", response.status_code)

except Exception as e:
    print("Lỗi:", e)