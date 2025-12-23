# Flanks SDK API Discrepancies Fix Plan

**Created:** 2025-12-23
**Issue:** Multiple sub-clients have implementation errors that don't match the documented Flanks API.

## Summary of Issues Found

| Client | Methods | Issue Type |
|--------|---------|------------|
| Report | All 4 methods | Wrong response keys, wrong types, wrong HTTP method |
| Links | 7 methods | Wrong response keys, wrong param names, missing model fields |
| Credentials | 5 methods | Wrong response key, wrong param name |
| Aggregation v1 | 11 methods | Likely wrong response keys (need API verification) |
| FlanksConnection | api_call | Missing query params support for GET requests |

---

## Task 1: Fix FlanksConnection - Add Query Params Support

**File:** `flanks/connection.py`

**Issue:** GET requests need query parameters but current implementation only supports JSON body for POST.

**Fix:**
```python
async def api_call(
    self,
    path: str,
    body: dict[str, Any] | None = None,
    method: str = "POST",
    params: dict[str, Any] | None = None,  # ADD THIS
) -> dict[str, Any] | list[Any]:
```

And in `_execute`:
```python
async def _execute(
    self, method: str, path: str, body: dict[str, Any] | None, params: dict[str, Any] | None = None
) -> dict[str, Any] | list[Any]:
    response = await self._http.request(
        method=method,
        url=path,
        json=body if method != "GET" else None,
        params=params,  # ADD THIS
        headers={"Authorization": f"Bearer {self._access_token}"},
    )
```

---

## Task 2: Fix Report API Client

**Files:** `flanks/report/client.py`, `flanks/report/models.py`

### Issue 2.1: list_templates() - Wrong response key

**Current (WRONG):**
```python
return [ReportTemplate.model_validate(item) for item in response.get("templates", [])]
```

**Documented Response:**
```json
{
  "items": [
    { "template_id": int, "name": string, "description": string }
  ]
}
```

**Fix:**
```python
return [ReportTemplate.model_validate(item) for item in response.get("items", [])]
```

### Issue 2.2: template_id and report_id should be int, not str

**Current models:**
```python
class ReportTemplate(BaseModel):
    template_id: str  # WRONG

class Report(BaseModel):
    report_id: str  # WRONG
    template_id: str | None = None  # WRONG
```

**Fix:**
```python
class ReportTemplate(BaseModel):
    template_id: int

class Report(BaseModel):
    report_id: int
    template_id: int | None = None
```

### Issue 2.3: ReportStatus enum values wrong

**Current (WRONG):**
```python
class ReportStatus(str, Enum):
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
```

**Documented values:**
```python
class ReportStatus(str, Enum):
    NEW = "new"
    PAYLOAD = "payload"
    FILE = "file"
    READY = "ready"
    FAIL = "fail"
```

### Issue 2.4: build_report() signature incomplete

**Current:**
```python
async def build_report(
    self,
    template_id: str,
    language: str,
    start_date: datetime.date,
    end_date: datetime.date,
    credentials_token: str,
    **kwargs
) -> Report:
```

**Documented API requires:**
- `template_id`: int (required)
- `language`: str (optional, defaults to "en")
- `start_date`: str (optional)
- `end_date`: str (optional, defaults to today)
- `query`: dict (required) - filtering criteria with labels
- `template_attributes`: dict (required) - template-specific settings

**Fix:**
```python
async def build_report(
    self,
    template_id: int,
    query: dict[str, Any],
    template_attributes: dict[str, Any],
    *,
    language: str = "en",
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> Report:
```

### Issue 2.5: get_status() and get_content_url() - report_id should be int

**Current:**
```python
async def get_status(self, report_id: str) -> Report:
async def get_content_url(self, report_id: str) -> str:
```

**Fix:**
```python
async def get_status(self, report_id: int) -> Report:
async def get_content_url(self, report_id: int) -> str:
```

---

## Task 3: Fix Links API Client

**Files:** `flanks/links/client.py`, `flanks/links/models.py`

### Issue 3.1: list() - Response is array directly, not wrapped

