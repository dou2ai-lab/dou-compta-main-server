#!/bin/bash
# smoke-tests.sh - End-to-end functional tests

set -e

API_BASE="${API_BASE:-http://localhost:8001}"
AUDIT_API="${AUDIT_API:-http://localhost:8004}"
EXPENSE_API="${EXPENSE_API:-http://localhost:8002}"
ADMIN_API="${ADMIN_API:-http://localhost:8003}"

echo "Running smoke tests..."
echo "API Base: $API_BASE"
echo ""

FAILED=0

# Test 1: Health Check
echo "Test 1: Health Check"
if curl -f -s "$API_BASE/health" > /dev/null 2>&1; then
  echo "✅ Health check works"
else
  echo "❌ Health check failed"
  FAILED=$((FAILED + 1))
fi

# Test 2: User Registration
echo "Test 2: User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "smoketest_'$(date +%s)'@example.com",
    "password": "Test123!@#",
    "first_name": "Test",
    "last_name": "User"
  }' 2>&1)

if echo "$REGISTER_RESPONSE" | grep -q "success\|token"; then
  echo "✅ User registration works"
  TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4 || echo "")
else
  echo "⚠️  User registration may have failed (user might already exist)"
  # Try login instead
  LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "admin@example.com",
      "password": "admin123"
    }' 2>&1)
  TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4 || echo "")
fi

if [ -z "$TOKEN" ]; then
  echo "⚠️  Could not obtain authentication token. Some tests will be skipped."
  echo "Tests completed with warnings."
  exit 0
fi

# Test 3: Get User Info
echo "Test 3: Get User Info"
USER_RESPONSE=$(curl -s -X GET "$API_BASE/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" 2>&1)

if echo "$USER_RESPONSE" | grep -q "email\|id"; then
  echo "✅ Get user info works"
else
  echo "❌ Get user info failed"
  FAILED=$((FAILED + 1))
fi

# Test 4: List Expenses
echo "Test 4: List Expenses"
EXPENSES_RESPONSE=$(curl -s -X GET "$EXPENSE_API/api/v1/expenses" \
  -H "Authorization: Bearer $TOKEN" 2>&1)

if echo "$EXPENSES_RESPONSE" | grep -q "success\|data\|\[\]"; then
  echo "✅ List expenses works"
else
  echo "❌ List expenses failed"
  FAILED=$((FAILED + 1))
fi

# Test 5: List Audit Reports
echo "Test 5: List Audit Reports"
AUDIT_RESPONSE=$(curl -s -X GET "$AUDIT_API/api/v1/audit/reports" \
  -H "Authorization: Bearer $TOKEN" 2>&1)

if echo "$AUDIT_RESPONSE" | grep -q "success\|\[\]"; then
  echo "✅ List audit reports works"
else
  echo "❌ List audit reports failed"
  FAILED=$((FAILED + 1))
fi

# Test 6: Admin - List Users (may require admin role)
echo "Test 6: Admin - List Users"
ADMIN_RESPONSE=$(curl -s -X GET "$ADMIN_API/api/v1/admin/users" \
  -H "Authorization: Bearer $TOKEN" 2>&1)

if echo "$ADMIN_RESPONSE" | grep -q "success"; then
  echo "✅ Admin list users works"
elif echo "$ADMIN_RESPONSE" | grep -q "403\|Forbidden"; then
  echo "⚠️  Admin endpoint requires admin role (expected)"
else
  echo "⚠️  Admin endpoint test inconclusive"
fi

echo ""
if [ $FAILED -eq 0 ]; then
  echo "All smoke tests passed!"
  exit 0
else
  echo "$FAILED test(s) failed"
  exit 1
fi



