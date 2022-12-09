from fastapi_keycloak import FastAPIKeycloak

idp = FastAPIKeycloak(
    server_url="https://auth.astrosync.ru/auth",
    client_id="test-client",
    client_secret="GzgACcJzhzQ4j8kWhmhazt7WSdxDVUyE",
    admin_client_secret="BIcczGsZ6I8W5zf0rZg5qSexlloQLPKB",
    realm="Test",
    callback_uri="http://192.168.196.209:8080/callback",
)