**Current (WRONG):**
```python
response = await self._transport.api_call("/v0/links/list-links", method="GET")
if not isinstance(response, dict):
    raise TypeError(...)
return [Link.model_validate(item) for item in response.get("links", [])]
```

**Documented:** Response is "Array of link objects" directly.

**Fix:**
```python
response = await self._transport.api_call("/v0/links/list-links", method="GET")
if not isinstance(response, list):
    raise TypeError(f"Expected list response, got {type(response)}")
return [Link.model_validate(item) for item in response]
```

### Issue 3.2: edit/delete/pause/resume - Wrong parameter name

**Current:** Uses `link_token`
**Documented:** Uses `token`

**Fix all methods:**
```python
async def edit(self, token: str, **kwargs: str) -> Link:
    response = await self._transport.api_call(
        "/v0/links/edit-link",
        {"token": token, **kwargs},
    )

async def delete(self, token: str) -> None:
    await self._transport.api_call(
        "/v0/links/delete-link",
        {"token": token},
    )
# etc.
```

### Issue 3.3: get_unused_codes() - Should use query params, response is array

**Current (WRONG):**
```python
response = await self._transport.api_call(
    "/v0/platform/link",
    {"link_token": link_token},
    method="GET",
)
return [LinkCode.model_validate(item) for item in response.get("codes", [])]
```

**Documented:**
- GET with query parameter `link_token` (optional)
- Response is array directly

**Fix:**
```python
async def get_unused_codes(self, link_token: str | None = None) -> list[LinkCode]:
    params = {"link_token": link_token} if link_token else None
    response = await self._transport.api_call(
        "/v0/platform/link",
        method="GET",
        params=params,
    )
    if not isinstance(response, list):
        raise TypeError(f"Expected list response, got {type(response)}")
    return [LinkCode.model_validate(item) for item in response]
```

### Issue 3.4: Link model - Missing fields, wrong field name

**Current:**
```python
class Link(BaseModel):
    link_token: str
    name: str | None = None
    redirect_uri: str | None = None
    is_paused: bool | None = None
```

**Documented fields:**
- `token` (not `link_token`)
- `name`
- `redirect_uri`
- `company_name`
- `terms_and_conditions_url`
- `privacy_policy_url`
- `active` (not `is_paused` - inverted logic)
- `pending_code_count`

**Fix:**
```python
class Link(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    token: str
    name: str | None = None
    redirect_uri: str | None = None
    company_name: str | None = None
    terms_and_conditions_url: str | None = None
    privacy_policy_url: str | None = None
    active: bool = True
    pending_code_count: int | None = None
```

### Issue 3.5: LinkCode model - Missing fields

**Documented response for get_unused_codes:**
- `code`
- `extra` (extra parameters)
- `link_token`

**Fix:**
```python
class LinkCode(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    code: str
    link_token: str | None = None
    extra: dict[str, Any] | None = None
```

---

## Task 4: Fix Credentials API Client

**Files:** `flanks/credentials/client.py`, `flanks/credentials/models.py`

### Issue 4.1: list() - Wrong response key

**Current (WRONG):**
```python
return [Credential.model_validate(item) for item in response.get("credentials", [])]
```

**Documented:** Response has `"items"` key:
```json
{
  "items": [{ credentials_token, external_id, bank, status }],
  "page": int,
  "pages": int
}
```

**Fix:**
```python
return [Credential.model_validate(item) for item in response.get("items", [])]
```

Also update model to match documented fields:
```python
class Credential(BaseModel):
    credentials_token: str
    external_id: str | None = None
    bank: str | None = None
    status: str | None = None  # Not an enum based on docs
```

### Issue 4.2: force_* methods - Wrong parameter name

**Current (WRONG):**
```python
async def _update_status(self, credentials_token: str, action: str) -> CredentialStatusResponse:
    response = await self._transport.api_call(
        "/v0/bank/credentials/status",
        {"credentials_token": credentials_token, "action": action},  # WRONG
        method="PUT",
    )
```

**Documented:** Uses `force` parameter with values "sca", "reset", "transaction"

