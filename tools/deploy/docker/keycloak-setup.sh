#!/bin/bash
# Keycloak Development Setup Script
# This script sets up a basic OAuth client in Keycloak for development

echo "🔐 Setting up Keycloak for development..."

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to start..."
until curl -s http://localhost:18080/health/ready > /dev/null; do
    sleep 2
done

echo "✅ Keycloak is ready!"

# Get admin access token
echo "🔑 Getting admin access token..."
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:18080/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -d "username=admin" \
    -d "password=admin" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token"
    exit 1
fi

echo "✅ Admin token acquired"

# Create realm for development
echo "🏛️ Creating development realm..."
curl -s -X POST "http://localhost:18080/admin/realms" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "realm": "litestar-dev",
        "displayName": "Litestar Development",
        "enabled": true,
        "registrationAllowed": true,
        "loginWithEmailAllowed": true,
        "duplicateEmailsAllowed": false
    }' > /dev/null

echo "✅ Development realm created"

# Create OAuth client
echo "🔧 Creating OAuth client..."
CLIENT_UUID=$(curl -s -X POST "http://localhost:18080/admin/realms/litestar-dev/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "litestar-app",
        "name": "Litestar Application",
        "description": "OAuth client for Litestar development",
        "enabled": true,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": [
            "http://localhost:3000/auth/callback",
            "http://localhost:3000/auth/google/callback",
            "http://localhost:8000/api/auth/google/callback"
        ],
        "webOrigins": [
            "http://localhost:3000",
            "http://localhost:8000"
        ],
        "protocol": "openid-connect",
        "publicClient": false,
        "bearerOnly": false,
        "standardFlowEnabled": true,
        "implicitFlowEnabled": false,
        "directAccessGrantsEnabled": true,
        "serviceAccountsEnabled": false,
        "attributes": {
            "saml.assertion.signature": "false",
            "saml.force.post.binding": "false",
            "saml.multivalued.roles": "false",
            "saml.encrypt": "false",
            "oauth2.device.authorization.grant.enabled": "false",
            "backchannel.logout.revoke.offline.tokens": "false",
            "saml.server.signature": "false",
            "saml.server.signature.keyinfo.ext": "false",
            "exclude.session.state.from.auth.response": "false",
            "oidc.ciba.grant.enabled": "false",
            "saml.artifact.binding": "false",
            "backchannel.logout.session.required": "true",
            "client_credentials.use_refresh_token": "false",
            "saml_force_name_id_format": "false",
            "saml.client.signature": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "saml.authnstatement": "false",
            "display.on.consent.screen": "false",
            "saml.onetimeuse.condition": "false"
        }
    }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -z "$CLIENT_UUID" ]; then
    echo "⚠️  Client might already exist, continuing..."
else
    echo "✅ OAuth client created"
fi

# Get client secret
echo "🔑 Retrieving client secret..."
CLIENT_SECRET=$(curl -s "http://localhost:18080/admin/realms/litestar-dev/clients/litestar-app/client-secret" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['value'])" 2>/dev/null)

if [ -z "$CLIENT_SECRET" ]; then
    echo "❌ Failed to get client secret"
    # Try to get it by searching for the client
    CLIENT_SECRET=$(curl -s "http://localhost:18080/admin/realms/litestar-dev/clients?clientId=litestar-app" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | \
        python3 -c "import sys, json; clients = json.load(sys.stdin); print(clients[0]['id'] if clients else '')" 2>/dev/null)

    if [ ! -z "$CLIENT_SECRET" ]; then
        CLIENT_SECRET=$(curl -s "http://localhost:18080/admin/realms/litestar-dev/clients/$CLIENT_SECRET/client-secret" \
            -H "Authorization: Bearer $ADMIN_TOKEN" | \
            python3 -c "import sys, json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
    fi
fi

# Create a test user
echo "👤 Creating test user..."
curl -s -X POST "http://localhost:18080/admin/realms/litestar-dev/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "testuser@localhost",
        "firstName": "Test",
        "lastName": "User",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{
            "type": "password",
            "value": "testpass123",
            "temporary": false
        }]
    }' > /dev/null

echo "✅ Test user created"

echo ""
echo "🎉 Keycloak setup complete!"
echo ""
echo "📋 Configuration Summary:"
echo "   Realm: litestar-dev"
echo "   Client ID: litestar-app"
echo "   Client Secret: $CLIENT_SECRET"
echo "   Auth URL: http://localhost:18080/realms/litestar-dev/protocol/openid-connect/auth"
echo "   Token URL: http://localhost:18080/realms/litestar-dev/protocol/openid-connect/token"
echo "   Test User: testuser / testpass123"
echo ""
echo "🔧 Update your .env file with:"
echo "   GOOGLE_CLIENT_ID=litestar-app"
echo "   GOOGLE_CLIENT_SECRET=$CLIENT_SECRET"
echo "   OAUTH_ENABLED=true"
echo ""
echo "🌐 Access Keycloak admin: http://localhost:18080 (admin/admin)"
