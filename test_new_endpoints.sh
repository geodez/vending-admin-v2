#!/bin/bash
# Скрипт для тестирования новых endpoints после деплоя
# Использование: ./test_new_endpoints.sh <JWT_TOKEN>

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${1:-}"

if [ -z "$TOKEN" ]; then
    echo "❌ Ошибка: требуется JWT токен"
    echo "Использование: $0 <JWT_TOKEN>"
    exit 1
fi

echo "🧪 Тестирование новых endpoints..."
echo "Base URL: $BASE_URL"
echo ""

# Функция для выполнения запроса
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo "📋 Тест: $description"
    echo "   $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo "   ✅ Успех (HTTP $http_code)"
        echo "$body" | python3 -m json.tool 2>/dev/null | head -5 || echo "$body" | head -3
    else
        echo "   ❌ Ошибка (HTTP $http_code)"
        echo "$body" | head -3
    fi
    echo ""
}

# Тест 1: GET /api/v1/analytics/sales/summary
test_endpoint "GET" "/api/v1/analytics/sales/summary?from_date=2026-01-01&to_date=2026-01-25" "" \
    "Sales Summary"

# Тест 2: GET /api/v1/analytics/sales/margin
test_endpoint "GET" "/api/v1/analytics/sales/margin?from_date=2026-01-01&to_date=2026-01-25" "" \
    "Sales Margin"

# Тест 3: GET /api/v1/analytics/owner-report/daily
test_endpoint "GET" "/api/v1/analytics/owner-report/daily?period_start=2026-01-01&period_end=2026-01-25" "" \
    "Owner Report Daily"

# Тест 4: GET /api/v1/analytics/owner-report/issues
test_endpoint "GET" "/api/v1/analytics/owner-report/issues" "" \
    "Owner Report Issues"

# Тест 5: GET /api/v1/expenses/analytics
test_endpoint "GET" "/api/v1/expenses/analytics?from_date=2026-01-01&to_date=2026-01-25" "" \
    "Expenses Analytics"

# Тест 6: GET /api/v1/expenses/categories
test_endpoint "GET" "/api/v1/expenses/categories" "" \
    "Expenses Categories"

# Тест 7: Проверка существующих endpoints (чтобы убедиться, что ничего не сломалось)
echo "📋 Проверка существующих endpoints..."
test_endpoint "GET" "/api/v1/analytics/overview?from_date=2026-01-01" "" \
    "Analytics Overview (существующий)"

test_endpoint "GET" "/api/v1/mapping/button-matrices" "" \
    "Button Matrices (существующий)"

echo "✅ Тестирование завершено!"