**Fix:**
```python
async def force_sca(self, credentials_token: str) -> str:
    """Force SCA. Returns sca_token."""
    response = await self._transport.api_call(
        "/v0/bank/credentials/status",
        {"credentials_token": credentials_token, "force": "sca"},
        method="PUT",
    )
    return response["sca_token"]

async def force_reset(self, credentials_token: str) -> str:
    """Force reset. Returns reset_token."""
    response = await self._transport.api_call(
        "/v0/bank/credentials/status",
        {"credentials_token": credentials_token, "force": "reset"},
        method="PUT",
    )
    return response["reset_token"]

async def force_transaction(self, credentials_token: str) -> str:
    """Force transaction refresh. Returns transaction_token."""
    response = await self._transport.api_call(
        "/v0/bank/credentials/status",
        {"credentials_token": credentials_token, "force": "transaction"},
        method="PUT",
    )
    return response["transaction_token"]
```

### Issue 4.3: CredentialStatusResponse - Missing many fields

**Documented fields:**
- `pending`
- `blocked`
- `reset_token`
- `sca_token`
- `transaction_token`
- `name`
- `last_update`
- `last_transaction_date`
- `errored`
- `created`

**Fix:**
```python
class CredentialStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    pending: bool | None = None
    blocked: bool | None = None
    reset_token: str | None = None
    sca_token: str | None = None
    transaction_token: str | None = None
    name: str | None = None
    last_update: datetime | None = None
    last_transaction_date: datetime | None = None
    errored: bool | None = None
    created: datetime | None = None
```

---

## Task 5: Fix Aggregation v1 API Client

**Files:** `flanks/aggregation_v1/client.py`, `flanks/aggregation_v1/models.py`

### Issue 5.1: Response structure - Need API verification

The documentation says endpoints return "array of objects" but doesn't specify if they're wrapped. Current implementation assumes:
- `get_portfolios` → `response["portfolios"]`
- `get_investments` → `response["investments"]`
- etc.

**This needs API testing to verify.** Based on the pattern in Entities API (which returns array directly), these likely also return arrays directly.

**Likely Fix (all methods):**
```python
async def get_portfolios(
    self,
    credentials_token: str,
    query: dict[str, Any] | None = None,
    ignore_data_error: bool = False,
) -> list[Portfolio]:
    response = await self._transport.api_call(
        "/v0/bank/credentials/portfolio",
        {
            "credentials_token": credentials_token,
            "query": query or {},
            "ignore_data_error": ignore_data_error,
        },
    )
    if not isinstance(response, list):
        raise TypeError(f"Expected list response, got {type(response)}")
    return [Portfolio.model_validate(item) for item in response]
```

### Issue 5.2: Query parameter structure

**Documented:**
- `credentials_token` (required)
- `query` (optional, object with filters)
- `ignore_data_error` (optional, boolean)

**Current (WRONG):**
```python
{"credentials_token": credentials_token, **query}  # Spreads query at top level
```

**Fix:**
```python
{
    "credentials_token": credentials_token,
    "query": query or {},
    "ignore_data_error": ignore_data_error,
}
```

---

## Task 6: Update Tests

All test files need to be updated to match the new API contracts:
- `tests/report/test_client.py`
- `tests/links/test_client.py`
- `tests/credentials/test_client.py`
- `tests/aggregation_v1/test_client.py`

Key changes:
1. Update mock responses to match documented structure
2. Update assertions for new parameter names and types
3. Add tests for new query params support in GET requests

---

## Execution Order

1. **Fix FlanksConnection** first (adds query params support)
2. **Fix Report API** (most clear discrepancies from user report)
3. **Fix Links API** (multiple issues)
4. **Fix Credentials API** (parameter naming)
5. **Fix Aggregation v1 API** (may need API testing to verify response structure)
6. **Update all tests**
7. **Run type checks and full test suite**

---

## Notes

- The Connect API v2 and Aggregation v2 documentation was not fully accessible, so those clients weren't fully verified
- Entities API appears correct (GET, returns array directly)
- All fixes should maintain backward compatibility where possible, but some breaking changes (like `template_id: str` → `int`) are necessary
